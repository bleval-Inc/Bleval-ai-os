"""FastAPI integration for the Axiom Voice Pipeline.

Endpoints and WebSocket handlers for integrating the voice pipeline with the backend.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Form, File
from pydantic import BaseModel

# Use axiom.voice package (the actual voice pipeline implementation)
from axiom.voice.config import voice_config, EXECUTIVE_WAKE_WORDS, VALID_EXECUTIVES
from axiom.voice.pipeline_orchestrator import VoicePipelineOrchestrator
from axiom.voice.relay.ws_server import WebSocketConnectionManager as VoiceConnectionManager

logger = logging.getLogger(__name__)

# Create router for voice pipeline endpoints
router = APIRouter(prefix="/api/v1/voice", tags=["voice-pipeline"])

# Global pipeline instance (in production, use dependency injection)
_pipeline_instance: Optional[VoicePipelineOrchestrator] = None
_connection_manager: Optional[VoiceConnectionManager] = None

# Injected Axiom runtime (set from main.py lifespan) so voice commands can
# reach the intelligence engine rather than always falling back to mock.
_runtime = None


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
    from axiom.voice.voice_intelligence_callback import create_voice_callback

    return create_voice_callback(_runtime)


def get_pipeline() -> VoicePipelineOrchestrator:
    """Get or create the global pipeline instance.

    If a runtime has been injected, use its voice pipeline to avoid
    duplicate initialization and port conflicts.
    """
    global _pipeline_instance, _connection_manager, _runtime
    if _pipeline_instance is None:
        # If we have a runtime with a voice pipeline, use it
        if _runtime is not None and hasattr(_runtime, 'voice_pipeline') and _runtime.voice_pipeline is not None:
            _pipeline_instance = _runtime.voice_pipeline
            # For backward compatibility, we still need a connection manager
            # that matches the expected interface. The axiom.voice pipeline's
            # relay server should provide the needed methods.
            _connection_manager = VoiceConnectionManager(_runtime.voice_pipeline.relay_server)
        else:
            # Use mock pipeline for testing when runtime not available
            _pipeline_instance = VoicePipelineOrchestrator(use_mock=True)
            _connection_manager = VoiceConnectionManager(_pipeline_instance.relay_server) if _pipeline_instance.relay_server else None
            print(f"[STARTUP_VOICE] Using mock voice pipeline (id={id(_pipeline_instance)})")
    return _pipeline_instance


def get_connection_manager() -> VoiceConnectionManager:
    """Get the global connection manager."""
    return get_pipeline().connection_manager


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
    return PipelineConfigResponse(
        capture_behavior="vad",  # Default
        confidence_threshold=voice_config.wake_word.confidence_threshold,
        vad_engine=voice_config.capture.vad_engine,
        stt_model_size=voice_config.stt.model_size,
        tts_provider=voice_config.tts.provider,
    )


@router.get("/entities")
async def get_entities() -> dict:
    """Get list of configured entities and their profiles."""
    from axiom.voice.config import EXECUTIVE_WAKE_WORDS, EXECUTIVE_WORKSTATIONS

    return {
        entity_name: {
            "display_name": entity_name.title(),
            "wake_phrases": EXECUTIVE_WAKE_WORDS.get(entity_name, []),
            "voice_character": EXECUTIVE_WORKSTATIONS.get(entity_name, ""),
        }
        for entity_name in VALID_EXECUTIVES
    }


@router.post("/test/synthesize")
async def test_synthesize(entity_name: str = Form(...), text: str = Form(...)) -> dict:
    """
    Test TTS synthesis for a specific entity.

    Args:
        entity_name: Entity to synthesize with (axiom, jenson, yamako, valta_prime)
        text: Text to synthesize

    Returns:
        Synthesis result with duration and audio metadata
    """
    pipeline = get_pipeline()

    try:
        audio_result = pipeline.tts.synthesize(text, entity_name)

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
async def process_audio_chunk(entity_wake_word: str = Form(...), audio_bytes: bytes = File(...)) -> dict:
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
        detection = pipeline.audio_processor.wake_detector.detect_from_audio(audio_bytes)

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
async def transcribe_audio(audio_bytes: bytes = File(...)) -> dict:
    """
    Transcribe audio to text.

    Args:
        audio_bytes: Raw audio data (WAV or PCM)

    Returns:
        Transcription result with text and confidence
    """
    pipeline = get_pipeline()

    try:
        transcription = pipeline.stt_engine.transcribe(audio_bytes)

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
@router.get("/debug/identity")
async def debug_identity():
    pipeline = get_pipeline()
    return {
        "route_pipeline_id": id(pipeline),
        "runtime_pipeline_id": id(_runtime.voice_pipeline) if _runtime and _runtime.voice_pipeline else None,
        "same": id(pipeline) == id(_runtime.voice_pipeline) if _runtime and _runtime.voice_pipeline else False
    }
