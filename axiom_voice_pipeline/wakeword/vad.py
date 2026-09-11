"""
Voice Activity Detection (VAD) module.

Detects when the user has finished speaking, enabling clean audio capture windows.
Supports both silero-vad and webrtcvad engines.
"""

import logging
from typing import Optional

import numpy as np

from ..config import VADConfig, vad_config

logger = logging.getLogger(__name__)


class VADEngine:
    """Base class for VAD engines."""
    
    def process(self, audio_chunk: np.ndarray) -> float:
        """
        Process an audio chunk and return a speech probability (0.0-1.0).
        
        Args:
            audio_chunk: Audio samples (float32, mono, 16kHz)
            
        Returns:
            Probability that audio contains speech (0.0 = silence, 1.0 = speech)
        """
        raise NotImplementedError


class SileroVAD(VADEngine):
    """VAD using Silero's open-source model."""
    
    def __init__(self, threshold: float = 0.5):
        """
        Initialize Silero VAD.
        
        Args:
            threshold: Speech probability threshold
        """
        self.threshold = threshold
        try:
            # Silero models are downloaded on first use
            torch = __import__("torch")
            self.model, self.get_speech_timestamps, self.save_audio, self.read_audio = (
                torch.hub.load(
                    repo_or_dir='snakers4/silero-vad',
                    model='silero_vad',
                    force_reload=False
                )
            )
            self.model.eval()
            logger.info("Silero VAD model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD: {e}")
            self.model = None
    
    def process(self, audio_chunk: np.ndarray) -> float:
        """
        Process audio with Silero VAD.
        
        Args:
            audio_chunk: Audio samples
            
        Returns:
            Speech probability (0.0-1.0)
        """
        if self.model is None:
            # Fallback: assume speech
            return 1.0
        
        try:
            torch = __import__("torch")
            # Convert numpy to torch tensor
            audio_tensor = torch.from_numpy(audio_chunk).float()
            
            # Get speech probability
            with torch.no_grad():
                prob = self.model(audio_tensor, 16000).item()
            
            return prob
        except Exception as e:
            logger.error(f"Error in Silero VAD processing: {e}")
            return 1.0


class WebRTCVAD(VADEngine):
    """VAD using WebRTC's Voice Activity Detector."""
    
    def __init__(self, aggressiveness: int = 2):
        """
        Initialize WebRTC VAD.
        
        Args:
            aggressiveness: 0-3, higher = more aggressive filtering of non-speech
        """
        self.aggressiveness = aggressiveness
        try:
            import webrtcvad
            self.vad = webrtcvad.Vad(aggressiveness)
            logger.info(f"WebRTC VAD loaded with aggressiveness={aggressiveness}")
        except Exception as e:
            logger.error(f"Failed to load WebRTC VAD: {e}")
            self.vad = None
    
    def process(self, audio_chunk: np.ndarray) -> float:
        """
        Process audio with WebRTC VAD.
        
        Args:
            audio_chunk: Audio samples (must be 16-bit PCM)
            
        Returns:
            Binary detection: 1.0 = speech, 0.0 = silence
        """
        if self.vad is None:
            return 1.0
        
        try:
            # Convert to 16-bit PCM bytes
            audio_bytes = audio_chunk.astype(np.int16).tobytes()
            
            # WebRTC VAD returns True/False for speech detection
            is_speech = self.vad.is_speech(audio_bytes, 16000)
            
            return 1.0 if is_speech else 0.0
        except Exception as e:
            logger.error(f"Error in WebRTC VAD processing: {e}")
            return 1.0


class VoiceActivityDetector:
    """
    Wrapper for VAD engines with configurable silence detection.
    
    Tracks speech/silence transitions to determine when user has stopped speaking.
    """
    
    def __init__(self, config: VADConfig = None):
        """
        Initialize the VAD detector.
        
        Args:
            config: VADConfig instance. If None, uses global vad_config.
        """
        self.config = config or vad_config
        self.engine = self._create_engine()
        
        # State tracking
        self.speech_frames = []
        self.silence_frames = 0
        self.in_speech = False
    
    def _create_engine(self) -> VADEngine:
        """Create the configured VAD engine."""
        if self.config.engine == "silero":
            return SileroVAD(threshold=self.config.vad_threshold)
        elif self.config.engine == "webrtcvad":
            return WebRTCVAD(aggressiveness=int(self.config.vad_threshold * 3))
        else:
            logger.warning(f"Unknown VAD engine: {self.config.engine}. Using Silero.")
            return SileroVAD()
    
    def process_frame(self, audio_frame: np.ndarray) -> tuple[bool, bool]:
        """
        Process a single audio frame and detect speech/silence.
        
        Args:
            audio_frame: Audio samples for one frame
            
        Returns:
            Tuple of (has_speech, speech_ended)
            - has_speech: True if current frame contains speech
            - speech_ended: True if speech session just ended
        """
        speech_prob = self.engine.process(audio_frame)
        has_speech = speech_prob >= self.config.vad_threshold
        
        speech_ended = False
        
        if has_speech:
            self.silence_frames = 0
            if not self.in_speech:
                self.in_speech = True
                logger.debug("Speech started")
            self.speech_frames.append(audio_frame)
        else:
            # Silence frame detected
            if self.in_speech:
                self.silence_frames += 1
                
                # Check if silence duration exceeds threshold
                silence_duration = (
                    self.silence_frames * len(audio_frame) / self.config.sample_rate
                )
                
                if silence_duration >= self.config.silence_duration:
                    self.in_speech = False
                    speech_ended = True
                    logger.debug("Speech ended")
        
        return has_speech, speech_ended
    
    def get_captured_audio(self) -> Optional[np.ndarray]:
        """
        Get all captured speech frames as a single audio array.
        
        Returns:
            Concatenated audio array or None if no speech captured
        """
        if not self.speech_frames:
            return None
        
        return np.concatenate(self.speech_frames)
    
    def reset(self):
        """Reset VAD state for a new capture window."""
        self.speech_frames = []
        self.silence_frames = 0
        self.in_speech = False
        logger.debug("VAD state reset")
