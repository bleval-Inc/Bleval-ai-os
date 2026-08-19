// Shared types + palette for the PERSONAL workstation.
// Personal is the Founder's private operating environment, coordinated by
// Yamako as its executive intelligence layer.

export type BaseIcon =
  | "dashboard"
  | "yamako"
  | "schedule"
  | "learning"
  | "rnd"
  | "progress";

export type PersonalViewId =
  | "dashboard"
  | "yamako"
  | "schedule"
  | "learning"
  | "rnd"
  | "progress";

export type ResultTone = "win" | "loss" | "breakeven" | "none";

// ── Brand palette ────────────────────────────────────────────────────────────
// Calm, warm-but-consistent AXIOM language. Yamako's identity is a subtle teal;
// the rest stays in the restrained blue/violet family.

export const PERSONAL_GRADIENT = "linear-gradient(135deg, #6d7cff 0%, #a88cff 100%)";
export const PERSONAL_ACCENT = "#6d7cff";
export const PERSONAL_VIOLET = "#a88cff";
export const PERSONAL_TEAL = "#2dd4bf";   // Yamako identity — used sparingly
export const PERSONAL_CYAN = "#4da3ff";
export const PERSONAL_GOLD = "#e8c66a";
export const PERSONAL_SUCCESS = "#22d377";
export const PERSONAL_WARNING = "#ffb830";
export const PERSONAL_ERROR = "#ff4d6a";
export const PERSONAL_NEUTRAL = "#4a4d55";

export type MetricKpi = {
  key: string;
  label: string;
  value: string;
  delta?: string;
  trend?: "up" | "down" | "flat";
  series?: number[];
};

export type StatusTone = "healthy" | "active" | "warning" | "danger" | "neutral";