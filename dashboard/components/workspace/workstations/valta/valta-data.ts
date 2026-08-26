// HOUSE OF VALTA — demo data.
// All values below are clearly isolated placeholder numbers. No live market
// feeds, broker APIs, or journal DB are connected. Each section is shaped so a
// future data source can replace it without redesigning the components.
// Replace the exports (not the component logic) to go live.

import type { BaseIcon, ResultTone } from "./types";

export const HOUSE_TITLE = "HOUSE OF VALTA";

// ── Internal dock destinations ──────────────────────────────────────────────
export type TradingViewId =
  | "dashboard"
  | "calendar"
  | "journal"
  | "reports";

export interface TradingViewMeta {
  id: TradingViewId;
  label: string;
  shortLabel: string;
  subtitle: string;
  icon: BaseIcon;
}

export const TRADING_VIEWS: TradingViewMeta[] = [
  { id: "dashboard", label: "Main Dashboard", shortLabel: "Dash", subtitle: "Command centre", icon: "dashboard" },
  { id: "calendar", label: "Trading Calendar", shortLabel: "Calendar", subtitle: "Daily performance", icon: "calendar" },
  { id: "journal", label: "Trading Journal", shortLabel: "Journal", subtitle: "Trade decisions", icon: "journal" },
  { id: "reports", label: "Reports", shortLabel: "Reports", subtitle: "Deep analytics", icon: "reports" },
];

// Authority boundary — surfaced in the UI, never implying auto-execution.
export const VALTA_AUTHORITY =
  "Valta Prime analyses, monitors, researches, prepares, challenges, notifies and coaches. It cannot execute, modify or close trades.";

// ── KPI row (exactly the five requested) ────────────────────────────────────
export interface Kpi {
  key: string;
  label: string;
  value: string;
  delta: string;
  trend: "up" | "down" | "flat";
  series: number[];
}

export const kpis: Kpi[] = [
  { key: "total-profits", label: "Total Profit", value: "$14,790", delta: "+12.6%", trend: "up", series: [62, 78, 74, 92, 101, 118, 122, 147] },
  { key: "net-profit", label: "Net Profit", value: "$9,410", delta: "+8.3%", trend: "up", series: [58, 64, 60, 71, 82, 79, 90, 94] },
  { key: "profit-factor", label: "Profit Factor", value: "2.41", delta: "+0.18", trend: "up", series: [40, 46, 48, 45, 55, 52, 56, 58] },
  { key: "win-rate", label: "Win Rate", value: "64.8%", delta: "+2.1%", trend: "up", series: [48, 51, 50, 55, 58, 57, 61, 60] },
  { key: "total-trades", label: "Total Trades", value: "214", delta: "14 this week", trend: "flat", series: [30, 34, 33, 38, 40, 39, 42, 44] },
];

// ── Equity / profit growth series (primary chart) ───────────────────────────
export interface EquityPoint {
  label: string;
  equity: number; // account equity in USD
}

// Equity curve — placeholder, ending well above start with realistic drawdowns.
export const equitySeries: EquityPoint[] = [
  { label: "W1", equity: 10000 },
  { label: "W2", equity: 10420 },
  { label: "W3", equity: 10280 },
  { label: "W4", equity: 10990 },
  { label: "W5", equity: 11240 },
  { label: "W6", equity: 11080 },
  { label: "W7", equity: 11630 },
  { label: "W8", equity: 12050 },
  { label: "W9", equity: 11890 },
  { label: "W10", equity: 12470 },
  { label: "W11", equity: 12810 },
  { label: "W12", equity: 12640 },
  { label: "W13", equity: 13220 },
  { label: "W14", equity: 13650 },
  { label: "W15", equity: 13410 },
  { label: "W16", equity: 14080 },
  { label: "W17", equity: 14420 },
  { label: "W18", equity: 14290 },
  { label: "W19", equity: 14930 },
  { label: "W20", equity: 15360 },
  { label: "W21", equity: 15120 },
  { label: "W22", equity: 15740 },
  { label: "W23", equity: 16210 },
  { label: "W24", equity: 16820 },
];

// ── Profit distribution (donut) ─────────────────────────────────────────────
export interface DistributionSlice {
  key: string;
  label: string;
  count: number;
  value: number; // aggregate P/L in USD
  tone: "win" | "loss" | "breakeven";
}

export const profitDistribution: DistributionSlice[] = [
  { key: "wins", label: "Winning trades", count: 139, value: 14790, tone: "win" },
  { key: "losses", label: "Losing trades", count: 61, value: -5380, tone: "loss" },
  { key: "breakeven", label: "Breakeven", count: 14, value: 0, tone: "breakeven" },
];

// ── Trade breakdown by instrument ───────────────────────────────────────────
export interface InstrumentBreakdown {
  key: string;
  instrument: string;
  name: string;
  trades: number;
  wins: number;
  losses: number;
  pl: number; // USD
  winRate: number; // %
}

export const instrumentBreakdown: InstrumentBreakdown[] = [
  { key: "xauusd", instrument: "XAUUSD", name: "Gold", trades: 24, wins: 17, losses: 7, pl: 4210, winRate: 70.8 },
  { key: "us30", instrument: "US30", name: "Wall Street 30", trades: 12, wins: 8, losses: 4, pl: 1260, winRate: 66.7 },
];

// Placeholder slot — shows the list is intended to grow. Not a live instrument.
export const instrumentPlaceholder: InstrumentBreakdown = {
  key: "next",
  instrument: "—",
  name: "Add instrument",
  trades: 0,
  wins: 0,
  losses: 0,
  pl: 0,
  winRate: 0,
};

// ── Monthly performance (bar chart) ─────────────────────────────────────────
export interface MonthResult {
  month: string;
  profit: number; // USD
  loss: number;   // USD (positive magnitude)
  net: number;    // USD
}

export const monthlySeries: MonthResult[] = [
  { month: "Mar", profit: 1890, loss: 720, net: 1170 },
  { month: "Apr", profit: 1620, loss: 940, net: 680 },
  { month: "May", profit: 2140, loss: 610, net: 1530 },
  { month: "Jun", profit: 1380, loss: 1180, net: 200 },
  { month: "Jul", profit: 2410, loss: 840, net: 1570 },
  { month: "Aug", profit: 2630, loss: 690, net: 1940 },
];

// ── Recent trading activity ─────────────────────────────────────────────────
export interface RecentTrade {
  id: string;
  instrument: string;
  direction: "BUY" | "SELL";
  entry: string;
  result: ResultTone;
  pl: number; // USD
  lot: string;
  date: string;
}

export const recentTrades: RecentTrade[] = [
  { id: "t1", instrument: "XAUUSD", direction: "BUY", entry: "2384.5", result: "win", pl: 420, lot: "0.20", date: "17 Aug" },
  { id: "t2", instrument: "US30", direction: "SELL", entry: "41062", result: "win", pl: 185, lot: "0.10", date: "17 Aug" },
  { id: "t3", instrument: "XAUUSD", direction: "BUY", entry: "2371.8", result: "loss", pl: -120, lot: "0.15", date: "16 Aug" },
  { id: "t4", instrument: "XAUUSD", direction: "SELL", entry: "2392.0", result: "win", pl: 335, lot: "0.20", date: "16 Aug" },
  { id: "t5", instrument: "US30", direction: "BUY", entry: "40980", result: "win", pl: 96, lot: "0.10", date: "15 Aug" },
  { id: "t6", instrument: "XAUUSD", direction: "BUY", entry: "2368.2", result: "breakeven", pl: 0, lot: "0.10", date: "15 Aug" },
  { id: "t7", instrument: "US30", direction: "BUY", entry: "41140", result: "loss", pl: -85, lot: "0.15", date: "14 Aug" },
  { id: "t8", instrument: "XAUUSD", direction: "BUY", entry: "2379.0", result: "win", pl: 268, lot: "0.20", date: "14 Aug" },
];

// ── Live market intelligence ────────────────────────────────────────────────
export interface NewsItem {
  id: string;
  category: NewsCategory;
  headline: string;
  summary: string;
  source: string;
  time: string;
  importance: "breaking" | "high" | "medium" | "low";
}

export type NewsCategory =
  | "Market News"
  | "Macro"
  | "Central Banks"
  | "Institutional"
  | "Commodities"
  | "Equities";

export const newsCategories: NewsCategory[] = [
  "Market News",
  "Macro",
  "Central Banks",
  "Institutional",
  "Commodities",
  "Equities",
];

export const newsFeed: NewsItem[] = [
  {
    id: "n1",
    category: "Market News",
    headline: "Gold breaks above $2,390 following unexpected central-bank policy announcement",
    summary: "Spot bullion surged on safe-haven demand as a surprise policy shift re-priced rate-cut expectations.",
    source: "Reuters",
    time: "2 min ago",
    importance: "breaking",
  },
  {
    id: "n2",
    category: "Commodities",
    headline: "Oil steadies as inventories draw offset by demand concerns",
    summary: "Prices held a narrow band after mixed weekly inventory and forward-demand signals.",
    source: "Bloomberg",
    time: "11 min ago",
    importance: "medium",
  },
  {
    id: "n3",
    category: "Central Banks",
    headline: "Fed officials signal data-dependent path into Q3",
    summary: "Multiple speakers reiterated a patient approach, keeping near-term volatility elevated.",
    source: "MarketWatch",
    time: "24 min ago",
    importance: "high",
  },
  {
    id: "n4",
    category: "Macro",
    headline: "Core CPI comes in at 3.2%, slightly above consensus",
    summary: "The print strengthened the case for a later easing cycle and lifted bond yields.",
    source: "Reuters",
    time: "38 min ago",
    importance: "high",
  },
  {
    id: "n5",
    category: "Equities",
    headline: "US30 futures point to a marginally firmer open",
    summary: "Index futures ticked higher, tracking strength in rate-sensitive technology names.",
    source: "CNBC",
    time: "1 hr ago",
    importance: "low",
  },
  {
    id: "n6",
    category: "Institutional",
    headline: "Gold ETF holdings rise for a second consecutive week",
    summary: "Institutional allocations continue to accumulate, supporting the bullish metal narrative.",
    source: "World Gold Council",
    time: "2 hrs ago",
    importance: "medium",
  },
  {
    id: "n7",
    category: "Central Banks",
    headline: "Bank of Japan minutes awaited for currency guidance",
    summary: "Traders position ahead of commentary on intervention and the pace of normalisation.",
    source: "Nikkei",
    time: "3 hrs ago",
    importance: "low",
  },
];

export interface InstitutionalIntel {
  id: string;
  kind: string;
  detail: string;
  source: string;
  time: string;
  tone: "bullish" | "bearish" | "neutral";
}

export const institutionalIntel: InstitutionalIntel[] = [
  {
    id: "i1",
    kind: "Central bank activity",
    detail: "Gold reserves increased by a reported 12 tonnes across two EM central banks.",
    source: "World Gold Council",
    time: "Today",
    tone: "bullish",
  },
  {
    id: "i2",
    kind: "Large positioning",
    detail: "Managed-money net-long on gold extended to a 9-week high.",
    source: "CFTC COT",
    time: "Yesterday",
    tone: "bullish",
  },
  {
    id: "i3",
    kind: "Major bank commentary",
    detail: "Bank strategist lifts 12-month gold forecast, citing real-rate trajectory.",
    source: "Goldman Sachs",
    time: "Yesterday",
    tone: "bullish",
  },
  {
    id: "i4",
    kind: "Significant flows",
    detail: "Spot volumes spiked during the London fix; liquidity broadly two-way.",
    source: "Interbroker feed",
    time: "Today",
    tone: "neutral",
  },
];

// ── Trading calendar (structural demo month) ────────────────────────────────
export interface TradingDay {
  id: string;
  day: number; // day of month
  status: "profit" | "loss" | "none";
  pl?: number;
  instruments?: string[];
  trades?: number;
  lots?: string;
}

// August 2026 — Monday first column. Placeholder week layout only.
export const calendarMonth = {
  label: "August 2026",
  year: 2026,
  month: 7, // 0-indexed Aug
  weekdayHeaders: ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
  leadingBlanks: 5, // Aug 1 2026 falls on a Saturday in a Monday-first grid
  days: [
    { id: "d4", day: 3, status: "profit", pl: 420, instruments: ["XAUUSD", "US30"], trades: 2, lots: "0.20 / 0.10" },
    { id: "d5", day: 4, status: "loss", pl: -120, instruments: ["XAUUSD"], trades: 1, lots: "0.15" },
    { id: "d6", day: 5, status: "profit", pl: 335, instruments: ["XAUUSD"], trades: 1, lots: "0.20" },
    { id: "d7", day: 6, status: "profit", pl: 96, instruments: ["US30"], trades: 1, lots: "0.10" },
    { id: "d8", day: 7, status: "none" },
    { id: "d9", day: 9, status: "profit", pl: 268, instruments: ["XAUUSD"], trades: 1, lots: "0.20" },
    { id: "d10", day: 10, status: "loss", pl: -85, instruments: ["US30"], trades: 1, lots: "0.15" },
    { id: "d14", day: 14, status: "profit", pl: 380, instruments: ["XAUUSD", "US30"], trades: 3, lots: "0.20 / 0.10 / 0.10" },
    { id: "d15", day: 15, status: "none" },
    { id: "d20", day: 20, status: "profit", pl: 245, instruments: ["XAUUSD"], trades: 2, lots: "0.20 / 0.10" },
  ] as TradingDay[],
};

// ── Journal ─────────────────────────────────────────────────────────────────
export interface JournalEntry {
  id: string;
  symbol: string;
  direction: "BUY" | "SELL";
  setup: string;
  entry: string;
  target: string;
  stop: string;
  result: ResultTone;
  pl: number;
  lessons: string;
  date: string;
}

export const journalEntries: JournalEntry[] = [
  {
    id: "j1",
    symbol: "XAUUSD",
    direction: "BUY",
    setup: "Pullback to 50-period EMA on the 4H with bullish divergence.",
    entry: "2384.5",
    target: "2402.0",
    stop: "2378.0",
    result: "win",
    pl: 420,
    lessons: "Entry at the zone was clean; scale risk to 20% until target logic confirms.",
    date: "17 Aug",
  },
  {
    id: "j2",
    symbol: "US30",
    direction: "SELL",
    setup: "Break of session low with momentum continuation on lower timeframe.",
    entry: "41062",
    target: "40920",
    stop: "41140",
    result: "win",
    pl: 185,
    lessons: "Partial at 50% preserved gains when reversal candles printed late.",
    date: "17 Aug",
  },
  {
    id: "j3",
    symbol: "XAUUSD",
    direction: "BUY",
    setup: "Range-break retest after Asia range compression.",
    entry: "2371.8",
    target: "2388.0",
    stop: "2364.0",
    result: "loss",
    pl: -120,
    lessons: "Stop too tight for the session volatility — widen to ATR next time.",
    date: "16 Aug",
  },
];

export const journalObservation =
  "Consistent execution on XAUUSD setup at the EMA pullback. Losses cluster around stops placed inside the session range — widen invalidation to the swing low.";

// ── Reports ─────────────────────────────────────────────────────────────────
export interface WeeklyReport {
  week: string;
  profit: number;
  loss: number;
  winRate: number;
  trades: number;
  avgWin: number;
  avgLoss: number;
}

export const weeklyReports: WeeklyReport[] = [
  { week: "W/C 11 Aug", profit: 1890, loss: 410, winRate: 71, trades: 14, avgWin: 188, avgLoss: -137 },
  { week: "W/C 4 Aug", profit: 1460, loss: 520, winRate: 63, trades: 11, avgWin: 209, avgLoss: -104 },
  { week: "W/C 28 Jul", profit: 1720, loss: 300, winRate: 75, trades: 12, avgWin: 191, avgLoss: -100 },
];

export interface MonthlyReport {
  month: string;
  totalProfit: number;
  netProfit: number;
  profitFactor: number;
  winRate: number;
  drawdown: number; // %
  trades: number;
}

export const monthlyReports: MonthlyReport[] = [
  { month: "June", totalProfit: 3820, netProfit: 200, profitFactor: 1.22, winRate: 58, drawdown: 11.4, trades: 96 },
  { month: "July", totalProfit: 5230, netProfit: 1570, profitFactor: 2.11, winRate: 66, drawdown: 6.8, trades: 118 },
  { month: "August", totalProfit: 4740, netProfit: 1940, profitFactor: 2.44, winRate: 69, drawdown: 4.1, trades: 76 },
];

export const reportAnalytics: { id: string; label: string; description: string }[] = [
  { id: "a1", label: "Equity growth", description: "Cumulative equity progression" },
  { id: "a2", label: "Profit distribution", description: "Wins vs losses vs breakeven" },
  { id: "a3", label: "Instrument performance", description: "P/L split by instrument" },
  { id: "a4", label: "Win/loss ratio", description: "Relative strike efficiency" },
  { id: "a5", label: "Monthly performance", description: "Net result by month" },
  { id: "a6", label: "Trading frequency", description: "Trade velocity by symbol" },
];