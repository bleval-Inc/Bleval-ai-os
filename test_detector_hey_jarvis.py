import sys
import os
import numpy as np
from gtts import gTTS
from pydub import AudioSegment

sys.path.append('C:\\Users\\byagi\\Desktop\\Bleval-ai-os')
from axiom_voice_pipeline.wakeword.detector import WakeWordDetector

def test_detector_with_hey_jarvis():
    print("Testing WakeWordDetector with hey jarvis audio...")
    
    # Generate audio for "hey jarvis"
    tts = gTTS(text="hey jarvis", lang='en')
    tts.save("hey_jarvis_test.mp3")
    
    # Convert to 16kHz mono wav
    sound = AudioSegment.from_mp3("hey_jarvis_test.mp3")
    sound = sound.set_frame_rate(16000).set_channels(1)
    sound.export("hey_jarvis_test.wav", format="wav")
    
    # Load the wav file and get raw audio data
    seg = AudioSegment.from_wav("hey_jarvis_test.wav")
    samples = np.array(seg.get_array_of_samples())
    if seg.channels == 2:
        samples = samples.reshape((-1, 2))
        samples = samples.mean(axis=1)
    if seg.sample_width == 2:
        audio_float = samples.astype(np.float32) / 32768.0
    else:
        raise ValueError("Only 16-bit audio is supported")
    
    # Initialize the detector
    detector = WakeWordDetector()
    print(f"Loaded entities: {detector.get_loaded_entities()}")
    
    # Process in chunks
    chunk_size = 1280
    max_score = 0.0
    detected_entity = None
    for i in range(0, len(audio_float), chunk_size):
        chunk = audio_float[i:i+chunk_size]
        if len(chunk) < chunk_size:
            chunk = np.pad(chunk, (0, chunk_size - len(chunk)), 'constant')
        # Convert to bytes for the detector
        audio_bytes = (chunk * 32767).astype(np.int16).tobytes()
        wake_result = detector.detect_from_audio(audio_bytes)
        if wake_result:
            score = wake_result.confidence
            entity = wake_result.wake_entity
            print(f"Chunk {i//chunk_size}: {entity} with score {score}")
            if score > max_score:
                max_score = score
                detected_entity = entity
    
    print(f"Maximum prediction score: {max_score}")
    print(f"Detected entity: {detected_entity}")
    if max_score > 0.0:  # Since threshold is 0.0 in config
        print("DETECTION: Wake word detected!")
    else:
        print("No detection (score at or below threshold)")
    
    # Clean up
    os.remove("hey_jarvis_test.mp3")
    os.remove("hey_jarvis_test.wav")

if __name__ == "__main__":
    test_detector_with_hey_jarvis()