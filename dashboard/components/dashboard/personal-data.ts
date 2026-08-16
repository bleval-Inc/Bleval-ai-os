// PERSONAL console demo data — isolated placeholder values for Yamako's
// personal operations. Replace these with real personal/live data later.
// No generated content; everything here is intentionally static sample data.

export interface ScheduleItem {
  id: string;
  time: string; // "HH:MM"
  label: string;
}

export interface Habit {
  id: string;
  label: string;
  done: boolean; // today's completion
  streak: number; // consecutive-day streak
  week: boolean[]; // Mon–Sun progress (7 entries)
}

export interface PersonalData {
  identity: string;
  location: string;
  temperature: number;
  condition: string;
  high: number;
  low: number;
  baseYear: number; // month shown on load (today's month)
  baseMonth: number; // 0-indexed
  baseDay: number; // today's day-of-month (highlighted on load)
  now: string; // wall-clock used for the schedule "now" indicator
  schedule: ScheduleItem[];
  habits: Habit[];
}

export const personalData: PersonalData = {
  identity: "PERSONAL",
  location: "Cape Town",
  temperature: 18,
  condition: "Partly Cloudy",
  high: 22,
  low: 14,
  baseYear: 2026,
  baseMonth: 7, // August
  baseDay: 16,
  now: "09:32",
  schedule: [
    { id: "s1", time: "05:00", label: "Morning routine" },
    { id: "s2", time: "06:00", label: "Training" },
    { id: "s3", time: "07:00", label: "Market analysis" },
    { id: "s4", time: "09:00", label: "Deep work" },
    { id: "s5", time: "12:00", label: "Lunch" },
    { id: "s6", time: "14:00", label: "Client / business" },
    { id: "s7", time: "18:00", label: "Learning" },
    { id: "s8", time: "22:00", label: "Wind down" },
  ],
  habits: [
    { id: "h1", label: "Wake at 05:00", done: true, streak: 21, week: [true, true, true, true, true, false, false] },
    { id: "h2", label: "Training", done: true, streak: 8, week: [true, false, true, true, true, false, false] },
    { id: "h3", label: "Trading preparation", done: true, streak: 14, week: [true, true, true, true, true, true, false] },
    { id: "h4", label: "Learning", done: false, streak: 6, week: [false, true, false, true, false, true, false] },
    { id: "h5", label: "Reading", done: true, streak: 12, week: [true, true, false, true, true, false, false] },
    { id: "h6", label: "Meditation", done: false, streak: 5, week: [true, false, true, false, true, false, false] },
    { id: "h7", label: "Sleep routine", done: false, streak: 9, week: [true, true, true, false, true, false, false] },
  ],
};