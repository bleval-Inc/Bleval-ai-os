import sys
import numpy as np
sys.path.append('C:\\Users\\byagi\\Desktop\\Bleval-ai-os')
from axiom_voice_pipeline.wakeword.detector import WakeWordDetector

def test_detector_raw():
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
    
    # Create a random noise audio chunk
    noisy_audio = np.random.randint(-32768, 32767, size=num_samples, dtype=np.int16)
    noisy_bytes = noisy_audio.tobytes()
    
    # We'll also try a chunk that might resemble a wake word? Not available.
    # Instead, let's directly call each model's predict and see the raw scores.
    print("\n=== Raw model predictions on silence ===")
    for entity_name, model in detector.models.items():
        try:
            prediction = model.predict(silent_audio)
            print(f"{entity_name}: {prediction}")
        except Exception as e:
            print(f"{entity_name}: Error - {e}")
    
    print("\n=== Raw model predictions on noise ===")
    for entity_name, model in detector.models.items():
        try:
            prediction = model.predict(noisy_audio)
            print(f"{entity_name}: {prediction}")
        except Exception as e:
            print(f"{entity_name}: Error - {e}")
    
    # Now test the detector's detect_from_audio with a very low threshold
    print("\n=== Testing detect_from_audio with threshold 0.0 ===")
    original_threshold = detector.config.confidence_threshold
    detector.config.confidence_threshold = 0.0
    print(f"Set threshold to {detector.config.confidence_threshold}")
    
    pred_silent = detector.detect_from_audio(silent_bytes)
    print(f"Silence prediction: {pred_silent}")
    
    pred_noise = detector.detect_from_audio(noisy_bytes)
    print(f"Noise prediction: {pred_noise}")
    
    # Restore threshold
    detector.config.confidence_threshold = original_threshold
    print(f"Restored threshold to {original_threshold}")

if __name__ == "__main__":
    test_detector_raw()