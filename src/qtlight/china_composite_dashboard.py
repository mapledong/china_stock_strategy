"""Live composite strategy state for the public dashboard."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from qtlight.ah_twostage_research import build_targets_quarterly_buffer
from qtlight.china_layered_composite_low_turnover import (
    LOW_TURNOVER_SPEC,
    _load_monthly_premium_cache,
    run_ah_tushare_with_targets,
)
from qtlight.china_layered_composite_research import (
    incentive_positions_through_month,
    project_incentive_month_end,
)


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
OUTPUT_PREFIX = "china_layered_composite_low_turnover"
AH_DRIFT_WEIGHTS_PATH = RESULTS / f"{OUTPUT_PREFIX}_ah_drift_weights.csv"

AH_WEIGHT = LOW_TURNOVER_SPEC.ah_weight
INDUSTRY_WEIGHT = LOW_TURNOVER_SPEC.industry_weight
QUARTER_MONTHS = {3, 6, 9, 12}
INCENTIVE_SPEC = LOW_TURNOVER_SPEC.incentive


def _pair_to_symbol(pair: str) -> str:
    match = re.search(r"\((\d{6})/", pair)
    return match.group(1) if match else pair


def _last_quarter_rebalance_date(premium: pd.DataFrame, as_of: pd.Timestamp) -> pd.Timestamp:
    targets = build_targets_quarterly_buffer(premium)
    active = targets[targets.sum(axis=1) > 0]
    if active.empty:
        return pd.Timestamp(premium.index[-1])
    eligible = active.index[active.index <= as_of]
    return pd.Timestamp(eligible[-1] if len(eligible) else active.index[-1])


def _load_ah_drift_weights(premium: pd.DataFrame) -> pd.DataFrame:
    if AH_DRIFT_WEIGHTS_PATH.exists():
        frame = pd.read_csv(AH_DRIFT_WEIGHTS_PATH, index_col=0, parse_dates=True).sort_index()
        return frame

    targets = build_targets_quarterly_buffer(premium)
    _, _, weights = run_ah_tushare_with_targets(targets, "quarterly_buffer")
    AH_DRIFT_WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    weights.to_csv(AH_DRIFT_WEIGHTS_PATH)
    return weights


def _current_ah_drift_holdings(
    premium: pd.DataFrame,
    as_of: pd.Timestamp,
) -> tuple[pd.Timestamp, pd.Timestamp, list[dict]]:
    weights = _load_ah_drift_weights(premium)
    eligible = weights.index[weights.index <= as_of]
    if eligible.empty:
        return _last_quarter_rebalance_date(premium, as_of), as_of, []

    drift_date = pd.Timestamp(eligible[-1])
    row = weights.loc[drift_date]
    held = row[row > 1e-6].sort_values(ascending=False)
    prem_row = premium.loc[premium.index <= as_of].iloc[-1]

    holdings = []
    for pair, weight in held.items():
        prem = prem_row[pair] if pair in prem_row.index else float("nan")
        holdings.append(
            {
                "pair": pair,
                "symbol": _pair_to_symbol(pair),
                "weight": float(weight),
                "ah_premium": float(prem) if pd.notna(prem) else None,
            }
        )
    return _last_quarter_rebalance_date(premium, as_of), drift_date, holdings


def _ah_month_end_projection(
    premium: pd.DataFrame,
    current: list[dict],
    signal_date: pd.Timestamp,
) -> dict:
    is_quarter = signal_date.month in QUARTER_MONTHS
    current_keys = {h["pair"] for h in current}
    if not is_quarter:
        return {
            "unchanged": True,
            "signal_date": signal_date.date().isoformat(),
            "holdings": current,
            "entries": [],
            "exits": [],
            "note_zh": "AH 季频调仓（3/6/9/12 月末信号，次月首个交易日执行）；本月持有缓冲，无需调整。",
            "note_en": "AH rebalances quarterly (Mar/Jun/Sep/Dec); hold buffer this month — no change.",
        }

    signal_row = premium.loc[premium.index <= signal_date].iloc[-1]
    ranked = signal_row.dropna().sort_values()
    top = ranked.head(10)
    target_weight = 1.0 / len(top) if len(top) else 0.0
    projected = [
        {
            "pair": pair,
            "symbol": _pair_to_symbol(pair),
            "weight": target_weight,
            "ah_premium": float(prem),
        }
        for pair, prem in top.items()
    ]
    projected_keys = {h["pair"] for h in projected}
    entries = [h for h in projected if h["pair"] not in current_keys]
    exits = [h for h in current if h["pair"] not in projected_keys]
    return {
        "unchanged": not entries and not exits,
        "signal_date": signal_date.date().isoformat(),
        "holdings": projected,
        "entries": entries,
        "exits": exits,
        "note_zh": "季末信号月：对比 Top10 折价池，次月首个交易日执行调入/调出（非季内仅漂移权重）。",
        "note_en": "Quarter-end signal month: Top-10 discount pool; trades next month's first session (intra-quarter weights drift).",
    }


def _incentive_positions_at(as_of: pd.Timestamp) -> list[dict]:
    month_end = pd.Timestamp(as_of).to_period("M").to_timestamp("M")
    return incentive_positions_through_month(INCENTIVE_SPEC, month_end)


def _aggregate_top_holdings(
    ah_holdings: list[dict],
    industry_holdings: list[dict],
    incentive_positions: list[dict],
    zh: dict[str, str],
    en: dict[str, str],
    ah_pair_en: dict[str, str],
) -> tuple[list[dict], float, list[dict]]:
    rows: list[dict] = []

    for h in ah_holdings:
        sym = h["symbol"]
        rows.append(
            {
                "sleeve": "ah",
                "sleeve_zh": "AH折价",
                "sleeve_en": "AH discount",
                "symbol": sym,
                "name": zh.get(sym, sym),
                "name_en": en.get(sym, sym),
                "weight": h["weight"] * AH_WEIGHT,
                "sleeve_weight": h["weight"],
                "pair": h.get("pair"),
                "pair_en": ah_pair_en.get(h.get("pair", ""), h.get("pair")),
                "ah_premium": h.get("ah_premium"),
            }
        )

    for h in industry_holdings:
        sym = h["symbol"]
        rows.append(
            {
                "sleeve": "industry",
                "sleeve_zh": "红利/创业板",
                "sleeve_en": "Div/ChiNext",
                "symbol": sym,
                "name": h.get("name", zh.get(sym, sym)),
                "name_en": h.get("name_en", en.get(sym, sym)),
                "weight": h["weight"] * INDUSTRY_WEIGHT,
                "sleeve_weight": h["weight"],
            }
        )

    for p in incentive_positions:
        sym = p["symbol"]
        w = float(p["weight"])
        rows.append(
            {
                "sleeve": "incentive",
                "sleeve_zh": "股权激励",
                "sleeve_en": "Equity incentive",
                "symbol": sym,
                "name": zh.get(sym, sym),
                "name_en": en.get(sym, sym),
                "weight": w,
                "sleeve_weight": w,
                "exit_month": p.get("exit_month"),
            }
        )

    cash_weight = max(0.0, 1.0 - sum(r["weight"] for r in rows))
    rows.sort(key=lambda x: x["weight"], reverse=True)
    return rows[:20], cash_weight, rows


def compute_composite_state(
    zh: dict[str, str],
    en: dict[str, str],
    ah_pair_en: dict[str, str],
    div_state: dict,
    premium: pd.DataFrame,
) -> dict:
    nav_path = RESULTS / f"{OUTPUT_PREFIX}_daily_nav.csv"
    summary_path = RESULTS / f"{OUTPUT_PREFIX}_summary.json"

    if not nav_path.exists():
        raise FileNotFoundError(f"Missing {nav_path}. Run china_layered_composite_low_turnover first.")

    nav_df = pd.read_csv(nav_path, index_col=0, parse_dates=True).sort_index()
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    metrics_low = summary.get("metrics", {}).get("low_turnover_composite", {})
    metrics_hs300 = summary.get("metrics", {}).get("csi300", {})

    nav_start = "2018-04-02"
    start_dt = pd.Timestamp(nav_start)
    window = nav_df.loc[nav_df.index >= start_dt]
    combo = window["combo_nav"] / window.loc[window.index.min(), "combo_nav"]
    hs300 = window["hs300_nav"] / window.loc[window.index.min(), "hs300_nav"]
    nav_rows = [
        {"date": dt.date().isoformat(), "strategy_nav": float(combo.loc[dt]), "hs300_nav": float(hs300.loc[dt])}
        for dt in combo.index
    ]

    as_of = nav_df.index.max()
    signal_date = pd.Timestamp(as_of) + pd.offsets.MonthEnd(0)

    ah_rebal_date, ah_drift_date, ah_holdings = _current_ah_drift_holdings(premium, as_of)
    for h in ah_holdings:
        h["pair_en"] = ah_pair_en.get(h["pair"], h["pair"])

    industry_holdings = div_state["holdings"]
    industry_projection = div_state["projected_month_end"]

    incentive_open = _incentive_positions_at(as_of)
    ah_projection = _ah_month_end_projection(premium, ah_holdings, signal_date)
    incentive_projection = project_incentive_month_end(INCENTIVE_SPEC, incentive_open, signal_date)

    top20, cash_weight, all_holdings = _aggregate_top_holdings(
        ah_holdings, industry_holdings, incentive_open, zh, en, ah_pair_en
    )

    overall_unchanged = (
        ah_projection["unchanged"]
        and industry_projection.get("unchanged", False)
        and incentive_projection["unchanged"]
    )

    return {
        "id": "composite",
        "featured_variant": LOW_TURNOVER_SPEC.name,
        "latest_rebalance": ah_rebal_date.date().isoformat(),
        "holdings_as_of": as_of.date().isoformat(),
        "holdings": top20,
        "holdings_all_count": len(all_holdings),
        "cash_weight": cash_weight,
        "sleeve_weights": {
            "ah": AH_WEIGHT,
            "industry": INDUSTRY_WEIGHT,
            "incentive_cap": INCENTIVE_SPEC.max_gross,
        },
        "sleeves": {
            "ah": {
                "weight": AH_WEIGHT,
                "holdings": ah_holdings,
                "holdings_as_of": ah_drift_date.date().isoformat(),
                "latest_rebalance": ah_rebal_date.date().isoformat(),
                "weight_note_zh": "层内权重随价格漂移（季内不调仓）",
                "weight_note_en": "Intra-sleeve weights drift with prices (no rebalance intra-quarter)",
            },
            "industry": {
                "weight": INDUSTRY_WEIGHT,
                "holdings": industry_holdings,
                "latest_rebalance": div_state["latest_rebalance"],
            },
            "incentive": {
                "weight_cap": INCENTIVE_SPEC.max_gross,
                "slot_weight": INCENTIVE_SPEC.slot_weight,
                "hold_months": INCENTIVE_SPEC.hold_months,
                "positions": incentive_open,
                "position_count": len(incentive_open),
                "gross_weight": float(sum(p["weight"] for p in incentive_open)),
            },
        },
        "projected_month_end": {
            "signal_date": signal_date.date().isoformat(),
            "month": signal_date.strftime("%Y-%m"),
            "unchanged": overall_unchanged,
            "ah": ah_projection,
            "industry": industry_projection,
            "incentive": incentive_projection,
        },
        "rules_zh": [
            "复合策略：AH折价 50%（季频 3/6/9/12 月末 + Top10 持有缓冲，层内权重漂移）+ 红利/创业板 30% + 股权激励月频增量 2%/笔（公告后首个可交易月纳入，9 个月，15% cap）。",
            "Top20 为组合穿透权重（AH/行业层内已含价格漂移）；月底分三层展示调入/调出或「无需调整」。",
        ],
        "rules_en": [
            "Composite: AH 50% (quarterly Mar/Jun/Sep/Dec + hold buffer, intra-sleeve drift) + Div/ChiNext 30% + monthly incremental incentive 2% (first tradable month, 9M, 15% cap).",
            "Top 20 = look-through weights (AH/industry sleeves include price drift); month-end panel shows per-sleeve entries/exits or hold-buffer notes.",
        ],
        "metrics": {
            "cagr": float(metrics_low.get("cagr", 0)),
            "sharpe": float(metrics_low.get("sharpe", 0)),
            "max_drawdown": float(metrics_low.get("max_drawdown", 0)),
            "final_nav": float(metrics_low.get("final_nav", combo.iloc[-1])),
            "turnover_per_year": float(summary.get("estimated_low_turnover_portfolio_turnover", 0) or 0),
        },
        "benchmark_metrics": {
            "cagr": float(metrics_hs300.get("cagr", 0)),
            "sharpe": float(metrics_hs300.get("sharpe", 0)),
            "max_drawdown": float(metrics_hs300.get("max_drawdown", 0)),
            "final_nav": float(metrics_hs300.get("final_nav", hs300.iloc[-1])),
        },
        "nav": nav_rows,
        "nav_start": nav_start,
        "backtest_start": nav_start,
        "backtest_end": as_of.date().isoformat(),
        "cost_bps": 20.0,
    }
