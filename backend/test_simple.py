#!/usr/bin/env python
import sys
import os
sys.path.insert(0, '.')

# Set environment to avoid ElevenLabs issues
os.environ['ELEVENLABS_API_KEY'] = 'test'

from axiom.voice.pipeline_orchestrator import VoicePipelineOrchestrator

def test_pipeline():
    print("Creating VoicePipelineOrchestrator...")
    orchestrator = VoicePipelineOrchestrator()
    
    print("Initializing pipeline...")
    init_result = orchestrator.initialize()
    print(f"Initialization result: {init_result}")
    
    if init_result:
        print("Starting pipeline...")
        start_result = orchestrator.start()
        print(f"Start result: {start_result}")
        
        if start_result:
            print("Pipeline started successfully!")
            print("Running for 10 seconds to test continuous cycle...")
            import time
            time.sleep(10)
            
            print("Stopping pipeline...")
            orchestrator.stop()
            print("Pipeline stopped.")
        else:
            print("Failed to start pipeline")
    else:
        print("Failed to initialize pipeline")

if __name__ == "__main__":
    test_pipeline()
