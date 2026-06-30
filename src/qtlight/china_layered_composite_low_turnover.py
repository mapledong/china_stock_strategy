"""Low-turnover conservative composite: AH quarterly+buffer, DivChi 30%, incentive 2%."""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pandas as pd

from qtlight.ah_tushare_backtest import (
    START,
    TRADE_COST_BPS,
    build_monthly_premium_tushare,
    load_current_ah_pairs,
    load_tushare_selected_daily,
    _fetch_hk_basic,
    _fetch_stock_basic,
)
from qtlight.ah_twostage_research import (
    BENCHMARK_TICKER,
    build_targets,
    build_targets_quarterly_buffer,
    load_yahoo_adj_close,
    run_execution_backtest,
)
from qtlight.china_layered_composite_research import (
    CONSERVATIVE_SPEC,
    CompositeSpec,
    IncrementalIncentiveSpec,
    _build_incentive_monthly_nav,
    _enrich_analytics,
    _load_daily_sleeves,
    _metrics,
    _save_nav_excess_drawdown_plot,
    analyze_conservative_turnover,
    export_return_calendars,
    run_composite,
)
from qtlight.tushare_client import get_pro_api


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
OUTPUT_PREFIX = "china_layered_composite_low_turnover"

LOW_TURNOVER_SPEC = CompositeSpec(
    name="low_turnover_AH50_DivChi30_Inc2pct",
    ah_weight=0.50,
    industry_weight=0.30,
    industry_source="div_chinext",
    incentive=IncrementalIncentiveSpec(slot_weight=0.02, max_gross=0.15, scale_mode="proportional"),
)


def _load_monthly_premium_cache() -> pd.DataFrame:
    path = RESULTS / "ah_tushare_monthly_premium.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run ah_tushare_backtest first.")
    frame = pd.read_csv(path)
    frame = frame.rename(columns={frame.columns[0]: "date"})
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.set_index("date").sort_index()


def run_ah_tushare_with_targets(
    monthly_targets: pd.DataFrame,
    label: str,
    daily_bundle: dict | None = None,
) -> tuple[pd.Series, pd.Series]:
    """Run AH execution backtest from cached Tushare daily data."""
    if daily_bundle is None:
        pro = get_pro_api()
        pairs = load_current_ah_pairs(refresh=False)
        stock_basic = _fetch_stock_basic(pro)
        hk_basic = _fetch_hk_basic(pro)
        _, metadata = build_monthly_premium_tushare(pairs, pro, stock_basic, hk_basic)
        selected_keys = sorted(monthly_targets.columns[(monthly_targets > 0).any()].tolist())
        benchmark = load_yahoo_adj_close(BENCHMARK_TICKER, "510300_SS_yahoo")
        dates = benchmark.index[benchmark.index >= pd.Timestamp(START)]
        daily_bundle = load_tushare_selected_daily(selected_keys, metadata, dates, pro)

    equity, _, turnover = run_execution_backtest(
        monthly_targets=monthly_targets,
        returns=daily_bundle["returns"],
        pct_change=daily_bundle["pct_change"],
        volume=daily_bundle["volume"],
        trade_cost_bps=TRADE_COST_BPS,
    )
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    turnover_per_year = float(turnover.sum() / years) if years > 0 else np.nan
    nav = equity["strategy_equity"] / equity["strategy_equity"].iloc[0]
    nav.name = label
    turnover.name = label
    print(f"AH {label}: turnover/year={turnover_per_year:.2f}x, final={nav.iloc[-1]:.3f}")
    return nav, turnover


QUARTER_CYCLE_PRESETS: dict[str, tuple[int, ...]] = {
    "Jan_Apr_Jul_Oct": (1, 4, 7, 10),
    "Feb_May_Aug_Nov": (2, 5, 8, 11),
    "Mar_Jun_Sep_Dec": (3, 6, 9, 12),
}


def _load_ah_daily_bundle(monthly_premium: pd.DataFrame) -> dict:
    pro = get_pro_api()
    pairs = load_current_ah_pairs(refresh=False)
    stock_basic = _fetch_stock_basic(pro)
    hk_basic = _fetch_hk_basic(pro)
    _, metadata = build_monthly_premium_tushare(pairs, pro, stock_basic, hk_basic)
    monthly_targets = build_targets(monthly_premium)
    selected_keys = sorted(monthly_targets.columns[(monthly_targets > 0).any()].tolist())
    benchmark = load_yahoo_adj_close(BENCHMARK_TICKER, "510300_SS_yahoo")
    dates = benchmark.index[benchmark.index >= pd.Timestamp(START)]
    return load_tushare_selected_daily(selected_keys, metadata, dates, pro)


def scan_quarter_rebalance_months() -> dict:
    """Compare three quarterly rebalance calendars on AH sleeve and full composite."""
    RESULTS.mkdir(parents=True, exist_ok=True)
    monthly_premium = _load_monthly_premium_cache()
    daily_bundle = _load_ah_daily_bundle(monthly_premium)
    daily_base = _load_daily_sleeves()
    inc_returns, _ = _build_incentive_monthly_nav(LOW_TURNOVER_SPEC.incentive)[:2]

    rows: list[dict] = []
    for cycle_name, months in QUARTER_CYCLE_PRESETS.items():
        targets = build_targets_quarterly_buffer(monthly_premium, rebalance_months=months)
        ah_nav, ah_turn = run_ah_tushare_with_targets(targets, cycle_name, daily_bundle=daily_bundle)
        combo = _build_composite_daily(ah_nav, LOW_TURNOVER_SPEC, inc_returns, daily_base)
        enriched = _enrich_analytics(combo)
        overlap = enriched.loc["2018-04-02":]
        start = overlap.index.min()
        nav = overlap["combo_nav"] / overlap.loc[start, "combo_nav"]
        m = _metrics(nav, overlap["combo_return"])
        years = (ah_turn.index[-1] - ah_turn.index[0]).days / 365.25
        rows.append(
            {
                "cycle": cycle_name,
                "rebalance_months": list(months),
                "ah_turnover_per_year": float(ah_turn.sum() / years),
                "composite_cagr": m["cagr"],
                "composite_sharpe": m["sharpe"],
                "composite_max_drawdown": m["max_drawdown"],
                "composite_final_nav": m["final_nav"],
                "excess_final_ratio": float(overlap["excess_nav"].iloc[-1]),
            }
        )

    # monthly AH baseline for reference
    monthly_targets = build_targets(monthly_premium)
    ah_nav_m, ah_turn_m = run_ah_tushare_with_targets(monthly_targets, "monthly", daily_bundle=daily_bundle)
    combo_m = _build_composite_daily(ah_nav_m, LOW_TURNOVER_SPEC, inc_returns, daily_base)
    enriched_m = _enrich_analytics(combo_m).loc["2018-04-02":]
    start_m = enriched_m.index.min()
    nav_m = enriched_m["combo_nav"] / enriched_m.loc[start_m, "combo_nav"]
    m_m = _metrics(nav_m, enriched_m["combo_return"])
    years_m = (ah_turn_m.index[-1] - ah_turn_m.index[0]).days / 365.25
    rows.append(
        {
            "cycle": "monthly_baseline",
            "rebalance_months": list(range(1, 13)),
            "ah_turnover_per_year": float(ah_turn_m.sum() / years_m),
            "composite_cagr": m_m["cagr"],
            "composite_sharpe": m_m["sharpe"],
            "composite_max_drawdown": m_m["max_drawdown"],
            "composite_final_nav": m_m["final_nav"],
            "excess_final_ratio": float(enriched_m["excess_nav"].iloc[-1]),
        }
    )

    df = pd.DataFrame(rows).sort_values(["composite_sharpe", "composite_cagr"], ascending=False)
    out_csv = RESULTS / f"{OUTPUT_PREFIX}_quarter_month_scan.csv"
    df.to_csv(out_csv, index=False)
    best = df.iloc[0].to_dict()
    payload = {
        "scan": df.to_dict(orient="records"),
        "best_cycle": best,
        "note": "Composite = AH50% quarterly+buffer + DivChi30% + incentive2%; overlap from 2018-04-02.",
        "output_csv": str(out_csv),
    }
    with (RESULTS / f"{OUTPUT_PREFIX}_quarter_month_scan.json").open("w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
    print(df.to_string(index=False))
    print(f"\nBest: {best['cycle']} months={best['rebalance_months']}")
    return payload


def _build_composite_daily(
    ah_nav: pd.Series,
    spec: CompositeSpec,
    incentive_returns: pd.Series,
    daily_base: pd.DataFrame,
) -> pd.DataFrame:
    frame = daily_base.copy()
    ah_aligned = ah_nav.reindex(frame.index).ffill()
    frame["ah_nav"] = ah_aligned / ah_aligned.dropna().iloc[0]
    return run_composite(spec, frame, incentive_returns)


def _comparison_plot(baseline: pd.DataFrame, low_turn: pd.DataFrame, path: Path) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True, gridspec_kw={"height_ratios": [2, 1.3, 1.3]})

    axes[0].plot(baseline.index, baseline["combo_nav_rebased"], label="Conservative (monthly AH)", linewidth=1.4)
    axes[0].plot(low_turn.index, low_turn["combo_nav_rebased"], label="Low turnover (quarterly AH+buffer)", linewidth=1.4)
    axes[0].plot(baseline.index, baseline["hs300_nav_rebased"], label="CSI300", linestyle="--", color="#888")
    axes[0].set_title("Conservative vs low-turnover composite")
    axes[0].set_ylabel("NAV")
    axes[0].legend(loc="upper left", fontsize=8)
    axes[0].grid(True, alpha=0.28)

    axes[1].plot(baseline.index, baseline["excess_nav"], label="Conservative / CSI300", linewidth=1.3)
    axes[1].plot(low_turn.index, low_turn["excess_nav"], label="Low turnover / CSI300", linewidth=1.3)
    axes[1].axhline(1.0, color="black", linewidth=0.8, alpha=0.5)
    axes[1].set_ylabel("Excess NAV")
    axes[1].legend(loc="upper left", fontsize=8)
    axes[1].grid(True, alpha=0.28)

    axes[2].plot(baseline.index, baseline["combo_drawdown"], label="Conservative DD", linewidth=1.2)
    axes[2].plot(low_turn.index, low_turn["combo_drawdown"], label="Low turnover DD", linewidth=1.2)
    axes[2].plot(baseline.index, baseline["hs300_drawdown"], label="CSI300 DD", linestyle="--", color="#888")
    axes[2].set_ylabel("Drawdown")
    axes[2].set_xlabel("Date")
    axes[2].legend(loc="lower left", fontsize=8)
    axes[2].grid(True, alpha=0.28)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run_low_turnover_research() -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)
    monthly_premium = _load_monthly_premium_cache()
    monthly_targets = build_targets(monthly_premium)
    quarterly_targets = build_targets_quarterly_buffer(monthly_premium)

    ah_monthly_nav, ah_monthly_turn = run_ah_tushare_with_targets(monthly_targets, "monthly")
    ah_quarterly_nav, ah_quarterly_turn = run_ah_tushare_with_targets(quarterly_targets, "quarterly_buffer")

    ah_monthly_nav.to_csv(RESULTS / f"{OUTPUT_PREFIX}_ah_monthly_nav.csv")
    ah_quarterly_nav.to_csv(RESULTS / f"{OUTPUT_PREFIX}_ah_quarterly_buffer_nav.csv")

    daily_base = _load_daily_sleeves()
    inc_returns, inc_holdings, _ = _build_incentive_monthly_nav(LOW_TURNOVER_SPEC.incentive)

    # Baseline conservative uses monthly AH from existing equity file
    baseline_combo = run_composite(CONSERVATIVE_SPEC, daily_base, inc_returns)
    baseline_daily = _enrich_analytics(baseline_combo)

    # Low turnover: replace AH sleeve with quarterly+buffer NAV
    low_combo = _build_composite_daily(ah_quarterly_nav, LOW_TURNOVER_SPEC, inc_returns, daily_base)
    low_daily = _enrich_analytics(low_combo)

    overlap_start = max(
        baseline_daily.index.min(),
        low_daily.index.min(),
    )
    baseline_daily = baseline_daily.loc[overlap_start:]
    low_daily = low_daily.loc[overlap_start:]
    for frame in (baseline_daily, low_daily):
        start = frame.index.min()
        frame["combo_nav_rebased"] = frame["combo_nav"] / frame.loc[start, "combo_nav"]
        frame["hs300_nav_rebased"] = frame["hs300_nav"] / frame.loc[start, "hs300_nav"]
        frame["excess_nav"] = frame["combo_nav_rebased"] / frame["hs300_nav_rebased"]

    metrics_baseline = _metrics(baseline_daily["combo_nav_rebased"], baseline_daily["combo_return"])
    metrics_low = _metrics(low_daily["combo_nav_rebased"], low_daily["combo_return"])
    metrics_hs300 = _metrics(low_daily["hs300_nav_rebased"], low_daily["hs300_return"])

    years_ah = (ah_monthly_turn.index[-1] - ah_monthly_turn.index[0]).days / 365.25
    ah_turnover = {
        "monthly_ah_full_sleeve": float(ah_monthly_turn.sum() / years_ah),
        "quarterly_buffer_ah_full_sleeve": float(ah_quarterly_turn.sum() / years_ah),
    }

    turnover_analysis = analyze_conservative_turnover()
    # Re-label scenario names for clarity in summary
    turnover_scenarios = turnover_analysis["reduction_scenarios_per_year"]

    comparison_path = RESULTS / f"{OUTPUT_PREFIX}_comparison_nav_excess_drawdown.png"
    _comparison_plot(baseline_daily, low_daily, comparison_path)
    _save_nav_excess_drawdown_plot(low_daily, RESULTS / f"{OUTPUT_PREFIX}_nav_excess_drawdown.png", LOW_TURNOVER_SPEC.name)

    low_daily_out = low_daily[
        [
            "combo_nav_rebased",
            "combo_return",
            "combo_drawdown",
            "excess_nav",
            "excess_return",
            "excess_nav_drawdown",
            "hs300_nav_rebased",
            "hs300_drawdown",
            "ah_nav",
            "div_nav",
            "incentive_nav",
        ]
    ].rename(columns={"combo_nav_rebased": "combo_nav", "hs300_nav_rebased": "hs300_nav"})
    low_daily_out.to_csv(RESULTS / f"{OUTPUT_PREFIX}_daily_nav.csv")

    calendar = export_return_calendars(low_combo, label=LOW_TURNOVER_SPEC.name, file_suffix="low_turnover")

    payload = {
        "low_turnover_spec": {
            "ah_weight": LOW_TURNOVER_SPEC.ah_weight,
            "industry_weight": LOW_TURNOVER_SPEC.industry_weight,
            "ah_execution": "quarter-end rebalance + top10 hold buffer (no monthly reweight)",
            "incentive": "2% per event, 9M hold, 15% cap",
        },
        "metrics": {
            "low_turnover_composite": metrics_low,
            "conservative_baseline_monthly_ah": metrics_baseline,
            "csi300": metrics_hs300,
        },
        "excess_low_turnover": {
            "final_ratio": float(low_daily["excess_nav"].iloc[-1]),
            "excess_cagr": float(
                (low_daily["excess_nav"].iloc[-1]) ** (1 / ((low_daily.index[-1] - low_daily.index[0]).days / 365.25)) - 1
            ),
            "max_excess_drawdown": float(low_daily["excess_nav_drawdown"].min()),
        },
        "ah_sleeve_turnover_per_year": ah_turnover,
        "portfolio_turnover_scenarios": turnover_scenarios,
        "estimated_low_turnover_portfolio_turnover": turnover_scenarios.get("ah_quarterly_plus_buffer"),
        "return_calendar": calendar["stability"],
        "outputs": {
            "comparison_plot": str(comparison_path),
            "low_turnover_daily_csv": str(RESULTS / f"{OUTPUT_PREFIX}_daily_nav.csv"),
            "low_turnover_plot": str(RESULTS / f"{OUTPUT_PREFIX}_nav_excess_drawdown.png"),
            "ah_quarterly_nav_csv": str(RESULTS / f"{OUTPUT_PREFIX}_ah_quarterly_buffer_nav.csv"),
            **calendar["outputs"],
        },
    }
    with (RESULTS / f"{OUTPUT_PREFIX}_summary.json").open("w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    pd.DataFrame(
        [
            {"variant": "low_turnover", **metrics_low},
            {"variant": "conservative_baseline", **metrics_baseline},
            {"variant": "csi300", **metrics_hs300},
        ]
    ).to_csv(RESULTS / f"{OUTPUT_PREFIX}_metrics.csv", index=False)

    print("\n=== Low turnover vs conservative baseline ===")
    print(pd.DataFrame([metrics_low, metrics_baseline, metrics_hs300], index=["low_turnover", "baseline", "hs300"]).to_string())
    print(f"\nAH sleeve turnover: monthly {ah_turnover['monthly_ah_full_sleeve']:.2f}x -> quarterly+buffer {ah_turnover['quarterly_buffer_ah_full_sleeve']:.2f}x")
    print(f"Estimated portfolio turnover (quarterly+buffer): {turnover_scenarios.get('ah_quarterly_plus_buffer', 0):.2f}x")
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return payload


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "scan-quarters":
        scan_quarter_rebalance_months()
    else:
        run_low_turnover_research()
