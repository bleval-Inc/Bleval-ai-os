// Speech Arbiter
// Client-side speech coordination that mirrors the backend
// CommunicationCoordinator's rules — one speaker at a time, urgency-based
// queuing, emergency preemption.
//
// Priority (matches backend resolve_speaker_conflict):
//   Valta Prime (trading critical) > Jenson (business) > Yamako (personal)
//
// AXIOM is the default voice. Executives speak only when:
//   - Founder directly addresses them
//   - Escalation rules trigger (POI alerts, emergencies)
//   - Board Room meeting is in session

import type { SpeakerId } from "../api-types";
import { speak, stopSpeaking } from "./speak";
import { getVoiceProfile } from "./voices";
import { useAxiomStore } from "../store/axiom-store";

// Types

export type SpeechUrgency = "silent" | "low" | "normal" | "high" | "critical" | "escalation";

interface SpeechRequest {
  id: string;
  speaker: SpeakerId;
  text: string;
  urgency: SpeechUrgency;
  queuedAt: number;
}

// Priority mapping (mirrors backend: lower = higher priority)
const URGENCY_ORDER: Record<SpeechUrgency, number> = {
  escalation: 0,
  critical: 1,
  high: 2,
  normal: 3,
  low: 4,
  silent: 5,
};

// Domain priority for equal urgency (lower = higher priority)
const DOMAIN_PRIORITY: Record<SpeakerId, number> = {
  valta_prime: 0,
  jenson: 1,
  yamako: 2,
  axiom: 3,
};

// State

let _activeSpeaker: SpeakerId | null = null;
let _queue: SpeechRequest[] = [];
let _emergencyOverride = false;
let _emergencySpeaker: SpeakerId | null = null;
let _onSpeakingStarted: ((speaker: SpeakerId) => void) | null = null;
let _onSpeakingEnded: (() => void) | null = null;
let _onQueueChanged: ((queue: SpeechRequest[]) => void) | null = null;

// Callbacks

export function setArbiterCallbacks(callbacks: {
  onSpeakingStarted?: (speaker: SpeakerId) => void;
  onSpeakingEnded?: () => void;
  onQueueChanged?: (queue: SpeechRequest[]) => void;
}) {
  if (callbacks.onSpeakingStarted) _onSpeakingStarted = callbacks.onSpeakingStarted;
  if (callbacks.onSpeakingEnded) _onSpeakingEnded = callbacks.onSpeakingEnded;
  if (callbacks.onQueueChanged) _onQueueChanged = callbacks.onQueueChanged;
}

// Public API

/** Request to speak. Routes through the arbiter for queue/interrupt logic. */
export async function requestSpeak(
  speaker: SpeakerId,
  text: string,
  urgency: SpeechUrgency = "normal",
): Promise<void> {
  const request: SpeechRequest = {
    id: `speech-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    speaker,
    text,
    urgency,
    queuedAt: Date.now(),
  };

  // Emergency: interrupt immediately
  if (urgency === "critical" || urgency === "escalation") {
    _emergencyOverride = true;
    _emergencySpeaker = speaker;

    // Stop current speech
    stopSpeaking();

    // Clear non-emergency queue
    _queue = [];

    // Speak immediately
    _activeSpeaker = speaker;
    _onSpeakingStarted?.(speaker);
    updateStoreSpeaker(speaker);
    await speakWithProfile(speaker, text);
    _activeSpeaker = null;
    _emergencyOverride = false;
    _emergencySpeaker = null;
    _onSpeakingEnded?.();
    updateStoreSpeaker(null);

    // Process any queued items
    processQueue();
    return;
  }

  // High urgency: queue at front if someone is speaking
  if (urgency === "high") {
    if (_activeSpeaker !== null) {
      // Insert at front of queue (after any existing high/emergency)
      const insertIndex = _queue.findIndex(
        (q) => q.urgency !== "high" && q.urgency !== "critical" && q.urgency !== "escalation",
      );
      if (insertIndex === -1) {
        _queue.push(request);
      } else {
        _queue.splice(insertIndex, 0, request);
      }
      notifyQueueChanged();
      return;
    }
    // No active speaker — speak immediately
    _activeSpeaker = speaker;
    _onSpeakingStarted?.(speaker);
    updateStoreSpeaker(speaker);
    await speakWithProfile(speaker, text);
    _activeSpeaker = null;
    _onSpeakingEnded?.();
    updateStoreSpeaker(null);
    processQueue();
    return;
  }

  // Normal/Low urgency: queue
  _queue.push(request);
  sortQueue();
  notifyQueueChanged();

  // If nothing is speaking, process queue
  if (_activeSpeaker === null) {
    processQueue();
  }
}

/** Release the current speaker and process the next in queue. */
export function releaseSpeaker(speaker: SpeakerId): void {
  if (_activeSpeaker === speaker) {
    stopSpeaking();
    _activeSpeaker = null;
    _onSpeakingEnded?.();
    updateStoreSpeaker(null);
    processQueue();
  }
}

/** Check if a specific speaker is currently speaking. */
export function isSpeakerActive(speaker: SpeakerId): boolean {
  return _activeSpeaker === speaker;
}

/** Check if any speaker is currently speaking. */
export function isAnySpeakerActive(): boolean {
  return _activeSpeaker !== null;
}

/** Get the currently active speaker. */
export function getActiveSpeaker(): SpeakerId | null {
  return _activeSpeaker;
}

/** Get the current queue of pending speech requests. */
export function getQueue(): SpeechRequest[] {
  return [..._queue];
}

/** Interrupt the current speaker (e.g., user says "stop"). */
export function interruptCurrentSpeaker(): void {
  if (_activeSpeaker) {
    stopSpeaking();
    const interrupted = _activeSpeaker;
    _activeSpeaker = null;
    _onSpeakingEnded?.();
    updateStoreSpeaker(null);
    processQueue();
  }
}

/** Clear the entire speech queue. */
export function clearQueue(): void {
  _queue = [];
  notifyQueueChanged();
}

/** Clear emergency override. */
export function clearEmergencyOverride(): void {
  _emergencyOverride = false;
  _emergencySpeaker = null;
}

// Internal

function processQueue(): void {
  // Don't process if emergency is active
  if (_emergencyOverride) return;

  // Don't interrupt if someone is already speaking
  if (_activeSpeaker !== null) return;

  if (_queue.length === 0) return;

  const next = _queue.shift()!;
  notifyQueueChanged();

  _activeSpeaker = next.speaker;
  _onSpeakingStarted?.(next.speaker);
  updateStoreSpeaker(next.speaker);

  speakWithProfile(next.speaker, next.text).then(() => {
    _activeSpeaker = null;
    _onSpeakingEnded?.();
    updateStoreSpeaker(null);
    processQueue();
  });
}

async function speakWithProfile(speaker: SpeakerId, text: string): Promise<void> {
  const profile = getVoiceProfile(speaker);

  return new Promise((resolve) => {
    speak(text, {
      rate: profile.rate,
      pitch: profile.pitch,
      onStart: () => {
        useAxiomStore.getState().setIsSpeaking(true);
      },
      onEnd: () => {
        useAxiomStore.getState().setIsSpeaking(false);
        resolve();
      },
      onError: () => {
        useAxiomStore.getState().setIsSpeaking(false);
        resolve(); // Resolve even on error to continue queue
      },
    });
  });
}

function sortQueue(): void {
  _queue.sort((a, b) => {
    const ua = URGENCY_ORDER[a.urgency] ?? 99;
    const ub = URGENCY_ORDER[b.urgency] ?? 99;
    if (ua !== ub) return ua - ub;
    // Same urgency — use domain priority
    const da = DOMAIN_PRIORITY[a.speaker] ?? 99;
    const db = DOMAIN_PRIORITY[b.speaker] ?? 99;
    if (da !== db) return da - db;
    // Same domain — earliest first
    return a.queuedAt - b.queuedAt;
  });
}

function updateStoreSpeaker(speaker: SpeakerId | null): void {
  const store = useAxiomStore.getState();
  store.setActiveSpeaker(speaker);
  store.setCurrentSpeaker(speaker);
}

function notifyQueueChanged(): void {
  _onQueueChanged?.([..._queue]);
}