"""Piper TTS provider implementation."""

from __future__ import annotations

import logging
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from axiom.voice.tts.provider_base import TTSProvider, VoiceProfile, tts_registry
from axiom.voice.config import voice_config

logger = logging.getLogger("axiom.voice.tts.piper_provider")


class PiperTTS(TTSProvider):
    """Piper TTS provider for local, offline speech synthesis."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.models_dir = Path(config.get("models_dir", voice_config.tts.piper_models_dir))
        self._piper_bin = config.get("piper_bin", "piper")
        self._model_cache: Dict[str, Path] = {}
        self._lock = threading.Lock()
        
    @property
    def name(self) -> str:
        return "piper"
    
    def initialize(self) -> bool:
        """Check if Piper is available and models exist."""
        try:
            # Check if piper binary exists
            result = subprocess.run(
                [self._piper_bin, "--help"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode != 0:
                logger.error("Piper binary not found or not executable")
                return False
            
            # Check models directory
            if not self.models_dir.exists():
                logger.warning(f"Piper models directory not found: {self.models_dir}")
                self.models_dir.mkdir(parents=True, exist_ok=True)
            
            # Scan for available models
            self._scan_models()
            
            self._initialized = True
            logger.info(f"Piper TTS initialized with {len(self._model_cache)} models")
            return True
            
        except FileNotFoundError:
            logger.error("Piper not installed. Install with: pip install piper-tts")
            return False
        except Exception as e:
            logger.error(f"Piper initialization failed: {e}")
            return False
    
    def _scan_models(self) -> None:
        """Scan models directory for available .onnx models."""
        self._model_cache.clear()
        for model_file in self.models_dir.glob("*.onnx"):
            model_name = model_file.stem
            self._model_cache[model_name] = model_file
            # Also check for .json config
            json_file = model_file.with_suffix(".onnx.json")
            if json_file.exists():
                self._model_cache[f"{model_name}.json"] = json_file
    
    def is_available(self) -> bool:
        return self._initialized
    
    def get_model_path(self, model_name: str) -> Optional[Path]:
        """Get the path to a model file."""
        with self._lock:
            return self._model_cache.get(model_name)
    
    def synthesize(self, text: str, voice_profile: VoiceProfile) -> bytes:
        """
        Synthesize text to speech using Piper.
        
        Args:
            text: Text to synthesize
            voice_profile: Voice profile with model and parameters
            
        Returns:
            WAV audio data as bytes
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("Piper TTS not initialized")
        
        model_name = voice_profile.model
        model_path = self.get_model_path(model_name)
        
        if not model_path:
            # Try to find a matching model
            available = list(self._model_cache.keys())
            logger.warning(f"Model '{model_name}' not found. Available: {available}")
            # Fallback to first available model
            if available:
                model_path = self._model_cache[available[0]]
                logger.info(f"Using fallback model: {available[0]}")
            else:
                raise RuntimeError(f"No Piper models available in {self.models_dir}")
        
        # Create temp output file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = tmp.name
        
        try:
            # Build piper command
            cmd = [
                self._piper_bin,
                "--model", str(model_path),
                "--output_file", output_path,
            ]
            
            # Add speaker ID if multi-speaker model
            if voice_profile.speaker_id > 0:
                cmd.extend(["--speaker", str(voice_profile.speaker_id)])
            
            # Add synthesis parameters
            cmd.extend([
                "--length_scale", str(voice_profile.length_scale),
                "--noise_scale", str(voice_profile.noise_scale),
                "--noise_w", str(voice_profile.noise_w),
            ])
            
            # Add extra config if provided
            for key, value in voice_profile.extra.items():
                if key not in ["length_scale", "noise_scale", "noise_w", "speaker_id"]:
                    cmd.extend([f"--{key}", str(value)])
            
            # Run piper with text input
            logger.debug(f"Running Piper: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode("utf-8", errors="replace")
                logger.error(f"Piper synthesis failed: {error_msg}")
                raise RuntimeError(f"Piper synthesis failed: {error_msg}")
            
            # Read output file
            with open(output_path, "rb") as f:
                audio_data = f.read()
            
            logger.info(f"Piper synthesized {len(text)} chars -> {len(audio_data)} bytes")
            return audio_data
            
        finally:
            # Cleanup temp file
            try:
                Path(output_path).unlink(missing_ok=True)
            except Exception:
                pass
    
    def synthesize_streaming(
        self,
        text: str,
        voice_profile: VoiceProfile,
        chunk_callback: callable,
    ) -> None:
        """
        Synthesize with streaming output (for real-time playback).
        
        Note: Piper doesn't natively support streaming, so this simulates
        it by synthesizing full audio and yielding chunks.
        """
        audio_data = self.synthesize(text, voice_profile)
        
        # Parse WAV header to get sample rate and format
        import wave
        import io
        
        with wave.open(io.BytesIO(audio_data), "rb") as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            frames = wf.readframes(wf.getnframes())
        
        # Yield chunks (e.g., 100ms at a time)
        chunk_size = int(sample_rate * channels * sample_width * 0.1)
        for i in range(0, len(frames), chunk_size):
            chunk = frames[i:i + chunk_size]
            chunk_callback(chunk)


def download_piper_model(model_name: str, models_dir: Path) -> bool:
    """
    Download a Piper model from the official repository.
    
    Args:
        model_name: Model identifier (e.g., "en_US-lessac-medium")
        models_dir: Directory to save model
        
    Returns:
        True if successful
    """
    import urllib.request
    import json
    
    base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
    
    try:
        # Try to get model info from voices.json
        voices_url = f"{base_url}/voices.json"
        with urllib.request.urlopen(voices_url) as response:
            voices = json.load(response)
        
        if model_name not in voices:
            logger.error(f"Model {model_name} not found in voices catalog")
            return False
        
        model_info = voices[model_name]
        files = model_info.get("files", [])
        
        models_dir.mkdir(parents=True, exist_ok=True)
        
        for file_info in files:
            file_url = f"{base_url}/{model_name}/{file_info['name']}"
            dest_path = models_dir / file_info["name"]
            
            if dest_path.exists():
                logger.info(f"Model file already exists: {dest_path}")
                continue
            
            logger.info(f"Downloading {file_info['name']}...")
            urllib.request.urlretrieve(file_url, dest_path)
            logger.info(f"Downloaded to {dest_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to download model {model_name}: {e}")
        return False


# Register Piper provider
piper_provider = PiperTTS({
    "models_dir": str(voice_config.tts.piper_models_dir),
})
tts_registry.register(piper_provider)