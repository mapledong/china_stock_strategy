"""Layered China composite: AH base + industry sleeve + incremental equity incentive.

Architecture (user-specified):
- AH low-premium Top10 as the core anchor sleeve.
- Industry exposure from either dividend/chinext pair rotation or ETF sector Top2.
- Equity incentive: each strict-core event enters at 1–3% weight (no 20-slot skip bias);
  gross incentive exposure is capped and scaled dynamically when over budget.

Outputs under results/china_layered_composite_*.
"""

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

from qtlight.equity_incentive_hs300_event_study import _entry_month
from qtlight.equity_incentive_slot_strategy_backtest import (
    COST_BPS,
    Position,
    _position_return_since_entry,
    filter_tradable_events,
    load_cached_benchmark,
    load_cached_monthly_prices,
    load_strict_core_events,
)


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
OUTPUT_PREFIX = "china_layered_composite"
CONSERVATIVE_OUTPUT_PREFIX = "china_layered_composite_conservative"

AH_NAV_PATH = RESULTS / "ah_tushare_equity.csv"
ETF_NAV_PATH = RESULTS / "tushare_momentum" / "tushare_6m_skip_1m_daily_nav.csv"
DIV_NAV_PATH = RESULTS / "dividend_chinext_momentum" / "pair_best_strategy_daily_nav.csv"


@dataclass(frozen=True)
class IncrementalIncentiveSpec:
    slot_weight: float = 0.02
    hold_months: int = 9
    max_gross: float = 0.15
    scale_mode: str = "proportional"  # proportional | trim_worst
    universe: str = "hs300_csi500"
    require_ma200_above: bool = False
    ma_window_months: int = 10  # monthly bars ≈ MA200 on daily (~10 months)


@dataclass(frozen=True)
class CompositeSpec:
    name: str
    ah_weight: float
    industry_weight: float
    industry_source: str  # div_chinext | etf_top2
    incentive: IncrementalIncentiveSpec


CONSERVATIVE_SPEC = CompositeSpec(
    name="conservative_AH50_DivChi30_Inc2pct",
    ah_weight=0.50,
    industry_weight=0.30,
    industry_source="div_chinext",
    incentive=IncrementalIncentiveSpec(slot_weight=0.02, max_gross=0.15, scale_mode="proportional"),
)


def _metrics(nav: pd.Series, returns: pd.Series) -> dict[str, float | str]:
    active = nav.dropna()
    if len(active) < 2:
        return {}
    years = (active.index[-1] - active.index[0]).days / 365.25
    cagr = float((active.iloc[-1] / active.iloc[0]) ** (1.0 / years) - 1.0)
    ann_vol = float(returns.loc[active.index].std() * math.sqrt(252))
    drawdown = active / active.cummax() - 1.0
    max_drawdown = float(drawdown.min())
    monthly_returns = active.resample("ME").last().pct_change().dropna()
    return {
        "start": active.index.min().date().isoformat(),
        "end": active.index.max().date().isoformat(),
        "cagr": cagr,
        "ann_vol": ann_vol,
        "sharpe": float(cagr / ann_vol) if ann_vol > 0 else np.nan,
        "max_drawdown": max_drawdown,
        "calmar": float(cagr / abs(max_drawdown)) if max_drawdown < 0 else np.nan,
        "final_nav": float(active.iloc[-1] / active.iloc[0]),
        "monthly_win_rate": float((monthly_returns > 0).mean()) if len(monthly_returns) else np.nan,
    }


def _prepare_incentive_signals(events: pd.DataFrame, monthly_index: pd.DatetimeIndex) -> pd.DataFrame:
    rows = []
    for _, event in events.iterrows():
        entry = _entry_month(monthly_index, pd.Timestamp(event["announcement_time"]))
        if entry is None:
            continue
        rows.append(
            {
                "symbol": event["symbol"],
                "announcement_time": event["announcement_time"],
                "entry_month": entry,
            }
        )
    if not rows:
        return pd.DataFrame()
    signals = pd.DataFrame(rows).sort_values(["entry_month", "announcement_time", "symbol"])
    return signals.drop_duplicates(["symbol", "entry_month"], keep="first")


def build_price_above_ma(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    ma = prices.rolling(window, min_periods=window).mean()
    return prices > ma


def filter_signals_ma200(
    signals: pd.DataFrame,
    prices: pd.DataFrame,
    window: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keep signals where month-end close is above MA (monthly window ≈ daily MA200)."""
    above = build_price_above_ma(prices, window)
    rows = []
    diag = []
    for _, row in signals.iterrows():
        month = pd.Timestamp(row["entry_month"])
        symbol = row["symbol"]
        flag = None
        if symbol in above.columns and month in above.index:
            raw = above.at[month, symbol]
            flag = bool(raw) if pd.notna(raw) else None
        passed = flag is True
        diag.append(
            {
                "symbol": symbol,
                "entry_month": month,
                "announcement_time": row["announcement_time"],
                "above_ma": flag,
                "passed": passed,
            }
        )
        if passed:
            rows.append(row.to_dict())
    filtered = pd.DataFrame(rows)
    if not filtered.empty:
        filtered = filtered.sort_values(["entry_month", "announcement_time", "symbol"])
    return filtered, pd.DataFrame(diag)


def _scale_positions(positions: list[Position], spec: IncrementalIncentiveSpec, month: pd.Timestamp, monthly_returns: pd.DataFrame) -> list[Position]:
    gross = sum(p.weight for p in positions)
    if gross <= spec.max_gross + 1e-12:
        return positions
    if spec.scale_mode == "proportional":
        factor = spec.max_gross / gross
        for pos in positions:
            pos.weight *= factor
        return positions
    if spec.scale_mode == "trim_worst":
        trimmed = list(positions)
        while sum(p.weight for p in trimmed) > spec.max_gross + 1e-12 and trimmed:
            worst_idx = int(
                min(
                    range(len(trimmed)),
                    key=lambda i: _position_return_since_entry(trimmed[i], month, monthly_returns),
                )
            )
            trimmed.pop(worst_idx)
        gross = sum(p.weight for p in trimmed)
        if gross > spec.max_gross + 1e-12:
            factor = spec.max_gross / gross
            for pos in trimmed:
                pos.weight *= factor
        return trimmed
    raise ValueError(f"Unknown scale_mode: {spec.scale_mode}")


def run_incremental_incentive(
    spec: IncrementalIncentiveSpec,
    signals: pd.DataFrame,
    monthly_returns: pd.DataFrame,
    cost_bps: float = COST_BPS,
) -> tuple[pd.Series, pd.DataFrame]:
    """All events enter; no max-slot skip. Scale dynamically when gross > max_gross."""
    months = monthly_returns.index
    positions: list[Position] = []
    strategy_returns: list[float] = []
    holding_rows: list[dict] = []
    signals_by_month = {
        month: group.sort_values(["announcement_time", "symbol"])
        for month, group in signals.groupby("entry_month")
    }
    cost_rate = cost_bps / 10_000.0

    for month in months[:-1]:
        month_turnover = 0.0
        remaining: list[Position] = []
        for pos in positions:
            if month >= pos.exit_month:
                month_turnover += pos.weight
                continue
            remaining.append(pos)
        positions = remaining

        for _, signal in signals_by_month.get(month, pd.DataFrame()).iterrows():
            symbol = signal["symbol"]
            if symbol not in monthly_returns.columns:
                continue
            if any(p.symbol == symbol for p in positions):
                continue
            if pd.isna(monthly_returns.at[month, symbol]):
                continue
            exit_month = month + pd.offsets.MonthEnd(spec.hold_months)
            positions.append(
                Position(
                    symbol=symbol,
                    entry_month=month,
                    exit_month=exit_month,
                    weight=spec.slot_weight,
                    event_time=pd.Timestamp(signal["announcement_time"]),
                )
            )
            month_turnover += spec.slot_weight

        positions = _scale_positions(positions, spec, month, monthly_returns)
        gross_weight = sum(pos.weight for pos in positions)

        month_return = 0.0
        next_month = months[months.get_loc(month) + 1]
        for pos in positions:
            if next_month > pos.exit_month:
                continue
            stock_ret = monthly_returns.at[next_month, pos.symbol]
            if pd.isna(stock_ret):
                continue
            month_return += pos.weight * float(stock_ret)
        month_return -= month_turnover * cost_rate
        strategy_returns.append(month_return)

        holding_rows.append(
            {
                "month": month,
                "gross_weight": gross_weight,
                "positions": len(positions),
                "turnover": month_turnover,
                "symbols": ",".join(sorted({p.symbol for p in positions})),
            }
        )

    ret_series = pd.Series(strategy_returns, index=months[:-1], name="incentive_return")
    holdings = pd.DataFrame(holding_rows)
    return ret_series, holdings


def _incentive_inputs(spec: IncrementalIncentiveSpec) -> tuple[pd.DataFrame, pd.DataFrame]:
    events = load_strict_core_events(spec.universe)
    symbols = sorted(events["symbol"].unique())
    prices = load_cached_monthly_prices(symbols)
    price_symbols = set(prices.columns)
    events = filter_tradable_events(events, price_symbols)
    monthly_returns = prices.pct_change(fill_method=None)
    signals = _prepare_incentive_signals(events, monthly_returns.index)
    if spec.require_ma200_above:
        signals, _ = filter_signals_ma200(signals, prices, spec.ma_window_months)
    return signals, monthly_returns


def incentive_positions_through_month(
    spec: IncrementalIncentiveSpec,
    through_month: pd.Timestamp,
) -> list[dict]:
    """Replay incremental incentive through a calendar month-end (matches backtest holdings)."""
    signals, monthly_returns = _incentive_inputs(spec)
    if monthly_returns.empty:
        return []
    through_month = pd.Timestamp(through_month).to_period("M").to_timestamp("M")
    months = monthly_returns.index
    positions: list[Position] = []
    signals_by_month = {
        month: group.sort_values(["announcement_time", "symbol"])
        for month, group in signals.groupby("entry_month")
    }

    for month in months[:-1]:
        remaining: list[Position] = []
        for pos in positions:
            if month >= pos.exit_month:
                continue
            remaining.append(pos)
        positions = remaining

        for _, signal in signals_by_month.get(month, pd.DataFrame()).iterrows():
            symbol = str(signal["symbol"]).zfill(6)
            if symbol not in monthly_returns.columns:
                continue
            if any(p.symbol == symbol for p in positions):
                continue
            if pd.isna(monthly_returns.at[month, symbol]):
                continue
            exit_month = month + pd.offsets.MonthEnd(spec.hold_months)
            positions.append(
                Position(
                    symbol=symbol,
                    entry_month=month,
                    exit_month=exit_month,
                    weight=spec.slot_weight,
                    event_time=pd.Timestamp(signal["announcement_time"]),
                )
            )

        positions = _scale_positions(positions, spec, month, monthly_returns)
        if month >= through_month:
            break

    rows: list[dict] = []
    for pos in positions:
        rows.append(
            {
                "symbol": str(pos.symbol).zfill(6),
                "weight": float(pos.weight),
                "entry_month": pd.Timestamp(pos.entry_month).date().isoformat(),
                "exit_month": pd.Timestamp(pos.exit_month).date().isoformat(),
            }
        )
    return rows


def project_incentive_month_end(
    spec: IncrementalIncentiveSpec,
    open_positions: list[dict],
    signal_date: pd.Timestamp,
) -> dict:
    signal_month = pd.Timestamp(signal_date).to_period("M").to_timestamp("M")
    signals, _ = _incentive_inputs(spec)
    current_keys = {p["symbol"] for p in open_positions}

    entry_rows: list[dict] = []
    if not signals.empty:
        pending = signals[signals["entry_month"] == signal_month]
        for _, row in pending.iterrows():
            sym = str(row["symbol"]).zfill(6)
            if sym in current_keys:
                continue
            entry_rows.append(
                {
                    "symbol": sym,
                    "weight": spec.slot_weight,
                    "trade_date": signal_month.date().isoformat(),
                    "reason": "monthly_incremental",
                    "status": "pending",
                }
            )

    exit_rows: list[dict] = []
    for pos in open_positions:
        exit_month = pd.Timestamp(pos["exit_month"]).to_period("M").to_timestamp("M")
        if exit_month != signal_month:
            continue
        exit_rows.append(
            {
                "symbol": pos["symbol"],
                "weight": pos["weight"],
                "trade_date": signal_month.date().isoformat(),
                "reason": "expiry",
                "status": "scheduled",
            }
        )

    return {
        "unchanged": not entry_rows and not exit_rows,
        "signal_date": signal_date.date().isoformat(),
        "entries": entry_rows,
        "exits": exit_rows,
        "note_zh": "月频增量：公告后首个可交易月纳入，持有 9 个月；总敞口超 15% 时等比压缩。",
        "note_en": "Monthly incremental: first tradable month after announcement, 9M hold; scale to 15% cap.",
    }


def _load_daily_sleeves() -> pd.DataFrame:
    missing = [p for p in (AH_NAV_PATH, ETF_NAV_PATH, DIV_NAV_PATH) if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing inputs: "
            + ", ".join(str(p) for p in missing)
            + ". Run ah_tushare_backtest, etf_momentum_tushare_backtest, dividend_chinext_momentum_research."
        )

    ah = pd.read_csv(AH_NAV_PATH, parse_dates=["date"]).set_index("date").sort_index()
    etf = pd.read_csv(ETF_NAV_PATH, index_col=0, parse_dates=True).sort_index()
    div = pd.read_csv(DIV_NAV_PATH, index_col=0, parse_dates=True).sort_index()
    div_col = "strategy_nav" if "strategy_nav" in div.columns else div.columns[-1]

    frame = pd.DataFrame(
        {
            "ah_nav_raw": ah["AH_low_premium_top10_tushare"],
            "etf_nav_raw": etf["strategy_nav"],
            "div_nav_raw": div[div_col],
            "hs300_nav_raw": etf["hs300_nav"],
        }
    ).dropna()
    start = frame.index.min()
    for col in ["ah_nav_raw", "etf_nav_raw", "div_nav_raw", "hs300_nav_raw"]:
        rebased = f"{col.replace('_raw', '')}"
        frame[rebased] = frame[col] / frame.loc[start, col]
    return frame


def _build_incentive_monthly_nav(
    spec: IncrementalIncentiveSpec,
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    events = load_strict_core_events(spec.universe)
    symbols = sorted(events["symbol"].unique())
    prices = load_cached_monthly_prices(symbols)
    price_symbols = set(prices.columns)
    events = filter_tradable_events(events, price_symbols)
    monthly_returns = prices.pct_change(fill_method=None)
    signals = _prepare_incentive_signals(events, monthly_returns.index)
    if signals.empty:
        raise RuntimeError("No tradable incentive signals found.")
    filter_diag = pd.DataFrame()
    if spec.require_ma200_above:
        signals, filter_diag = filter_signals_ma200(signals, prices, spec.ma_window_months)
        if signals.empty:
            raise RuntimeError("No incentive signals passed MA200 filter.")
    returns, holdings = run_incremental_incentive(spec, signals, monthly_returns)
    holdings["slot_weight"] = spec.slot_weight
    holdings["max_gross"] = spec.max_gross
    holdings["scale_mode"] = spec.scale_mode
    holdings["require_ma200_above"] = spec.require_ma200_above
    holdings["ma_window_months"] = spec.ma_window_months
    return returns, holdings, filter_diag


def _apply_monthly_overlay(daily_returns: pd.Series, monthly_overlay: pd.Series) -> pd.Series:
    """Add monthly sleeve return on the last available trading day of each month."""
    out = daily_returns.copy()
    for month_end, overlay_ret in monthly_overlay.dropna().items():
        period = out.index[(out.index.year == month_end.year) & (out.index.month == month_end.month)]
        if len(period) == 0:
            continue
        out.loc[period[-1]] = out.loc[period[-1]] + float(overlay_ret)
    return out


def run_composite(
    spec: CompositeSpec,
    daily: pd.DataFrame,
    incentive_monthly_returns: pd.Series,
) -> pd.DataFrame:
    industry_col = "div_nav" if spec.industry_source == "div_chinext" else "etf_nav"
    out = daily[["ah_nav", "etf_nav", "div_nav", "hs300_nav"]].copy()
    out["ah_return"] = out["ah_nav"].pct_change(fill_method=None).fillna(0.0)
    out["industry_return"] = daily[industry_col].pct_change(fill_method=None).fillna(0.0)
    out["hs300_return"] = out["hs300_nav"].pct_change(fill_method=None).fillna(0.0)

    # Incentive returns are absolute portfolio weights (e.g. 2% per name, capped at max_gross).
    incentive_nav = (1.0 + incentive_monthly_returns).cumprod()
    out["incentive_nav"] = incentive_nav.reindex(out.index, method="ffill").ffill()

    base_daily = spec.ah_weight * out["ah_return"] + spec.industry_weight * out["industry_return"]
    out["combo_return"] = _apply_monthly_overlay(base_daily, incentive_monthly_returns)
    out["combo_nav"] = (1.0 + out["combo_return"]).cumprod()
    out["combo_drawdown"] = out["combo_nav"] / out["combo_nav"].cummax() - 1.0
    out["strategy"] = spec.name
    out["ah_weight"] = spec.ah_weight
    out["industry_weight"] = spec.industry_weight
    out["industry_source"] = spec.industry_source
    out["incentive_slot_weight"] = spec.incentive.slot_weight
    out["incentive_max_gross"] = spec.incentive.max_gross
    out["incentive_scale_mode"] = spec.incentive.scale_mode
    return out


def _scan_specs() -> list[CompositeSpec]:
    specs: list[CompositeSpec] = []
    for ah_w in (0.60, 0.65, 0.70, 0.75):
        for ind_w in (0.15, 0.20, 0.25):
            if ah_w + ind_w > 0.90:
                continue
            for industry in ("div_chinext", "etf_top2"):
                for slot_w in (0.01, 0.02, 0.03):
                    for max_gross in (0.10, 0.15, 0.20):
                        if slot_w * 30 < max_gross * 0.5:
                            continue
                        for scale_mode in ("proportional", "trim_worst"):
                            tag = (
                                f"AH{int(ah_w*100)}_"
                                f"{'DivChi' if industry == 'div_chinext' else 'ETF'}_{int(ind_w*100)}_"
                                f"Inc{int(slot_w*100)}pct_cap{int(max_gross*100)}_{scale_mode[:4]}"
                            )
                            specs.append(
                                CompositeSpec(
                                    name=tag,
                                    ah_weight=ah_w,
                                    industry_weight=ind_w,
                                    industry_source=industry,
                                    incentive=IncrementalIncentiveSpec(
                                        slot_weight=slot_w,
                                        max_gross=max_gross,
                                        scale_mode=scale_mode,
                                    ),
                                )
                            )
    return specs


def _period_return_table(daily: pd.DataFrame, freq: str) -> pd.DataFrame:
    industry_col = "div_nav" if daily["industry_source"].iloc[0] == "div_chinext" else "etf_nav"
    nav = daily[["combo_nav", "ah_nav", industry_col, "incentive_nav", "hs300_nav"]]
    returns = nav.resample(freq).last().pct_change().dropna()
    returns = returns.rename(
        columns={
            "combo_nav": "combo_return",
            "ah_nav": "ah_return",
            industry_col: "industry_return",
            "incentive_nav": "incentive_return",
            "hs300_nav": "hs300_return",
        }
    )
    returns["combo_excess_vs_hs300"] = returns["combo_return"] - returns["hs300_return"]
    returns["combo_win_vs_hs300"] = returns["combo_excess_vs_hs300"] > 0
    if freq == "YE":
        returns.index = returns.index.year
        returns.index.name = "year"
    else:
        returns.index = returns.index.strftime("%Y-%m")
        returns.index.name = "month"
    return returns


def _calendar_stability_summary(annual: pd.DataFrame, monthly: pd.DataFrame) -> dict:
    return {
        "years": int(len(annual)),
        "annual_outperform_years": int(annual["combo_win_vs_hs300"].sum()),
        "annual_outperform_rate": float(annual["combo_win_vs_hs300"].mean()),
        "annual_positive_years": int((annual["combo_return"] > 0).sum()),
        "annual_positive_rate": float((annual["combo_return"] > 0).mean()),
        "months": int(len(monthly)),
        "monthly_outperform_months": int(monthly["combo_win_vs_hs300"].sum()),
        "monthly_outperform_rate": float(monthly["combo_win_vs_hs300"].mean()),
        "monthly_positive_months": int((monthly["combo_return"] > 0).sum()),
        "monthly_positive_rate": float((monthly["combo_return"] > 0).mean()),
        "average_monthly_return": float(monthly["combo_return"].mean()),
        "average_monthly_excess_vs_hs300": float(monthly["combo_excess_vs_hs300"].mean()),
        "average_annual_excess_vs_hs300": float(annual["combo_excess_vs_hs300"].mean()),
        "worst_month_combo_return": float(monthly["combo_return"].min()),
        "worst_year_combo_return": float(annual["combo_return"].min()),
        "longest_monthly_outperform_streak": int(
            _longest_true_streak(monthly["combo_win_vs_hs300"].tolist())
        ),
        "longest_monthly_underperform_streak": int(
            _longest_true_streak((~monthly["combo_win_vs_hs300"]).tolist())
        ),
    }


def _longest_true_streak(flags: list[bool]) -> int:
    best = 0
    current = 0
    for flag in flags:
        if flag:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _save_return_calendar_plots(
    monthly: pd.DataFrame,
    annual: pd.DataFrame,
    strategy_name: str,
    path: Path,
) -> None:
    month_index = pd.PeriodIndex(monthly.index, freq="M")
    monthly_work = monthly.copy()
    monthly_work["year"] = month_index.year
    monthly_work["month_num"] = month_index.month

    excess_pivot = monthly_work.pivot(index="year", columns="month_num", values="combo_excess_vs_hs300")
    win_pivot = monthly_work.pivot(index="year", columns="month_num", values="combo_win_vs_hs300")

    plt.style.use("seaborn-v0_8-whitegrid")
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.5, 1.5, 1.1], hspace=0.32)

    ax0 = fig.add_subplot(gs[0])
    vmax = max(0.08, float(np.nanmax(np.abs(excess_pivot.values))))
    im0 = ax0.imshow(excess_pivot.values, aspect="auto", cmap="RdYlGn", vmin=-vmax, vmax=vmax)
    ax0.set_title(f"Monthly excess return vs CSI300 — {strategy_name}")
    ax0.set_yticks(range(len(excess_pivot.index)))
    ax0.set_yticklabels(excess_pivot.index.astype(str))
    ax0.set_xticks(range(12))
    ax0.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    for i, year in enumerate(excess_pivot.index):
        for j, month_num in enumerate(excess_pivot.columns):
            val = excess_pivot.loc[year, month_num]
            if pd.isna(val):
                continue
            ax0.text(j, i, f"{val * 100:.1f}", ha="center", va="center", fontsize=7, color="black")
    fig.colorbar(im0, ax=ax0, fraction=0.025, pad=0.02, label="Excess return")

    ax1 = fig.add_subplot(gs[1])
    im1 = ax1.imshow(win_pivot.fillna(0).astype(float).values, aspect="auto", cmap="PiYG", vmin=0, vmax=1)
    ax1.set_title("Monthly outperform CSI300 (green = win)")
    ax1.set_yticks(range(len(win_pivot.index)))
    ax1.set_yticklabels(win_pivot.index.astype(str))
    ax1.set_xticks(range(12))
    ax1.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    for i, year in enumerate(win_pivot.index):
        for j, month_num in enumerate(win_pivot.columns):
            val = win_pivot.loc[year, month_num]
            if pd.isna(val):
                continue
            ax1.text(j, i, "W" if bool(val) else "L", ha="center", va="center", fontsize=8, color="black")
    fig.colorbar(im1, ax=ax1, fraction=0.025, pad=0.02, ticks=[0, 1])

    ax2 = fig.add_subplot(gs[2])
    years = annual.index.astype(str)
    width = 0.35
    x = np.arange(len(years))
    ax2.bar(x - width / 2, annual["combo_return"] * 100, width=width, label="Composite", color="#2a6fbb")
    ax2.bar(x + width / 2, annual["hs300_return"] * 100, width=width, label="CSI300", color="#888888")
    ax2.set_xticks(x)
    ax2.set_xticklabels(years, rotation=0)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_ylabel("Return (%)")
    ax2.set_title("Annual returns")
    ax2.legend(loc="upper left", ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _save_plot(best_daily: pd.DataFrame, path: Path) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]})
    plot_cols = {
        "combo_nav": "Layered composite",
        "ah_nav": "AH base",
        "hs300_nav": "CSI300",
    }
    industry_col = "div_nav" if best_daily["industry_source"].iloc[0] == "div_chinext" else "etf_nav"
    plot_cols[industry_col] = "Industry sleeve"
    plot_cols["incentive_nav"] = "Incremental incentive"
    best_daily[list(plot_cols)].rename(columns=plot_cols).plot(ax=axes[0], linewidth=1.3)
    axes[0].set_title(f"Layered composite: {best_daily['strategy'].iloc[0]}")
    axes[0].set_ylabel("NAV")
    axes[0].legend(loc="upper left", fontsize=8)
    axes[0].grid(True, alpha=0.28)

    best_daily["combo_drawdown"].plot(ax=axes[1], label="Composite drawdown", color="C0")
    axes[1].set_ylabel("Drawdown")
    axes[1].set_xlabel("Date")
    axes[1].legend(loc="lower left")
    axes[1].grid(True, alpha=0.28)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def export_return_calendars(daily: pd.DataFrame, label: str | None = None, file_suffix: str = "") -> dict:
    strategy_name = label or str(daily["strategy"].iloc[0])
    suffix = f"_{file_suffix}" if file_suffix else ""
    annual = _period_return_table(daily, "YE")
    monthly = _period_return_table(daily, "ME")
    stability = _calendar_stability_summary(annual, monthly)

    annual_path = RESULTS / f"{OUTPUT_PREFIX}{suffix}_annual_returns_vs_hs300.csv"
    monthly_path = RESULTS / f"{OUTPUT_PREFIX}{suffix}_monthly_returns_vs_hs300.csv"
    calendar_path = RESULTS / f"{OUTPUT_PREFIX}{suffix}_return_calendar.png"
    annual.to_csv(annual_path)
    monthly.to_csv(monthly_path)
    _save_return_calendar_plots(monthly, annual, strategy_name, calendar_path)

    return {
        "strategy": strategy_name,
        "stability": stability,
        "annual_returns": annual.to_dict("index"),
        "outputs": {
            "annual_returns_csv": str(annual_path),
            "monthly_returns_csv": str(monthly_path),
            "return_calendar_png": str(calendar_path),
        },
    }


def analyze_conservative_turnover(start: str = "2018-04-01") -> dict:
    """Estimate portfolio turnover from monthly holdings snapshots."""
    ah_w = CONSERVATIVE_SPEC.ah_weight
    ind_w = CONSERVATIVE_SPEC.industry_weight
    start_ts = pd.Timestamp(start)

    ah = pd.read_csv(RESULTS / "ah_tushare_holdings.csv", parse_dates=["date"])
    ah["symbol"] = ah["pair"].str.extract(r"\((\d{6})/")[0]
    ah = ah[ah["date"] >= start_ts]
    inc = pd.read_csv(RESULTS / f"{CONSERVATIVE_OUTPUT_PREFIX}_incentive_holdings.csv", parse_dates=["month"])
    inc = inc[inc["month"] >= start_ts]
    div = pd.read_csv(DIV_NAV_PATH.parent / "pair_best_strategy_holdings.csv", parse_dates=["date"])
    div = div[div["date"] >= start_ts]
    months = sorted(ah["date"].unique())
    years = (months[-1] - months[0]).days / 365.25

    def ah_target(month: pd.Timestamp) -> dict[str, float]:
        row = ah[ah["date"] == month]
        return {r["symbol"]: ah_w * float(r["weight"]) for _, r in row.iterrows()}

    def ind_target(month: pd.Timestamp) -> dict[str, float]:
        div_day = div[div["date"] <= month]
        if div_day.empty:
            return {}
        return {str(div_day.iloc[-1]["symbol"]): ind_w}

    def inc_target(month: pd.Timestamp) -> dict[str, float]:
        row = inc[inc["month"] == month]
        if row.empty:
            row = inc[inc["month"] <= month].tail(1)
        if row.empty:
            return {}
        row = row.iloc[-1]
        if pd.isna(row["symbols"]) or not str(row["symbols"]).strip():
            return {}
        syms = str(row["symbols"]).split(",")
        per = float(row["gross_weight"]) / len(syms)
        return {s: per for s in syms}

    def build_pw(held_ah: dict[str, float], month: pd.Timestamp) -> dict[tuple[str, str], float]:
        pw: dict[tuple[str, str], float] = {}
        for symbol, weight in held_ah.items():
            pw[("stock", symbol)] = weight
        for symbol, weight in ind_target(month).items():
            pw[("etf", symbol)] = weight
        for symbol, weight in inc_target(month).items():
            pw[("stock", symbol)] = pw.get(("stock", symbol), 0.0) + weight
        pw[("cash", "cash")] = max(0.0, 1.0 - sum(pw.values()))
        return pw

    def simulate(ah_mode: str) -> tuple[float, float, float, float]:
        held_ah: dict[str, float] = {}
        last_q = None
        prev: dict[tuple[str, str], float] | None = None
        total = ah_total = ind_total = inc_total = 0.0
        prev_ah: dict | None = None
        prev_ind: dict | None = None
        prev_inc: dict | None = None
        for month in months:
            tgt = ah_target(month)
            if ah_mode == "monthly":
                held_ah = tgt
            elif ah_mode == "quarterly":
                quarter = pd.Timestamp(month).to_period("Q")
                if last_q != quarter:
                    held_ah = tgt
                    last_q = quarter
            elif ah_mode == "quarterly_buffer":
                quarter = pd.Timestamp(month).to_period("Q")
                if last_q != quarter:
                    top = set(tgt)
                    held_ah = {s: held_ah[s] for s in held_ah if s in top}
                    for symbol in top:
                        if symbol not in held_ah:
                            held_ah[symbol] = tgt[symbol]
                    last_q = quarter
            elif ah_mode == "buffer":
                top = set(tgt)
                held_ah = {s: held_ah[s] for s in held_ah if s in top}
                for symbol in top:
                    if symbol not in held_ah:
                        held_ah[symbol] = tgt[symbol]

            pw = build_pw(held_ah, month)
            ah_pw = {("stock", s): w for s, w in held_ah.items()}
            ind_pw = {("etf", s): w for s, w in ind_target(month).items()}
            inc_pw = {("stock", s): w for s, w in inc_target(month).items()}
            if prev is not None and prev_ah is not None and prev_ind is not None and prev_inc is not None:
                keys = set(prev) | set(pw)
                total += sum(abs(pw.get(k, 0.0) - prev.get(k, 0.0)) for k in keys)
                keys_ah = set(prev_ah) | set(ah_pw)
                ah_total += sum(abs(ah_pw.get(k, 0.0) - prev_ah.get(k, 0.0)) for k in keys_ah)
                keys_ind = set(prev_ind) | set(ind_pw)
                ind_total += sum(abs(ind_pw.get(k, 0.0) - prev_ind.get(k, 0.0)) for k in keys_ind)
                keys_inc = set(prev_inc) | set(inc_pw)
                inc_total += sum(abs(inc_pw.get(k, 0.0) - prev_inc.get(k, 0.0)) for k in keys_inc)
            prev = pw
            prev_ah, prev_ind, prev_inc = ah_pw, ind_pw, inc_pw
        return total / years, ah_total / years, ind_total / years, inc_total / years

    baseline, ah_t, ind_t, inc_t = simulate("monthly")
    scenarios = {
        "monthly_baseline": baseline,
        "ah_quarterly": simulate("quarterly")[0],
        "ah_hold_buffer": simulate("buffer")[0],
        "ah_quarterly_plus_buffer": simulate("quarterly_buffer")[0],
    }
    cost_bps = 30.0
    payload = {
        "start": start,
        "years": years,
        "definition": "Sum of |Δportfolio_weight| per month, annualized (two-sided; matches AH backtest convention).",
        "conservative_spec": {
            "ah_weight": ah_w,
            "industry_weight": ind_w,
            "incentive_slot_weight": CONSERVATIVE_SPEC.incentive.slot_weight,
        },
        "baseline_turnover_per_year": {
            "portfolio": baseline,
            "ah_sleeve": ah_t,
            "industry_etf_sleeve": ind_t,
            "incentive_sleeve": inc_t,
        },
        "reported_full_sleeve_turnover": {
            "ah_tushare": 4.51,
            "dividend_chinext_12m": 1.68,
            "incentive_incremental": float(inc["turnover"].sum() / years),
        },
        "reduction_scenarios_per_year": scenarios,
        "cost_drag_at_30bps": {k: v * cost_bps / 10_000 for k, v in scenarios.items()},
        "target_200pct_note": "Use ah_quarterly_plus_buffer (~202%) or ah_quarterly (~210%) to approach 200% cap.",
    }
    out_path = RESULTS / f"{CONSERVATIVE_OUTPUT_PREFIX}_turnover_analysis.json"
    with out_path.open("w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    payload["output"] = str(out_path)
    return payload


def _enrich_analytics(daily: pd.DataFrame) -> pd.DataFrame:
    out = daily.copy()
    start = out.index.min()
    out["combo_nav_rebased"] = out["combo_nav"] / out.loc[start, "combo_nav"]
    out["hs300_nav_rebased"] = out["hs300_nav"] / out.loc[start, "hs300_nav"]
    out["excess_nav"] = out["combo_nav_rebased"] / out["hs300_nav_rebased"]
    out["excess_return"] = out["combo_return"] - out["hs300_return"]
    out["hs300_drawdown"] = out["hs300_nav_rebased"] / out["hs300_nav_rebased"].cummax() - 1.0
    out["excess_nav_drawdown"] = out["excess_nav"] / out["excess_nav"].cummax() - 1.0
    return out


def _save_nav_excess_drawdown_plot(daily: pd.DataFrame, path: Path, title: str) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True, gridspec_kw={"height_ratios": [2.0, 1.4, 1.4]})

    axes[0].plot(daily.index, daily["combo_nav_rebased"], label="Composite", linewidth=1.5, color="#2a6fbb")
    axes[0].plot(daily.index, daily["hs300_nav_rebased"], label="CSI300", linewidth=1.3, color="#888888", linestyle="--")
    axes[0].set_title(f"{title} — NAV (rebased to 1.0)")
    axes[0].set_ylabel("NAV")
    axes[0].legend(loc="upper left")
    axes[0].grid(True, alpha=0.28)

    axes[1].plot(daily.index, daily["excess_nav"], label="Composite / CSI300", linewidth=1.5, color="#1a8f4a")
    axes[1].axhline(1.0, color="black", linewidth=0.8, alpha=0.5)
    axes[1].set_title("Relative strength vs CSI300 (>1 = outperforming)")
    axes[1].set_ylabel("Excess NAV ratio")
    axes[1].legend(loc="upper left")
    axes[1].grid(True, alpha=0.28)

    axes[2].plot(daily.index, daily["combo_drawdown"], label="Composite drawdown", linewidth=1.2, color="#2a6fbb")
    axes[2].plot(daily.index, daily["hs300_drawdown"], label="CSI300 drawdown", linewidth=1.2, color="#888888")
    axes[2].plot(
        daily.index,
        daily["excess_nav_drawdown"],
        label="Excess NAV drawdown",
        linewidth=1.0,
        color="#1a8f4a",
        linestyle=":",
    )
    axes[2].set_title("Drawdown curves")
    axes[2].set_ylabel("Drawdown")
    axes[2].set_xlabel("Date")
    axes[2].legend(loc="lower left", fontsize=8)
    axes[2].grid(True, alpha=0.28)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run_conservative_compliant() -> dict:
    """Conservative compliance sleeve mix: 50% AH + 30% Div/ChiNext ETF + incremental incentive."""
    RESULTS.mkdir(parents=True, exist_ok=True)
    daily_base = _load_daily_sleeves()
    inc_returns, inc_holdings, _ = _build_incentive_monthly_nav(CONSERVATIVE_SPEC.incentive)
    combo = run_composite(CONSERVATIVE_SPEC, daily_base, inc_returns)
    daily = _enrich_analytics(combo)

    metrics_combo = _metrics(daily["combo_nav_rebased"], daily["combo_return"])
    metrics_hs300 = _metrics(daily["hs300_nav_rebased"], daily["hs300_return"])
    excess_final = float(daily["excess_nav"].iloc[-1])
    years = (daily.index[-1] - daily.index[0]).days / 365.25
    excess_cagr = float(daily["excess_nav"].iloc[-1] ** (1.0 / years) - 1.0) if years > 0 else np.nan

    daily_out = daily[
        [
            "combo_nav_rebased",
            "combo_return",
            "combo_drawdown",
            "excess_nav",
            "excess_return",
            "excess_nav_drawdown",
            "hs300_nav_rebased",
            "hs300_return",
            "hs300_drawdown",
            "ah_nav",
            "div_nav",
            "incentive_nav",
            "strategy",
            "ah_weight",
            "industry_weight",
            "industry_source",
            "incentive_slot_weight",
            "incentive_max_gross",
        ]
    ].rename(columns={"combo_nav_rebased": "combo_nav", "hs300_nav_rebased": "hs300_nav"})

    prefix = CONSERVATIVE_OUTPUT_PREFIX
    daily_path = RESULTS / f"{prefix}_daily_nav.csv"
    metrics_path = RESULTS / f"{prefix}_metrics.csv"
    plot_path = RESULTS / f"{prefix}_nav_excess_drawdown.png"
    holdings_path = RESULTS / f"{prefix}_incentive_holdings.csv"

    daily_out.to_csv(daily_path)
    inc_holdings.to_csv(holdings_path, index=False)
    pd.DataFrame(
        [
            {"asset": "Conservative composite (AH50+DivChi30+Inc2%)", **metrics_combo},
            {"asset": "CSI300", **metrics_hs300},
            {
                "asset": "Excess (combo/CSI300 ratio)",
                "final_nav": excess_final,
                "cagr": excess_cagr,
                "max_drawdown": float(daily["excess_nav_drawdown"].min()),
            },
        ]
    ).to_csv(metrics_path, index=False)
    _save_nav_excess_drawdown_plot(daily, plot_path, CONSERVATIVE_SPEC.name)
    calendar = export_return_calendars(combo, label=CONSERVATIVE_SPEC.name, file_suffix="conservative")
    turnover = analyze_conservative_turnover()

    payload = {
        "spec": {
            "ah_weight": CONSERVATIVE_SPEC.ah_weight,
            "industry_weight": CONSERVATIVE_SPEC.industry_weight,
            "industry_source": CONSERVATIVE_SPEC.industry_source,
            "incentive_slot_weight": CONSERVATIVE_SPEC.incentive.slot_weight,
            "incentive_max_gross": CONSERVATIVE_SPEC.incentive.max_gross,
            "compliance_note": "ETF held at 30%; stock-level 8%/top5-40% via look-through (not simulated here).",
        },
        "metrics": metrics_combo,
        "hs300_metrics": metrics_hs300,
        "excess": {
            "final_ratio": excess_final,
            "excess_cagr": excess_cagr,
            "max_excess_nav_drawdown": float(daily["excess_nav_drawdown"].min()),
        },
        "avg_incentive_gross": float(inc_holdings["gross_weight"].mean()),
        "turnover_analysis": turnover,
        "return_calendar": calendar["stability"],
        "outputs": {
            "daily_csv": str(daily_path),
            "metrics_csv": str(metrics_path),
            "plot_png": str(plot_path),
            "holdings_csv": str(holdings_path),
            **calendar["outputs"],
        },
    }
    with (RESULTS / f"{prefix}_summary.json").open("w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return payload


def export_calendars_from_saved_daily() -> dict:
    daily_path = RESULTS / f"{OUTPUT_PREFIX}_daily_nav.csv"
    if not daily_path.exists():
        raise FileNotFoundError(f"Missing {daily_path}. Run china_layered_composite_research first.")
    daily = pd.read_csv(daily_path, index_col=0, parse_dates=True).sort_index()
    return export_return_calendars(daily)


def run_research() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    daily_base = _load_daily_sleeves()

    incentive_cache: dict[tuple, tuple[pd.Series, pd.DataFrame]] = {}
    metrics_rows: list[dict] = []
    best_sharpe = -np.inf
    best_daily: pd.DataFrame | None = None
    best_holdings: pd.DataFrame | None = None

    for spec in _scan_specs():
        key = (
            spec.incentive.slot_weight,
            spec.incentive.max_gross,
            spec.incentive.scale_mode,
            spec.incentive.universe,
        )
        if key not in incentive_cache:
            incentive_cache[key] = _build_incentive_monthly_nav(spec.incentive)
        incentive_returns, incentive_holdings, _ = incentive_cache[key]

        combo = run_composite(spec, daily_base, incentive_returns)
        m = _metrics(combo["combo_nav"], combo["combo_return"])
        if not m:
            continue
        row = {
            "strategy": spec.name,
            "ah_weight": spec.ah_weight,
            "industry_weight": spec.industry_weight,
            "industry_source": spec.industry_source,
            "incentive_slot_weight": spec.incentive.slot_weight,
            "incentive_max_gross": spec.incentive.max_gross,
            "incentive_scale_mode": spec.incentive.scale_mode,
            "avg_incentive_gross": float(incentive_holdings["gross_weight"].mean()),
            "avg_incentive_positions": float(incentive_holdings["positions"].mean()),
            "events_entered_total": int(incentive_holdings["positions"].sum()),
            **m,
        }
        metrics_rows.append(row)
        if m["sharpe"] > best_sharpe:
            best_sharpe = float(m["sharpe"])
            best_daily = combo
            best_holdings = incentive_holdings.copy()
            best_holdings["composite_strategy"] = spec.name

    metrics_df = pd.DataFrame(metrics_rows).sort_values(["sharpe", "cagr"], ascending=False)
    metrics_df.to_csv(RESULTS / f"{OUTPUT_PREFIX}_scan_metrics.csv", index=False)

    if best_daily is None:
        raise RuntimeError("No composite specs produced metrics.")

    best_name = str(best_daily["strategy"].iloc[0])
    daily_out = best_daily[
        [
            "combo_nav",
            "combo_return",
            "combo_drawdown",
            "ah_nav",
            "etf_nav",
            "div_nav",
            "incentive_nav",
            "hs300_nav",
            "ah_return",
            "industry_return",
            "hs300_return",
            "strategy",
            "ah_weight",
            "industry_weight",
            "industry_source",
            "incentive_slot_weight",
            "incentive_max_gross",
            "incentive_scale_mode",
        ]
    ]
    daily_out.to_csv(RESULTS / f"{OUTPUT_PREFIX}_daily_nav.csv")
    best_holdings.to_csv(RESULTS / f"{OUTPUT_PREFIX}_incentive_holdings.csv", index=False)

    # Reference architectures the user described explicitly
    user_specs = [
        CompositeSpec(
            name="user_AH65_DivChi20_Inc2pct",
            ah_weight=0.65,
            industry_weight=0.20,
            industry_source="div_chinext",
            incentive=IncrementalIncentiveSpec(slot_weight=0.02, max_gross=0.15, scale_mode="proportional"),
        ),
        CompositeSpec(
            name="user_AH65_ETF20_Inc2pct",
            ah_weight=0.65,
            industry_weight=0.20,
            industry_source="etf_top2",
            incentive=IncrementalIncentiveSpec(slot_weight=0.02, max_gross=0.15, scale_mode="proportional"),
        ),
        CompositeSpec(
            name="user_AH70_DivChi15_Inc3pct_trim",
            ah_weight=0.70,
            industry_weight=0.15,
            industry_source="div_chinext",
            incentive=IncrementalIncentiveSpec(slot_weight=0.03, max_gross=0.15, scale_mode="trim_worst"),
        ),
    ]
    user_rows = []
    user_daily_frames = []
    for uspec in user_specs:
        key = (
            uspec.incentive.slot_weight,
            uspec.incentive.max_gross,
            uspec.incentive.scale_mode,
            uspec.incentive.universe,
        )
        if key not in incentive_cache:
            incentive_cache[key] = _build_incentive_monthly_nav(uspec.incentive)
        inc_returns, _ = incentive_cache[key][:2]
        combo = run_composite(uspec, daily_base, inc_returns)
        m = _metrics(combo["combo_nav"], combo["combo_return"])
        user_rows.append({"strategy": uspec.name, **m})
        user_daily_frames.append(combo[["combo_nav", "strategy"]])
    pd.DataFrame(user_rows).to_csv(RESULTS / f"{OUTPUT_PREFIX}_user_variants_metrics.csv", index=False)

    # Incremental incentive standalone vs capped slot (20) for bias comparison
    inc_specs = [
        IncrementalIncentiveSpec(0.02, max_gross=0.15, scale_mode="proportional"),
        IncrementalIncentiveSpec(0.02, max_gross=1.0, scale_mode="proportional"),
        IncrementalIncentiveSpec(0.05, max_gross=1.0, scale_mode="proportional"),
    ]
    inc_compare = []
    for isp in inc_specs:
        ret, hold, _ = _build_incentive_monthly_nav(isp)
        nav = (1.0 + ret).cumprod()
        years = (ret.index[-1] - ret.index[0]).days / 365.25
        cagr = float(nav.iloc[-1] ** (1 / years) - 1)
        vol = float(ret.std() * math.sqrt(12))
        inc_compare.append(
            {
                "slot_weight": isp.slot_weight,
                "max_gross": isp.max_gross,
                "scale_mode": isp.scale_mode,
                "cagr": cagr,
                "sharpe": cagr / vol if vol else np.nan,
                "avg_gross": float(hold["gross_weight"].mean()),
                "avg_positions": float(hold["positions"].mean()),
                "max_positions": int(hold["positions"].max()),
                "events_skipped": 0,
            }
        )
    pd.DataFrame(inc_compare).to_csv(RESULTS / f"{OUTPUT_PREFIX}_incentive_modes.csv", index=False)

    best_row = metrics_df.iloc[0].to_dict()
    summary = {
        "architecture": {
            "base": "AH low-premium Top10 (Tushare)",
            "industry_sleeve": "dividend/chinext 12M pair OR ETF 6M skip 1M Top2",
            "incentive": "incremental 1-3% per event, 9M hold, dynamic cap scaling (no 20-slot skip)",
        },
        "best_scan": best_row,
        "user_variants": user_rows,
        "incentive_bias_note": (
            "Slot cap at 20 skips late-month events when full (sampling bias). "
            "Incremental mode enters every event and scales gross down when above max_gross."
        ),
        "top5_scan": metrics_df.head(5).to_dict(orient="records"),
    }
    with (RESULTS / f"{OUTPUT_PREFIX}_summary.json").open("w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    calendar_payload = export_return_calendars(best_daily)
    summary["return_calendar"] = calendar_payload
    with (RESULTS / f"{OUTPUT_PREFIX}_summary.json").open("w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    _save_plot(best_daily, RESULTS / f"{OUTPUT_PREFIX}_nav_drawdown.png")

    print("Top 5 layered composite specs:")
    print(
        metrics_df[
            [
                "strategy",
                "cagr",
                "sharpe",
                "max_drawdown",
                "ah_weight",
                "industry_source",
                "incentive_slot_weight",
                "avg_incentive_positions",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )
    print("\nUser-specified variants:")
    print(pd.DataFrame(user_rows).to_string(index=False))
    print(f"\nReturn calendar stability ({calendar_payload['strategy']}):")
    print(json.dumps(calendar_payload["stability"], ensure_ascii=False, indent=2))
    print(f"\nBest: {best_name}")
    print(f"Outputs: {RESULTS / OUTPUT_PREFIX}_*")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "calendar":
        payload = export_calendars_from_saved_daily()
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "turnover":
        print(json.dumps(analyze_conservative_turnover(), ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "conservative":
        run_conservative_compliant()
    else:
        run_research()
