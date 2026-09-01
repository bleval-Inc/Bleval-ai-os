// Executive Voice Registry
// Maps each executive to distinct browser voice profiles for natural TTS.
//
// Each profile has ordered voice preferences so the system picks the
// best available voice on any platform (macOS, Windows, Chrome).
//
// Voice characteristics:
//   AXIOM:       Warm British female — default, elegant, naturally flirty
//   Jenson:      Professional male — COO tone, authoritative
//   Valta Prime: Analytical male — deliberate, measured, mentor-like
//   Yamako:      Energetic female — supportive, intelligent assistant/coach

import type { SpeakerId } from "../api-types";

// Voice Profile

export interface VoiceProfile {
  speakerId: SpeakerId;
  label: string;
  preferredVoices: string[];
  rate: number;
  pitch: number;
  description: string;
}

// Voice Profiles

const VOICE_PROFILES: Record<SpeakerId, VoiceProfile> = {
  axiom: {
    speakerId: "axiom",
    label: "AXIOM",
    // Samantha (macOS neural — warm, expressive, best free voice)
    // Fiona (Scottish female), Moira (Irish female)
    preferredVoices: ["Samantha", "Fiona", "Moira", "Microsoft Hazel", "Microsoft Susan", "Google UK English Female"],
    rate: 0.82,
    pitch: 1.10,
    description: "Warm British female — elegance, confidence, natural wit",
  },
  jenson: {
    speakerId: "jenson",
    label: "Jenson",
    // Daniel (macOS — professional British male)
    preferredVoices: ["Daniel", "Microsoft David", "Microsoft Mark", "Google UK English Male", "Alex"],
    rate: 0.85,
    pitch: 0.95,
    description: "Professional male — COO, authoritative, direct",
  },
  valta_prime: {
    speakerId: "valta_prime",
    label: "Valta Prime",
    // Alex (macOS — neutral US male), deep and deliberate
    preferredVoices: ["Alex", "Microsoft Mark", "Microsoft David", "Google US English", "Daniel"],
    rate: 0.80,
    pitch: 0.85,
    description: "Analytical male — deliberate, measured, trading mentor",
  },
  yamako: {
    speakerId: "yamako",
    label: "Yamako",
    // Karen (macOS — warm Australian female)
    preferredVoices: ["Karen", "Microsoft Zira", "Microsoft Hazel", "Google US English", "Veena"],
    rate: 0.88,
    pitch: 1.15,
    description: "Energetic female — intelligent assistant, supportive coach",
  },
};

// State

let _resolvedVoices: Record<SpeakerId, SpeechSynthesisVoice | null> = {
  axiom: null,
  jenson: null,
  valta_prime: null,
  yamako: null,
};

let _voicesLoaded = false;

// Public API

/** Get the voice profile for a speaker. */
export function getVoiceProfile(speaker: SpeakerId): VoiceProfile {
  return VOICE_PROFILES[speaker];
}

/** Get all voice profiles. */
export function getAllProfiles(): Record<SpeakerId, VoiceProfile> {
  return { ...VOICE_PROFILES };
}

/** Get the resolved SpeechSynthesisVoice for a speaker. */
export function getSpeakerVoice(speaker: SpeakerId): SpeechSynthesisVoice | null {
  if (!_voicesLoaded && typeof window !== "undefined") {
    const voices = window.speechSynthesis.getVoices();
    resolveAllVoices(voices);
    _voicesLoaded = true;
  }
  return _resolvedVoices[speaker];
}

/** Load all voices and resolve profiles for every speaker. */
export function loadAllVoices(): Promise<void> {
  return new Promise((resolve) => {
    if (typeof window === "undefined") {
      resolve();
      return;
    }

    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      resolveAllVoices(voices);
      _voicesLoaded = true;
      resolve();
      return;
    }

    window.speechSynthesis.onvoiceschanged = () => {
      const updated = window.speechSynthesis.getVoices();
      resolveAllVoices(updated);
      _voicesLoaded = true;
      resolve();
    };
  });
}

/** Get a human-readable description of what voice each speaker is using. */
export function getVoiceInfo(): Record<SpeakerId, { name: string; description: string }> {
  const info: Record<string, { name: string; description: string }> = {};
  for (const [id, profile] of Object.entries(VOICE_PROFILES)) {
    const voice = _resolvedVoices[id as SpeakerId];
    info[id] = {
      name: voice?.name ?? "Browser default",
      description: profile.description,
    };
  }
  return info as Record<SpeakerId, { name: string; description: string }>;
}

// Internal

function resolveAllVoices(voices: SpeechSynthesisVoice[]): void {
  for (const [id, profile] of Object.entries(VOICE_PROFILES)) {
    _resolvedVoices[id as SpeakerId] = selectBestVoice(voices, profile.preferredVoices);
  }
}

function selectBestVoice(
  voices: SpeechSynthesisVoice[],
  preferred: string[],
): SpeechSynthesisVoice | null {
  // 1. Exact match from preferred list
  for (const name of preferred) {
    const found = voices.find((v) => v.name === name && v.lang.startsWith("en"));
    if (found) return found;
  }

  // 2. Any English voice as fallback
  const english = voices.find((v) => v.lang.startsWith("en"));
  if (english) return english;

  return voices[0] ?? null;
}