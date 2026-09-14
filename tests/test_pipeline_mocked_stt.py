import sys
import asyncio
import numpy as np
from unittest.mock import AsyncMock, patch
sys.path.append('C:\\Users\\byagi\\Desktop\\Bleval-ai-os')
from axiom_voice_pipeline.pipeline_orchestrator import VoicePipeline
from axiom_voice_pipeline.models import WakeWordDetection, TranscriptionComplete, ResultContent, IntelligenceEngineOutput
from datetime import datetime

async def test_pipeline_with_mocked_stt():
    """Test the pipeline with a mocked STT to simulate a command."""
    print("Initializing voice pipeline...")
    pipeline = VoicePipeline()
    print(f"Pipeline health: {pipeline.health_check()}")
    
    # Simulate a wake word detection for axiom
    wake_result = WakeWordDetection(
        wake_entity="axiom",
        confidence=0.8,
        timestamp=datetime.now()
    )
    print(f"\nSimulating wake word detection: {wake_result}")
    
    # Create a mock audio source that returns some dummy audio data (numpy array)
    async def mock_audio_source():
        # Generate 1 second of audio (16000 samples at 16kHz) - let's use a sine wave to mimic speech
        samples = 16000
        t = np.linspace(0, 1, samples, False)
        audio = np.sin(2 * np.pi * 200 * t) * 0.3  # 200 Hz tone
        audio_int16 = (audio * 32767).astype(np.int16)
        yield audio_int16
        # Signal end of stream
        return
    
    # Mock on_intelligence_result callback
    async def mock_intelligence_result(target_entity, command_text):
        print(f"[Mock Intelligence] Target entity: {target_entity}, Command: {command_text}")
        return IntelligenceEngineOutput(
            full_result=ResultContent(
                type="text",
                content={"response": f"Hello from {target_entity}! You said: {command_text}"},
            ),
            spoken_summary=f"I heard you say {command_text}. This is {target_entity} responding.",
            target_workstation="os"
        )
    
    # Mock the STT transcribe method to return a fixed transcription
    # We'll patch the stt.transcribe method of the pipeline's stt instance
    original_transcribe = pipeline.stt.transcribe
    def mock_transcribe(audio_bytes_wav):
        # Return a fixed transcription
        print(f"[Mock STT] Transcribing audio bytes of length {len(audio_bytes_wav)}")
        # We'll return a transcription that says "hello axiom"
        return TranscriptionComplete(
            raw_text="hello axiom",
            language="en",
            language_probability=0.99
        )
    pipeline.stt.transcribe = mock_transcribe
    
    print("\nProcessing simulated wake word through pipeline with mocked STT...")
    try:
        # This will run the full wake word handling flow
        await pipeline._handle_wake_word(
            wake_result=wake_result,
            audio_source=mock_audio_source(),
            on_intelligence_result=mock_intelligence_result
        )
        print("\nPipeline processing completed successfully.")
    except Exception as e:
        print(f"\nError during pipeline processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original transcribe method
        pipeline.stt.transcribe = original_transcribe

if __name__ == "__main__":
    asyncio.run(test_pipeline_with_mocked_stt())