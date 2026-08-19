// SETTINGS workstation — demo / placeholder data.
// Values are clearly isolated placeholders. No real credentials or secrets are
// shown anywhere. The data layer is kept separate from presentation so each
// section view can later be connected to the real AXIOM backend independently.

import type { BaseIcon, SettingsSectionId, StatusTone } from "./types";

// ── Section navigation ───────────────────────────────────────────────────────
export interface SettingsSectionMeta {
  id: SettingsSectionId;
  label: string;
  shortLabel: string;
  description: string;
  icon: BaseIcon;
}

export const SETTINGS_SECTIONS: SettingsSectionMeta[] = [
  { id: "system", label: "System", shortLabel: "System", description: "OS configuration · runtime · health", icon: "system" },
  { id: "ai", label: "AI & Models", shortLabel: "AI & Models", description: "Active models · provider · parameters", icon: "ai" },
  { id: "executives", label: "Executives", shortLabel: "Executives", description: "Jenson · Valta Prime · Yamako", icon: "executives" },
  { id: "founder", label: "Founder", shortLabel: "Founder", description: "Authority · approvals · boundaries", icon: "founder" },
  { id: "voice", label: "Voice", shortLabel: "Voice", description: "Microphone · engines · wake words", icon: "voice" },
  { id: "notifications", label: "Notifications", shortLabel: "Notify", description: "Alerts · requests · escalation", icon: "notifications" },
  { id: "integrations", label: "Integrations", shortLabel: "Integrate", description: "Email · calendars · services", icon: "integrations" },
  { id: "security", label: "Security", shortLabel: "Security", description: "Auth · sessions · audit", icon: "security" },
  { id: "appearance", label: "Appearance", shortLabel: "Appearance", description: "Theme · density · motion", icon: "appearance" },
];

// ── System ───────────────────────────────────────────────────────────────────
export const systemStatus: { label: string; value: string }[] = [
  { label: "Status", value: "Operational" },
  { label: "Uptime", value: "6d 14h 09m" },
  { label: "Build", value: "AXIOM 2.1.0" },
  { label: "Region", value: "eu-central-1" },
];

export const systemHealth: { label: string; value: number }[] = [
  { label: "CPU", value: 34 },
  { label: "Memory", value: 52 },
  { label: "Storage", value: 41 },
  { label: "Network", value: 18 },
];

export const systemStacks: { title: string; items: string[] }[] = [
  { title: "Engines", items: ["Reasoning", "Memory (hybrid)", "Neural", "HNSW"] },
  { title: "Workflows", items: ["Research", "Coordination pipeline", "Swarm routing"] },
  { title: "Agents", items: ["Jenson", "Valta Prime", "Yamako"] },
  { title: "Services", items: ["Indexer", "Scheduler", "Gatekeeper", "Notifier"] },
];

// ── AI & Models ──────────────────────────────────────────────────────────────
export const aiActiveModel = {
  name: "claude-fable-5",
  label: "AXIOM active model",
  desc: "General reasoning across all workstations",
};

export const executiveModels: FieldRow[] = [
  { id: "m1", label: "Jenson", value: "claude-opus-4-8", desc: "BLEVAL ops" },
  { id: "m2", label: "Valta Prime", value: "claude-opus-4-8", desc: "Trading Eval", tone: "active" },
  { id: "m3", label: "Yamako", value: "claude-sonnet-5", desc: "Executive intelligence", tone: "active" },
];

export const modelParameters: FieldRow[] = [
  { id: "p1", label: "Temperature", value: "0.2", desc: "Low — precise" },
  { id: "p2", label: "Max tokens", value: "16,384" },
  { id: "p3", label: "Top-P", value: "0.9" },
  { id: "p4", label: "Reasoning effort", value: "Auto" },
];

export interface FieldRow {
  id: string;
  label: string;
  value: string;
  desc?: string;
  tone?: StatusTone;
}

export const aiApiConfig: FieldRow[] = [
  { id: "a1", label: "Provider", value: "Anthropic" },
  { id: "a2", label: "API endpoint", value: "api.anthropic.com/v1" },
  { id: "a3", label: "Organization", value: "Bleval INC" },
  { id: "a4", label: "API key", value: "sk-••••••••••••4242", desc: "Masked — never displayed", tone: "warning" },
];

// ── Executives ───────────────────────────────────────────────────────────────
export interface ExecutiveConfig {
  id: string;
  name: string;
  role: string;
  emojiGlyph: "jenson" | "valta" | "yamako";
  gradient: string;
  accent: string;
  status: "active" | "idle" | "standby";
  comms: string;
  personality: string;
  behaviour: string;
  permissions: string[];
}

export const executives: ExecutiveConfig[] = [
  {
    id: "exec1", name: "Jenson", role: "BLEVAL operations", emojiGlyph: "jenson",
    gradient: "linear-gradient(135deg,#3b82f6,#6d7cff)", accent: "#3b82f6",
    status: "active", comms: "Text · async",
    personality: "Structured · systematic",
    behaviour: "Sequential, detail-oriented, verifies before acting",
    permissions: ["Read analytics", "Prepare proposals", "Coordinate workflows"],
  },
  {
    id: "exec2", name: "Valta Prime", role: "Trading executive", emojiGlyph: "valta",
    gradient: "linear-gradient(135deg,#6d7cff,#a88cff)", accent: "#6d7cff",
    status: "active", comms: "Text · voice · alerts",
    personality: "Analytical · assertive",
    behaviour: "Monitors, challenges, prepares — never executes or closes trades",
    permissions: ["Analyse", "Notify", "Coach", "Prepare", "Challenge"],
  },
  {
    id: "exec3", name: "Yamako", role: "Executive intelligence", emojiGlyph: "yamako",
    gradient: "linear-gradient(135deg,#2dd4bf,#4da3ff)", accent: "#2dd4bf",
    status: "active", comms: "Text · voice",
    personality: "Perceptive · proactive",
    behaviour: "Coordinates schedule, learning, research and progress",
    permissions: ["Schedule", "Research", "Coach", "Summarise"],
  },
];

// ── Founder / Authority ──────────────────────────────────────────────────────
export type AuthorityLevel = "full" | "approve" | "restricted" | "locked";

export interface AuthorityRule {
  id: string;
  label: string;
  desc: string;
  level: AuthorityLevel;
}

export const authorityLevelMeta: Record<AuthorityLevel, { label: string; tone: StatusTone }> = {
  full: { label: "Full authority", tone: "active" },
  approve: { label: "Requires approval", tone: "warning" },
  restricted: { label: "Restricted", tone: "danger" },
  locked: { label: "Locked", tone: "neutral" },
};

export const authorityRules: AuthorityRule[] = [
  { id: "au1", label: "Approval rules", desc: "High-value actions require explicit founder approval", level: "approve" },
  { id: "au2", label: "Spending authority", desc: "Payments and external purchases", level: "approve" },
  { id: "au3", label: "External communication", desc: "Messages sent outside the AXIOM environment", level: "approve" },
  { id: "au4", label: "Trading authority", desc: "No executive may execute, modify or close a trade", level: "locked" },
  { id: "au5", label: "Irreversible actions", desc: "Deletes, overwrites, permanent config changes", level: "restricted" },
  { id: "au6", label: "Emergency escalation", desc: "Direct route to the founder on critical conditions", level: "full" },
];

// ── Voice ────────────────────────────────────────────────────────────────────
export const voiceConfig: FieldRow[] = [
  { id: "v1", label: "Microphone", value: "Built-in (MacBook Pro)", tone: "active" },
  { id: "v2", label: "Voice engine", value: "Neural · Premium" },
  { id: "v3", label: "Wake words", value: "\"AXIOM\", \"Valta\", \"Yamako\"" },
  { id: "v4", label: "System voice", value: "Atlas · calm" },
];

export const executiveVoices: FieldRow[] = [
  { id: "ev1", label: "Jenson", value: "Vector · neutral" },
  { id: "ev2", label: "Valta Prime", value: "Orion · confident" },
  { id: "ev3", label: "Yamako", value: "Nova · warm" },
];

export const voiceArbitration = "Primary = first executive to respond · conflicts escalate to Founder";

// ── Notifications ────────────────────────────────────────────────────────────
export interface NotifToggle {
  id: string;
  label: string;
  desc: string;
  on: boolean;
  channel: "push" | "email" | "sms" | "voice";
}

export const notificationToggles: NotifToggle[] = [
  { id: "n1", label: "Critical alerts", desc: "Irreversible-action or emergency warnings", on: true, channel: "voice" },
  { id: "n2", label: "Approval requests", desc: "Founder authority requests", on: true, channel: "push" },
  { id: "n3", label: "Executive requests", desc: "Jenson · Valta Prime · Yamako", on: true, channel: "push" },
  { id: "n4", label: "System alerts", desc: "Runtime and health warnings", on: true, channel: "push" },
  { id: "n5", label: "Emergency notifications", desc: "Mobile + SMS escalation path", on: true, channel: "sms" },
];

// ── Integrations ─────────────────────────────────────────────────────────────
export interface Integration {
  id: string;
  name: string;
  provider: string;
  channel: string;
  status: "connected" | "notConnected" | "setup";
}

export const integrations: Integration[] = [
  { id: "i1", name: "Email", provider: "Gmail", channel: "mail", status: "connected" },
  { id: "i2", name: "SMS", provider: "Twilio", channel: "sms", status: "connected" },
  { id: "i3", name: "Calendar", provider: "Google Calendar", channel: "calendar", status: "connected" },
  { id: "i4", name: "Social platforms", provider: "—", channel: "social", status: "notConnected" },
  { id: "i5", name: "Development tools", provider: "GitHub", channel: "git", status: "setup" },
  { id: "i6", name: "Trading & data services", provider: "Market data", channel: "data", status: "setup" },
];

// ── Security ─────────────────────────────────────────────────────────────────
export const securityRows: FieldRow[] = [
  { id: "s1", label: "Authentication", value: "Passkey + biometric", tone: "active" },
  { id: "s2", label: "Sessions", value: "2 active · auto-expire 12h" },
  { id: "s3", label: "Permissions", value: "Role-based · least privilege" },
  { id: "s4", label: "API credentials", value: "•••• 4242 · rotated 12h ago", tone: "warning" },
  { id: "s5", label: "Audit log", value: "Enabled · 90-day retention", tone: "active" },
];