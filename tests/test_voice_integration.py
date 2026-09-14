#!/usr/bin/env python
"""Test script to verify voice listener integration."""

import sys
import time
import threading
from unittest.mock import patch

# Add backend to path
sys.path.insert(0, 'backend')

def test_voice_listener_integration():
    """Test that VoiceListener works with the pipeline orchestrator."""
    print("Testing VoiceListener integration...")

    # Import after path modification
    from axiom.voice.pipeline_orchestrator import VoicePipelineOrchestrator
    from axiom.voice.wake_listener import VoiceListener

    # Create a mock runtime object
    class MockRuntime:
        def __init__(self):
            self.executive_board = None

    runtime = MockRuntime()

    # Create pipeline orchestrator
    pipeline = VoicePipelineOrchestrator(runtime=runtime, use_mock=True)

    # Initialize
    print("Initializing pipeline...")
    if not pipeline.initialize():
        print("ERROR: Failed to initialize pipeline")
        return False

    print("Pipeline initialized successfully")

    # Check that voice listener was created
    if pipeline.voice_listener is None:
        print("ERROR: Voice listener not created")
        return False

    print("Voice listener created successfully")

    # Start pipeline
    print("Starting pipeline...")
    if not pipeline.start():
        print("ERROR: Failed to start pipeline")
        return False

    print("Pipeline started successfully")

    # Give it a moment to start up
    time.sleep(2)

    # Check status
    status = pipeline.get_status()
    print(f"Pipeline status: {status}")

    # Check that voice listener is running
    if not status.get('running', False):
        print("WARNING: Pipeline not running")

    # Stop pipeline
    print("Stopping pipeline...")
    pipeline.stop()
    print("Pipeline stopped")

    print("Test completed successfully")
    return True

if __name__ == "__main__":
    success = test_voice_listener_integration()
    sys.exit(0 if success else 1)