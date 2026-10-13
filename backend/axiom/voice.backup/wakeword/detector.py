"""
Wake word detection using openWakeWord.

Supports multi-model concurrent detection with confidence thresholding.
"""

import logging
from typing import Optional

try:
    from openwakeword.model import Model
except ImportError:
    Model = None  # openWakeWord unavailable; wake word detection degrades to a no-op

from ..config import ENTITIES, WakeWordConfig, wake_word_config
from ..models import WakeWordDetection

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    Detects wake words using openWakeWord models.
    
    Supports concurrent multi-model detection against a live audio stream.
    Each entity has its own trained model that recognizes multiple phrase variants.
    """
    
    def __init__(self, config: WakeWordConfig = None):
        """
        Initialize the wake word detector.
        
        Args:
            config: WakeWordConfig instance. If None, uses global wake_word_config.
        """
        self.config = config or wake_word_config
        self.models: dict[str, Model] = {}
        self._load_models()
    
    def _load_models(self):
        """Load all entity wake word models."""
        logger.info("Loading wake word models...")
        
        for entity_name, entity_profile in ENTITIES.items():
            model_path = self.config.model_paths.get(entity_name)
            
            if not model_path:
                logger.warning(f"No model path configured for entity '{entity_name}'")
                continue
            
            try:
                # In a real deployment, these would be custom-trained .onnx models.
                # For now, use openWakeWord's built-in models or provide a fallback.
                # This will be replaced with actual trained models.
                model = self._load_model(entity_name, model_path)
                if model:
                    self.models[entity_name] = model
                    logger.info(f"Loaded wake word model for '{entity_name}'")
            except Exception as e:
                logger.error(f"Failed to load wake word model for '{entity_name}': {e}")
    
    def _load_model(self, entity_name: str, model_path: str) -> Optional[Model]:
            """
            Load a wake word model from a path.
        
            Args:
                entity_name: Name of the entity (axiom, jenson, yamako, valtaprime)
                model_path: Path to the .onnx model file or pre-trained model name
            
            Returns:
                Loaded Model instance or None if loading fails.
            """
            try:
                # openWakeWord loads models from a list of paths (no from_file API).
                # If model_path is a pre-trained model name (e.g., 'hey_jarvis'), it will be resolved automatically.
                model = Model(
                                    wakeword_models=[model_path],
                                    inference_framework="onnx",
                                )
                return model
            except FileNotFoundError:
                # Model file doesn't exist yet - this is expected during setup
                logger.debug(f"Model file not found at {model_path}. Will use placeholder.")
                # Return a placeholder that can be trained later
                return None
            except Exception as e:
                logger.error(f"Error loading model from {model_path}: {e}")
                return None
    
    def detect_from_audio(self, audio_chunk: bytes) -> Optional[WakeWordDetection]:
            """
            Detect wake words from an audio chunk.

            Runs all loaded models concurrently and returns the highest-confidence detection
            that exceeds the configured threshold.

            Args:
                audio_chunk: Raw audio bytes (PCM, 16-bit, mono, 16kHz)

            Returns:
                WakeWordDetection if a wake word is detected and exceeds threshold, else None
            """
            if not self.models:
                logger.warning("No wake word models loaded")
                return None

            # Convert audio bytes to numpy array of int16 samples
            import numpy as np
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16)

            best_detection = None
            best_confidence = -1.0  # Initialize to -1 so that any score >=0 will be considered

            # Run all models concurrently (simplified synchronous version here)
            for entity_name, model in self.models.items():
                try:
                    # Get the model's prediction on this audio chunk
                    prediction = model.predict(audio_np)

                    # prediction is typically a dict like {"some_entity_wake_word": score}
                    # Extract the highest score for this model
                    if isinstance(prediction, dict):
                        score = max(prediction.values()) if prediction else 0.0
                    else:
                        score = float(prediction) if prediction else 0.0

                    logger.debug(f"Model {entity_name} prediction: {prediction}, score: {score}")

                    # Track the best detection across all models
                    if score > best_confidence and score >= self.config.confidence_threshold:
                        best_confidence = score
                        best_detection = WakeWordDetection(
                            wake_entity=entity_name,
                            confidence=score
                        )
                except Exception as e:
                    logger.error(f"Error predicting with model for '{entity_name}': {e}")
                    continue

            return best_detection
    def get_loaded_entities(self) -> list[str]:
        """
        Get list of entities with successfully loaded wake word models.
        
        Returns:
            List of entity names that have models ready
        """
        return list(self.models.keys())
    
    def health_check(self) -> dict[str, bool]:
        """
        Check health of all loaded models.
        
        Returns:
            Dict mapping entity names to model availability
        """
        return {entity: entity in self.models for entity in ENTITIES.keys()}
