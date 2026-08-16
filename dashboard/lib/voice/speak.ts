// ── AXIOM Voice Engine ────────────────────────────────────────────
// Primary: browser SpeechSynthesis — free, unlimited, no API key
// Premium: ElevenLabs — purely optional upgrade (set a key to activate)
//
// Voice goal: natural, warm, British female with a flirtatious,
// confident tone — all using free OS-level voices.
//
// Best free voices by platform:
//   macOS:      Samantha (premium/enhanced — incredibly natural, warm)
//               Fiona (Scottish/British female, very natural)
//               Moira (Irish female, warm)
//   Windows/Edge: Microsoft Hazel (UK female neural — excellent)
//                 Microsoft Susan, Linda (neural voices)
//   Chrome:     Google UK English Female, Google US English

import type { SpeechOptions } from "./types";

// ── Voice selection ───────────────────────────────────────────────

let axiomVoice: SpeechSynthesisVoice | null = null;
let voicesLoaded = false;

/**
 * Free high-quality voices ranked by naturalness.
 *
 * macOS (Apple):
 *   Samantha  — Enhanced neural voice; warm, expressive, often
 *               mistaken for a real person. The gold standard for
 *               free TTS naturalness on macOS.
 *   Fiona     — Scottish female; closer to a British accent.
 *   Moira     — Irish female; warm, natural.
 *
 * Windows Edge:
 *   Hazel     — UK female neural voice; genuinely excellent,
 *               near ElevenLabs quality for many sentences.
 *   Susan     — Another neural UK female.
 *   Zira      — Natural US female.
 *
 * Chrome:
 *   Google UK English Female — decent quality.
 */
const PREFERRED_VOICES = [
  // macOS premium (most natural)
  "Samantha",
  "Fiona",
  "Moira",
  // Windows Edge neural
  "Microsoft Hazel",
  "Microsoft Susan",
  "Microsoft Linda",
  "Microsoft Zira",
  // Google
  "Google UK English Female",
  "Google US English",
  "Karen",
  "Veena",
  "Tessa",
];

// Warm, conversational tuning for a naturally flirty, professional tone
const WARMTH_RATE = 0.82;   // Slightly slow = deliberate, sultry cadence
const WARMTH_PITCH = 1.10;  // Slightly raised = warm, approachable

export function getAxiomVoice(): SpeechSynthesisVoice | null {
  if (!voicesLoaded && typeof window !== "undefined") {
    const voices = window.speechSynthesis.getVoices();
    axiomVoice = selectBestVoice(voices);
    voicesLoaded = true;
  }
  return axiomVoice;
}

export function loadVoices(): Promise<SpeechSynthesisVoice | null> {
  return new Promise((resolve) => {
    if (typeof window === "undefined") {
      resolve(null);
      return;
    }

    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      axiomVoice = selectBestVoice(voices);
      voicesLoaded = true;
      resolve(axiomVoice);
      return;
    }

    window.speechSynthesis.onvoiceschanged = () => {
      const updated = window.speechSynthesis.getVoices();
      axiomVoice = selectBestVoice(updated);
      voicesLoaded = true;
      resolve(axiomVoice);
    };
  });
}

function selectBestVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  // 1. Exact match from preferred list (best natural voices first)
  for (const name of PREFERRED_VOICES) {
    const found = voices.find((v) => v.name === name && v.lang.startsWith("en"));
    if (found) return found;
  }

  // 2. Any English female voice
  const female = voices.find(
    (v) =>
      v.lang.startsWith("en") &&
      (v.name.toLowerCase().includes("female") ||
        v.name.toLowerCase().includes("zira") ||
        v.name.toLowerCase().includes("hazel") ||
        v.name.toLowerCase().includes("samantha")),
  );
  if (female) return female;

  // 3. Any English voice
  const english = voices.find((v) => v.lang.startsWith("en"));
  if (english) return english;

  return voices[0] ?? null;
}

// ── State ─────────────────────────────────────────────────────────

let currentUtterance: SpeechSynthesisUtterance | null = null;

// Global callbacks for UI state
let _onSpeakingStarted: (() => void) | null = null;
let _onSpeakingEnded: (() => void) | null = null;

export function setSpeakingCallbacks(
  onStart: (() => void) | null,
  onEnd: (() => void) | null,
) {
  _onSpeakingStarted = onStart;
  _onSpeakingEnded = onEnd;
}

export function isAxiomSpeaking(): boolean {
  if (typeof window !== "undefined" && window.speechSynthesis.speaking) return true;
  return false;
}

// ── Speak ─────────────────────────────────────────────────────────

/**
 * Speak text through AXIOM's voice.
 *
 * Primary: browser SpeechSynthesis — free, unlimited, no API key.
 *   On macOS this uses Samantha/Fiona/Moira (premium-enhanced neural
 *   voices). On Windows Edge it uses Microsoft's neural UK voices.
 *   Both are genuinely human-quality with zero cost.
 *
 * Premium: ElevenLabs — purely optional. Pass a key to activate.
 */
export async function speak(
  text: string,
  options?: SpeechOptions,
): Promise<void> {
  // Cancel any current speech first
  stopSpeaking();

  // ── Try ElevenLabs if configured (purely optional upgrade) ───
  if (getElevenLabsKey()) {
    try {
      const { generateSpeech, playAudio } = await import("./elevenlabs");
      const audioData = await generateSpeech(text);
      if (audioData) {
        const audio = playAudio(audioData, options?.onStart, options?.onEnd, options?.onError);
        if (audio) {
          (await import("./elevenlabs")).setCurrentAudio(audio);
          return;
        }
      }
    } catch {
      // Fall through to browser TTS
    }
  }

  // ── Primary: browser SpeechSynthesis (free, unlimited) ────────
  const utterance = new SpeechSynthesisUtterance(text);

  // Select the best natural voice
  const voice = getAxiomVoice();
  if (voice) {
    utterance.voice = voice;
  }

  // Warm, conversational, flirty-professional tuning
  utterance.rate = options?.rate ?? WARMTH_RATE;
  utterance.pitch = options?.pitch ?? WARMTH_PITCH;
  utterance.volume = options?.volume ?? 1.0;

  const onStart = () => {
    _onSpeakingStarted?.();
    options?.onStart?.();
  };

  const onEnd = () => {
    _onSpeakingEnded?.();
    options?.onEnd?.();
  };

  utterance.onstart = onStart;
  utterance.onend = onEnd;
  utterance.onerror = () => {
    _onSpeakingEnded?.();
    options?.onError?.();
  };

  currentUtterance = utterance;
  window.speechSynthesis.speak(utterance);
}

// ── Stop ──────────────────────────────────────────────────────────

export function stopSpeaking(): void {
  if (typeof window !== "undefined") {
    window.speechSynthesis.cancel();
  }
  currentUtterance = null;

  // Also stop ElevenLabs if running
  try {
    const { stopElevenLabs } = require("./elevenlabs");
    stopElevenLabs();
  } catch {
    // ElevenLabs not available — fine
  }
}

// ── ElevenLabs integration (re-export for convenience) ─────────────

let _elevenLabsKey: string | null = null;

export function setElevenLabsKey(key: string) {
  _elevenLabsKey = key;
  try {
    require("./elevenlabs").setElevenLabsKey(key);
  } catch {
    // Module not loaded yet
  }
}

export function getElevenLabsKey(): string | null {
  return _elevenLabsKey;
}

// ── Voice info ────────────────────────────────────────────────────

export function getAxiomVoiceInfo() {
  const hasElevenLabs = !!getElevenLabsKey();
  const voice = axiomVoice;
  return {
    name: hasElevenLabs ? "Charlotte" : voice?.name ?? "Browser voice",
    description: hasElevenLabs
      ? "British female — warm, articulate, confident"
      : `${voice?.name ?? "Default"} — browser SpeechSynthesis (free)`,
    provider: hasElevenLabs ? "ElevenLabs" : "Browser (free)",
    active: hasElevenLabs ? "ElevenLabs" : voice?.name ?? "Default",
  };
}