// ── Founder Detector ──────────────────────────────────────────────────
// Detects the Founder's availability across multiple signals:
//   - Schedule (from Yamako's ScheduleCoordinator)
//   - Workstation activity (keyboard/mouse)
//   - Voice state (currently in a voice session)
//   - Working hours (05:00–21:00 from IDEAL_DAILY_SCHEDULE)
//   - Manual override (DND toggle in StatusBar)
//
// Exports a Zustand-compatible hook that updates on polling + events.

import { useEffect, useRef } from "react";
import { useAxiomStore } from "../store/axiom-store";
import { executives as execApi } from "../api";
import type { FounderAvailability } from "../api-types";

// ── Working Hours ──────────────────────────────────────────────────────

const WORKING_HOURS_START = 5;  // 05:00
const WORKING_HOURS_END = 21;   // 21:00

// ── Schedule-based resolution ──────────────────────────────────────────

interface ScheduleBlock {
  category?: string;
  name?: string;
  start_time?: string;
  end_time?: string;
}

/** Resolve availability from a schedule block's category. */
function availabilityFromSchedule(block: ScheduleBlock | null): FounderAvailability {
  if (!block) return "available";

  const category = (block.category || "").toLowerCase();
  const name = (block.name || "").toLowerCase();

  if (category === "sleep" || name.includes("sleep") || name.includes("wind-down")) {
    return "sleeping";
  }
  if (category === "trading" || name.includes("trade") || name.includes("market")) {
    return "in_trade";
  }
  if (category === "meeting" || name.includes("meeting") || name.includes("call")) {
    return "in_meeting";
  }
  if (category === "training" || name.includes("training") || name.includes("exercise")) {
    return "training";
  }
  if (category === "learning" || name.includes("learning") || name.includes("study")) {
    return "studying";
  }

  return "available";
}

// ── Activity tracking ─────────────────────────────────────────────────

let _lastActivityTime = Date.now();

/** Register user activity (called from event listeners). */
export function registerActivity(): void {
  _lastActivityTime = Date.now();
  useAxiomStore.getState().setFounderLastActive(_lastActivityTime);
}

/** Install global activity listeners. Call once during app init. */
export function installActivityTracking(): () => void {
  const handler = () => registerActivity();
  window.addEventListener("mousedown", handler);
  window.addEventListener("keydown", handler);
  window.addEventListener("touchstart", handler);
  window.addEventListener("mousemove", handler, { passive: true });

  return () => {
    window.removeEventListener("mousedown", handler);
    window.removeEventListener("keydown", handler);
    window.removeEventListener("touchstart", handler);
    window.removeEventListener("mousemove", handler);
  };
}

// ── Detection Logic ───────────────────────────────────────────────────

const INACTIVITY_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

async function detectAvailability(): Promise<FounderAvailability> {
  const store = useAxiomStore.getState();

  // 1. Manual override takes highest precedence
  if (store.founderManualOverride) {
    return store.founderManualOverride as FounderAvailability;
  }

  // 2. Working hours check
  const hour = new Date().getHours();
  const isWorkingHours = hour >= WORKING_HOURS_START && hour < WORKING_HOURS_END;
  if (!isWorkingHours) {
    return "sleeping";
  }

  // 3. Activity check
  const timeSinceActivity = Date.now() - _lastActivityTime;
  if (timeSinceActivity > INACTIVITY_TIMEOUT_MS) {
    // If inactive > 5 min, still available but may be away
  }

  // 4. Schedule check (from Yamako)
  try {
    const scheduleRes = await execApi.schedules("yamako");
    const schedule = scheduleRes as unknown as { today_blocks?: ScheduleBlock[] };
    if (schedule?.today_blocks) {
      const nowMinutes = new Date().getHours() * 60 + new Date().getMinutes();
      const currentBlock = schedule.today_blocks.find((block) => {
        const [sh, sm] = (block.start_time || "00:00").split(":").map(Number);
        const [eh, em] = (block.end_time || "00:00").split(":").map(Number);
        const start = sh * 60 + sm;
        const end = eh * 60 + em;
        return nowMinutes >= start && nowMinutes < end;
      });
      if (currentBlock) {
        return availabilityFromSchedule(currentBlock);
      }
    }
  } catch {
    // Schedule unavailable — fall through
  }

  // 5. Voice state
  if (store.isListening || store.isAwake) {
    return "available";
  }

  return "available";
}

// ── Hook ───────────────────────────────────────────────────────────────

/** Zustand-compatible hook that polls founder availability every 30s. */
export function useFounderState() {
  const setFounderAvailability = useAxiomStore((s) => s.setFounderAvailability);
  const pollingRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  useEffect(() => {
    const poll = async () => {
      const availability = await detectAvailability();
      setFounderAvailability(availability);
    };

    poll(); // Immediate first check
    pollingRef.current = setInterval(poll, 30000);
    return () => clearInterval(pollingRef.current);
  }, [setFounderAvailability]);
}

// ── One-shot check ─────────────────────────────────────────────────────

export async function checkFounderAvailability(): Promise<FounderAvailability> {
  return detectAvailability();
}