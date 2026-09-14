"""Pipeline orchestrator - ties wake -> stt -> router -> engine -> tts -> relay together."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from queue import Queue, Empty

import numpy as np

from axiom.voice.config import voice_config
from axiom.voice.wakeword import (
    WakeWordDetector,
    create_wake_word_detector,
)
from axiom.voice.wakeword.vad import SileroVAD
from axiom.voice.stt import (
    WhisperEngine,
    create_whisper_engine,
)
from axiom.voice.router import IntentRouter
from axiom.voice.tts import (
    get_tts_service,
    TextToSpeechService,
)
from axiom.voice.relay.ws_server import VoiceRelayServer
from axiom.voice.wake_listener import VoiceListener


logger = logging.getLogger("axiom.voice.pipeline_orchestrator")


class VoiceConnectionManager:
    """Wrapper around VoiceRelayServer to match WebSocketConnectionManager interface."""

    def __init__(self, relay_server: VoiceRelayServer):
        self.relay_server = relay_server

    async def connect(self, websocket) -> None:
        """Delegate to the relay server's internal client handler."""
        await self.relay_server._handle_client(websocket)

    async def disconnect(self, websocket) -> None:
        """The relay server removes the websocket when the client handler exits."""
        pass

    def get_connection_count(self) -> int:
        """Return the current relay client count."""
        return self.relay_server.client_count


class VoiceState(Enum):
    """Voice pipeline states."""

    LISTENING = "listening"
    ACKNOWLEDGING = "acknowledging"
    CAPTURING = "capturing"
    PROCESSING = "processing"
    SPEAKING = "speaking"


@dataclass
class VoiceEvent:
    """Event in the voice pipeline."""

    event_type: str
    entity: str
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )
    data: Dict[str, Any] = field(default_factory=dict)


class AudioProcessor:
    """Process audio for voice command capture (no microphone stream)."""

    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1280):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size

        # Audio queue for incoming audio frames (from VoiceListener in capturing state)
        self.audio_queue = Queue(maxsize=20)

        # Controls whether callback frames are accepted for processing.
        self._running = False

        # Prevent accidental duplicate initialization.
        self._initialized = False

        # Components.
        self.wake_detector: Optional[WakeWordDetector] = None
        self.vad_processor: Optional[Any] = None

        # Capture state.
        self._audio_buffer: List[np.ndarray] = []
        self._preroll_buffer: List[np.ndarray] = []
        self._preroll_sample_count = 0
        self._preroll_samples = int(sample_rate * 1.0)

        self._silence_start: Optional[float] = None
        self._speech_detected = False
        self._capture_start_time: Optional[float] = None

        self._max_duration: float = 10.0
        self._silence_timeout: float = 1.5
        self._min_duration: float = 1.0

        self._on_capture_complete: Optional[
            Callable[[np.ndarray], None]
        ] = None

        # Diagnostics.
        self._callback_count = 0
        self._frames_received = 0
        self._frames_dropped = 0
        self._wake_predictions = 0
        self._wake_detections = 0

        # Last wake result.
        self._last_wake_entity: Optional[str] = None
        self._last_wake_word: Optional[str] = None
        self._last_wake_confidence: float = 0.0
        self._last_wake_time: float = 0.0

        self._wake_result_lock = threading.Lock()

    def initialize(self, runtime: Any = None) -> bool:
        """Initialize models and VAD (no microphone stream)."""
        if self._initialized:
            logger.warning("[AUDIO_INIT] Audio processor already initialized")
            return True

        try:
            # ---------------------------------------------------------
            # Wake-word detector
            # ---------------------------------------------------------
            wake_detector = create_wake_word_detector(
                use_mock=False,
                on_wake=None,
            )

            if not wake_detector.load_models():
                logger.error("[AUDIO_INIT] Wake word models failed to load")
                return False

            self.wake_detector = wake_detector

            # Important:
            # The detector is NOT started here.
            #
            # initialize() prepares models.
            # start() enables actual frame processing.
            #
            # This prevents audio from accumulating in the queue before
            # the audio consumer thread exists.
            logger.info("[AUDIO_INIT] Wake word models loaded")

            # ---------------------------------------------------------
            # Silero VAD
            # ---------------------------------------------------------
            self.vad_processor = SileroVAD(
                sample_rate=self.sample_rate,
                threshold=0.5,
                min_silence_duration_ms=int(
                    self._silence_timeout * 1000
                ),
            )

            if not self.vad_processor.load():
                logger.error("[AUDIO_INIT] VAD model failed to load")
                self.wake_detector = None
                return False

            logger.info("[AUDIO_INIT] VAD loaded")

            self._initialized = True

            logger.info(
                "[AUDIO_INIT] Audio processor initialized successfully"
            )

            return True

        except Exception as e:
            logger.error(
                f"[AUDIO_INIT] Failed to initialize audio processor: {e}",
                exc_info=True,
            )

            # Clean up anything that may have been opened.
            self._running = False
            self.wake_detector = None
            self.vad_processor = None
            self._initialized = False

            return False

    def start(self) -> bool:
        """
        Start audio processing.

        No microphone stream to start. This method only enables processing
        and starts the wake detector's processing state.
        """
        if self._running:
            logger.warning("[AUDIO_PROCESSOR_START] Already running")
            return True

        if not self._initialized:
            logger.error(
                "[AUDIO_PROCESSOR_START] Audio processor is not initialized"
            )
            return False

        if not self.wake_detector:
            logger.error(
                "[AUDIO_PROCESSOR_START] Wake word detector is unavailable"
            )
            return False

        if not self.wake_detector.start():
            logger.error(
                "[AUDIO_PROCESSOR_START] Wake word detector failed to start"
            )
            return False

        # Enable microphone callback processing only after the detector
        # has successfully entered its running state.
        # Small delay to allow wake detector to fully initialize
        time.sleep(0.1)
        self._running = True

        logger.info(
            "[AUDIO_PROCESSOR_START] Audio processor started"
        )

        return True

    def process_audio_chunk(
        self,
        audio_chunk: np.ndarray,
        state: VoiceState,
        current_entity: Optional[str],
    ) -> None:
        """Process one audio chunk according to the current voice state."""

        if not self._running:
            return

        if state == VoiceState.LISTENING:
            self._process_for_wake_word(audio_chunk)

        elif state == VoiceState.CAPTURING:
            self._process_for_capture(
                audio_chunk,
                current_entity,
            )

        # During ACKNOWLEDGING, PROCESSING and SPEAKING the microphone
        # remains physically open, but wake/capture processing is disabled.

    def _process_for_wake_word(
        self,
        audio_chunk: np.ndarray,
    ) -> None:
        """Process an audio chunk through the wake-word detector."""

        if not self.wake_detector:
            return

        self._wake_predictions += 1

        result = self.wake_detector.process_audio(audio_chunk)

        if result is None:
            return

        entity, confidence, wake_word = result

        self._wake_detections += 1

        logger.info(
            f"[WAKE_DETECTED] Entity: {entity}, "
            f"Wake word: '{wake_word}', "
            f"Score: {confidence:.3f}"
        )

        with self._wake_result_lock:
            self._last_wake_entity = entity
            self._last_wake_word = wake_word
            self._last_wake_confidence = confidence
            self._last_wake_time = time.time()

    def _process_for_capture(
        self,
        audio_chunk: np.ndarray,
        current_entity: Optional[str],
    ) -> None:
        """Process audio through Silero VAD during command capture."""

        if not self.vad_processor or not self._on_capture_complete:
            return

        self._audio_buffer.append(audio_chunk.copy())

        # -------------------------------------------------------------
        # Preroll
        # -------------------------------------------------------------
        if not self._speech_detected:
            self._preroll_buffer.append(audio_chunk.copy())
            self._preroll_sample_count += len(audio_chunk)

            while self._preroll_sample_count > self._preroll_samples:
                removed = self._preroll_buffer.pop(0)
                self._preroll_sample_count -= len(removed)

        # -------------------------------------------------------------
        # VAD
        # -------------------------------------------------------------
        try:
            is_speech = self.vad_processor.is_speech(audio_chunk)
            current_time = time.time()

            if is_speech and not self._speech_detected:
                logger.debug("[VAD_SPEECH_START] Speech detected")

                # Add the buffered preroll before the current speech.
                if self._preroll_buffer:
                    # Avoid duplicating the current chunk because it has
                    # already been added to _audio_buffer above.
                    preroll = list(self._preroll_buffer)

                    if preroll:
                        self._audio_buffer = (
                            preroll[:-1] + self._audio_buffer
                            if np.array_equal(
                                preroll[-1],
                                audio_chunk,
                            )
                            else preroll + self._audio_buffer
                        )

                self._preroll_buffer = []
                self._preroll_sample_count = 0

                self._speech_detected = True
                self._silence_start = None

            elif self._speech_detected and is_speech:
                self._silence_start = None

            elif self._speech_detected and not is_speech:
                if self._silence_start is None:
                    self._silence_start = current_time
                    logger.debug("[VAD_SILENCE_START] Silence started")

                elif (
                    current_time - self._silence_start
                ) >= self._silence_timeout:
                    logger.info(
                        "[VAD_CAPTURE_COMPLETE] "
                        "Silence timeout reached"
                    )

                    self._finalize_capture(current_entity)
                    return

        except Exception as e:
            logger.debug(
                f"[VAD_PROCESSING_ERROR] {e}"
            )

        # -------------------------------------------------------------
        # Maximum capture duration
        # -------------------------------------------------------------
        if self._capture_start_time:
            capture_duration = (
                time.time() - self._capture_start_time
            )

            if capture_duration >= self._max_duration:
                logger.info(
                    "[VAD_CAPTURE_COMPLETE] Max duration reached"
                )

                self._finalize_capture(current_entity)

    def _finalize_capture(
        self,
        current_entity: Optional[str],
    ) -> None:
        """Finalize the current VAD capture exactly once."""

        if not self._audio_buffer:
            logger.warning(
                "[VAD_CAPTURE] No audio captured"
            )
            return

        # Any remaining preroll belongs at the beginning of the capture.
        if self._preroll_buffer:
            self._audio_buffer = (
                self._preroll_buffer + self._audio_buffer
            )

        audio = np.concatenate(self._audio_buffer)

        duration = len(audio) / self.sample_rate

        logger.info(
            f"[VAD_CAPTURE] Capture complete: "
            f"{duration:.2f}s ({len(audio)} samples)"
        )

        # Reset capture state BEFORE invoking the callback.
        # This prevents duplicate completion if downstream processing
        # takes time.
        self._audio_buffer = []
        self._preroll_buffer = []
        self._preroll_sample_count = 0
        self._silence_start = None
        self._speech_detected = False
        self._capture_start_time = None

        callback = self._on_capture_complete

        # The callback is one-shot for each capture.
        self._on_capture_complete = None

        if callback:
            try:
                callback(audio)
            except Exception as e:
                logger.error(
                    f"[VAD_CAPTURE_CALLBACK_ERROR] {e}",
                    exc_info=True,
                )

    def start_capture(
        self,
        on_capture_complete: Callable[[np.ndarray], None],
    ) -> bool:
        """Start capturing the command after a wake word."""

        if not self._running:
            logger.error(
                "[VAD_CAPTURE_START] Audio processor is not running"
            )
            return False

        if not self.vad_processor:
            logger.error(
                "[VAD_CAPTURE_START] VAD processor unavailable"
            )
            return False

        # Reset any stale capture state.
        self._audio_buffer = []
        self._preroll_buffer = []
        self._preroll_sample_count = 0
        self._silence_start = None
        self._speech_detected = False
        self._capture_start_time = time.time()

        self._on_capture_complete = on_capture_complete

        logger.info(
            "[VAD_CAPTURE_START] Capture started"
        )

        return True

    def stop(self) -> None:
        """Stop audio processing, wake detection and clear queues."""

        self._running = False

        # Stop wake detector processing first.
        if self.wake_detector:
            try:
                self.wake_detector.stop()
            except Exception as e:
                logger.debug(
                    f"[AUDIO_PROCESSOR_STOP] Wake detector stop error: {e}"
                )

        # Cancel active capture state.
        self._on_capture_complete = None
        self._audio_buffer = []
        self._preroll_buffer = []
        self._preroll_sample_count = 0
        self._silence_start = None
        self._speech_detected = False
        self._capture_start_time = None

        # Clear queued audio so a future lifecycle start cannot process
        # stale frames from the previous run.
        while True:
            try:
                self.audio_queue.get_nowait()
            except Empty:
                break

        logger.info(
            "[AUDIO_PROCESSOR_STOP] Audio processor stopped"
        )

    def get_diagnostics(self) -> Dict[str, Any]:
        """Return audio pipeline diagnostics."""

        wake_running = False

        if self.wake_detector:
            wake_running = bool(
                getattr(
                    self.wake_detector,
                    "_running",
                    False,
                )
            )

        return {
            "callback_count": self._callback_count,
            "frames_received": self._frames_received,
            "frames_dropped": self._frames_dropped,
            "wake_predictions": self._wake_predictions,
            "wake_detections": self._wake_detections,
            "audio_processor_running": self._running,
            "wake_detector_running": wake_running,
            "initialized": self._initialized,
        }

    def _get_wake_detection_result(
        self,
    ) -> Optional[Dict[str, Any]]:
        """Get the last wake-word detection result."""

        with self._wake_result_lock:
            if self._last_wake_entity is not None:
                return {
                    "entity": self._last_wake_entity,
                    "wake_word": self._last_wake_word,
                    "confidence": self._last_wake_confidence,
                    "timestamp": self._last_wake_time,
                }

        return None

    def _clear_wake_detection_result(self) -> None:
        """Clear the stored wake-word result."""

        with self._wake_result_lock:
            self._last_wake_entity = None
            self._last_wake_word = None
            self._last_wake_confidence = 0.0
            self._last_wake_time = 0.0


class VoicePipelineOrchestrator:
    """
    Main orchestrator for the voice pipeline with explicit state machine.

    LISTENING
        -> wake word
    ACKNOWLEDGING
        -> fixed acknowledgment
    CAPTURING
        -> VAD detects command end
    PROCESSING
        -> STT -> Route -> Execute -> TTS
    SPEAKING
        -> response complete
    LISTENING
    """

    def __init__(
        self,
        config: Optional[Any] = None,
        runtime: Optional[Any] = None,
        use_mock: bool = False,
    ):
        self.config = config or voice_config
        self.runtime = runtime
        self.use_mock = use_mock

        # -------------------------------------------------------------
        # State
        # -------------------------------------------------------------
        self._state = VoiceState.LISTENING
        self._state_lock = threading.Lock()
        self._running = False
        self._current_entity: Optional[str] = None

        # -------------------------------------------------------------
        # Components
        # -------------------------------------------------------------
        self.audio_processor = AudioProcessor()
        self.voice_listener: Optional[VoiceListener] = None

        self.stt_engine: Optional[WhisperEngine] = None
        self.intent_router = IntentRouter()
        self.tts_service: Optional[TextToSpeechService] = None
        self.relay_server: Optional[VoiceRelayServer] = None

        # Compatibility for voice_pipeline_routes.
        self.connection_manager = None

        # -------------------------------------------------------------
        # Conversation history
        # -------------------------------------------------------------
        self._conversation_history: Dict[
            str,
            List[Dict[str, str]],
        ] = {}

        # -------------------------------------------------------------
        # Async event loop
        # -------------------------------------------------------------
        self._loop: Optional[
            asyncio.AbstractEventLoop
        ] = None

        # -------------------------------------------------------------
        # Audio loop
        # -------------------------------------------------------------
        self._audio_loop_thread: Optional[
            threading.Thread
        ] = None

        # -------------------------------------------------------------
        # Event callbacks
        # -------------------------------------------------------------
        self._event_callbacks: List[
            Callable[[VoiceEvent], None]
        ] = []

    def _emit_event(self, event: VoiceEvent) -> None:
        """Emit an event to callbacks and the relay server."""

        for callback in self._event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(
                    f"Event callback error: {e}",
                    exc_info=True,
                )

        if self.relay_server and self._loop:
            try:
                if self._loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.relay_server.broadcast_event(event),
                        self._loop,
                    )
            except Exception as e:
                logger.debug(
                    f"Relay broadcast error: {e}"
                )

    def _transition_state(
        self,
        new_state: VoiceState,
    ) -> None:
        """Safely transition the voice state."""

        with self._state_lock:
            old_state = self._state
            self._state = new_state

        if old_state != new_state:
            logger.info(
                f"[VOICE_STATE_TRANSITION] "
                f"{old_state.value} -> {new_state.value}"
            )

    def initialize(self) -> bool:
        """Initialize all voice pipeline components."""

        logger.info(
            "Initializing voice pipeline..."
        )

        try:
            # ---------------------------------------------------------
            # TTS
            # ---------------------------------------------------------
            self.tts_service = get_tts_service(use_mock=self.use_mock)

            if not self.tts_service.initialize():
                logger.error(
                    "TTS service initialization failed"
                )
                return False

            # ---------------------------------------------------------
            # STT
            # ---------------------------------------------------------
            self.stt_engine = create_whisper_engine(
                use_mock=self.use_mock
            )

            if not self.stt_engine.load():
                logger.error(
                    "STT engine initialization failed"
                )
                return False

            # ---------------------------------------------------------
            # Wake Word Detector (for VoiceListener)
            # ---------------------------------------------------------
            wake_detector = create_wake_word_detector(
                use_mock=self.use_mock,
                on_wake=None,
            )

            if not wake_detector.load_models():
                logger.error("[AUDIO_INIT] Wake word models failed to load")
                return False

            # ---------------------------------------------------------
            # Voice Listener
            # ---------------------------------------------------------
            # Pass the audio processor's audio queue to the voice listener
            # so it can send audio frames during capturing state.
            self.voice_listener = VoiceListener(
                wake_detector=wake_detector,
                on_wake=self._handle_wake_word_detected,
                audio_queue=self.audio_processor.audio_queue,
                device=1,
                samplerate=16000,
                channels=1,
                dtype='float32',
                blocksize=1280
            )

            # ---------------------------------------------------------
            # Relay
            # ---------------------------------------------------------
            self.relay_server = VoiceRelayServer(
                host=self.config.ws_host,
                port=self.config.ws_port,
            )

            self.connection_manager = VoiceConnectionManager(
                self.relay_server
            )

            logger.info(
                "Voice pipeline initialized successfully"
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to initialize voice pipeline: {e}",
                exc_info=True,
            )
            return False

    def start(self) -> bool:
        """Start the complete voice pipeline."""

        if self._running:
            logger.warning(
                "Pipeline already running"
            )
            return True

        # -------------------------------------------------------------
        # Start voice listener for wake-word detection
        # -------------------------------------------------------------
        if not self.voice_listener.start():
            logger.error(
                "Voice listener failed to start"
            )
            return False

        self._running = True

        # Store the running event loop when start() is invoked from
        # an async application context.
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

        # -------------------------------------------------------------
        # Start audio consumer thread.
        # -------------------------------------------------------------
        self._audio_loop_thread = threading.Thread(
            target=self._process_audio_loop,
            name="axiom-voice-audio-loop",
            daemon=True,
        )

        self._audio_loop_thread.start()

        # -------------------------------------------------------------
        # Start relay server.
        # -------------------------------------------------------------
        if self.relay_server:
            try:
                self.relay_server.start()
            except Exception as e:
                logger.error(
                    f"Relay server failed to start: {e}",
                    exc_info=True,
                )

                self._running = False
                self.voice_listener.stop()

                if self._audio_loop_thread:
                    self._audio_loop_thread.join(
                        timeout=2.0
                    )

                self._audio_loop_thread = None

                return False

        logger.info(
            "Voice pipeline started"
        )

        return True

    def stop(self) -> None:
        """Stop the complete voice pipeline cleanly."""

        logger.info(
            "[VOICE_PIPELINE_STOP] Stopping voice pipeline"
        )

        self._running = False

        # Prevent new state transitions into capture/processing.
        self._transition_state(
            VoiceState.LISTENING
        )

        # Stop voice listener.
        if self.voice_listener:
            self.voice_listener.stop()

        # Stop microphone, wake detector and VAD capture.
        if self.audio_processor:
            self.audio_processor.stop()

        # Stop relay.
        if self.relay_server:
            try:
                self.relay_server.stop()
            except Exception as e:
                logger.debug(
                    f"Relay server stop error: {e}"
                )

        # Wait briefly for the audio consumer thread.
        if (
            self._audio_loop_thread
            and self._audio_loop_thread.is_alive()
            and self._audio_loop_thread
            is not threading.current_thread()
        ):
            self._audio_loop_thread.join(
                timeout=2.0
            )

        self._audio_loop_thread = None

        logger.info(
            "[VOICE_PIPELINE_STOP] Voice pipeline stopped"
        )

    def _process_audio_loop(self) -> None:
        """Main audio consumer loop."""

        logger.info(
            "[AUDIO_LOOP_START] "
            "Audio processing loop started"
        )

        while self._running:
            try:
                # Only process audio chunks when in CAPTURING state (command capture)
                if self._state == VoiceState.CAPTURING:
                    try:
                        audio_chunk = (
                            self.audio_processor.audio_queue.get(
                                timeout=0.1
                            )
                        )
                    except Empty:
                        continue

                    if not self._running:
                        break

                    current_state = self._state
                    current_entity = self._current_entity

                    self.audio_processor.process_audio_chunk(
                        audio_chunk,
                        current_state,
                        current_entity,
                    )
                else:
                    # In other states, we don't process audio from the queue.
                    # Sleep briefly to avoid busy loop.
                    time.sleep(0.1)

            except Exception as e:
                logger.error(
                    f"[AUDIO_LOOP_ERROR] {e}",
                    exc_info=True,
                )

                time.sleep(0.1)

        logger.info(
            "[AUDIO_LOOP_END] "
            "Audio processing loop ended"
        )

    def _handle_wake_word_detected(
        self,
        entity: str,
        confidence: float,
        wake_word: str,
    ) -> None:
        """Handle a confirmed wake-word detection."""

        if not self._running:
            return

        # Only accept wake words while actually listening.
        if self._state != VoiceState.LISTENING:
            logger.debug(
                "[WAKE_HANDLE] Ignoring wake detection "
                f"while state={self._state.value}"
            )
            return

        logger.info(
            f"[WAKE_HANDLE] Entity: {entity}, "
            f"Word: '{wake_word}', "
            f"Confidence: {confidence:.3f}"
        )

        self._current_entity = entity

        self._emit_event(
            VoiceEvent(
                event_type="wake_detected",
                entity=entity,
                data={
                    "wake_word": wake_word,
                    "confidence": confidence,
                },
            )
        )

        self._transition_state(
            VoiceState.ACKNOWLEDGING
        )

        threading.Thread(
            target=self._play_fixed_acknowledgment,
            args=(entity,),
            name="axiom-voice-ack",
            daemon=True,
        ).start()

    def _play_fixed_acknowledgment(
        self,
        entity: str,
    ) -> None:
        """Synthesize and play the fixed wake acknowledgment."""

        acknowledgment_text = (
            "Hey, I'm here. How can I assist you?"
        )

        logger.info(
            f"[ACK_PLAY_START] "
            f"Playing fixed acknowledgment for {entity}"
        )

        self._emit_event(
            VoiceEvent(
                event_type="listening_started",
                entity=entity,
            )
        )

        try:
            if not self.tts_service:
                raise RuntimeError(
                    "TTS service is unavailable"
                )

            audio_data = self.tts_service.synthesize(
                acknowledgment_text,
                entity,
            )

            logger.info(
                "[ACK_SYNTHESIZE] "
                "Acknowledgment synthesized, "
                f"length={len(audio_data) if audio_data else 0}"
            )

            self._emit_event(
                VoiceEvent(
                    event_type="executive_speaking",
                    entity=entity,
                    data={
                        "spoken_text": acknowledgment_text,
                        "audio_data": audio_data,
                        "target_workstation": (
                            self.intent_router
                            .get_workstation_for_entity(
                                entity
                            )
                        ),
                    },
                )
            )

            # Approximate playback duration.
            word_count = len(
                acknowledgment_text.split()
            )

            estimated_duration = max(
                1.5,
                word_count / 2.5,
            )

            time.sleep(
                estimated_duration
            )

        except Exception as e:
            logger.error(
                f"[ACK_ERROR] "
                f"Failed to play acknowledgment: {e}",
                exc_info=True,
            )

        if not self._running:
            return

        logger.info(
            "[ACK_PLAY_END] "
            "Acknowledgment completed, "
            "transitioning to CAPTURING"
        )

        # Set voice listener to capturing state before transitioning to CAPTURING
        if self.voice_listener:
            self.voice_listener.set_capturing(True)

        self._transition_state(
            VoiceState.CAPTURING
        )

        if not self.audio_processor.start_capture(
            self._on_capture_complete
        ):
            logger.error(
                "[ACK_CAPTURE_START] "
                "Failed to start audio capture"
            )

            self._current_entity = None

            # Reset voice listener to listening state on error
            if self.voice_listener:
                self.voice_listener.set_capturing(False)

            self._transition_state(
                VoiceState.LISTENING
            )

            # Restart voice listener for wake-word detection
            if self.voice_listener:
                self.voice_listener.start()

    def _on_capture_complete(
        self,
        audio: np.ndarray,
    ) -> None:
        """Handle completed VAD capture."""

        if not self._running:
            return

        logger.info(
            f"[CAPTURE_COMPLETE] "
            f"Audio captured: "
            f"{len(audio) / self.audio_processor.sample_rate:.2f}s"
        )

        entity = self._current_entity

        self._emit_event(
            VoiceEvent(
                event_type="transcription_started",
                entity=entity or "unknown",
            )
        )

        self._transition_state(
            VoiceState.PROCESSING
        )

        threading.Thread(
            target=self._process_audio,
            args=(audio, entity),
            name="axiom-voice-processing",
            daemon=True,
        ).start()

    def _process_audio(
        self,
        audio: np.ndarray,
        entity: Optional[str],
    ) -> None:
        """Transcribe, route, execute and synthesize a command."""

        logger.info(
            f"[AUDIO_PROCESS_START] "
            f"Processing audio for entity: {entity}"
        )

        try:
            if not self.stt_engine:
                raise RuntimeError(
                    "STT engine is unavailable"
                )

            # ---------------------------------------------------------
            # STT
            # ---------------------------------------------------------
            logger.info(
                "[AUDIO_PROCESS] Starting transcription"
            )

            transcript, confidence = (
                self.stt_engine.transcribe(audio)
            )

            logger.info(
                f"[AUDIO_PROCESS] "
                f"Transcription: '{transcript}' "
                f"(confidence: {confidence:.3f})"
            )

            if not transcript.strip():
                logger.warning(
                    "[AUDIO_PROCESS] Empty transcription"
                )

                self._emit_event(
                    VoiceEvent(
                        event_type="transcription_complete",
                        entity=entity or "unknown",
                        data={
                            "text": "",
                            "confidence": confidence,
                            "empty": True,
                        },
                    )
                )

                self._emit_event(
                    VoiceEvent(
                        event_type="idle",
                        entity=entity or "unknown",
                    )
                )

                return

            # ---------------------------------------------------------
            # Transcription event
            # ---------------------------------------------------------
            self._emit_event(
                VoiceEvent(
                    event_type="transcription_complete",
                    entity=entity or "unknown",
                    data={
                        "text": transcript,
                        "confidence": confidence,
                    },
                )
            )

            # ---------------------------------------------------------
            # Intent routing
            # ---------------------------------------------------------
            logger.info(
                "[AUDIO_PROCESS] Routing command"
            )

            router_output = self.intent_router.route(
                transcript=transcript,
                wake_entity=entity or "axiom",
                confidence=confidence,
            )

            target_entity = (
                router_output.target_entity
            )

            delegated_by = (
                router_output.delegated_by
            )

            logger.info(
                f"[AUDIO_PROCESS] Routed to: "
                f"{target_entity}"
                + (
                    f" (delegated by {delegated_by})"
                    if delegated_by
                    else ""
                )
            )

            self._emit_event(
                VoiceEvent(
                    event_type="processing",
                    entity=target_entity,
                    data={
                        "transcript": transcript,
                        "delegated_by": delegated_by,
                        "target_workstation": (
                            router_output.target_workstation
                        ),
                    },
                )
            )

            # ---------------------------------------------------------
            # Conversation history
            # ---------------------------------------------------------
            history = (
                self._conversation_history.get(
                    target_entity,
                    [],
                )
            )

            logger.info(
                f"[AUDIO_PROCESS] "
                f"Conversation history for "
                f"{target_entity}: "
                f"{len(history)} exchanges"
            )

            # ---------------------------------------------------------
            # Runtime execution
            # ---------------------------------------------------------
            logger.info(
                "[AUDIO_PROCESS] "
                "Executing command via runtime"
            )

            response_text = self._execute_command(
                target_entity,
                transcript,
                history,
            )

            logger.info(
                f"[AUDIO_PROCESS] "
                f"Command execution result: "
                f"'{response_text[:100]}"
                f"{'...' if len(response_text) > 100 else ''}'"
            )

            # ---------------------------------------------------------
            # History update
            # ---------------------------------------------------------
            if target_entity not in self._conversation_history:
                self._conversation_history[
                    target_entity
                ] = []

            self._conversation_history[
                target_entity
            ].append(
                {
                    "role": "user",
                    "content": transcript,
                }
            )

            self._conversation_history[
                target_entity
            ].append(
                {
                    "role": "assistant",
                    "content": response_text,
                }
            )

            if len(
                self._conversation_history[target_entity]
            ) > 20:
                self._conversation_history[
                    target_entity
                ] = self._conversation_history[
                    target_entity
                ][-20:]

            # ---------------------------------------------------------
            # TTS
            # ---------------------------------------------------------
            logger.info(
                "[AUDIO_PROCESS] "
                "Synthesizing response"
            )

            self._emit_event(
                VoiceEvent(
                    event_type="synthesizing",
                    entity=target_entity,
                    data={
                        "text": response_text,
                    },
                )
            )

            if not self.tts_service:
                raise RuntimeError(
                    "TTS service is unavailable"
                )

            audio_data = self.tts_service.synthesize(
                response_text,
                target_entity,
            )

            logger.info(
                "[AUDIO_PROCESS] "
                f"TTS synthesis complete, "
                f"audio length: "
                f"{len(audio_data) if audio_data else 0}"
            )

            # ---------------------------------------------------------
            # Speaking event
            # ---------------------------------------------------------
            self._emit_event(
                VoiceEvent(
                    event_type="executive_speaking",
                    entity=target_entity,
                    data={
                        "spoken_text": response_text,
                        "audio_data": audio_data,
                        "target_workstation": (
                            router_output.target_workstation
                        ),
                    },
                )
            )

            # ---------------------------------------------------------
            # Display result
            # ---------------------------------------------------------
            self._emit_event(
                VoiceEvent(
                    event_type="display_result",
                    entity=target_entity,
                    data={
                        "workstation": (
                            router_output.target_workstation
                        ),
                        "transcript": transcript,
                        "response": response_text,
                    },
                )
            )

        except Exception as e:
            logger.error(
                f"[AUDIO_PROCESS_ERROR] {e}",
                exc_info=True,
            )

            self._emit_event(
                VoiceEvent(
                    event_type="error",
                    entity=entity or "unknown",
                    data={
                        "message": str(e),
                    },
                )
            )

        finally:
            logger.info(
                "[AUDIO_PROCESS_CLEANUP] "
                "Cleaning up and returning to listening"
            )

            self._current_entity = None

            self._emit_event(
                VoiceEvent(
                    event_type="idle",
                    entity=entity or "unknown",
                )
            )

            if self._running:
                self._transition_state(
                    VoiceState.LISTENING
                )
            else:
                self._transition_state(
                    VoiceState.LISTENING
                )

            # Set voice listener to listening state before restarting
            if self.voice_listener:
                self.voice_listener.set_capturing(False)

            # Restart voice listener for wake-word detection
            if self.voice_listener:
                self.voice_listener.start()

            logger.info(
                "[AUDIO_PROCESS_END] "
                "Audio processing completed"
            )

    def _execute_command(
        self,
        entity: str,
        transcript: str,
        history: List[Dict],
    ) -> str:
        """Execute a command through the runtime."""

        try:
            if self.runtime:
                return self._execute_via_runtime(
                    entity,
                    transcript,
                    history,
                )

            return self._get_default_response(
                entity,
                transcript,
            )

        except Exception as e:
            logger.error(
                f"Command execution failed: {e}",
                exc_info=True,
            )

            return (
                "I encountered an error processing "
                "your request: "
                f"{str(e)}"
            )

    def _execute_via_runtime(
        self,
        entity: str,
        transcript: str,
        history: List[Dict],
    ) -> str:
        """Execute the command through the existing executive runtime."""

        logger.info(
            "[EXECUTE_VIA_RUNTIME] ENTRY: "
            f"entity={entity}, "
            f"transcript='{transcript[:50]}"
            f"{'...' if len(transcript) > 50 else ''}'"
        )

        try:
            if (
                hasattr(self.runtime, "executive_board")
                and self.runtime.executive_board
            ):
                loop = (
                    self.runtime.executive_board
                    .get_loop(entity)
                )

                if loop:
                    logger.info(
                        "[EXECUTE_VIA_RUNTIME] "
                        f"Found executive loop for {entity}"
                    )

                    try:
                        loop_ref = self._loop

                        if loop_ref is None:
                            try:
                                loop_ref = (
                                    asyncio.get_running_loop()
                                )

                                logger.info(
                                    "[EXECUTE_VIA_RUNTIME] "
                                    "Got running event loop"
                                )

                            except RuntimeError:
                                logger.error(
                                    "[EXECUTE_VIA_RUNTIME] "
                                    "No event loop available "
                                    "for runtime execution"
                                )

                                return (
                                    self._get_default_response(
                                        entity,
                                        transcript,
                                    )
                                )

                        if not loop_ref.is_running():
                            logger.error(
                                "[EXECUTE_VIA_RUNTIME] "
                                "Stored event loop is not running"
                            )

                            return (
                                    self._get_default_response(
                                        entity,
                                        transcript,
                                    )
                                )

                        logger.info(
                            "[EXECUTE_VIA_RUNTIME] "
                            f"Triggering voice cycle for {entity}"
                        )

                        future = (
                            asyncio.run_coroutine_threadsafe(
                                loop.trigger_cycle(
                                    "voice",
                                    {
                                        "voice_command": transcript,
                                        "conversation_history": history,
                                    },
                                ),
                                loop_ref,
                            )
                        )

                        result = future.result(
                            timeout=30
                        )

                        logger.info(
                            "[EXECUTE_VIA_RUNTIME] "
                            f"Voice cycle completed "
                            f"with result: {result}"
                        )

                        from axiom.api.routes import (
                            _generate_executive_response
                        )

                        response = (
                            _generate_executive_response(
                                entity,
                                transcript,
                                result,
                            )
                        )

                        logger.info(
                            "[EXECUTE_VIA_RUNTIME] "
                            f"Generated response: "
                            f"'{response[:100]}"
                            f"{'...' if len(response) > 100 else ''}'"
                        )

                        return response

                    except Exception as e:
                        logger.error(
                            "[EXECUTE_VIA_RUNTIME_ERROR] "
                            f"Runtime execution failed: {e}",
                            exc_info=True,
                        )

                else:
                    logger.warning(
                        "[EXECUTE_VIA_RUNTIME] "
                        f"No executive loop found for entity: {entity}"
                    )

            else:
                logger.warning(
                    "[EXECUTE_VIA_RUNTIME] "
                    "Runtime or executive_board not available"
                )

            logger.info(
                "[EXECUTE_VIA_RUNTIME] "
                "Using fallback response"
            )

            return self._get_default_response(
                entity,
                transcript,
            )

        except Exception as e:
            logger.error(
                f"[EXECUTE_VIA_RUNTIME_ERROR] {e}",
                exc_info=True,
            )

            return self._get_default_response(
                entity,
                transcript,
            )

    def _get_default_response(
        self,
        entity: str,
        transcript: str,
    ) -> str:
        """Return a safe response when runtime is unavailable."""

        defaults = {
            "axiom": (
                "Command received. "
                "How can I assist further?"
            ),
            "jenson": (
                "Jenson acknowledged. "
                "Operations update queued."
            ),
            "valta_prime": (
                "Valta Prime received. "
                "Analyzing request."
            ),
            "yamako": (
                "Yamako here. "
                "Personal ops notified."
            ),
        }

        return defaults.get(
            entity,
            "Command received.",
        )

    def trigger_push_to_talk(
        self,
        entity: str = "axiom",
    ) -> bool:
        """Manually trigger command capture without a wake word."""

        if not self._running:
            logger.warning(
                "Pipeline is not running"
            )
            return False

        if self._state != VoiceState.LISTENING:
            logger.warning(
                "Not in listening state"
            )
            return False

        logger.info(
            f"Push-to-talk triggered for {entity}"
        )

        self._handle_wake_word_detected(
            entity,
            1.0,
            "push_to_talk",
        )

        return True

    def get_status(self) -> Dict[str, Any]:
        """Return complete pipeline status."""

        audio_diag = (
            self.audio_processor.get_diagnostics()
            if self.audio_processor
            else {}
        )

        wake_detector_running = False

        if (
            self.audio_processor
            and self.audio_processor.wake_detector
        ):
            wake_detector_running = bool(
                getattr(
                    self.audio_processor.wake_detector,
                    "_running",
                    False,
                )
            )

        stt_loaded = False

        if self.stt_engine:
            stt_loaded = bool(
                getattr(
                    self.stt_engine,
                    "_model",
                    None,
                ) is not None
            )

        relay_running = False

        if self.relay_server:
            relay_running = bool(
                getattr(
                    self.relay_server,
                    "_running",
                    False,
                )
            )

        return {
            "running": self._running,
            "state": self._state.value,
            "current_entity": self._current_entity,
            "wake_detector_running": wake_detector_running,
            "stt_loaded": stt_loaded,
            "tts_providers": (
                self.tts_service.get_available_providers()
                if self.tts_service
                else []
            ),
            "relay_connected": relay_running,
            **audio_diag,
        }

    def health_check(self) -> Dict[str, bool]:
        """Check health of all voice pipeline components."""

        wake_detector_healthy = bool(
            self.audio_processor
            and self.audio_processor.wake_detector
            and getattr(
                self.audio_processor.wake_detector,
                "_running",
                False,
            )
        )

        vad_healthy = bool(
            self.audio_processor
            and self.audio_processor.vad_processor
        )

        stt_healthy = False

        if self.stt_engine:
            stt_healthy = bool(
                getattr(
                    self.stt_engine,
                    "_model",
                    None,
                ) is not None
            )

        tts_healthy = bool(
            self.tts_service
            and hasattr(
                self.tts_service,
                "initialize",
            )
        )

        return {
            "wake_detector": wake_detector_healthy,
            "vad": vad_healthy,
            "stt": stt_healthy,
            "tts": tts_healthy,
        }


# ---------------------------------------------------------------------
# Global pipeline instance
# ---------------------------------------------------------------------

_pipeline_instance: Optional[
    VoicePipelineOrchestrator
] = None


def get_pipeline() -> VoicePipelineOrchestrator:
    """Get or create the global pipeline instance."""

    global _pipeline_instance

    if _pipeline_instance is None:
        _pipeline_instance = VoicePipelineOrchestrator(
            use_mock=True
        )

        print(
            "[STARTUP_VOICE] "
            "VoicePipelineOrchestrator created "
            f"id={id(_pipeline_instance)} "
            "via get_pipeline() (mock mode)"
        )

    return _pipeline_instance


def initialize_pipeline(
    runtime: Any = None,
    use_mock: bool = False,
) -> VoicePipelineOrchestrator:
    """Initialize and return the global pipeline instance."""

    global _pipeline_instance

    print(
        "[STARTUP_VOICE] "
        f"initialize_pipeline ENTER: "
        f"runtime={runtime}, "
        f"use_mock={use_mock}"
    )

    _pipeline_instance = VoicePipelineOrchestrator(
        runtime=runtime,
        use_mock=use_mock,
    )

    print(
        "[STARTUP_VOICE] "
        "initialize_pipeline: "
        f"VoicePipelineOrchestrator created "
        f"id={id(_pipeline_instance)}"
    )

    init_result = _pipeline_instance.initialize()

    print(
        "[STARTUP_VOICE] "
        "initialize_pipeline: "
        "VoicePipelineOrchestrator.initialize() "
        f"returned {init_result}"
    )

    return _pipeline_instance