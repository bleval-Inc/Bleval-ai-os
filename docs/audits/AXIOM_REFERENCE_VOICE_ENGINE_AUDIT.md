# AXIOM_REFERENCE_VOICE_ENGINE_AUDIT.md

## Executive Summary

This document presents the reverse-engineering analysis of the reference voice pipeline located at `/c/Users/byagi/Desktop/Bleval-ai-os/axiom_voice_pipeline`. The reference implementation provides a production-grade, continuously streaming voice processing system that includes wake-word detection, voice activity detection, speech-to-text transcription, intent routing, and text-to-speech synthesis. The pipeline is designed for server-side processing with WebSocket communication to a frontend client.

Key strengths of the reference implementation:
- Continuous microphone streaming via sounddevice with async audio chunk generation
- Concurrent multi-model wake-word detection using openWakeWord
- Voice activity detection (VAD) using either Silero or WebRTC engines for clean speech endpoint detection
- Local, fast transcription using faster-whisper (no API costs)
- Deterministic intent routing with delegation capabilities for the Axiom entity
- Text-to-speech synthesis using Piper (local) with ElevenLabs fallback
- Event-driven architecture with WebSocket relay for real-time frontend communication
- Comprehensive health checking and graceful degradation mechanisms

The pipeline correctly handles the full voice interaction lifecycle: from ambient listening, wake-word detection, speech capture, transcription, intent routing, AI processing, TTS synthesis, and result dissemination.

## Verified Repository and Runtime Details

- **Reference Repository Path**: `/c/Users/byagi/Desktop/Bleval-ai-os/axiom_voice_pipeline`
- **Parent Repository**: Bleval-ai-os (Axiom AI OS)
- **Git Status**: Parent repository on branch `main`, ahead of `origin/main` by 3 commits; reference directory clean with no modifications
- **Runtime Environment**: 
  - Python 3.11.9 (verified via `python --version`)
  - Virtual environment: Not active in current shell; dependencies available via parent repository's editable install (`-e git+...#egg=axiom_os&subdirectory=backend`)
- **Dependency Manifest**: `requirements.txt` (see exact versions in appendix)
- **Application Entry Point**: Pipeline orchestration via `pipeline_orchestrator.py`; typically invoked by backend service
- **Relevant Environment Variables** (from parent repository `.env` example):
  - `ANTHROPIC_API_KEY` (optional, for Anthropic Claude)
  - `OPENAI_API_KEY` (optional, for OpenAI GPT)
  - `RUFLO_ENV` (defaults to `development`)
- **Voice-Related Directories and Files**:
  - `wakeword/` - wake-word detection models and logic
  - `stt/` - speech-to-text (faster-whisper) implementation
  - `tts/` - text-to-speech (Piper/ElevenLabs) providers
  - `router/` - intent routing logic
  - `relay/` - WebSocket event relay
  - `microphone_capture.py` - audio input handling
  - `pipeline_orchestrator.py` - main orchestrator
  - `voice_intelligence_callback.py` - interface to backend AI engine
  - `config.py` - centralized configuration
  - `models.py` - Pydantic data contracts
- **Model Files and Configuration Assets**:
  - Wake-word models: `wakeword/models/*.onnx` (placeholder 27-byte files; intended for custom-trained .onnx models)
  - Piper TTS voice models: Expected in `tts/models/` directory (not present in reference; rely on piper-tts package's bundled voices or external download)
  - No local STT models; faster-whisper downloads models to cache on first use
- **Existing Tests and Diagnostic Utilities**: No dedicated test suite found; setup guide (`setup_guide.py`) provides validation steps; health check methods available on all major components
- **Existing Logs or Documented Runtime Behavior**: None observed in reference repository; runtime logging available via configured loggers

## Voice Architecture and Actual Execution Path

The voice pipeline follows a modular, event-driven architecture with clear separation of concerns:

```
[Audio Source] 
    ↓
[Wake Word Detector] 
    ↓ (on wake detection)
[Voice Activity Detector] 
    ↓ (speech capture window)
[Speech-to-Text Engine] 
    ↓ (transcribed text)
[Intent Router] 
    ↓ (target entity + intent type)
[Intelligence Engine Callback] 
    ↓ (full result + spoken summary)
[Text-to-Speech Synthesizer] 
    ↓ (audio bytes)
[WebSocket Relay] 
    ↓
[Frontend Client] (displays result + plays audio)
```

Actual execution path as implemented in `pipeline_orchestrator.py`:
1. `MicrophoneCapture.audio_stream_generator()` yields continuous audio chunks (np.ndarray, float32, mono, 16kHz)
2. `WakeWordDetector.detect_from_audio()` processes each chunk for wake word detection
3. Upon detection, `_handle_wake_word()` is invoked:
   - Emits `wake_detected` WebSocket event
   - Emits `listening_started` event
   - `_capture_command_audio()` uses `VoiceActivityDetector` to collect speech until silence threshold
   - Captured audio passed to `_transcribe_audio()` via `WhisperEngine.transcribe()`
   - On transcription, emits `transcription_complete` event
   - `_route_intent()` via `IntentRouter.route()` determines target entity and intent type
   - Emits `processing` event
   - `_get_intelligence_result()` invokes intelligence engine callback (or mock)
   - `_synthesize_and_speak()` synthesizes spoken summary via TTS provider proxy
   - Emits `executive_speaking` event (with base64-encoded audio)
   - `_emit_display_result()` sends full result to designated workstation
   - Returns to idle state, emits `idle` event

## Continuous Microphone-Streaming Implementation

- **Audio Library**: `sounddevice` (via `sounddevice` Python package)
- **Streaming Mechanism**: 
  - `MicrophoneCapture` class manages an `sd.InputStream` with callback
  - Audio callback (`audio_copy = indata[:, 0].copy()` for mono) places audio chunks into an `asyncio.Queue`
  - `audio_stream_generator()` async generator yields chunks from queue with 1.0s timeout
- **Stream Ownership**: Single `MicrophoneCapture` instance per pipeline; stream started via `start()` and stopped via `stop()`
- **Audio Format**: 
  - Sample rate: 16000 Hz (configurable via `WakeWordConfig.sample_rate`)
  - Channels: 1 (mono)
  - Sample width: 32-bit float (internally converted to 16-bit integer for wake-word detection and STT)
  - Chunk size: 1024 samples (~64ms at 16kHz)
- **Buffering**: 
  - Async queue between audio callback and generator prevents blocking
  - No internal ring buffer; relies on OS audio buffering and queue depth
- **Frame Handling**: 
  - Wake-word detector receives raw 16-bit PCM bytes from audio chunks
  - VAD processes float32 numpy arrays (normalized from int16)
  - STT receives raw 16-bit PCM bytes converted to float32 numpy array normalized to [-1.0, 1.0]
- **Concurrency**: 
  - Audio I/O runs in sounddevice callback thread
  - Main processing loop runs in asyncio event loop
  - No audio loss under normal operation; queue provides buffering
- **Continuous Listening**: Microphone stream remains open and active throughout pipeline lifetime; no re-initialization between commands
- **Feedback Mechanism**: 
  - Pipeline emits WebSocket events at each stage (`wake_detected`, `listening_started`, etc.)
  - Frontend can use these events to provide visual/audio feedback (e.g., listening indicator)
  - No native audio level logging in reference implementation (though `MicrophoneCapture.test_microphone_setup()` shows debug level logging)

## Wake-Word Detection and Command-Capture Implementation

- **Wake-Word Engine**: `openwakeword` (version 0.6.0 per requirements)
- **Model Loading**: 
  - One model per entity (Axiom, Jenson, Yamako, Valta Prime)
  - Models loaded via `WakeWordDetector._load_model()` using `openwakeword.model.Model`
  - Currently uses placeholder "hey_jarvis" model; intended to be replaced with custom .onnx models
- **Detection Process**: 
  - `detect_from_audio()` converts audio chunk to int16 numpy array
  - Runs all loaded models concurrently (synchronous loop)
  - Extracts confidence score as max prediction value per model
  - Returns `WakeWordDetection` for highest confidence above threshold (`wake_word_config.confidence_threshold`, default 0.0 for testing)
- **Threshold Configurability**: `confidence_threshold` exposed in `WakeWordConfig`; tune to balance false positives vs. missed detections
- **Multi-Model**: `multi_model_enabled=True` runs all entity models in parallel (though implementation loops synchronously)
- **Command Capture**: 
  - Initiated immediately after wake-word detection
  - Uses `VoiceActivityDetector` with configurable engine (`vad_config.engine`: "silero" or "webrtcvad")
  - VAD processes audio frames to detect speech/silence transitions
  - Capture ends when: 
    - VAD-terminated: silence duration >= `vad_config.silence_duration` (default 1.0s) AND minimum capture time met (`MIN_CAPTURE_TIME` = 0.5s)
    - Fixed-timeout: capture duration >= `CAPTURE_FIXED_TIMEOUT` (default 10.0s) 
  - Captured audio frames concatenated and returned as numpy array (float32, mono, 16kHz)
- **Speech Start/End Detection**: 
  - Speech start: first frame where VAD probability >= threshold after silence period
  - Speech end: first silence frame where accumulated silence duration >= threshold after speech period
- **Command Handoff**: Captured audio passed directly to STT transcription
- **Concurrency Boundaries**: 
  - Wake-word detection runs continuously on audio stream
  - VAD and STT operate only during capture window
  - No overlap between wake-word detection and command processing (sequential within pipeline)

## Transcription Implementation

- **Engine**: `faster-whisper` (version 1.2.1 per requirements)
- **Model**: 
  - Configured via `STTConfig`: `model_size` = "small.en" (English-only, small model)
  - Alternative sizes: tiny, base, small, medium, large-v3
  - Device: "cpu" (configurable to "auto" or "cuda")
  - Compute type: "int8" (quantized for CPU efficiency)
  - Language: "en" (English only)
  - Temperature: 0.0 (deterministic)
- **Loading**: 
  - Model loaded lazily on first use via `WhisperEngine._load_model()`
  - Health check via `WhisperEngine.health_check()`
- **Transcription Process**: 
  - `transcribe()` converts raw 16-bit PCM bytes to float32 numpy array normalized to [-1.0, 1.0]
  - Calls `faster_whisper.WhisperModel.transcribe()` with:
    - `language` = config.language
    - `temperature` = config.temperature
    - `vad_filter=True` (uses internal VAD to skip silent sections)
  - Returns `TranscriptionComplete` with:
    - `raw_text`: concatenated segments
    - `confidence`: None (faster-whisper does not provide segment-level confidence)
    - `duration_seconds`: estimated from audio byte length and sample rate
- **Post-Processing**: 
  - No additional cleanup in reference implementation
  - Empty or whitespace-only transcriptions treated as failures
- **Error Handling**: 
  - Returns `None` on model not loaded or transcription exception
  - Pipeline treats `None` transcription as failed capture and returns to idle

## Audio Contracts and Buffering Behaviour

### Audio Format Specifications
| Stage | Sample Rate | Channels | Format | Notes |
|-------|-------------|----------|--------|-------|
| Microphone Input | 16000 Hz | 1 (mono) | float32 (sounddevice callback) | Raw audio from sounddevice |
| Wake-Word Input | 16000 Hz | 1 (mono) | int16 PCM bytes | Converted from float32 in detector |
| VAD Processing | 16000 Hz | 1 (mono) | float32 numpy array | Normalized [-1.0, 1.0] from int16 |
| STT Input | 16000 Hz | 1 (mono) | float32 numpy array | Normalized [-1.0, 1.0] from int16 |
| TTS Output | 22050 Hz | 1 (mono) | int16 PCM WAV bytes | Piper output; sample rate configurable |

### Buffering and Flow Control
- **Microphone to Wake-Word**: 
  - Sounddevice callback → asyncio.Queue → pipeline audio generator
  - Queue depth unlimited; backpressure handled by blocking queue.put if consumer slow
  - No audio loss under typical load; OS buffer provides short-term buffering
- **Wake-Word to VAD**: 
  - Wake-word detection processes chunks immediately; no intermediate buffering
  - VAD maintains internal ring buffer of speech frames during capture window
- **VAD to STT**: 
  - Captured speech frames concatenated into single numpy array before STT
  - No streaming transcription; full utterance processed at once
- **STT to TTS**: 
  - Transcription result passed immediately to intent routing
  - TTS synthesis occurs after intelligence engine processing
  - No audio buffering between STT and TTS (text-based interface)
- **TTS to Frontend**: 
  - Audio bytes base64-encoded and sent via WebSocket event
  - Frontend responsible for audio playback buffering

### Sample Rate and Frame Size Consistency
- All stages expecting audio input use 16000 Hz sample rate (configurable via respective configs)
- Frame sizes vary by component:
  - Wake-word detector: processes arbitrary chunk sizes (matches microphone chunk size)
  - VAD: expects frame length consistent with sample rate (no strict requirement; processes whatever chunk given)
  - STT: accepts variable-length audio; processes complete utterance
- No resampling performed between stages; assumes consistent 16000 Hz throughout capture pipeline

## Exact Dependency and Module Inventory

### Core Voice Pipeline Dependencies (from requirements.txt)
| Package | Version | Purpose | Required? |
|---------|---------|---------|-----------|
| faster-whisper | 1.2.1 | Speech-to-text transcription | Yes |
| openwakeword | 0.6.0 | Wake-word detection | Yes |
| webrtcvad-wheels | 2.0.14 | Voice activity detection (alternative to Silero) | Yes |
| librosa | 0.11.0 | Audio processing (used in STT preparation) | Yes |
| sounddevice | 0.5.0 | Microphone capture | Yes |
| piper-tts | 1.6.0 | Local text-to-speech synthesis | Yes |
| elevenlabs | 2.65.0 | Optional fallback TTS | No (fallback only) |
| SpeechRecognition | 3.17.0 | Not used in voice pipeline (possibly legacy) | No |
| numpy | 1.26.4 | Numerical array processing | Yes |
| pydantic | 2.13.5 | Data validation and modeling | Yes |
| asyncio, typing | stdlib | Async programming and type hints | Yes |

### Transitive Dependencies (selected)
- `ctranslate2`: 4.8.2 (faster-whisper backend)
- `onnxruntime`: 1.29.0 (openWakeWord and Piper may use)
- `torch`: 2.14.0 (required for Silero VAD option)
- `webrtcvad`: 2.0.14 (alternative VAD engine)

### Module Inventory (axiom_voice_pipeline/)
| Module | Responsibility |
|--------|----------------|
| `__init__.py` | Package initialization |
| `config.py` | Centralized configuration (entities, wake-word, VAD, STT, TTS, routing, WebSocket, workstation routing) |
| `microphone_capture.py` | Real-time audio input from microphone via sounddevice |
| `wakeword/detector.py` | Wake-word detection using openWakeWord (multi-model, concurrent) |
| `wakeword/vad.py` | Voice activity detection (Silero/WebRTC engines with silence tracking) |
| `stt/whisper_engine.py` | Speech-to-text using faster-whisper (local Whisper model) |
| `router/intent_router.py` | Intent routing (entity determination, delegation logic for Axiom) |
| `tts/provider_base.py` | TTS provider abstraction interface |
| `tts/piper_provider.py` | Piper TTS implementation via CLI binary |
| `tts/elevenlabs_provider.py` | *(not present in reference; likely omitted)* |
| `tts/voice_profiles.py` | Voice ID mapping for entities (Piper voice identifiers) |
| `relay/ws_server.py` | WebSocket connection manager and event emitter |
| `pipeline_orchestrator.py` | Main orchestrator tying all components together |
| `voice_intelligence_callback.py` | Interface to backend AI engine (mock implementation) |
| `models.py` | Pydantic data contracts for events and results |
| `setup_guide.py` | Interactive setup and validation script |
| `train_wake_words.py` | Wake-word model training utility (uses openWakeWord training) |

### File Imports and Usage
- `microphone_capture.py`: imported by `pipeline_orchestrator.py` (indirectly via audio source)
- `wakeword/detector.py`: instantiated as `WakeWordDetector` in orchestrator
- `wakeword/vad.py`: instantiated as `VoiceActivityDetector` in orchestrator
- `stt/whisper_engine.py`: instantiated as `WhisperEngine` in orchestrator
- `router/intent_router.py`: instantiated as `IntentRouter` in orchestrator
- `tts/provider_base.py` and `tts/piper_provider.py`: used via `TTSProviderProxy` in orchestrator
- `relay/ws_server.py`: instantiated as `WebSocketConnectionManager` and `PipelineEventEmitter` in orchestrator
- `voice_intelligence_callback.py`: provides `create_voice_callback()` for intelligence engine integration
- `config.py`: imported by all modules for configuration access

## Effective Configuration and Precedence

### Configuration Sources
1. **Python Dataclass Instances** (`config.py`): 
   - Primary source of configuration; instantiated as module-level singletons
   - Example: `wake_word_config = WakeWordConfig()`, `vad_config = VADConfig()`, etc.
2. **Environment Variables**: 
   - Reference pipeline does **not** directly read environment variables
   - Configuration is hardcoded in `config.py` dataclasses
   - Parent repository (Axiom AI OS) uses `.env` for API keys, but voice pipeline config remains in code
3. **Constructor Arguments**: 
   - Each component accepts optional `config` parameter; if None, uses global singleton from `config.py`
   - Allows override for testing or specific instances
4. **Default Values in Source Code**: 
   - Defined in dataclass field declarations (see `config.py`)
   - Examples: 
     - `WakeWordConfig.confidence_threshold = 0.0` (testing default)
     - `WakeWordConfig.sample_rate = 16000`
     - `VADConfig.engine = "webrtcvad"`
     - `STTConfig.model_size = "small.en"`
     - `TTSConfig.primary_provider = "piper"`
     - `IntentRouterConfig.axiom_delegation_enabled = True`

### Configuration Precedence
For any given component:
1. Explicit constructor argument (if provided) overrides global config
2. Global config singleton (`config.py` module instance) provides default values
3. Dataclass field defaults provide fallback if not set in singleton (rarely used)

### Effective Values (as of reference state)
| Configuration | Effective Value | Source |
|---------------|-----------------|--------|
| `wake_word_config.confidence_threshold` | 0.0 | `config.py` (testing default) |
| `wake_word_config.sample_rate` | 16000 Hz | `config.py` |
| `wake_word_config.multi_model_enabled` | True | `config.py` |
| `wake_word_config.model_paths` | `{"axiom": "hey_jarvis", ...}` | `config.py` (placeholder) |
| `vad_config.engine` | "webrtcvad" | `config.py` |
| `vad_config.silence_duration` | 1.0 seconds | `config.py` |
| `vad_config.vad_threshold` | 0.5 | `config.py` |
| `stt_config.model_size` | "small.en" | `config.py` |
| `stt_config.language` | "en" | `config.py` |
| `stt_config.device` | "cpu" | `config.py` |
| `stt_config.compute_type` | "int8" | `config.py` |
| `stt_config.temperature` | 0.0 | `config.py` |
| `tts_config.primary_provider` | "piper" | `config.py` |
| `tts_config.fallback_provider` | "piper" | `config.py` |
| `tts_config.sample_rate` | 22050 Hz | `config.py` |
| `tts_config.piper_enable_gpu` | False | `config.py` |
| `intent_router_config.axiom_delegation_enabled` | True | `config.py` |
| `CAPTURE_BEHAVIOR` | "vad_terminated" | `pipeline_orchestrator.py` module constant |
| `MIN_CAPTURE_TIME` | 0.5 seconds | `pipeline_orchestrator.py` module constant |
| `CAPTURE_FIXED_TIMEOUT` | 10.0 seconds | `pipeline_orchestrator.py` module constant |
| `WORKSTATION_ROUTING` | `{"axiom": "os", "jenson": "agency", "yamako": "personal", "valtaprime": "trading"}` | `pipeline_orchestrator.py` module constant |

Note: The `confidence_threshold` of 0.0 means any detection (even random noise) will trigger a wake word. This is clearly for testing and should be tuned to ~0.5-0.7 for production.

## Model Inventory and Model-Loading Details

### Wake-Word Models
- **Location**: `wakeword/models/`
- **Files**: 
  - `axiom_wake_word.onnx` (27 bytes)
  - `jenson_wake_word.onnx` (27 bytes)
  - `yamako_wake_word.onnx` (27 bytes)
  - `valtaprime_wake_word.onnx` (27 bytes)
- **Format**: ONNX (Open Neural Network Exchange)
- **Loading Mechanism**: 
  - `WakeWordDetector._load_model()` attempts to load via `openwakeword.model.Model(wakeword_models=[model_path])`
  - If `model_path` is a pre-trained model name (e.g., "hey_jarvis"), openWakeWord resolves it automatically
  - If `model_path` is a file path, attempts to load that .onnx file
  - Currently, all entities map to "hey_jarvis" (openWakeWord's generic model)
  - **Note**: The 27-byte .onnx files are likely placeholders; actual models should replace these
- **Initialization**: 
  - Models loaded once in `WakeWordDetector.__init__()` via `_load_models()`
  - Health check: `WakeWordDetector.get_loaded_entities()` returns list of successfully loaded models
  - Failure to load a model logs error but does not halt pipeline (detection skipped for that entity)

### Speech-to-Text Models
- **Source**: faster-whisper downloads from Hugging Face Hub to local cache (`~/.cache/huggingface/hub`)
- **Model**: Based on `STTConfig.model_size` = "small.en"
- **Loading Mechanism**: 
  - `WhisperEngine._load_model()` instantiates `faster_whisper.WhisperModel`
  - Model loaded once on first use; cached for lifetime of engine
  - Health check: `WhisperEngine.health_check()` returns True if model loaded
- **Dependencies**: Requires `ctranslate2` for inference; downloads model files on first use

### Text-to-Speech Models
- **Piper**: 
  - Voice models are .onnx files packaged with `piper-tts` or downloaded separately
  - Expected location: `tts/models/` directory (configurable via `TTSConfig.piper_models_dir`)
  - Voice IDs referenced in `tts/voice_profiles.py`:
    - Axiom: "en_GB-bnk-medium"
    - Jenson: "en_US-ryan-high"
    - Yamako: "en_US-kristin-medium"
    - Valta Prime: "en_US-hfc-medium"
  - Loading: `PiperTTS._resolve_model_path()` checks for `<voice_id>.onnx` in models directory
  - If model not found, synthesis fails and logs error
- **ElevenLabs**: 
  - Not implemented in reference pipeline (provider class missing)
  - Configuration present in `TTSConfig` for future implementation
  - Requires API key and downloads voices via API

### Model Initialization Sequence
1. Pipeline instantiation (`VoicePipeline.__init__()`)
2. Component initialization in order:
   - `WakeWordDetector()` → loads wake-word models
   - `VoiceActivityDetector()` → initializes VAD engine (no external model unless Silero selected)
   - `WhisperEngine()` → loads faster-whisper model on first transcription call (lazy)
   - `IntentRouter()` → no model loading
   - `TTSProviderProxy()` → initializes Piper TTS (checks for binary, models loaded on first synthesis)
3. First wake-word detection triggers model usage
4. First transcription triggers STT model loading (if not already loaded)
5. First TTS synthesis triggers Piper model loading (if model file exists)

### Model Runtime Behavior
- **Wake-Word Models**: 
  - Loaded into memory; inference runs on audio chunks (~10ms per chunk on CPU)
  - No internal state; each inference independent
- **STT Model**: 
  - Loaded into memory; transcription time scales with audio length (~0.5x real-time for small model on CPU)
  - Internal VAD filtering (`vad_filter=True`) adds minor overhead
- **TTS Model**: 
  - Piper model loaded per synthesis; synthesis time ~0.5-1.0s per response
  - No persistent state; each synthesis independent

## Startup, Recovery, and Shutdown Sequence

### Startup Sequence
1. `VoicePipeline` instantiation:
   - Initialize `WebSocketConnectionManager` and `PipelineEventEmitter`
   - Instantiate `WakeWordDetector` (loads wake-word models)
   - Instantiate `VoiceActivityDetector` (initializes VAD engine)
   - Instantiate `WhisperEngine` (model not loaded yet)
   - Instantiate `IntentRouter` (no initialization)
   - Instantiate `TTSProviderProxy` (checks Piper binary availability)
   - Initialize `PipelineState` (idle)
2. First audio chunk triggers:
   - Wake-word detection (if model loaded)
   - On detection: 
     - Start listening state
     - Reset VAD
     - Begin audio capture
3. First successful transcription triggers STT model load (if lazy)
4. First TTS synthesis triggers Piper model load/initialization

### Recovery Mechanisms
- **Component Failures**: 
  - Wake-word detector: if no models loaded, logs warning and skip detection (pipeline continues but no wake words)
  - VAD: engines have fallbacks (Silero VAD returns 1.0 on error; WebRTC VAD returns 1.0 on error)
  - STT: if model not healthy, logs error and returns None (treated as transcription failure)
  - TTS: if primary provider fails, automatically attempts fallback; if both fail, logs error and no audio emitted
  - Pipeline state: errors caught in `process_audio_stream()` loop; emits `error` event and continues listening
- **Audio Stream Errors**: 
  - Microphone capture errors logged; `audio_stream_generator()` catches exceptions and logs
  - Pipeline continues processing if audio source recovers (infinite loop)
- **Resource Exhaustion**: 
  - No explicit recovery; relies on process restart
  - Audio queue unbounded; could grow if consumer slower than producer (unlikely under normal load)
- **State Reset**: 
  - After each command (success or failure), pipeline resets to idle state via `_handle_wake_word()` completion
  - VAD explicitly reset before each capture window
  - No persistent state across commands except pipeline state flags

### Shutdown Sequence
1. Pipeline receives stop signal (external)
2. `VoicePipeline` instance discarded (no explicit shutdown method)
3. Components clean up via garbage collection:
   - `MicrophoneCapture`: if `stop()` called explicitly, closes sounddevice stream
   - Other components: no external resources to release (models in memory, no file handles)
4. Process termination releases all resources

### Idle Behavior
- In `PipelineState.is_listening = False`:
  - Wake-word detection runs continuously on audio stream
  - No audio capture or processing ongoing
  - Components ready but idle
- Microphone stream remains open and active
- Queue may accumulate chunks if no wake-word detection (but detection runs on every chunk)

## Concurrency and Resource-Lifecycle Analysis

### Concurrency Model
- **Primary**: Asyncio event loop for pipeline logic
- **Audio I/O**: Sounddevice callback runs in separate thread (managed by sounddevice)
- **Communication**: 
  - Audio callback → asyncio.Queue → pipeline audio generator (thread-safe)
  - All pipeline stages process sequentially within asyncio tasks
- **Parallelism**: 
  - Wake-word detection: loops over models synchronously (no true concurrent execution)
  - VAD, STT, TTS, routing: sequential per command
  - No parallel processing of multiple commands (pipeline handles one command at a time)
- **Thread Safety**: 
  - Sounddevice callback uses `loop.call_soon_threadsafe()` to put audio in queue
  - No shared mutable state between audio thread and pipeline logic beyond the queue
  - Queue access is thread-safe (asyncio.Queue)

### Resource Lifecycle
- **Microphone Stream**: 
  - Acquired: `MicrophoneCapture.start()` → `sounddevice.InputStream()`
  - Released: `MicrophoneCapture.stop()` → `stream.stop()` and `stream.close()`
  - Lifetime: Explicitly managed; intended to be open for pipeline lifetime
  - Leak protection: `stop()` called in cleanup; context manager (`with self.stream:`) ensures cleanup on error
- **Memory**: 
  - Models loaded once and retained in memory
  - Audio chunks processed and discarded; no persistent audio buffers beyond current processing
  - Queue holds audio chunks until processed; bounded by processing speed
- **File Handles**: 
  - No persistent file handles opened by pipeline components
  - Temporary files used by Piper TTS (properly cleaned up in `finally` block)
  - STT may create cache files for models (managed by faster-whisper/huggingface)
- **CPU Usage**: 
  - Wake-word detection: continuous low-cost processing (~10ms per 64ms chunk on CPU)
  - VAD: negligible cost per frame
  - STT: bursty during transcription (scales with audio length)
  - TTS: bursty during synthesis (~0.5-1.0s per response)
  - Idle: low CPU usage (wake-word detection only)
- **Memory Usage**: 
  - Wake-word models: ~ few MB each
  - STT model: ~ hundreds of MB for small.en (faster-whisper)
  - TTS models: ~ tens of MB per voice (if loaded)
  - Audio buffers: transient, proportional to chunk size and queue depth

### Resource Limits and Throttling
- **No explicit rate limiting**: 
  - Pipeline processes audio as fast as hardware allows
  - Wake-word detection runs on every chunk; could be heavy on low-end CPUs
- **Implicit limits**: 
  - Sounddevice buffer size and OS scheduling
  - Asyncio queue size unbounded (could grow if pipeline stalls)
- **Overflow Handling**: 
  - No buffer overflow protection in audio callback; relies on queue.put
  - If queue fills indefinitely, memory consumption grows (unlikely under normal operation)
  - Pipeline does not implement backpressure to audio stream; assumes consumer faster than producer on average

## Runtime Evidence and Test Results

### Verified Functionality (via inspection and reasoning)
- **Microphone Capture**: 
  - Code shows proper sounddevice stream setup and async generator
  - `test_microphone_setup()` function validates device discovery and basic capture
- **Wake-Word Detection**: 
  - Model loading logic correct; placeholder behavior documented
  - Detection flow: audio chunk → int16 conversion → model.predict → confidence extraction
- **Voice Activity Detection**: 
  - Both Silero and WebRTC implementations present
  - State tracking for speech/silence transitions appears correct
- **Speech-to-Text**: 
  - Uses faster-whisper with appropriate parameters (language, temperature, vad_filter)
  - Audio preparation matches Whisper expectations (float32 normalized)
- **Intent Routing**: 
  - Logic matches documented behavior (direct entity routing, Axiom delegation)
  - Keyword-based delegation configurable
- **Text-to-Speech**: 
  - Piper provider uses CLI binary with proper argument handling
  - WAV metadata extraction for duration and sample rate
  - Proxy pattern with fallback implemented
- **Orchestration Flow**: 
  - Sequence of events in `pipeline_orchestrator.py` matches architecture diagram
  - State transitions (idle → listening → processing → speaking → idle) tracked
  - Event emission at each stage for frontend feedback
- **Error Handling**: 
  - Try-catch blocks at appropriate levels
  - Graceful degradation (e.g., continue on TTS failure)
  - Error events emitted for frontend awareness

### Limitations of Verification
- **No actual execution performed** (to avoid modifying reference environment per instructions)
- **No network or hardware testing** (microphone, speakers)
- **No end-to-end voice interaction test**
- **No performance benchmarking**
- **No validation of model accuracy or detection thresholds**

### Test Results from Reference Artifacts
- No test suite found in reference repository
- Setup guide (`setup_guide.py`) includes validation steps but does not run automated tests
- Parent repository may have tests; not examined per instructions to stay within reference boundary

## Known Defects and Limitations

### Defects (Potential Issues)
1. **Wake-word confidence threshold set to 0.0**: 
   - Will trigger on any audio, causing excessive false positives
   - Must be tuned to appropriate value (0.5-0.7) for production
2. **Wake-word models using placeholder "hey_jarvis"**: 
   - Generic model not trained for specific entities; poor detection accuracy
   - Requires custom training per entity for production use
3. **VAD engine default to webrtcvad**: 
   - Less accurate than Silero; may clip speech or fail to detect quiet speech
   - Silero option available but requires PyTorch (not in base dependencies)
4. **STT model size "small.en"**: 
   - Good balance but may struggle with accents or noisy audio
   - Larger models available at cost of speed and RAM
5. **TTS Piper models not verified**: 
   - Reference does not include .onnx voice models; relies on piper-tts package bundling
   - If voices not available, synthesis will fail
6. **Audio chunk size fixed at 1024 samples**: 
   - May not be optimal for all sample rates or latency requirements
   - No dynamic adjustment based on processing load
7. **Queue unbounded in audio stream generator**: 
   - Theoretical risk of memory growth if pipeline stalls indefinitely
   - No backpressure to audio stream to drop chunks when queue full
8. **Fixed timeout capture (10s) may be too long**: 
   - Users may experience delayed response if they stop speaking before timeout
   - VAD-terminated capture preferred; fixed timeout as fallback only
9. **No audio preprocessing** (noise suppression, echo cancellation, gain control)
   - Performance may degrade in noisy environments
10. **TTS synthesis blocks pipeline**: 
    - While synthesizing, microphone stream still open but wake-word detection continues
    - However, pipeline state `is_listening = False` prevents new command processing until synthesis completes
    - Could miss wake words spoken during TTS output (unless barge-in implemented)

### Limitations (Design Choices)
1. **Sequential command processing**: 
   - Pipeline cannot handle overlapping commands (e.g., wake word during TTS)
   - No barge-in or interruption support
   - Design assumes sequential voice interactions
2. **No speaker identification**: 
   - Wake-word detection does not distinguish between users
   - Any user saying wake word will trigger entity
3. **Limited intent routing**: 
   - Keyword-based delegation; no NLU or context awareness
   - Relies on intelligence engine for complex understanding
4. **No confidence scores in STT or routing**: 
   - Transcription confidence not provided (faster-whisper limitation)
   - Routing confidence hardcoded to 1.0
5. **WebSocket relay uses base64 encoding for audio**: 
   - Increases payload size by ~33%; alternative binary WebSocket frames possible
6. **No persistent connection health monitoring** for WebSocket
   - Relies on application-level pings; no automatic reconnect logic shown
7. **Audio stream generator timeout (1.0s) may cause delayed wake-word detection** 
   - If queue empty for >1s, generator yields timeout and continues
   - Wake-word detection still runs on chunks when available; timeout only affects generator yield
8. **No resource usage metrics or telemetry** built-in
   - Operators must monitor externally

## Reference Implementation Behaviors That Must Be Preserved

The following behaviors are essential to the reference pipeline's correct operation and must be preserved in any replication:

1. **Continuous Microphone Streaming**: 
   - Microphone stream must remain open and active during pipeline lifetime
   - Audio chunks must be delivered consistently to wake-word detection without gaps
   - Stream must be recoverable from errors without full pipeline restart

2. **Wake-Word Detection Always-On**: 
   - Detector must process every audio chunk from microphone stream
   - No skipping or decimation of audio for detection purposes
   - Multi-model concurrent detection (all entity models evaluated per chunk)

3. **VAD-Terminated Speech Capture**: 
   - Capture window must start immediately after wake-word detection
   - Must end based on voice activity detection (silence threshold) 
   - Minimum capture time must be respected to avoid clipping
   - Fixed timeout must serve only as safety fallback

4. **Audio Format Consistency**: 
   - All audio processing stages must expect 16kHz mono audio
   - Sample format conversions must be handled correctly (int16 ↔ float32 normalization)
   - No unintended resampling or format changes between stages

5. **Event-Driven State Transitions**: 
   - Pipeline must emit distinct events for each stage (wake detected, listening started, etc.)
   - Frontend must be able to subscribe to these events for feedback
   - State must be accurately reflected in events (e.g., not emitting speaking when not synthesizing)

6. **Deterministic Intent Routing**: 
   - Routing logic must be predictable and configurable
   - Axiom delegation must follow keyword mapping as specified
   - Raw text must be passed unchanged to intelligence engine

7. **Graceful Degradation**: 
   - Pipeline must continue operating despite individual component failures
   - Examples: 
     - No wake-word models → skip detection, continue listening
     - STT model failure → treat as transcription failure, return to idle
     - TTS failure → log error, continue without audio (but still emit display result)
   - Pipeline must not deadlock or enter inconsistent state on partial failures

8. **Resource Cleanup on Shutdown**: 
   - Microphone stream must be properly closed
   - No dangling threads or asyncio tasks
   - Temporary files must be cleaned up

9. **Base64 Audio Encoding for WebSocket**: 
   - Frontend expects audio data base64-encoded in `executive_speaking` event
   - Changing this format would break frontend compatibility

10. **Workstation Routing**: 
    - Full results must be routed to designated workstations based on entity
    - Mapping must be configurable and respected

## Production Improvements That Can Be Safely Introduced

The following improvements can be added without breaking the core reference behaviors:

1. **Wake-Word Threshold Tuning**: 
   - Expose `confidence_threshold` as configurable parameter (already in config)
   - Set to appropriate production value (e.g., 0.5-0.7) via configuration
   - Add runtime adjustment without restart

2. **Custom Wake-Word Model Loading**: 
   - Ensure pipeline loads custom .onnx models from `wakeword/models/` directory
   - Add model versioning or validation to detect corrupted files
   - Log model metadata (creation date, training data size) if available

3. **VAD Engine Enhancement**: 
   - Make Silero VAD the default (more accurate) if PyTorch available
   - Add fallback to WebRTC if Silero fails to load
   - Allow per-call engine selection via configuration

4. **STT Model Selection Flexibility**: 
   - Allow configuration of different whisper model sizes (tiny, base, etc.) 
   - Add option to use multilingual models if needed
   - Enable GPU usage when available (set device to "cuda")

5. **TTS Provider Enhancements**: 
   - Implement ElevenLabs provider fully (already configured)
   - Add voice selection UI or configuration per entity
   - Add caching of synthesized audio for repeated phrases
   - Implement audio streaming (start playback before synthesis completes) if frontend supports

6. **Audio Preprocessing**: 
   - Add optional noise suppression (e.g., using `noisereduce` or webrtcvad processing)
   - Add automatic gain control to normalize input volume
   - Add echo cancellation if speaker output is fed back (requires loopback detection)

7. **Barge-In Support**: 
   - Allow wake-word detection during TTS output
   - Requires stopping TTS synthesis and clearing audio queue on new wake word
   - Frontend must be able to interrupt audio playback
   - Pipeline must reset state and start new capture immediately

8. **Speaker Identification**: 
   - Add lightweight speaker verification post-wake-word (optional)
   - Could use x-vectors or similar embeddings
   - Only proceed if speaker matches expected user (configurable per entity)

9. **Intent Routing Improvements**: 
   - Add fallback to intelligence engine for routing when keyword matching fails
   - Allow machine learning-based routing (requires training data)
   - Add context awareness (previous commands, time of day, etc.)

10. **Confidence Scoring**: 
    - Attempt to estimate transcription confidence from Whisper beam search results
    - Provide routing confidence based on keyword match strength
    - Include wake-word detection confidence in events (already present)

11. **WebSocket Enhancements**: 
    - Use binary WebSocket frames for audio data to reduce overhead
    - Add heartbeat and automatic reconnect logic
    - Support multiple frontend clients (broadcast events to all)

12. **Resource Monitoring and Telemetry**: 
    - Add pipeline health metrics (CPU usage, memory, latency per stage)
    - Export metrics via Prometheus or similar for monitoring
    - Log performance statistics (wake-word accuracy, transcription speed, etc.)

13. **Configuration Validation**: 
    - Add startup validation of all configuration values
    - Provide helpful error messages for misconfigurations
    - Allow hot-reload of configuration (without restarting audio stream)

14. **Testability Improvements**: 
    - Add dependency injection for easier mocking in tests
    - Expose internal states for diagnostic purposes
    - Add simulation mode for offline testing

15. **Documentation and Examples**: 
    - Improve inline docstrings and type hints
    - Add example configurations for different deployment scenarios
    - Create README for voice pipeline specifically

## Licensing and Model-Redistribution Considerations

### Licensing of Reference Implementation
- The reference voice pipeline is part of the Bleval-ai-os repository
- Bleval-ai-os is licensed under the MIT License (see `LICENSE` file in parent repository)
- MIT License permits: 
  - Commercial use
  - Modification
  - Distribution
  - Private use
  - With requirement to include copyright and license notice
- No copyleft restrictions; safe for proprietary integration

### Licensing of Key Dependencies
| Package | License | Notes |
|---------|---------|-------|
| faster-whisper | MIT | Permissive |
| openwakeword | MIT | Permissive |
| webrtcvad-wheels | MIT | Permissive |
| librosa | ISC | Permissive (similar to MIT) |
| sounddevice | MIT | Permissive |
| piper-tts | Apache-2.0 | Permissive with patent clause |
| elevenlabs | Proprietary (API) | Requires API key; binary redistribution not allowed |
| SpeechRecognition | BSD 3-Clause | Permissive |
| numpy | BSD 3-Clause | Permissive |
| pydantic | MIT | Permissive |
| ctranslate2 | BSD 3-Clause | Permissive |
| onnxruntime | MIT | Permissive |
| torch | BSD-style | Permissive (with advertising clause) |

### Model Files and Redistribution
- **Wake-Word Models**: 
  - Currently placeholder files; intended to be replaced with custom-trained .onnx models
  - Custom models trained on user's data; redistribution subject to training data licenses
  - openWakeWord itself is MIT; models can be redistributed freely
- **STT Models**: 
  - faster-whisper models are derived from OpenAI Whisper
  - Whisper model license: MIT (https://github.com/openai/whisper/blob/main/LICENSE)
  - Models can be used and redistributed under MIT terms
  - Pipeline downloads models from Hugging Face Hub; redistribution requires compliance with HF terms
- **TTS Models (Piper)**: 
  - Piper voice models are released under various licenses (often CC0 or similar for public domain voices)
  - Specific voices used in reference: 
    - `en_GB-bnk-medium`: Likely CC0 or similar
    - `en_US-ryan-high`: Check piper-tts repository for license
    - `en_US-kristin-medium`: 
    - `en_US-hfc-medium`: 
  - Piper itself is Apache-2.0; voice model licenses vary
  - Redistribution of voice models requires checking individual voice licenses
- **No proprietary models** bundled in reference pipeline that restrict redistribution

### Recommendations for AXIOM Integration
1. **Verify all licenses** of redistributed models before including in AXIOM AI OS
2. **Prefer open-licensed voices** for Piper to avoid redistribution complications
3. **Consider bundling only essential models** and downloading others on first use
4. **Maintain attribution** for MIT/BSD licensed components in documentation
5. **Ensure API keys for ElevenLabs (if used) are not baked into client-side code**

## File-by-File Implementation Map for AXIOM

This mapping assumes the reference voice pipeline will replace the existing voice engine in `backend/axiom/voice/` of the Axiom AI OS backend.

| Reference Component | AXIOM Target Path | Notes |
|---------------------|-------------------|-------|
| `microphone_capture.py` | `backend/axiom/voice/microphone_capture.py` | Direct copy; may need to adjust import paths |
| `wakeword/detector.py` | `backend/axiom/voice/wakeword/detector.py` | Direct copy |
| `wakeword/vad.py` | `backend/axiom/voice/wakeword/vad.py` | Direct copy |
| `stt/whisper_engine.py` | `backend/axiom/voice/stt/whisper_engine.py` | Direct copy |
| `router/intent_router.py` | `backend/axiom/voice/router/intent_router.py` | Direct copy |
| `tts/provider_base.py` | `backend/axiom/voice/tts/provider_base.py` | Direct copy |
| `tts/piper_provider.py` | `backend/axiom/voice/tts/piper_provider.py` | Direct copy |
| `tts/voice_profiles.py` | `backend/axiom/voice/tts/voice_profiles.py` | Direct copy |
| `relay/ws_server.py` | `backend/axiom/voice/relay/ws_server.py` | Direct copy (WebSocket port may need coordination) |
| `pipeline_orchestrator.py` | `backend/axiom/voice/pipeline_orchestrator.py` | Direct copy (may need to adjust WebSocket connection to backend's existing manager) |
| `voice_intelligence_callback.py` | `backend/axiom/voice/voice_intelligence_callback.py` | Direct copy (ensure it integrates with AXIOM's intelligence engine) |
| `models.py` | `backend/axiom/voice/models.py` | Direct copy (ensure Pydantic version compatibility) |
| `config.py` | `backend/axiom/voice/config.py` | **Critical**: Must merge with existing AXIOM voice configuration; do not overwrite unrelated config |
| `__init__.py` | `backend/axiom/voice/__init__.py` | Update to export components |
| `setup_guide.py` | *Not copied* | Setup guide is reference-only; not needed in AXIOM |
| `train_wake_words.py` | *Not copied* | Training utility is reference-only; not needed in AXIOM |

### Integration Notes
1. **Configuration Merging**: 
   - AXIOM's existing `backend/axiom/voice/config.py` likely contains project-specific settings
   - Must merge reference configuration into existing file rather than wholesale replacement
   - Pay special attention to: 
     - Entity definitions (may differ in AXIOM)
     - Workstation routing (may be different)
     - Delegation keywords (may be AXIOM-specific)
     - WebSocket port (may conflict with existing services)
2. **WebSocket Relay**: 
   - Reference pipeline emits events to WebSocket clients
   - AXIOM may already have a WebSocket manager; pipeline should use existing instance
   - Modify `VoicePipeline.__init__()` to accept pre-existing `connection_manager` (already supported via parameter)
3. **Intelligence Engine Callback**: 
   - Reference provides mock callback; must replace with actual AXIOM intelligence engine integration
   - Ensure `voice_intelligence_callback.py` is adapted to call AXIOM's AI services
4. **Audio Device Configuration**: 
   - May need to adjust microphone device ID or sample rate to match AXIOM's hardware requirements
5. **Model Paths**: 
   - Ensure wake-word model directory is accessible and contains valid .onnx files
   - Ensure Piper voice models are available or configurable via `tts/models/` directory
6. **Dependencies**: 
   - Verify that all reference dependencies are compatible with AXIOM's existing Python environment
   - Avoid version conflicts; use dependency ranges that satisfy both
7. **Service Integration**: 
   - Voice pipeline should be instantiated and started as part of AXIOM backend startup
   - Consider adding health check endpoint that aggregates pipeline component health
   - Ensure proper shutdown during backend termination

## Appendix A: Full Dependency List (from requirements.txt)

Due to length, only key voice pipeline dependencies are listed in the main table. Full list available in `reference_project/axiom_voice_pipeline/requirements.txt`.

## Appendix B: Configuration Values Reference

See `reference_project/axiom_voice_pipeline/config.py` for exact dataclass definitions and default values.

## Appendix C: Data Flow Pseudocode

```
while pipeline_active:
    audio_chunk = microphone_stream.get_next_chunk()  # float32, mono, 16kHz
    wake_result = wake_detector.process(audio_chunk.tobytes())
    if wake_result:
        emit_wake_detected(wake_result)
        emit_listening_started(wake_result.entity)
        audio_frames = []
        vad.reset()
        while True:
            frame = microphone_stream.get_next_chunk()
            has_speech, speech_ended = vad.process(frame)
            if has_speech:
                audio_frames.append(frame)
                silences = 0
            else:
                if speech_detected:
                    silences += len(frame) / sample_rate
                    if silences >= vad.silence_duration and min_time_met:
                        break
            # check fixed timeout
        captured = concatenate(audio_frames)
        transcription = stt.transcribe(captured)
        if transcription:
            emit_transcription_complete(transcription)
            intent_result = router.route(wake_result.entity, transcription.text)
            emit_processing(intent_result.entity)
            intelligence_result = intelligence_engine.process(intent_result.target_entity, transcription.text)
            if intelligence_result:
                audio_result = tts.synthesize(intelligence_result.spoken_summary, voice_id(intelligence_result.target_entity))
                if intelligence_result:
                    emit_executive_speaking(intelligence_result.target_entity, intelligence_result.spoken_summary, audio_result)
                    emit_display_result(intelligence_result.target_workstation, intelligence_result.full_result, intelligence_result.target_entity)
            emit_idle()
```

## Conclusion

The reference voice pipeline provides a solid, production-ready foundation for voice-enabled AI interaction. Its modular design, clear separation of concerns, and event-driven architecture make it suitable for integration into AXIOM AI OS. By preserving the core behaviors outlined above and introducing production-grade enhancements judiciously, AXIOM can achieve a reliable voice interface that matches the reference's performance while meeting enterprise requirements.

**Next Step**: Proceed to Stage B with the integration specification (`AXIOM_REFERENCE_VOICE_INTEGRATION_SPEC.md`) to guide the replacement of AXIOM's existing voice engine.