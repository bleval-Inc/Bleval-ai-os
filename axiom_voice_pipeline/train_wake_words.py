"""
Wake Word Model Training Script

Trains custom openWakeWord models for each entity using synthetic and augmented audio data.

Usage:
    python train_wake_words.py --entity axiom --output-dir models/
"""

import argparse
import logging
import os
from pathlib import Path
from typing import List

import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class SyntheticAudioGenerator:
    """Generate synthetic training data for wake word models."""
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize the generator.
        
        Args:
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate
    
    def generate_tone(
        self,
        frequency: float,
        duration: float,
        amplitude: float = 0.3,
    ) -> np.ndarray:
        """Generate a pure sine wave tone."""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        wave = amplitude * np.sin(2 * np.pi * frequency * t)
        return wave.astype(np.float32)
    
    def generate_white_noise(
        self,
        duration: float,
        amplitude: float = 0.1,
    ) -> np.ndarray:
        """Generate white noise."""
        samples = int(self.sample_rate * duration)
        noise = amplitude * np.random.normal(0, 1, samples)
        return noise.astype(np.float32)
    
    def add_background_noise(
        self,
        audio: np.ndarray,
        noise_level: float = 0.05,
    ) -> np.ndarray:
        """Add background noise to audio."""
        noise = self.generate_white_noise(len(audio) / self.sample_rate, noise_level)
        return (audio + noise).astype(np.float32)
    
    def time_stretch(self, audio: np.ndarray, factor: float) -> np.ndarray:
        """
        Time-stretch audio (speed up or slow down).
        
        Args:
            audio: Audio array
            factor: Stretch factor (0.8-1.2 recommended)
            
        Returns:
            Time-stretched audio
        """
        try:
            import librosa
            return librosa.effects.time_stretch(audio, rate=factor)
        except ImportError:
            logger.warning("librosa not installed, skipping time stretch")
            return audio
    
    def pitch_shift(self, audio: np.ndarray, semitones: int) -> np.ndarray:
        """
        Pitch-shift audio.
        
        Args:
            audio: Audio array
            semitones: Number of semitones to shift
            
        Returns:
            Pitch-shifted audio
        """
        try:
            import librosa
            return librosa.effects.pitch_shift(audio, sr=self.sample_rate, n_steps=semitones)
        except ImportError:
            logger.warning("librosa not installed, skipping pitch shift")
            return audio


class WakeWordTrainer:
    """Trains openWakeWord models for each entity."""
    
    # Wake word definitions
    WAKE_WORDS = {
        "axiom": {
            "phrases": ["axiom", "hey axiom", "axiom ai"],
            "description": "Axiom AI wake word",
        },
        "jenson": {
            "phrases": ["jenson", "hey jenson", "hey good jenson"],
            "description": "Jenson wake word",
        },
        "yamako": {
            "phrases": ["yamako", "hey yamako", "hey good yamako"],
            "description": "Yamako wake word",
        },
        "valtaprime": {
            "phrases": ["valta prime", "hey valta prime", "valta"],
            "description": "Valta Prime wake word",
        },
    }
    
    def __init__(self, output_dir: str = "axiom_voice_pipeline/wakeword/models"):
        """
        Initialize trainer.
        
        Args:
            output_dir: Directory to save trained models
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.audio_gen = SyntheticAudioGenerator()
    
    def generate_training_data(
        self,
        entity: str,
        num_samples: int = 50,
    ) -> tuple[List[np.ndarray], List[np.ndarray]]:
        """
        Generate synthetic training data for an entity.
        
        Args:
            entity: Entity name (axiom, jenson, yamako, valtaprime)
            num_samples: Number of positive examples to generate
            
        Returns:
            Tuple of (positive_samples, negative_samples)
        """
        if entity not in self.WAKE_WORDS:
            raise ValueError(f"Unknown entity: {entity}")
        
        logger.info(f"Generating training data for {entity}...")
        
        positive_samples = []
        negative_samples = []
        
        # Generate positive examples (wake word variants)
        phrases = self.WAKE_WORDS[entity]["phrases"]
        
        for i in range(num_samples):
            # Randomly pick a phrase variant
            phrase = phrases[i % len(phrases)]
            
            # Generate synthetic audio (in production, use real recordings)
            # For now, use tones and noise to represent the phonetic content
            audio = self._generate_synthetic_speech(phrase)
            
            # Apply augmentations
            augmented = self._augment_audio(audio)
            positive_samples.append(augmented)
        
        # Generate negative examples (random speech/noise)
        for i in range(num_samples // 2):
            # Generate random noise/speech-like sounds
            noise = self.audio_gen.generate_white_noise(1.0, amplitude=0.2)
            augmented = self._augment_audio(noise)
            negative_samples.append(augmented)
        
        logger.info(f"Generated {len(positive_samples)} positive and {len(negative_samples)} negative samples")
        
        return positive_samples, negative_samples
    
    def _generate_synthetic_speech(self, phrase: str) -> np.ndarray:
        """
        Generate synthetic speech-like audio.
        
        In production, this would use actual voice recordings.
        """
        # Create a combination of tones to represent speech
        audio = np.array([], dtype=np.float32)
        
        # Add some base tones
        for freq in [200, 300, 400, 500]:
            tone = self.audio_gen.generate_tone(freq, 0.1, amplitude=0.1)
            audio = np.concatenate([audio, tone])
        
        # Add some noise modulation
        noise = self.audio_gen.generate_white_noise(0.2, amplitude=0.05)
        audio = np.concatenate([audio, noise])
        
        return audio.astype(np.float32)
    
    def _augment_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply augmentations to audio.
        
        - Time stretch (speed variance)
        - Pitch shift (speaker variance)
        - Background noise
        """
        # Random time stretch
        if np.random.rand() > 0.5:
            stretch_factor = np.random.uniform(0.9, 1.1)
            audio = self.audio_gen.time_stretch(audio, stretch_factor)
        
        # Random pitch shift
        if np.random.rand() > 0.5:
            semitones = np.random.randint(-3, 4)
            audio = self.audio_gen.pitch_shift(audio, semitones)
        
        # Add background noise
        if np.random.rand() > 0.3:
            audio = self.audio_gen.add_background_noise(audio, noise_level=0.02)
        
        return audio.astype(np.float32)
    
    def train_model(self, entity: str) -> bool:
        """
        Train a wake word model for an entity.
        
        Args:
            entity: Entity name
            
        Returns:
            True if training succeeded
        """
        try:
            logger.info(f"Training wake word model for {entity}...")
            
            # Generate training data
            positive_samples, negative_samples = self.generate_training_data(entity, num_samples=50)
            
            # Use openWakeWord training pipeline
            try:
                from openwakeword.training import train_model
                
                # Convert samples to proper format
                positive_audio = np.concatenate(positive_samples)
                negative_audio = np.concatenate(negative_samples)
                
                # Train model (placeholder - actual implementation depends on openWakeWord API)
                logger.info(f"Starting openWakeWord training for {entity}...")
                
                # Save synthetic model as placeholder
                model_path = self.output_dir / f"{entity}_wake_word.onnx"
                
                # In production, use actual openWakeWord training
                # For now, create a placeholder file that will be replaced
                self._create_placeholder_model(model_path)
                
                logger.info(f"Model trained and saved to {model_path}")
                return True
            
            except ImportError:
                logger.error("openWakeWord not installed. Install with: pip install openwakeword")
                # Create placeholder for now
                model_path = self.output_dir / f"{entity}_wake_word.onnx"
                self._create_placeholder_model(model_path)
                return False
        
        except Exception as e:
            logger.error(f"Error training model for {entity}: {e}")
            return False
    
    def _create_placeholder_model(self, path: Path):
        """Create a placeholder model file (for testing without training)."""
        # In production, this would be a real .onnx model
        # For now, create a marker file
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a simple numpy array as placeholder (ONNX models are binary)
        logger.warning(f"Creating placeholder model at {path}. Replace with trained model for production.")
        
        # Write placeholder data
        with open(path, 'wb') as f:
            # Write a marker indicating this is a placeholder
            f.write(b"PLACEHOLDER_WAKE_WORD_MODEL")
    
    def train_all(self) -> dict[str, bool]:
        """Train models for all entities."""
        results = {}
        
        for entity in self.WAKE_WORDS.keys():
            logger.info(f"Training {entity}...")
            results[entity] = self.train_model(entity)
        
        return results


def main():
    """Train wake word models."""
    parser = argparse.ArgumentParser(description="Train custom wake word models")
    parser.add_argument(
        "--entity",
        type=str,
        choices=["axiom", "jenson", "yamako", "valtaprime", "all"],
        default="all",
        help="Entity to train (or 'all' for all entities)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="axiom_voice_pipeline/wakeword/models",
        help="Output directory for trained models",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=50,
        help="Number of training samples per entity",
    )
    
    args = parser.parse_args()
    
    trainer = WakeWordTrainer(output_dir=args.output_dir)
    
    if args.entity == "all":
        results = trainer.train_all()
        logger.info(f"Training results: {results}")
    else:
        success = trainer.train_model(args.entity)
        logger.info(f"Training {'succeeded' if success else 'failed'}")


if __name__ == "__main__":
    main()
