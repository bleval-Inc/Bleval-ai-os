"""Voice pipeline configuration for Axiom OS."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel

from axiom.config import settings

# ============================================================================
# EXECUTIVE DEFINITIONS (Merged from reference and AXIOM)
# ============================================================================

# Executive wake word configuration — kept in sync with the frontend
# (dashboard/components/axiom/VoiceEngine.tsx) and /voice/executives.
EXECUTIVE_WAKE_WORDS: Dict[str, List[str]] = {
    "axiom": ["axiom on", "axiom", "hey axiom", "ok axiom"],
    "jenson": ["jenson", "hey jenson", "hey good jenson", "jensen"],
    "valta_prime": ["valta prime", "valta", "hey valta", "prime"],
    "yamako": ["yamako", "hey yamako", "hey good yamako"],
}

# Official executive IDs accepted by the voice pipeline.
VALID_EXECUTIVES = ["axiom", "jenson", "valta_prime", "yamako"]

# Workstation mapping (from reference, matches AXIOM's existing mapping)
EXECUTIVE_WORKSTATIONS: Dict[str, str] = {
    "axiom": "os",
    "jenson": "agency",
    "valta_prime": "trading",
    "yamako": "personal",
}

# Moved to CaptureConfig and PipelineConfig classes below

# Entity definitions
@dataclass
class EntityProfile:
    """Voice profile for an entity (Axiom, Jenson, Yamako, or Valta Prime)."""

    name: str
    display_name: str
    wake_phrases: list[str]
    voice_model: str  # Piper voice identifier
    voice_character: str  # Brief character description for clarity
    delegation_capable: bool = False  # Can this entity delegate to others?


ENTITIES = {
    "axiom": EntityProfile(
        name="axiom",
        display_name="Axiom AI",
        wake_phrases=["axiom", "hey axiom", "axiom ai"],
        voice_model="en_GB-bnk-medium",  # High-quality British voice (from reference)
        voice_character="female_british_secret_agent",
        delegation_capable=True,  # Only if AXIOM allows delegation
    ),
    "jenson": EntityProfile(
        name="jenson",
        display_name="Jenson",
        wake_phrases=["jenson", "hey jenson", "hey good jenson"],
        voice_model="en_US-ryan-high",  # Male authoritative US voice (from reference)
        voice_character="male_commanding",
        delegation_capable=False,
    ),
    "yamako": EntityProfile(
        name="yamako",
        display_name="Yamako",
        wake_phrases=["yamako", "hey yamako", "hey good yamako"],
        voice_model="en_US-kristin-medium",  # Female lighter pitch (from reference)
        voice_character="female_flirty_quirky",
        delegation_capable=False,
    ),
    "valtaprime": EntityProfile(
        name="valtaprime",
        display_name="Valta Prime",
        wake_phrases=["valta prime", "hey valta prime", "valta"],
        voice_model="en_US-hfc-medium",  # Male stern/serious tone (from reference)
        voice_character="male_stern_serious",
        delegation_capable=False,
    ),
}

# Keep AXIOM's existing executive wake word mapping for backward compatibility
EXECUTIVE_WAKE_WORDS: Dict[str, List[str]] = {
    "axiom": ["axiom on", "axiom", "hey axiom", "ok axiom"],
    "jenson": ["jenson", "hey jenson", "hey good jenson", "jensen"],
    "valta_prime": ["valta prime", "valta", "hey valta", "prime"],
    "yamako": ["yamako", "hey yamako", "hey good yamako"],
}

VALID_EXECUTIVES = ["axiom", "jenson", "valta_prime", "yamako"]

# Workstation mapping (from reference, matches AXIOM's existing mapping)
EXECUTIVE_WORKSTATIONS: Dict[str, str] = {
    "axiom": "os",
    "jenson": "agency",
    "valta_prime": "trading",
    "yamako": "personal",
}

# Wake word model paths (using reference structure but AXIOM's paths)
WAKEWORD_MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "runtime" / "state" / "models" / "wakeword"


class WakeWordConfig(BaseModel):
    """Configuration for wake word detection."""
    # Confidence threshold for wake word detection (0.0 - 1.0)
    # Reference default: 0.0 (testing) -> AXIOM production: 0.6 (tuned)
    confidence_threshold: float = 0.70  # Keeping AXIOM's existing value as it's already tuned
    # Sample rate for audio capture
    sample_rate: int = 16000
    # Chunk size for processing
    chunk_size: int = 1280  # Keeping AXIOM's existing value
    # Enable/disable wake word detection
    enabled: bool = True
    # Model paths per executive
    model_paths: Dict[str, str] = {
        "axiom": str(WAKEWORD_MODELS_DIR / "axiom.onnx"),
        "jenson": str(WAKEWORD_MODELS_DIR / "jenson.onnx"),
        "valta_prime": str(WAKEWORD_MODELS_DIR / "valta_prime.onnx"),
        "yamako": str(WAKEWORD_MODELS_DIR / "yamako.onnx"),
    }


class STTConfig(BaseModel):
    """Configuration for Speech-to-Text."""
    # Model size: tiny, base, small, medium, large-v3
    # Reference: "small.en" -> AXIOM: keeping "small.en" as it's a good balance
    model_size: str = "small.en"
    # Device: cpu, cuda
    # Reference: "cpu" -> AXIOM: keeping "cpu" for compatibility (can be overridden)
    device: str = "cpu"
    # Compute type: int8, float16, float32
    # Reference: "int8" -> AXIOM: keeping "int8"
    compute_type: str = "int8"
    # Language (None for auto-detect)
    language: Optional[str] = "en"
    # VAD filter for silence detection
    vad_filter: bool = True
    # Beam size for decoding
    beam_size: int = 5
    # Sample rate for audio
    sample_rate: int = 16000


class TTSConfig(BaseModel):
    """Configuration for Text-to-Speech."""
    # Provider: piper, elevenlabs
    # Reference: "piper" -> AXIOM: keeping "piper" as primary
    provider: str = "piper"
    # Piper model directory
    piper_models_dir: str = str(settings.state_dir / "models" / "piper")
    # Sample rate for output
    sample_rate: int = 22050
    # Voice profiles per executive (keeping AXIOM's existing profiles)
    voice_profiles: Dict[str, Dict] = {
        "axiom": {
            "provider": "piper",
            "model": "en_GB-alan-medium",  # British female - will use en_GB voice
            "speaker_id": 0,
            "length_scale": 1.0,
            "noise_scale": 0.667,
            "noise_w": 0.8,
        },
        "jenson": {
            "provider": "piper",
            "model": "en_US-ryan-high",  # Male authoritative
            "speaker_id": 0,
            "length_scale": 1.0,
            "noise_scale": 0.667,
            "noise_w": 0.8,
        },
        "yamako": {
            "provider": "piper",
            "model": "en_US-lessac-high",  # Lighter/brighter female
            "speaker_id": 0,
            "length_scale": 1.1,
            "noise_scale": 0.667,
            "noise_w": 0.8,
        },
        "valta_prime": {
            "provider": "piper",
            "model": "en_US-ryan-low",  # Stern, serious male
            "speaker_id": 0,
            "length_scale": 0.9,
            "noise_scale": 0.667,
            "noise_w": 0.8,
        },
    }
    # ElevenLabs fallback config (optional)
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_ids: Dict[str, str] = {
        "axiom": "",
        "jenson": "",
        "yamako": "",
        "valta_prime": "",
    }


class VADConfig(BaseModel):
    """Configuration for Voice Activity Detection."""
    # VAD engine: "silero" or "webrtcvad"
    # Reference: "silero" -> AXIOM: keeping "silero" as it's more accurate
    engine: str = "silero"
    # Voice activity detection threshold (0.0-1.0)
    # Reference: 0.5 -> AXIOM: keeping 0.5 as it's a good balance
    vad_threshold: float = 0.5
    # Sample rate for audio processing
    sample_rate: int = 16000
    # Silence duration to consider speech ended (seconds)
    # Reference: 0.5 -> AXIOM: keeping 0.5 for responsive voice detection
    silence_duration: float = 0.5


class CaptureConfig(BaseModel):
    """Configuration for audio capture after wake word."""
    # Use VAD to detect end of speech
    use_vad: bool = True
    # VAD aggressiveness (0-3)
    vad_aggressiveness: int = 2
    vad_engine: str = "silero"  # Keeping AXIOM's preference for silero
    # Capture behavior: vad_terminated or fixed_timeout
    capture_behavior: str = "vad_terminated"
    # Fixed timeout for capture (seconds) when capture_behavior is "fixed_timeout"
    capture_fixed_timeout: float = 10.0
    # Minimum capture duration (seconds)
    min_capture_time: float = 1.0
    # Maximum capture duration (seconds)
    max_duration: float = 10.0
    # Minimum capture duration (seconds)
    min_duration: float = 1.0
    # Silence timeout after speech ends (seconds)
    silence_timeout: float = 1.5


class PipelineConfig(BaseModel):
    """Main voice pipeline configuration."""
    wake_word: WakeWordConfig = WakeWordConfig()
    stt: STTConfig = STTConfig()
    tts: TTSConfig = TTSConfig()
    vad: VADConfig = VADConfig()
    capture: CaptureConfig = CaptureConfig()

    # Executive definitions
    executive_wake_words: Dict[str, List[str]] = {
        "axiom": ["axiom on", "axiom", "hey axiom", "ok axiom"],
        "jenson": ["jenson", "hey jenson", "hey good jenson", "jensen"],
        "valta_prime": ["valta prime", "valta", "hey valta", "prime"],
        "yamako": ["yamako", "hey yamako", "hey good yamako"],
    }
    valid_executives: List[str] = ["axiom", "jenson", "valta_prime", "yamako"]
    executive_workstations: Dict[str, str] = {
        "axiom": "os",
        "jenson": "agency",
        "valta_prime": "trading",
        "yamako": "personal",
    }

    # Workstation routing for display output
    workstation_routing: Dict[str, str] = {
        "axiom": "os",
        "jenson": "agency",
        "valta_prime": "trading",
        "yamako": "personal",
    }

    # WebSocket settings
    ws_host: str = "0.0.0.0"
    ws_port: int = 8008  # Keeping AXIOM's existing port to avoid conflict

    # Audio input device (None for default)
    audio_device: Optional[int] = 5  # Keeping AXIOM's existing device setting


class WebSocketConfig(BaseModel):
    """Configuration for WebSocket relay."""
    # Host to bind to
    host: str = "0.0.0.0"
    # Port to listen on
    port: int = 8008
    # Enable/disable WebSocket relay
    enabled: bool = True
    # Authentication token (optional)
    auth_token: Optional[str] = None
    # Allowed origins for CORS
    allowed_origins: List[str] = ["*"]


class IntentRouterConfig(BaseModel):
    """Configuration for intent routing."""
    # Whether Axiom can delegate commands to subordinates
    axiom_delegation_enabled: bool = True
    # Keywords for delegating to each entity
    delegation_keywords: Dict[str, List[str]] = {
        "jenson": ["trade", "trading", "market", "stock", "agency", "agent"],
        "yamako": ["personal", "home", "family", "friend", "social", "date"],
        "valta_prime": ["trading", "stock", "market", "investment", "portfolio", "finance"],
    }


# Global config instance
websocket_config = WebSocketConfig()
vad_config = VADConfig()
stt_config = STTConfig()
intent_router_config = IntentRouterConfig()
wake_word_config = WakeWordConfig()
voice_config = PipelineConfig()