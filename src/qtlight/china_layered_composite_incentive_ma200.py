"""Compare equity-incentive MA200 filter within low-turnover composite."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pandas as pd

from qtlight.china_layered_composite_low_turnover import (
    LOW_TURNOVER_SPEC,
    _build_composite_daily,
)
from qtlight.china_layered_composite_research import (
    CompositeSpec,
    IncrementalIncentiveSpec,
    _build_incentive_monthly_nav,
    _enrich_analytics,
    _load_daily_sleeves,
    _metrics,
    _save_nav_excess_drawdown_plot,
)


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
OUTPUT_PREFIX = "china_layered_composite_incentive_ma200"

BASE_INCENTIVE = IncrementalIncentiveSpec(
    slot_weight=0.02,
    hold_months=9,
    max_gross=0.15,
    scale_mode="proportional",
    require_ma200_above=False,
)

MA200_INCENTIVE = IncrementalIncentiveSpec(
    slot_weight=0.02,
    hold_months=9,
    max_gross=0.15,
    scale_mode="proportional",
    require_ma200_above=True,
    ma_window_months=10,
)

LOW_TURNOVER_MA200 = CompositeSpec(
    name="low_turnover_AH50_DivChi30_Inc2pct_MA200",
    ah_weight=LOW_TURNOVER_SPEC.ah_weight,
    industry_weight=LOW_TURNOVER_SPEC.industry_weight,
    industry_source=LOW_TURNOVER_SPEC.industry_source,
    incentive=MA200_INCENTIVE,
)


def _incentive_metrics(returns: pd.Series, holdings: pd.DataFrame) -> dict:
    nav = (1.0 + returns.fillna(0.0)).cumprod()
    m = _metrics(nav, returns.fillna(0.0))
    return {
        **m,
        "avg_gross": float(holdings["gross_weight"].mean()),
        "avg_positions": float(holdings["positions"].mean()),
        "max_positions": int(holdings["positions"].max()),
        "total_position_months": int(holdings["positions"].sum()),
    }


def _filter_summary(diag: pd.DataFrame) -> dict:
    if diag.empty:
        return {"total_signals": 0, "passed": 0, "rejected": 0, "pass_rate": np.nan}
    total = len(diag)
    passed = int(diag["passed"].sum())
    return {
        "total_signals": total,
        "passed": passed,
        "rejected": total - passed,
        "pass_rate": float(passed / total) if total else np.nan,
    }


def _load_quarterly_ah_nav() -> pd.Series:
    path = RESULTS / "china_layered_composite_low_turnover_ah_quarterly_buffer_nav.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run: PYTHONPATH=src .venv/bin/python -m qtlight.china_layered_composite_low_turnover"
        )
    series = pd.read_csv(path, index_col=0, parse_dates=True).squeeze("columns")
    series.name = "ah_quarterly_buffer"
    return series.sort_index()


def _comparison_plot(baseline: pd.DataFrame, filtered: pd.DataFrame, path: Path) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True, gridspec_kw={"height_ratios": [2, 1.3, 1.3]})

    axes[0].plot(baseline.index, baseline["combo_nav_rebased"], label="No MA200 filter", linewidth=1.4)
    axes[0].plot(filtered.index, filtered["combo_nav_rebased"], label="MA200 above only", linewidth=1.4)
    axes[0].plot(baseline.index, baseline["hs300_nav_rebased"], label="CSI300", linestyle="--", color="#888")
    axes[0].set_title("Low-turnover composite: incentive MA200 filter")
    axes[0].set_ylabel("NAV")
    axes[0].legend(loc="upper left", fontsize=8)
    axes[0].grid(True, alpha=0.28)

    axes[1].plot(baseline.index, baseline["excess_nav"], label="No filter / CSI300", linewidth=1.3)
    axes[1].plot(filtered.index, filtered["excess_nav"], label="MA200 / CSI300", linewidth=1.3)
    axes[1].axhline(1.0, color="black", linewidth=0.8, alpha=0.5)
    axes[1].set_ylabel("Excess NAV")
    axes[1].legend(loc="upper left", fontsize=8)
    axes[1].grid(True, alpha=0.28)

    axes[2].plot(baseline.index, baseline["combo_drawdown"], label="No filter DD", linewidth=1.2)
    axes[2].plot(filtered.index, filtered["combo_drawdown"], label="MA200 DD", linewidth=1.2)
    axes[2].plot(baseline.index, baseline["hs300_drawdown"], label="CSI300 DD", linestyle="--", color="#888")
    axes[2].set_ylabel("Drawdown")
    axes[2].set_xlabel("Date")
    axes[2].legend(loc="lower left", fontsize=8)
    axes[2].grid(True, alpha=0.28)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _rebase_overlap(*frames: pd.DataFrame) -> tuple[pd.DataFrame, ...]:
    overlap_start = max(f.index.min() for f in frames)
    out = []
    for frame in frames:
        f = frame.loc[overlap_start:].copy()
        start = f.index.min()
        f["combo_nav_rebased"] = f["combo_nav"] / f.loc[start, "combo_nav"]
        f["hs300_nav_rebased"] = f["hs300_nav"] / f.loc[start, "hs300_nav"]
        f["excess_nav"] = f["combo_nav_rebased"] / f["hs300_nav_rebased"]
        out.append(f)
    return tuple(out)


def run_ma200_research() -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)

    inc_base_ret, inc_base_hold, _ = _build_incentive_monthly_nav(BASE_INCENTIVE)
    inc_ma_ret, inc_ma_hold, inc_ma_diag = _build_incentive_monthly_nav(MA200_INCENTIVE)

    inc_base_m = _incentive_metrics(inc_base_ret, inc_base_hold)
    inc_ma_m = _incentive_metrics(inc_ma_ret, inc_ma_hold)
    filter_stats = _filter_summary(inc_ma_diag)

    ah_nav = _load_quarterly_ah_nav()
    daily_base = _load_daily_sleeves()

    combo_base = _build_composite_daily(ah_nav, LOW_TURNOVER_SPEC, inc_base_ret, daily_base)
    combo_ma = _build_composite_daily(ah_nav, LOW_TURNOVER_MA200, inc_ma_ret, daily_base)

    daily_base_enriched = _enrich_analytics(combo_base)
    daily_ma_enriched = _enrich_analytics(combo_ma)
    daily_base_enriched, daily_ma_enriched = _rebase_overlap(daily_base_enriched, daily_ma_enriched)

    comp_base_m = _metrics(daily_base_enriched["combo_nav_rebased"], daily_base_enriched["combo_return"])
    comp_ma_m = _metrics(daily_ma_enriched["combo_nav_rebased"], daily_ma_enriched["combo_return"])
    hs300_m = _metrics(daily_ma_enriched["hs300_nav_rebased"], daily_ma_enriched["hs300_return"])

    comparison_path = RESULTS / f"{OUTPUT_PREFIX}_comparison_nav_excess_drawdown.png"
    _comparison_plot(daily_base_enriched, daily_ma_enriched, comparison_path)
    _save_nav_excess_drawdown_plot(
        daily_ma_enriched,
        RESULTS / f"{OUTPUT_PREFIX}_nav_excess_drawdown.png",
        LOW_TURNOVER_MA200.name,
    )

    metrics_rows = [
        {"layer": "incentive_standalone", "variant": "no_ma200", **inc_base_m},
        {"layer": "incentive_standalone", "variant": "ma200_above", **inc_ma_m},
        {"layer": "low_turnover_composite", "variant": "no_ma200", **comp_base_m},
        {"layer": "low_turnover_composite", "variant": "ma200_above", **comp_ma_m},
        {"layer": "benchmark", "variant": "csi300", **hs300_m},
    ]
    metrics_df = pd.DataFrame(metrics_rows)
    metrics_csv = RESULTS / f"{OUTPUT_PREFIX}_metrics.csv"
    metrics_df.to_csv(metrics_csv, index=False)

    if not inc_ma_diag.empty:
        inc_ma_diag.to_csv(RESULTS / f"{OUTPUT_PREFIX}_signal_filter_diag.csv", index=False)

    daily_ma_enriched[
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
    ].rename(columns={"combo_nav_rebased": "combo_nav", "hs300_nav_rebased": "hs300_nav"}).to_csv(
        RESULTS / f"{OUTPUT_PREFIX}_daily_nav.csv"
    )

    delta = {
        "composite_cagr_delta": comp_ma_m["cagr"] - comp_base_m["cagr"],
        "composite_sharpe_delta": comp_ma_m["sharpe"] - comp_base_m["sharpe"],
        "composite_max_dd_delta": comp_ma_m["max_drawdown"] - comp_base_m["max_drawdown"],
        "composite_final_nav_delta": comp_ma_m["final_nav"] - comp_base_m["final_nav"],
        "incentive_cagr_delta": inc_ma_m["cagr"] - inc_base_m["cagr"],
        "incentive_sharpe_delta": inc_ma_m["sharpe"] - inc_base_m["sharpe"],
    }

    payload = {
        "spec": {
            "composite": "AH50% quarterly 3/6/9/12 + buffer, DivChi30%, incentive 2% x 9M, 15% cap",
            "ma200_filter": "entry month close > 10-month rolling mean on monthly qfq (≈ daily MA200)",
            "ma_window_months": MA200_INCENTIVE.ma_window_months,
        },
        "incentive_filter": filter_stats,
        "incentive_standalone": {"no_ma200": inc_base_m, "ma200_above": inc_ma_m},
        "low_turnover_composite": {"no_ma200": comp_base_m, "ma200_above": comp_ma_m},
        "csi300": hs300_m,
        "delta_ma200_vs_baseline": delta,
        "improves_composite": bool(
            comp_ma_m["sharpe"] > comp_base_m["sharpe"]
            and comp_ma_m["max_drawdown"] >= comp_base_m["max_drawdown"]
        ),
        "outputs": {
            "metrics_csv": str(metrics_csv),
            "comparison_plot": str(comparison_path),
            "ma200_daily_nav": str(RESULTS / f"{OUTPUT_PREFIX}_daily_nav.csv"),
            "signal_filter_diag": str(RESULTS / f"{OUTPUT_PREFIX}_signal_filter_diag.csv"),
        },
    }
    summary_path = RESULTS / f"{OUTPUT_PREFIX}_summary.json"
    with summary_path.open("w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    print("\n=== Incentive standalone ===")
    print(pd.DataFrame([inc_base_m, inc_ma_m], index=["no_ma200", "ma200_above"]).to_string())
    print(f"\nMA200 filter: {filter_stats}")
    print("\n=== Low-turnover composite ===")
    print(pd.DataFrame([comp_base_m, comp_ma_m], index=["no_ma200", "ma200_above"]).to_string())
    print(f"\nDelta (MA200 - baseline): {json.dumps(delta, indent=2)}")
    return payload


if __name__ == "__main__":
    run_ma200_research()
