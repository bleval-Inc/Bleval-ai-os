"""Wake word detection using openWakeWord."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from axiom.voice.config import voice_config, EXECUTIVE_WAKE_WORDS, VALID_EXECUTIVES

logger = logging.getLogger("axiom.voice.wakeword.detector")


class WakeWordDetector:
    """
    Multi-model wake word detector using openWakeWord.
    
    Runs 4 models concurrently (one per executive) against the same live
    mic stream. On detection, emits an event with the executive ID and confidence.
    """
    
    def __init__(
        self,
        config: Optional[Any] = None,
        on_wake: Optional[Callable[[str, float, str], None]] = None,
    ):
        self.config = config or voice_config.wake_word
        self.on_wake = on_wake
        self._models: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._audio_stream = None
        self._sample_rate = self.config.sample_rate
        self._chunk_size = self.config.chunk_size
        
    def load_models(self) -> bool:
        """Load all wake word models."""
        try:
            import openwakeword
            from openwakeword.model import Model
        except ImportError:
            logger.error("openWakeWord not installed. Install with: pip install openwakeword")
            return False
            
        loaded_count = 0
        
        # First, try to load custom verifier models
        for exec_id in VALID_EXECUTIVES:
            model_path = self.config.model_paths.get(exec_id)
            if model_path and Path(model_path).exists():
                try:
                    model = Model(
                        wakeword_models=[model_path],
                        inference_framework="onnx",
                    )
                    self._models[exec_id] = model
                    logger.info(f"Loaded custom wake word model for {exec_id}: {model_path}")
                    loaded_count += 1
                except Exception as e:
                    logger.error(f"Failed to load custom wake word model for {exec_id}: {e}")
        
        # If no custom models loaded, fall back to base openWakeWord models
        if loaded_count == 0:
            logger.info("No custom wake word models found, using base openWakeWord models")
            # Use the model from our local models directory
            base_model_path = str(Path(__file__).parent.parent.parent.parent / "runtime" / "state" / "models" / "wakeword" / "hey_jarvis_v0.1.onnx")
            if not Path(base_model_path).exists():
                # Fallback to openwakeword's default location
                base_model_path = "hey_jarvis"
            
            base_models = {
                "axiom": base_model_path,
                "jenson": base_model_path, 
                "valta_prime": base_model_path,
                "yamako": base_model_path,
            }
            
            for exec_id, model_name in base_models.items():
                try:
                    model = Model(
                        wakeword_models=[model_name],
                        inference_framework="onnx",
                    )
                    self._models[exec_id] = model
                    logger.info(f"Loaded base wake word model for {exec_id}: {model_name}")
                    loaded_count += 1
                except Exception as e:
                    logger.error(f"Failed to load base wake word model for {exec_id}: {e}")
        
        logger.info(f"Loaded {loaded_count}/{len(VALID_EXECUTIVES)} wake word models")
        return loaded_count > 0
    
    def start(self, audio_stream: Any = None) -> bool:
        """Start the wake word detection loop."""
        if self._running:
            logger.warning("Wake word detector already running")
            return True
            
        if not self._models:
            if not self.load_models():
                logger.error("No wake word models loaded")
                return False
        
        self._audio_stream = audio_stream
        self._running = True
        self._thread = threading.Thread(target=self._detection_loop, daemon=True)
        self._thread.start()
        logger.info("Wake word detector started")
        return True
    
    def stop(self) -> None:
        """Stop the wake word detection loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._audio_stream:
            try:
                self._audio_stream.stop()
                self._audio_stream.close()
            except Exception:
                pass
        logger.info("Wake word detector stopped")
    
    def _detection_loop(self) -> None:
        """Main detection loop - processes audio chunks through all models."""
        import sounddevice as sd
        
        # If no audio stream provided, create one
        stream = self._audio_stream
        if stream is None:
            try:
                stream = sd.InputStream(
                    samplerate=self._sample_rate,
                    channels=1,
                    dtype="float32",
                    blocksize=self._chunk_size,
                    device=voice_config.audio_device,
                )
                stream.start()
                self._audio_stream = stream
            except Exception as e:
                logger.error(f"Failed to open audio stream: {e}")
                self._running = False
                return
        
        logger.info("Wake word detection loop running")
        
        while self._running:
            try:
                # Read audio chunk
                audio_data, overflowed = stream.read(self._chunk_size)
                if overflowed:
                    logger.debug("Audio buffer overflow")
                
                # Convert to format expected by openWakeWord (int16)
                audio_int16 = (audio_data.flatten() * 32767).astype(np.int16)
                
                # Run inference on all models
                for exec_id, model in self._models.items():
                    try:
                        prediction = model.predict(audio_int16)
                        # prediction is a dict with model names as keys
                        for model_name, score in prediction.items():
                            if score >= self.config.confidence_threshold:
                                wake_word = self._get_triggered_wake_word(exec_id, model_name)
                                logger.info(
                                    f"Wake word detected: {exec_id} ({wake_word}) "
                                    f"confidence={score:.3f}"
                                )
                                if self.on_wake:
                                    self.on_wake(exec_id, score, wake_word)
                                # Brief pause to avoid repeated triggers
                                time.sleep(0.5)
                                break
                    except Exception as e:
                        logger.debug(f"Model inference error for {exec_id}: {e}")
                        
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
                time.sleep(0.1)
    
    def _get_triggered_wake_word(self, exec_id: str, model_name: str) -> str:
        """Map model output to wake word phrase."""
        # openWakeWord model names might be different from our phrases
        # Return the primary wake word for this executive
        return EXECUTIVE_WAKE_WORDS.get(exec_id, [exec_id])[0]


class MockWakeWordDetector:
    """
    Mock detector for testing without hardware/models.
    Simulates wake word detection after a configurable delay.
    """
    
    def __init__(
        self,
        config: Optional[Any] = None,
        on_wake: Optional[Callable[[str, float, str], None]] = None,
    ):
        self.config = config or voice_config.wake_word
        self.on_wake = on_wake
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
    def load_models(self) -> bool:
        logger.info("Mock wake word detector: models 'loaded'")
        return True
    
    def start(self, audio_stream: Any = None) -> bool:
        if self._running:
            return True
        self._running = True
        self._thread = threading.Thread(target=self._mock_loop, daemon=True)
        self._thread.start()
        logger.info("Mock wake word detector started")
        return True
    
    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        logger.info("Mock wake word detector stopped")
    
    def _mock_loop(self) -> None:
        """Simulate wake word detection every 30 seconds for testing."""
        import random
        executives = list(VALID_EXECUTIVES)
        while self._running:
            time.sleep(30)  # Wait 30 seconds between simulated detections
            if not self._running:
                break
            exec_id = random.choice(executives)
            wake_word = EXECUTIVE_WAKE_WORDS[exec_id][0]
            confidence = random.uniform(0.6, 0.95)
            logger.info(f"[MOCK] Wake word: {exec_id} ({wake_word}) confidence={confidence:.3f}")
            if self.on_wake:
                self.on_wake(exec_id, confidence, wake_word)


def create_wake_word_detector(
    use_mock: bool = False,
    on_wake: Optional[Callable[[str, float, str], None]] = None,
) -> WakeWordDetector | MockWakeWordDetector:
    """Factory function to create the appropriate detector."""
    if use_mock:
        return MockWakeWordDetector(on_wake=on_wake)
    return WakeWordDetector(on_wake=on_wake)