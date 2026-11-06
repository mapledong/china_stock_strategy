#!/usr/bin/env python3
"""Build and optionally email a Friday strategy status + holdings-change report.

Reads current ``web/data/strategies.json`` and compares against the previous
snapshot in ``results/weekly_report_snapshot.json`` (updated after each send).

SMTP settings (optional, from env / .env):
  SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASSWORD,
  SMTP_STARTTLS (default 1), MAIL_FROM, MAIL_TO
If SMTP is not configured, the HTML report is still written under results/.
"""

from __future__ import annotations

import argparse
import json
import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STRATEGIES = ROOT / "web" / "data" / "strategies.json"
SNAPSHOT = ROOT / "results" / "weekly_report_snapshot.json"
RESULTS = ROOT / "results"
SITE_URL = "https://mapledong.github.io/china_stock_strategy/"

STRATEGY_LABELS = {
    "composite": "复合策略",
    "etf": "ETF轮动",
    "ah": "AH折价",
    "dividend": "红利/创业板",
    "equity": "股权激励",
}


def _load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _holding_key(item: dict[str, Any]) -> str:
    return str(
        item.get("symbol")
        or item.get("pair")
        or item.get("name")
        or item.get("ts_code")
        or json.dumps(item, ensure_ascii=False, sort_keys=True)
    )


def _holding_label(item: dict[str, Any]) -> str:
    name = item.get("name") or item.get("pair") or item.get("symbol") or "?"
    symbol = item.get("symbol") or ""
    if symbol and symbol not in str(name):
        return f"{name} ({symbol})"
    return str(name)


def _weight(item: dict[str, Any]) -> float | None:
    for key in ("weight", "sleeve_weight", "entry_weight", "target_weight"):
        if key in item and item[key] is not None:
            try:
                return float(item[key])
            except (TypeError, ValueError):
                return None
    return None


def _fmt_pct(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.{digits}f}%"


def _diff_holdings(
    prev: list[dict[str, Any]] | None,
    curr: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    prev = prev or []
    curr = curr or []
    prev_map = {_holding_key(x): x for x in prev}
    curr_map = {_holding_key(x): x for x in curr}
    added = [curr_map[k] for k in curr_map.keys() - prev_map.keys()]
    removed = [prev_map[k] for k in prev_map.keys() - curr_map.keys()]
    kept = []
    for key in curr_map.keys() & prev_map.keys():
        pw = _weight(prev_map[key])
        cw = _weight(curr_map[key])
        delta = None if pw is None or cw is None else cw - pw
        kept.append({"item": curr_map[key], "prev_w": pw, "curr_w": cw, "delta": delta})
    kept.sort(key=lambda row: abs(row["delta"] or 0.0), reverse=True)
    return {"added": added, "removed": removed, "kept": kept}


def _metrics_line(strategy: dict[str, Any]) -> str:
    metrics = strategy.get("metrics") or {}
    bits = []
    for key, label in (
        ("cagr", "CAGR"),
        ("sharpe", "Sharpe"),
        ("max_drawdown", "MaxDD"),
        ("final_equity", "净值"),
        ("final_nav", "净值"),
    ):
        if key in metrics and metrics[key] is not None:
            val = float(metrics[key])
            if key in ("cagr", "max_drawdown"):
                bits.append(f"{label} {_fmt_pct(val)}")
            elif key in ("final_equity", "final_nav"):
                bits.append(f"{label} {val:.2f}")
            else:
                bits.append(f"{label} {val:.2f}")
    as_of = strategy.get("holdings_as_of") or strategy.get("as_of") or "—"
    bits.insert(0, f"截至 {as_of}")
    return " · ".join(bits)


def build_report(current: dict[str, Any], previous: dict[str, Any] | None) -> tuple[str, str]:
    generated = current.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M")
    version = current.get("data_version", "?")
    order = current.get("strategy_order") or list(STRATEGY_LABELS)
    prev_strategies = (previous or {}).get("strategies") or {}

    text_parts = [
        f"中国股票策略周报",
        f"生成时间: {generated}  |  dashboard v{version}",
        f"公网: {SITE_URL}",
        "",
    ]
    html_parts = [
        "<html><body style='font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;line-height:1.45'>",
        f"<h2>中国股票策略周报</h2>",
        f"<p>生成时间：<b>{generated}</b> · dashboard v{version}<br/>",
        f"公网：<a href='{SITE_URL}'>{SITE_URL}</a></p>",
    ]

    for key in order:
        strategy = (current.get("strategies") or {}).get(key) or {}
        label = STRATEGY_LABELS.get(key, key)
        holdings = strategy.get("holdings") or []
        prev_holdings = (prev_strategies.get(key) or {}).get("holdings") or []
        diff = _diff_holdings(prev_holdings, holdings)

        text_parts.append(f"## {label}")
        text_parts.append(_metrics_line(strategy))
        text_parts.append(f"当前持仓 {len(holdings)} 只：")
        for item in holdings:
            w = _fmt_pct(_weight(item))
            extra = ""
            if "ah_premium" in item and item["ah_premium"] is not None:
                extra = f"  AH溢价 {_fmt_pct(float(item['ah_premium']))}"
            text_parts.append(f"  - {_holding_label(item)}  {w}{extra}")

        if previous is None:
            text_parts.append("（首次快照，无上周对比）")
        else:
            text_parts.append(
                f"变动：新增 {len(diff['added'])} / 剔除 {len(diff['removed'])}"
            )
            for item in diff["added"]:
                text_parts.append(f"  + {_holding_label(item)}  {_fmt_pct(_weight(item))}")
            for item in diff["removed"]:
                text_parts.append(f"  - {_holding_label(item)}  {_fmt_pct(_weight(item))}")
            meaningful = [row for row in diff["kept"] if row["delta"] is not None and abs(row["delta"]) >= 0.005]
            if meaningful:
                text_parts.append("权重变化 ≥0.5%：")
                for row in meaningful[:12]:
                    text_parts.append(
                        f"  ~ {_holding_label(row['item'])}  "
                        f"{_fmt_pct(row['prev_w'])} → {_fmt_pct(row['curr_w'])} "
                        f"({_fmt_pct(row['delta'], 2)})"
                    )
        text_parts.append("")

        html_parts.append(f"<h3>{label}</h3>")
        html_parts.append(f"<p>{_metrics_line(strategy)}</p>")
        html_parts.append("<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;font-size:13px'>")
        html_parts.append("<tr><th>持仓</th><th>权重</th><th>备注</th></tr>")
        for item in holdings:
            note = ""
            if "ah_premium" in item and item["ah_premium"] is not None:
                note = f"AH溢价 {_fmt_pct(float(item['ah_premium']))}"
            elif item.get("sleeve_zh"):
                note = str(item["sleeve_zh"])
            html_parts.append(
                f"<tr><td>{_holding_label(item)}</td>"
                f"<td>{_fmt_pct(_weight(item))}</td><td>{note}</td></tr>"
            )
        html_parts.append("</table>")
        if previous is None:
            html_parts.append("<p><i>首次快照，无上周对比。</i></p>")
        else:
            html_parts.append(
                f"<p>变动：新增 <b>{len(diff['added'])}</b> / 剔除 <b>{len(diff['removed'])}</b></p><ul>"
            )
            for item in diff["added"]:
                html_parts.append(f"<li>+ {_holding_label(item)} {_fmt_pct(_weight(item))}</li>")
            for item in diff["removed"]:
                html_parts.append(f"<li>− {_holding_label(item)} {_fmt_pct(_weight(item))}</li>")
            if not diff["added"] and not diff["removed"]:
                html_parts.append("<li>持仓名单无变化</li>")
            html_parts.append("</ul>")
            meaningful = [row for row in diff["kept"] if row["delta"] is not None and abs(row["delta"]) >= 0.005]
            if meaningful:
                html_parts.append("<p>权重变化 ≥0.5%：</p><ul>")
                for row in meaningful[:12]:
                    html_parts.append(
                        f"<li>{_holding_label(row['item'])}: "
                        f"{_fmt_pct(row['prev_w'])} → {_fmt_pct(row['curr_w'])} "
                        f"({_fmt_pct(row['delta'], 2)})</li>"
                    )
                html_parts.append("</ul>")

    html_parts.append("</body></html>")
    return "\n".join(text_parts), "\n".join(html_parts)


def send_email(subject: str, text_body: str, html_body: str) -> bool:
    host = os.environ.get("SMTP_HOST", "").strip()
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()
    mail_from = os.environ.get("MAIL_FROM", user).strip()
    mail_to = os.environ.get("MAIL_TO", "").strip()
    port = int(os.environ.get("SMTP_PORT", "587"))
    starttls = os.environ.get("SMTP_STARTTLS", "1").strip() not in {"0", "false", "False"}

    if not host or not mail_to:
        print("SMTP not configured (need SMTP_HOST and MAIL_TO). Skipped email send.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if starttls:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=60) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            if user:
                server.login(user, password)
            server.sendmail(mail_from, [addr.strip() for addr in mail_to.split(",")], msg.as_string())
    else:
        with smtplib.SMTP_SSL(host, port, timeout=60) as server:
            if user:
                server.login(user, password)
            server.sendmail(mail_from, [addr.strip() for addr in mail_to.split(",")], msg.as_string())
    print(f"Email sent to {mail_to}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--send", action="store_true", help="Send email if SMTP is configured")
    parser.add_argument("--no-snapshot", action="store_true", help="Do not overwrite weekly snapshot")
    args = parser.parse_args()

    _load_dotenv()
    if not STRATEGIES.exists():
        raise SystemExit(f"Missing {STRATEGIES}; run daily_update first.")

    current = json.loads(STRATEGIES.read_text(encoding="utf-8"))
    previous = None
    if SNAPSHOT.exists():
        previous = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    text_body, html_body = build_report(current, previous)
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    text_path = RESULTS / f"weekly_report_{stamp}.txt"
    html_path = RESULTS / f"weekly_report_{stamp}.html"
    text_path.write_text(text_body, encoding="utf-8")
    html_path.write_text(html_body, encoding="utf-8")
    print(f"Wrote {text_path}")
    print(f"Wrote {html_path}")

    as_of = current.get("generated_at", stamp)
    subject = f"策略周报 {as_of} · dashboard v{current.get('data_version', '?')}"
    if args.send:
        send_email(subject, text_body, html_body)

    if not args.no_snapshot:
        SNAPSHOT.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Updated snapshot {SNAPSHOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
