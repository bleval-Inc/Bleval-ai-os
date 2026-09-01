# Vosk Integration – Updated Voice Engine (Axiom AI OS)

**Overview**  
This document captures the latest changes to the offline voice‑engine implementation that replaces the browser `SpeechRecognition` API with the local Vosk library for wake‑word detection and transcription.

## Key Changes Made

1. **Removed `"network"` from `terminalErrors`**  
   - Updated the error set to `{ "audio-capture", "not-allowed", "service-not-allowed" }`.  
   - Eliminates the “Speech recognition unavailable (network)” warning.

2. **Vosk Model Loading**  
   - Dynamically injects the Vosk script via CDN.  
   - Loads the small English model (`vosk-model-small-en-us-v0.5.1`) the first time the listener starts.  
   - Ensures the model is cached to avoid duplicate fetches.

3. **Keyword‑Spotting (KWS) recognizer**  
   - Instantiates `window.vosk.Kws` with wake‑words defined in `EXECUTIVE_CONFIG`.  
   - Processes audio chunks from the microphone pipeline and calls `wakeExecutiveByName` on matches.

4. **Fallback Handling**  
   - If Vosk fails to load or the model is unavailable, the code automatically reverts to the original `SpeechRecognition` flow, preserving functionality.

5. **UI Preservation**  
   - All dashboard components (calendar, schedule, habit‑tracker, weather, emergency banner, microphone widget, tooltips, etc.) remain untouched.  
   - Only internal voice‑engine logic was modified.

## Supporting Files

- `references/vosk-integration.md` – original implementation details and patches.  
- `templates/vosk-starter.tsx` – starter template for future voice‑engine rewrites.  
- `scripts/vosk-verify.js` – verification script to confirm Vosk model loading and basic functionality.

## Pitfalls & Recommendations

- **Model Load Race** – Ensure the Vosk script resolves before `startWakeListener` executes; otherwise the fallback will always trigger.  
- **Compatibility** – The CDN currently serves only the small English model. For other languages, update the model URL accordingly.  
- **Script Injection Safety** – Inject the Vosk script only when `typeof window !== 'undefined'` and only once to avoid duplicate loads.

## Verification Steps

1. Open the dashboard and grant microphone permission.  
2. Verify that no “network” related error appears in the console.  
3. Speak a configured wake‑word (e.g., “axiom on”).  
4. Confirm that the appropriate executive action fires and the UI updates accordingly.  
5. Check that all existing dashboard components continue to render correctly.

---  
*Document generated on 2026‑08‑29 by the Hermes voice‑engine integration skill.*