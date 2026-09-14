import sys
import asyncio
import numpy as np
sys.path.append('C:\\Users\\byagi\\Desktop\\Bleval-ai-os')
from axiom_voice_pipeline.pipeline_orchestrator import VoicePipeline
from axiom_voice_pipeline.models import WakeWordDetection
from datetime import datetime

async def test_full_pipeline():
    """Test the full pipeline by simulating a wake word detection."""
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
    
    # Create a mock audio source that returns dummy audio data as numpy arrays (matching real pipeline)
    async def mock_audio_source():
        # Generate 1 second of silence (16000 samples at 16kHz) as numpy array
        samples = 16000
        audio = np.zeros(samples, dtype=np.int16)
        yield audio
        # Signal end of stream
        return
    
    # Mock on_intelligence_result callback
    async def mock_intelligence_result(target_entity, command_text):
        from axiom_voice_pipeline.models import IntelligenceEngineOutput, ResultContent
        return IntelligenceEngineOutput(
            full_result=ResultContent(
                type="text",
                content={"response": f"Hello from {target_entity}! You said: {command_text}"},
            ),
            spoken_summary=f"I heard you say {command_text}. This is {target_entity} responding.",
            target_workstation="os"
        )
    
    print("\nProcessing simulated wake word through pipeline...")
    try:
        # This will run the full wake word handling flow
        await pipeline._handle_wake_word(
            wake_result=wake_result,
            audio_source=mock_audio_source(),
            on_intelligence_result=mock_intelligence_result
        )
        print("\nPipeline processing completed.")
    except Exception as e:
        print(f"\nError during pipeline processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())