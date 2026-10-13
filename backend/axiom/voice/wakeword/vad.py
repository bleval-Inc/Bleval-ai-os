"""Voice Activity Detection for end-of-speech detection after wake word."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Optional

import numpy as np

logger = logging.getLogger("axiom.voice.wakeword.vad")


class SileroVAD:
    """
    Silero VAD wrapper for voice activity detection.

    More accurate than webrtcvad, works well for end-of-speech detection.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 100,
    ):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        self._model = None
        self._utils = None
        self._lock = threading.Lock()

    def load(self) -> bool:
        """Load the Silero VAD model."""
        try:
            import torch
            # Load from torch hub
            self._model, self._utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                trust_repo=True,
            )
            self._model.eval()
            logger.info("Silero VAD model loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load Silero VAD: {e}")
            return False

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """Check if audio chunk contains speech."""
        if self._model is None:
            if not self.load():
                return True  # Default to speech if model not loaded

        try:
            import torch
            with torch.no_grad():
                # Ensure audio is float32 tensor
                if audio_chunk.dtype != np.float32:
                    audio_chunk = audio_chunk.astype(np.float32)
                # Normalize if needed
                if audio_chunk.max() > 1.0:
                    audio_chunk = audio_chunk / 32768.0

                tensor = torch.from_numpy(audio_chunk).unsqueeze(0)
                speech_prob = self._model(tensor, self.sample_rate).item()
                return speech_prob > self.threshold
        except Exception as e:
            logger.debug(f"VAD error: {e}")
            return True  # Default to speech on error

    def get_speech_timestamps(
        self,
        audio: np.ndarray,
        min_speech_duration_ms: Optional[int] = None,
        min_silence_duration_ms: Optional[int] = None,
    ) -> list:
        """Get speech segments from audio."""
        if self._model is None:
            if not self.load():
                return [{"start": 0, "end": len(audio)}]

        try:
            import torch
            min_speech = min_speech_duration_ms or self.min_speech_duration_ms
            min_silence = min_silence_duration_ms or self.min_silence_duration_ms

            # Use silero's built-in function
            get_speech_timestamps = self._utils[0]
            with torch.no_grad():
                if audio.dtype != np.float32:
                    audio = audio.astype(np.float32)
                if audio.max() > 1.0:
                    audio = audio / 32768.0
                tensor = torch.from_numpy(audio)
                timestamps = get_speech_timestamps(
                    tensor,
                    self._model,
                    sampling_rate=self.sample_rate,
                    min_speech_duration_ms=min_speech,
                    min_silence_duration_ms=min_silence,
                )
                return timestamps
        except Exception as e:
            logger.debug(f"Speech timestamp error: {e}")
            return [{"start": 0, "end": len(audio)}]


class WebRTCVAD:
    """
    WebRTC VAD wrapper - lighter weight alternative.

    Good for real-time processing, less accurate than Silero but faster.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        aggressiveness: int = 2,
        frame_duration_ms: int = 30,
    ):
        self.sample_rate = sample_rate
        self.aggressiveness = aggressiveness
        self.frame_duration_ms = frame_duration_ms
        self._vad = None
        self._frame_size = int(sample_rate * frame_duration_ms / 1000)

    def load(self) -> bool:
        """Load WebRTC VAD."""
        try:
            import webrtcvad
            self._vad = webrtcvad.Vad(self.aggressiveness)
            logger.info(f"WebRTC VAD loaded (aggressiveness={self.aggressiveness})")
            return True
        except ImportError:
            logger.error("webrtcvad not installed. Install with: pip install webrtcvad")
            return False
        except Exception as e:
            logger.error(f"Failed to load WebRTC VAD: {e}")
            return False

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """Check if audio frame contains speech."""
        if self._vad is None:
            if not self.load():
                return True

        try:
            # WebRTC VAD expects 16-bit PCM at specific frame sizes
            if audio_chunk.dtype != np.int16:
                if audio_chunk.max() <= 1.0:
                    audio_chunk = (audio_chunk * 32767).astype(np.int16)
                else:
                    audio_chunk = audio_chunk.astype(np.int16)

            # Ensure correct frame size
            if len(audio_chunk) != self._frame_size:
                # Pad or truncate
                if len(audio_chunk) < self._frame_size:
                    audio_chunk = np.pad(audio_chunk, (0, self._frame_size - len(audio_chunk)))
                else:
                    audio_chunk = audio_chunk[:self._frame_size]

            return self._vad.is_speech(audio_chunk.tobytes(), self.sample_rate)
        except Exception as e:
            logger.debug(f"WebRTC VAD error: {e}")
            return True

    def process_stream(self, audio_stream: np.ndarray) -> list:
        """Process a stream and return speech/silence segments."""
        if self._vad is None:
            self.load()

        segments = []
        num_frames = len(audio_stream) // self._frame_size

        for i in range(num_frames):
            frame = audio_stream[i * self._frame_size:(i + 1) * self._frame_size]
            is_speech = self.is_speech(frame)
            segments.append({
                "start": i * self._frame_size,
                "end": (i + 1) * self._frame_size,
                "is_speech": is_speech,
            })

        return segments


class VoiceActivityDetector:
    """
    Wrapper for VAD engines with configurable silence detection.

    Tracks speech/silence transitions to determine when user has stopped speaking.
    """

    def __init__(self, config: Any = None):
        """
        Initialize the VAD detector.

        Args:
            config: VADConfig instance. If None, uses global vad_config.
        """
        # Avoid circular import by importing inside the function
        from ..config import vad_config
        self.config = config or vad_config
        self.engine = self._create_engine()

        # State tracking
        self.speech_frames = []
        self.silence_frames = 0
        self.in_speech = False

    def _create_engine(self) -> Any:
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


# VAD Capture Manager and related classes from the other backup
class VADCaptureManager:
    """
    Manages audio capture after wake word detection using VAD
    to determine when the user has finished speaking.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        vad_type: str = "silero",  # "silero" or "webrtc"
        vad_aggressiveness: int = 2,
        silence_timeout: float = 1.5,
        max_duration: float = 10.0,
        min_duration: float = 1.0,
        on_capture_complete: Optional[Callable[[np.ndarray], None]] = None,
        device: Optional[int] = None,
    ):
        self.sample_rate = sample_rate
        self.silence_timeout = silence_timeout
        self.max_duration = max_duration
        self.min_duration = min_duration
        self.on_capture_complete = on_capture_complete
        self.device = device

        # Initialize VAD
        if vad_type == "silero":
            self.vad = SileroVAD(
                sample_rate=sample_rate,
                threshold=0.5,
                min_silence_duration_ms=int(silence_timeout * 1000),
            )
        else:
            self.vad = WebRTCVAD(
                sample_rate=sample_rate,
                aggressiveness=vad_aggressiveness,
                frame_duration_ms=30,
            )

        self._capturing = False
        self._audio_buffer: list = []
        self._preroll_buffer: list = []
        self._preroll_sample_count = 0
        self._silence_start: Optional[float] = None
        self._speech_detected = False
        self._capture_start_time: Optional[float] = None
        self._lock = threading.Lock()
        self._stream = None

    def start_capture(self) -> bool:
        """Start capturing audio after wake word."""
        logger.info("[VADCaptureManager] start_capture ENTRY")
        with self._lock:
            if self._capturing:
                logger.debug("[VADCaptureManager] Already capturing, returning False")
                return False

            import sounddevice as sd

            logger.info("[VADCaptureManager] Imported sounddevice")

            try:
                logger.info(f"[VADCaptureManager] Creating InputStream: samplerate={self.sample_rate}, device={self.device}")
                self._stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="float32",
                    blocksize=512,
                    device=self.device,
                    callback=self._audio_callback,
                )
                logger.info("[VADCaptureManager] Starting stream")
                self._stream.start()
                self._capturing = True
                self._audio_buffer = []
                self._preroll_buffer = []
                self._preroll_sample_count = 0
                self._silence_start = None
                self._speech_detected = False
                self._capture_start_time = time.time()
                logger.info("[VADCaptureManager] VAD capture started successfully")
                return True
            except Exception as e:
                logger.error(f"[VADCaptureManager] Failed to start capture: {e}", exc_info=True)
                return False

    def stop_capture(self) -> Optional[np.ndarray]:
        """Stop capture and return accumulated audio."""
        logger.info("[VADCaptureManager] stop_capture ENTRY")
        with self._lock:
            if not self._capturing:
                logger.debug("[VADCaptureManager] Not capturing, returning None")
                return None

            logger.info("[VADCaptureManager] Setting _capturing = False")
            self._capturing = False

            if self._stream:
                logger.info("[VADCaptureManager] Stopping and closing audio stream")
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception as e:
                    logger.error(f"[VADCaptureManager] Error stopping/closing stream: {e}")
                self._stream = None
                logger.info("[VADCaptureManager] Audio stream stopped and closed")

            if not self._audio_buffer:
                logger.warning("[VADCaptureManager] No audio captured")
                return None

            audio_length = len(self._audio_buffer)
            logger.info(f"[VADCaptureManager] Concatenating {audio_length} audio buffers")
            audio = np.concatenate(self._audio_buffer)
            logger.info(f"[VADCaptureManager] Capture complete: {len(audio)/self.sample_rate:.2f}s ({len(audio)} samples)")
            return audio

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info: Any, status: Any) -> None:
        """Audio callback for real-time processing."""
        logger.debug(f"[VADCaptureManager] _audio_callback ENTRY: _capturing={self._capturing}, frames={frames}")
        if not self._capturing:
            logger.debug("[VADCaptureManager] Not capturing, returning early")
            return

        audio_chunk = indata[:, 0].copy()  # Mono
        logger.debug(f"[VADCaptureManager] Audio chunk shape: {audio_chunk.shape}, dtype: {audio_chunk.dtype}")

        # Keep a rolling 1-second pre-roll so the first words after
        # the wake word are not lost while VAD is detecting speech.
        if not self._speech_detected:
            self._preroll_buffer.append(audio_chunk)
            self._preroll_sample_count += len(audio_chunk)
            logger.debug(f"[VADCaptureManager] Preroll buffer: {len(self._preroll_buffer)} chunks, {self._preroll_sample_count} samples")

            while self._preroll_sample_count > self._preroll_samples:
                removed = self._preroll_buffer.pop(0)
                self._preroll_sample_count -= len(removed)
                logger.debug(f"[VADCaptureManager] Preroll buffer trimmed: {len(self._preroll_buffer)} chunks, {self._preroll_sample_count} samples")

        # Check VAD
        logger.debug("[VADCaptureManager] Checking VAD")
        is_speech = self.vad.is_speech(audio_chunk)
        logger.debug(f"[VADCaptureManager] VAD result: is_speech={is_speech}")

        if is_speech and not self._speech_detected:
            logger.info("[VADCaptureManager] Speech detected - including preroll buffer")
            # Include audio immediately preceding speech detection.
            if self._preroll_buffer:
                self._audio_buffer.extend(self._preroll_buffer)
                logger.info(f"[VADCaptureManager] Added {len(self._preroll_buffer)} preroll chunks to audio buffer")
            self._preroll_buffer = []
            self._preroll_sample_count = 0

        self._audio_buffer.append(audio_chunk)
        logger.debug(f"[VADCaptureManager] Audio buffer now has {len(self._audio_buffer)} chunks")
        current_time = time.time()

        if is_speech:
            if not self._speech_detected:
                logger.info("[VADCaptureManager] Speech started")
            self._speech_detected = True
            self._silence_start = None
            logger.debug("[VADCaptureManager] Speech detected, reset silence timer")
        elif self._speech_detected and self._silence_start is None:
            # Speech ended, start silence timer
            logger.info("[VADCaptureManager] Speech ended - starting silence timer")
            self._silence_start = current_time
            logger.debug(f"[VADCaptureManager] Silence timer started at {current_time}")
        elif self._speech_detected and self._silence_start is not None:
            # Check if silence timeout reached
            silence_duration = current_time - self._silence_start
            logger.debug(f"[VADCaptureManager] Silence duration: {silence_duration:.3f}s (timeout: {self.silence_timeout}s)")
            if silence_duration >= self.silence_timeout:
                logger.info("Silence timeout reached, stopping capture")
                self._schedule_stop()

        # Check max duration
        if self._capture_start_time:
            capture_duration = current_time - self._capture_start_time
            logger.debug(f"[VADCaptureManager] Capture duration: {capture_duration:.3f}s (max: {self.max_duration}s)")
            if capture_duration >= self.max_duration:
                logger.info("Max duration reached, stopping capture")
                self._schedule_stop()

    def _schedule_stop(self) -> None:
        """Schedule capture stop from the audio callback thread."""
        if not self._capturing:
            return

        def finish_capture() -> None:
            audio = self.stop_capture()
            if audio is not None and self._on_capture_complete:
                try:
                    self._on_capture_complete(audio)
                except Exception as e:
                    logger.error(f"Capture callback failed: {e}")

        threading.Thread(target=finish_capture, daemon=True).start()


class MockVADCaptureManager:
    """Mock capture manager for testing."""

    def __init__(self, **kwargs):
        self.on_capture_complete = kwargs.get("on_capture_complete")
        self._capturing = False

    def start_capture(self) -> bool:
        self._capturing = True
        logger.info("[MOCK] VAD capture started")
        # Simulate capture after 2 seconds
        import threading
        threading.Timer(2.0, self._mock_complete).start()
        return True

    def stop_capture(self) -> Optional[np.ndarray]:
        self._capturing = False
        # Return dummy audio (1 second of silence)
        return np.zeros(16000, dtype=np.float32)

    def _mock_complete(self) -> None:
        if self.on_capture_complete:
            audio = np.zeros(16000, dtype=np.float32)  # 1 second
            self.on_capture_complete(audio)


def create_vad_capture_manager(
    use_mock: bool = False,
    **kwargs,
) -> VADCaptureManager | MockVADCaptureManager:
    """Factory function to create the appropriate capture manager."""
    if use_mock:
        return MockVADCaptureManager(**kwargs)
    return VADCaptureManager(**kwargs)