"""Voice pipeline configuration for Axiom OS."""

from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel
from axiom.config import settings


# Executive wake word configuration
EXECUTIVE_WAKE_WORDS: Dict[str, List[str]] = {
    "axiom": ["axiom on", "axiom", "hey axiom", "ok axiom"],
    "jenson": ["jenson", "hey jenson", "hey good jenson", "jensen"],
    "valta_prime": ["valta prime", "valta", "hey valta", "prime"],
    "yamako": ["yamako", "hey yamako", "hey good yamako"],
}

VALID_EXECUTIVES = ["axiom", "jenson", "valta_prime", "yamako"]

# Workstation mapping
EXECUTIVE_WORKSTATIONS: Dict[str, str] = {
    "axiom": "os",
    "jenson": "agency",
    "valta_prime": "trading",
    "yamako": "personal",
}

# Wake word model paths (trained .onnx models)
WAKEWORD_MODELS_DIR = settings.state_dir / "models" / "wakeword"

class WakeWordConfig(BaseModel):
    """Configuration for wake word detection."""
    # Confidence threshold for wake word detection (0.0 - 1.0)
    confidence_threshold: float = 0.5
    # Sample rate for audio capture
    sample_rate: int = 16000
    # Chunk size for processing
    chunk_size: int = 1280
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
    model_size: str = "small.en"
    # Device: cpu, cuda
    device: str = "cpu"
    # Compute type: int8, float16, float32
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
    provider: str = "piper"
    # Piper model directory
    piper_models_dir: str = str(settings.state_dir / "models" / "piper")
    # Sample rate for output
    sample_rate: int = 22050
    # Voice profiles per executive
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


class CaptureConfig(BaseModel):
    """Configuration for audio capture after wake word."""
    # Use VAD to detect end of speech
    use_vad: bool = True
    # VAD aggressiveness (0-3)
    vad_aggressiveness: int = 2
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
    capture: CaptureConfig = CaptureConfig()
    
    # WebSocket settings
    ws_host: str = "0.0.0.0"
    ws_port: int = 8000
    
    # Audio input device (None for default)
    audio_device: Optional[str] = None


# Global config instance
voice_config = PipelineConfig()