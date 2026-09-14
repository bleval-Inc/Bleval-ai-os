#!/usr/bin/env python3
"""Test script to verify the wake word detection fix works correctly."""

import time

def test_wake_word_detection_leads_to_acknowledging():
    """Test that wake word detection properly triggers state transition to ACKNOWLEDGING."""
    print("Testing wake word detection -> ACKNOWLEDGING transition...")

    # Import the voice pipeline components
    from axiom.voice.pipeline_orchestrator import VoicePipelineOrchestrator, VoiceState
    from axiom.voice.config import voice_config

    # Create pipeline with mock mode to avoid hardware dependencies
    pipeline = VoicePipelineOrchestrator(use_mock=True)

    # Initialize the pipeline
    assert pipeline.initialize(), "Pipeline initialization failed"
    print("[PASS] Pipeline initialized")

    # Start the pipeline
    assert pipeline.start(), "Pipeline start failed"
    print("[PASS] Pipeline started")

    try:
        # Verify initial state is LISTENING
        assert pipeline._state == VoiceState.LISTENING, f"Expected LISTENING, got {pipeline._state}"
        print("[PASS] Initial state is LISTENING")

        # Simulate wake word detection by directly calling the handler
        # This bypasses the audio processing but tests the state transition logic
        pipeline._handle_wake_word_detected("axiom", 0.9, "axiom")

        # Give a moment for the acknowledgment thread to start and transition states
        time.sleep(0.2)

        # Check that we transitioned to ACKNOWLEDGING (briefly) then to CAPTURING
        # Note: The acknowledgment thread runs asynchronously, so we might catch it in either state
        current_state = pipeline._state
        print(f"Current state after wake word detection: {current_state}")

        # The state should have moved past LISTENING
        assert current_state != VoiceState.LISTENING, f"State should have changed from LISTENING, but is still {current_state}"
        print("[PASS] State transitioned from LISTENING")

        # It should be either ACKNOWLEDGING or CAPTURING (acknowledgment thread may have completed)
        assert current_state in [VoiceState.ACKNOWLEDGING, VoiceState.CAPTURING], \
            f"Expected ACKNOWLEDGING or CAPTURING, got {current_state}"
        print(f"[PASS] State is correctly {current_state.value}")

        # Wait a bit more to allow transition to CAPTURING if still in ACKNOWLEDGING
        if current_state == VoiceState.ACKNOWLEDGING:
            time.sleep(0.5)  # Wait for acknowledgment to complete
            final_state = pipeline._state
            print(f"State after acknowledgment: {final_state}")
            assert final_state == VoiceState.CAPTURING, f"Expected CAPTURING after acknowledgment, got {final_state}"
            print("[PASS] State transitioned to CAPTURING after acknowledgment")

        print("\n[PASS] Wake word detection fix verified successfully!")
        return True

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        return False

    finally:
        # Clean up
        pipeline.stop()
        print("[PASS] Pipeline stopped")

if __name__ == "__main__":
    success = test_wake_word_detection_leads_to_acknowledging()
    exit(0 if success else 1)