import sys
import numpy as np
import time
sys.path.append('C:\\Users\\byagi\\Desktop\\Bleval-ai-os')
from axiom_voice_pipeline.wakeword.detector import WakeWordDetector

def test_hey_jarvis_detection():
    """Test if hey_jarvis model detects 'hey jarvis' audio."""
    print("Initializing WakeWordDetector...")
    detector = WakeWordDetector()
    print(f"Loaded entities: {detector.get_loaded_entities()}")
    print(f"Number of models: {len(detector.models)}")
    
    # Generate a simple audio signal that might trigger detection
    # We'll create a buffer of silence first
    duration = 1.0  # seconds
    sample_rate = 16000
    samples = int(duration * sample_rate)
    
    # Create audio buffer (all zeros = silence)
    audio_buffer = np.zeros(samples, dtype=np.float32)
    
    print("\nTesting with silence (should not detect)...")
    # Convert to bytes as expected by detect_from_audio
    audio_bytes = (audio_buffer * 32767).astype(np.int16).tobytes()
    result = detector.detect_from_audio(audio_bytes)
    print(f"Detection result: {result}")
    
    # Now let's try to see what the model outputs by accessing internal methods
    # We'll test one model directly
    if detector.models:
        entity = list(detector.models.keys())[0]
        model = detector.models[entity]
        print(f"\nTesting {entity} model directly...")
        
        # Try to get a prediction from the model
        try:
            # The model expects audio as numpy array of floats in [-1, 1]
            prediction = model.predict(audio_buffer)
            print(f"Raw prediction shape: {prediction.shape}")
            print(f"Prediction values: {prediction}")
            print(f"Max prediction: {np.max(prediction)}")
        except Exception as e:
            print(f"Error in direct prediction: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_hey_jarvis_detection()