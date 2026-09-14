# Voice Pipeline Testing Guide

This guide provides steps to test and debug the voice pipeline wake word detection system.

## 1. Enable Detailed Logging

To see what's happening in the voice pipeline, enable debug logging:

### Backend Server Logging
When starting the backend server, set the log level to DEBUG:

```bash
# Using uvicorn directly
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level debug

# Or if using a script, ensure logging is configured for DEBUG
```

### Component-Specific Logging
Add these to your environment or startup script to get verbose voice pipeline logs:

```bash
# Enable debug logging for voice components
export LOG_LEVEL=debug
export Axiom_Voice_WakeWord_Detector__level=DEBUG
export Axiom_Voice_PipelineOrchestrator__level=DEBUG
export Axiom_Voice_STT__level=DEBUG
export Axiom_Voice_TTS__level=DEBUG
```

## 2. Test Wake Word Detector in Isolation

Run this test to verify the wake word detector works independently:

```python
# From backend directory
python -c "
import sys
sys.path.append('.')
from axiom.voice.wakeword import create_wake_word_detector
import time
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def on_wake(entity, confidence, wake_word):
    print(f'WAKE DETECTED: {entity} ({wake_word}) confidence={confidence:.3f}')

# Create detector
detector = create_wake_word_detector(use_mock=False, on_wake=on_wake)

print('Loading wake word models...')
if not detector.load_models():
    print('ERROR: Failed to load wake word models')
    sys.exit(1)

print('Starting wake word detector...')
if not detector.start():
    print('ERROR: Failed to start wake word detector')
    sys.exit(1)

print('Wake word detector running. Speak wake words like:')
print('  - \"axiom on\"')
print('  - \"hey jenson\"')  
print('  - \"valta prime\"')
print('  - \"hey yamako\"')
print('Press Ctrl+C to stop...')

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('\\nStopping...')
    detector.stop()
    print('Done.')
"
```

## 3. Test Audio Device Configuration

Verify your microphone is working and correctly configured:

```python
# Test audio input
python -c "
import sounddevice as sd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)

print('Available audio devices:')
print(sd.query_devices())

print('\\nDefault input device:', sd.default.device[0])

# Test recording 2 seconds of audio
print('\\nRecording 2 seconds of audio...')
def callback(indata, frames, time, status):
    if status:
        print(f'Status: {status}')
    volume_norm = np.linalg.norm(indata) * 10
    print(f'Volume: {volume_norm:.2f}')

with sd.InputStream(callback=callback, channels=1, samplerate=16000, blocksize=1280):
    sd.sleep(2000)
print('Done.')
"
```

Check your `backend/axiom/voice/config.py` for the correct `audio_device` setting:
```python
audio_device: Optional[int] = 5  # Make sure this matches your microphone
```

## 4. Verify Wake Word Models Exist

Check that the trained wake word models are present:

```bash
ls -la backend/axiom/voice/wakeword/models/
# Should show: axiom.onnx, jenson.onnx, valta_prime.onnx, yamako.onnx

# If missing, you need to train them:
python backend/scripts/train_wakeword_models.py
```

## 5. Test Push-to-Talk (Bypass Wake Word)

To test if the rest of the pipeline works (STT -> LLM -> TTS), use push-to-talk:

```python
# From backend directory
python -c "
import sys
sys.path.append('.')
from axiom.voice.pipeline_orchestrator import get_pipeline
import time
import logging

logging.basicConfig(level=logging.DEBUG)

# Get pipeline instance
pipeline = get_pipeline()

print('Initializing pipeline...')
if not pipeline.initialize():
    print('ERROR: Failed to initialize pipeline')
    sys.exit(1)

print('Starting pipeline...')
if not pipeline.start():
    print('ERROR: Failed to start pipeline')
    sys.exit(1)

print('Pipeline running. Testing push-to-talk...')
print('In another terminal, you can test with:')
print('  curl -X POST http://localhost:8000/api/voice/push-to-talk?entity=axiom')
print('Or wait 10 seconds for automatic test...')

time.sleep(10)

print('\\nTriggering push-to-talk for axiom...')
if pipeline.trigger_push_to_talk('axiom'):
    print('Push-to-talk triggered successfully')
    print('Speak now after the beep...')
else:
    print('ERROR: Failed to trigger push-to-talk')

# Keep running for a bit to see results
time.sleep(15)

print('\\nStopping pipeline...')
pipeline.stop()
print('Done.')
"
```

## 6. Test Full Pipeline via HTTP Endpoints

If your backend server is running, test these endpoints:

### Check Pipeline Status
```bash
curl http://localhost:8000/api/voice/status
```

### Start Pipeline
```bash
curl -X POST http://localhost:8000/api/voice/start
```

### Test Push-to-Talk
```bash
curl -X POST "http://localhost:8000/api/voice/push-to-talk?entity=axiom"
```

### Stop Pipeline
```bash
curl -X POST http://localhost:8000/api/voice/stop
```

### Check Voice Pipeline Logs (if endpoint exists)
```bash
curl http://localhost:8000/api/voice/logs
```

## 7. Common Issues and Solutions

### Issue: "No wake word models loaded"
**Solution:** 
- Run `python backend/scripts/train_wakeword_models.py` to generate models
- Verify model files exist in `backend/axiom/voice/wakeword/models/`

### Issue: "Failed to open audio stream"
**Solution:**
- Check microphone permissions
- Verify `audio_device` in config matches your microphone index
- Try setting `audio_device: null` to use default device
- Close other applications using the microphone

### Issue: Wake words detected but no response
**Solution:**
- Check if VAD capture is working (listen for beep when push-to-talk works)
- Verify STT engine loads correctly
- Check if intent router is finding matches
- Verify TTS service can synthesize audio

### Issue: High CPU usage or audio glitches
**Solution:**
- Adjust `chunk_size` in wake word config (try 512 or 256)
- Reduce `sample_rate` if your microphone doesn't support 16000Hz
- Close other audio-intensive applications

## 8. Debugging Checklist

When wake words aren't being detected:

☐ **Backend server is running** with voice pipeline started
☐ **Logging shows "Wake word detection loop running"** 
☐ **Audio levels are visible** in debug logs (look for volume/RMS values)
☐ **Wake word models loaded successfully** (check startup logs)
☐ **Correct audio device selected** (check `voice_config.audio_device`)
☐ **Microphone not muted** and working in other applications
☐ **Speaking clearly** and close to microphone
☐ **Using correct wake phrases** (check `EXECUTIVE_WAKE_WORDS` in config)
☐ **Confidence threshold not too high** (default 0.70, try lowering to 0.5 for testing)
☐ **No cooldown blocking detection** (wait >1 second between attempts)

## 9. Quick Test Commands

Run these from the backend directory:

### Test 1: Wake word detector alone
```bash
python -c "
import sys; sys.path.append('.')
from axiom.voice.wakeword import create_wake_word_detector
import logging; logging.basicConfig(level=logging.INFO)
def cb(e,c,w): print(f'DETECTED: {e} ({w}) {c:.2f}')
d = create_wake_word_detector(on_wake=cb)
d.load_models(); d.start()
import time
try:
    while True: time.sleep(1)
except KeyboardInterrupt: d.stop()
"
```

### Test 2: Full pipeline with push-to-talk
```bash
python -c "
import sys; sys.path.append('.')
from axiom.voice.pipeline_orchestrator import get_pipeline
import logging; logging.basicConfig(level=logging.INFO)
p = get_pipeline()
p.initialize(); p.start()
print('Push-to-talk ready - speak after beep')
p.trigger_push_to_talk('axiom')
import time; time.sleep(10)
p.stop()
"
```

## 10. When All Else Fails

If you've verified everything above and still get no detection:

1. **Try the mock detector** to verify the pipeline works without hardware:
   ```python
   detector = create_wake_word_detector(use_mock=True, on_wake=on_wake)
   ```
   This simulates wake words every 30 seconds.

2. **Check actual audio input** to the detector by adding debug in `_detection_loop`:
   ```python
   # Add after getting audio_data:
   logger.debug(f'Audio chunk RMS: {np.sqrt(np.mean(audio_data**2)):.4f}')
   ```

3. **Verify openWakeWord is working** by testing directly:
   ```python
   from openwakeword.model import Model
   import numpy as np
   model = Model(wakeword_models=['path/to/your/model.onnx'], inference_framework='onnx')
   audio = np.zeros(1280, dtype=np.int16)  # silence
   pred = model.predict(audio)
   print(f'Model prediction: {pred}')
   ```

Remember: The wake word detector processes audio in chunks and needs continuous audio input to work. Make sure your microphone is providing data to the detector's audio queue.