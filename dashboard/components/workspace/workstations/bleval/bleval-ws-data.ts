// BLEVAL INC workstation demo data — clearly isolated placeholder values.
// Replace with live workstation/API data later without redesigning the components.

import type { BaseIcon } from "./types";

export type BlevalViewId =
  | "dashboard"
  | "jenson"
  | "truth"
  | "acquisition"
  | "content"
  | "clients"
  | "operations";

export interface BlevalViewMeta {
  id: BlevalViewId;
  label: string;
  shortLabel: string;
  subtitle: string;
  icon: BaseIcon;
}

export const BLEVAL_VIEWS: BlevalViewMeta[] = [
  { id: "dashboard", label: "Dashboard", shortLabel: "Dash", subtitle: "Command center", icon: "dashboard" },
  { id: "jenson", label: "Jenson", shortLabel: "Jenson", subtitle: "COO AI workstation", icon: "jenson" },
  { id: "truth", label: "Truth Engine", shortLabel: "Truth", subtitle: "Research network", icon: "truth" },
  { id: "acquisition", label: "Acquisition", shortLabel: "Acq", subtitle: "Sales & pipeline", icon: "acquisition" },
  { id: "content", label: "Content", shortLabel: "Content", subtitle: "Creative engine", icon: "content" },
  { id: "clients", label: "Clients", shortLabel: "Clients", subtitle: "Account portfolio", icon: "clients" },
  { id: "operations", label: "Operations", shortLabel: "Ops", subtitle: "Running the company", icon: "operations" },
];

// ── Primary KPI cards ──────────────────────────────────────────────────────
export interface WSKpi {
  key: string;
  label: string;
  value: string;
  delta: string;
  trend: "up" | "down";
  series: number[];
}

export const wsKpis: WSKpi[] = [
  {
    key: "revenue",
    label: "Revenue",
    value: "R125,400",
    delta: "+18.4%",
    trend: "up",
    series: [62, 70, 66, 78, 88, 95, 112, 125],
  },
  {
    key: "profit",
    label: "Net Profit",
    value: "R82,300",
    delta: "+21.7%",
    trend: "up",
    series: [40, 44, 46, 52, 60, 66, 74, 82],
  },
  {
    key: "clients",
    label: "Clients",
    value: "14",
    delta: "+3",
    trend: "up",
    series: [8, 9, 9, 10, 11, 12, 13, 14],
  },
  {
    key: "pipeline",
    label: "Pipeline",
    value: "R246,000",
    delta: "+32.1%",
    trend: "up",
    series: [130, 148, 142, 168, 188, 204, 226, 246],
  },
];

// ── Revenue / Growth performance chart ─────────────────────────────────────
export interface PerformancePoint {
  label: string;
  revenue: number;
  profit: number;
}

// Values in Rand '000 — placeholder only.
export const performanceSeries: PerformancePoint[] = [
  { label: "Jan", revenue: 62, profit: 40 },
  { label: "Feb", revenue: 70, profit: 44 },
  { label: "Mar", revenue: 66, profit: 46 },
  { label: "Apr", revenue: 78, profit: 52 },
  { label: "May", revenue: 88, profit: 60 },
  { label: "Jun", revenue: 95, profit: 66 },
  { label: "Jul", revenue: 112, profit: 74 },
  { label: "Aug", revenue: 125, profit: 82 },
];

// ── Sales pipeline (funnel) ────────────────────────────────────────────────
export interface PipelineStage {
  id: string;
  label: string;
  value: number;
}

export const salesPipeline: PipelineStage[] = [
  { id: "prospects", label: "Prospects", value: 248 },
  { id: "contacted", label: "Contacted", value: 172 },
  { id: "engaged", label: "Engaged", value: 86 },
  { id: "qualified", label: "Qualified", value: 41 },
  { id: "booked", label: "Booked", value: 17 },
  { id: "closed", label: "Closed", value: 6 },
];

// ── Jenson daily briefing ──────────────────────────────────────────────────
export interface BriefingPriority {
  label: string;
  meta: string;
  kind: "prospects" | "calls" | "projects" | "approvals" | "content";
}

export const jensonBriefing = {
  salutation: "Good morning, Founder.",
  statusLine: "Company status is healthy.",
  priorities: [
    { label: "Qualified prospects require follow-up", meta: "23", kind: "prospects" },
    { label: "Sales calls scheduled", meta: "4", kind: "calls" },
    { label: "Client projects in production", meta: "3", kind: "projects" },
    { label: "Content assets awaiting your approval", meta: "8", kind: "approvals" },
  ] as BriefingPriority[],
  recommendation:
    "Open the day with the Solar campaign follow-ups — they carry the largest closed-won potential in the current pipeline (R64,000) and three prospects went dark after initial contact.",
};

// ── Jenson conversation (mock) ─────────────────────────────────────────────
export interface ChatMessage {
  id: string;
  role: "jenson" | "founder";
  text: string;
  time: string;
}

export const jensonInitialMessages: ChatMessage[] = [
  {
    id: "j1",
    role: "jenson",
    time: "07:30",
    text: "Good morning, Founder. Overnight the system processed 14 new leads; 3 moved into Qualified. Net profit is trending 21.7% ahead of last month.",
  },
  {
    id: "j2",
    role: "jenson",
    time: "07:31",
    text: "Your priorities for today: the Solar campaign follow-ups (R64,000 at risk), 4 scheduled sales calls, and 8 content assets needing your approval to ship.",
  },
  {
    id: "f1",
    role: "founder",
    time: "07:35",
    text: "Which three prospects are closest to booking?",
  },
  {
    id: "j3",
    role: "jenson",
    time: "07:35",
    text: "Asteris Group (R18,000 retainer), Fernwood Capital (R12,500 build), and Veridian Health (R9,800 commission) — all in final contract review. I've queued reminder drafts if you'd like me to nudge them.",
  },
];

// ── Company context (right panel, mock) ────────────────────────────────────
export interface ContextStat {
  label: string;
  value: string;
  delta?: string;
}

export interface ContextBlock {
  title: string;
  stats: ContextStat[];
}

export const jensonContext: ContextBlock[] = [
  {
    title: "Revenue",
    stats: [
      { label: "Month revenue", value: "R125,400", delta: "+18.4%" },
      { label: "Net profit", value: "R82,300", delta: "+21.7%" },
    ],
  },
  {
    title: "Clients",
    stats: [
      { label: "Active clients", value: "14", delta: "+3" },
      { label: "At-risk", value: "1" },
    ],
  },
  {
    title: "Pipeline",
    stats: [
      { label: "Open pipeline", value: "R246,000" },
      { label: "Qualified", value: "41" },
      { label: "Booked", value: "17" },
    ],
  },
  {
    title: "Active projects",
    stats: [
      { label: "In production", value: "3" },
      { label: "Shipping this week", value: "1" },
    ],
  },
  {
    title: "Current priorities",
    stats: [
      { label: "Solar campaign", value: "Follow-ups" },
      { label: "Content approvals", value: "8 pending" },
    ],
  },
];