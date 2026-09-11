"""Axiom Voice Pipeline - Server-side voice activation, STT, routing, and TTS."""

# Import main orchestrator
from axiom_voice_pipeline.pipeline_orchestrator import VoicePipeline
from axiom_voice_pipeline.relay.ws_server import (
    PipelineEventEmitter,
    WebSocketConnectionManager,
)

# Import configuration
from axiom_voice_pipeline.config import (
    ENTITIES,
    WORKSTATION_ROUTING,
    EntityProfile,
    IntentRouterConfig,
    STTConfig,
    TTSConfig,
    VADConfig,
    WakeWordConfig,
    WebSocketConfig,
    intent_router_config,
    stt_config,
    tts_config,
    vad_config,
    wake_word_config,
    websocket_config,
)

# Import data models
from axiom_voice_pipeline.models import (
    DisplayResultEvent,
    ErrorEvent,
    EventType,
    ExecutiveSpeakingEvent,
    IdleEvent,
    IntelligenceEngineOutput,
    IntentRouterOutput,
    ListeningStartedEvent,
    PipelineState,
    ProcessingEvent,
    SynthesizedAudio,
    TranscriptionComplete,
    TranscriptionCompleteEvent,
    WakeWordDetection,
    WakeWordEvent,
)

# Import components
from axiom_voice_pipeline.wakeword.detector import WakeWordDetector
from axiom_voice_pipeline.wakeword.vad import (
    SileroVAD,
    VoiceActivityDetector,
    WebRTCVAD,
)
from axiom_voice_pipeline.stt.whisper_engine import WhisperEngine
from axiom_voice_pipeline.router.intent_router import IntentRouter
from axiom_voice_pipeline.tts.provider_base import (
    TTSProvider,
    TTSProviderFactory,
    TTSProviderProxy,
)
from axiom_voice_pipeline.tts.piper_provider import PiperTTS
from axiom_voice_pipeline.tts.elevenlabs_provider import ElevenLabsTTS
from axiom_voice_pipeline.tts.voice_profiles import (
    VoiceProfile,
    get_elevenlabs_voice_id,
    get_piper_voice_id,
    get_voice_profile,
)

__version__ = "1.0.0"
__all__ = [
    # Main orchestrator
    "VoicePipeline",
    # WebSocket relay
    "WebSocketConnectionManager",
    "PipelineEventEmitter",
    # Configuration
    "ENTITIES",
    "WORKSTATION_ROUTING",
    "EntityProfile",
    "WakeWordConfig",
    "VADConfig",
    "STTConfig",
    "TTSConfig",
    "IntentRouterConfig",
    "WebSocketConfig",
    "wake_word_config",
    "vad_config",
    "stt_config",
    "tts_config",
    "intent_router_config",
    "websocket_config",
    # Models
    "EventType",
    "WakeWordDetection",
    "WakeWordEvent",
    "TranscriptionComplete",
    "TranscriptionCompleteEvent",
    "IntentRouterOutput",
    "IntelligenceEngineOutput",
    "SynthesizedAudio",
    "ExecutiveSpeakingEvent",
    "DisplayResultEvent",
    "IdleEvent",
    "ListeningStartedEvent",
    "ProcessingEvent",
    "ErrorEvent",
    "PipelineState",
    # Components
    "WakeWordDetector",
    "VoiceActivityDetector",
    "SileroVAD",
    "WebRTCVAD",
    "WhisperEngine",
    "IntentRouter",
    "TTSProvider",
    "TTSProviderFactory",
    "TTSProviderProxy",
    "PiperTTS",
    "ElevenLabsTTS",
    "VoiceProfile",
    "get_voice_profile",
    "get_piper_voice_id",
    "get_elevenlabs_voice_id",
]
