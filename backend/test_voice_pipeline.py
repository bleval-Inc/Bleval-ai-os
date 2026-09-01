#!/usr/bin/env python3
"""Test script to verify the voice pipeline components."""

import sys
import traceback

def test_imports():
    """Test that all voice pipeline modules can be imported."""
    print("Testing imports...")
    
    try:
        from axiom.voice.config import voice_config, EXECUTIVE_WAKE_WORDS, VALID_EXECUTIVES
        print("✓ axiom.voice.config")
    except Exception as e:
        print(f"✗ axiom.voice.config: {e}")
        return False
    
    try:
        from axiom.voice.wakeword.detector import WakeWordDetector, MockWakeWordDetector, create_wake_word_detector
        print("✓ axiom.voice.wakeword.detector")
    except Exception as e:
        print(f"✗ axiom.voice.wakeword.detector: {e}")
        return False
    
    try:
        from axiom.voice.wakeword.vad import SileroVAD, WebRTCVAD, VADCaptureManager, create_vad_capture_manager
        print("✓ axiom.voice.wakeword.vad")
    except Exception as e:
        print(f"✗ axiom.voice.wakeword.vad: {e}")
        return False
    
    try:
        from axiom.voice.stt.whisper_engine import WhisperEngine, MockWhisperEngine, create_whisper_engine
        print("✓ axiom.voice.stt.whisper_engine")
    except Exception as e:
        print(f"✗ axiom.voice.stt.whisper_engine: {e}")
        return False
    
    try:
        from axiom.voice.router.intent_router import IntentRouter, RouterOutput
        print("✓ axiom.voice.router.intent_router")
    except Exception as e:
        print(f"✗ axiom.voice.router.intent_router: {e}")
        return False
    
    try:
        from axiom.voice.tts.provider_base import TTSProvider, VoiceProfile, TTSProviderRegistry, tts_registry
        print("✓ axiom.voice.tts.provider_base")
    except Exception as e:
        print(f"✗ axiom.voice.tts.provider_base: {e}")
        return False
    
    try:
        from axiom.voice.tts.piper_provider import PiperTTS
        print("✓ axiom.voice.tts.piper_provider")
    except Exception as e:
        print(f"✗ axiom.voice.tts.piper_provider: {e}")
        return False
    
    try:
        from axiom.voice.tts.voice_profiles import EXECUTIVE_VOICE_PROFILES, EXECUTIVE_GREETINGS, get_voice_profile, get_best_voice_profile
        print("✓ axiom.voice.tts.voice_profiles")
    except Exception as e:
        print(f"✗ axiom.voice.tts.voice_profiles: {e}")
        return False
    
    try:
        from axiom.voice.tts.service import TextToSpeechService, tts_service
        print("✓ axiom.voice.tts.service")
    except Exception as e:
        print(f"✗ axiom.voice.tts.service: {e}")
        return False
    
    try:
        from axiom.voice.relay.ws_server import VoiceRelayServer
        print("✓ axiom.voice.relay.ws_server")
    except Exception as e:
        print(f"✗ axiom.voice.relay.ws_server: {e}")
        return False
    
    try:
        from axiom.voice.pipeline_orchestrator import VoicePipelineOrchestrator, VoiceEvent, get_pipeline, initialize_pipeline
        print("✓ axiom.voice.pipeline_orchestrator")
    except Exception as e:
        print(f"✗ axiom.voice.pipeline_orchestrator: {e}")
        return False
    
    return True


def test_config():
    """Test configuration values."""
    print("\nTesting configuration...")
    
    from axiom.voice.config import voice_config, EXECUTIVE_WAKE_WORDS, VALID_EXECUTIVES, EXECUTIVE_WORKSTATIONS
    
    print(f"  Executives: {VALID_EXECUTIVES}")
    print(f"  Wake words: {EXECUTIVE_WAKE_WORDS}")
    print(f"  Workstations: {EXECUTIVE_WORKSTATIONS}")
    print(f"  STT model: {voice_config.stt.model_size}")
    print(f"  TTS provider: {voice_config.tts.provider}")
    print(f"  Piper models dir: {voice_config.tts.piper_models_dir}")
    
    return True


def test_intent_router():
    """Test intent routing logic."""
    print("\nTesting intent router...")
    
    from axiom.voice.router.intent_router import IntentRouter
    
    router = IntentRouter()
    
    # Test direct wake word routing
    result = router.route("check my trades", "valta_prime", 0.9, "valta prime")
    assert result.target_entity == "valta_prime"
    assert result.delegated_by is None
    print("✓ Direct wake word routing (Valta Prime)")
    
    result = router.route("schedule a meeting", "jenson", 0.9, "jenson")
    assert result.target_entity == "jenson"
    assert result.delegated_by is None
    print("✓ Direct wake word routing (Jenson)")
    
    result = router.route("remind me to drink water", "yamako", 0.9, "yamako")
    assert result.target_entity == "yamako"
    assert result.delegated_by is None
    print("✓ Direct wake word routing (Yamako)")
    
    # Test Axiom delegation
    result = router.route("analyze gold price action", "axiom", 0.9, "axiom")
    assert result.target_entity == "valta_prime"
    assert result.delegated_by == "axiom"
    print("✓ Axiom delegation to Valta Prime")
    
    result = router.route("create a new project for the agency", "axiom", 0.9, "axiom")
    assert result.target_entity == "jenson"
    assert result.delegated_by == "axiom"
    print("✓ Axiom delegation to Jenson")
    
    result = router.route("set a reminder for tomorrow", "axiom", 0.9, "axiom")
    assert result.target_entity == "yamako"
    assert result.delegated_by == "axiom"
    print("✓ Axiom delegation to Yamako")
    
    # Test Axiom direct handling
    result = router.route("what is the system status", "axiom", 0.9, "axiom")
    assert result.target_entity == "axiom"
    assert result.delegated_by is None
    print("✓ Axiom direct handling")
    
    return True


def test_mock_pipeline():
    """Test pipeline with mock components."""
    print("\nTesting mock pipeline...")
    
    from axiom.voice.pipeline_orchestrator import VoicePipelineOrchestrator
    
    try:
        pipeline = VoicePipelineOrchestrator(use_mock=True)
        assert pipeline.initialize()
        print("✓ Pipeline initialization")
        
        pipeline.start()
        print("✓ Pipeline start")
        
        # Test push-to-talk trigger
        pipeline.trigger_push_to_talk("axiom")
        print("✓ Push-to-talk trigger")
        
        # Give some time for processing
        import time
        time.sleep(3)
        
        pipeline.stop()
        print("✓ Pipeline stop")
        
        return True
    except Exception as e:
        print(f"✗ Mock pipeline test failed: {e}")
        traceback.print_exc()
        return False


def test_tts_service():
    """Test TTS service initialization."""
    print("\nTesting TTS service...")
    
    from axiom.voice.tts.service import get_tts_service
    
    try:
        # Just test initialization doesn't crash
        service = get_tts_service()
        result = service.initialize()
        print(f"✓ TTS service initialized (providers: {service.get_available_providers()})")
        return True
    except Exception as e:
        print(f"✗ TTS service test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Axiom Voice Pipeline - Component Tests")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config,
        test_intent_router,
        test_tts_service,
        test_mock_pipeline,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)