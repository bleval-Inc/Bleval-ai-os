// Shared types + palette for the HOUSE OF VALTA trading workstation.
// House of Valta is managed by Valta Prime — analysis, monitoring, preparation,
// coaching, and challenge only. It cannot execute, modify, or close trades.

export type BaseIcon =
  | "dashboard"
  | "calendar"
  | "journal"
  | "reports";

export type TradingViewId =
  | "dashboard"
  | "calendar"
  | "journal"
  | "reports";

// Result tone for trades / days / instruments.
export type ResultTone = "win" | "loss" | "breakeven" | "none";

// ── Brand palette ────────────────────────────────────────────────────────────
// Stays inside the AXIOM design language: electric blue → indigo → violet.
// Gold is used sparingly as the metal-identity accent (XAUUSD).
// Profit/loss reuse the AXIOM semantic greens/reds.

export const VALTA_GRADIENT = "linear-gradient(135deg, #6d7cff 0%, #a88cff 100%)";
export const VALTA_ACCENT = "#6d7cff";
export const VALTA_VIOLET = "#a88cff";
export const VALTA_CYAN = "#4da3ff";
export const VALTA_GOLD = "#e8c66a";
export const VALTA_GOLD_DEEP = "#c79a3a";
export const VALTA_SUCCESS = "#22d377";
export const VALTA_LOSS = "#ff4d6a";
export const VALTA_NEUTRAL = "#4a4d55";

export type MetricKpi = {
  key: string;
  label: string;
  value: string;
  delta?: string;
  trend?: "up" | "down" | "flat";
  series?: number[];
};

export type StatusTone = "healthy" | "active" | "warning" | "danger" | "neutral";