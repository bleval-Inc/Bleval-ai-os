import sys
import numpy as np
sys.path.append('C:\\Users\\byagi\\Desktop\\Bleval-ai-os')
from axiom_voice_pipeline.wakeword.detector import WakeWordDetector

def test_detector():
    print("Initializing WakeWordDetector...")
    detector = WakeWordDetector()
    print(f"Loaded entities: {detector.get_loaded_entities()}")
    print(f"Number of loaded models: {len(detector.models)}")
    
    # Create a silent audio chunk (16-bit, mono, 16kHz, 0.1 seconds)
    duration = 0.1  # seconds
    sample_rate = 16000
    num_samples = int(duration * sample_rate)
    silent_audio = np.zeros(num_samples, dtype=np.int16)
    silent_bytes = silent_audio.tobytes()
    
    print("\nTesting with silence...")
    prediction = detector.detect_from_audio(silent_bytes)
    print(f"Prediction: {prediction}")
    
    # Create a random noise audio chunk
    noisy_audio = np.random.randint(-32768, 32767, size=num_samples, dtype=np.int16)
    noisy_bytes = noisy_audio.tobytes()
    
    print("\nTesting with random noise...")
    prediction = detector.detect_from_audio(noisy_bytes)
    print(f"Prediction: {prediction}")
    
    # Test health check
    print("\nRunning health check...")
    health = detector.health_check()
    print(f"Health: {health}")
    
    return detector

if __name__ == "__main__":
    test_detector()