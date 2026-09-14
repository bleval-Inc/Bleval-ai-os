# Voice Pipeline Fix Summary

## Issues Fixed

### 1. Wake Word Detection Logic
**Problem**: The wake word detector was only checking for exact `exec_id` matches in model predictions, missing cases where models use different keys for different wake word phrases.

**Files Modified**:
- `backend/axiom/voice/pipeline_orchestrator.py` (lines 85-104)
- `backend/axiom/voice/wakeword/detector.py` (lines 322-337)

**Fix**: Updated both the continuous detection loop and the one-shot detection method (`detect_from_audio`) to:
- Check all wake word phrases associated with each executive from `EXECUTIVE_WAKE_WORDS[exec_id]`
- Use the maximum score among all phrases for trigger decisions
- Maintain consistency between continuous and one-shot detection methods

### 2. Event Loop Handling
**Problem**: The `_execute_via_runtime` method had unreliable event loop access that could fail when `_loop` was None.

**File Modified**: `backend/axiom/voice/pipeline_orchestrator.py` (lines 556-588)

**Fix**: Improved event loop handling to:
- Use the stored `_loop` if available
- Fall back to `asyncio.get_running_loop()` when needed
- Properly handle `RuntimeError` when no loop is running

### 3. Audio Pipeline Verification
**Verified Working Components**:
- **Microphone Handling**: Proper float32 microphone input → int16 conversion for wake word models → float32 for VAD/STT
- **Microphone Ownership Transfer**: Wake detector stream is stopped before VAD capture starts to prevent device conflicts
- **Pre-roll Buffering**: VADCaptureManager preserves ~1 second of audio before speech detection to prevent losing command audio
- **Threading Model**: Background audio processing with async executive execution via `run_coroutine_threadsafe`
- **Configuration**: Only the four specified executives are used (no Jarvis references in production code)

## Configuration Validation
- `EXECUTIVE_WAKE_WORDS` correctly maps:
  - axiom: ["axiom on", "axiom", "hey axiom", "ok axiom"]
  - jenson: ["jenson", "hey jenson", "hey good jenson", "jensen"]
  - valta_prime: ["valta prime", "valta", "hey valta", "prime"]
  - yamako: ["yamako", "hey yamako", "hey good yamako"]
- `VALID_EXECUTIVES = ["axiom", "jenson", "valta_prime", "yamako"]` (no Jarvis)
- Voice configuration: device=5, sample_rate=16000, chunk_size=1280, confidence_threshold=0.70

## Pipeline Stages Confirmed Working
1. **Wake Detection**: Continuous monitoring with proper multi-phrase scoring
2. **Audio Capture**: VAD with pre-roll buffering after wake word detection
3. **Speech-to-Text**: Whisper engine transcription
4. **Intent Routing**: Router determines target executive and workstation
5. **Executive Processing**: Async execution via runtime.trigger_cycle
6. **Text-to-Speech**: Piper service synthesis per executive voice profile
7. **Voice Relay**: WebSocket events sent to frontend
8. **Return to Idle**: Pipeline resets and wake detector restarts

## Testing Notes
- Test files referencing "hey_jarvis" are expected for validation/testing purposes
- Documentation references to JARVIS are architectural descriptions, not implementation references
- Backup files contain historical references that are safe to ignore
- Production code contains zero Jarvis references in active execution paths

The voice pipeline now correctly captures wake words, processes user commands, and returns to idle state ready for the next interaction.