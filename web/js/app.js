/* China Stock Strategies Dashboard */

const I18N = {
  zh: {
    brand: "中国股票策略",
    "hero.eyebrow": "量化研究",
    "hero.title": "中国股票策略仪表盘",
    "hero.subtitle": "复合策略 + 四套单策略：当前 Top20 持仓、月底调仓提示与历史净值。",
    loading: "正在加载策略数据…",
    "strategies.composite.short": "复合策略",
    "strategies.etf.short": "ETF 轮动",
    "strategies.ah.short": "AH 折价",
    "strategies.dividend.short": "红利创业板",
    "strategies.equity.short": "股权激励",
    "footer.disclaimer": "仅供研究参考，不构成投资建议。历史回测不代表未来表现。",
    "common.rebalance": "最近调仓",
    "common.nextRebalance": "下次调仓",
    "common.monthEnd": "每月最后一个交易日",
    "common.monthEndNextDay": "次月首个交易日",
    "common.holdNow": "当前应持有",
    "common.performance": "历史表现",
    "common.holdings": "持仓明细",
    "common.rebalanceGuide": "如何调仓",
    "common.strategyNav": "策略净值",
    "common.benchmark": "基准",
    "common.cagr": "年化收益",
    "common.sharpe": "夏普比率",
    "common.maxDd": "最大回撤",
    "common.finalNav": "累计净值",
    "common.turnover": "年换手",
    "common.weight": "权重",
    "common.asset": "资产",
    "common.premium": "AH 溢价",
    "common.discount": "折价",
    "common.premiumLabel": "溢价",
    "common.cost": "交易成本",
    "common.bps": "bps",
    "common.updated": "数据更新",
    "common.holdingsAsOf": "持仓截至",
    "common.navPeriod": "净值区间",
    "common.projectedRebalance": "月底可能调仓",
    "common.projectedDesc": "按截至 {date} 的行情模拟月末信号；若名单变化，次月首个交易日等权执行。",
    "common.projectedUnchanged": "预计持仓名单不变（仅权重随涨跌自然漂移）。",
    "common.newEntry": "新增",
    "common.possibleExit": "可能退出",
    "common.targetWeight": "目标权重",
    "etf.actionTitle": "持有 6M skip-1M 动量排名前 2 的 ETF（权重随涨跌漂移）",
    "etf.actionDesc": "月末按 6 个月动量排名（跳过最近约 1 个月），取前 2 名；仅在名单变化时于次月首个交易日等权调仓，月内权重随价格自然漂移、不再平衡。",
    "etf.guide1.title": "每月末计算信号",
    "etf.guide1.desc": "在月末收盘后，对全部 ETF 计算 6 个月动量（不含最近约 1 个月），按得分从高到低排名。",
    "etf.guide2.title": "次交易日执行",
    "etf.guide2.desc": "T+1 按目标权重调仓，卖出跌出前 2 的 ETF，买入新进入前 2 的 ETF，等权分配。",
    "etf.guide3.title": "何时可能换仓",
    "etf.guide3.desc": "仅当月末排名前 2 的 ETF 名单发生变化时，次月首个交易日等权调仓；若名单不变，权重在月内随涨跌自然漂移，不再平衡。",
    "ah.actionTitle": "持有 AH 溢价最低的 10 只 A 股，等权约 10%",
    "ah.actionDesc": "在 ~194 对 AH 同股中，选取 A 股相对 H 股溢价（discount）最低的 10 只，等权配置 A 股。负溢价 = A 股折价，数值越低越便宜。",
    "ah.guide1.title": "每月末排名",
    "ah.guide1.desc": "计算 premium = A收盘价 / (H收盘价 × 汇率) − 1，按 premium 从低到高排序，取前 10 只。",
    "ah.guide2.title": "次交易日调仓",
    "ah.guide2.desc": "在次月首个交易日执行，等权买入/卖出；若 A 股跌停则当日无法卖出，留现金等待。",
    "ah.guide3.title": "何时可能换仓",
    "ah.guide3.desc": "每月排名变化时替换：新进入 top-10 的 A 股买入，跌出 top-10 的卖出。关注 premium 变化——折价收窄或转溢价时可能被换出。",
    "dividend.actionTitle": "持有 12M 动量更高的一只：红利 ETF 或 创业板 ETF",
    "dividend.actionDesc": "在 510880 红利 ETF 与 159915 创业板 ETF 之间，月末按 12 个月动量二选一满仓持有；仅当标的变化时于次月首个交易日换仓。",
    "dividend.guide1.title": "每月末计算信号",
    "dividend.guide1.desc": "比较两只 ETF 的 12 个月动量得分，选得分更高者作为下月持仓（100% 仓位）。",
    "dividend.guide2.title": "次交易日执行",
    "dividend.guide2.desc": "若月末信号与当前持仓不同，次月首个交易日全仓切换；相同则继续持有。",
    "dividend.guide3.title": "何时可能换仓",
    "dividend.guide3.desc": "仅当动量领先者从红利切到创业板（或反向）时换仓；历史约各持有约一半月份。",
    "dividend.holdingStats": "历史持仓占比",
    "equity.actionTitle": "日频槽位：14×7%，持有 9 个月；ESOP>MA200 入场，满员 MA200 下方换仓",
    "equity.actionDesc": "HS300+CSI500 可交易回测（2017-09 起展示）：日频 7%×14；CAGR ~20.1%，Sharpe ~0.98，最大回撤 ~-27%。",
    "equity.guide1.title": "Tushare 逐股扫描公告",
    "equity.guide1.desc": "anns_d 遍历 5,288 只股票；股权激励保留草案/预案/首次授予；员工持股严格匹配「YYYY年/第N期员工持股计划（草案）」，剔除过户/持有人会议/法律意见等程序性公告。",
    "equity.guide2.title": "最优持有 9–12 个月",
    "equity.guide2.desc": "strict core 约 3,400 事件、770 只有价样本：12M 平均超额 ~+11.9%（t≈8.7）；9M ~+9.7%（t≈8.5）。中位数超额仍为负，需分散持仓。",
    "equity.guide3.title": "日频槽位 vs 事件研究",
    "equity.guide3.desc": "日频 7%×14：公告后首个可交易日收盘买入；ESOP 需 close>MA200；满员时卖出 MA200 下方存量腾位。2017-09 起 CAGR ~20.1%、Sharpe ~0.98。",
    "equity.eventStudy": "全 A 股事件研究（vs 沪深300）",
    "equity.eventStudyMeta": "Strict core · 同股同月首次 · {symbols} 只股票 · {events} 条事件",
    "equity.recommendedHold": "推荐",
    "equity.months": "个月",
    "equity.excessReturn": "平均超额",
    "equity.watchlist": "最新 eligible 候选（待纳入）",
    "equity.coreEvents": "核心事件",
    "equity.symbols": "涉及股票",
    "equity.staleNote": "组合持仓数据截至上述日期；候选池已更新至更近日期，下次调仓时将刷新。",
    "equity.monthEndChanges": "本月调仓变动（月底信号）",
    "equity.monthEndDesc": "按截至 {date} 的持仓与信号，汇总本月已执行及剩余交易日待执行的纳入/剔除（日频策略，有信号即日执行）。",
    "equity.monthEndUnchanged": "本月暂无新增纳入或到期/换仓剔除。",
    "equity.toAdd": "新纳入",
    "equity.toRemove": "剔除",
    "equity.tradeDate": "执行日",
    "equity.tradeReason": "原因",
    "equity.reason.executed": "已执行",
    "equity.reason.pending": "待执行",
    "equity.reason.scheduled": "待到期",
    "equity.reason.esop": "员工持股",
    "equity.reason.equity_incentive": "股权激励",
    "equity.reason.expiry": "9M到期",
    "equity.reason.ma200_swap": "MA200换仓",
    "composite.actionTitle": "低换手复合：AH 50% + 红利/创业板 30% + 月频增量激励",
    "composite.actionDesc": "穿透 Top20；AH 季频持有缓冲且层内权重漂移，行业月频二选一，激励公告后首个可交易月纳入（9 个月，15% cap）。",
    "composite.top20": "组合 Top20 持仓（穿透权重）",
    "composite.sleeve": "层级",
    "composite.monthEndTitle": "月底调仓指引（分三层）",
    "composite.monthEndUnchanged": "三层均无强制调仓；重要持仓按规则继续持有。",
    "composite.monthEndDesc": "截至 {date} 的月末信号模拟；AH 仅 3/6/9/12 月调仓，其余月份持有缓冲。",
    "composite.sleeve.ah": "AH 折价层（50%）",
    "composite.sleeve.industry": "红利/创业板层（30%）",
    "composite.sleeve.incentive": "股权激励层（≤15%）",
    "composite.noChange": "本月无需调整",
    "composite.cash": "现金",
  },
  en: {
    brand: "China Stock Strategies",
    "hero.eyebrow": "Quantitative Research",
    "hero.title": "China Stock Strategy Dashboard",
    "hero.subtitle": "Composite plus four sleeves — Top 20 holdings, month-end rebalance notes, and NAV history.",
    loading: "Loading strategy data…",
    "strategies.composite.short": "Composite",
    "strategies.etf.short": "ETF Rotation",
    "strategies.ah.short": "AH Discount",
    "strategies.dividend.short": "Div / ChiNext",
    "strategies.equity.short": "Equity Incentive",
    "footer.disclaimer": "For research only. Not investment advice. Past performance does not guarantee future results.",
    "common.rebalance": "Last rebalance",
    "common.nextRebalance": "Next rebalance",
    "common.monthEnd": "Last trading day of month",
    "common.monthEndNextDay": "First trading day of next month",
    "common.holdNow": "Hold now",
    "common.performance": "Performance",
    "common.holdings": "Holdings",
    "common.rebalanceGuide": "How to rebalance",
    "common.strategyNav": "Strategy NAV",
    "common.benchmark": "Benchmark",
    "common.cagr": "CAGR",
    "common.sharpe": "Sharpe",
    "common.maxDd": "Max drawdown",
    "common.finalNav": "Final NAV",
    "common.turnover": "Turnover/yr",
    "common.weight": "Weight",
    "common.asset": "Asset",
    "common.premium": "AH premium",
    "common.discount": "Discount",
    "common.premiumLabel": "Premium",
    "common.cost": "Transaction cost",
    "common.bps": "bps",
    "common.updated": "Data updated",
    "common.holdingsAsOf": "Holdings as of",
    "common.navPeriod": "NAV period",
    "common.projectedRebalance": "Possible month-end rebalance",
    "common.projectedDesc": "Simulated month-end signal using data through {date}; equal-weight execution on the first trading day of next month if names change.",
    "common.projectedUnchanged": "Expected same names (weights keep drifting with prices).",
    "common.newEntry": "New",
    "common.possibleExit": "May exit",
    "common.targetWeight": "Target weight",
    "etf.actionTitle": "Hold top-2 ETFs (6M skip-1M momentum); weights drift intra-month",
    "etf.actionDesc": "Rank by 6-month momentum skipping the latest ~1 month at month-end; rebalance equal-weight only when the top-2 set changes on the next month's first trading day. Weights drift naturally within the month.",
    "etf.guide1.title": "Signal at month-end",
    "etf.guide1.desc": "After month-end close, compute 6-month momentum excluding the latest ~1 month for all ETFs, then rank by score.",
    "etf.guide2.title": "Execute T+1",
    "etf.guide2.desc": "Rebalance next trading day to target weights. Sell ETFs falling out of top 2; buy new entrants at equal weight.",
    "etf.guide3.title": "When holdings may change",
    "etf.guide3.desc": "Rebalance equal-weight only when the top-2 set changes at month-end; otherwise weights drift with daily returns and are not rebalanced intra-month.",
    "ah.actionTitle": "Hold 10 lowest AH-premium A-shares, ~10% each",
    "ah.actionDesc": "Among ~194 AH pairs, select 10 A-shares with lowest premium vs H-share (A/H×FX − 1). Equal weight. Negative = A-share discount; lower is cheaper.",
    "ah.guide1.title": "Rank at month-end",
    "ah.guide1.desc": "Compute premium = A close / (H close × FX) − 1. Sort ascending, take bottom 10.",
    "ah.guide2.title": "Rebalance next trading day",
    "ah.guide2.desc": "Execute on first trading day of next month at equal weight. If A-share limit-down, hold cash until sellable.",
    "ah.guide3.title": "When holdings may change",
    "ah.guide3.desc": "Monthly rerank replaces names entering/leaving top 10. Watch premium — narrowing discount or flipping to premium triggers exit.",
    "dividend.actionTitle": "Hold the stronger 12M momentum name: Dividend ETF or ChiNext ETF",
    "dividend.actionDesc": "Between 510880 Dividend ETF and 159915 ChiNext ETF, pick the 12M momentum winner at month-end at 100% weight; switch only when the leader changes, executed next month's first trading day.",
    "dividend.guide1.title": "Signal at month-end",
    "dividend.guide1.desc": "Compare 12-month momentum scores; the higher-scoring ETF is held at full weight next month.",
    "dividend.guide2.title": "Execute T+1",
    "dividend.guide2.desc": "If the month-end signal differs from current holding, switch 100% on the first trading day of next month; otherwise hold.",
    "dividend.guide3.title": "When holdings may change",
    "dividend.guide3.desc": "Switch only when momentum leadership flips between dividend and ChiNext; historically each is held roughly half the time.",
    "dividend.holdingStats": "Historical holding mix",
    "equity.actionTitle": "Daily slots: 14×7%, hold 9M; ESOP>MA200 entry, MA200-below swap when full",
    "equity.actionDesc": "Tradable HS300+CSI500 backtest (display from 2017-09): daily 7%×14; ~20.1% CAGR, Sharpe ~0.98, max DD ~-27%.",
    "equity.guide1.title": "Per-stock Tushare scan",
    "equity.guide1.desc": "anns_d across 5,288 listings; equity incentive keeps draft/plan/first grant; ESOP requires 「YYYY/phase N employee stock plan (draft)」 only.",
    "equity.guide2.title": "Optimal hold: 9–12 months",
    "equity.guide2.desc": "~3,400 strict-core events, 770 priced symbols: 12M mean excess ~+11.9% (t≈8.7); 9M ~+9.7% (t≈8.5). Median excess stays negative — diversify.",
    "equity.guide3.title": "Daily slots vs event study",
    "equity.guide3.desc": "Daily 7%×14: buy at close on first tradable day after announcement; ESOP requires close>MA200; when full, sell MA200-below holdings. ~20.1% CAGR, Sharpe ~0.98 from 2017-09.",
    "equity.eventStudy": "All-A event study (vs CSI 300)",
    "equity.eventStudyMeta": "Strict core · first event per symbol-month · {symbols} stocks · {events} events",
    "equity.recommendedHold": "Best",
    "equity.months": "mo",
    "equity.excessReturn": "Mean excess",
    "equity.watchlist": "Latest eligible candidates",
    "equity.coreEvents": "Core events",
    "equity.symbols": "Symbols",
    "equity.staleNote": "Portfolio holdings as of date above; candidate pool is more recent and will refresh on next rebalance.",
    "equity.monthEndChanges": "This month's changes (month-end signal)",
    "equity.monthEndDesc": "Entries and exits executed or still scheduled this month through {date} (daily strategy — trades on signal days).",
    "equity.monthEndUnchanged": "No new entries or expiry/swap exits this month.",
    "equity.toAdd": "Add",
    "equity.toRemove": "Remove",
    "equity.tradeDate": "Date",
    "equity.tradeReason": "Reason",
    "equity.reason.executed": "Done",
    "equity.reason.pending": "Pending",
    "equity.reason.scheduled": "Due",
    "equity.reason.esop": "ESOP",
    "equity.reason.equity_incentive": "Equity incentive",
    "equity.reason.expiry": "9M expiry",
    "equity.reason.ma200_swap": "MA200 swap",
    "composite.actionTitle": "Low-turnover composite: AH 50% + Div/ChiNext 30% + monthly incremental incentive",
    "composite.actionDesc": "Top 20 look-through; quarterly AH buffer with intra-sleeve drift, monthly industry rotation, incentive enters first tradable month (9M, 15% cap).",
    "composite.top20": "Top 20 holdings (look-through)",
    "composite.sleeve": "Sleeve",
    "composite.monthEndTitle": "Month-end rebalance guide (by sleeve)",
    "composite.monthEndUnchanged": "No required trades across sleeves; key holdings stay per rules.",
    "composite.monthEndDesc": "Month-end simulation as of {date}; AH trades only in Mar/Jun/Sep/Dec — hold buffer otherwise.",
    "composite.sleeve.ah": "AH discount (50%)",
    "composite.sleeve.industry": "Div/ChiNext (30%)",
    "composite.sleeve.incentive": "Equity incentive (≤15%)",
    "composite.noChange": "No change this month",
    "composite.cash": "Cash",
  },
};

const PAIR_NAMES_EN = {
  "510880": "Dividend ETF",
  "159915": "ChiNext ETF",
};

const ETF_NAMES_EN = {
  "513050": "China Internet ETF",
  "159928": "Consumer ETF",
  "510230": "Financials ETF",
  "510880": "Dividend ETF",
  "512120": "Healthcare ETF",
  "512220": "TMT ETF",
  "562910": "Advanced Manufacturing ETF",
  "HYDRO_EQ": "Hydro Equal-Weight",
};

const APP_VERSION = 16;

const STOCK_NAMES_EN = {
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
  "002241": "Goertek",
  "002371": "NAURA Technology",
  "002558": "Giant Network",
  "002624": "Perfect World",
  "300274": "Sungrow Power",
  "300750": "CATL",
  "600438": "Tongwei",
  "603501": "Will Semiconductor",
  "002841": "CVTE",
  "600031": "Sany Heavy Industry",
  "601012": "LONGi Green Energy",
  "002001": "Zhejiang NHU",
};

let lang = localStorage.getItem("lang") || "zh";
let theme = localStorage.getItem("theme") || "light";
let data = null;
let charts = {};
let chartsReady = {};
let activeStrategy = "composite";

const CHART_CONFIG = {
  composite: { canvasId: "chart-composite", strategyField: "strategy_nav", benchField: "hs300_nav" },
  etf: { canvasId: "chart-etf", strategyField: "strategy_nav", benchField: "hs300_nav" },
  ah: { canvasId: "chart-ah", strategyField: "AH_low_premium_top10_tushare", benchField: "CSI300_ETF_proxy" },
  dividend: { canvasId: "chart-dividend", strategyField: "strategy_nav", benchField: "hs300_nav" },
  equity: { canvasId: "chart-equity", strategyField: "strategy_nav", benchField: "hs300_nav" },
};

function t(key) {
  return I18N[lang][key] || key;
}

function pct(v, digits = 1) {
  return `${(v * 100).toFixed(digits)}%`;
}

function fmtNav(v) {
  return v.toFixed(2);
}

function fmtDate(d) {
  if (!d) return "—";
  return d.slice(0, 10);
}

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function isMobileLayout() {
  return window.matchMedia("(max-width: 768px)").matches;
}

function decimateNav(nav, maxPoints = 520) {
  if (!nav?.length || nav.length <= maxPoints) return nav;
  const step = Math.ceil(nav.length / maxPoints);
  const out = [nav[0]];
  for (let i = step; i < nav.length; i += step) out.push(nav[i]);
  const last = nav[nav.length - 1];
  if (out[out.length - 1] !== last) out.push(last);
  return out;
}

function tableWrap(tableHtml) {
  const hint =
    lang === "zh" ? "表格较宽时可左右滑动" : "Swipe horizontally if the table is wider than the screen";
  return `<p class="table-scroll-hint">${hint}</p><div class="table-wrap">${tableHtml}</div>`;
}

/** Base path for static hosting (GitHub Pages project sites, subfolders). */
function webRoot() {
  const path = window.location.pathname;
  if (path.endsWith("/")) return path;
  const last = path.split("/").pop() || "";
  if (last.includes(".")) return path.slice(0, path.lastIndexOf("/") + 1);
  return `${path}/`;
}

function dataUrl(relativePath) {
  return `${webRoot()}${relativePath.replace(/^\//, "")}`;
}

function displaySymbolLabel(strategyKey, item) {
  const zhName = item.name || item.symbol;
  let enName = item.name_en;
  if (!enName && strategyKey === "etf") enName = ETF_NAMES_EN[item.symbol];
  if (!enName && strategyKey === "dividend") enName = PAIR_NAMES_EN[item.symbol];
  if (!enName && strategyKey === "equity") enName = STOCK_NAMES_EN[item.symbol];
  const label = lang === "zh" ? zhName : enName || zhName;
  return item.symbol ? `${item.symbol} ${label}` : label;
}

function displayPairLabel(item) {
  return lang === "zh" ? item.pair : item.pair_en || item.pair;
}

function displayNameOnly(strategyKey, item) {
  return displaySymbolLabel(strategyKey, item).replace(/^\d{6}\s*/, "");
}

function destroyAllCharts() {
  Object.keys(charts).forEach((id) => {
    charts[id]?.destroy();
    delete charts[id];
  });
  chartsReady = {};
}

async function loadStrategyNav(key) {
  const strategy = data?.strategies?.[key];
  if (!strategy) return null;
  if (strategy.nav) return strategy.nav;
  if (!strategy.nav_src) return null;
  const res = await fetch(dataUrl(`data/${strategy.nav_src}?v=${APP_VERSION}`));
  if (!res.ok) throw new Error(`Failed to load ${strategy.nav_src}`);
  strategy.nav = await res.json();
  return strategy.nav;
}

async function loadAllNav() {
  const keys = data.strategy_order || Object.keys(data.strategies);
  await Promise.all(keys.map((key) => loadStrategyNav(key)));
}

function initChartFor(key) {
  const cfg = CHART_CONFIG[key];
  const strategy = data?.strategies?.[key];
  if (!cfg || !strategy?.nav?.length || chartsReady[key]) return;
  renderChart(cfg.canvasId, strategy.nav, key, cfg.strategyField, cfg.benchField);
  chartsReady[key] = true;
}

function renderPanelSafe(key, renderFn) {
  const el = document.getElementById(`panel-${key}`);
  if (!el) return;
  const strategy = data?.strategies?.[key];
  if (!strategy) {
    el.innerHTML = `<p class="note-text">${lang === "zh" ? "策略数据缺失，请运行 build_data.py 重新生成。" : "Strategy data missing. Re-run build_data.py."}</p>`;
    return;
  }
  try {
    renderFn(strategy);
  } catch (err) {
    console.error(`render ${key}`, err);
    el.innerHTML = `<p class="note-text">${lang === "zh" ? "渲染失败：" : "Render error: "}${err.message}</p>`;
  }
}

function applyTheme() {
  document.documentElement.setAttribute("data-theme", theme);
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.textContent = theme === "dark" ? "☾" : "☀";
  let meta = document.querySelector('meta[name="theme-color"][data-dynamic="true"]');
  if (!meta) {
    meta = document.createElement("meta");
    meta.name = "theme-color";
    meta.setAttribute("data-dynamic", "true");
    document.head.appendChild(meta);
  }
  meta.content = theme === "dark" ? "#000000" : "#f5f5f7";
}

function applyI18n() {
  document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (I18N[lang][key]) el.textContent = I18N[lang][key];
  });
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === lang);
  });
}

function renderActionCard(strategyKey, holdings, rebalanceDate, titleKey, descKey, holdingsAsOf) {
  const compact = holdings.length >= 8;
  const holdingsClass = compact ? "action-holdings compact" : "action-holdings";
  const chipClass = compact ? "action-chip compact" : "action-chip";
  const chips = holdings
    .map((h) => {
      const label =
        strategyKey === "ah"
          ? displayPairLabel(h)
          : compact
            ? displayNameOnly(strategyKey, h)
            : displaySymbolLabel(strategyKey, h);
      return `<div class="${chipClass}"><span>${label}</span><span class="weight">${pct(h.weight, 1)}</span></div>`;
    })
    .join("");

  const asOfLine = holdingsAsOf
    ? `<span>${t("common.holdingsAsOf")}: <strong>${fmtDate(holdingsAsOf)}</strong></span>`
    : "";

  return `
    <div class="action-card">
      <div class="action-card-label">${t("common.holdNow")}</div>
      <h2>${t(titleKey)}</h2>
      <p>${t(descKey)}</p>
      <div class="${holdingsClass}">${chips}</div>
      <div class="action-meta">
        ${asOfLine}
        <span>${t("common.rebalance")}: <strong>${fmtDate(rebalanceDate)}</strong></span>
        <span>${t("common.nextRebalance")}: <strong>${t("common.monthEnd")}</strong> → ${t("common.monthEndNextDay")}</span>
      </div>
    </div>`;
}

function equityReasonLabel(reason, status) {
  const statusKey = status ? `equity.reason.${status}` : null;
  const statusText = statusKey && I18N[lang][statusKey] ? I18N[lang][statusKey] : status || "";
  let reasonText = reason || "";
  if (reason === "expiry") reasonText = t("equity.reason.expiry");
  else if (reason === "ma200_swap") reasonText = t("equity.reason.ma200_swap");
  else if (reason === "esop" || reason === "pending_esop") reasonText = t("equity.reason.esop");
  else if (reason === "equity_incentive" || reason === "pending_equity_incentive")
    reasonText = t("equity.reason.equity_incentive");
  else if (reason === "month_end_ma200" || reason === "pending_month_end_ma200")
    reasonText = lang === "zh" ? "月末MA200纳入" : "Month-end MA200 entry";
  else if (reason === "monthly_incremental" || reason === "pending_monthly_incremental")
    reasonText = lang === "zh" ? "月频增量纳入" : "Monthly incremental entry";
  if (statusText && reasonText && statusText !== reasonText) return `${reasonText} · ${statusText}`;
  return reasonText || statusText || "—";
}

function renderEquityChangeRows(rows) {
  if (!rows?.length) {
    return `<p class="note-text">—</p>`;
  }
  return tableWrap(`<table>
      <thead><tr><th>${t("common.asset")}</th><th>${t("common.weight")}</th><th>${t("equity.tradeDate")}</th><th>${t("equity.tradeReason")}</th></tr></thead>
      <tbody>
        ${rows
          .map(
            (h) => `
          <tr class="row-highlight">
            <td><span class="symbol-badge">${h.symbol}</span>${lang === "zh" ? h.name : h.name_en || STOCK_NAMES_EN[h.symbol] || h.name}</td>
            <td>${pct(h.weight, 0)}</td>
            <td>${h.trade_date || "—"}</td>
            <td>${equityReasonLabel(h.reason, h.status)}</td>
          </tr>`
          )
          .join("")}
      </tbody>
    </table>`);
}

function renderEquityMonthEndSection(projection) {
  if (!projection) return "";
  const desc = projection.unchanged
    ? t("equity.monthEndUnchanged")
    : t("equity.monthEndDesc").replace("{date}", fmtDate(projection.signal_date));
  const monthLabel = projection.month || fmtDate(projection.signal_date).slice(0, 7);
  return `
    <div class="card projection-card">
      <div class="card-header">
        <h3 class="card-title">${t("equity.monthEndChanges")}</h3>
        <span class="card-subtitle">${monthLabel}</span>
      </div>
      <p class="note-text">${desc}</p>
      <div class="grid-2" style="margin-top:12px">
        <div>
          <h4 class="card-subtitle">${t("equity.toAdd")}</h4>
          ${renderEquityChangeRows(projection.entries)}
        </div>
        <div>
          <h4 class="card-subtitle">${t("equity.toRemove")}</h4>
          ${renderEquityChangeRows(projection.exits)}
        </div>
      </div>
    </div>`;
}

function renderProjectionSection(strategyKey, projection) {
  if (!projection || !projection.holdings?.length) return "";

  const desc = projection.unchanged
    ? t("common.projectedUnchanged")
    : t("common.projectedDesc").replace("{date}", fmtDate(projection.signal_date));

  const changeTags =
    !projection.unchanged && (projection.entries?.length || projection.exits?.length)
      ? `<div class="projection-changes">
          ${(projection.entries || [])
            .map(
              (h) =>
                `<span class="change-tag entry">${t("common.newEntry")}: ${
                  strategyKey === "ah" ? displayPairLabel(h) : displayNameOnly(strategyKey, h)
                }</span>`
            )
            .join("")}
          ${(projection.exits || [])
            .map(
              (h) =>
                `<span class="change-tag exit">${t("common.possibleExit")}: ${
                  strategyKey === "ah" ? displayPairLabel(h) : displayNameOnly(strategyKey, h)
                }</span>`
            )
            .join("")}
        </div>`
      : "";

  const rows = projection.holdings
    .map((h) => {
      const isEntry = (projection.entries || []).some((e) =>
        strategyKey === "etf" ? e.symbol === h.symbol : e.pair === h.pair
      );
      const assetCell =
        strategyKey === "ah"
          ? displayPairLabel(h)
          : `<span class="symbol-badge">${h.symbol}</span>${lang === "zh" ? h.name : h.name_en || h.name}`;
      const premiumCell =
        strategyKey === "ah" && h.ah_premium != null
          ? `<span class="premium-tag ${h.ah_premium < 0 ? "discount" : "premium"}">${
              h.ah_premium < 0 ? t("common.discount") : t("common.premiumLabel")
            } ${pct(Math.abs(h.ah_premium), 1)}</span>`
          : "—";
      return `
        <tr class="${isEntry ? "row-highlight" : ""}">
          <td>${assetCell}${isEntry ? ` <span class="change-tag inline entry">${t("common.newEntry")}</span>` : ""}</td>
          <td>${pct(h.weight, 1)}</td>
          ${strategyKey === "ah" ? `<td>${premiumCell}</td>` : `<td><div class="weight-bar-wrap"><div class="weight-bar"><div class="weight-bar-fill" style="width:${h.weight * 100}%"></div></div></div></td>`}
        </tr>`;
    })
    .join("");

  const headExtra = strategyKey === "ah" ? `<th>${t("common.premium")}</th>` : `<th></th>`;

  return `
    <div class="card projection-card">
      <div class="card-header">
        <h3 class="card-title">${t("common.projectedRebalance")}</h3>
        <span class="card-subtitle">${fmtDate(projection.signal_date)}</span>
      </div>
      <p class="note-text">${desc}</p>
      ${changeTags}
      ${tableWrap(`<table>
          <thead><tr><th>${t("common.asset")}</th><th>${t("common.targetWeight")}</th>${headExtra}</tr></thead>
          <tbody>${rows}</tbody>
        </table>`)}
    </div>`;
}

function renderMetrics(metrics, benchmarkMetrics, navKey, benchKey) {
  const items = [
    { label: t("common.cagr"), value: pct(metrics.cagr), cls: metrics.cagr >= 0 ? "positive" : "negative" },
    { label: t("common.sharpe"), value: metrics.sharpe.toFixed(2) },
    { label: t("common.maxDd"), value: pct(metrics.max_drawdown ?? metrics.max_dd), cls: "negative" },
    {
      label: t("common.finalNav"),
      value: fmtNav(metrics.final_nav ?? metrics.final_equity),
    },
  ];
  if (metrics.turnover_per_year != null) {
    items.push({ label: t("common.turnover"), value: metrics.turnover_per_year.toFixed(1) + "×" });
  }

  const grid = items
    .slice(0, 4)
    .map(
      (m) => `
      <div class="metric">
        <div class="metric-value ${m.cls || ""}">${m.value}</div>
        <div class="metric-label">${m.label}</div>
      </div>`
    )
    .join("");

  const benchNote =
    benchmarkMetrics &&
    `<p class="card-subtitle" style="margin-top:12px">${t("common.benchmark")}: CAGR ${pct(benchmarkMetrics.cagr)}${
      benchmarkMetrics.sharpe != null ? `, Sharpe ${benchmarkMetrics.sharpe.toFixed(2)}` : ""
    }${benchmarkMetrics.excess_cagr != null ? ` · ${lang === "zh" ? "超额" : "Excess"} ${pct(benchmarkMetrics.excess_cagr ?? metrics.excess_cagr)}` : metrics.excess_cagr != null ? ` · ${lang === "zh" ? "超额" : "Excess"} ${pct(metrics.excess_cagr)}` : ""}</p>`;

  return `<div class="metrics-grid">${grid}</div>${benchNote || ""}`;
}

function navPeriodLabel(s) {
  if (!s.nav_start || !s.nav?.length) return "";
  const end = s.nav[s.nav.length - 1].date;
  return `${t("common.navPeriod")}: ${fmtDate(s.nav_start)} – ${fmtDate(end)} · ${lang === "zh" ? "日度" : "daily"}`;
}

function renderSlotRules(s) {
  const rules = lang === "zh" ? s.rules_zh || [] : s.rules_en || s.rules_zh || [];
  if (!rules.length) return renderGuide("equity");
  return `<ol class="guide-steps">${rules.map((rule) => `<li><span>${rule}</span></li>`).join("")}</ol>`;
}

function slotMetaLabel(s) {
  const meta = s.slot_meta;
  if (!meta) return "";
  const replacement = meta.replacement === "skip" ? (lang === "zh" ? "满员跳过" : "skip when full") : meta.replacement;
  const universe =
    meta.universe === "hs300_csi500"
      ? lang === "zh"
        ? "HS300+CSI500"
        : "HS300 + CSI 500"
      : meta.universe;
  const gross = lang === "zh" ? `gross ${pct(meta.gross_weight, 1)} · 权重随价格漂移` : `gross ${pct(meta.gross_weight, 1)} · weights drift with prices`;
  return lang === "zh"
    ? `${meta.max_slots} 槽 · 单槽目标 ${pct(meta.slot_weight, 0)} · ${gross} · 持有 ${meta.hold_months} 个月 · ${replacement} · ${universe}`
    : `${meta.max_slots} slots · target ${pct(meta.slot_weight, 0)} each · ${gross} · ${meta.hold_months}M hold · ${replacement} · ${universe}`;
}

function renderGuide(prefix) {
  return `
    <ol class="guide-steps">
      <li><strong>${t(`${prefix}.guide1.title`)}</strong><span>${t(`${prefix}.guide1.desc`)}</span></li>
      <li><strong>${t(`${prefix}.guide2.title`)}</strong><span>${t(`${prefix}.guide2.desc`)}</span></li>
      <li><strong>${t(`${prefix}.guide3.title`)}</strong><span>${t(`${prefix}.guide3.desc`)}</span></li>
    </ol>`;
}

function renderChart(canvasId, nav, strategyKey, navField, benchField) {
  const mobile = isMobileLayout();
  const plotNav = decimateNav(nav, mobile ? 360 : 720);
  const labels = plotNav.map((d) => d.date);
  const stratData = plotNav.map((d) => d[navField]);
  const benchData = plotNav.map((d) => d[benchField]);

  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  if (charts[canvasId]) charts[canvasId].destroy();

  const wrap = ctx.parentElement;
  wrap?.querySelector(".chart-legend")?.remove();

  const accent = cssVar("--accent") || "#0071e3";
  const accentSoft = cssVar("--accent-soft") || "rgba(0, 113, 227, 0.08)";
  const benchColor = cssVar("--chart-bench") || "#aeaeb2";
  const gridColor = cssVar("--chart-grid") || "rgba(0,0,0,0.05)";
  const tickColor = cssVar("--text-tertiary") || "#86868b";
  const tooltipBg = cssVar("--tooltip-bg") || "rgba(255,255,255,0.96)";
  const tooltipText = cssVar("--tooltip-text") || "#1d1d1f";
  const tooltipBorder = cssVar("--tooltip-border") || "rgba(0,0,0,0.08)";
  const tickSize = mobile ? 10 : 11;
  const stratLabel = t("common.strategyNav");
  const benchLabel = t("common.benchmark");

  charts[canvasId] = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: stratLabel,
          data: stratData,
          borderColor: accent,
          backgroundColor: accentSoft,
          borderWidth: mobile ? 2.5 : 2,
          pointRadius: 0,
          pointHitRadius: mobile ? 12 : 8,
          tension: 0.2,
          fill: true,
        },
        {
          label: benchLabel,
          data: benchData,
          borderColor: benchColor,
          borderWidth: mobile ? 2 : 1.5,
          pointRadius: 0,
          pointHitRadius: mobile ? 12 : 8,
          tension: 0.2,
          borderDash: [4, 4],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: "index" },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: tooltipBg,
          titleColor: tooltipText,
          bodyColor: tooltipText,
          borderColor: tooltipBorder,
          borderWidth: 1,
          padding: mobile ? 10 : 12,
          cornerRadius: 10,
          displayColors: true,
          boxWidth: 8,
          boxHeight: 8,
          callbacks: {
            title: (items) => (items[0]?.label ? fmtDate(items[0].label) : ""),
            label: (item) => `${item.dataset.label}: ${item.parsed.y.toFixed(2)}`,
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            maxTicksLimit: mobile ? 4 : 6,
            maxRotation: 0,
            autoSkipPadding: mobile ? 12 : 8,
            color: tickColor,
            font: { size: tickSize },
          },
        },
        y: {
          grid: { color: gridColor },
          ticks: {
            color: tickColor,
            font: { size: tickSize },
            maxTicksLimit: mobile ? 5 : 7,
          },
        },
      },
    },
  });

  wrap?.insertAdjacentHTML(
    "beforeend",
    `<div class="chart-legend" aria-hidden="true">
      <span class="legend-item"><span class="legend-dot" style="background:${accent}"></span>${stratLabel}</span>
      <span class="legend-item"><span class="legend-dot" style="background:${benchColor}"></span>${benchLabel}</span>
    </div>`
  );
}

function renderCompositeSleeveRebalance(sleeveKey, projection) {
  if (!projection) return "";
  const titleKey = `composite.sleeve.${sleeveKey}`;
  const note = lang === "zh" ? projection.note_zh : projection.note_en;

  if (projection.unchanged) {
    return `
      <div class="sleeve-rebalance">
        <h4 class="card-subtitle">${t(titleKey)}</h4>
        <p class="note-text">${note || t("composite.noChange")}</p>
      </div>`;
  }

  if (sleeveKey === "incentive") {
    return `
      <div class="sleeve-rebalance">
        <h4 class="card-subtitle">${t(titleKey)}</h4>
        <p class="note-text">${note || ""}</p>
        <div class="grid-2" style="margin-top:8px">
          <div>
            <h5 class="card-subtitle">${t("equity.toAdd")}</h5>
            ${renderEquityChangeRows(projection.entries)}
          </div>
          <div>
            <h5 class="card-subtitle">${t("equity.toRemove")}</h5>
            ${renderEquityChangeRows(projection.exits)}
          </div>
        </div>
      </div>`;
  }

  const entries = projection.entries || [];
  const exits = projection.exits || [];
  const entryTags = entries
    .map((h) => {
      const label =
        sleeveKey === "ah"
          ? displayPairLabel(h)
          : displaySymbolLabel("dividend", h);
      return `<span class="change-tag entry">${t("common.newEntry")}: ${label}</span>`;
    })
    .join("");
  const exitTags = exits
    .map((h) => {
      const label =
        sleeveKey === "ah"
          ? displayPairLabel(h)
          : displaySymbolLabel("dividend", h);
      return `<span class="change-tag exit">${t("common.possibleExit")}: ${label}</span>`;
    })
    .join("");

  return `
    <div class="sleeve-rebalance">
      <h4 class="card-subtitle">${t(titleKey)}</h4>
      <p class="note-text">${note || ""}</p>
      <div class="projection-changes">${entryTags}${exitTags}</div>
    </div>`;
}

function renderCompositeMonthEndSection(projection) {
  if (!projection) return "";
  const desc = projection.unchanged
    ? t("composite.monthEndUnchanged")
    : t("composite.monthEndDesc").replace("{date}", fmtDate(projection.signal_date));
  const monthLabel = projection.month || fmtDate(projection.signal_date).slice(0, 7);
  return `
    <div class="card projection-card">
      <div class="card-header">
        <h3 class="card-title">${t("composite.monthEndTitle")}</h3>
        <span class="card-subtitle">${monthLabel}</span>
      </div>
      <p class="note-text">${desc}</p>
      <div class="sleeve-rebalance-grid">
        ${renderCompositeSleeveRebalance("ah", projection.ah)}
        ${renderCompositeSleeveRebalance("industry", projection.industry)}
        ${renderCompositeSleeveRebalance("incentive", projection.incentive)}
      </div>
    </div>`;
}

function renderCompositePanel(s) {
  const el = document.getElementById("panel-composite");
  const sw = s.sleeve_weights || {};
  const sleeveMeta =
    lang === "zh"
      ? `AH ${pct(sw.ah || 0.5, 0)} · 行业 ${pct(sw.industry || 0.3, 0)} · 激励 cap ${pct(sw.incentive_cap || 0.15, 0)} · 激励 gross ${pct(s.sleeves?.incentive?.gross_weight || 0, 0)}`
      : `AH ${pct(sw.ah || 0.5, 0)} · Industry ${pct(sw.industry || 0.3, 0)} · Incentive cap ${pct(sw.incentive_cap || 0.15, 0)} · gross ${pct(s.sleeves?.incentive?.gross_weight || 0, 0)}`;
  const ahDriftNote =
    lang === "zh"
      ? s.sleeves?.ah?.weight_note_zh || "AH 层内权重随价格漂移"
      : s.sleeves?.ah?.weight_note_en || "AH sleeve weights drift with prices";

  const top20Rows = (s.holdings || [])
    .map((h) => {
      const sleeve = lang === "zh" ? h.sleeve_zh : h.sleeve_en;
      const asset =
        h.sleeve === "ah"
          ? `${displayPairLabel(h)} <span class="symbol-badge">${h.symbol}</span>`
          : `<span class="symbol-badge">${h.symbol}</span>${lang === "zh" ? h.name : h.name_en || STOCK_NAMES_EN[h.symbol] || h.name}`;
      const premCell =
        h.ah_premium != null
          ? `<span class="premium-tag ${h.ah_premium < 0 ? "discount" : "premium"}">${
              h.ah_premium < 0 ? t("common.discount") : t("common.premiumLabel")
            } ${pct(Math.abs(h.ah_premium), 1)}</span>`
          : "—";
      return `
        <tr>
          <td><span class="sleeve-tag">${sleeve}</span></td>
          <td>${asset}</td>
          <td>${pct(h.weight, 1)}</td>
          <td>${premCell}</td>
        </tr>`;
    })
    .join("");

  const cashRow =
    s.cash_weight > 0.001
      ? `<tr><td>—</td><td>${t("composite.cash")}</td><td>${pct(s.cash_weight, 1)}</td><td>—</td></tr>`
      : "";

  el.innerHTML = `
    <div class="action-card">
      <div class="action-card-label">${t("common.holdNow")}</div>
      <h2>${t("composite.actionTitle")}</h2>
      <p>${t("composite.actionDesc")}</p>
      <p class="note-text">${sleeveMeta}</p>
      <p class="note-text">${ahDriftNote}</p>
      <div class="action-meta">
        <span>${t("common.holdingsAsOf")}: <strong>${fmtDate(s.holdings_as_of)}</strong></span>
        <span>${t("common.rebalance")}: <strong>${fmtDate(s.latest_rebalance)}</strong></span>
      </div>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">${t("common.performance")}</h3>
          <span class="card-subtitle">${s.featured_variant || "low_turnover"}</span>
        </div>
        ${renderMetrics(s.metrics, s.benchmark_metrics)}
        <p class="card-subtitle">${t("common.cost")}: ${s.cost_bps} ${t("common.bps")}</p>
      </div>
      <div class="card">
        <div class="card-header"><h3 class="card-title">${t("common.rebalanceGuide")}</h3></div>
        ${renderSlotRules(s)}
      </div>
    </div>
    <div class="card" style="margin-bottom:20px">
      <div class="card-header">
        <h3 class="card-title">${t("common.performance")} · NAV</h3>
        <span class="card-subtitle">${navPeriodLabel(s)}</span>
      </div>
      <div class="chart-wrap"><canvas id="chart-composite"></canvas></div>
    </div>
    <div class="card" style="margin-bottom:20px">
      <div class="card-header">
        <h3 class="card-title">${t("composite.top20")}</h3>
        <span class="card-subtitle">${t("common.holdingsAsOf")} ${fmtDate(s.holdings_as_of)} · ${s.holdings_all_count || s.holdings?.length || 0} ${lang === "zh" ? "只穿透持仓" : "look-through names"} · ${lang === "zh" ? "含漂移" : "drifted"}</span>
      </div>
      ${tableWrap(`<table>
          <thead><tr><th>${t("composite.sleeve")}</th><th>${t("common.asset")}</th><th>${t("common.weight")}</th><th>${t("common.premium")}</th></tr></thead>
          <tbody>${top20Rows}${cashRow}</tbody>
        </table>`)}
    </div>
    ${renderCompositeMonthEndSection(s.projected_month_end)}`;
}

function renderEtfPanel(s) {
  const el = document.getElementById("panel-etf");
  el.innerHTML = `
    ${renderActionCard("etf", s.holdings, s.latest_rebalance, "etf.actionTitle", "etf.actionDesc", s.holdings_as_of)}
    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">${t("common.performance")}</h3>
          <span class="card-subtitle">${s.featured_variant}</span>
        </div>
        ${renderMetrics(s.metrics, s.benchmark_metrics)}
        <p class="card-subtitle">${t("common.cost")}: ${s.cost_bps} ${t("common.bps")}</p>
      </div>
      <div class="card">
        <div class="card-header"><h3 class="card-title">${t("common.rebalanceGuide")}</h3></div>
        ${renderGuide("etf")}
      </div>
    </div>
    <div class="card" style="margin-bottom:20px">
      <div class="card-header">
        <h3 class="card-title">${t("common.performance")} · NAV</h3>
        <span class="card-subtitle">${navPeriodLabel(s)}</span>
      </div>
      <div class="chart-wrap"><canvas id="chart-etf"></canvas></div>
    </div>
    <div class="card" style="margin-bottom:20px">
      <div class="card-header">
        <h3 class="card-title">${t("common.holdings")}</h3>
        <span class="card-subtitle">${t("common.holdingsAsOf")} ${fmtDate(s.holdings_as_of)} · ${lang === "zh" ? "月内漂移权重" : "drifted weights"}</span>
      </div>
      ${tableWrap(`<table>
          <thead><tr><th>${t("common.asset")}</th><th>${t("common.weight")}</th><th></th></tr></thead>
          <tbody>
            ${s.holdings
              .map(
                (h) => `
              <tr>
                <td><span class="symbol-badge">${h.symbol}</span>${lang === "zh" ? h.name : h.name_en || ETF_NAMES_EN[h.symbol] || h.name}</td>
                <td>${pct(h.weight, 1)}</td>
                <td><div class="weight-bar-wrap"><div class="weight-bar"><div class="weight-bar-fill" style="width:${h.weight * 100}%"></div></div></div></td>
              </tr>`
              )
              .join("")}
          </tbody>
        </table>`)}
    </div>
    ${renderProjectionSection("etf", s.projected_month_end)}`;
}

function renderAhPanel(s) {
  const el = document.getElementById("panel-ah");
  el.innerHTML = `
    ${renderActionCard("ah", s.holdings, s.latest_rebalance, "ah.actionTitle", "ah.actionDesc", s.holdings_as_of)}
    <div class="grid-2">
      <div class="card">
        <div class="card-header"><h3 class="card-title">${t("common.performance")}</h3></div>
        ${renderMetrics(s.metrics, s.benchmark_metrics)}
        <p class="card-subtitle">${t("common.cost")}: ${s.cost_bps} ${t("common.bps")} · ~${s.universe_pairs} AH pairs</p>
      </div>
      <div class="card">
        <div class="card-header"><h3 class="card-title">${t("common.rebalanceGuide")}</h3></div>
        ${renderGuide("ah")}
      </div>
    </div>
    <div class="card" style="margin-bottom:20px">
      <div class="card-header">
        <h3 class="card-title">NAV</h3>
        <span class="card-subtitle">${navPeriodLabel(s)}</span>
      </div>
      <div class="chart-wrap"><canvas id="chart-ah"></canvas></div>
    </div>
    <div class="card" style="margin-bottom:20px">
      <div class="card-header">
        <h3 class="card-title">${t("common.holdings")}</h3>
        <span class="card-subtitle">${t("common.holdingsAsOf")} ${fmtDate(s.holdings_as_of)} · ${lang === "zh" ? "月内漂移权重" : "drifted weights"}</span>
      </div>
      ${tableWrap(`<table>
          <thead><tr><th>${t("common.asset")}</th><th>${t("common.weight")}</th><th>${t("common.premium")}</th></tr></thead>
          <tbody>
            ${s.holdings
              .map((h) => {
                const prem = h.ah_premium;
                const cls = prem < 0 ? "discount" : "premium";
                const label = prem < 0 ? t("common.discount") : t("common.premiumLabel");
                return `
              <tr>
                <td>${displayPairLabel(h)}</td>
                <td>${pct(h.weight, 1)}</td>
                <td><span class="premium-tag ${cls}">${label} ${pct(Math.abs(prem), 1)}</span></td>
              </tr>`;
              })
              .join("")}
          </tbody>
        </table>`)}
    </div>
    ${renderProjectionSection("ah", s.projected_month_end)}`;
}

function renderDividendPanel(s) {
  const stats =
    s.holding_stats
      ?.map((h) => `${lang === "zh" ? h.name : h.name_en || PAIR_NAMES_EN[h.symbol] || h.name} ${h.pct_months.toFixed(0)}%`)
      .join(" · ") || "";

  const el = document.getElementById("panel-dividend");
  el.innerHTML = `
    ${renderActionCard("dividend", s.holdings, s.latest_rebalance, "dividend.actionTitle", "dividend.actionDesc", s.holdings_as_of)}
    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">${t("common.performance")}</h3>
          <span class="card-subtitle">${s.featured_variant}</span>
        </div>
        ${renderMetrics(s.metrics, s.benchmark_metrics)}
        <p class="card-subtitle">${t("common.cost")}: ${s.cost_bps} ${t("common.bps")}</p>
        ${stats ? `<p class="card-subtitle">${t("dividend.holdingStats")}: ${stats}</p>` : ""}
      </div>
      <div class="card">
        <div class="card-header"><h3 class="card-title">${t("common.rebalanceGuide")}</h3></div>
        ${renderGuide("dividend")}
      </div>
    </div>
    <div class="card" style="margin-bottom:20px">
      <div class="card-header">
        <h3 class="card-title">${t("common.performance")} · NAV</h3>
        <span class="card-subtitle">${navPeriodLabel(s)}</span>
      </div>
      <div class="chart-wrap"><canvas id="chart-dividend"></canvas></div>
    </div>
    <div class="card" style="margin-bottom:20px">
      <div class="card-header">
        <h3 class="card-title">${t("common.holdings")}</h3>
        <span class="card-subtitle">${t("common.holdingsAsOf")} ${fmtDate(s.holdings_as_of)}</span>
      </div>
      ${tableWrap(`<table>
          <thead><tr><th>${t("common.asset")}</th><th>${t("common.weight")}</th><th></th></tr></thead>
          <tbody>
            ${s.holdings
              .map(
                (h) => `
              <tr>
                <td><span class="symbol-badge">${h.symbol}</span>${lang === "zh" ? h.name : h.name_en || PAIR_NAMES_EN[h.symbol] || h.name}</td>
                <td>${pct(h.weight, 1)}</td>
                <td><div class="weight-bar-wrap"><div class="weight-bar"><div class="weight-bar-fill" style="width:${h.weight * 100}%"></div></div></div></td>
              </tr>`
              )
              .join("")}
          </tbody>
        </table>`)}
    </div>
    ${renderProjectionSection("dividend", s.projected_month_end)}`;
}

function renderEquityPanel(s) {
  const meta = s.event_study_meta || {};
  const bestMonths = meta.best_holding_months || 9;
  const metaLabel = t("equity.eventStudyMeta")
    .replace("{symbols}", meta.core_symbols ?? s.core_symbols ?? "—")
    .replace("{events}", meta.core_events ?? s.core_events ?? "—");

  const horizons = (s.event_study || [])
    .map((h) => {
      const months = h.horizon_months;
      const recommended = months === bestMonths;
      return `
    <div class="horizon-card${recommended ? " recommended" : ""}">
      <div class="period">${months}${t("equity.months")}${recommended ? ` · ${t("equity.recommendedHold")}` : ""}</div>
      <div class="alpha">+${pct(h.mean_excess_return, 1)}</div>
      <div class="tstat">t = ${h.excess_t_stat.toFixed(1)}</div>
    </div>`;
    })
    .join("");

  const watchlistRows =
    s.watchlist && s.watchlist.length
      ? s.watchlist
          .map(
            (w) => `
        <tr>
          <td><span class="symbol-badge">${w.symbol}</span>${lang === "zh" ? w.name : w.name_en || STOCK_NAMES_EN[w.symbol] || w.name}</td>
          <td>${w.announcement_time}</td>
          <td class="cell-title">${w.title}</td>
        </tr>`
          )
          .join("")
      : "";

  const el = document.getElementById("panel-equity");
  el.innerHTML = `
    ${renderActionCard("equity", s.holdings, s.latest_rebalance, "equity.actionTitle", "equity.actionDesc")}
    ${s.slot_meta ? `<p class="note-text">${slotMetaLabel(s)}</p>` : ""}
    <p class="note-text">${t("equity.staleNote")}</p>
    <div class="grid-2">
      <div class="card">
        <div class="card-header"><h3 class="card-title">${t("common.performance")}</h3></div>
        ${renderMetrics(s.metrics, s.benchmark_metrics)}
        <p class="card-subtitle">${t("equity.coreEvents")}: ${s.core_events} · ${t("equity.symbols")}: ${s.core_symbols}</p>
      </div>
      <div class="card">
        <div class="card-header"><h3 class="card-title">${t("equity.eventStudy")}</h3></div>
        <p class="card-subtitle">${metaLabel}</p>
        <div class="horizon-grid">${horizons}</div>
      </div>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-header"><h3 class="card-title">${t("common.rebalanceGuide")}</h3></div>
        ${renderSlotRules(s)}
        <div style="margin-top:16px">${renderGuide("equity")}</div>
      </div>
      <div class="card">
        <div class="card-header"><h3 class="card-title">${t("common.holdings")}</h3></div>
        ${tableWrap(`<table>
            <thead><tr><th>${t("common.asset")}</th><th>${t("common.weight")}</th></tr></thead>
            <tbody>
              ${s.holdings
                .map(
                  (h) => `
                <tr>
                  <td><span class="symbol-badge">${h.symbol}</span>${lang === "zh" ? h.name : h.name_en || STOCK_NAMES_EN[h.symbol] || h.name}</td>
                  <td>${pct(h.weight, 0)}</td>
                </tr>`
                )
                .join("")}
            </tbody>
          </table>`)}
      </div>
    </div>
    ${renderEquityMonthEndSection(s.projected_month_end)}
    ${
      watchlistRows
        ? `
    <div class="card" style="margin-top:20px">
      <div class="card-header">
        <h3 class="card-title">${t("equity.watchlist")}</h3>
        <span class="card-subtitle">${s.watchlist_month}</span>
      </div>
      ${tableWrap(`<table>
          <thead><tr><th>${t("common.asset")}</th><th>${lang === "zh" ? "公告日" : "Announced"}</th><th>${lang === "zh" ? "公告标题" : "Title"}</th></tr></thead>
          <tbody>${watchlistRows}</tbody>
        </table>`)}
    </div>`
        : ""
    }
    <div class="card" style="margin-top:20px">
      <div class="card-header">
        <h3 class="card-title">NAV</h3>
        <span class="card-subtitle">${navPeriodLabel(s)}</span>
      </div>
      <div class="chart-wrap"><canvas id="chart-equity"></canvas></div>
    </div>`;
}

function renderAll() {
  if (!data) return;
  destroyAllCharts();
  renderPanelSafe("composite", renderCompositePanel);
  renderPanelSafe("etf", renderEtfPanel);
  renderPanelSafe("ah", renderAhPanel);
  renderPanelSafe("dividend", renderDividendPanel);
  renderPanelSafe("equity", renderEquityPanel);
  document.getElementById("data-timestamp").textContent = `${t("common.updated")}: ${data.generated_at}`;
  initChartFor(activeStrategy);
}

function switchStrategy(key) {
  activeStrategy = key;
  document.querySelectorAll(".segment-btn").forEach((btn) => {
    const active = btn.dataset.strategy === key;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-selected", active);
  });
  document.querySelectorAll(".strategy-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `panel-${key}`);
  });
  initChartFor(key);
}

async function init() {
  applyTheme();
  applyI18n();

  document.getElementById("theme-toggle")?.addEventListener("click", () => {
    theme = theme === "light" ? "dark" : "light";
    localStorage.setItem("theme", theme);
    applyTheme();
    renderAll();
  });

  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      lang = btn.dataset.lang;
      localStorage.setItem("lang", lang);
      applyI18n();
      renderAll();
    });
  });

  document.querySelectorAll(".segment-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchStrategy(btn.dataset.strategy));
  });

  try {
    const res = await fetch(dataUrl(`data/strategies.json?v=${APP_VERSION}`));
    if (!res.ok) throw new Error(`strategies.json HTTP ${res.status}`);
    data = await res.json();
    await loadAllNav();
    document.getElementById("loading").classList.add("hidden");
    document.getElementById("panels").classList.remove("hidden");
    renderAll();
  } catch (err) {
    document.getElementById("loading").textContent =
      lang === "zh" ? "加载失败，请通过本地服务器打开。" : "Failed to load data. Serve via local HTTP server.";
    console.error(err);
  }
}

document.addEventListener("DOMContentLoaded", init);

let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    if (!data) return;
    destroyAllCharts();
    chartsReady = {};
    initChartFor(activeStrategy);
  }, 180);
});
