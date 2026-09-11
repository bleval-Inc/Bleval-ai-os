"""
Speech-to-Text using faster-whisper.

Local, fast, no per-second API cost.
"""

import logging
from typing import Optional

import numpy as np

from ..config import STTConfig, stt_config
from ..models import TranscriptionComplete

logger = logging.getLogger(__name__)


class WhisperEngine:
    """Speech-to-Text engine using OpenAI's Whisper via faster-whisper."""
    
    def __init__(self, config: STTConfig = None):
        """
        Initialize the Whisper engine.
        
        Args:
            config: STTConfig instance. If None, uses global stt_config.
        """
        self.config = config or stt_config
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            from faster_whisper import WhisperModel

            logger.info(f"Loading Whisper model: {self.config.model_size}")

            # faster-whisper's constructor does not accept "auto" or "language";
            # resolve "auto" to concrete values and pass language at transcribe().
            device = self.config.device
            if device == "auto":
                device = "cpu"
            compute_type = self.config.compute_type
            if compute_type == "auto":
                compute_type = "int8" if device == "cpu" else "float16"

            self.model = WhisperModel(
                self.config.model_size,
                device=device,
                compute_type=compute_type,
            )

            logger.info("Whisper model loaded successfully")
        except ImportError:
            logger.error(
                "faster-whisper not installed. Install with: pip install faster-whisper"
            )
            self.model = None
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            self.model = None
    
    def transcribe(self, audio_bytes: bytes) -> Optional[TranscriptionComplete]:
        """
        Transcribe audio to text.
        
        Args:
            audio_bytes: Raw audio data (WAV format or raw PCM)
            
        Returns:
            TranscriptionComplete object with transcribed text and metadata
        """
        if self.model is None:
            logger.error("Whisper model not loaded")
            return None
        
        try:
            # Convert audio bytes to WAV format if needed
            audio = self._prepare_audio(audio_bytes)
            
            # Transcribe with temperature control
            segments, info = self.model.transcribe(
                audio,
                language=self.config.language,
                temperature=self.config.temperature,
                vad_filter=True,  # Use VAD to auto-detect speech segments
            )
            
            # Collect all segments into full text
            full_text = " ".join(segment.text for segment in segments)
            
            if not full_text.strip():
                logger.warning("Transcription resulted in empty text")
                return None
            
            # Estimate duration
            duration = len(audio_bytes) / (self.config.model_size != "tiny" and 32000 or 16000)
            
            logger.info(f"Transcription complete: '{full_text}'")
            
            return TranscriptionComplete(
                raw_text=full_text.strip(),
                confidence=None,  # faster-whisper doesn't provide per-segment confidence
                duration_seconds=duration,
            )
        
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return None
    
    def _prepare_audio(self, audio_bytes: bytes) -> np.ndarray:
        """
        Prepare audio bytes for Whisper.
        
        Whisper expects audio loaded via librosa.
        
        Args:
            audio_bytes: Raw audio bytes
            
        Returns:
            Audio array compatible with Whisper
        """
        try:
            # The orchestrator passes raw 16-bit PCM mono 16kHz samples; decode
            # directly to a normalized float32 array for faster-whisper.
            audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            return audio
        except Exception as e:
            logger.error(f"Error preparing audio: {e}")
            # Return empty array to allow graceful degradation
            return np.array([], dtype=np.float32)
    
    def health_check(self) -> bool:
        """Check if the model is loaded and ready."""
        return self.model is not None
