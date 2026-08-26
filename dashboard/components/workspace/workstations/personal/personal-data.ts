// PERSONAL workstation — demo data.
// All values are clearly isolated placeholder numbers. The data layer is kept
// separate from presentation so real schedules, learning records, research and
// habit databases can be connected later without rebuilding the components.

import type { BaseIcon } from "./types";

// ── Internal dock destinations ──────────────────────────────────────────────
export type PersonalViewId =
  | "dashboard"
  | "yamako"
  | "schedule"
  | "learning"
  | "rnd"
  | "progress";

export interface PersonalViewMeta {
  id: PersonalViewId;
  label: string;
  shortLabel: string;
  subtitle: string;
  icon: BaseIcon;
}

export const PERSONAL_VIEWS: PersonalViewMeta[] = [
  { id: "dashboard", label: "Personal Dashboard", shortLabel: "Today", subtitle: "Your day", icon: "dashboard" },
  { id: "yamako", label: "Yamako", shortLabel: "Yamako", subtitle: "Executive intelligence", icon: "yamako" },
  { id: "schedule", label: "Schedule", shortLabel: "Schedule", subtitle: "Calendar & routine", icon: "schedule" },
  { id: "learning", label: "Learning", shortLabel: "Learn", subtitle: "Knowledge & goals", icon: "learning" },
  { id: "rnd", label: "R&D", shortLabel: "R&D", subtitle: "Personal research", icon: "rnd" },
  { id: "progress", label: "Progress", shortLabel: "Progress", subtitle: "Habits & growth", icon: "progress" },
];

// ── Quick status (Today) ────────────────────────────────────────────────────
export interface QuickStat {
  key: string;
  label: string;
  value: number; // 0–100 completion
  display: string;
}

export const quickStatus: QuickStat[] = [
  { key: "schedule", label: "Schedule", value: 80, display: "80%" },
  { key: "habits", label: "Habits", value: 90, display: "90%" },
  { key: "learning", label: "Learning", value: 60, display: "60%" },
];

export const dailyBrief = {
  date: "Monday, 17 August 2026",
  greeting: "Good morning, founder.",
  prioritiesDone: 3,
  prioritiesTotal: 5,
  trainingComplete: true,
};

// ── Today's routine / schedule timeline ─────────────────────────────────────
export interface RoutineBlock {
  id: string;
  time: string;
  label: string;
  type: "wake" | "routine" | "trading" | "training" | "learning" | "work" | "review" | "sleep";
  status: "done" | "current" | "upcoming";
  note?: string;
}

export const todaysRoutine: RoutineBlock[] = [
  { id: "r0", time: "05:00", label: "Wake", type: "wake", status: "done" },
  { id: "r1", time: "05:15", label: "Morning routine", type: "routine", status: "done", note: "Cold shower · journal · goals" },
  { id: "r2", time: "06:00", label: "Trading block", type: "trading", status: "done", note: "House of Valta · XAUUSD session" },
  { id: "r3", time: "08:30", label: "Training", type: "training", status: "done", note: "Strength — upper body" },
  { id: "r4", time: "10:00", label: "Learning block", type: "learning", status: "current", note: "Deep work · OODA loop protocol" },
  { id: "r5", time: "12:30", label: "Work block", type: "work", status: "upcoming", note: "Bleval Inc · deep work" },
  { id: "r6", time: "18:00", label: "Review", type: "review", status: "upcoming", note: "Daily review · journal" },
  { id: "r7", time: "21:30", label: "Wind down", type: "sleep", status: "upcoming" },
];

export const routineTypeColor: Record<RoutineBlock["type"], string> = {
  wake: "#4da3ff",
  routine: "#8b8d93",
  trading: "#e8c66a",
  training: "#22d377",
  learning: "#a88cff",
  work: "#6d7cff",
  review: "#2dd4bf",
  sleep: "#4a4d55",
};

// ── Upcoming events ─────────────────────────────────────────────────────────
export interface UpcomingEvent {
  id: string;
  time: string;
  title: string;
  kind: "meeting" | "training" | "learning" | "personal" | "reminder" | "work" | "review";
  note?: string;
}

export const upcomingEvents: UpcomingEvent[] = [
  { id: "e1", time: "12:30", title: "Deep work — Bleval Ops", kind: "work", note: "2h focus block" },
  { id: "e2", time: "15:00", title: "Coaching call", kind: "meeting", note: "Performance review" },
  { id: "e3", time: "18:00", title: "Daily review", kind: "review", note: "Journal reflection" },
  { id: "e4", time: "21:30", title: "Read — Deep Work ch. 6", kind: "learning", note: "20 min" },
];

// ── Daily priorities ────────────────────────────────────────────────────────
export interface PriorityItem {
  id: string;
  label: string;
  done: boolean;
  kind: "work" | "personal" | "learning" | "trading";
}

export const dailyPriorities: PriorityItem[] = [
  { id: "p1", label: "Execute XAUUSD morning setup", done: true, kind: "trading" },
  { id: "p2", label: "Complete OODA learning module", done: true, kind: "learning" },
  { id: "p3", label: "Publish client report", done: true, kind: "work" },
  { id: "p4", label: "Review week's journal entries", done: false, kind: "personal" },
  { id: "p5", label: "Plan tomorrow's trading calendar", done: false, kind: "work" },
];

// ── Reminders ───────────────────────────────────────────────────────────────
export interface Reminder {
  id: string;
  text: string;
  day: string;
  kind: "personal" | "learning" | "health";
}

export const reminders: Reminder[] = [
  { id: "m1", text: "Optician appointment — Friday 10:00", day: "Fri", kind: "personal" },
  { id: "m2", text: "Finish Deep Work book notes", day: "This week", kind: "learning" },
  { id: "m3", text: "Hydration + movement break", day: "Hourly", kind: "health" },
];

// ── Yaho conversation (mock) ────────────────────────────────────────────────
export interface YamakoMessage {
  id: string;
  role: "yamako" | "founder";
  text: string;
  time: string;
}

export const yamakoInitialMessages: YamakoMessage[] = [
  {
    id: "y1",
    role: "yamako",
    time: "09:40",
    text: "Good morning. Your learning block is open — the OODA loop protocol module is 60% complete. There are two free 25-minute windows before your work block if you want to close it out.",
  },
  {
    id: "y2",
    role: "founder",
    time: "09:43",
    text: "Review tomorrow's schedule and tell me where I have gaps.",
  },
  {
    id: "y3",
    role: "yamako",
    time: "09:43",
    text: "Tomorrow has a 90-minute unmapped stretch between 14:00 and 15:30, and your evening review is squeezed to 20 minutes. I'd suggest inserting a 45-minute deep-work session at 14:00 and opening the review to 30. Want me to draft it?",
  },
];

export const yamakoSuggestions: string[] = [
  "Review my schedule tomorrow and find gaps",
  "Research the most effective deep-work methods",
  "How did my week track against my goals?",
  "Plan a focused learning path for trading psychology",
];

export const yamakoCapabilities: string[] = [
  "Schedule",
  "Research",
  "Learning",
  "Progress review",
  "Task planning",
  "Day planning",
  "Reflection",
  "Workflows",
];

// ── Schedule (day/week/month demo) ──────────────────────────────────────────
export interface CalendarEvent {
  id: string;
  day: number;
  start: string;
  durationMin: number;
  title: string;
  kind: "event" | "task" | "training" | "learning" | "meeting" | "reminder";
}

export const weekEvents: CalendarEvent[] = [
  { id: "c1", day: 17, start: "06:00", durationMin: 150, title: "Trading block · Valta", kind: "training" },
  { id: "c2", day: 17, start: "08:30", durationMin: 60, title: "Training — upper body", kind: "training" },
  { id: "c3", day: 17, start: "10:00", durationMin: 120, title: "Learning — OODA protocol", kind: "learning" },
  { id: "c4", day: 17, start: "12:30", durationMin: 120, title: "Deep work — Bleval Ops", kind: "event" },
  { id: "c5", day: 17, start: "15:00", durationMin: 45, title: "Coaching call", kind: "meeting" },
  { id: "c6", day: 18, start: "06:00", durationMin: 150, title: "Trading block · Valta", kind: "training" },
  { id: "c7", day: 18, start: "14:00", durationMin: 90, title: "Deep work — open slot", kind: "task" },
  { id: "c8", day: 20, start: "10:00", durationMin: 60, title: "Optician appointment", kind: "reminder" },
];

export const scheduleKindColor: Record<CalendarEvent["kind"], string> = {
  event: "#6d7cff",
  task: "#4da3ff",
  training: "#22d377",
  learning: "#a88cff",
  meeting: "#ffb830",
  reminder: "#8b8d93",
};

// ── Learning ────────────────────────────────────────────────────────────────
export interface LearningSubject {
  id: string;
  name: string;
  why: string;
  progress: number; // %
  branch: string;
  resource: string;
  next: string;
  weakAt: string;
}

export const learningSubjects: LearningSubject[] = [
  {
    id: "l1",
    name: "Trading psychology",
    why: "To remove emotional bias from execution.",
    progress: 62,
    branch: "Performance",
    resource: "The Mental Game of Trading",
    next: "Processing trade streaks without overconfidence",
    weakAt: "Riding winners after losses",
  },
  {
    id: "l2",
    name: "Deep work protocols",
    why: "To build sustained focused output.",
    progress: 48,
    branch: "Productivity",
    resource: "Deep Work — Newport",
    next: "Implementing the OODA loop for focus",
    weakAt: "Starting blocks without plan",
  },
  {
    id: "l3",
    name: "Learning science",
    why: "To make study time compound.",
    progress: 35,
    branch: "Self-development",
    resource: "Make It Stick",
    next: "Spaced repetition scheduling",
    weakAt: "Retrieval practice consistency",
  },
  {
    id: "l4",
    name: "Leadership & systems",
    why: "To scale decisions beyond myself.",
    progress: 27,
    branch: "Leadership",
    resource: "Traction — EOS",
    next: "Writing operating principles",
    weakAt: "Delegation",
  },
];

export interface LearningGoal {
  id: string;
  label: string;
  progress: number;
  due: string;
}

export const learningGoals: LearningGoal[] = [
  { id: "g1", label: "Finish Deep Work book & notes", progress: 70, due: "This week" },
  { id: "g2", label: "Complete trading psychology module", progress: 40, due: "2 weeks" },
  { id: "g3", label: "30 study sessions logged", progress: 66, due: "Ongoing" },
];

// ── R&D (media-first research) ──────────────────────────────────────────────
export const rndCategories = [
  "Productivity", "Personal development", "Learning", "Training", "Wellness",
  "Psychology", "Philosophy", "Leadership", "Business", "Technology", "Systems", "Habits",
];

export interface RndProject {
  id: string;
  title: string;
  category: string;
  question: string;
  summary: string;
  status: "active" | "complete" | "queued";
  updated: string;
}

export const rndProjects: RndProject[] = [
  { id: "rnd1", title: "Deep Work", category: "Productivity", question: "How do I build sustained deep focus?", status: "active", updated: "Today", summary: "Framing, protocols and evidence for producing focused output reliably." },
  { id: "rnd2", title: "Deliberate Practice", category: "Learning", question: "How do I learn trading skills fastest?", status: "active", updated: "Yesterday", summary: "Structured practice cycles with rapid corrective feedback." },
  { id: "rnd3", title: "Sleep & Performance", category: "Wellness", question: "How does sleep shape decision quality?", status: "queued", updated: "—", summary: "Sleep architecture and its effect on executive function." },
];

export interface RndBlock {
  id: string;
  kind: "text" | "video" | "diagram" | "chart" | "source" | "recommendation";
  title?: string;
  text?: string;
}

// ── Progress / habits ───────────────────────────────────────────────────────
export interface Habit {
  id: string;
  label: string;
  streak: number;
  consistency: number; // 0–100 %
  weekly: boolean[]; // Mon..Sun
}

export const habits: Habit[] = [
  { id: "h1", label: "Wake-up consistency", streak: 21, consistency: 92, weekly: [true, true, true, true, true, true, false] },
  { id: "h2", label: "Training", streak: 14, consistency: 88, weekly: [true, true, false, true, true, false, true] },
  { id: "h3", label: "Learning / study", streak: 31, consistency: 95, weekly: [true, true, true, true, true, true, true] },
  { id: "h4", label: "Reading", streak: 17, consistency: 81, weekly: [true, false, true, true, true, true, false] },
  { id: "h5", label: "Meditation", streak: 9, consistency: 74, weekly: [true, true, false, true, true, false, true] },
  { id: "h6", label: "Sleep — 8h", streak: 12, consistency: 86, weekly: [true, true, true, false, true, true, true] },
];

export interface TrendPoint {
  label: string;
  value: number;
}

export const weeklyTrend: TrendPoint[] = [
  { label: "Mon", value: 82 }, { label: "Tue", value: 90 }, { label: "Wed", value: 78 },
  { label: "Thu", value: 94 }, { label: "Fri", value: 86 }, { label: "Sat", value: 70 },
  { label: "Sun", value: 74 },
];

export const monthlyTrend: TrendPoint[] = [
  { label: "Mar", value: 66 }, { label: "Apr", value: 72 }, { label: "May", value: 78 },
  { label: "Jun", value: 81 }, { label: "Jul", value: 85 }, { label: "Aug", value: 90 },
];