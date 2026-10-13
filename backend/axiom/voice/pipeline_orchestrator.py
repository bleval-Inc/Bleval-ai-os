"""
Pipeline orchestrator - ties wake -> stt -> router -> engine -> tts -> relay together.

Flow:
    [Mic] -> [Wake Word Detection] -> [VAD Capture] -> [STT] -> [Intent Router] ->
    [Intelligence Engine] -> [TTS] -> [WebSocket Relay] -> [Frontend]
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from .config import voice_config
from .tts.service import tts_service
from .models import (
    AcknowledgingEvent,
    CapturingEvent,
    DisplayResultEvent,
    ErrorEvent,
    ExecutiveSpeakingEvent,
    IdleEvent,
    IntelligenceEngineOutput,
    ListeningStartedEvent,
    ProcessingEvent,
    TranscriptionComplete,
    TranscriptionCompleteEvent,
    WakeWordDetection,
    WakeWordEvent,
)
from .relay.ws_server import PipelineEventEmitter, WebSocketConnectionManager
from .router.intent_router import IntentRouter
from .stt.whisper_engine import WhisperEngine
from .tts.voice_profiles import get_voice_profile
from .wakeword.detector import WakeWordDetector
from .wakeword.vad import VoiceActivityDetector


logger = logging.getLogger(__name__)


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
        connection_manager: WebSocketConnectionManager = None,
        runtime: Any = None,
        use_mock: bool = False,
    ):
        """
        Initialize the voice pipeline orchestrator.

        Args:
            connection_manager: WebSocketConnectionManager for relay. If None, creates new.
            runtime: AxiomRuntime instance for intelligence engine integration.
            use_mock: Whether to use mock components for testing.
        """
        self.connection_manager = connection_manager or WebSocketConnectionManager()
        self.emitter = PipelineEventEmitter(self.connection_manager)
        self.runtime = runtime
        self.use_mock = use_mock

        # State
        self._state = VoiceState.LISTENING
        self._state_lock = asyncio.Lock()
        self._running = False
        self._current_entity: Optional[str] = None

        # Initialize pipeline components
        logger.info("Initializing voice pipeline components...")
        self.wake_detector = WakeWordDetector()
        self.vad = VoiceActivityDetector()
        self.stt = WhisperEngine()
        self.router = IntentRouter()
        # TTS service will be initialized on first use
        self._tts_service = None

        logger.info("Voice pipeline initialized")

    async def initialize(self) -> bool:
        """Initialize all voice pipeline components."""
        if self._running:
            logger.warning("Voice pipeline is already running")
            return True

        try:
            # Initialize TTS service
            if self._tts_service is None:
                self._tts_service = tts_service
                if self._tts_service is None:
                    from .tts.service import get_tts_service
                    self._tts_service = get_tts_service()

            if self._tts_service is not None and not self._tts_service._initialized:
                await self._tts_service.initialize()

            logger.info("Voice pipeline initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize voice pipeline: {e}", exc_info=True)
            return False

    async def start(self) -> bool:
        """Start the complete voice pipeline."""
        if self._running:
            logger.warning("Pipeline is already running")
            return True

        # Initialize if not already done
        if not await self.initialize():
            logger.error("Failed to initialize voice pipeline")
            return False

        self._running = True
        logger.info("Voice pipeline started")
        return True

    def stop(self) -> None:
        """Stop the complete voice pipeline cleanly."""
        logger.info("Stopping voice pipeline")
        self._running = False

        # Prevent new state transitions into capture/processing
        # (In a full implementation, we would transition states properly)
        logger.info("Voice pipeline stopped")

    async def process_audio_stream(
        self,
        audio_source,
        on_intelligence_result: Optional[Callable] = None,
    ):
        """
        Process continuous audio stream for wake words and commands.

        Args:
            audio_source: Audio source generator yielding audio chunks (np.ndarray)
            on_intelligence_result: Callback for processing intelligence engine results
        """
        logger.info("Starting audio stream processing")

        try:
            async for audio_chunk in audio_source:
                # Process chunk for wake word detection
                wake_result = self.wake_detector.detect_from_audio(
                    audio_chunk.tobytes()
                )

                if wake_result:
                    await self._handle_wake_word(
                        wake_result,
                        audio_source,
                        on_intelligence_result,
                    )

        except asyncio.CancelledError:
            logger.info("Audio stream processing cancelled")
        except Exception as e:
            logger.error(f"Error in audio stream processing: {e}")
            await self.emitter.emit_error(
                ErrorEvent(error_message=str(e))
            )

    async def _handle_wake_word(
        self,
        wake_result: WakeWordDetection,
        audio_source,
        on_intelligence_result: Optional[Callable] = None,
    ):
        """
        Handle a detected wake word.

        Captures command audio via VAD, transcribes, routes, processes, and speaks.

        Args:
            wake_result: WakeWordDetection result
            audio_source: Audio source for continuing to read
            on_intelligence_result: Callback for intelligence results
        """
        async with self._state_lock:
            if self._state != VoiceState.LISTENING:
                logger.debug(
                    f"Ignoring wake word '{wake_result.wake_word}' - current state: {self._state}"
                )
                return

            self._current_entity = wake_result.wake_entity
            self._state = VoiceState.ACKNOWLEDGING

        logger.info(f"Wake word detected: {wake_result.wake_entity} (conf: {wake_result.confidence})")

        # Emit acknowledging event
        await self.emitter.emit_acknowledging(
            AcknowledgingEvent(wake_entity=wake_result.wake_entity)
        )

        # Emit wake detected event
        await self.emitter.emit_wake_detected(
            WakeWordEvent(detection=wake_result)
        )

        # Emit listening started
        await self.emitter.emit_listening_started(
            ListeningStartedEvent(wake_entity=wake_result.wake_entity)
        )

        # Transition to capturing state and emit event
        async with self._state_lock:
            self._state = VoiceState.CAPTURING
        await self.emitter.emit_capturing(
            CapturingEvent(wake_entity=wake_result.wake_entity)
        )

        # Capture command audio
        captured_audio = await self._capture_command_audio(audio_source)

        if captured_audio is None or len(captured_audio) == 0:
            logger.warning("No audio captured after wake word")
            async with self._state_lock:
                self._state = VoiceState.LISTENING
                self._current_entity = None
            return

        # Transcribe audio
        transcription = await self._transcribe_audio(captured_audio)

        if not transcription or not transcription.raw_text.strip():
            logger.warning("Transcription failed or returned empty text")
            async with self._state_lock:
                self._state = VoiceState.LISTENING
                self._current_entity = None
            return

        # Emit transcription complete
        await self.emitter.emit_transcription_complete(
            TranscriptionCompleteEvent(
                wake_entity=wake_result.wake_entity,
                transcription=transcription,
            )
        )

        # Transition to processing state and emit event
        async with self._state_lock:
            self._state = VoiceState.PROCESSING
        await self.emitter.emit_processing(
            ProcessingEvent(entity=wake_result.wake_entity)
        )

        # Extract entity from transcription text
        target_entity = self._extract_entity_from_text(transcription.raw_text)
        if target_entity is None:
            target_entity = wake_result.wake_entity

        routing_result = self.router.route(
            target_entity,
            transcription.raw_text,
        )
        if not routing_result:
            logger.error("Intent routing failed")
            async with self._state_lock:
                self._state = VoiceState.LISTENING
                self._current_entity = None
            return

        # Get intelligence engine result
        intelligence_result = await self._get_intelligence_result(
            routing_result.target_entity,
            transcription.raw_text,
            on_intelligence_result,
        )

        if not intelligence_result:
            logger.error("Intelligence engine result failed")
            async with self._state_lock:
                self._state = VoiceState.LISTENING
                self._current_entity = None
            return

        # Synthesize spoken summary
        await self._synthesize_and_speak(
            routing_result.target_entity,
            intelligence_result,
        )

        # Display full result on designated workstation
        workstation = voice_config.workstation_routing.get(routing_result.target_entity, "os")
        await self.emitter.emit_display_result(
            DisplayResultEvent(
                workstation=workstation,
                data=intelligence_result.full_result,
                requested_by_entity=routing_result.target_entity,
            )
        )

        # Return to idle
        async with self._state_lock:
            self._state = VoiceState.LISTENING
            self._current_entity = None
        await self.emitter.emit_idle(IdleEvent())

    def _extract_entity_from_text(self, text: str) -> Optional[str]:
        """
        Extract entity name from transcribed text.
        Looks for known entity names (axiom, jenson, yamako, valtaprime) in the text.
        Returns the entity name if found, else None.
        """
        if not text:
            return None
        text_lower = text.lower()
        # List of known entities
        entities = ["axiom", "jenson", "yamako", "valtaprime"]
        for entity in entities:
            # Check for the entity name as a word (with optional "hey " prefix)
            if f"hey {entity}" in text_lower or entity in text_lower:
                return entity
        return None

    async def _capture_command_audio(self, audio_source) -> Optional[np.ndarray]:
        """
        Capture audio for a command after wake word.

        Uses VAD-terminated or fixed-timeout capture depending on config.

        Args:
            audio_source: Async generator yielding audio chunks

        Returns:
            Concatenated audio array or None if capture fails
        """
        logger.debug("Starting audio capture for command")
        self.vad.reset()

        start_time = 0
        min_capture_done = False

        try:
            async for audio_chunk in audio_source:
                # Check minimum capture time
                current_time = start_time + len(audio_chunk) / 16000
                if current_time >= voice_config.capture.min_capture_time:
                    min_capture_done = True
                start_time = current_time

                # Process frame for VAD
                has_speech, speech_ended = self.vad.process_frame(
                    audio_chunk.astype(np.float32)
                )

                if voice_config.capture.capture_behavior == "vad_terminated":
                    # Stop capture when speech ends and minimum time met
                    if speech_ended and min_capture_done:
                        logger.debug("VAD detected end of speech, stopping capture")
                        break

                elif voice_config.capture.capture_behavior == "fixed_timeout":
                    # Use fixed timeout
                    if current_time >= voice_config.capture.capture_fixed_timeout:
                        logger.debug(f"Fixed timeout reached ({voice_config.capture.capture_fixed_timeout}s)")
                        break

        except asyncio.TimeoutError:
            logger.warning("Audio capture timeout")
        except Exception as e:
            logger.error(f"Error during audio capture: {e}")
            return None

        # Get captured audio
        captured = self.vad.get_captured_audio()
        if captured is not None:
            logger.debug(f"Captured {len(captured) / 16000:.2f}s of audio")

        return captured

    async def _transcribe_audio(self, audio_bytes: np.ndarray) -> Optional[TranscriptionComplete]:
        """Transcribe captured audio."""
        if self.stt.health_check():
            # Ensure audio is in the correct format for WhisperEngine (float32 numpy array)
            if audio_bytes.dtype != np.float32:
                # Convert from int16 to float32 if needed
                if audio_bytes.dtype == np.int16:
                    audio_bytes = audio_bytes.astype(np.float32) / 32768.0
                else:
                    audio_bytes = audio_bytes.astype(np.float32)

            # Normalize if needed (Whisper expects audio in range [-1, 1])
            if audio_bytes.max() > 1.0:
                audio_bytes = audio_bytes / 32768.0

            transcription = self.stt.transcribe(audio_bytes)
            return transcription
        else:
            logger.error("STT engine not healthy")
            return None

    async def _get_intelligence_result(
        self,
        target_entity: str,
        command_text: str,
        on_intelligence_result: Optional[Callable] = None,
    ) -> Optional[IntelligenceEngineOutput]:
        """
        Get result from intelligence engine (AI model).

        Args:
            target_entity: Which entity should handle this
            command_text: The transcribed command
            on_intelligence_result: Callback to delegate to intelligence engine

        Returns:
            IntelligenceEngineOutput with full_result and spoken_summary
        """
        if on_intelligence_result:
            # Delegate to external intelligence engine
            return await on_intelligence_result(target_entity, command_text)

        # Fallback: mock response
        logger.warning("No intelligence engine callback provided, using mock")

        from .models import ResultContent

        return IntelligenceEngineOutput(
            full_result=ResultContent(
                type="text",
                content={"message": f"Received command: {command_text}"},
            ),
            spoken_summary=f"I received your command. {command_text}",
            target_workstation=WORKSTATION_ROUTING.get(target_entity, "os"),
        )

    async def _synthesize_and_speak(
        self,
        entity_name: str,
        intelligence_result: IntelligenceEngineOutput,
    ):
        """
        Synthesize TTS for spoken summary and emit speaking event.

        Args:
            entity_name: Entity doing the speaking
            intelligence_result: Result with spoken_summary
        """
        try:
            # Get TTS service instance (lazy initialization)
            if self._tts_service is None:
                self._tts_service = tts_service
                if self._tts_service is None:
                    from .tts.service import get_tts_service
                    self._tts_service = get_tts_service()

            # Initialize if needed
            if not self._tts_service._initialized:
                await self._tts_service.initialize()

            # Get voice profile for the entity
            voice_profile = get_voice_profile(entity_name)

            # Transition to speaking state
            async with self._state_lock:
                self._state = VoiceState.SPEAKING

            # Synthesize using TTS service
            audio_result = self._tts_service.synthesize(
                intelligence_result.spoken_summary,
                entity_name,
            )

            if audio_result:
                # Emit speaking event with audio
                await self.emitter.emit_executive_speaking(
                    ExecutiveSpeakingEvent(
                        entity=entity_name,
                        spoken_text=intelligence_result.spoken_summary,
                        audio=audio_result,
                    )
                )
            else:
                logger.error(f"TTS synthesis failed for entity {entity_name}")
                # Still emit the event but with None audio to indicate failure
                await self.emitter.emit_executive_speaking(
                    ExecutiveSpeakingEvent(
                        entity=entity_name,
                        spoken_text=intelligence_result.spoken_summary,
                        audio=None,  # Indicates synthesis failure
                    )
                )

        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")

    def health_check(self) -> dict[str, bool]:
        """Check health of all pipeline components."""
        # Check TTS service health
        tts_healthy = False
        try:
            # Try to get and initialize TTS service
            tts_svc = self._tts_service or tts_service
            if tts_svc is None:
                from .tts.service import get_tts_service
                tts_svc = get_tts_service()

            if tts_svc is not None:
                # Check if already initialized (don't try to initialize in health check to avoid blocking)
                if tts_svc._initialized:
                    # Check if any provider is available
                    providers = tts_svc.get_available_providers()
                    tts_healthy = any(providers.values()) if providers else False
                # If not initialized, we consider it unhealthy for health check purposes
                # Initialization should be done via the proper initialize() method
        except Exception as e:
            logger.debug(f"TTS health check failed: {e}")
            tts_healthy = False

        return {
            "wake_detector": bool(self.wake_detector.get_loaded_entities()),
            "vad": True,  # VAD always initialized
            "stt": self.stt.health_check(),
            "router": True,  # Router always ready
            "tts": tts_healthy,
        }


# ---------------------------------------------------------------------
# Global pipeline instance
# ---------------------------------------------------------------------

_pipeline_instance: Optional[VoicePipelineOrchestrator] = None


def get_pipeline() -> VoicePipelineOrchestrator:
    """Get or create the global pipeline instance."""
    global _pipeline_instance

    if _pipeline_instance is None:
        _pipeline_instance = VoicePipelineOrchestrator(use_mock=True)
        logger.info(
            f"VoicePipelineOrchestrator created "
            f"id={id(_pipeline_instance)} "
            "via get_pipeline() (mock mode)"
        )

    return _pipeline_instance


def initialize_pipeline(
    connection_manager: WebSocketConnectionManager = None,
    runtime: Any = None,
    use_mock: bool = False,
) -> VoicePipelineOrchestrator:
    """Initialize and return the global pipeline instance."""
    global _pipeline_instance

    logger.info(
        f"initialize_pipeline ENTER: "
        f"connection_manager={connection_manager is not None}, "
        f"runtime={runtime is not None}, "
        f"use_mock={use_mock}"
    )

    _pipeline_instance = VoicePipelineOrchestrator(
        connection_manager=connection_manager,
        runtime=runtime,
        use_mock=use_mock,
    )

    logger.info(
        "initialize_pipeline: "
        f"VoicePipelineOrchestrator created "
        f"id={id(_pipeline_instance)}"
    )

    # Initialize the pipeline (this would normally be async, but for sync compatibility)
    # In a real implementation, this would be handled differently
    # For now, we'll note that initialization should be done via the async initialize() method

    return _pipeline_instance