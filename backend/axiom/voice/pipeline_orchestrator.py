"""Pipeline orchestrator - ties wake -> stt -> router -> engine -> tts -> relay together."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from axiom.voice.config import voice_config, EXECUTIVE_WAKE_WORDS, VALID_EXECUTIVES
from axiom.voice.wakeword import (
    WakeWordDetector,
    MockWakeWordDetector,
    create_wake_word_detector,
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


@dataclass
class VoiceEvent:
    """Event in the voice pipeline."""
    event_type: str
    entity: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    data: Dict[str, Any] = field(default_factory=dict)


class VoicePipelineOrchestrator:
    """
    Main orchestrator for the voice pipeline.
    
    Flow:
    1. WakeWordDetector detects wake word -> on_wake callback
    2. VADCaptureManager captures audio until silence
    3. WhisperEngine transcribes captured audio
    4. IntentRouter routes to target executive
    5. Intelligence engine processes command (via existing API)
    6. TTS service synthesizes response
    7. VoiceRelayServer emits events to frontend
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
        
        # Components
        self.wake_detector: Optional[WakeWordDetector] = None
        self.vad_capture: Optional[VADCaptureManager] = None
        self.stt_engine: Optional[WhisperEngine] = None
        self.intent_router = IntentRouter()
        # State
        self._running = False
        self._capturing = False
        self._current_entity: Optional[str] = None
        self._conversation_history: Dict[str, List[Dict[str, str]]] = {}
        
        # Callbacks
        self._event_callbacks: List[Callable[[VoiceEvent], None]] = []
        self._tts_service = None
        
    @property
    def tts_service(self):
        if self._tts_service is None:
            self._tts_service = get_tts_service()
        return self._tts_service
    
    def add_event_callback(self, callback: Callable[[VoiceEvent], None]) -> None:
        """Add a callback for pipeline events."""
        self._event_callbacks.append(callback)
    
    def _emit_event(self, event: VoiceEvent) -> None:
        """Emit event to all callbacks and relay server."""
        for callback in self._event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
        
        # Also send to relay server if available
        if self.relay_server:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.relay_server.broadcast_event(event),
                    self.relay_server._loop if hasattr(self.relay_server, '_loop') else asyncio.get_event_loop()
                )
            except Exception as e:
                logger.debug(f"Relay broadcast error: {e}")
    
    def initialize(self) -> bool:
        """Initialize all pipeline components."""
        logger.info("Initializing voice pipeline...")
        
        # Initialize TTS service
        if not self.tts_service.initialize():
            logger.error("TTS service initialization failed")
            return False
        
        # Initialize STT engine
        self.stt_engine = create_whisper_engine(use_mock=self.use_mock)
        if not self.stt_engine.load():
            logger.error("STT engine initialization failed")
            return False
        
        # Initialize wake word detector
        self.wake_detector = create_wake_word_detector(
            use_mock=self.use_mock,
            on_wake=self._on_wake_word,
        )
        if not self.wake_detector.load_models():
            logger.warning("Wake word models not loaded, detection may not work")
        
        # Initialize VAD capture manager
        self.vad_capture = create_vad_capture_manager(
            use_mock=self.use_mock,
            sample_rate=self.config.stt.sample_rate if hasattr(self.config, 'stt') else 16000,
            vad_type="silero",
            silence_timeout=self.config.capture.silence_timeout,
            max_duration=self.config.capture.max_duration,
            min_duration=self.config.capture.min_duration,
            on_capture_complete=self._on_capture_complete,
        )
        
        # Initialize relay server
        self.relay_server = VoiceRelayServer(
            host=self.config.ws_host,
            port=self.config.ws_port,
        )
        
        logger.info("Voice pipeline initialized")
        return True
    
    def start(self) -> bool:
        """Start the voice pipeline."""
        if self._running:
            logger.warning("Pipeline already running")
            return True
        
        if not self.wake_detector:
            if not self.initialize():
                return False
        
        self._running = True
        
        # Start wake word detection
        if not self.wake_detector.start():
            logger.error("Failed to start wake word detector")
            self._running = False
            return False
        
        # Start relay server
        if self.relay_server:
            self.relay_server.start()
        
        logger.info("Voice pipeline started")
        return True
    
    def stop(self) -> None:
        """Stop the voice pipeline."""
        self._running = False
        
        if self.wake_detector:
            self.wake_detector.stop()
        
        if self.vad_capture and self._capturing:
            self.vad_capture.stop_capture()
        
        if hasattr(self, 'relay_server') and self.relay_server:
            self.relay_server.stop()
        
        logger.info("Voice pipeline stopped")
    
    def _on_wake_word(self, entity: str, confidence: float, wake_word: str) -> None:
        """Callback when wake word is detected."""
        if self._capturing:
            logger.debug("Already capturing, ignoring wake word")
            return
        
        logger.info(f"Wake word detected: {entity} ({wake_word}) confidence={confidence:.3f}")
        
        self._current_entity = entity
        self._capturing = True
        
        # Emit wake detected event
        self._emit_event(VoiceEvent(
            event_type="wake_detected",
            entity=entity,
            data={
                "wake_word": wake_word,
                "confidence": confidence,
            }
        ))
        
        # Emit listening started event
        self._emit_event(VoiceEvent(
            event_type="listening_started",
            entity=entity,
        ))
        
        # Start VAD capture
        if not self.vad_capture.start_capture():
            logger.error("Failed to start VAD capture")
            self._capturing = False
            self._emit_event(VoiceEvent(
                event_type="error",
                entity=entity,
                data={"message": "Failed to start audio capture"},
            ))
    
    def _on_capture_complete(self, audio: np.ndarray) -> None:
        """Callback when VAD capture completes."""
        if not self._capturing or not self._current_entity:
            logger.debug("Capture complete but not capturing")
            return
        
        entity = self._current_entity
        self._capturing = False
        
        logger.info(f"Capture complete for {entity}, processing...")
        
        # Emit transcription started
        self._emit_event(VoiceEvent(
            event_type="transcription_started",
            entity=entity,
        ))
        
        # Run transcription in background
        threading.Thread(
            target=self._process_audio,
            args=(audio, entity),
            daemon=True,
        ).start()
    
    def _process_audio(self, audio: np.ndarray, entity: str) -> None:
        """Process captured audio: transcribe -> route -> execute -> respond."""
        try:
            # Transcribe
            transcript, confidence = self.stt_engine.transcribe(audio)
            
            if not transcript.strip():
                logger.warning("Empty transcription")
                self._emit_event(VoiceEvent(
                    event_type="transcription_complete",
                    entity=entity,
                    data={"text": "", "confidence": confidence, "empty": True},
                ))
                self._emit_event(VoiceEvent(
                    event_type="idle",
                    entity=entity,
                ))
                return
            
            logger.info(f"Transcription for {entity}: '{transcript}' (confidence: {confidence:.3f})")
            
            # Emit transcription complete
            self._emit_event(VoiceEvent(
                event_type="transcription_complete",
                entity=entity,
                data={
                    "text": transcript,
                    "confidence": confidence,
                },
            ))
            
            # Route command
            router_output = self.intent_router.route(
                transcript=transcript,
                wake_entity=entity,
                confidence=confidence,
            )
            
            target_entity = router_output.target_entity
            delegated_by = router_output.delegated_by
            
            logger.info(f"Routed to: {target_entity}" + (f" (delegated by {delegated_by})" if delegated_by else ""))
            
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
            
            # Process command via backend API
            response_text = self._execute_command(target_entity, transcript, history)
            
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
            self._emit_event(VoiceEvent(
                event_type="synthesizing",
                entity=target_entity,
                data={"text": response_text},
            ))
            
            audio_data = self.tts_service.synthesize(response_text, target_entity)
            
            # Emit executive speaking event with audio
            self._emit_event(VoiceEvent(
                event_type="executive_speaking",
                entity=target_entity,
                data={
                    "spoken_text": response_text,
                    "audio_data": audio_data,  # Will be base64 encoded by relay
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
            logger.error(f"Pipeline processing error: {e}")
            self._emit_event(VoiceEvent(
                event_type="error",
                entity=entity,
                data={"message": str(e)},
            ))
        finally:
            self._current_entity = None
            # Emit idle
            self._emit_event(VoiceEvent(
                event_type="idle",
                entity=entity,
            ))
    
    def _execute_command(self, entity: str, transcript: str, history: List[Dict]) -> str:
        """Execute command via backend API/runtime."""
        try:
            # Use the existing voice command API endpoint logic
            # This integrates with the existing executive runtime loops
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
        # This would call into the existing executive loop trigger_cycle method
        # For now, return a placeholder that matches the existing API behavior
        if hasattr(self.runtime, 'executive_board') and self.runtime.executive_board:
            loop = self.runtime.executive_board.get_loop(entity)
            if loop:
                # Trigger a voice cycle
                import asyncio
                try:
                    # This is async, so we need to run it
                    future = asyncio.run_coroutine_threadsafe(
                        loop.trigger_cycle("voice", {
                            "voice_command": transcript,
                            "conversation_history": history,
                        }),
                        asyncio.get_event_loop()
                    )
                    result = future.result(timeout=30)
                    
                    # Generate response from result
                    from axiom.voice.router.intent_router import _generate_executive_response
                    return _generate_executive_response(entity, transcript, result)
                except Exception as e:
                    logger.error(f"Runtime execution failed: {e}")
        
        # Fallback
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
        if self._capturing:
            logger.warning("Already capturing")
            return False
        
        logger.info(f"Push-to-talk triggered for {entity}")
        self._on_wake_word(entity, 1.0, "push_to_talk")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status."""
        return {
            "running": self._running,
            "capturing": self._capturing,
            "current_entity": self._current_entity,
            "wake_detector_running": self.wake_detector._running if self.wake_detector else False,
            "stt_loaded": self.stt_engine._model is not None if self.stt_engine else False,
            "tts_providers": self.tts_service.get_available_providers(),
            "relay_connected": self.relay_server._running if self.relay_server else False,
        }


# Global pipeline instance
_pipeline_instance: Optional[VoicePipelineOrchestrator] = None


def get_pipeline() -> VoicePipelineOrchestrator:
    """Get or create the global pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = VoicePipelineOrchestrator()
    return _pipeline_instance


def initialize_pipeline(runtime: Any = None, use_mock: bool = False) -> VoicePipelineOrchestrator:
    """Initialize and return the global pipeline instance."""
    global _pipeline_instance
    _pipeline_instance = VoicePipelineOrchestrator(runtime=runtime, use_mock=use_mock)
    _pipeline_instance.initialize()
    return _pipeline_instance