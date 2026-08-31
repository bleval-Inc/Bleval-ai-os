// Emergency Escalator
// Graduated urgency system for executive alerts:
//
//   Valta Prime POI alerts    → HIGH → CRITICAL (escalates after 60s)
//   Yamako routine reminders  → NORMAL (queued behind current speaker)
//   System emergencies        → CRITICAL (immediate interrupt)
//   Clear on acknowledge      → Founder says "acknowledged" or clicks
//
// Integrates with the SpeechArbiter for voice preemption and the
// Zustand store for UI state (red banner, emergency indicators).

import { useAxiomStore } from "../store/axiom-store";
import { requestSpeak, type SpeechUrgency } from "./speech-arbiter";
import type { SpeakerId } from "../api-types";
import { system } from "@/lib/api";  // Fixed import path

// Types

export interface EscalationEvent {
  id: string;
  source: "valta_prime" | "yamako" | "system";
  level: "normal" | "high" | "critical";
  subject: string;
  message: string;
  speaker: SpeakerId;
  raisedAt: number;
  acknowledged: boolean;
}

// State

let _activeEscalations: EscalationEvent[] = [];
let _poiTimers: Map<string, ReturnType<typeof setTimeout>> = new Map();
let _systemPolling: ReturnType<typeof setInterval> | null = null;

// Callbacks

type EscalationCallback = (event: EscalationEvent) => void;
let _onEscalation: EscalationCallback | null = null;
let _onEscalationCleared: ((eventId: string) => void) | null = null;

export function setEscalationCallbacks(callbacks: {
  onEscalation?: EscalationCallback;
  onEscalationCleared?: (eventId: string) => void;
}) {
  if (callbacks.onEscalation) _onEscalation = callbacks.onEscalation;
  if (callbacks.onEscalationCleared) _onEscalationCleared = callbacks.onEscalationCleared;
}

// Raising Escalations

/** Raise a POI alert from Valta Prime. Starts at HIGH, escalates to CRITICAL after 60s. */
export function raisePoiAlert(subject: string, message: string): string {
  const id = `poi-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;

  const event: EscalationEvent = {
    id,
    source: "valta_prime",
    level: "high",
    subject,
    message,
    speaker: "valta_prime",
    raisedAt: Date.now(),
    acknowledged: false,
  };

  _activeEscalations.push(event);
  updateStoreEmergency(event);
  _onEscalation?.(event);

  // Speak as HIGH urgency
  requestSpeak("valta_prime", `Point of Interest: ${message}`, "high");

  // Schedule escalation to CRITICAL after 60s
  const timer = setTimeout(() => {
    escalateToCritical(id);
  }, 60000);
  _poiTimers.set(id, timer);

  return id;
}

/** Raise a system emergency (immediate CRITICAL). */
export function raiseSystemEmergency(subject: string, message: string): string {
  const id = `sys-em-${Date.now()}`;

  const event: EscalationEvent = {
    id,
    source: "system",
    level: "critical",
    subject,
    message,
    speaker: "axiom",
    raisedAt: Date.now(),
    acknowledged: false,
  };

  _activeEscalations.push(event);
  updateStoreEmergency(event);
  _onEscalation?.(event);

  // Interrupt immediately with CRITICAL
  requestSpeak("axiom", `System emergency: ${message}`, "critical");

  return id;
}

/** Queue a routine reminder from Yamako (NORMAL urgency). */
export function raiseRoutineReminder(subject: string, message: string): string {
  const id = `rem-${Date.now()}`;

  const event: EscalationEvent = {
    id,
    source: "yamako",
    level: "normal",
    subject,
    message,
    speaker: "yamako",
    raisedAt: Date.now(),
    acknowledged: false,
  };

  _activeEscalations.push(event);
  _onEscalation?.(event);

  // Queue as normal priority speech
  requestSpeak("yamako", message, "normal");

  return id;
}

// Acknowledging

/** Acknowledge an escalation event. Clears the emergency state. */
export function acknowledgeEscalation(eventId: string): void {
  const idx = _activeEscalations.findIndex((e) => e.id === eventId);
  if (idx === -1) return;

  const event = _activeEscalations[idx];
  event.acknowledged = true;

  // Clear any POI timer
  const timer = _poiTimers.get(eventId);
  if (timer) {
    clearTimeout(timer);
    _poiTimers.delete(eventId);
  }

  _activeEscalations.splice(idx, 1);
  _onEscalationCleared?.(eventId);

  // Update store
  if (_activeEscalations.length === 0) {
    useAxiomStore.getState().clearEmergency();
  } else {
    updateStoreEmergency(_activeEscalations[_activeEscalations.length - 1]);
  }
}

/** Acknowledge all active escalations. */
export function acknowledgeAllEscalations(): void {
  for (const event of [..._activeEscalations]) {
    acknowledgeEscalation(event.id);
  }
}

/** Get all currently active escalations. */
export function getActiveEscalations(): EscalationEvent[] {
  return [..._activeEscalations];
}

/** Check if there's an active critical escalation. */
export function hasCriticalEscalation(): boolean {
  return _activeEscalations.some((e) => e.level === "critical");
}

// Polling (System Monitor)

/** Start polling for system health escalations (call once during app init). */
export function startSystemHealthPolling(intervalMs = 30000): () => void {
  if (_systemPolling) clearInterval(_systemPolling);

  _systemPolling = setInterval(async () => {
    try {
      const health = await system.health();
      if (health && health.overall === "unhealthy" && health.unhealthy > 0) {
        // Only raise if not already active for the same symptom
        const hasExistingSystemAlert = _activeEscalations.some(
          (e) => e.source === "system" && e.level === "critical",
        );
        if (!hasExistingSystemAlert) {
          raiseSystemEmergency(
            "System degradation detected",
            `${health.unhealthy} component${health.unhealthy > 1 ? "s" : ""} reporting unhealthy. Please check the system status panel.`,
          );
        }
      }
    } catch {
      // Backend unavailable — skip
    }
  }, intervalMs);

  return () => {
    if (_systemPolling) {
      clearInterval(_systemPolling);
      _systemPolling = null;
    }
  };
}

// Internal

function escalateToCritical(eventId: string): void {
  const event = _activeEscalations.find((e) => e.id === eventId);
  if (!event || event.acknowledged) return;

  event.level = "critical";
  updateStoreEmergency(event);
  _onEscalation?.(event);

  // Interrupt with CRITICAL
  const speaker = event.source === "system" ? "axiom" : "valta_prime";
  requestSpeak(
    speaker,
    `Unacknowledged alert: ${event.message}. Please respond.`,
    "critical",
  );
}

function updateStoreEmergency(event: EscalationEvent): void {
  const store = useAxiomStore.getState();
  store.setEmergencyActive(true);
  store.setEmergencySource(event.source);
  store.setEmergencyLevel(event.level);
}