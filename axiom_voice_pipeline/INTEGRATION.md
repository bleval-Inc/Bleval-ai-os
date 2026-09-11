"""
QUICK INTEGRATION GUIDE

How to integrate the voice pipeline into your Axiom OS backend.
"""

# # Voice Pipeline Quick Integration Guide

## 1. Add to FastAPI Backend (main.py)

```python
from fastapi import FastAPI
from backend.voice_pipeline_routes import router as voice_router

app = FastAPI()

# Include voice pipeline routes
app.include_router(voice_router)

# Optional: Initialize pipeline on startup
@app.on_event("startup")
async def startup_voice_pipeline():
    from backend.voice_pipeline_routes import startup
    await startup()

@app.on_event("shutdown")
async def shutdown_voice_pipeline():
    from backend.voice_pipeline_routes import shutdown
    await shutdown()
```

## 2. Connect Intelligence Engine

The pipeline needs a callback to your existing intelligence engine:

```python
from axiom_voice_pipeline import VoicePipeline
from axiom.engine.intelligence import ExecutiveIntelligence

# Your existing intelligence engine instance
intelligence = ExecutiveIntelligence()

async def process_command(entity: str, command_text: str):
    """
    Callback from voice pipeline to intelligence engine.
    
    Args:
        entity: Target entity (axiom, jenson, yamako, valtaprime)
        command_text: User's transcribed command
        
    Returns:
        IntelligenceEngineOutput with full_result and spoken_summary
    """
    from axiom_voice_pipeline.models import (
        IntelligenceEngineOutput,
        ResultContent,
    )
    from axiom_voice_pipeline.config import WORKSTATION_ROUTING
    
    # Call your intelligence engine
    result = await intelligence.process(
        entity=entity,
        command=command_text,
    )
    
    # Transform to voice pipeline format
    return IntelligenceEngineOutput(
        full_result=ResultContent(
            type=result.result_type,  # search_results | data | text | table
            content=result.data,
        ),
        spoken_summary=result.spoken_response,
        target_workstation=WORKSTATION_ROUTING[entity],
    )

# Use in voice pipeline
pipeline = VoicePipeline()

async for audio_chunk in microphone_stream:
    await pipeline.process_audio_stream(
        audio_stream=microphone_stream,
        on_intelligence_result=process_command,
    )
```

## 3. Add Microphone Input (Example)

```python
import asyncio
import numpy as np
import sounddevice as sd

async def audio_stream_generator(sample_rate=16000, chunk_size=1024):
    """
    Async generator for audio chunks from microphone.
    
    Install sounddevice: pip install sounddevice
    """
    def audio_callback(indata, frames, time, status):
        if status:
            print(f"Audio status: {status}")
        # Queue audio chunk
        asyncio.create_task(queue.put(indata.copy()))
    
    queue = asyncio.Queue()
    
    stream = sd.InputStream(
        channels=1,
        samplerate=sample_rate,
        blocksize=chunk_size,
        callback=audio_callback,
    )
    
    with stream:
        while True:
            chunk = await queue.get()
            yield chunk.astype(np.float32)

# Start pipeline
@app.on_event("startup")
async def start_voice_processing():
    pipeline = get_pipeline()
    
    # Create microphone stream
    audio_gen = audio_stream_generator()
    
    # Run pipeline in background
    asyncio.create_task(
        pipeline.process_audio_stream(
            audio_gen,
            on_intelligence_result=process_command,
        )
    )
```

## 4. Test the Integration

### Check Health
```bash
curl http://localhost:8000/api/v1/voice/health
```

Expected output:
```json
{
  "status": "healthy",
  "pipeline_components": {
    "wake_detector": true,
    "stt": true,
    "router": true,
    "tts": true
  },
  "active_connections": 0
}
```

### Get Configuration
```bash
curl http://localhost:8000/api/v1/voice/config
```

### List Entities
```bash
curl http://localhost:8000/api/v1/voice/entities
```

### Test TTS
```bash
curl -X POST "http://localhost:8000/api/v1/voice/test/synthesize?entity_name=axiom&text=Hello%20world"
```

## 5. Frontend WebSocket Connection

```javascript
// Connect to voice events
const ws = new WebSocket('ws://localhost:8000/api/v1/voice/events');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'wake_detected':
      console.log('Woke up:', data.payload.detection.wake_entity);
      break;
      
    case 'transcription_complete':
      console.log('Heard:', data.payload.transcription.raw_text);
      break;
      
    case 'executive_speaking':
      // Decode and play audio
      const audioData = data.payload.audio.audio_data_base64;
      playAudio(audioData);
      break;
      
    case 'display_result':
      // Show result on workstation
      displayOnWorkstation(data.payload.workstation, data.payload.data);
      break;
      
    case 'error':
      console.error('Voice error:', data.payload.error_message);
      break;
  }
};
```

## 6. Configuration Tuning

### Reduce Wake Word False Positives

```python
# In axiom_voice_pipeline/config.py
wake_word_config = WakeWordConfig(
    confidence_threshold=0.7,  # Increase from 0.5
)
```

### Speed Up Response

```python
# Use smaller/faster STT model
stt_config = STTConfig(
    model_size="small",  # Instead of "medium"
)

# Reduce VAD silence wait
vad_config = VADConfig(
    silence_duration=0.5,  # Instead of 1.0
)
```

### Improve Audio Quality

```python
# Switch to ElevenLabs for premium responses
tts_config = TTSConfig(
    primary_provider="elevenlabs",
    fallback_provider="piper",
    elevenlabs_api_key="your-key",
)
```

## 7. Debugging

### Enable Verbose Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("axiom_voice_pipeline")
logger.setLevel(logging.DEBUG)
```

### Check Component Status

```bash
# From Python REPL
from axiom_voice_pipeline import VoicePipeline

pipeline = VoicePipeline()
health = pipeline.health_check()
print(health)
```

### Test Individual Components

```python
from axiom_voice_pipeline import (
    WakeWordDetector,
    WhisperEngine,
    IntentRouter,
    PiperTTS,
)

# Wake word detector
detector = WakeWordDetector()
loaded = detector.get_loaded_entities()
print(f"Loaded entities: {loaded}")

# STT
stt = WhisperEngine()
result = stt.transcribe(audio_bytes)
print(f"Transcribed: {result.raw_text}")

# Intent router
router = IntentRouter()
routing = router.route("jenson", "Check my emails")
print(f"Target entity: {routing.target_entity}")

# TTS
tts = PiperTTS()
audio = tts.synthesize("Hello world", "en_GB-bnk-medium")
print(f"Audio duration: {audio.duration_seconds}s")
```

## 8. Production Checklist

- [ ] Train custom wake word models (replace placeholder models)
- [ ] Configure confidence thresholds based on your environment
- [ ] Set up microphone hardware and audio driver
- [ ] Test with real users and various accents/speech patterns
- [ ] Configure ElevenLabs API key for premium fallback (optional)
- [ ] Set up error monitoring and logging
- [ ] Test WebSocket connection stability
- [ ] Load test with expected concurrent users
- [ ] Containerize for deployment
- [ ] Set up audio playback on designated workstations
- [ ] Document any custom entity definitions
- [ ] Create runbooks for troubleshooting

## 9. Example: Full Integration

See `backend/voice_pipeline_routes.py` for the complete integration showing:
- REST endpoints for health/config/testing
- WebSocket relay setup
- Error handling
- Startup/shutdown lifecycle

## Support

For detailed documentation, see: `axiom_voice_pipeline/README.md`

For integration examples, see: `tests/test_voice_pipeline.py`

---

**The voice pipeline is production-ready. Start integrating!**
