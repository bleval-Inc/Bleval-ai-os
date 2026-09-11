"""
Piper TTS provider implementation.

Piper is a fast, local, free text-to-speech system. The `piper-tts` package does
not expose a stable importable Python API, so this provider drives the `piper`
CLI binary via subprocess (same approach as the backend reference).
"""

import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from ..config import TTSConfig, tts_config
from ..models import SynthesizedAudio
from .provider_base import TTSProvider, TTSProviderFactory

logger = logging.getLogger(__name__)


class PiperTTS(TTSProvider):
    """Text-to-Speech using Piper via its CLI binary."""

    def __init__(self, config: TTSConfig = None):
        """
        Initialize Piper TTS.

        Args:
            config: TTSConfig instance
        """
        self.config = config or tts_config
        self.models_dir = Path(self.config.piper_models_dir)
        self.engine = None  # path to the piper binary, or None when unavailable
        self._load_engine()

    def _load_engine(self):
        """Locate the piper CLI binary and verify it runs."""
        venv_bin = Path(sys.executable).with_name("piper.exe")
        candidate = str(venv_bin) if venv_bin.exists() else "piper"

        try:
            result = subprocess.run(
                [candidate, "--help"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode != 0:
                self.engine = None
                logger.warning("Piper binary present but unusable; TTS disabled")
            else:
                self.engine = candidate
                logger.info(f"Piper TTS engine ready: {candidate}")
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            self.engine = None
            logger.warning(
                "Piper executable not found. Install with: pip install piper-tts"
            )

    def _resolve_model_path(self, voice_id: str) -> Optional[Path]:
        """Resolve a Piper voice identifier to a .onnx model file."""
        candidates = []
        if voice_id.endswith(".onnx"):
            candidates.append(Path(voice_id))
        candidates.append(self.models_dir / f"{voice_id}.onnx")

        for candidate in candidates:
            if candidate.exists():
                return candidate

        logger.warning(f"Piper model not found for voice '{voice_id}' in {self.models_dir}")
        return None

    def synthesize(
        self,
        text: str,
        voice_id: str,
    ) -> Optional[SynthesizedAudio]:
        """
        Synthesize text to speech using Piper.

        Args:
            text: Text to synthesize
            voice_id: Piper voice identifier (e.g., "en_GB-bnk-medium")

        Returns:
            SynthesizedAudio with audio bytes
        """
        if self.engine is None:
            logger.error("Piper TTS engine not loaded")
            return None

        model_path = self._resolve_model_path(voice_id)
        if model_path is None:
            logger.error(f"No Piper model available for voice '{voice_id}'")
            return None

        try:
            logger.debug(
                f"Synthesizing with Piper: voice={voice_id}, text='{text[:50]}...'"
            )

            audio_bytes = self._synthesize_with_piper(text, model_path)

            if not audio_bytes:
                logger.error("Piper synthesis returned empty audio")
                return None

            # Piper emits a WAV file; duration is estimated from raw samples.
            # We read the sample rate from the WAV header for accuracy.
            sample_rate, duration = self._wav_metadata(audio_bytes)

            logger.info(f"Piper synthesis complete: {duration:.2f}s audio")

            return SynthesizedAudio(
                audio_bytes=audio_bytes,
                audio_url=None,  # Not using file storage in this version
                duration_seconds=duration,
                sample_rate=sample_rate,
            )

        except Exception as e:
            logger.error(f"Error in Piper synthesis: {e}")
            return None

    def _synthesize_with_piper(self, text: str, model_path: Path) -> Optional[bytes]:
        """
        Run the piper binary to synthesize text into a WAV file.

        Args:
            text: Text to synthesize
            model_path: Path to the .onnx voice model

        Returns:
            WAV audio bytes, or None on failure
        """
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = tmp.name

        try:
            cmd = [
                self.engine,
                "--model", str(model_path),
                "--output_file", output_path,
            ]
            if not self.config.piper_enable_gpu:
                cmd.append("--cpu")

            result = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=30,
            )

            if result.returncode != 0:
                error = result.stderr.decode("utf-8", errors="replace")
                logger.error(f"Piper synthesis failed: {error}")
                return None

            with open(output_path, "rb") as f:
                return f.read()

        except (subprocess.TimeoutExpired, OSError) as e:
            logger.error(f"Error running Piper: {e}")
            return None
        finally:
            try:
                Path(output_path).unlink(missing_ok=True)
            except Exception:
                pass

    @staticmethod
    def _wav_metadata(audio_bytes: bytes) -> tuple[int, float]:
        """Extract (sample_rate, duration_seconds) from WAV bytes."""
        import wave
        import io

        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                return sample_rate, n_frames / sample_rate
        except Exception:
            # Fallback: assume 22050 Hz and 16-bit mono samples
            sample_rate = tts_config.sample_rate
            samples = len(audio_bytes) // 2
            return sample_rate, samples / sample_rate

    def health_check(self) -> bool:
        """Check if the piper binary is available."""
        return self.engine is not None


# Register Piper as a TTS provider
TTSProviderFactory.register("piper", PiperTTS)