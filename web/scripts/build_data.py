#!/usr/bin/env python3
"""Export strategy results to web/data/strategies.json for the dashboard."""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
OUT = Path(__file__).resolve().parents[1] / "data" / "strategies.json"
NAV_DIR = Path(__file__).resolve().parents[1] / "data" / "nav"
DATA_VERSION = 5
SRC = ROOT / "src"

sys.path.insert(0, str(SRC))

STOCK_NAMES = {
    "300124": "汇川技术",
    "600153": "建发股份",
    "600196": "复星医药",
    "300308": "中际旭创",
    "600398": "海澜之家",
    "600873": "梅花生物",
    "300014": "亿纬锂能",
    "600208": "衢州发展",
    "601985": "中国核电",
    "300570": "太辰光",
    "688248": "南网科技",
    "300666": "江丰电子",
    "600655": "豫园股份",
}

STOCK_NAMES_EN = {
    "300124": "Inovance Technology",
    "600153": "C&D Inc.",
    "600196": "Fosun Pharma",
    "300308": "Zhongji Innolight",
    "600398": "Heilan Home",
    "600873": "Meihua Bio",
    "300014": "EVE Energy",
    "600208": "Quzhou Development",
    "601985": "China Nuclear Power",
    "300570": "Everbright Technology",
    "688248": "CSG Tech",
    "300666": "Konfoong Materials",
    "600655": "Yuyuan Inc.",
}

ETF_NAMES_EN = {
    "513050": "China Internet ETF",
    "159928": "Consumer ETF",
    "510230": "Financials ETF",
    "510880": "Dividend ETF",
    "512120": "Healthcare ETF",
    "512220": "TMT ETF",
    "562910": "Advanced Manufacturing ETF",
    "HYDRO_EQ": "Hydro Equal-Weight",
}

AH_PAIR_EN = {
    "XD中远海(601919/01919)": "COSCO Shipping (601919/01919)",
    "XD国泰海(601211/02611)": "Guotai Haitong (601211/02611)",
    "XD广深铁(601333/00525)": "Guang-Shen Railway (601333/00525)",
    "XD浙商银(601916/02016)": "CZBank (601916/02016)",
    "XD紫金矿(601899/02899)": "Zijin Mining (601899/02899)",
    "万  科Ａ(000002/02202)": "Vanke A (000002/02202)",
    "三一重工(600031/06031)": "Sany Heavy Industry (600031/06031)",
    "上海医药(601607/02607)": "Shanghai Pharma (601607/02607)",
    "中信证券(600030/06030)": "CITIC Securities (600030/06030)",
    "中创智领(601717/00564)": "Zhongchuang Zhiling (601717/00564)",
    "中国中免(601888/01880)": "China Tourism Duty Free (601888/01880)",
    "中国中铁(601390/00390)": "China Railway Group (601390/00390)",
    "中国太保(601601/02601)": "CPIC (601601/02601)",
    "中国平安(601318/02318)": "Ping An Insurance (601318/02318)",
    "中国石化(600028/00386)": "Sinopec (600028/00386)",
    "中国神华(601088/01088)": "China Shenhua (601088/01088)",
    "中国铁建(601186/01186)": "CRCC (601186/01186)",
    "中国银行(601988/03988)": "Bank of China (601988/03988)",
    "中联重科(000157/01157)": "Zoomlion (000157/01157)",
    "中集集团(000039/02039)": "CIMC (000039/02039)",
    "交通银行(601328/03328)": "Bank of Communications (601328/03328)",
    "亿华通-U(688339/02402)": "SinoHytec (688339/02402)",
    "兆易创新(603986/03986)": "GigaDevice (603986/03986)",
    "先导智能(300450/00470)": "Lead Intelligent (300450/00470)",
    "光大银行(601818/06818)": "Everbright Bank (601818/06818)",
    "农业银行(601288/01288)": "ABC (601288/01288)",
    "华泰证券(601688/06886)": "Huatai Securities (601688/06886)",
    "国恩股份(002768/02768)": "Guoen Co. (002768/02768)",
    "复星医药(600196/02196)": "Fosun Pharma (600196/02196)",
    "宁德时代(300750/03750)": "CATL (300750/03750)",
    "宁沪高速(600377/00177)": "Ninghu Expressway (600377/00177)",
    "山东墨龙(002490/00568)": "Shandong Molong (002490/00568)",
    "工商银行(601398/01398)": "ICBC (601398/01398)",
    "广发证券(000776/01776)": "GF Securities (000776/01776)",
    "康龙化成(300759/03759)": "Pharmaron (300759/03759)",
    "建设银行(601939/00939)": "CCB (601939/00939)",
    "恒瑞医药(600276/01276)": "Hengrui Medicine (600276/01276)",
    "招商银行(600036/03968)": "China Merchants Bank (600036/03968)",
    "比亚迪(002594/01211)": "BYD (002594/01211)",
    "民生银行(600016/01988)": "CMBC (600016/01988)",
    "泰格医药(300347/03347)": "Tigermed (300347/03347)",
    "洛阳钼业(603993/03993)": "CMOC (603993/03993)",
    "海信家电(000921/00921)": "Hisense Home Appliances (000921/00921)",
    "海尔智家(600690/06690)": "Haier Smart Home (600690/06690)",
    "海螺水泥(600585/00914)": "Conch Cement (600585/00914)",
    "深高速(600548/00548)": "Shenzhen Expressway (600548/00548)",
    "潍柴动力(000338/02338)": "Weichai Power (000338/02338)",
    "澜起科技(688008/06809)": "Montage Technology (688008/06809)",
    "百济神州(688235/06160)": "BeiGene (688235/06160)",
    "福耀玻璃(600660/03606)": "Fuyao Glass (600660/03606)",
    "美的集团(000333/00300)": "Midea Group (000333/00300)",
    "胜宏科技(300476/02476)": "Shengyi Technology (300476/02476)",
    "荣昌生物(688331/09995)": "RemeGen (688331/09995)",
    "药明康德(603259/02359)": "WuXi AppTec (603259/02359)",
    "赣锋锂业(002460/01772)": "Ganfeng Lithium (002460/01772)",
    "赤峰黄金(600988/06693)": "Chifeng Gold (600988/06693)",
    "邮储银行(601658/01658)": "PSBC (601658/01658)",
    "金风科技(002202/02208)": "Goldwind (002202/02208)",
    "青岛啤酒(600600/00168)": "Tsingtao Brewery (600600/00168)",
    "青岛银行(002948/03866)": "Bank of Qingdao (002948/03866)",
    "鞍钢股份(000898/00347)": "Ansteel (000898/00347)",
    "顺丰控股(002352/06936)": "SF Holding (002352/06936)",
    "马钢股份(600808/00323)": "Magang Steel (600808/00323)",
}

PAIR_NAMES_EN = {
    "510880": "Dividend ETF",
    "159915": "ChiNext ETF",
}

ETF_STRATEGY = "6M skip 1M"
ETF_NAV_START = "2017-09-01"
AH_TOP_N = 10
DIVIDEND_CHINEXT_DIR = RESULTS / "dividend_chinext_momentum"
DIVIDEND_CHINEXT_STRATEGY = "12M momentum"
PAIR_NAMES = {"510880": "红利ETF", "159915": "创业板ETF"}
EQUITY_STRATEGY = "equal_weight_all"
EQUITY_COST_BPS = 20.0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def daily_nav_rows(frame, strategy_col: str, bench_col: str) -> list[dict]:
    out = []
    for dt, row in frame.iterrows():
        out.append(
            {
                "date": dt.date().isoformat() if hasattr(dt, "date") else str(dt)[:10],
                strategy_col: float(row[strategy_col]),
                bench_col: float(row[bench_col]),
            }
        )
    return out


def _first_on_or_after(index, start: str):
    import pandas as pd

    start_ts = pd.Timestamp(start)
    eligible = index[index >= start_ts]
    if eligible.empty:
        raise ValueError(f"No dates on or after {start}")
    return eligible[0]


def _attach_symbol_names(items: list[dict], name_map: dict[str, str], en_map: dict[str, str]) -> list[dict]:
    for item in items:
        symbol = item.get("symbol")
        if symbol and symbol not in item.get("name", ""):
            item.setdefault("name", name_map.get(symbol, symbol))
        if symbol:
            item["name_en"] = en_map.get(symbol, item.get("name", symbol))
    return items


def _attach_pair_names(items: list[dict]) -> list[dict]:
    for item in items:
        pair = item.get("pair", "")
        item["pair_en"] = AH_PAIR_EN.get(pair, pair)
    return items


def _write_nav_bundle(strategy_key: str, strategy: dict) -> dict:
    import math

    nav = strategy.pop("nav")
    NAV_DIR.mkdir(parents=True, exist_ok=True)

    def _clean_nav(obj):
        if isinstance(obj, dict):
            return {k: _clean_nav(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_clean_nav(v) for v in obj]
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        return obj

    nav_path = NAV_DIR / f"{strategy_key}.json"
    nav_path.write_text(json.dumps(_clean_nav(nav), ensure_ascii=False), encoding="utf-8")
    strategy["nav_src"] = f"nav/{strategy_key}.json"
    strategy["nav_points"] = len(nav)
    return strategy


def latest_holdings_by_date(rows: list[dict], date_key: str, group_keys: list[str]) -> tuple[str, list[dict]]:
    if not rows:
        return "", []
    latest_date = max(r[date_key] for r in rows)
    holdings = []
    for row in rows:
        if row[date_key] != latest_date:
            continue
        item = {k: row[k] for k in group_keys if k in row}
        if "weight" in item:
            item["weight"] = float(item["weight"])
        if "ah_premium" in item:
            item["ah_premium"] = float(item["ah_premium"])
        holdings.append(item)
    holdings.sort(key=lambda x: x.get("weight", 0), reverse=True)
    return latest_date, holdings


def _holding_keys(holdings: list[dict], key: str) -> set[str]:
    return {h[key] for h in holdings}


def _compare_holdings(current: list[dict], projected: list[dict], key: str) -> dict:
    current_keys = _holding_keys(current, key)
    projected_keys = _holding_keys(projected, key)
    return {
        "entries": [h for h in projected if h[key] not in current_keys],
        "exits": [h for h in current if h[key] not in projected_keys],
        "unchanged": projected_keys == current_keys and len(projected_keys) > 0,
    }


def _select_etf_at_date(prices, score, spec, date, prev_holdings: list[str], top_n: int) -> list[str]:
    from qtlight.etf_momentum_rotation import _select_with_hysteresis

    month_score = score.loc[date].dropna()
    if month_score.empty:
        return []

    eligible = month_score.index
    if spec.positive_momentum_filter:
        eligible = month_score[month_score > 0].index
    if spec.ma_filter is not None:
        moving_average = prices.rolling(spec.ma_filter).mean().loc[date]
        eligible = eligible.intersection(moving_average[moving_average < prices.loc[date]].index)

    if spec.min_switch_gap is not None:
        return _select_with_hysteresis(month_score, eligible, prev_holdings, top_n, spec.min_switch_gap)

    return list(month_score.loc[eligible].sort_values(ascending=False).head(top_n).index)


def compute_etf_state() -> dict:
    import pandas as pd

    from qtlight.etf_momentum_rotation import (
        ETF_NAMES,
        TOP_N,
        SPECS,
        _metrics,
        _month_end_selections,
        _monthly_rebalance_dates,
        _score,
        _simulate_drift_with_conditional_rebalance,
        get_hs300_index,
        load_prices,
        run_rotation,
    )

    spec = next(s for s in SPECS if s.name == ETF_STRATEGY)
    prices, _, _ = load_prices("tushare")
    returns = prices.pct_change(fill_method=None)
    score = _score(prices, returns, spec, volumes=None)
    rebalance_dates = _monthly_rebalance_dates(prices.index)
    top_n = spec.top_n if spec.top_n is not None else TOP_N
    selections = _month_end_selections(prices, score, spec, rebalance_dates, top_n)

    _, _, weight_history, _ = _simulate_drift_with_conditional_rebalance(
        prices, returns, selections, rebalance_dates, top_n, spec
    )
    equity, _, diagnostics = run_rotation(prices, spec)

    latest_date = weight_history.index.max()
    drift_row = weight_history.loc[latest_date]
    drift_holdings = []
    for symbol, weight in drift_row.items():
        if float(weight) < 1e-4:
            continue
        drift_holdings.append(
            {
                "symbol": symbol,
                "name": ETF_NAMES.get(symbol, symbol),
                "weight": float(weight),
            }
        )
    drift_holdings.sort(key=lambda x: x["weight"], reverse=True)

    last_rebalance_dates = rebalance_dates[rebalance_dates <= latest_date]
    last_signal_date = last_rebalance_dates.max() if len(last_rebalance_dates) else latest_date
    prev_selected = selections.get(last_signal_date, [])

    projected_symbols = _select_etf_at_date(
        prices, score, spec, latest_date, prev_selected, top_n
    )
    per_name = 1.0 / top_n if projected_symbols else 0.0
    projected_holdings = [
        {
            "symbol": symbol,
            "name": ETF_NAMES.get(symbol, symbol),
            "weight": per_name,
        }
        for symbol in projected_symbols
    ]

    cash_weight = max(0.0, 1.0 - sum(h["weight"] for h in drift_holdings))
    comparison = _compare_holdings(drift_holdings, projected_holdings, "symbol")

    diag = diagnostics.copy()
    strategy_returns = diag["strategy_return"]
    start_dt = _first_on_or_after(equity.index, ETF_NAV_START)
    window = equity.index >= start_dt

    strategy_nav = (equity / equity.loc[start_dt]).loc[window]
    hs300_close = get_hs300_index().reindex(equity.index).ffill()
    hs300_nav = (hs300_close / hs300_close.loc[start_dt]).loc[window]
    hs300_returns = hs300_close.pct_change(fill_method=None).fillna(0.0)

    daily = pd.DataFrame({"strategy_nav": strategy_nav, "hs300_nav": hs300_nav})
    nav_rows = daily_nav_rows(daily, "strategy_nav", "hs300_nav")

    metrics = _metrics(
        strategy_nav,
        strategy_returns.loc[window],
        diag["turnover"].loc[window],
        diag["exposure"].loc[window],
    )
    benchmark_metrics = _metrics(
        hs300_nav,
        hs300_returns.loc[window],
        pd.Series(0.0, index=hs300_nav.index),
        pd.Series(1.0, index=hs300_nav.index),
    )

    summary = json.loads((RESULTS / "etf_momentum_summary.json").read_text())

    _enrich_etf_holdings(drift_holdings)
    _enrich_etf_holdings(projected_holdings)
    _enrich_etf_holdings(comparison["entries"])
    _enrich_etf_holdings(comparison["exits"])

    return {
        "id": "etf",
        "featured_variant": ETF_STRATEGY,
        "execution_note": summary.get("execution_note", ""),
        "latest_rebalance": last_signal_date.date().isoformat(),
        "holdings_as_of": latest_date.date().isoformat(),
        "holdings": drift_holdings,
        "cash_weight": cash_weight,
        "projected_month_end": {
            "signal_date": latest_date.date().isoformat(),
            "holdings": projected_holdings,
            "entries": comparison["entries"],
            "exits": comparison["exits"],
            "unchanged": comparison["unchanged"],
        },
        "metrics": {
            "cagr": metrics["cagr"],
            "sharpe": metrics["sharpe"],
            "max_drawdown": metrics["max_drawdown"],
            "final_nav": metrics["final_nav"],
            "turnover_per_year": metrics["turnover_per_year"],
        },
        "benchmark_metrics": {
            "cagr": benchmark_metrics["cagr"],
            "sharpe": benchmark_metrics["sharpe"],
            "max_drawdown": benchmark_metrics["max_drawdown"],
            "final_nav": benchmark_metrics["final_nav"],
        },
        "nav": nav_rows,
        "nav_start": start_dt.date().isoformat(),
        "cost_bps": summary["transaction_cost_bps"],
        "backtest_start": ETF_NAV_START,
        "backtest_end": latest_date.date().isoformat(),
        "universe": summary["universe"],
    }


def compute_ah_projection(current: list[dict], latest_date: str) -> dict:
    import pandas as pd

    premium = pd.read_csv(RESULTS / "ah_tushare_monthly_premium.csv")
    premium = premium.rename(columns={"Date": "date"})
    premium["date"] = pd.to_datetime(premium["date"])
    premium = premium.sort_values("date")
    signal_row = premium.iloc[-1]
    signal_date = signal_row["date"].date().isoformat()

    pairs = []
    for col in premium.columns:
        if col == "date":
            continue
        val = signal_row[col]
        if pd.isna(val):
            continue
        pairs.append((col, float(val)))
    pairs.sort(key=lambda x: x[1])
    top = pairs[:AH_TOP_N]
    target_weight = 1.0 / len(top) if top else 0.0
    projected = [
        {
            "pair": pair,
            "weight": target_weight,
            "ah_premium": prem,
        }
        for pair, prem in top
    ]
    comparison = _compare_holdings(current, projected, "pair")
    _attach_pair_names(projected)
    _attach_pair_names(comparison["entries"])
    _attach_pair_names(comparison["exits"])
    return {
        "signal_date": signal_date,
        "holdings": projected,
        "entries": comparison["entries"],
        "exits": comparison["exits"],
        "unchanged": comparison["unchanged"],
    }


def build_ah() -> dict:
    import pandas as pd

    metrics = read_csv(RESULTS / "ah_tushare_metrics.csv")[0]
    holdings_rows = read_csv(RESULTS / "ah_tushare_holdings.csv")
    latest_date, holdings = latest_holdings_by_date(holdings_rows, "date", ["pair", "weight", "ah_premium"])
    nav_df = pd.read_csv(RESULTS / "ah_tushare_equity.csv", parse_dates=["date"]).set_index("date")
    strategy_col = "AH_low_premium_top10_tushare"
    bench_col = "CSI300_ETF_proxy"
    start_dt = nav_df.index[0]
    nav_df = nav_df.assign(
        **{
            strategy_col: nav_df[strategy_col] / nav_df[strategy_col].iloc[0],
            bench_col: nav_df[bench_col] / nav_df[bench_col].iloc[0],
        }
    )

    current = _attach_pair_names(
        [
            {
                "pair": h["pair"],
                "weight": h["weight"],
                "ah_premium": h["ah_premium"],
            }
            for h in holdings
        ]
    )

    return {
        "id": "ah",
        "latest_rebalance": latest_date,
        "holdings_as_of": latest_date,
        "holdings": current,
        "projected_month_end": compute_ah_projection(current, latest_date),
        "metrics": {
            "cagr": float(metrics["cagr"]),
            "sharpe": float(metrics["sharpe"]),
            "max_drawdown": float(metrics["max_drawdown"]),
            "final_equity": float(metrics["final_equity"]),
            "turnover_per_year": float(metrics["turnover_per_year"]),
            "average_names": float(metrics["average_names"]),
        },
        "benchmark_metrics": {
            "cagr": float(metrics["benchmark_cagr"]),
            "sharpe": float(metrics["benchmark_sharpe"]),
            "max_drawdown": float(metrics["benchmark_max_drawdown"]),
        },
        "nav": daily_nav_rows(nav_df[[strategy_col, bench_col]], strategy_col, bench_col),
        "nav_start": start_dt.date().isoformat(),
        "cost_bps": float(metrics["trade_cost_bps"]),
        "universe_pairs": int(float(metrics["current_ah_pairs"])),
    }


def compute_dividend_chinext_state() -> dict:
    import pandas as pd
    from dataclasses import replace

    from qtlight.etf_momentum_rotation import (
        SPECS,
        _metrics,
        _month_end_selections,
        _monthly_rebalance_dates,
        _score,
        _simulate_drift_with_conditional_rebalance,
        get_hs300_index,
        load_prices,
        run_rotation,
    )

    summary = json.loads((DIVIDEND_CHINEXT_DIR / "research_summary.json").read_text())
    spec = replace(next(s for s in SPECS if s.name == DIVIDEND_CHINEXT_STRATEGY), top_n=1)

    prices = pd.read_csv(DIVIDEND_CHINEXT_DIR / "pair_close_prices.csv", index_col=0, parse_dates=True)
    returns = prices.pct_change(fill_method=None)
    score = _score(prices, returns, spec, volumes=None)
    rebalance_dates = _monthly_rebalance_dates(prices.index)
    selections = _month_end_selections(prices, score, spec, rebalance_dates, 1)

    _, _, weight_history, _ = _simulate_drift_with_conditional_rebalance(
        prices, returns, selections, rebalance_dates, 1, spec
    )
    equity, _, diagnostics = run_rotation(prices, spec)

    latest_date = weight_history.index.max()
    drift_row = weight_history.loc[latest_date]
    drift_holdings = []
    for symbol, weight in drift_row.items():
        if float(weight) < 1e-4:
            continue
        drift_holdings.append(
            {
                "symbol": symbol,
                "name": PAIR_NAMES.get(symbol, symbol),
                "weight": float(weight),
            }
        )

    last_rebalance_dates = rebalance_dates[rebalance_dates <= latest_date]
    last_signal_date = last_rebalance_dates.max() if len(last_rebalance_dates) else latest_date

    month_score = score.loc[latest_date].dropna()
    projected_symbols = selections.get(latest_date, [])
    if not projected_symbols and not month_score.empty:
        projected_symbols = [month_score.sort_values(ascending=False).index[0]]
    projected_holdings = [
        {"symbol": symbol, "name": PAIR_NAMES.get(symbol, symbol), "weight": 1.0}
        for symbol in projected_symbols
    ]
    comparison = _compare_holdings(drift_holdings, projected_holdings, "symbol")

    load_prices("tushare")
    nav_start = summary["pair_best_metrics"]["start_date"]
    start_dt = _first_on_or_after(equity.index, nav_start)
    window = equity.index >= start_dt

    strategy_nav = (equity / equity.loc[start_dt]).loc[window]
    hs300_close = get_hs300_index().reindex(equity.index).ffill()
    hs300_nav = (hs300_close / hs300_close.loc[start_dt]).loc[window]
    hs300_returns = hs300_close.pct_change(fill_method=None).fillna(0.0)

    daily = pd.DataFrame({"strategy_nav": strategy_nav, "hs300_nav": hs300_nav})
    nav_rows = daily_nav_rows(daily, "strategy_nav", "hs300_nav")

    metrics = _metrics(
        strategy_nav,
        diagnostics["strategy_return"].loc[window],
        diagnostics["turnover"].loc[window],
        diagnostics["exposure"].loc[window],
    )
    benchmark_metrics = _metrics(
        hs300_nav,
        hs300_returns.loc[window],
        pd.Series(0.0, index=hs300_nav.index),
        pd.Series(1.0, index=hs300_nav.index),
    )

    holding_stats = read_csv(DIVIDEND_CHINEXT_DIR / "pair_best_strategy_holding_distribution.csv")

    _attach_symbol_names(drift_holdings, PAIR_NAMES, PAIR_NAMES_EN)
    _attach_symbol_names(projected_holdings, PAIR_NAMES, PAIR_NAMES_EN)
    _attach_symbol_names(comparison["entries"], PAIR_NAMES, PAIR_NAMES_EN)
    _attach_symbol_names(comparison["exits"], PAIR_NAMES, PAIR_NAMES_EN)

    return {
        "id": "dividend",
        "featured_variant": DIVIDEND_CHINEXT_STRATEGY,
        "execution_note": summary.get("execution", ""),
        "latest_rebalance": last_signal_date.date().isoformat(),
        "holdings_as_of": latest_date.date().isoformat(),
        "holdings": drift_holdings,
        "projected_month_end": {
            "signal_date": latest_date.date().isoformat(),
            "holdings": projected_holdings,
            "entries": comparison["entries"],
            "exits": comparison["exits"],
            "unchanged": comparison["unchanged"],
        },
        "metrics": {
            "cagr": metrics["cagr"],
            "sharpe": metrics["sharpe"],
            "max_drawdown": metrics["max_drawdown"],
            "final_nav": metrics["final_nav"],
            "turnover_per_year": metrics["turnover_per_year"],
        },
        "benchmark_metrics": {
            "cagr": benchmark_metrics["cagr"],
            "sharpe": benchmark_metrics["sharpe"],
            "max_drawdown": benchmark_metrics["max_drawdown"],
            "final_nav": benchmark_metrics["final_nav"],
        },
        "nav": nav_rows,
        "nav_start": start_dt.date().isoformat(),
        "cost_bps": 30.0,
        "backtest_start": nav_start,
        "backtest_end": latest_date.date().isoformat(),
        "universe": summary["pair_universe"],
        "holding_stats": [
            {
                "symbol": row["symbol"],
                "name": row["name"],
                "name_en": PAIR_NAMES_EN.get(row["symbol"], row["name"]),
                "pct_months": float(row["pct_months"]),
            }
            for row in holding_stats
        ],
    }


def _enrich_etf_holdings(items: list[dict]) -> list[dict]:
    for item in items:
        item["name_en"] = ETF_NAMES_EN.get(item["symbol"], item.get("name", item["symbol"]))
    return items


def compute_equity_daily_nav() -> tuple[list[dict], str]:
    import pandas as pd

    from qtlight.equity_incentive_optimized_backtest import load_daily_panels

    diagnostics = pd.read_csv(RESULTS / "equity_incentive_optimized_diagnostics.csv")
    diagnostics = diagnostics[
        (diagnostics["strategy"] == EQUITY_STRATEGY) & (diagnostics["cost_bps"] == EQUITY_COST_BPS)
    ].copy()
    diagnostics["rebalance_month"] = pd.to_datetime(diagnostics["rebalance_month"])
    diagnostics = diagnostics.sort_values("rebalance_month")

    holdings = pd.read_csv(RESULTS / "equity_incentive_optimized_holdings.csv")
    holdings = holdings[
        (holdings["strategy"] == EQUITY_STRATEGY) & (holdings["cost_bps"] == EQUITY_COST_BPS)
    ].copy()
    weight_table = (
        holdings.pivot_table(index="rebalance_month", columns="symbol", values="weight", aggfunc="last")
        .fillna(0.0)
    )
    weight_table.index = pd.to_datetime(weight_table.index)

    symbols = sorted(weight_table.columns.tolist())
    panels = load_daily_panels(symbols)
    closes = panels["close"][symbols]
    returns = closes.pct_change(fill_method=None).fillna(0.0)

    bench = pd.read_csv(RESULTS / "ah_tushare_equity.csv", parse_dates=["date"], index_col="date")[
        "CSI300_ETF_proxy"
    ]
    end_month = diagnostics["rebalance_month"].max()
    calendar = closes.index[closes.index <= bench.index.max()]
    calendar = calendar[calendar <= end_month + pd.offsets.MonthEnd(0)]

    exec_targets: dict[pd.Timestamp, pd.Series] = {}
    for _, row in diagnostics.iterrows():
        signal_date = row["rebalance_month"]
        future = calendar[calendar > signal_date]
        if future.empty:
            continue
        exec_date = future[0]
        if row["holding_count"] > 0 and signal_date in weight_table.index:
            target = weight_table.loc[signal_date].reindex(symbols).fillna(0.0)
        else:
            target = pd.Series(0.0, index=symbols)
        exec_targets[exec_date] = target

    asset_weights = pd.Series(0.0, index=symbols)
    cash_weight = 1.0
    strategy_nav = 1.0
    rows: list[dict] = []
    bench_aligned = bench.reindex(calendar).ffill().bfill()
    nav_start = calendar[0]
    bench_base = float(bench_aligned.loc[nav_start])

    for date in calendar:
        if date in exec_targets:
            target = exec_targets[date]
            turnover = float((target - asset_weights).abs().sum() + abs((1.0 - target.sum()) - cash_weight))
            strategy_nav *= 1.0 - turnover * EQUITY_COST_BPS / 10000.0
            asset_weights = target.copy()
            cash_weight = max(0.0, 1.0 - float(target.sum()))

        day_return = float((asset_weights * returns.loc[date]).sum())
        strategy_nav *= 1.0 + day_return

        gross = 1.0 + day_return
        if gross > 0 and (asset_weights.sum() + cash_weight) > 0:
            asset_values = asset_weights * (1.0 + returns.loc[date])
            total = float(asset_values.sum() + cash_weight)
            if total > 0:
                asset_weights = asset_values / total
                cash_weight = cash_weight / total

        bench_nav = float(bench_aligned.loc[date] / bench_base)
        rows.append(
            {
                "date": date.date().isoformat(),
                "equal_weight_all_20bps": strategy_nav,
                "沪深300": bench_nav,
            }
        )

    return rows, nav_start.date().isoformat()


def build_equity() -> dict:
    summary = json.loads((RESULTS / "equity_incentive_optimized_summary.json").read_text())
    event_summary = json.loads((RESULTS / "equity_incentive_event_study_summary.json").read_text())
    holdings_rows = [
        r
        for r in read_csv(RESULTS / "equity_incentive_optimized_holdings.csv")
        if r["strategy"] == EQUITY_STRATEGY and r["cost_bps"] == str(EQUITY_COST_BPS)
    ]
    latest_date, holdings = latest_holdings_by_date(holdings_rows, "rebalance_month", ["symbol", "weight"])
    for h in holdings:
        h["name"] = STOCK_NAMES.get(h["symbol"], h["symbol"])
        h["name_en"] = STOCK_NAMES_EN.get(h["symbol"], h["name"])

    candidates = [r for r in read_csv(RESULTS / "equity_incentive_optimized_candidates.csv") if r["eligible"] == "True"]
    latest_candidates_date = max(r["rebalance_month"] for r in candidates) if candidates else ""
    watchlist = [
        {
            "symbol": r["symbol"],
            "name": r["name"],
            "name_en": STOCK_NAMES_EN.get(r["symbol"], r["name"]),
            "announcement_time": r["announcement_time"][:10],
            "title": r["title_clean"],
        }
        for r in candidates
        if r["rebalance_month"] == latest_candidates_date
    ]

    nav_rows, nav_start = compute_equity_daily_nav()
    best = summary["best_primary_cost_strategy"]

    return {
        "id": "equity",
        "latest_rebalance": latest_date,
        "holdings": holdings,
        "watchlist": watchlist,
        "watchlist_month": latest_candidates_date,
        "metrics": {
            "cagr": best["cagr"],
            "sharpe": best["sharpe"],
            "max_drawdown": best["max_drawdown"],
            "final_nav": best["final_nav"],
            "turnover_per_year": best["turnover_per_year"],
        },
        "event_study": event_summary["summary"],
        "core_events": summary["core_event_rows"],
        "core_symbols": summary["core_symbols"],
        "nav": nav_rows,
        "nav_start": nav_start,
        "cost_bps": EQUITY_COST_BPS,
        "filters": summary["filters"],
    }


def main() -> None:
    import math

    def _sanitize(obj):
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize(v) for v in obj]
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        return obj

    builders = {
        "etf": compute_etf_state,
        "ah": build_ah,
        "dividend": compute_dividend_chinext_state,
        "equity": build_equity,
    }
    strategies = {}
    for key, builder in builders.items():
        strategies[key] = _write_nav_bundle(key, _sanitize(builder()))

    payload = _sanitize(
        {
            "data_version": DATA_VERSION,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "strategy_order": list(builders.keys()),
            "strategies": strategies,
        }
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} (v{DATA_VERSION})")
    for key in builders:
        print(f"  nav/{key}.json -> {strategies[key]['nav_points']} points")


if __name__ == "__main__":
    main()
