import sys
import numpy as np
import asyncio
sys.path.append('C:\\Users\\byagi\\Desktop\\Bleval-ai-os')
from axiom_voice_pipeline.wakeword.detector import WakeWordDetector
from axiom_voice_pipeline.config import wake_word_config

def test_detection_scores():
    """Test what scores we get for different audio inputs."""
    print("Initializing wake word detector...")
    detector = WakeWordDetector()
    print(f"Loaded entities: {detector.get_loaded_entities()}")
    
    # Create test audio buffers (silence, then simulated speech)
    sample_rate = wake_word_config.sample_rate
    duration = 1.0  # seconds
    samples = int(sample_rate * duration)
    
    # Test 1: Silence
    print("\nTest 1: Silence")
    silence = np.zeros(samples, dtype=np.int16)
    result = detector.detect_from_audio(silence.tobytes())
    print(f"Detection result: {result}")
    
    # Test 2: Simulate audio that might trigger hey_jarvis
    # We'll use a simple sine wave at a frequency that might resemble speech
    print("\nTest 2: Sine wave audio")
    t = np.linspace(0, duration, samples, False)
    # Frequency around 100-300 Hz for speech-like tone
    tone = np.sin(2 * np.pi * 200 * t) * 0.3
    audio_int16 = (tone * 32767).astype(np.int16)
    result = detector.detect_from_audio(audio_int16.tobytes())
    print(f"Detection result: {result}")
    
    # Show model paths being used
    print("\nModel paths in use:")
    for entity, path in detector.config.model_paths.items():
        print(f"  {entity}: {path}")

if __name__ == "__main__":
    test_detection_scores()