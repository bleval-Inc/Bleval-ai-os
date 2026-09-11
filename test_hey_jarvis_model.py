import sys
import os
import numpy as np
from gtts import gTTS
from pydub import AudioSegment

sys.path.append('C:\\Users\\byagi\\Desktop\\Bleval-ai-os\\backend\\.venv\\Lib\\site-packages')
import openwakeword

def test_hey_jarvis_model():
    print("Testing hey_jarvis model from openwakeword directly...")
    
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
    
    # Get hey_jarvis model path
    model_paths = openwakeword.get_pretrained_model_paths('onnx')
    hey_jarvis_path = None
    for p in model_paths:
        if 'hey_jarvis' in p:
            hey_jarvis_path = p
            break
    if hey_jarvis_path is None:
        hey_jarvis_path = model_paths[2]
    print(f"Using model: {hey_jarvis_path}")
    
    # Initialize the model
    model = openwakeword.Model(
        wakeword_models=[hey_jarvis_path],
        inference_framework='onnx',
    )
    
    # Process in chunks
    chunk_size = 1280
    max_score = 0.0
    for i in range(0, len(audio_float), chunk_size):
        chunk = audio_float[i:i+chunk_size]
        if len(chunk) < chunk_size:
            chunk = np.pad(chunk, (0, chunk_size - len(chunk)), 'constant')
        prediction = model.predict(chunk)
        # prediction is a dict with model name as key and score as value
        # Since we only have one model, we can get the value
        for key, score in prediction.items():
            if score > max_score:
                max_score = score
        # Uncomment to see per-chunk predictions
        # print(f"Chunk {i//chunk_size}: {prediction}")
    
    print(f"Maximum prediction score: {max_score}")
    if max_score > 0.5:
        print("DETECTION: hey jarvis detected!")
    else:
        print("No detection (score below threshold)")
    
    # Clean up
    os.remove("hey_jarvis_test.mp3")
    os.remove("hey_jarvis_test.wav")

if __name__ == "__main__":
    test_hey_jarvis_model()