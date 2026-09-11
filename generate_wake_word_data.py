import os
import sys
from gtts import gTTS
from pydub import AudioSegment

# Define entities
entities = ["axiom", "jenson", "yamako", "valtaprime"]

# Create directories
os.makedirs("positive_samples", exist_ok=True)
os.makedirs("negative_samples", exist_ok=True)

for entity in entities:
    os.makedirs(f"positive_samples/{entity}", exist_ok=True)

# Generate positive samples: "hey <entity>"
for entity in entities:
    for i in range(10):  # 10 samples per entity
        tts = gTTS(text=f"hey {entity}", lang='en')
        mp3_path = f"temp_{entity}_{i}.mp3"
        tts.save(mp3_path)
        
        # Convert to 16kHz mono wav
        sound = AudioSegment.from_mp3(mp3_path)
        sound = sound.set_frame_rate(16000).set_channels(1)
        wav_path = f"positive_samples/{entity}/{entity}_{i}.wav"
        sound.export(wav_path, format="wav")
        
        # Clean up mp3
        os.remove(mp3_path)
        print(f"Generated {wav_path}")

# Generate negative samples: 1 second of silence
for i in range(20):  # 20 silence samples
    silence = AudioSegment.silent(duration=1000)  # 1 second in milliseconds
    silence = silence.set_frame_rate(16000).set_channels(1)
    wav_path = f"negative_samples/negative_{i}.wav"
    silence.export(wav_path, format="wav")
    print(f"Generated {wav_path}")

print("Audio generation complete.")