from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from qtlight.equity_incentive_event_backtest import DATA_RAW as EVENT_DATA_RAW, END_DATE, START_DATE
from qtlight.equity_incentive_optimized_backtest import RAW_DIR as OPT_RAW_DIR, _read_csv_if_valid
from qtlight.equity_incentive_slot_strategy_backtest import (
    COST_BPS,
    MAX_SLOTS,
    SLOT_WEIGHT,
    classify_event_kind,
    filter_tradable_events,
    load_strict_core_events,
)

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
BACKTEST_START = pd.Timestamp("2016-01-01")
DAILY_CACHE_DIR = EVENT_DATA_RAW
HS300_DAILY_PATH = EVENT_DATA_RAW / f"hs300_index_daily_{START_DATE}_{END_DATE}.csv"


@dataclass(frozen=True)
class DailySlotSpec:
    name: str
    slot_weight: float = SLOT_WEIGHT
    max_slots: int = MAX_SLOTS
    hold_months: int = 9
    cost_bps: float = COST_BPS
    full_policy: str = "ma200_swap"  # skip | ma200_swap
    esop_requires_ma200: bool = False


@dataclass
class DailyPosition:
    symbol: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    weight: float
    event_kind: str
    announcement_time: pd.Timestamp


def limit_up_threshold(symbol: str) -> float:
    if symbol.startswith(("688", "300", "301")):
        return 19.5
    if symbol.startswith(("8", "4")):
        return 29.5
    return 9.5


def is_limit_up_row(pct_chg: float, symbol: str) -> bool:
    if pd.isna(pct_chg):
        return True
    return float(pct_chg) >= limit_up_threshold(symbol) - 0.3


def _daily_cache_path(symbol: str) -> Path:
    return DAILY_CACHE_DIR / f"stock_{symbol}_daily_qfq.csv"


def _load_daily_frame(path: Path) -> pd.DataFrame:
    raw = _read_csv_if_valid(path)
    if raw.empty:
        return raw
    frame = raw.copy()
    frame["日期"] = pd.to_datetime(frame["日期"])
    return frame.sort_values("日期").drop_duplicates("日期")


DAILY_CACHE_DIR = EVENT_DATA_RAW
HS300_DAILY_PATH = EVENT_DATA_RAW / f"hs300_index_daily_{START_DATE}_{END_DATE}.csv"
TUSHARE_DAILY_RAW = EVENT_DATA_RAW / "tushare_daily"


def _to_ts_code(symbol: str) -> str:
    return f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"


def _date_chunks(start: str, end: str, years: int = 4) -> list[tuple[str, str]]:
    start_ts = pd.to_datetime(start)
    end_ts = pd.to_datetime(end)
    chunks = []
    chunk_start = start_ts
    while chunk_start <= end_ts:
        chunk_end = min(chunk_start + pd.DateOffset(years=years) - pd.Timedelta(days=1), end_ts)
        chunks.append((chunk_start.strftime("%Y%m%d"), chunk_end.strftime("%Y%m%d")))
        chunk_start = chunk_end + pd.Timedelta(days=1)
    return chunks


def _cached_tushare_query(path: Path, query_fn) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    import time

    frame = query_fn()
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    time.sleep(0.35)
    return frame


def _qfq_close(daily: pd.DataFrame, adj: pd.DataFrame) -> pd.Series:
    daily = daily.copy()
    adj = adj.copy()
    daily["trade_date"] = pd.to_datetime(daily["trade_date"].astype(str))
    adj["trade_date"] = pd.to_datetime(adj["trade_date"].astype(str))
    merged = daily.merge(adj, on=["ts_code", "trade_date"], how="left")
    merged = merged.sort_values("trade_date")
    merged["adj_factor"] = merged["adj_factor"].ffill().bfill()
    latest_factor = float(merged["adj_factor"].dropna().iloc[-1])
    close = merged["close"].astype(float) * merged["adj_factor"].astype(float) / latest_factor
    return pd.Series(close.to_numpy(), index=merged["trade_date"], name="close")


def fetch_stock_daily_qfq(symbol: str) -> pd.DataFrame:
    path = _daily_cache_path(symbol)
    cached = _load_daily_frame(path)
    if not cached.empty:
        return cached

    from qtlight.tushare_client import get_pro_api

    pro = get_pro_api()
    ts_code = _to_ts_code(symbol)
    daily_frames = []
    adj_frames = []
    for start, end in _date_chunks(START_DATE, END_DATE):
        daily_frames.append(
            _cached_tushare_query(
                TUSHARE_DAILY_RAW / f"{symbol}_daily_{start}_{end}.csv",
                lambda start=start, end=end: pro.daily(ts_code=ts_code, start_date=start, end_date=end),
            )
        )
        adj_frames.append(
            _cached_tushare_query(
                TUSHARE_DAILY_RAW / f"{symbol}_adj_{start}_{end}.csv",
                lambda start=start, end=end: pro.adj_factor(ts_code=ts_code, start_date=start, end_date=end),
            )
        )
    daily_frames = [frame for frame in daily_frames if not frame.empty]
    adj_frames = [frame for frame in adj_frames if not frame.empty]
    if not daily_frames or not adj_frames:
        return pd.DataFrame()
    daily = pd.concat(daily_frames, ignore_index=True)
    adj = pd.concat(adj_frames, ignore_index=True)
    daily["trade_date"] = daily["trade_date"].astype(str)
    adj["trade_date"] = adj["trade_date"].astype(str)
    daily = daily.drop_duplicates(["ts_code", "trade_date"])
    adj = adj.drop_duplicates(["ts_code", "trade_date"])
    if daily.empty or adj.empty:
        return pd.DataFrame()
    daily["trade_date"] = pd.to_datetime(daily["trade_date"].astype(str))
    close = _qfq_close(daily, adj)
    pct = (
        daily.sort_values("trade_date")
        .drop_duplicates("trade_date", keep="last")
        .set_index("trade_date")["pct_chg"]
        .astype(float)
        .reindex(close.index)
    )
    frame = pd.DataFrame({"日期": close.index, "收盘": close.values, "涨跌幅": pct.values})
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return frame


def load_stock_daily_panels(symbols: list[str]) -> dict[str, pd.DataFrame]:
    panels: dict[str, pd.DataFrame] = {}
    for idx, symbol in enumerate(symbols, start=1):
        for candidate in (_daily_cache_path(symbol), OPT_RAW_DIR / f"stock_{symbol}_daily_qfq.csv"):
            frame = _load_daily_frame(candidate)
            if not frame.empty:
                panels[symbol] = frame.set_index("日期")
                break
        else:
            try:
                fetched = fetch_stock_daily_qfq(symbol)
            except Exception as exc:
                print(f"skip daily fetch {symbol}: {exc}")
                continue
            if fetched.empty:
                continue
            panels[symbol] = fetched.set_index("日期")
        if idx % 25 == 0:
            print(f"daily panels loaded {idx}/{len(symbols)}")
    if not panels:
        raise RuntimeError("No daily stock panels loaded")
    return panels


def load_hs300_daily() -> pd.Series:
    if HS300_DAILY_PATH.exists():
        raw = pd.read_csv(HS300_DAILY_PATH)
    else:
        from qtlight.tushare_client import get_pro_api

        pro = get_pro_api()
        frames = []
        for start, end in _date_chunks(START_DATE, END_DATE):
            frames.append(
                _cached_tushare_query(
                    TUSHARE_DAILY_RAW / f"hs300_index_daily_{start}_{end}.csv",
                    lambda start=start, end=end: pro.index_daily(
                        ts_code="000300.SH",
                        start_date=start,
                        end_date=end,
                    ),
                )
            )
        raw = pd.concat(frames, ignore_index=True).drop_duplicates(["trade_date"])
        raw.to_csv(HS300_DAILY_PATH, index=False)
    if "日期" in raw.columns:
        raw["日期"] = pd.to_datetime(raw["日期"])
        close = raw.sort_values("日期").drop_duplicates("日期").set_index("日期")["收盘"].astype(float)
    else:
        raw["trade_date"] = pd.to_datetime(raw["trade_date"].astype(str))
        close = raw.sort_values("trade_date").drop_duplicates("trade_date").set_index("trade_date")["close"].astype(float)
        close.index.name = "日期"
    return close.rename("hs300")


def build_daily_close_panels(stock_panels: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    calendar = sorted(set().union(*(frame.index for frame in stock_panels.values())))
    calendar_index = pd.DatetimeIndex(calendar)
    close = pd.DataFrame(index=calendar_index)
    pct = pd.DataFrame(index=calendar_index)
    for symbol, frame in stock_panels.items():
        close[symbol] = frame["收盘"].astype(float)
        if "涨跌幅" in frame.columns:
            pct[symbol] = frame["涨跌幅"].astype(float)
        else:
            pct[symbol] = close[symbol].pct_change() * 100.0
    return close.sort_index(), pct.sort_index(), close.sort_index()


def first_tradable_entry_date(
    announcement_time: pd.Timestamp,
    symbol: str,
    calendar: pd.DatetimeIndex,
    close: pd.DataFrame,
    pct: pd.DataFrame,
) -> pd.Timestamp | None:
    ann_day = pd.Timestamp(announcement_time).normalize()
    candidates = calendar[calendar > ann_day]
    for day in candidates:
        if symbol not in close.columns:
            return None
        if pd.isna(close.at[day, symbol]):
            continue
        if is_limit_up_row(pct.at[day, symbol], symbol):
            continue
        return pd.Timestamp(day)
    return None


def prepare_daily_signals(
    events: pd.DataFrame,
    calendar: pd.DatetimeIndex,
    close: pd.DataFrame,
    pct: pd.DataFrame,
    above_ma: pd.DataFrame | None = None,
    esop_requires_ma200: bool = False,
    start: pd.Timestamp = BACKTEST_START,
) -> pd.DataFrame:
    rows = []
    for _, event in events.iterrows():
        kind = classify_event_kind(event.get("title_clean") or event.get("title", ""))
        if kind == "other":
            continue
        symbol = str(event["symbol"]).zfill(6)
        ann = pd.Timestamp(event["announcement_time"])
        entry_date = first_tradable_entry_date(ann, symbol, calendar, close, pct)
        if entry_date is None or entry_date < start:
            continue
        if esop_requires_ma200 and kind == "esop":
            if above_ma is None or symbol not in above_ma.columns or entry_date not in above_ma.index:
                continue
            if pd.isna(above_ma.at[entry_date, symbol]) or not bool(above_ma.at[entry_date, symbol]):
                continue
        rows.append(
            {
                "symbol": symbol,
                "announcement_time": ann,
                "entry_date": entry_date,
                "exit_date": entry_date + pd.DateOffset(months=9),
                "event_kind": kind,
                "title_clean": event.get("title_clean", ""),
            }
        )
    if not rows:
        return pd.DataFrame()
    signals = pd.DataFrame(rows).sort_values(["entry_date", "announcement_time", "symbol"])
    return signals.drop_duplicates(["symbol", "entry_date"], keep="first")


def _position_return_since_entry(
    position: DailyPosition,
    day: pd.Timestamp,
    daily_returns: pd.DataFrame,
) -> float:
    path = daily_returns.loc[position.entry_date:day, position.symbol].dropna()
    if path.empty:
        return 0.0
    return float((1.0 + path).prod() - 1.0)


def _pick_swap_indices(
    positions: list[DailyPosition],
    day: pd.Timestamp,
    above_ma: pd.DataFrame,
    daily_returns: pd.DataFrame,
    target_weight: float,
) -> list[int]:
    below = []
    for idx, pos in enumerate(positions):
        if pos.symbol not in above_ma.columns or day not in above_ma.index:
            continue
        flag = above_ma.at[day, pos.symbol]
        if pd.isna(flag) or bool(flag):
            continue
        below.append(idx)
    if not below:
        return []
    below.sort(key=lambda idx: _position_return_since_entry(positions[idx], day, daily_returns))
    sold_weight = 0.0
    chosen: list[int] = []
    for idx in below:
        chosen.append(idx)
        sold_weight += positions[idx].weight
        if sold_weight + 1e-9 >= target_weight:
            break
    return chosen


def run_daily_slot_strategy(
    spec: DailySlotSpec,
    signals: pd.DataFrame,
    close: pd.DataFrame,
    daily_returns: pd.DataFrame,
    above_ma: pd.DataFrame,
) -> tuple[pd.Series, pd.Series, pd.DataFrame, dict]:
    calendar = daily_returns.index
    start = max(BACKTEST_START, calendar.min())
    calendar = calendar[calendar >= start]
    signals_by_day = {
        day: group.sort_values(["announcement_time", "symbol"])
        for day, group in signals.groupby("entry_date")
    }

    positions: list[DailyPosition] = []
    strategy_returns = []
    turnover_rows = []
    holding_rows = []
    swap_count = 0
    skipped_full = 0

    for day in calendar:
        cost_rate = spec.cost_bps / 10_000.0
        day_turnover = 0.0

        day_return = 0.0
        for pos in positions:
            if day <= pos.entry_date:
                continue
            stock_ret = daily_returns.at[day, pos.symbol]
            if pd.isna(stock_ret):
                continue
            day_return += pos.weight * float(stock_ret)

        remaining = []
        for pos in positions:
            if day >= pos.exit_date:
                day_turnover += pos.weight
                continue
            remaining.append(pos)
        positions = remaining

        for _, signal in signals_by_day.get(day, pd.DataFrame()).iterrows():
            symbol = signal["symbol"]
            if symbol not in daily_returns.columns or any(p.symbol == symbol for p in positions):
                continue
            if pd.isna(daily_returns.at[day, symbol]):
                continue

            target_weight = spec.slot_weight
            gross_after = sum(p.weight for p in positions) + target_weight
            need_room = len(positions) >= spec.max_slots or gross_after > 1.0 + 1e-9

            if need_room:
                if spec.full_policy == "skip":
                    skipped_full += 1
                    continue
                if spec.full_policy == "ma200_swap":
                    swap_indices = _pick_swap_indices(positions, day, above_ma, daily_returns, target_weight)
                    if not swap_indices:
                        skipped_full += 1
                        continue
                    for idx in sorted(swap_indices, reverse=True):
                        day_turnover += positions[idx].weight
                        positions.pop(idx)
                    swap_count += 1
                else:
                    raise ValueError(spec.full_policy)

            positions.append(
                DailyPosition(
                    symbol=symbol,
                    entry_date=day,
                    exit_date=pd.Timestamp(signal["exit_date"]),
                    weight=target_weight,
                    event_kind=str(signal["event_kind"]),
                    announcement_time=pd.Timestamp(signal["announcement_time"]),
                )
            )
            day_turnover += target_weight

        gross_weight = sum(p.weight for p in positions)
        if gross_weight > 1.0 + 1e-9:
            scale = 1.0 / gross_weight
            for pos in positions:
                pos.weight *= scale
            gross_weight = 1.0

        day_return -= day_turnover * cost_rate

        strategy_returns.append(day_return)
        turnover_rows.append(day_turnover)
        holding_rows.append(
            {
                "date": day,
                "strategy": spec.name,
                "gross_weight": gross_weight,
                "positions": len(positions),
                "turnover": day_turnover,
            }
        )

    ret = pd.Series(strategy_returns, index=calendar, name=spec.name)
    turnover = pd.Series(turnover_rows, index=calendar, name=spec.name)
    stats = {"swap_count": swap_count, "skipped_full": skipped_full}
    return ret, turnover, pd.DataFrame(holding_rows), stats


def _metrics(returns: pd.Series, turnover: pd.Series, benchmark_returns: pd.Series) -> dict:
    aligned_bench = benchmark_returns.reindex(returns.index).fillna(0.0)
    excess = returns - aligned_bench
    equity = (1.0 + returns).cumprod()
    bench_equity = (1.0 + aligned_bench).cumprod()
    years = (returns.index[-1] - returns.index[0]).days / 365.25 if len(returns) > 1 else np.nan
    cagr = float(equity.iloc[-1] ** (1.0 / years) - 1.0) if years and years > 0 else np.nan
    vol = float(returns.std(ddof=1) * math.sqrt(252))
    max_dd = float((equity / equity.cummax() - 1.0).min())
    bench_cagr = float(bench_equity.iloc[-1] ** (1.0 / years) - 1.0) if years and years > 0 else np.nan
    return {
        "start_date": returns.index[0].date().isoformat(),
        "end_date": returns.index[-1].date().isoformat(),
        "days": int(len(returns)),
        "cagr": cagr,
        "benchmark_cagr": bench_cagr,
        "excess_cagr": cagr - bench_cagr if pd.notna(cagr) and pd.notna(bench_cagr) else np.nan,
        "ann_vol": vol,
        "sharpe": cagr / vol if vol > 0 and pd.notna(cagr) else np.nan,
        "max_drawdown": max_dd,
        "final_nav": float(equity.iloc[-1]),
        "turnover_per_year": float(turnover.sum() / years) if years and years > 0 else np.nan,
    }


def save_curve(equity_df: pd.DataFrame, path: Path, title: str) -> None:
    plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(12, 6))
    for col in equity_df.columns:
        ax.plot(equity_df.index, equity_df[col], label=col, linewidth=2 if col != "沪深300" else 1.5)
    ax.set_title(title)
    ax.set_ylabel("净值")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    prefix = "equity_incentive_daily_slot"

    events_all = load_strict_core_events("hs300_csi500")
    symbols = sorted(events_all["symbol"].astype(str).str.zfill(6).unique())
    print(f"Loading daily data for {len(symbols)} symbols...")
    stock_panels = load_stock_daily_panels(symbols)
    available = set(stock_panels)
    events = filter_tradable_events(events_all, available)
    close, pct, _ = build_daily_close_panels(stock_panels)
    daily_returns = close.pct_change(fill_method=None)
    monthly_close = close.resample("ME").last()
    ma200_daily = close.rolling(200, min_periods=200).mean()
    above_ma_daily = close > ma200_daily
    hs300 = load_hs300_daily()
    hs300 = hs300.reindex(close.index).ffill()
    bench_returns = hs300.pct_change(fill_method=None)

    specs = [
        DailySlotSpec("daily_7x14_skip", full_policy="skip"),
        DailySlotSpec("daily_7x14_ma200_swap", full_policy="ma200_swap"),
        DailySlotSpec("daily_7x14_ma200_swap_esop_filter", full_policy="ma200_swap", esop_requires_ma200=True),
    ]

    rows = []
    equity_cols = {}
    for spec in specs:
        signals = prepare_daily_signals(
            events,
            close.index,
            close,
            pct,
            above_ma=above_ma_daily,
            esop_requires_ma200=spec.esop_requires_ma200,
        )
        returns, turnover, holdings, stats = run_daily_slot_strategy(
            spec, signals, close, daily_returns, above_ma_daily
        )
        bench = bench_returns.reindex(returns.index).fillna(0.0)
        metrics = _metrics(returns, turnover, bench)
        metrics.update(
            strategy=spec.name,
            signal_count=int(len(signals)),
            avg_positions=float(holdings["positions"].mean()),
            avg_gross_weight=float(holdings["gross_weight"].mean()),
            swap_count=int(stats["swap_count"]),
            skipped_full=int(stats["skipped_full"]),
        )
        rows.append(metrics)
        equity_cols[spec.name] = (1.0 + returns).cumprod()
        holdings.to_csv(RESULTS_DIR / f"{prefix}_holdings_{spec.name}.csv", index=False)
        signals.to_csv(RESULTS_DIR / f"{prefix}_signals_{spec.name}.csv", index=False)

    metrics_df = pd.DataFrame(rows)
    metrics_df.to_csv(RESULTS_DIR / f"{prefix}_metrics.csv", index=False)

    equity_df = pd.DataFrame(equity_cols)
    equity_df["沪深300"] = (1.0 + bench_returns.reindex(equity_df.index).fillna(0.0)).cumprod()
    equity_df.index.name = "date"
    equity_df.to_csv(RESULTS_DIR / f"{prefix}_equity.csv")
    save_curve(
        equity_df,
        RESULTS_DIR / f"{prefix}_curve.png",
        "日频 7%×14：满员 skip vs MA200下方换仓 (2016+)",
    )

    payload = {
        "rules_zh": [
            "日频回测；ESOP/股权激励均在公告后首个可交易日收盘价入场（涨停日顺延）。",
            "持有 9 个自然月后在首个可交易日退出；单票 7%，最多 14 槽。",
            "满员不再 skip：卖出存量 MA200 下方持仓（日 MA200），优先卖表现最差者，腾位买新信号。",
            f"交易成本：单边 {COST_BPS:.0f} bps。",
        ],
        "metrics": metrics_df.to_dict(orient="records"),
    }
    with (RESULTS_DIR / f"{prefix}_summary.json").open("w") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    print(metrics_df[
        ["strategy", "signal_count", "cagr", "excess_cagr", "sharpe", "max_drawdown", "final_nav", "swap_count", "skipped_full", "avg_gross_weight"]
    ].to_string(index=False))


if __name__ == "__main__":
    main()
