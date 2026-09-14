import sys
import asyncio
import numpy as np
sys.path.append('C:\\Users\\byagi\\Desktop\\Bleval-ai-os')
from axiom_voice_pipeline.pipeline_orchestrator import VoicePipeline

async def test_pipeline():
    print("Creating VoicePipeline...")
    pipeline = VoicePipeline()
    print(f"Pipeline health: {pipeline.health_check()}")
    
    # Create a mock audio source that yields 5 chunks of silence and then stops
    async def mock_audio_source():
        sample_rate = 16000
        chunk_duration = 0.1  # 100 ms
        chunk_size = int(sample_rate * chunk_duration)
        silent_chunk = np.zeros(chunk_size, dtype=np.int16)
        for i in range(5):
            yield silent_chunk
            await asyncio.sleep(0.01)  # small delay to simulate real-time
    
    # We'll run the pipeline for a short time and then cancel
    async def run_pipeline():
        try:
            await pipeline.process_audio_stream(
                mock_audio_source(),
                on_intelligence_result=lambda entity, text: print(f"Intelligence result: {entity} - {text}")
            )
        except asyncio.CancelledError:
            print("Pipeline task cancelled")
        except Exception as e:
            print(f"Pipeline error: {e}")
    
    # Create a task and wait for 2 seconds, then cancel
    task = asyncio.create_task(run_pipeline())
    await asyncio.sleep(2)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Pipeline task was cancelled as expected")
    
    print("Test completed.")

if __name__ == "__main__":
    asyncio.run(test_pipeline())