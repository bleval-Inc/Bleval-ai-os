#!/usr/bin/env python3
"""Test script to verify voice pipeline component initialization."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from axiom.voice.pipeline_orchestrator import VoicePipelineOrchestrator
from axiom.voice.config import voice_config, EXECUTIVE_WAKE_WORDS, VALID_EXECUTIVES

def test_pipeline_initialization():
    """Test that the pipeline initializes correctly."""
    print("Testing pipeline initialization...")

    # Test config values
    print(f"Valid executives: {VALID_EXECUTIVES}")
    print(f"Executive wake words: {EXECUTIVE_WAKE_WORDS}")
    print(f"Audio device: {voice_config.audio_device}")
    print(f"Sample rate: {voice_config.wake_word.sample_rate}")
    print(f"Chunk size: {voice_config.wake_word.chunk_size}")
    print(f"Confidence threshold: {voice_config.wake_word.confidence_threshold}")

    # Initialize pipeline
    pipeline = VoicePipelineOrchestrator(use_mock=True)  # Use mock to avoid hardware dependencies

    if pipeline.initialize():
        print("[PASS] Pipeline initialized successfully")

        # Check components
        if pipeline.wake_detector:
            print("[PASS] Wake word detector initialized")
        else:
            print("[FAIL] Wake word detector failed to initialize")

        if pipeline.vad_capture:
            print("[PASS] VAD capture manager initialized")
        else:
            print("[FAIL] VAD capture manager failed to initialize")

        if pipeline.stt_engine:
            print("[PASS] STT engine initialized")
        else:
            print("[FAIL] STT engine failed to initialize")

        if pipeline.tts_service:
            print("[PASS] TTS service initialized")
        else:
            print("[FAIL] TTS service failed to initialize")

        if pipeline.intent_router:
            print("[PASS] Intent router initialized")
        else:
            print("[FAIL] Intent router failed to initialize")

        # Test starting pipeline
        if pipeline.start():
            print("[PASS] Pipeline started successfully")
            pipeline.stop()
            print("[PASS] Pipeline stopped successfully")
            return True
        else:
            print("[FAIL] Pipeline failed to start")
            return False
    else:
        print("[FAIL] Pipeline initialization failed")
        return False

if __name__ == "__main__":
    success = test_pipeline_initialization()
    sys.exit(0 if success else 1)