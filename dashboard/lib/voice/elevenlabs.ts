// ElevenLabs TTS Integration
// Premium AI voice for AXIOM — warm, articulate, confident British female
// Falls back to browser SpeechSynthesis if no API key is configured

const ELEVENLABS_API = "https://api.elevenlabs.io/v1";

// Voice ID for "Charlotte" — British female, warm, articulate
// Fallback: "Rachel" (American) if Charlotte is unavailable
const AXIOM_VOICE_ID = "XB0fDUnXU5powFXDhCwa"; // Charlotte — British, warm
const FALLBACK_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"; // Rachel

let apiKey: string | null = null;

export function setElevenLabsKey(key: string) {
  apiKey = key;
}

export function getElevenLabsKey(): string | null {
  return apiKey;
}

// Cache recent audio URLs to avoid re-fetching
const audioCache = new Map<string, string>();

// Queue to prevent concurrent requests
let pendingRequest: Promise<ArrayBuffer> | null = null;

/**
 * Generate speech from text using ElevenLabs API.
 * Returns an ArrayBuffer of MP3 audio data.
 */
export async function generateSpeech(text: string): Promise<ArrayBuffer | null> {
  if (!apiKey) return null;

  // Check cache
  const cacheKey = text.slice(0, 100);
  if (audioCache.has(cacheKey)) {
    const cached = audioCache.get(cacheKey);
    if (cached) {
      const response = await fetch(cached);
      return response.arrayBuffer();
    }
  }

  // Rate limit: queue requests
  while (pendingRequest) {
    await pendingRequest.catch(() => {});
  }

  const abortController = new AbortController();
  const timeout = setTimeout(() => abortController.abort(), 10000);

  try {
    const request = fetch(
      `${ELEVENLABS_API}/text-to-speech/${AXIOM_VOICE_ID}/stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "xi-api-key": apiKey,
          Accept: "audio/mpeg",
        },
        body: JSON.stringify({
          text,
          model_id: "eleven_turbo_v2_5",
          voice_settings: {
            stability: 0.28,        // Lower = more expressive, natural variation
            similarity_boost: 0.82,  // Balanced — stays Charlotte but allows range
            style: 0.38,            // Higher style for flirty warmth & inflection
            use_speaker_boost: true,
          },
        }),
        signal: abortController.signal,
      },
    );

    pendingRequest = request.then((r) => r.arrayBuffer());
    const audioData = await pendingRequest;

    // Cache the blob URL
    const blob = new Blob([audioData], { type: "audio/mpeg" });
    const url = URL.createObjectURL(blob);
    audioCache.set(cacheKey, url);

    // Limit cache size
    if (audioCache.size > 50) {
      const firstKey = audioCache.keys().next().value;
      if (firstKey) audioCache.delete(firstKey);
    }

    return audioData;
  } catch (error) {
    if ((error as Error).name === "AbortError") {
      console.warn("ElevenLabs request timed out");
    }
    return null;
  } finally {
    clearTimeout(timeout);
    pendingRequest = null;
  }
}

/**
 * Play audio from an ArrayBuffer.
 * Returns a promise that resolves when playback completes.
 */
export function playAudio(
  buffer: ArrayBuffer,
  onStart?: () => void,
  onEnd?: () => void,
  onError?: () => void,
): HTMLAudioElement | null {
  try {
    const blob = new Blob([buffer], { type: "audio/mpeg" });
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);

    audio.onplay = () => {
      onStart?.();
    };

    audio.onended = () => {
      URL.revokeObjectURL(url);
      onEnd?.();
    };

    audio.onerror = () => {
      URL.revokeObjectURL(url);
      onError?.();
    };

    audio.play().catch(() => {
      onError?.();
    });

    return audio;
  } catch {
    onError?.();
    return null;
  }
}

let currentAudio: HTMLAudioElement | null = null;

export function setCurrentAudio(audio: HTMLAudioElement): void {
  currentAudio = audio;
}

export function stopElevenLabs(): void {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
}

// Voice info
export const AXIOM_VOICE_INFO = {
  name: "Charlotte",
  description: "British female — warm, articulate, confident with a naturally flirty edge",
  provider: "ElevenLabs",
};