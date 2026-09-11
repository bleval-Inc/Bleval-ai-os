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

import sounddevice as sd

from axiom.voice.config import voice_config, EXECUTIVE_WAKE_WORDS, VALID_EXECUTIVES
from axiom.voice.wakeword import (
    WakeWordDetector,
    MockWakeWordDetector,
    create_wake_word_detector,
)
from axiom.voice.wakeword.vad import (
    SileroVAD,
    WebRTCVAD,
    VADCaptureManager,
    MockVADCaptureManager,
    create_vad_capture_manager,
)
from axiom.voice.stt import (
    WhisperEngine,
    MockWhisperEngine,
    create_whisper_engine,
)
from axiom.voice.router import (
    IntentRouter,
    RouterOutput,
)
from axiom.voice.tts import (
    get_tts_service,
    TextToSpeechService,
)
from axiom.voice.relay.ws_server import VoiceRelayServer

logger = logging.getLogger("axiom.voice.pipeline_orchestrator")


class VoiceConnectionManager:
    """Wrapper around VoiceRelayServer to match WebSocketConnectionManager interface."""

    def __init__(self, relay_server: VoiceRelayServer):
        self.relay_server = relay_server

    async def connect(self, websocket) -> None:
        # Delegate to the relay server's internal client handling
        await self.relay_server._handle_client(websocket)

    async def disconnect(self, websocket) -> None:
        # The _handle_client method already removes the websocket from _clients when done
        pass

    def get_connection_count(self) -> int:
        return self.relay_server.client_count


class VoiceState(Enum):
    """Voice pipeline states."""
    LISTENING = "listening"      # Waiting for wake word
    ACKNOWLEDGING = "acknowledging"  # Playing fixed acknowledgment
    CAPTURING = "capturing"      # Capturing user command after wake word
    PROCESSING = "processing"    # Processing captured command (STT -> Route -> Execute -> TTS)
    SPEAKING = "speaking"        # Speaking TTS response


@dataclass
class VoiceEvent:
    """Event in the voice pipeline."""
    event_type: str
    entity: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    data: Dict[str, Any] = field(default_factory=dict)


class AudioProcessor:
    """Processes audio from a single microphone stream for different purposes based on state."""

    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1280):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = Queue(maxsize=20)  # Buffer for audio chunks
        self._stream: Optional[sd.InputStream] = None
        self._running = False

        # Components
        self.wake_detector: Optional[WakeWordDetector] = None
        self.vad_processor: Optional[Any] = None  # Will be SileroVAD or WebRTCVAD

        # State for VAD processing
        self._audio_buffer: List[np.ndarray] = []  # Buffered audio for capture
        self._preroll_buffer: List[np.ndarray] = []  # Audio before speech detection
        self._preroll_sample_count = 0
        self._preroll_samples = int(sample_rate * 1.0)  # 1 second preroll
        self._silence_start: Optional[float] = None
        self._speech_detected = False
        self._capture_start_time: Optional[float] = None
        self._max_duration: float = 10.0
        self._silence_timeout: float = 1.5
        self._min_duration: float = 1.0
        self._on_capture_complete: Optional[Callable[[np.ndarray], None]] = None

        # Diagnostic counters
        self._callback_count = 0
        self._frames_received = 0
        self._frames_dropped = 0
        self._wake_predictions = 0
        self._wake_detections = 0

        # Last wake word detection (thread-safe)
        self._last_wake_entity: Optional[str] = None
        self._last_wake_word: Optional[str] = None
        self._last_wake_confidence: float = 0.0
        self._last_wake_time: float = 0.0
        self._wake_result_lock = threading.Lock()

    def initialize(self, runtime: Any = None) -> bool:
        """Initialize audio processor components."""
        try:
            # Initialize wake word detector
            wake_detector = create_wake_word_detector(
                use_mock=False,
                on_wake=None  # We'll handle wake detection ourselves via audio callback
            )
            if not wake_detector.load_models():
                logger.warning("Wake word models not loaded")
            self.wake_detector = wake_detector
            # Start the wake word detector's internal thread
            if not self.wake_detector.start():
                logger.warning("Failed to start wake word detector")

            # Initialize VAD (using silero as default)
            self.vad_processor = SileroVAD(
                sample_rate=self.sample_rate,
                threshold=0.5,
                min_silence_duration_ms=int(self._silence_timeout * 1000),
            )
            if not self.vad_processor.load():
                logger.warning("VAD model not loaded")

            # Start microphone stream
            self._start_microphone_stream()

            logger.info("Audio processor initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize audio processor: {e}")
            return False

    def _start_microphone_stream(self) -> None:
        """Start the single, continuous microphone input stream."""
        def audio_callback(indata, frames, time_info, status):
            """Microphone callback - puts audio data into queue for processing."""
            if status:
                logger.debug(f"Audio callback status: {status}")

            if not self._running:
                return

            # Diagnostic instrumentation
            self._callback_count += 1
            self._frames_received += len(indata)

            # Calculate audio levels (for debugging)
            if self._callback_count % 50 == 0 or self._callback_count == 1:
                audio_float = indata[:, 0]
                peak = np.max(np.abs(audio_float)) if len(audio_float) > 0 else 0.0
                rms = np.sqrt(np.mean(audio_float**2)) if len(audio_float) > 0 else 0.0
                if self._callback_count == 1:
                    logger.info(f"[AUDIO_START] Stream started: peak={peak:.6f}, rms={rms:.6f}")
                elif self._callback_count % 50 == 0:
                    logger.info(f"[AUDIO_UPDATE] callback={self._callback_count}, peak={peak:.6f}, rms={rms:.6f}")

            # Put audio data in queue for processing
            try:
                self.audio_queue.put_nowait(indata[:, 0].copy())  # Mono channel
            except Exception:
                self._frames_dropped += len(indata)
                # Queue full - drop oldest frame to make space for newest
                try:
                    self.audio_queue.get_nowait()
                    self.audio_queue.put_nowait(indata[:, 0].copy())
                except Exception:
                    pass  # Still couldn't queue it

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=self.chunk_size,
                device=voice_config.audio_device,
                callback=audio_callback,
            )
            self._stream.start()
            logger.info(f"[MIC_STREAM_START] Microphone stream started: active={self._stream.active}")
        except Exception as e:
            logger.error(f"Failed to start microphone stream: {e}")
            raise

    def process_audio_chunk(self, audio_chunk: np.ndarray, state: VoiceState, current_entity: Optional[str]) -> None:
        """Process a single audio chunk based on current state."""
        if not self._running:
            return

        if state == VoiceState.LISTENING:
            self._process_for_wake_word(audio_chunk)
        elif state == VoiceState.CAPTURING:
            self._process_for_capture(audio_chunk, current_entity)
        # In ACKNOWLEDGING, PROCESSING, SPEAKING states, we still buffer audio but don't process for wake/command
        # This ensures we don't lose audio during state transitions

    def _process_for_wake_word(self, audio_chunk: np.ndarray) -> None:
        """Process audio chunk for wake word detection."""
        self._wake_predictions += 1

        if not self.wake_detector or not self.wake_detector._models:
            return

        try:
            # Convert to int16 for openWakeWord
            audio_int16 = (audio_chunk.flatten() * 32767).astype(np.int16)

            # Get scores from all models
            scores: Dict[str, float] = {}
            for exec_id, model in self.wake_detector._models.items():
                try:
                    prediction = model.predict(audio_int16)
                    executive_score = 0.0
                    if isinstance(prediction, dict) and prediction:
                        wake_word_phrases = EXECUTIVE_WAKE_WORDS.get(exec_id, [exec_id])
                        phrase_scores = []
                        for phrase in wake_word_phrases:
                            if phrase in prediction:
                                phrase_scores.append(float(prediction[phrase]))

                        if phrase_scores:
                            executive_score = max(phrase_scores)
                        elif prediction:
                            executive_score = max(float(v) for v in prediction.values())

                    scores[exec_id] = executive_score
                except Exception as e:
                    logger.debug(f"Wake word model error for {exec_id}: {e}")
                    scores[exec_id] = 0.0

            if not scores:
                return

            # Store latest scores for debug endpoint
            self.wake_detector._latest_scores = dict(scores)

            # Rank executives by confidence
            ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
            winner, winner_score = ranked[0]
            second_score = ranked[1][1] if len(ranked) > 1 else 0.0
            margin = winner_score - second_score

            # Check detection criteria
            confidence_threshold = voice_config.wake_word.confidence_threshold
            winner_margin = 0.05

            if (winner_score >= confidence_threshold and
                margin >= winner_margin):

                self._wake_detections += 1
                wake_word = self.wake_detector._get_triggered_wake_word(winner, winner)

                logger.info(f"[WAKE_DETECTED] Entity: {winner}, Wake word: '{wake_word}', "
                           f"Score: {winner_score:.3f}, Margin: {margin:.3f}")

                # Store wake result thread-safely
                with self._wake_result_lock:
                    self._last_wake_entity = winner
                    self._last_wake_word = wake_word
                    self._last_wake_confidence = winner_score
                    self._last_wake_time = time.time()

        except Exception as e:
            logger.debug(f"Wake word processing error: {e}")

    def _process_for_capture(self, audio_chunk: np.ndarray, current_entity: Optional[str]) -> None:
        """Process audio chunk for voice activity detection during capture."""
        if not self.vad_processor or not self._on_capture_complete:
            return

        # Add to audio buffer for eventual capture
        self._audio_buffer.append(audio_chunk.copy())

        # Manage preroll buffer (audio before speech detection)
        if not self._speech_detected:
            self._preroll_buffer.append(audio_chunk.copy())
            self._preroll_sample_count += len(audio_chunk)

            # Keep preroll buffer to ~1 second
            while self._preroll_sample_count > self._preroll_samples:
                removed = self._preroll_buffer.pop(0)
                self._preroll_sample_count -= len(removed)

        # VAD processing
        try:
            is_speech = self.vad_processor.is_speech(audio_chunk)

            current_time = time.time()

            if is_speech and not self._speech_detected:
                # Speech started - include preroll
                logger.debug("[VAD_SPEECH_START] Speech detected")
                if self._preroll_buffer:
                    self._audio_buffer.extend(self._preroll_buffer)
                self._preroll_buffer = []
                self._preroll_sample_count = 0
                self._speech_detected = True
                self._silence_start = None

            elif self._speech_detected and is_speech:
                # Ongoing speech - reset silence timer
                self._silence_start = None

            elif self._speech_detected and not is_speech:
                # Potential end of speech
                if self._silence_start is None:
                    self._silence_start = current_time
                    logger.debug("[VAD_SILENCE_START] Silence started")
                elif (current_time - self._silence_start) >= self._silence_timeout:
                    # Silence timeout reached - end capture
                    logger.info("[VAD_CAPTURE_COMPLETE] Silence timeout reached")
                    self._finalize_capture(current_entity)

        except Exception as e:
            logger.debug(f"VAD processing error: {e}")

        # Check max duration
        if self._capture_start_time:
            capture_duration = time.time() - self._capture_start_time
            if capture_duration >= self._max_duration:
                logger.info("[VAD_CAPTURE_COMPLETE] Max duration reached")
                self._finalize_capture(current_entity)

    def _finalize_capture(self, current_entity: Optional[str]) -> None:
        """Finalize capture and return audio data."""
        if not self._audio_buffer:
            logger.warning("[VAD_CAPTURE] No audio captured")
            return

        # Combine preroll + captured audio
        if self._preroll_buffer:
            self._audio_buffer.extend(self._preroll_buffer)

        audio = np.concatenate(self._audio_buffer)
        duration = len(audio) / self.sample_rate
        logger.info(f"[VAD_CAPTURE] Capture complete: {duration:.2f}s ({len(audio)} samples)")

        # Reset capture state
        self._audio_buffer = []
        self._preroll_buffer = []
        self._preroll_sample_count = 0
        self._silence_start = None
        self._speech_detected = False
        self._capture_start_time = None

        # Call completion callback
        if self._on_capture_complete:
            try:
                self._on_capture_complete(audio)
            except Exception as e:
                logger.error(f"Capture completion callback error: {e}")

    def start_capture(self, on_capture_complete: Callable[[np.ndarray], None]) -> bool:
        """Start capturing audio for command after wake word."""
        self._on_capture_complete = on_capture_complete
        self._capture_start_time = time.time()
        self._speech_detected = False
        self._silence_start = None
        logger.info("[VAD_CAPTURE_START] Capture started")
        return True

    def stop(self) -> None:
        """Stop the audio processor and cleanup."""
        self._running = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        logger.info("[AUDIO_PROCESSOR_STOP] Audio processor stopped")

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information."""
        return {
            "callback_count": self._callback_count,
            "frames_received": self._frames_received,
            "frames_dropped": self._frames_dropped,
            "wake_predictions": self._wake_predictions,
            "wake_detections": self._wake_detections,
            "stream_active": self._stream.active if self._stream else False,
            "stream_closed": getattr(self._stream, 'closed', True) if self._stream else True,
        }

    def _get_wake_detection_result(self) -> Optional[Dict[str, Any]]:
        """Get the last wake word detection result."""
        with self._wake_result_lock:
            if self._last_wake_entity is not None:
                return {
                    "entity": self._last_wake_entity,
                    "wake_word": self._last_wake_word,
                    "confidence": self._last_wake_confidence,
                    "timestamp": self._last_wake_time
                }
        return None

    def _clear_wake_detection_result(self) -> None:
        """Clear the last wake word detection result."""
        with self._wake_result_lock:
            self._last_wake_entity = None
            self._last_wake_word = None
            self._last_wake_confidence = 0.0
            self._last_wake_time = 0.0


class VoicePipelineOrchestrator:
    """
    Main orchestrator for the voice pipeline with explicit state machine.

    States:
    LISTENING -> wake word -> ACKNOWLEDGING -> fixed ack -> CAPTURING ->
    VAD detects end -> PROCESSING -> STT->Route->Execute->TTS -> SPEAKING ->
    TTS done -> LISTENING
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

        # State management
        self._state = VoiceState.LISTENING
        self._state_lock = threading.Lock()
        self._running = False
        self._current_entity: Optional[str] = None

        # Components
        self.audio_processor = AudioProcessor()
        self.stt_engine: Optional[WhisperEngine] = None
        self.intent_router = IntentRouter()
        self.tts_service: Optional[TextToSpeechService] = None
        self.relay_server: Optional[VoiceRelayServer] = None
        self.connection_manager = None  # For voice_pipeline_routes compatibility

        # Conversation history
        self._conversation_history: Dict[str, List[Dict[str, str]]] = {}

        # Event loop for thread-safe coroutine scheduling
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        # Audio processing loop thread
        self._audio_loop_thread: Optional[threading.Thread] = None

        # Event callbacks
        self._event_callbacks: List[Callable[[VoiceEvent], None]] = []

    def _emit_event(self, event: VoiceEvent) -> None:
        """Emit event to all callbacks and relay server."""
        for callback in self._event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

        # Also send to relay server if available
        if self.relay_server and self._loop:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.relay_server.broadcast_event(event),
                    self._loop
                )
            except Exception as e:
                logger.debug(f"Relay broadcast error: {e}")

    def _transition_state(self, new_state: VoiceState) -> None:
        """Safely transition to a new state."""
        with self._state_lock:
            old_state = self._state
            self._state = new_state
            logger.info(f"[VOICE_STATE_TRANSITION] {old_state.value} -> {new_state.value}")

    def initialize(self) -> bool:
        """Initialize all pipeline components."""
        logger.info("Initializing voice pipeline...")

        try:
            # Initialize TTS service
            self.tts_service = get_tts_service()
            if not self.tts_service.initialize():
                logger.error("TTS service initialization failed")
                return False

            # Initialize STT engine
            self.stt_engine = create_whisper_engine(use_mock=self.use_mock)
            if not self.stt_engine.load():
                logger.error("STT engine initialization failed")
                return False

            # Initialize audio processor (handles microphone stream and wake/VAD processing)
            if not self.audio_processor.initialize(runtime=self.runtime):
                logger.error("Audio processor initialization failed")
                return False

            # Initialize relay server
            relay_server = VoiceRelayServer(
                host=self.config.ws_host,
                port=self.config.ws_port,
            )
            self.relay_server = relay_server
            self.connection_manager = VoiceConnectionManager(relay_server)  # For compatibility

            logger.info("Voice pipeline initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize voice pipeline: {e}", exc_info=True)
            return False

    def start(self) -> bool:
        """Start the voice pipeline."""
        if self._running:
            logger.warning("Pipeline already running")
            return True

        if not self.initialize():
            return False

        self._running = True
        # Store the running event loop for thread-safe coroutine scheduling
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

        # Start audio processing loop
        self._audio_loop_thread = threading.Thread(
            target=self._process_audio_loop,
            daemon=True
        )
        self._audio_loop_thread.start()

        # Start relay server
        if self.relay_server:
            self.relay_server.start()

        logger.info("Voice pipeline started")
        return True

    def stop(self) -> None:
        """Stop the voice pipeline."""
        self._running = False
        self._transition_state(VoiceState.LISTENING)

        if self.audio_processor:
            self.audio_processor.stop()

        if self.relay_server:
            self.relay_server.stop()

        logger.info("Voice pipeline stopped")

    def _process_audio_loop(self) -> None:
        """Main audio processing loop - runs in background thread."""
        logger.info("[AUDIO_LOOP_START] Audio processing loop started")

        while self._running:
            try:
                # Get audio chunk from queue (with timeout to allow checking _running)
                try:
                    audio_chunk = self.audio_processor.audio_queue.get(timeout=0.1)
                except Empty:
                    continue

                # Process audio based on current state
                current_state = self._state
                current_entity = self._current_entity

                self.audio_processor.process_audio_chunk(audio_chunk, current_state, current_entity)

                # Check for wake word detection when in LISTENING state
                if current_state == VoiceState.LISTENING:
                    wake_result = self.audio_processor._get_wake_detection_result()
                    if wake_result:
                        self._handle_wake_word_detected(
                            wake_result["entity"],
                            wake_result["confidence"],
                            wake_result["wake_word"]
                        )
                        self.audio_processor._clear_wake_detection_result()

            except Exception as e:
                logger.error(f"[AUDIO_LOOP_ERROR] {e}", exc_info=True)
                time.sleep(0.1)

        logger.info("[AUDIO_LOOP_END] Audio processing loop ended")

    def _handle_wake_word_detected(self, entity: str, confidence: float, wake_word: str) -> None:
        """Handle wake word detection - transition to acknowledgment state."""
        logger.info(f"[WAKE_HANDLE] Entity: {entity}, Word: '{wake_word}', Confidence: {confidence:.3f}")

        # Store current entity
        self._current_entity = entity

        # Emit wake detected event
        self._emit_event(VoiceEvent(
            event_type="wake_detected",
            entity=entity,
            data={
                "wake_word": wake_word,
                "confidence": confidence,
            }
        ))

        # Transition to acknowledgment state
        self._transition_state(VoiceState.ACKNOWLEDGING)

        # Play fixed acknowledgment in background thread
        threading.Thread(
            target=self._play_fixed_acknowledgment,
            args=(entity,),
            daemon=True
        ).start()

    def _play_fixed_acknowledgment(self, entity: str) -> None:
        """Play the fixed wake acknowledgment."""
        acknowledgment_text = "Hey, I'm here. How can I assist you?"
        logger.info(f"[ACK_PLAY_START] Playing fixed acknowledgment for {entity}")

        # Emit listening started event
        self._emit_event(VoiceEvent(
            event_type="listening_started",
            entity=entity,
        ))

        # Synthesize and play acknowledgment
        try:
            audio_data = self.tts_service.synthesize(acknowledgment_text, entity)
            logger.info(f"[ACK_SYNTHESIZE] Acknowledgment synthesized, length: {len(audio_data) if audio_data else 0}")

            # Emit executive speaking event with audio
            self._emit_event(VoiceEvent(
                event_type="executive_speaking",
                entity=entity,
                data={
                    "spoken_text": acknowledgment_text,
                    "audio_data": audio_data,
                    "target_workstation": self.intent_router.get_workstation_for_entity(entity),
                },
            ))

            # Wait for audio to play (approximate duration based on text length and speech rate)
            # Rough estimate: 150 wpm = 2.5 words per second
            word_count = len(acknowledgment_text.split())
            estimated_duration = max(1.5, word_count / 2.5)  # At least 1.5 seconds
            time.sleep(estimated_duration)

        except Exception as e:
            logger.error(f"[ACK_ERROR] Failed to play acknowledgment: {e}")

        # After acknowledgment completes, transition to capturing state
        logger.info("[ACK_PLAY_END] Acknowledgment completed, transitioning to CAPTURING")
        self._transition_state(VoiceState.CAPTURING)

        # Start audio capture for the command
        if not self.audio_processor.start_capture(self._on_capture_complete):
            logger.error("[ACK_CAPTURE_START] Failed to start audio capture")
            # Return to listening if capture fails to start
            self._transition_state(VoiceState.LISTENING)
            self._current_entity = None

    def _on_capture_complete(self, audio: np.ndarray) -> None:
        """Callback when VAD capture completes - transition to processing."""
        logger.info(f"[CAPTURE_COMPLETE] Audio captured: {len(audio)/self.audio_processor.sample_rate:.2f}s")

        # Emit transcription started event
        self._emit_event(VoiceEvent(
            event_type="transcription_started",
            entity=self._current_entity or "unknown",
        ))

        # Transition to processing state
        self._transition_state(VoiceState.PROCESSING)

        # Process audio in background thread
        threading.Thread(
            target=self._process_audio,
            args=(audio, self._current_entity),
            daemon=True
        ).start()

    def _process_audio(self, audio: np.ndarray, entity: Optional[str]) -> None:
        """Process captured audio: transcribe -> route -> execute -> respond."""
        logger.info(f"[AUDIO_PROCESS_START] Processing audio for entity: {entity}")

        try:
            # Transcribe
            logger.info("[AUDIO_PROCESS] Starting transcription")
            transcript, confidence = self.stt_engine.transcribe(audio)
            logger.info(f"[AUDIO_PROCESS] Transcription: '{transcript}' (confidence: {confidence:.3f})")

            if not transcript.strip():
                logger.warning("[AUDIO_PROCESS] Empty transcription")
                self._emit_event(VoiceEvent(
                    event_type="transcription_complete",
                    entity=entity or "unknown",
                    data={"text": "", "confidence": confidence, "empty": True},
                ))
                # Return to idle state
                self._emit_event(VoiceEvent(
                    event_type="idle",
                    entity=entity or "unknown",
                ))
                self._transition_state(VoiceState.LISTENING)
                self._current_entity = None
                return

            logger.info(f"[AUDIO_PROCESS] Transcription for {entity}: '{transcript}' (confidence: {confidence:.3f})")

            # Emit transcription complete
            self._emit_event(VoiceEvent(
                event_type="transcription_complete",
                entity=entity or "unknown",
                data={
                    "text": transcript,
                    "confidence": confidence,
                },
            ))

            # Route command
            logger.info("[AUDIO_PROCESS] Routing command")
            router_output = self.intent_router.route(
                transcript=transcript,
                wake_entity=entity or "axiom",  # Default to axiom if None
                confidence=confidence,
            )

            target_entity = router_output.target_entity
            delegated_by = router_output.delegated_by

            logger.info(f"[AUDIO_PROCESS] Routed to: {target_entity}" +
                       (f" (delegated by {delegated_by})" if delegated_by else ""))

            # Emit processing event
            self._emit_event(VoiceEvent(
                event_type="processing",
                entity=target_entity,
                data={
                    "transcript": transcript,
                    "delegated_by": delegated_by,
                    "target_workstation": router_output.target_workstation,
                },
            ))

            # Get conversation history for context
            history = self._conversation_history.get(target_entity, [])
            logger.info(f"[AUDIO_PROCESS] Conversation history for {target_entity}: {len(history)} exchanges")

            # Process command via backend API
            logger.info("[AUDIO_PROCESS] Executing command via runtime")
            response_text = self._execute_command(target_entity, transcript, history)
            logger.info(f"[AUDIO_PROCESS] Command execution result: '{response_text[:100]}{'...' if len(response_text) > 100 else ''}'")

            # Update conversation history
            if target_entity not in self._conversation_history:
                self._conversation_history[target_entity] = []
            self._conversation_history[target_entity].append({
                "role": "user",
                "content": transcript,
            })
            self._conversation_history[target_entity].append({
                "role": "assistant",
                "content": response_text,
            })
            # Keep last 10 exchanges
            if len(self._conversation_history[target_entity]) > 20:
                self._conversation_history[target_entity] = self._conversation_history[target_entity][-20:]

            # Synthesize response
            logger.info("[AUDIO_PROCESS] Synthesizing response")
            self._emit_event(VoiceEvent(
                event_type="synthesizing",
                entity=target_entity,
                data={"text": response_text},
            ))

            audio_data = self.tts_service.synthesize(response_text, target_entity)
            logger.info(f"[AUDIO_PROCESS] TTS synthesis complete, audio length: {len(audio_data) if audio_data else 0}")

            # Emit executive speaking event with audio
            self._emit_event(VoiceEvent(
                event_type="executive_speaking",
                entity=target_entity,
                data={
                    "spoken_text": response_text,
                    "audio_data": audio_data,
                    "target_workstation": router_output.target_workstation,
                },
            ))

            # Emit display result event
            self._emit_event(VoiceEvent(
                event_type="display_result",
                entity=target_entity,
                data={
                    "workstation": router_output.target_workstation,
                    "transcript": transcript,
                    "response": response_text,
                },
            ))

        except Exception as e:
            logger.error(f"[AUDIO_PROCESS_ERROR] {e}", exc_info=True)
            self._emit_event(VoiceEvent(
                event_type="error",
                entity=entity or "unknown",
                data={"message": str(e)},
            ))
        finally:
            logger.info("[AUDIO_PROCESS_CLEANUP] Cleaning up and returning to listening")
            self._current_entity = None

            # Emit idle event
            self._emit_event(VoiceEvent(
                event_type="idle",
                entity=entity or "unknown",
            ))

            # Return to listening state
            self._transition_state(VoiceState.LISTENING)

            logger.info("[AUDIO_PROCESS_END] Audio processing completed, returning to LISTENING")

    def _execute_command(self, entity: str, transcript: str, history: List[Dict]) -> str:
        """Execute command via backend API/runtime."""
        try:
            # Use the existing voice command API endpoint logic
            if self.runtime:
                # Direct runtime access
                return self._execute_via_runtime(entity, transcript, history)
            else:
                # Fallback: return a default response
                return self._get_default_response(entity, transcript)
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return f"I encountered an error processing your request: {str(e)}"

    def _execute_via_runtime(self, entity: str, transcript: str, history: List[Dict]) -> str:
        """Execute command via the existing runtime."""
        logger.info(f"[EXECUTE_VIA_RUNTIME] ENTRY: entity={entity}, transcript='{transcript[:50]}{'...' if len(transcript) > 50 else ''}'")

        try:
            # This would call into the existing executive loop trigger_cycle method
            if hasattr(self.runtime, 'executive_board') and self.runtime.executive_board:
                loop = self.runtime.executive_board.get_loop(entity)
                if loop:
                    logger.info(f"[EXECUTE_VIA_RUNTIME] Found executive loop for {entity}")
                    try:
                        # Trigger a voice cycle
                        logger.info(f"[EXECUTE_VIA_RUNTIME] Triggering voice cycle for {entity}")

                        # Use the stored event loop if available, otherwise try to get the running loop
                        loop_ref = self._loop
                        if loop_ref is None:
                            try:
                                loop_ref = asyncio.get_running_loop()
                                logger.info("[EXECUTE_VIA_RUNTIME] Got running event loop")
                            except RuntimeError:
                                logger.error("[EXECUTE_VIA_RUNTIME] No event loop available for runtime execution")
                                return self._get_default_response(entity, transcript)

                        logger.info(f"[EXECUTE_VIA_RUNTIME] Triggering voice cycle for {entity}")
                        future = asyncio.run_coroutine_threadsafe(
                            loop.trigger_cycle("voice", {
                                "voice_command": transcript,
                                "conversation_history": history,
                            }),
                            loop_ref
                        )
                        result = future.result(timeout=30)
                        logger.info(f"[EXECUTE_VIA_RUNTIME] Voice cycle completed with result: {result}")

                        # Generate response from result
                        from axiom.api.routes import _generate_executive_response
                        response = _generate_executive_response(entity, transcript, result)
                        logger.info(f"[EXECUTE_VIA_RUNTIME] Generated response: '{response[:100]}{'...' if len(response) > 100 else ''}'")
                        return response
                    except Exception as e:
                        logger.error(f"[EXECUTE_VIA_RUNTIME_ERROR] Runtime execution failed: {e}", exc_info=True)
                else:
                    logger.warning(f"[EXECUTE_VIA_RUNTIME] No executive loop found for entity: {entity}")
            else:
                logger.warning("[EXECUTE_VIA_RUNTIME] Runtime or executive_board not available")

            # Fallback
            logger.info("[EXECUTE_VIA_RUNTIME] Using fallback response")
            return self._get_default_response(entity, transcript)
        except Exception as e:
            logger.error(f"[EXECUTE_VIA_RUNTIME_ERROR] {e}", exc_info=True)
            return self._get_default_response(entity, transcript)

    def _get_default_response(self, entity: str, transcript: str) -> str:
        """Get a default response when runtime is not available."""
        defaults = {
            "axiom": "Command received. How can I assist further?",
            "jenson": "Jenson acknowledged. Operations update queued.",
            "valta_prime": "Valta Prime received. Analyzing request.",
            "yamako": "Yamako here. Personal ops notified.",
        }
        return defaults.get(entity, "Command received.")

    def trigger_push_to_talk(self, entity: str = "axiom") -> bool:
        """Manually trigger push-to-talk for an executive (bypasses wake word)."""
        if self._state != VoiceState.LISTENING:
            logger.warning("Not in listening state")
            return False

        logger.info(f"Push-to-talk triggered for {entity}")
        self._handle_wake_word_detected(entity, 1.0, "push_to_talk")
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status."""
        audio_diag = self.audio_processor.get_diagnostics() if self.audio_processor else {}
        return {
            "running": self._running,
            "state": self._state.value,
            "current_entity": self._current_entity,
            "wake_detector_running": self.audio_processor.wake_detector is not None and self.audio_processor.wake_detector._running if self.audio_processor else False,
            "stt_loaded": self.stt_engine._model is not None if self.stt_engine else False,
            "tts_providers": self.tts_service.get_available_providers() if self.tts_service else [],
            "relay_connected": self.relay_server._running if self.relay_server else False,
            **audio_diag
        }

    # Interface matching for voice_pipeline_routes compatibility
    def health_check(self) -> dict[str, bool]:
        """Check health of all pipeline components - compatible with voice_pipeline_routes."""
        return {
            "wake_detector": bool(self.audio_processor.wake_detector and self.audio_processor.wake_detector._running),
            "vad": bool(self.audio_processor.vad_processor is not None),
            "stt": bool(self.stt_engine and self.stt_engine._model is not None),
            "tts": bool(self.tts_service and hasattr(self.tts_service, 'initialize')),
        }


# Global pipeline instance
_pipeline_instance: Optional[VoicePipelineOrchestrator] = None


def get_pipeline() -> VoicePipelineOrchestrator:
    """Get or create the global pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = VoicePipelineOrchestrator(use_mock=True)
        print(f"[STARTUP_VOICE] VoicePipelineOrchestrator created id={id(_pipeline_instance)} via get_pipeline() (mock mode)")
    return _pipeline_instance


def initialize_pipeline(runtime: Any = None, use_mock: bool = False) -> VoicePipelineOrchestrator:
    """Initialize and return the global pipeline instance."""
    global _pipeline_instance
    print(f"[STARTUP_VOICE] initialize_pipeline ENTER: runtime={runtime}, use_mock={use_mock}")
    _pipeline_instance = VoicePipelineOrchestrator(runtime=runtime, use_mock=use_mock)
    print(f"[STARTUP_VOICE] initialize_pipeline: VoicePipelineOrchestrator created id={id(_pipeline_instance)}")
    init_result = _pipeline_instance.initialize()
    print(f"[STARTUP_VOICE] initialize_pipeline: VoicePipelineOrchestrator.initialize() returned {init_result}")
    return _pipeline_instance