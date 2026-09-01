"""Speech-to-Text using faster-whisper."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from axiom.voice.config import voice_config

logger = logging.getLogger("axiom.voice.stt.whisper_engine")


class WhisperEngine:
    """
    Wrapper around faster-whisper for local speech-to-text.
    
    Runs transcription only on captured post-wake-word audio windows,
    not continuously (to save resources).
    """
    
    def __init__(self, config: Optional[Any] = None):
        self.config = config or voice_config.stt
        self._model = None
        self._lock = threading.Lock()
        
    def load(self) -> bool:
        """Load the faster-whisper model."""
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            logger.error("faster-whisper not installed. Install with: pip install faster-whisper")
            return False
        
        try:
            logger.info(f"Loading faster-whisper model: {self.config.model_size}")
            self._model = WhisperModel(
                self.config.model_size,
                device=self.config.device,
                compute_type=self.config.compute_type,
            )
            logger.info("faster-whisper model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load faster-whisper model: {e}")
            return False
    
    def transcribe(
        self,
        audio: np.ndarray,
        language: Optional[str] = None,
    ) -> Tuple[str, float]:
        """
        Transcribe audio to text.
        
        Args:
            audio: Float32 audio array at 16kHz mono
            language: Language code (None for auto-detect)
            
        Returns:
            Tuple of (transcribed_text, confidence)
        """
        if self._model is None:
            if not self.load():
                raise RuntimeError("Whisper model not loaded")
        
        try:
            # Ensure audio is float32 and normalized
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            if audio.max() > 1.0:
                audio = audio / 32768.0
            
            # Run transcription
            segments, info = self._model.transcribe(
                audio,
                language=language or self.config.language,
                beam_size=self.config.beam_size,
                vad_filter=self.config.vad_filter,
            )
            
            # Combine all segments
            full_text = " ".join([seg.text for seg in segments]).strip()
            
            # Calculate average confidence (using no_speech_prob as inverse)
            confidences = [1.0 - seg.no_speech_prob for seg in segments]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(f"Transcription: '{full_text}' (confidence: {avg_confidence:.3f})")
            return full_text, avg_confidence
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    def transcribe_file(self, file_path: str) -> Tuple[str, float]:
        """Transcribe an audio file."""
        if self._model is None:
            if not self.load():
                raise RuntimeError("Whisper model not loaded")
        
        try:
            segments, info = self._model.transcribe(
                file_path,
                language=self.config.language,
                beam_size=self.config.beam_size,
                vad_filter=self.config.vad_filter,
            )
            
            full_text = " ".join([seg.text for seg in segments]).strip()
            confidences = [1.0 - seg.no_speech_prob for seg in segments]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return full_text, avg_confidence
        except Exception as e:
            logger.error(f"File transcription failed: {e}")
            raise


class MockWhisperEngine:
    """Mock STT engine for testing."""
    
    def __init__(self, config: Optional[Any] = None):
        self.config = config or voice_config.stt
        
    def load(self) -> bool:
        logger.info("Mock Whisper engine 'loaded'")
        return True
    
    def transcribe(self, audio: np.ndarray, language: Optional[str] = None) -> Tuple[str, float]:
        """Return a mock transcription."""
        import random
        mock_responses = [
            "check my schedule for today",
            "what's the status of the trading portfolio",
            "analyze gold price action",
            "create a new project for the agency",
            "set a reminder for tomorrow morning",
            "show me the latest market news",
        ]
        text = random.choice(mock_responses)
        confidence = random.uniform(0.7, 0.95)
        logger.info(f"[MOCK] Transcription: '{text}' (confidence: {confidence:.3f})")
        return text, confidence
    
    def transcribe_file(self, file_path: str) -> Tuple[str, float]:
        return self.transcribe(np.zeros(16000))


def create_whisper_engine(use_mock: bool = False) -> WhisperEngine | MockWhisperEngine:
    """Factory function to create the appropriate STT engine."""
    if use_mock:
        return MockWhisperEngine()
    return WhisperEngine()