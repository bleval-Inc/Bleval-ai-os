import sys
import numpy as np
sys.path.append('C:\\Users\\byagi\\Desktop\\Bleval-ai-os')
from axiom_voice_pipeline.wakeword.detector import WakeWordDetector
from axiom_voice_pipeline.config import WakeWordConfig

def test_detection_with_low_threshold():
    """Test detection with a very low confidence threshold to see if we get any response."""
    print("Initializing wake word detector with low threshold...")
    # Create a custom config with low threshold
    config = WakeWordConfig()
    config.confidence_threshold = 0.0  # Set to 0.0 to accept any detection
    detector = WakeWordDetector(config=config)
    print(f"Loaded entities: {detector.get_loaded_entities()}")
    print(f"Confidence threshold: {detector.config.confidence_threshold}")
    
    # Create test audio buffers (silence, then simulated speech)
    sample_rate = config.sample_rate
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
    
    # Test 3: Try a slightly more complex signal (white noise)
    print("\nTest 3: White noise")
    noise = np.random.randint(-32768, 32767, size=samples, dtype=np.int16)
    result = detector.detect_from_audio(noise.tobytes())
    print(f"Detection result: {result}")

if __name__ == "__main__":
    test_detection_with_low_threshold()