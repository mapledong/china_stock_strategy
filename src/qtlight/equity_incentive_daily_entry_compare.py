"""Daily equity-incentive backtest: T+1 open vs month-end close entry (MA200, limit-up skip)."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pandas as pd

from qtlight.china_layered_composite_research import _metrics
from qtlight.equity_incentive_daily_slot_backtest import (
    build_daily_close_panels,
    is_limit_up_row,
    load_stock_daily_panels,
)
from qtlight.equity_incentive_slot_strategy_backtest import (
    COST_BPS,
    filter_tradable_events,
    load_strict_core_events,
)


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
OUTPUT_PREFIX = "equity_incentive_daily_entry_compare"

MA_WINDOW_DAYS = 200
HOLD_TRADING_DAYS = 189  # ~9 months
ENTRY_SLIPPAGE_BPS = 20.0
LIMITUP_RETRY_DAYS = 5
UNIVERSE = "hs300_csi500"


@dataclass(frozen=True)
class DailyIncentiveSpec:
    name: str
    entry_mode: str  # t_plus_1 | month_end
    slot_weight: float = 0.02
    max_gross: float = 0.15
    require_ma200: bool = True
    ma_window: int = MA_WINDOW_DAYS
    hold_trading_days: int = HOLD_TRADING_DAYS
    base_cost_bps: float = COST_BPS
    entry_slippage_bps: float = ENTRY_SLIPPAGE_BPS
    limitup_retry_days: int = LIMITUP_RETRY_DAYS



def _build_ohlc_panels(
    stock_panels: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DatetimeIndex]:
    close, pct, _ = build_daily_close_panels(stock_panels)
    calendar = close.index
    open_ = pd.DataFrame(index=calendar)
    for symbol, frame in stock_panels.items():
        if "开盘" in frame.columns:
            open_[symbol] = frame["开盘"].astype(float).reindex(calendar)
        else:
            open_[symbol] = close[symbol].shift(1)
    return close, open_, pct, calendar


def load_daily_panels(symbols: list[str]) -> dict[str, pd.DataFrame]:
    stock_panels = load_stock_daily_panels(symbols)
    close, open_, pct, calendar = _build_ohlc_panels(stock_panels)
    return {
        "calendar": calendar,
        "open": open_,
        "close": close,
        "pct": pct,
    }


def _is_limit_up(symbol: str, date: pd.Timestamp, panels: dict[str, pd.DataFrame]) -> bool:
    if symbol not in panels["pct"].columns or date not in panels["pct"].index:
        return True
    pct = panels["pct"].at[date, symbol]
    return is_limit_up_row(pct, symbol)


def _above_ma200(symbol: str, signal_date: pd.Timestamp, panels: dict[str, pd.DataFrame], window: int) -> bool:
    """MA filter on signal_date close (day before entry for T+1 / month-end)."""
    close = panels["close"]
    if symbol not in close.columns:
        return False
    series = close[symbol].dropna()
    if signal_date not in series.index:
        return False
    loc = series.index.get_loc(signal_date)
    if isinstance(loc, slice):
        loc = loc.start
    if loc < window - 1:
        return False
    window_closes = series.iloc[loc - window + 1 : loc + 1]
    ma = float(window_closes.mean())
    px = float(series.iloc[loc])
    return px > ma


def _first_trading_after(calendar: pd.DatetimeIndex, ann_date: pd.Timestamp) -> int | None:
    pos = calendar.searchsorted(ann_date.normalize(), side="right")
    if pos >= len(calendar):
        return None
    return int(pos)


def _month_end_trading_pos(calendar: pd.DatetimeIndex, ann_time: pd.Timestamp) -> int | None:
    month_end = ann_time.to_period("M").to_timestamp("M")
    pos = calendar.searchsorted(month_end, side="left")
    if pos >= len(calendar):
        return None
    while pos + 1 < len(calendar) and calendar[pos].to_period("M") == calendar[pos + 1].to_period("M"):
        pos += 1
    if calendar[pos].to_period("M") != ann_time.to_period("M"):
        return None
    return int(pos)


def _resolve_entry(
    symbol: str,
    ann_time: pd.Timestamp,
    mode: str,
    spec: DailyIncentiveSpec,
    panels: dict[str, pd.DataFrame],
) -> dict:
    calendar: pd.DatetimeIndex = panels["calendar"]
    if mode == "t_plus_1":
        start_pos = _first_trading_after(calendar, ann_time.normalize())
        if start_pos is None:
            return {"status": "no_calendar"}
        candidates = range(start_pos, min(start_pos + spec.limitup_retry_days, len(calendar)))
    elif mode == "month_end":
        me_pos = _month_end_trading_pos(calendar, ann_time)
        if me_pos is None:
            return {"status": "no_month_end"}
        candidates = [me_pos]
    else:
        raise ValueError(mode)

    for pos in candidates:
        entry_date = calendar[pos]
        if mode == "t_plus_1":
            signal_date = calendar[pos - 1] if pos > 0 else None
        else:
            signal_date = calendar[pos - 1] if pos > 0 else None
        if signal_date is None:
            continue
        if spec.require_ma200 and not _above_ma200(symbol, signal_date, panels, spec.ma_window):
            return {
                "status": "ma200_reject",
                "entry_date": entry_date,
                "signal_date": signal_date,
            }
        if _is_limit_up(symbol, entry_date, panels):
            continue
        exit_pos = pos + spec.hold_trading_days
        if exit_pos >= len(calendar):
            return {"status": "short_calendar", "entry_date": entry_date}
        return {
            "status": "entered",
            "entry_date": entry_date,
            "exit_date": calendar[exit_pos],
            "signal_date": signal_date,
            "entry_pos": pos,
            "exit_pos": exit_pos,
        }
    return {"status": "limitup_skip"}


def build_entry_table(events: pd.DataFrame, spec: DailyIncentiveSpec, panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for _, event in events.iterrows():
        symbol = str(event["symbol"]).zfill(6)
        ann_time = pd.Timestamp(event["announcement_time"])
        resolved = _resolve_entry(symbol, ann_time, spec.entry_mode, spec, panels)
        rows.append(
            {
                "symbol": symbol,
                "announcement_time": ann_time,
                "entry_mode": spec.entry_mode,
                **resolved,
            }
        )
    return pd.DataFrame(rows)


@dataclass
class DailyPosition:
    symbol: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    weight: float
    entry_pos: int
    exit_pos: int


def _scale_daily_positions(positions: list[DailyPosition], max_gross: float) -> list[DailyPosition]:
    gross = sum(p.weight for p in positions)
    if gross <= max_gross + 1e-12:
        return positions
    factor = max_gross / gross
    for pos in positions:
        pos.weight *= factor
    return positions


def run_daily_incremental(
    spec: DailyIncentiveSpec,
    entries: pd.DataFrame,
    panels: dict[str, pd.DataFrame],
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    calendar = panels["calendar"]
    close = panels["close"]
    open_ = panels["open"]
    pct = panels["pct"]

    tradable = entries[entries["status"] == "entered"].copy()
    entries_by_pos: dict[int, list[dict]] = {}
    for _, row in tradable.iterrows():
        entries_by_pos.setdefault(int(row["entry_pos"]), []).append(row.to_dict())

    positions: list[DailyPosition] = []
    returns: list[float] = []
    index: list[pd.Timestamp] = []
    diag_rows: list[dict] = []
    base_cost = spec.base_cost_bps / 10_000.0
    slip_cost = spec.entry_slippage_bps / 10_000.0

    for i, date in enumerate(calendar):
        if i == 0:
            continue
        day_return = 0.0
        entry_turnover = 0.0
        exit_turnover = 0.0

        exit_turnover = sum(pos.weight for pos in positions if pos.exit_pos == i)
        positions = [pos for pos in positions if i <= pos.exit_pos]

        for row in entries_by_pos.get(i, []):
            symbol = row["symbol"]
            if any(p.symbol == symbol for p in positions):
                continue
            if symbol not in close.columns:
                continue
            positions.append(
                DailyPosition(
                    symbol=symbol,
                    entry_date=date,
                    exit_date=row["exit_date"],
                    weight=spec.slot_weight,
                    entry_pos=int(row["entry_pos"]),
                    exit_pos=int(row["exit_pos"]),
                )
            )
            entry_turnover += spec.slot_weight

        positions = _scale_daily_positions(positions, spec.max_gross)

        for pos in positions:
            sym = pos.symbol
            if sym not in close.columns:
                continue
            if i == pos.entry_pos:
                if spec.entry_mode == "t_plus_1":
                    o = open_.at[date, sym]
                    c = close.at[date, sym]
                    if pd.isna(o) or pd.isna(c) or o <= 0:
                        continue
                    day_return += pos.weight * float(c / o - 1.0)
            elif i > pos.entry_pos:
                if sym in pct.columns and pd.notna(pct.at[date, sym]):
                    day_return += pos.weight * float(pct.at[date, sym]) / 100.0

        trade_cost = entry_turnover * base_cost + exit_turnover * base_cost
        if spec.entry_mode == "t_plus_1":
            trade_cost += entry_turnover * slip_cost
        day_return -= trade_cost

        returns.append(day_return)
        index.append(date)
        diag_rows.append(
            {
                "date": date,
                "gross_weight": sum(p.weight for p in positions),
                "positions": len(positions),
                "entry_turnover": entry_turnover,
                "exit_turnover": exit_turnover,
            }
        )

    ret_series = pd.Series(returns, index=index, name="daily_return")
    holdings = pd.DataFrame(diag_rows)
    return ret_series, holdings, tradable


def _entry_diagnostics(entries: pd.DataFrame) -> dict:
    total = len(entries)
    entered = int((entries["status"] == "entered").sum())
    return {
        "total_events": total,
        "entered": entered,
        "enter_rate": float(entered / total) if total else np.nan,
        "ma200_reject": int((entries["status"] == "ma200_reject").sum()),
        "limitup_skip": int((entries["status"] == "limitup_skip").sum()),
        "no_calendar": int(entries["status"].isin(["no_calendar", "no_month_end", "short_calendar"]).sum()),
    }


def _plot_comparison(nav_frame: pd.DataFrame, path: Path) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    for col in nav_frame.columns:
        axes[0].plot(nav_frame.index, nav_frame[col], label=col, linewidth=1.3)
    axes[0].set_title("Equity incentive entry timing (daily, MA200, limit-up skip)")
    axes[0].set_ylabel("NAV")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.28)

    base = nav_frame.iloc[:, 0]
    for col in nav_frame.columns[1:]:
        axes[1].plot(nav_frame.index, nav_frame[col] / base, label=f"{col} / {nav_frame.columns[0]}", linewidth=1.1)
    axes[1].axhline(1.0, color="black", linewidth=0.8, alpha=0.4)
    axes[1].set_ylabel("Relative NAV")
    axes[1].set_xlabel("Date")
    axes[1].legend(fontsize=7)
    axes[1].grid(True, alpha=0.28)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run_compare() -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)
    events = load_strict_core_events(UNIVERSE)
    symbols = sorted(events["symbol"].astype(str).str.zfill(6).unique())
    print(f"Loading daily panels for {len(symbols)} symbols...")
    panels = load_daily_panels(symbols)
    price_symbols = set(panels["close"].columns)
    events = filter_tradable_events(events, price_symbols)

    specs = [
        DailyIncentiveSpec("t_plus_1_open_ma200", entry_mode="t_plus_1", require_ma200=True),
        DailyIncentiveSpec("month_end_close_ma200", entry_mode="month_end", require_ma200=True),
        DailyIncentiveSpec("t_plus_1_open_no_ma200", entry_mode="t_plus_1", require_ma200=False),
        DailyIncentiveSpec("month_end_close_no_ma200", entry_mode="month_end", require_ma200=False),
    ]

    metrics_rows: list[dict] = []
    nav_map: dict[str, pd.Series] = {}
    payload_variants: dict[str, dict] = {}

    for spec in specs:
        print(f"\n=== {spec.name} ===")
        entries = build_entry_table(events, spec, panels)
        entries.to_csv(RESULTS / f"{OUTPUT_PREFIX}_{spec.name}_entries.csv", index=False)
        diag = _entry_diagnostics(entries)
        print(diag)

        daily_ret, holdings, _ = run_daily_incremental(spec, entries, panels)
        nav = (1.0 + daily_ret.fillna(0.0)).cumprod()
        nav_map[spec.name] = nav
        holdings.to_csv(RESULTS / f"{OUTPUT_PREFIX}_{spec.name}_holdings_daily.csv", index=False)

        m = _metrics(nav, daily_ret.fillna(0.0))
        years = (nav.index[-1] - nav.index[0]).days / 365.25
        avg_gross = float(holdings["gross_weight"].mean())
        turnover_per_year = float((holdings["entry_turnover"] + holdings["exit_turnover"]).sum() / years) if years > 0 else np.nan
        row = {
            "variant": spec.name,
            "entry_mode": spec.entry_mode,
            "require_ma200": spec.require_ma200,
            **m,
            "avg_gross": avg_gross,
            "avg_positions": float(holdings["positions"].mean()),
            "turnover_per_year": turnover_per_year,
            **diag,
        }
        metrics_rows.append(row)
        payload_variants[spec.name] = {"metrics": row, "entry_diagnostics": diag}

    metrics_df = pd.DataFrame(metrics_rows).sort_values(["sharpe", "cagr"], ascending=False)
    metrics_csv = RESULTS / f"{OUTPUT_PREFIX}_metrics.csv"
    metrics_df.to_csv(metrics_csv, index=False)

    nav_frame = pd.DataFrame(nav_map).sort_index()
    overlap_start = nav_frame.first_valid_index()
    nav_frame = nav_frame.loc[overlap_start:]
    start = nav_frame.index.min()
    nav_rebased = nav_frame.div(nav_frame.loc[start])
    nav_rebased.to_csv(RESULTS / f"{OUTPUT_PREFIX}_nav.csv")
    plot_path = RESULTS / f"{OUTPUT_PREFIX}_nav.png"
    _plot_comparison(nav_rebased, plot_path)

    best = metrics_df.iloc[0].to_dict()
    t1 = metrics_df[metrics_df["entry_mode"] == "t_plus_1"]
    me = metrics_df[metrics_df["entry_mode"] == "month_end"]
    best_t1 = t1.sort_values("sharpe", ascending=False).iloc[0]
    best_me = me.sort_values("sharpe", ascending=False).iloc[0]

    recommendation = {
        "preferred_entry": str(best_t1["variant"]) if float(best_t1["sharpe"]) >= float(best_me["sharpe"]) else str(best_me["variant"]),
        "t_plus_1_best": best_t1.to_dict(),
        "month_end_best": best_me.to_dict(),
        "rationale": (
            "Compare Sharpe/CAGR after MA200 filter, limit-up skip, "
            f"{ENTRY_SLIPPAGE_BPS:.0f}bps T+1 slippage, {COST_BPS:.0f}bps trade cost."
        ),
    }

    payload = {
        "spec": {
            "universe": UNIVERSE,
            "slot_weight": 0.02,
            "max_gross": 0.15,
            "hold_trading_days": HOLD_TRADING_DAYS,
            "ma_window_days": MA_WINDOW_DAYS,
            "base_cost_bps": COST_BPS,
            "entry_slippage_bps_t_plus_1": ENTRY_SLIPPAGE_BPS,
            "limitup_retry_days": LIMITUP_RETRY_DAYS,
            "symbols_with_daily": len(price_symbols),
            "events": len(events),
        },
        "variants": payload_variants,
        "ranking": metrics_df.to_dict(orient="records"),
        "recommendation": recommendation,
        "outputs": {
            "metrics_csv": str(metrics_csv),
            "nav_csv": str(RESULTS / f"{OUTPUT_PREFIX}_nav.csv"),
            "plot": str(plot_path),
        },
    }
    summary_path = RESULTS / f"{OUTPUT_PREFIX}_summary.json"
    with summary_path.open("w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    print("\n=== Ranking ===")
    print(metrics_df.to_string(index=False))
    print(f"\nRecommendation: {recommendation['preferred_entry']}")
    return payload


if __name__ == "__main__":
    run_compare()
