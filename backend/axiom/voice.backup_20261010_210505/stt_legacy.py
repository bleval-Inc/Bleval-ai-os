"""Axiom OS speech-to-text engine (on-device, Vosk-based).

This module is the AI OS's own speech recognition layer. It replaces the
browser's native Web Speech API so that voice is captured on the machine and
transcribed entirely by Axiom OS — no dependency on Google/Chrome's speech
servers (which was the source of the recurring `network` errors).

Vosk is chosen because it is:
  - Lightweight (~40MB small-en model), fully offline.
  - Streaming/continuous-friendly: ideal for always-on wake-word listening.
  - Runs on CPU with low latency.

The model is downloaded lazily on first use and cached under the Axiom state
directory so subsequent starts are offline and fast.
"""

from __future__ import annotations

import io
import logging
import os
import threading
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from axiom.config import settings

logger = logging.getLogger("axiom.voice.stt")

# Executive wake-word configuration — kept in sync with the frontend
# (dashboard/components/axiom/VoiceEngine.tsx) and /voice/executives.
EXECUTIVE_WAKE_WORDS: Dict[str, List[str]] = {
    "axiom": ["axiom on", "axiom", "hey axiom", "ok axiom"],
    "jenson": ["jenson", "hey jenson", "jensen"],
    "valta_prime": ["valta prime", "valta", "hey valta", "prime"],
    "yamako": ["yamako", "hey yamako"],
}

# Official executive IDs accepted by the voice pipeline.
VALID_EXECUTIVES = ["axiom", "jenson", "valta_prime", "yamako"]

# Vosk small English model — good accuracy / size trade-off for on-device use.
VOSK_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
VOSK_MODEL_DIR = "vosk-model-small-en-us-0.15"

# Sentinel so we import vosk only when actually needed.
_vosk = None  # type: Optional[Any]


def _import_vosk():
    """Import the vosk module, raising a clear error if not installed."""
    global _vosk
    if _vosk is not None:
        return _vosk
    try:
        import vosk as _vosk_impl  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Vosk is not installed. Install it with: pip install vosk"
        ) from exc
    _vosk = _vosk_impl
    return _vosk


class SpeechToTextError(Exception):
    """Raised when speech-to-text processing fails."""


class _VoskEngine:
    """Thread-safe singleton wrapper around the Vosk recognizer."""

    def __init__(self) -> None:
        self._model = None
        self._lock = threading.Lock()
        self._model_dir: Optional[Path] = None
        self._sample_rate = 16000

    def ensure_model(self) -> Path:
        """Locate (downloading if necessary) the Vosk model directory."""
        if self._model_dir is not None and self._model_dir.exists():
            return self._model_dir

        vosk = _import_vosk()

        # Candidate locations, in priority order:
        #   1. AXIOM_VOSK_MODEL_PATH env override
        #   2. <state_dir>/models/<model_dir>  (auto-download target)
        #   3. on the module path (vosk's own auto-download fallback)
        override = os.getenv("AXIOM_VOSK_MODEL_PATH")
        candidates: List[Path] = []
        if override:
            candidates.append(Path(override))
        candidates.append(settings.state_dir / "models" / VOSK_MODEL_DIR)

        for cand in candidates:
            if cand.exists() and (cand / "am" / "final.mdl").exists():
                self._model_dir = cand
                logger.info("Using Vosk model at %s", cand)
                return cand

        # Download + extract into the state directory.
        try:
            import zipfile

            import urllib.request

            models_dir = settings.state_dir / "models"
            models_dir.mkdir(parents=True, exist_ok=True)
            target = models_dir / VOSK_MODEL_DIR
            if target.exists() and (target / "am" / "final.mdl").exists():
                self._model_dir = target
                return target

            logger.info("Downloading Vosk model from %s ...", VOSK_MODEL_URL)
            zip_path = models_dir / "vosk-model.zip"
            urllib.request.urlretrieve(VOSK_MODEL_URL, zip_path)  # noqa: S310
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(models_dir)
            zip_path.unlink(missing_ok=True)

            if not (target / "am" / "final.mdl").exists():
                raise SpeechToTextError(
                    "Vosk model downloaded but 'am/final.mdl' not found."
                )
            self._model_dir = target
            logger.info("Vosk model ready at %s", target)
            return target
        except SpeechToTextError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise SpeechToTextError(
                f"Failed to download Vosk model: {exc}. "
                "Set AXIOM_VOSK_MODEL_PATH to a pre-downloaded model directory "
                "or download manually and extract it."
            ) from exc

    def _get_recognizer(self):
        """Return a recognizer bound to the loaded model."""
        vosk = _import_vosk()
        if self._model is None:
            model_dir = self.ensure_model()
            self._model = vosk.Model(str(model_dir))
        return vosk.KaldiRecognizer(self._model, self._sample_rate)

    def transcribe_wav(self, wav_bytes: bytes) -> str:
        """Transcribe a 16 kHz mono 16-bit PCM WAV payload.

        Accepts a full WAV container (header + PCM) and returns the final
        recognized text (lowercased, trimmed). Returns "" when nothing spoken.
        """
        vosk = _import_vosk()
        try:
            # Parse the WAV header to normalise sample rate if needed.
            with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                frame_rate = wf.getframerate()
                pcm = wf.readframes(wf.getnframes())

            # Vosk expects mono 16-bit 16 kHz PCM.
            if sample_width == 2 and frame_rate == 16000 and channels == 1:
                raw = pcm
            else:
                raw = self._resample_pcm(pcm, channels, sample_width, frame_rate)

            rec = self._get_recognizer()
            if rec.AcceptWaveform(raw):
                result = rec.Result()
            else:
                result = rec.FinalResult()

            import json

            text = json.loads(result).get("text", "")
            return text.lower().strip()
        except SpeechToTextError:
            raise
        except Exception as exc:
            logger.warning("Vosk transcription failed: %s", exc)
            raise SpeechToTextError(f"Vosk transcription failed: {exc}") from exc

    def _resample_pcm(self, pcm: bytes, channels: int, sample_width: int, frame_rate: int) -> bytes:
        """Down-mix / resample to mono 16-bit 16 kHz using stdlib only.

        Uses a simple linear (sinc-free) resampler. For the common case where
        the frontend already sends mono 16 kHz this is a no-op passthrough.
        """
        import array

        samples = array.array("h")
        samples.frombytes(pcm)

        if channels > 1:
            samples = samples[::channels]

        if sample_width == 1:
            # 8-bit unsigned PCM -> 16-bit signed.
            raw8 = array.array("b", pcm)
            if channels > 1:
                raw8 = raw8[::channels]
            samples = array.array("h", (b * 256 - 32768 for b in raw8))

        if frame_rate == 16000:
            return samples.tobytes()

        # Linear resample from frame_rate -> 16000.
        target_len = int(len(samples) * 16000 / frame_rate)
        src_len = len(samples)
        out = array.array("h")
        for i in range(target_len):
            pos = i * src_len / target_len
            idx = int(pos)
            frac = pos - idx
            a = samples[min(idx, src_len - 1)]
            b = samples[min(idx + 1, src_len - 1)]
            out.append(int(a + (b - a) * frac))
        return out.tobytes()


# Module-level singleton (created lazily inside the accessor).
_engine: Optional[_VoskEngine] = None
_engine_lock = threading.Lock()


def get_engine() -> _VoskEngine:
    """Return the shared STT engine, initialising it on first use."""
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = _VoskEngine()
    return _engine


def is_available() -> bool:
    """Return True if vosk is importable (i.e. STT can run)."""
    try:
        _import_vosk()
        return True
    except Exception:  # noqa: BLE001
        return False


def transcribe_wav(wav_bytes: bytes) -> str:
    """Transcribe a WAV payload with the shared engine."""
    return get_engine().transcribe_wav(wav_bytes)


def detect_wake_word(transcript: str) -> Tuple[Optional[str], Optional[str]]:
    """Detect which executive a transcript is addressing.

    Returns (executive_id, wake_word) or (None, None) if no wake word found.
    """
    lower = transcript.lower()
    for exec_id, words in EXECUTIVE_WAKE_WORDS.items():
        for ww in words:
            if ww in lower:
                return exec_id, ww
    return None, None


def extract_command_after_wake(transcript: str, exec_id: Optional[str], wake_word: Optional[str]) -> str:
    """Strip the wake word from a transcript, returning the command text.

    If no wake word is matched, the full transcript is returned.
    """
    lower = transcript.lower()
    if wake_word and wake_word in lower:
        idx = lower.index(wake_word)
        return transcript[idx + len(wake_word):].strip()
    if exec_id:
        # Also strip the bare executive name when it leads the phrase.
        for ww in EXECUTIVE_WAKE_WORDS[exec_id]:
            if lower.startswith(ww):
                return transcript[len(ww):].strip()
    return transcript.strip()