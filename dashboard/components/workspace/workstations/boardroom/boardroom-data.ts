// ── Boardroom data model & persistence ───────────────────────────────
// Identity of the three executives who attend Boardroom meetings, plus the
// meeting/note/action structures used by the workstation.
//
// PERSISTENCE DESIGN:
// Meeting records are persisted to localStorage so a completed meeting survives
// a reload (real client persistence — not fabricated data). The Boardroom
// backend (backend/axiom/runtime/board_room.py + approval.py) is not reachable
// from the Next client (no /api proxy), so the save site is isolated in
// `persistMeeting`/`loadMeetings` — swap those two functions for the real API
// (boardApi) when a proxy exists. No other system is duplicated here.

import type { SpeakerId } from "@/lib/api-types";

// ── Voice states surface in the UI ────────────────────────────────────
export type BrVoiceState = "IDLE" | "LISTENING" | "THINKING" | "SPEAKING" | "CONNECTING";

export const VOICE_STATES: readonly BrVoiceState[] = [
  "IDLE",
  "LISTENING",
  "THINKING",
  "SPEAKING",
  "CONNECTING",
];

// ── AXIOM is the host/orchestrator of any Boardroom session ───────────
export const AXIOM_HOST: BrExecutive = {
  id: "axiom",
  name: "AXIOM",
  role: "Host · Orchestration",
  org: "AXIOM OS",
  initials: "AX",
  text: "text-sky-300",
  ring: "ring-sky-300",
  dot: "bg-sky-300",
  briefings: [],
};

// ── Executive identity (static, real — names/roles/orgs from the spec) ─
export interface BrExecutive {
  id: SpeakerId;
  name: string;
  role: string;
  org: string;
  initials: string;
  /** Tailwind utilities — accent colour for avatars/indicators */
  text: string;
  ring: string;
  dot: string;
  /** Briefing lines an executive can speak on demand (real TTS). */
  briefings: string[];
}

export const EXECUTIVES: BrExecutive[] = [
  {
    id: "jenson",
    name: "Jenson",
    role: "COO",
    org: "BLEVAL INC",
    initials: "JE",
    text: "text-[var(--axiom-accent)]",
    ring: "ring-[var(--axiom-accent)]",
    dot: "bg-[var(--axiom-accent)]",
    briefings: [
      "Operations are tracking clean. Content, client and acquisition workstreams are all within their targets for the cycle.",
      "The near-term priority is the acquisition campaign. I have a draft approach ready to walk through when you want it.",
    ],
  },
  {
    id: "valta_prime",
    name: "Valta Prime",
    role: "Trading Executive",
    org: "HOUSE OF VALTA",
    initials: "VP",
    text: "text-amber-300",
    ring: "ring-amber-300",
    dot: "bg-amber-300",
    briefings: [
      "Markets are behaving within my risk model. Nothing is being forced while we wait for cleaner setups.",
      "My view on capital deployment is to stay patient — the best trades come when risk is priced fairly.",
    ],
  },
  {
    id: "yamako",
    name: "Yamako",
    role: "Personal Operations Executive",
    org: "PERSONAL",
    initials: "YA",
    text: "text-[var(--axiom-violet)]",
    ring: "ring-[var(--axiom-violet)]",
    dot: "bg-[var(--axiom-violet)]",
    briefings: [
      "Personal operations are in balance. Schedule, learning and progress workstreams are running as planned.",
      "I can prep the next learning block or audit the week ahead — just say which you want first.",
    ],
  },
];

export function getExecutive(id: SpeakerId): BrExecutive {
  if (id === "axiom") return AXIOM_HOST;
  return EXECUTIVES.find((e) => e.id === id) ?? AXIOM_HOST;
}

// ── Boardroom deadline presets ────────────────────────────────────────
export const DEADLINES = ["Today", "Friday", "Next week", "End of month"] as const;

// ── Action items (structured decisions → execution) ──────────────────
export type BrActionStatus = "PENDING" | "IN PROGRESS" | "COMPLETE";
export type BrApprovalStatus = "none" | "pending" | "approved" | "rejected" | "rework";

export interface BrActionItem {
  id: string;
  title: string;
  owner: SpeakerId;
  deadline: string;
  status: BrActionStatus;
  /** Founder approval is enforced when true — executives cannot bypass it. */
  requiresApproval: boolean;
  approvalStatus: BrApprovalStatus;
}

export interface BrDecision {
  id: string;
  title: string;
  proposedBy: SpeakerId;
  approved: boolean;
}

// ── Meeting session transcript (real turns triggered by the Found) ────
export interface BrTurn {
  id: string;
  speaker: SpeakerId;
  text: string;
  at: number;
}

export interface BrMeeting {
  id: string;
  title: string;
  startedAt: number;
  completedAt: number | null;
  participants: SpeakerId[];
  turns: BrTurn[];
  summary: string;
  keyPoints: string[];
  decisions: BrDecision[];
  actionItems: BrActionItem[];
  recommendations: string[];
  questions: string[];
  followUps: string[];
}

export function emptyMeeting(participants: SpeakerId[]): BrMeeting {
  return {
    id: `br-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`,
    title: "Boardroom Session",
    startedAt: Date.now(),
    completedAt: null,
    participants,
    turns: [],
    summary: "",
    keyPoints: [],
    decisions: [],
    actionItems: [],
    recommendations: [],
    questions: [],
    followUps: [],
  };
}

// ── Persistence (isolated integration point → swap for boardApi later) ─
const STORAGE_KEY = "axiom:boardroom:meetings";

export function loadMeetings(): BrMeeting[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as BrMeeting[]) : [];
  } catch {
    return [];
  }
}

export function persistMeeting(meeting: BrMeeting): void {
  if (typeof window === "undefined") return;
  const existing = loadMeetings();
  const idx = existing.findIndex((m) => m.id === meeting.id);
  const next = idx >= 0 ? existing.slice(0, idx).concat(meeting, existing.slice(idx + 1)) : [meeting, ...existing];
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    /* storage full/unavailable — session-only */
  }
}

// ── Formatting helpers ────────────────────────────────────────────────
export function formatDuration(from: number, to: number): string {
  const total = Math.max(0, to - from);
  const mins = Math.floor(total / 60000);
  const secs = Math.floor((total % 60000) / 1000);
  if (mins === 0) return `${secs}s`;
  return `${mins}m ${secs}s`;
}

export function formatClock(ts: number): string {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function formatDate(ts: number): string {
  return new Date(ts).toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
}

export function uid(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}