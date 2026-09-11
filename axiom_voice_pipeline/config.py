"""
Configuration for the Axiom Voice Pipeline.

Defines entity profiles, thresholds, model paths, and provider settings.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# Project paths
PROJECT_ROOT = Path(__file__).parent
MODELS_DIR = PROJECT_ROOT / "wakeword" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# ENTITY DEFINITIONS
# ============================================================================

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
        voice_model="en_GB-bnk-medium",  # High-quality British voice
        voice_character="female_british_secret_agent",
        delegation_capable=True,
    ),
    "jenson": EntityProfile(
        name="jenson",
        display_name="Jenson",
        wake_phrases=["jenson", "hey jenson", "hey good jenson"],
        voice_model="en_US-ryan-high",  # Male authoritative US voice
        voice_character="male_commanding",
        delegation_capable=False,
    ),
    "yamako": EntityProfile(
        name="yamako",
        display_name="Yamako",
        wake_phrases=["yamako", "hey yamako", "hey good yamako"],
        voice_model="en_US-kristin-medium",  # Female lighter pitch
        voice_character="female_flirty_quirky",
        delegation_capable=False,
    ),
    "valtaprime": EntityProfile(
        name="valtaprime",
        display_name="Valta Prime",
        wake_phrases=["valta prime", "hey valta prime", "valta"],
        voice_model="en_US-hfc-medium",  # Male stern/serious tone
        voice_character="male_stern_serious",
        delegation_capable=False,
    ),
}

# ============================================================================
# WAKE WORD DETECTION CONFIG
# ============================================================================

@dataclass
class WakeWordConfig:
    """Configuration for wake word detection."""
    
    # Confidence threshold (0.0-1.0). Start at 0.5, tune upward to reduce false positives.
    # For testing, set to 0.0 to accept any detection.
    confidence_threshold: float = 0.0
    
    # Audio capture settings
    sample_rate: int = 16000  # Hz
    channels: int = 1  # Mono
    
    # Enable multi-model concurrent detection
    multi_model_enabled: bool = True
    
    # Model paths for each entity
    model_paths: dict[str, str] = None
    
    def __post_init__(self):
        if self.model_paths is None:
            # Use the hey_jarvis pre-trained model for all entities as a placeholder.
            # Replace with custom trained models (.onnx files) in axiom_voice_pipeline/wakeword/models/ for production.
            self.model_paths = {
                entity: "hey_jarvis"
                for entity in ENTITIES.keys()
            }
wake_word_config = WakeWordConfig()
@dataclass
class VADConfig:
    """Configuration for Voice Activity Detection."""
    
    # VAD engine: "silero" or "webrtcvad". webrtcvad is the default because it
    # has no torch dependency (silero requires PyTorch, which is not installed).
    engine: Literal["silero", "webrtcvad"] = "webrtcvad"
    
    # Silence duration (seconds) before considering speech ended
    silence_duration: float = 1.0
    
    # Sample rate for VAD processing
    sample_rate: int = 16000
    
    # VAD threshold (engine-dependent)
    vad_threshold: float = 0.5
    
    # Minimum speech duration (seconds) to consider as valid input
    min_speech_duration: float = 0.5


vad_config = VADConfig()

# ============================================================================
# SPEECH-TO-TEXT CONFIG
# ============================================================================

@dataclass
class STTConfig:
    """Configuration for Speech-to-Text using faster-whisper."""
    
    # Model size: tiny, base, small, medium, large-v3. "small.en" matches the
    # proven backend reference and avoids a multi-GB download on CPU.
    model_size: str = "small.en"

    # Use only English language model (faster)
    language: str = "en"

    # Enable GPU if available
    device: str = "cpu"  # "auto" | "cpu" | "cuda"

    # Compute type for quantization
    compute_type: str = "int8"  # "auto" | "default" | "int8" | "float16" | "float32"
    
    # Temperature for sampling (0.0-1.0)
    temperature: float = 0.0  # Lower = more deterministic


stt_config = STTConfig()

# ============================================================================
# TEXT-TO-SPEECH CONFIG
# ============================================================================

@dataclass
class TTSConfig:
    """Configuration for Text-to-Speech synthesis."""
    
    # Primary provider: "piper" or "elevenlabs"
    primary_provider: str = "piper"
    
    # Fallback provider for when primary is unavailable
    fallback_provider: str = "piper"
    
    # Sample rate for synthesized audio
    sample_rate: int = 22050
    
    # Piper-specific settings
    piper_enable_gpu: bool = False  # Piper typically runs on CPU

    # Directory holding Piper .onnx voice models (named <voice_id>.onnx)
    piper_models_dir: str = str(PROJECT_ROOT / "tts" / "models")
    
    # ElevenLabs settings (future/optional)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_stability: float = 0.5  # 0.0-1.0
    elevenlabs_voice_similarity_boost: float = 0.75  # 0.0-1.0


tts_config = TTSConfig()

# ============================================================================
# INTENT ROUTER CONFIG
# ============================================================================

@dataclass
class IntentRouterConfig:
    """Configuration for intent routing."""
    
    # Enable Axiom delegation logic when Axiom is the wake entity
    axiom_delegation_enabled: bool = True
    
    # Delegation phrases that trigger specific entity routing
    delegation_keywords: dict[str, list[str]] = None
    
    def __post_init__(self):
        if self.delegation_keywords is None:
            self.delegation_keywords = {
                "jenson": ["agency", "bleval", "client", "campaign", "project"],
                "valtaprime": ["trading", "trades", "market", "portfolio", "investment"],
                "yamako": ["personal", "schedule", "reminder", "calendar", "daily"],
            }


intent_router_config = IntentRouterConfig()

# ============================================================================
# WEBSOCKET RELAY CONFIG
# ============================================================================

@dataclass
class WebSocketConfig:
    """Configuration for WebSocket relay server."""
    
    # Server host and port
    host: str = "127.0.0.1"
    port: int = 8002
    
    # Connection settings
    ping_interval: float = 30.0  # seconds
    ping_timeout: float = 10.0  # seconds
    
    # Enable compression for audio data
    enable_compression: bool = True


websocket_config = WebSocketConfig()

# ============================================================================
# WORKSTATION ROUTING
# ============================================================================

# Maps entities to their designated workstations
WORKSTATION_ROUTING = {
    "axiom": "os",
    "jenson": "agency",
    "yamako": "personal",
    "valtaprime": "trading",
}

# ============================================================================
# CAPTURE WINDOW BEHAVIOR
# ============================================================================

# Use VAD-terminated capture window (recommended)
CAPTURE_BEHAVIOR = "vad_terminated"  # "vad_terminated" | "fixed_timeout"

# Fixed timeout fallback (seconds) if VAD doesn't work
CAPTURE_FIXED_TIMEOUT = 10.0

# Minimum time to listen after wake word (seconds)
MIN_CAPTURE_TIME = 0.5
