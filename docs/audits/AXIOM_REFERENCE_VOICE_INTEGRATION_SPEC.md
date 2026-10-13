# AXIOM_REFERENCE_VOICE_INTEGRATION_SPEC.md

## Integration Specification: Replacing AXIOM's Voice Engine with Reference Implementation

This document specifies how to integrate the reference voice pipeline (from `/c/Users/byagi/Desktop/Bleval-ai-os/axiom_voice_pipeline`) into the AXIOM AI OS backend, replacing the existing voice engine in `backend/axiom/voice/`. The goal is to faithfully reproduce the reference pipeline's proven architecture while making necessary adaptations for AXIOM's ecosystem.

## 1. Integration Goals

- Replace AXIOM's current voice engine (in `backend/axiom/voice/`) with a replicated implementation of the reference voice pipeline
- Preserve all core behaviors of the reference pipeline (continuous streaming, wake-word detection, VAD-terminated capture, etc.)
- Adapt configuration to align with AXIOM's existing systems (entity names, workstation routing, intelligence engine interface)
- Leverage AXIOM's existing infrastructure where appropriate (WebSocket manager, service lifecycle, dependency management)
- Ensure backward compatibility with AXIOM's frontend and API contracts where possible
- Introduce production-grade improvements only after reference behavior is verified

## 2. Components to Replace

The following directories/files in `backend/axiom/voice/` will be replaced or updated with reference implementations:

| Existing AXIOM Component | Action | Reference Source | Notes |
|--------------------------|--------|------------------|-------|
| `microphone_capture.py` | Replace | `axiom_voice_pipeline/microphone_capture.py` | Direct copy; verify sounddevice compatibility |
| `wakeword/` directory | Replace | `axiom_voice_pipeline/wakeword/` | Includes detector.py and vad.py |
| `stt/` directory | Replace | `axiom_voice_pipeline/stt/` | Includes whisper_engine.py |
| `router/` directory | Replace | `axiom_voice_pipeline/router/` | Includes intent_router.py |
| `tts/` directory | Replace | `axiom_voice_pipeline/tts/` | Includes provider_base.py, piper_provider.py, voice_profiles.py |
| `relay/` directory | Replace | `axiom_voice_pipeline/relay/` | Includes ws_server.py (WebSocket relay) |
| `pipeline_orchestrator.py` | Replace | `axiom_voice_pipeline/pipeline_orchestrator.py` | Main orchestrator |
| `voice_intelligence_callback.py` | Replace | `axiom_voice_pipeline/voice_intelligence_callback.py` | Adapt to AXIOM's intelligence engine |
| `models.py` | Replace | `axiom_voice_pipeline/models.py` | Data contracts; ensure Pydantic version compatibility |
| `config.py` | Merge | `axiom_voice_pipeline/config.py` | Merge with existing config; do not overwrite |
| `__init__.py` | Update | `axiom_voice_pipeline/__init__.py` | Export components for AXIOM's import structure |

### Components to Retain (Non-Voice or Unrelated)
- Any non-voice files in `backend/axiom/voice/` not listed above (verify existence)
- `backend/axiom/config.py` (global AXIOM configuration)
- `backend/axiom/models/` (non-voice Pydantic models)
- `backend/axiom/engine/` (core engines)
- `backend/axiom/runtime/` (execution layer)
- `backend/main.py` (FastAPI entry point)
- `backend/requirements.txt` (dependency management)

## 3. Configuration Mapping

AXIOM's existing voice configuration (if any) must be merged with the reference configuration. The following mapping outlines how reference configuration values should be adapted for AXIOM.

### 3.1 Entity Definitions
Reference entities: `axiom`, `jenson`, `yamako`, `valtaprime`
AXIOM entities: Likely same or subset; verify from AXIOM's existing configuration.
- **Action**: Update `config.py`'s `ENTITIES` dict to match AXIOM's entity roster
- **Wake phrases**: Customize per AXIOM's branding (e.g., "Hey Axiom" may already be correct)
- **Voice models**: Map AXIOM's preferred TTS voices to entities (reference provides Piper voice IDs)
- **Delegation capable**: Set to `True` only for entities that can delegate in AXIOM's hierarchy (likely only the main executive entity)

### 3.2 Audio Configuration
- **Sample rate**: Reference uses 16000 Hz; verify AXIOM's hardware and downstream components support this
- **Chunk size**: Reference 1024 samples (~64ms); acceptable for most use cases
- **Channels**: Mono (1) only; ensure AXIOM's audio pipeline does not expect stereo

### 3.3 Wake-Word Detection
- **Confidence threshold**: 
  - Reference default: 0.0 (testing)
  - AXIOM production: Set to 0.5-0.7 (tune based on false positive/negative testing)
  - Expose via configuration for runtime adjustment
- **Model paths**: 
  - Reference maps entities to "hey_jarvis" placeholder
  - AXIOM must provide custom .onnx models per entity in `wakeword/models/`
  - Consider using environment variable or config to point to model directory
- **Multi-model**: Keep enabled (True) for concurrent entity detection

### 3.4 Voice Activity Detection
- **Engine**: 
  - Reference default: "webrtcvad"
  - AXIOM recommendation: Use "silero" if PyTorch available (more accurate)
  - Add fallback logic: try Silero, fall back to WebRTC
- **Silence duration**: Reference 1.0s; tune based on testing (0.5s-2.0s)
- **VAD threshold**: 0.5 (engine-dependent); may need tuning
- **Minimum speech duration**: Reference 0.5s; adjust to avoid false triggers

### 3.5 Speech-to-Text
- **Model size**: Reference "small.en"; AXIOM may choose based on performance/accuracy tradeoff
  - Options: tiny (fastest, least accurate), base, small, medium, large-v3 (slowest, most accurate)
- **Language**: Reference "en"; AXIOM may need multilingual support (consider multi-model or language ID)
- **Device**: Reference "cpu"; AXIOM should set to "cuda" if GPU available
- **Compute type**: Reference "int8"; adjust based on device (float16 for GPU, int8 for CPU)
- **Temperature**: Reference 0.0 (deterministic); keep for consistency
- **VAD filter**: Keep `vad_filter=True` to remove silent sections

### 3.6 Text-to-Speech
- **Primary provider**: Reference "piper"; AXIOM may keep or add ElevenLabs as primary for premium voices
- **Fallback provider**: Reference "piper"; consider setting to "elevenlabs" if primary fails and API key available
- **Sample rate**: Reference 22050 Hz; verify matches AXIOM's audio playback expectations
- **Piper GPU enable**: Reference False; keep False (Piper primarily CPU)
- **Piper models directory**: Reference `tts/models/`; AXIOM must ensure voice .onnx files are present
- **ElevenLabs API key**: Must be sourced from AXIOM's secure configuration (e.g., environment variable or vault)
- **ElevenLabs voice stability/similarity**: Tune based on voice preference (0.0-1.0)

### 3.7 Intent Router
- **Axiom delegation enabled**: Reference True; AXIOM should set based on whether delegation logic is desired
- **Delegation keywords**: 
  - Reference: 
    - jenson: ["agency", "bleval", "client", "campaign", "project"]
    - valtaprime: ["trading", "trades", "market", "portfolio", "investment"]
    - yamako: ["personal", "schedule", "reminder", "calendar", "daily"]
  - AXIOM: Customize to match AXIOM's entity responsibilities and domain keywords
- **Intent classification**: Reference uses keyword heuristics; AXIOM may replace with intelligence engine-based classification if desired

### 3.8 Capture Window Behavior
- **Capture behavior**: Reference "vad_terminated" (recommended); keep as primary
- **Fixed timeout**: Reference 10.0s; consider reducing to 5.0s-8.0s as fallback
- **Minimum capture time**: Reference 0.5s; reasonable for most commands

### 3.9 Workstation Routing
- Reference mapping: 
  - axiom → "os"
  - jenson → "agency"
  - yamako → "personal"
  - valtaprime → "trading"
- AXIOM: Verify if these workstation names exist; adjust mapping to match AXIOM's frontend workstations
- If AXIOM uses different workstation identifiers, update `WORKSTATION_ROUTING` accordingly

### 3.10 WebSocket Relay
- **Host**: Reference "127.0.0.1"; AXIOM may use "0.0.0.0" or specific interface
- **Port**: Reference 8002; must not conflict with AXIOM's existing services (e.g., main API on 8000)
  - Consider using a port from AXIOM's reserved range (e.g., 8008-8010)
  - Or share AXIOM's existing WebSocket endpoint if appropriate (see below)
- **Enable compression**: Reference True; keep for bandwidth efficiency
- **Ping interval/timeout**: Reference 30.0s/10.0s; adjust based on network reliability

### 3.11 Integration with AXIOM's WebSocket System
If AXIOM already has a WebSocket manager for frontend communication:
- Modify `VoicePipeline.__init__()` to accept pre-existing `WebSocketConnectionManager` (already supported)
- Do not instantiate new manager in pipeline; use AXIOM's instance
- Ensure event types (`wake_detected`, `executive_speaking`, etc.) are compatible with frontend expectations
- If AXIOM uses different event structure, adapt `PipelineEventEmitter` to match

## 4. Interface Adaptations

### 4.1 Intelligence Engine Interface
The reference pipeline expects an `on_intelligence_result` callback with signature:
```python
async def on_intelligence_result(target_entity: str, command_text: str) -> IntelligenceEngineOutput
```
AXIOM must provide this callback that:
1. Calls AXIOM's intelligence engine (Anthropic Claude, OpenAI GPT, or mock)
2. Returns `IntelligenceEngineOutput` with:
   - `full_result`: `ResultContent` for display on workstation UI
   - `spoken_summary`: Natural language summary for TTS (1-3 sentences)
   - `target_workstation`: Workstation ID for full result display (must match AXIOM's workstation routing)
3. Handles errors gracefully (returns structured error result or raises exception)

### 4.2 Event Compatibility with AXIOM Frontend
Reference pipeline emits events over WebSocket:
- `wake_detected`
- `listening_started`
- `transcription_complete`
- `processing`
- `executive_speaking` (includes base64-encoded audio)
- `display_result`
- `idle`
- `error`

AXIOM's frontend must be able to handle these events. If AXIOM uses different event types:
- Option A: Update frontend to match reference events (preferred for consistency)
- Option B: Adapt `PipelineEventEmitter` to map reference events to AXIOM's event format
- Ensure audio data in `executive_speaking` is base64-encoded WAV (frontend expects this)

### 4.3 API Endpoints
Reference pipeline does not define REST endpoints; it is purely event-driven via WebSocket.
If AXIOM requires REST endpoints for voice pipeline control (e.g., health check, configuration):
- Add thin wrapper endpoints in AXIOM's backend that delegate to pipeline instance
- Example endpoints:
  - `GET /api/v1/voice/health` → aggregate component health checks
  - `POST /api/v1/voice/suspend` → pause pipeline
  - `POST /api/v1/voice/resume` → resume pipeline
  - `GET /api/v1/voice/config` → get non-sensitive configuration
  - `POST /api/v1/voice/test/synthesize` → test TTS for an entity

## 5. Production-Grade Improvements (Post-Verification)

After reference behavior is verified, consider these improvements:

### 5.1 Audio and Concurrency
- **Explicit microphone ownership**: Ensure pipeline is sole owner of audio device; add device lock if needed
- **Idempotent startup/shutdown**: Make `start()` and `stop()` safe to call multiple times
- **Bounded audio queue**: Replace `asyncio.Queue` with `asyncio.Queue(maxsize=N)` to prevent unbounded growth
- **Overflow policy**: Define behavior when queue full (drop oldest/newest block)
- **Backpressure to audio stream**: Implement mechanism to signal sounddevice to drop chunks if pipeline stalled
- **Device disconnection recovery**: Add error handling for `sounddevice` errors; attempt reconnect
- **Deterministic cancellation**: Use asyncio tasks with proper cancellation handling for pipeline components

### 5.2 Wake-Word and Command Processing
- **Configurable wake-word threshold**: Expose at runtime via configuration reload
- **Duplicate prevention**: Add timestamp-based deduplication to prevent same audio triggering multiple detections
- **Bounded phrase duration**: Already via VAD and fixed timeout; ensure values are appropriate
- **Explicit empty transcript handling**: Log and emit specific event for silent commands
- **Reliable listening resumption**: Ensure pipeline returns to idle state after every command (success/failure/timeout)

### 5.3 Speech Output
- **Barge-in support**: 
  - Allow wake-word detection during TTS output
  - Requires stopping TTS synthesis and clearing audio pipeline
  - Frontend must support interrupting audio playback
- **TTS streaming**: 
  - Modify Piper provider to start playback before synthesis completes (if frontend supports)
  - Alternatively, use WebSocket binary frames to stream audio chunks
- **Output volume normalization**: 
  - Apply gain control to synthesized audio to match system volume
- **Audio routing**: 
  - Ensure TTS output does not interfere with microphone input (acoustic echo cancellation if needed)

### 5.4 Configuration and Operations
- **Startup validation**: 
  - Validate model paths, audio parameters, required configuration
  - Fail fast with clear error messages if misconfigured
- **Health endpoint**: 
  - Expose detailed component health (wake-word models loaded, STT model healthy, TTS available, etc.)
  - Include latency statistics if available
- **Credential protection**: 
  - Ensure API keys (ElevenLabs) are loaded from secure vault/environment, not hardcoded
  - Avoid logging any keys or tokens
- **Optional cloud services**: 
  - Design TTS fallback to work even if ElevenLabs API key missing
  - Keep local Piper path as primary to ensure voice functionality without internet

### 5.5 Observability
- **Metrics collection**: 
  - Track wake-word detection rate, false positives (if ground truth available)
  - Measure latency: wake-word to transcript, transcript to TTS start, etc.
  - Monitor resource usage: CPU, memory, audio queue size
- **Logging enhancement**: 
  - Add structured logging (JSON) for easier parsing
  - Log performance counters at configurable intervals
- **Audit trail**: 
  - Log voice commands (anonymized if needed) for compliance and improvement

## 6. Validation and Testing Plan

### 6.1 Unit Tests
- Test each component in isolation with mocked dependencies
- Wake-word detector: test model loading and detection logic
- VAD: test speech/silence state transitions
- STT: test audio preparation and transcription (mock WhisperModel)
- TTS: test synthesis pipeline (mock subprocess)
- Router: test routing logic and delegation
- Orchestrator: test state transitions and event emission

### 6.2 Integration Tests
- Test pipeline with mocked audio source and intelligence engine
- Verify full flow: wake word → capture → transcription → routing → intelligence → TTS → events
- Test error paths: component failures, timeouts, empty audio
- Test configuration changes (reload without restart)

### 6.3 System Tests
- Deploy in AXIOM staging environment
- Test with real microphone and speakers
- Validate end-to-end voice command execution
- Check frontend receives events and displays/plays audio correctly
- Test multiple sequential commands
- Test behavior during TTS output (if barge-in not implemented, ensure no false wakewords)

### 6.4 Performance Tests
- Measure latency budgets:
  - Wake-word detection: < 50ms per chunk
  - End-to-end: < 2s for simple command (wake word to audio playback start)
- Resource usage:
  - CPU: < 20% on mid-range desktop
  - Memory: < 500MB additional
  - Audio dropout: < 1% under load

### 6.5 Regression Tests
- Verify existing AXIOM functionality unaffected:
  - Non-voice APIs still work
  - Executive agents and workflows functional
  - Memory system and persistence intact
  - Dashboard loads and shows data
  - Health endpoints (`/liveness`, `/readiness`) still respond

## 7. Rollback Procedure

### 7.1 Backup
- Before integration, backup existing `backend/axiom/voice/` directory:
  ```bash
  cp -r backend/axiom/voice backend/axiom/voice.backup_$(date +%Y%m%d_%H%M%S)
  ```

### 7.2 Rollback Steps
1. Stop AXIOM backend service
2. Remove new voice engine files:
   ```bash
   rm -rf backend/axiom/voice/microphone_capture.py
   rm -rf backend/axiom/voice/wakeword/
   rm -rf backend/axiom/voice/stt/
   rm -rf backend/axiom/voice/router/
   rm -rf backend/axiom/voice/tts/
   rm -rf backend/axiom/voice/relay/
   rm -rf backend/axiom/voice/pipeline_orchestrator.py
   rm -rf backend/axiom/voice/voice_intelligence_callback.py
   rm -rf backend/axiom/voice/models.py
   ```
3. Restore backup:
   ```bash
   cp -r backend/axiom/voice.backup_*/ backend/axiom/voice/
   ```
4. Restart AXIOM backend service

### 7.3 Verification After Rollback
- Confirm AXIOM backend starts without errors
- Verify voice functionality reverts to previous state
- Check that non-voice components remain operational

## 8. Acceptance Criteria

The integration is complete when:

### 8.1 Functional Criteria
- [ ] Continuous microphone streaming verified (no audio gaps between commands)
- [ ] Wake-word detection works for all AXIOM entities with < 5% false positive rate in quiet environment
- [ ] Voice activity detection correctly captures speech endpoints (no clipping, minimal trailing silence)
- [ ] Speech-to-text transcription achieves > 80% word accuracy on clear speech in AXIOM's accent
- [ ] Intent routing correctly maps commands to appropriate entities based on configuration
- [ ] Intelligence engine receives commands and returns structured results
- [ ] Text-to-speech synthesis produces audible, intelligible output for all entities
- [ ] WebSocket events emitted at each stage with correct payloads
- [ ] Frontend displays results and plays audio without user intervention
- [ ] System returns to idle state after each command (success or failure)
- [ ] Subsequent commands can be processed without restarting pipeline
- [ ] Pipeline handles errors gracefully (component failure, audio dropout, etc.)

### 8.2 Performance Criteria
- [ ] End-to-end latency (wake word to audio start) < 2.0 seconds for simple commands
- [ ] CPU usage < 30% during idle listening on target hardware
- [ ] Memory usage increase < 400MB over baseline
- [ ] No audio dropouts or stutters during prolonged operation (> 1 hour)

### 8.3 Compatibility Criteria
- [ ] Existing AXIOM REST APIs (`/api/v1/...`) remain functional
- [ ] Executive agents and workflows can be triggered via non-voice means
- [ ] Dashboard loads and shows real-time data
- [ ] Health endpoints `/liveness` and `/readiness` return healthy status
- [ ] Non-voice text commands (if any) still work
- [ ] Existing API authentication and authorization unaffected

### 8.4 Operational Criteria
- [ ] Pipeline starts automatically with AXIOM backend
- [ ] Pipeline shuts cleanly on backend termination
- [ ] No resource leaks (file descriptors, threads, memory) after prolonged operation
- [ ] Logs show appropriate levels (not excessive debug in production)
- [ ] Configuration changes (if supported) take effect without restart
- [ ] Rollback procedure works and restores previous voice functionality

## 9. Open Questions and Unverified Behaviors

### 9.1 Hardware-Dependent Behavior (Requires Physical Testing)
- [ ] Actual microphone device selection and performance on AXIOM's target hardware
- [ ] Speaker output volume and clarity without distortion
- [ ] Acoustic echo cancellation if microphone and speakers are co-located
- [ ] Performance under various noise conditions (office, factory, vehicle)
- [ ] Wake-word detection accuracy with distance and angle variation
- [ ] False positive rate in noisy environments (HVAC, machinery, speech)

### 9.2 Configuration and Integration Points
- [ ] Exact format of AXIOM's intelligence engine output (to adapt `voice_intelligence_callback.py`)
- [ ] Whether AXIOM's frontend expects different event structure or audio encoding
- [ ] If AXIOM already uses a WebSocket manager, how to share it without port conflicts
- [ ] Location of secure credential storage for ElevenLabs API key (if used)
- [ ] How AXIOM manages Python dependencies and version conflicts

### 9.3 Production Readiness Indicators
- [ ] Long-term stability test (24+ hours continuous operation)
- [ ] Recovery from simulated hardware failure (microphone unplugged/replugged)
- [ ] Behavior when intelligence engine is slow or unavailable
- [ ] Load testing with multiple rapid commands in succession
- [ ] Interaction with AXIOM's update and restart mechanisms

### 9.4 Legal and Licensing Considerations
- [ ] Verify licensing of any custom wake-word models to be used in production
- [ ] Confirm Piper voice licenses allow redistribution in AXIOM's deployment model
- [ ] Ensure ElevenLabs usage complies with terms of service (if API key used)
- [ ] Check that no GPL or copyleft licenses are inadvertently included via transitive dependencies

## 10. Next Steps

1. **Review and Approval**: Present this specification to stakeholders for review and approval
2. **Environment Preparation**: 
   - Set up AXIOM development environment with access to reference voice pipeline
   - Ensure all dependencies can be installed without conflict
3. **Implementation Phase**: 
   - Copy reference components to `backend/axiom/voice/` per mapping
   - Merge configuration files
   - Adapt intelligence engine callback
   - Adjust WebSocket integration as needed
4. **Verification Phase**: 
   - Run unit and integration tests in isolation
   - Deploy to staging and perform system tests
   - Address any defects or mismatches
5. **Production Rollout**: 
   - Schedule deployment during maintenance window
   - Monitor closely for first 24-48 hours
   - Have rollback procedure ready
6. **Post-Implementation Review**: 
   - Collect metrics and user feedback
   - Identify areas for further optimization
   - Plan iterative improvements based on data

## Appendix A: Component-Specific Adaptation Notes

### microphone_capture.py
- No changes needed unless AXIOM requires specific microphone device ID
- Consider adding method to list devices for diagnostics
- Ensure sounddevice version compatibility with AXIOM's Python

### wakeword/detector.py
- Update model loading to check for custom .onnx files first
- Add fallback to openWakeWord's pre-trained models if custom not found
- Log model load status and validation (file size, modification time)

### wakeword/vad.py
- Add logic to try Silero VAD first, fall back to WebRTC
- Expose engine choice and parameters via configuration
- Add diagnostics for VAD performance (speech detection rate)

### stt/whisper_engine.py
- Make model size, language, device, compute type fully configurable
- Add option to use multilingual models if needed
- Log model load time and VRAM/RAM usage

### router/intent_router.py
- Customize delegation keywords to match AXIOM's entity responsibilities
- Consider adding fallback to intelligence engine for routing
- Add unit tests for routing logic

### tts/piper_provider.py
- Verify voice .onnx files exist in specified directory
- Add caching of synthesized audio for repeated phrases (if useful)
- Consider implementing audio streaming if frontend supports

### tts/voice_profiles.py
- Update voice IDs to match AXIOM's selected Piper voices
- Add mapping for ElevenLabs voices if used
- Ensure voice characteristics match entity personas

### relay/ws_server.py
- Change host/port to match AXIOM's WebSocket configuration
- If sharing AXIOM's existing WebSocket manager, remove WS server instantiation
- Ensure event types match frontend expectations
- Consider adding authentication/token validation if required by AXIOM

### pipeline_orchestrator.py
- Verify import paths after copying to new location
- Ensure `connection_manager` parameter is used correctly (accept pre-existing manager)
- Adjust logging levels to match AXIOM's standards
- Add health check method that aggregates component status (already present)

### voice_intelligence_callback.py
- Replace mock implementation with actual call to AXIOM's intelligence engine
- Map AXIOM's engine output to `IntelligenceEngineOutput` structure
- Handle engine errors and timeouts gracefully
- Ensure `spoken_summary` is concise and natural-sounding
- Set `target_workstation` based on entity (use `WORKSTATION_ROUTING` from config)

### models.py
- Verify Pydantic version compatibility with AXIOM's existing models
- Ensure no field name conflicts with other AXIOM models
- Consider adding `__str__` methods for better logging

## Appendix B: Example Configuration Merge

Example of how to merge reference `config.py` with AXIOM's existing voice configuration:

```python
# In backend/axiom/voice/config.py
# Start with AXIOM's existing configuration (if any)
# Then overlay reference configuration, adapting values as needed

# ENTITIES: Update to match AXIOM's roster
ENTITIES = {
    "axiom": EntityProfile(
        name="axiom",
        display_name="Axiom AI",
        wake_phrases=["axiom", "hey axiom", "axiom ai"],
        voice_model="en_GB-bnk-medium",
        voice_character="female_british_secret_agent",
        delegation_capable=True,  # Only if AXIOM allows delegation
    ),
    # ... other entities as per AXIOM's hierarchy
}

# Wake-word config: use reference structure but adjust thresholds
wake_word_config = WakeWordConfig(
    confidence_threshold=0.6,  # Tuned for production
    sample_rate=16000,
    channels=1,
    multi_model_enabled=True,
    model_paths={  # Point to custom models
        "axiom": "wakeword/models/axiom_wake_word.onnx",
        "jenson": "wakeword/models/jenson_wake_word.onnx",
        "yamako": "wakeword/models/yamako_wake_word.onnx",
        "valtaprime": "wakeword/models/valtaprime_wake_word.onnx",
    }
)

# VAD config: prefer Silero if available
try:
    import torch
    vad_engine = "silero"
except ImportError:
    vad_engine = "webrtcvad"

vad_config = VADConfig(
    engine=vad_engine,
    silence_duration=1.0,
    vad_threshold=0.5 if vad_engine == "webrtcvad" else 0.4,  # Silero threshold different
    min_speech_duration=0.5,
)

# STT config: adjust for AXIOM's needs
stt_config = STTConfig(
    model_size="medium",  # AXIOM chose medium for better accuracy
    language="en",
    device="cuda" if torch.cuda.is_available() else "cpu",
    compute_type="float16" if torch.cuda.is_available() else "int8",
    temperature=0.0,
)

# TTS config: AXIOM may use ElevenLabs as primary for premium voices
tts_config = TTSConfig(
    primary_provider="elevenlabs",  # Change if ElevenLabs available and desired
    fallback_provider="piper",
    sample_rate=22050,
    piper_enable_gpu=False,
    piper_models_dir="tts/models/",
    elevenlabs_api_key="",  # Set from secure config
    elevenlabs_voice_stability=0.5,
    elevenlabs_voice_similarity_boost=0.75,
)

# Intent router: AXIOM-specific delegation keywords
intent_router_config = IntentRouterConfig(
    axiom_delegation_enabled=True,
    delegation_keywords={
        "jenson": ["client", "project", "agency", "bleval"],  # AXIOM's terms
        "valtaprime": ["trade", "portfolio", "market", "investment"],  # AXIOM's terms
        "yamako": ["personal", "home", "family", "schedule"],  # AXIOM's terms
    }
)

# Workstation routing: verify AXIOM's workstation names
WORKSTATION_ROUTING = {
    "axiom": "os",
    "jenson": "agency",
    "yamako": "personal",
    "valtaprime": "trading",
    # Add any AXIOM-specific workstations
}

# Capture behavior: keep reference recommendations
CAPTURE_BEHAVIOR = "vad_terminated"
MIN_CAPTURE_TIME = 0.5
CAPTURE_FIXED_TIMEOUT = 8.0  # Reduced from 10s for faster fallback
```

## Conclusion

This specification provides a comprehensive roadmap for replacing AXIOM's existing voice engine with the reference implementation. By following the outlined configuration mappings, interface adaptations, and validation steps, AXIOM can achieve a robust voice interface that leverages the reference pipeline's proven architecture while meeting enterprise requirements.

The integration preserves all essential behaviors of the reference pipeline (continuous streaming, wake-word detection, VAD-terminated capture, etc.) and allows for production-grade enhancements to be introduced after verification. Proper testing, rollback procedures, and acceptance criteria ensure a controlled and reversible integration process.

**Next Step**: Proceed with implementation Phase 1 (copying components and merging configuration) as outlined in Section 10.