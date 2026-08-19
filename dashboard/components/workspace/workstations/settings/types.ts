// Shared types + palette for the AXIOM SETTINGS workstation.
// Settings is the central configuration surface for the AXIOM AI OS itself —
// distinct from per-workstation operational content.

export type BaseIcon =
  | "system"
  | "ai"
  | "executives"
  | "founder"
  | "voice"
  | "notifications"
  | "integrations"
  | "security"
  | "appearance";

export type SettingsSectionId =
  | "system"
  | "ai"
  | "executives"
  | "founder"
  | "voice"
  | "notifications"
  | "integrations"
  | "security"
  | "appearance";

// ── Brand palette ────────────────────────────────────────────────────────────
// Settings shares the restrained blue/violet AXIOM language. Status tones mirror
// the global system (green/blue/amber/red/neutral) so pills read consistently.

export const SETTING_ACCENT = "#6d7cff";
export const SETTING_VIOLET = "#a88cff";
export const SETTING_BLUE = "#4da3ff";
export const SETTING_SUCCESS = "#22d377";
export const SETTING_WARNING = "#ffb830";
export const SETTING_DANGER = "#ff4d6a";
export const SETTING_NEUTRAL = "#4a4d55";

export type StatusTone = "healthy" | "active" | "warning" | "danger" | "neutral";

/** A labelled pill value, e.g. a model name or permission level. */
export interface FieldValue {
  label: string;
  value: string;
  tone?: StatusTone;
}