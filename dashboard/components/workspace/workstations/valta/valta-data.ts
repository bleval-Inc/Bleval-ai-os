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

// CLEARED FOR LIVE DATA INTEGRATION - PHASE V-2
export const kpis: Kpi[] = [];

// ── Equity / profit growth series (primary chart) ───────────────────────────
export interface EquityPoint {
  label: string;
  equity: number; // account equity in USD
}

// CLEARED FOR LIVE DATA INTEGRATION - PHASE V-2
export const equitySeries: EquityPoint[] = [];

// ── Profit distribution (donut) ─────────────────────────────────────────────
export interface DistributionSlice {
  key: string;
  label: string;
  count: number;
  value: number; // aggregate P/L in USD
  tone: "win" | "loss" | "breakeven";
}

// CLEARED FOR LIVE DATA INTEGRATION - PHASE V-2
export const profitDistribution: DistributionSlice[] = [];

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

// CLEARED FOR LIVE DATA INTEGRATION - PHASE V-2
export const instrumentBreakdown: InstrumentBreakdown[] = [];

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

// CLEARED FOR LIVE DATA INTEGRATION - PHASE V-2
export const monthlySeries: MonthResult[] = [];

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

// CLEARED FOR LIVE DATA INTEGRATION - PHASE V-2
export const recentTrades: RecentTrade[] = [];

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

// CLEARED FOR LIVE DATA INTEGRATION - PHASE V-2
export const newsFeed: NewsItem[] = [];

export interface InstitutionalIntel {
  id: string;
  kind: string;
  detail: string;
  source: string;
  time: string;
  tone: "bullish" | "bearish" | "neutral";
}

// CLEARED FOR LIVE DATA INTEGRATION - PHASE V-2
export const institutionalIntel: InstitutionalIntel[] = [];

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

// CLEARED FOR LIVE DATA INTEGRATION - PHASE V-2
export const calendarMonth = {
  label: "",
  year: 0,
  month: 0,
  weekdayHeaders: ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
  leadingBlanks: 0,
  days: [] as TradingDay[],
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

// CLEARED FOR LIVE DATA INTEGRATION - PHASE V-2
export const journalEntries: JournalEntry[] = [];

export const journalObservation =
  "Awaiting live trading data for performance analysis.";

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

// CLEARED FOR LIVE DATA INTEGRATION - PHASE V-2
export const weeklyReports: WeeklyReport[] = [];

export interface MonthlyReport {
  month: string;
  totalProfit: number;
  netProfit: number;
  profitFactor: number;
  winRate: number;
  drawdown: number; // %
  trades: number;
}

// CLEARED FOR LIVE DATA INTEGRATION - PHASE V-2
export const monthlyReports: MonthlyReport[] = [];

export const reportAnalytics: { id: string; label: string; description: string }[] = [
  { id: "a1", label: "Equity growth", description: "Cumulative equity progression" },
  { id: "a2", label: "Profit distribution", description: "Wins vs losses vs breakeven" },
  { id: "a3", label: "Instrument performance", description: "P/L split by instrument" },
  { id: "a4", label: "Win/loss ratio", description: "Relative strike efficiency" },
  { id: "a5", label: "Monthly performance", description: "Net result by month" },
  { id: "a6", label: "Trading frequency", description: "Trade velocity by symbol" },
];