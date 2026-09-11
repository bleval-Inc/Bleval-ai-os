"""
FastAPI integration for the Axiom Voice Pipeline.

Endpoints and WebSocket handlers for integrating the voice pipeline with the backend.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

# Ensure the repo root (parent of backend/) is importable so the standalone
# axiom_voice_pipeline package resolves regardless of the launch CWD.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from axiom_voice_pipeline.config import wake_word_config
from axiom_voice_pipeline.models import ErrorEvent
from axiom_voice_pipeline.pipeline_orchestrator import VoicePipeline
from axiom_voice_pipeline.relay.ws_server import WebSocketConnectionManager

logger = logging.getLogger(__name__)

# Create router for voice pipeline endpoints
router = APIRouter(prefix="/api/v1/voice", tags=["voice-pipeline"])

# Global pipeline instance (in production, use dependency injection)
_pipeline_instance: Optional[VoicePipeline] = None
_connection_manager: Optional[WebSocketConnectionManager] = None

# Injected Axiom runtime (set from main.py lifespan) so voice commands can
# reach the intelligence engine rather than always falling back to mock.
_runtime = None


class _VoicePipelineEventEmitter:
    """Simple event emitter that uses a WebSocketConnectionManager's broadcast_event method."""

    def __init__(self, connection_manager):
        self.manager = connection_manager

    async def emit(self, event) -> None:
        """Emit a VoiceEvent via the connection manager."""
        # Import here to avoid circular imports
        from axiom_voice_pipeline.models import VoiceEvent

        payload = {
            "entity": event.entity,
            "timestamp": event.timestamp,
            **event.data
        }
        await self.manager.broadcast_event(
            event_type=event.event_type,
            payload=payload,
        )


def set_runtime(runtime) -> None:
    """Inject the Axiom runtime into the voice pipeline layer."""
    global _runtime
    _runtime = runtime


def get_voice_callback():
    """
    Return a VoiceIntelligenceCallback bound to the injected runtime.

    Returns None when no runtime has been injected (e.g. standalone use),
    in which case the pipeline's own mock fallback applies.
    """
    from axiom_voice_pipeline.voice_intelligence_callback import create_voice_callback

    return create_voice_callback(_runtime)


def get_pipeline() -> VoicePipeline:
    """Get or create the global pipeline instance."""
    global _pipeline_instance, _connection_manager, _runtime

    # If we have a runtime, use its voice pipeline
    if _runtime is not None and hasattr(_runtime, 'voice_pipeline'):
        pipeline = _runtime.voice_pipeline
        # Ensure the pipeline uses our connection manager for event emission
        if pipeline.connection_manager is None:
            _connection_manager = WebSocketConnectionManager()
            pipeline.connection_manager = _connection_manager
            pipeline.emitter = _VoicePipelineEventEmitter(_connection_manager)
        return pipeline

    # Fallback to legacy standalone pipeline
    if _pipeline_instance is None:
        _connection_manager = WebSocketConnectionManager()
        _pipeline_instance = VoicePipeline(_connection_manager)
    return _pipeline_instance


def get_connection_manager() -> WebSocketConnectionManager:
    """Get the global connection manager."""
    global _connection_manager
    if _connection_manager is None:
        # Initialize if not already done
        get_pipeline()  # This will set _connection_manager
    return _connection_manager


# ============================================================================
# DATA MODELS
# ============================================================================


class HealthCheckResponse(BaseModel):
    """Response model for health check."""

    status: str
    pipeline_components: dict[str, bool]
    active_connections: int


class PipelineConfigResponse(BaseModel):
    """Response model for pipeline configuration."""

    capture_behavior: str
    confidence_threshold: float
    vad_engine: str
    stt_model_size: str
    tts_provider: str


# ============================================================================
# REST ENDPOINTS
# ============================================================================


@router.get("/health")
async def health_check() -> HealthCheckResponse:
    """
    Check health of the voice pipeline.

    Returns health status of all pipeline components.
    """
    pipeline = get_pipeline()
    health = pipeline.health_check()
    manager = get_connection_manager()

    return HealthCheckResponse(
        status="healthy" if all(health.values()) else "degraded",
        pipeline_components=health,
        active_connections=manager.get_connection_count(),
    )


@router.get("/config")
async def get_config() -> PipelineConfigResponse:
    """Get current pipeline configuration."""
    from axiom_voice_pipeline.config import (
        CAPTURE_BEHAVIOR,
        stt_config,
        tts_config,
        vad_config,
        wake_word_config,
    )

    return PipelineConfigResponse(
        capture_behavior=CAPTURE_BEHAVIOR,
        confidence_threshold=wake_word_config.confidence_threshold,
        vad_engine=vad_config.engine,
        stt_model_size=stt_config.model_size,
        tts_provider=tts_config.primary_provider,
    )


@router.get("/entities")
async def get_entities() -> dict:
    """Get list of configured entities and their profiles."""
    from axiom_voice_pipeline.config import ENTITIES

    return {
        entity_name: {
            "display_name": profile.display_name,
            "wake_phrases": profile.wake_phrases,
            "voice_character": profile.voice_character,
        }
        for entity_name, profile in ENTITIES.items()
    }


@router.post("/test/synthesize")
async def test_synthesize(entity_name: str, text: str) -> dict:
    """
    Test TTS synthesis for a specific entity.

    Args:
        entity_name: Entity to synthesize with (axiom, jenson, yamako, valtaprime)
        text: Text to synthesize

    Returns:
        Synthesis result with duration and audio metadata
    """
    from axiom_voice_pipeline.tts.voice_profiles import get_piper_voice_id

    pipeline = get_pipeline()

    try:
        voice_id = get_piper_voice_id(entity_name)
        audio_result = pipeline.tts_proxy.synthesize(text, voice_id)

        if audio_result:
            return {
                "status": "success",
                "entity": entity_name,
                "duration_seconds": audio_result.duration_seconds,
                "sample_rate": audio_result.sample_rate,
                "text_synthesized": text,
            }
        else:
            return {
                "status": "error",
                "error": "TTS synthesis failed",
            }
    except Exception as e:
        logger.error(f"Error in test synthesis: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


# ============================================================================
# WEBSOCKET HANDLERS
# ============================================================================


@router.websocket("/events")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for receiving voice pipeline events.

    Clients connect here to receive real-time events from the voice pipeline:
    - Wake word detected
    - Listening started
    - Transcription complete
    - Processing status
    - Executive speaking (with audio)
    - Display results
    - Idle/Ready
    - Errors

    Events are sent as JSON messages with the following structure:
    {
        "type": "event_type",
        "payload": {...},
        "metadata": {...}  (optional)
    }
    """
    manager = get_connection_manager()
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection open and listen for any client messages
            # In this implementation, we mainly broadcast from the server
            data = await websocket.receive_text()

            # Optional: handle client commands
            # For now, just acknowledge
            logger.debug(f"Received from client: {data}")

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)


# ============================================================================
# AUDIO PROCESSING ENDPOINTS (Future)
# ============================================================================


@router.post("/audio/process")
async def process_audio_chunk(entity_wake_word: str, audio_bytes: bytes) -> dict:
    """
    Process a single audio chunk for wake word detection.

    Args:
        entity_wake_word: Which entity wake word to detect (optional override)
        audio_bytes: Raw audio bytes to process

    Returns:
        Detection result or null if no wake word detected
    """
    pipeline = get_pipeline()

    try:
        detection = pipeline.wake_detector.detect_from_audio(audio_bytes)

        if detection:
            return {
                "wake_entity": detection.wake_entity,
                "confidence": detection.confidence,
                "timestamp": detection.timestamp.isoformat(),
            }
        else:
            return {"wake_entity": None}
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return {"error": str(e)}


@router.post("/transcribe")
async def transcribe_audio(audio_bytes: bytes) -> dict:
    """
    Transcribe audio to text.

    Args:
        audio_bytes: Raw audio data (WAV or PCM)

    Returns:
        Transcription result with text and confidence
    """
    pipeline = get_pipeline()

    try:
        transcription = pipeline.stt.transcribe(audio_bytes)

        if transcription:
            return {
                "text": transcription.raw_text,
                "confidence": transcription.confidence,
                "duration_seconds": transcription.duration_seconds,
            }
        else:
            return {"error": "Transcription failed"}
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return {"error": str(e)}


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================


async def startup():
    """Initialize voice pipeline on startup."""
    logger.info("Initializing voice pipeline...")
    pipeline = get_pipeline()
    health = pipeline.health_check()
    logger.info(f"Voice pipeline health: {health}")


async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Shutting down voice pipeline...")
    # Add cleanup logic here if needed


# Register startup/shutdown handlers
# (These should be added to the main FastAPI app instance)
# app.add_event_handler("startup", startup)
# app.add_event_handler("shutdown", shutdown)