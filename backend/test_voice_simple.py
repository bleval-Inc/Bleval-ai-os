#!/usr/bin/env python3
"""Simple test script to verify the voice pipeline components work."""

import sys
import os
import time

# Set environment to avoid ElevenLabs issues
os.environ['ELEVENLABS_API_KEY'] = 'test'

def test_wake_word_loading():
    """Test that wake word models load correctly."""
    print("[TEST] Testing wake word model loading...")

    try:
        sys.path.insert(0, '.')
        from axiom.voice.wakeword.detector import WakeWordDetector
        detector = WakeWordDetector()
        success = detector.load_models()
        print(f"[RESULT] Model loading success: {success}")
        print(f"[RESULT] Number of models loaded: {len(detector._models)}")

        if success:
            for exec_id, model in detector._models.items():
                print(f"[RESULT]  - {exec_id}: {type(model).__name__}")
            return True
        else:
            print("[FAIL] No models loaded")
            return False
    except Exception as e:
        print(f"[ERROR] Wake word test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_processor_init():
    """Test that audio processor initializes correctly."""
    print("\n[TEST] Testing audio processor initialization...")

    try:
        sys.path.insert(0, '.')
        from axiom.voice.pipeline_orchestrator import AudioProcessor
        processor = AudioProcessor()
        success = processor.initialize()
        print(f"[RESULT] Audio processor initialization: {success}")

        if success:
            # Start the microphone stream by setting _running and starting the stream
            processor._running = True
            processor._start_microphone_stream()
            time.sleep(0.5)  # Let it run briefly
            diag = processor.get_diagnostics()
            print(f"[RESULT] Audio processor diagnostics: {diag}")
            processor.stop()
            return True
        else:
            print("[FAIL] Audio processor initialization failed")
            return False
    except Exception as e:
        print(f"[ERROR] Audio processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pipeline_init():
    """Test that pipeline initializes correctly."""
    print("\n[TEST] Testing pipeline initialization...")

    try:
        sys.path.insert(0, '.')
        from axiom.voice.pipeline_orchestrator import VoicePipelineOrchestrator
        pipeline = VoicePipelineOrchestrator()
        success = pipeline.initialize()
        print(f"[RESULT] Pipeline initialization: {success}")

        if success:
            print("[PASS] Pipeline initialized successfully")
            return True
        else:
            print("[FAIL] Pipeline initialization failed")
            return False
    except Exception as e:
        print(f"[ERROR] Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("[TEST] Simple Voice Pipeline Tests")
    print("=" * 50)

    tests = [
        test_wake_word_loading,
        test_audio_processor_init,
        test_pipeline_init,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
                print("[PASS] Test passed\n")
            else:
                print("[FAIL] Test failed\n")
        except Exception as e:
            print(f"[ERROR] Test failed with exception: {e}\n")

    print("=" * 50)
    print(f"[RESULTS] {passed}/{total} tests passed")
    print("=" * 50)

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)