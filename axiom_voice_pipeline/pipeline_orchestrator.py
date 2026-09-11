"""
Pipeline Orchestrator - coordinates the complete voice pipeline.

Ties together wake word detection, VAD, STT, intent routing, intelligence engine,
TTS, and WebSocket relay.

Flow:
    [Mic] -> [Wake Word Detection] -> [VAD Capture] -> [STT] -> [Intent Router] ->
    [Intelligence Engine] -> [TTS] -> [WebSocket Relay] -> [Frontend]
"""

import asyncio
import io
import logging
from typing import Optional

import numpy as np

from .config import (
    CAPTURE_BEHAVIOR,
    CAPTURE_FIXED_TIMEOUT,
    MIN_CAPTURE_TIME,
    WORKSTATION_ROUTING,
)
from .models import (
    DisplayResultEvent,
    ErrorEvent,
    ExecutiveSpeakingEvent,
    IdleEvent,
    IntelligenceEngineOutput,
    ListeningStartedEvent,
    ProcessingEvent,
    PipelineState,
    TranscriptionComplete,
    TranscriptionCompleteEvent,
    WakeWordDetection,
    WakeWordEvent,
)
from .relay.ws_server import PipelineEventEmitter, WebSocketConnectionManager
from .router.intent_router import IntentRouter
from .stt.whisper_engine import WhisperEngine
from .tts.provider_base import TTSProviderProxy
from .tts.voice_profiles import get_piper_voice_id
from .wakeword.detector import WakeWordDetector
from .wakeword.vad import VoiceActivityDetector

logger = logging.getLogger(__name__)


class VoicePipeline:
    """
    Main orchestrator for the voice pipeline.
    
    Manages the complete flow from wake word detection through TTS synthesis.
    """
    
    def __init__(self, connection_manager: WebSocketConnectionManager = None):
        """
        Initialize the voice pipeline.
        
        Args:
            connection_manager: WebSocketConnectionManager for relay. If None, creates new.
        """
        self.connection_manager = connection_manager or WebSocketConnectionManager()
        self.emitter = PipelineEventEmitter(self.connection_manager)
        
        # Initialize pipeline components
        logger.info("Initializing voice pipeline components...")
        self.wake_detector = WakeWordDetector()
        self.vad = VoiceActivityDetector()
        self.stt = WhisperEngine()
        self.router = IntentRouter()
        self.tts_proxy = TTSProviderProxy("piper", "piper")
        
        # Pipeline state
        self.state = PipelineState()
        
        logger.info("Voice pipeline initialized")
    
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


    async def process_audio_stream(
        self,
        audio_source,
        on_intelligence_result: Optional[callable] = None,
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
        on_intelligence_result: Optional[callable] = None,
    ):
        """
        Handle a detected wake word.
        
        Captures command audio via VAD, transcribes, routes, processes, and speaks.
        
        Args:
            wake_result: WakeWordDetection result
            audio_source: Audio source for continuing to read
            on_intelligence_result: Callback for intelligence results
        """
        self.state.active_entity = wake_result.wake_entity
        self.state.is_listening = True
        
        logger.info(f"Wake word detected: {wake_result.wake_entity} (conf: {wake_result.confidence})")
        
        # Emit wake detected event
        await self.emitter.emit_wake_detected(
            WakeWordEvent(detection=wake_result)
        )
        
        # Emit listening started
        await self.emitter.emit_listening_started(
            ListeningStartedEvent(wake_entity=wake_result.wake_entity)
        )
        
        # Capture command audio
        captured_audio = await self._capture_command_audio(audio_source)

        if captured_audio is None or len(captured_audio) == 0:
            logger.warning("No audio captured after wake word")
            self.state.is_listening = False
            return
        
        # Transcribe audio
        transcription = await self._transcribe_audio(captured_audio)
        
        if not transcription or not transcription.raw_text.strip():
            logger.warning("Transcription failed or returned empty text")
            self.state.is_listening = False
            return
        
        # Emit transcription complete
        await self.emitter.emit_transcription_complete(
            TranscriptionCompleteEvent(
                wake_entity=wake_result.wake_entity,
                transcription=transcription,
            )
        )
        
        # Route the intent
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
            self.state.is_listening = False
            return
        
        # Get intelligence engine result
        # This is where the AI model would process the command
        intelligence_result = await self._get_intelligence_result(
            routing_result.target_entity,
            transcription.raw_text,
            on_intelligence_result,
        )
        
        if not intelligence_result:
            logger.error("Intelligence engine result failed")
            self.state.is_listening = False
            return
        
        # Synthesize spoken summary
        await self._synthesize_and_speak(
            routing_result.target_entity,
            intelligence_result,
        )
        
        # Display full result on designated workstation
        workstation = WORKSTATION_ROUTING.get(routing_result.target_entity, "os")
        await self.emitter.emit_display_result(
            DisplayResultEvent(
                workstation=workstation,
                data=intelligence_result.full_result,
                requested_by_entity=routing_result.target_entity,
            )
        )
        
        # Return to idle
        self.state.is_listening = False
        await self.emitter.emit_idle(IdleEvent())
    
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
                if current_time >= MIN_CAPTURE_TIME:
                    min_capture_done = True
                start_time = current_time
                
                # Process frame for VAD
                has_speech, speech_ended = self.vad.process_frame(
                    audio_chunk.astype(np.float32)
                )
                
                if CAPTURE_BEHAVIOR == "vad_terminated":
                    # Stop capture when speech ends and minimum time met
                    if speech_ended and min_capture_done:
                        logger.debug("VAD detected end of speech, stopping capture")
                        break
                
                elif CAPTURE_BEHAVIOR == "fixed_timeout":
                    # Use fixed timeout
                    if current_time >= CAPTURE_FIXED_TIMEOUT:
                        logger.debug(f"Fixed timeout reached ({CAPTURE_FIXED_TIMEOUT}s)")
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
            # Convert numpy array to bytes for transcription
            audio_bytes_wav = audio_bytes.astype(np.int16).tobytes()
            transcription = self.stt.transcribe(audio_bytes_wav)
            return transcription
        else:
            logger.error("STT engine not healthy")
            return None
    
    async def _get_intelligence_result(
        self,
        target_entity: str,
        command_text: str,
        on_intelligence_result: Optional[callable] = None,
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
            voice_id = get_piper_voice_id(entity_name)
            
            # Synthesize
            audio_result = self.tts_proxy.synthesize(
                intelligence_result.spoken_summary,
                voice_id,
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
        
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
    
    def health_check(self) -> dict[str, bool]:
        """Check health of all pipeline components."""
        return {
            "wake_detector": bool(self.wake_detector.get_loaded_entities()),
            "vad": True,  # VAD always initialized
            "stt": self.stt.health_check(),
            "router": True,  # Router always ready
            "tts": self.tts_proxy.health_check(),
        }
