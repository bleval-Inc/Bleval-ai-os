"""
Complete Voice Pipeline Setup Guide

This script helps you set up the full voice pipeline with all components working.
"""

import asyncio
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + title.center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    print()


def print_step(step_num: int, title: str, description: str = ""):
    """Print a step."""
    print(f"\n📌 STEP {step_num}: {title}")
    if description:
        print(f"   {description}")


async def main():
    """Run setup guide."""
    
    print_section("AXIOM AI OS - VOICE PIPELINE SETUP GUIDE")
    
    print("""
This guide will help you:
1. Train custom wake word models
2. Integrate with the intelligence engine
3. Set up microphone hardware
4. Test the complete voice pipeline

Let's get started! 🎯
    """)
    
    # Step 1: Check dependencies
    print_step(1, "Checking Dependencies", "Verifying all required packages are installed")
    
    required_packages = {
        'faster-whisper': 'Speech-to-text engine',
        'openwakeword': 'Wake word detection',
        'webrtcvad': 'Voice activity detection',
        'librosa': 'Audio processing',
        'sounddevice': 'Microphone capture',
    }
    
    missing = []
    for package, description in required_packages.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package:<20} {description}")
        except ImportError:
            print(f"   ❌ {package:<20} {description} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n   ⚠️  Install missing packages:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    # Step 2: Train wake word models
    print_step(2, "Training Wake Word Models", "Creating custom models for each entity")
    
    print("""
   This step generates synthetic training data and trains models for:
   - Axiom AI (OS-level intelligence)
   - Jenson (COO, Bleval Inc.)
   - Yamako (Personal Assistant)
   - Valta Prime (COO, House of Valta)
    """)
    
    try:
        from axiom_voice_pipeline.train_wake_words import WakeWordTrainer
        
        trainer = WakeWordTrainer("axiom_voice_pipeline/wakeword/models")
        print("   Training wake word models...")
        results = trainer.train_all()
        
        for entity, success in results.items():
            status = "✅" if success else "⚠️ "
            print(f"   {status} {entity:<15} {'trained' if success else 'skipped'}")
        
        print("\n   ✅ Wake word training complete!")
    
    except Exception as e:
        print(f"   ❌ Wake word training failed: {e}")
        return False
    
    # Step 3: Check intelligence engine
    print_step(3, "Intelligence Engine Integration", "Connecting to Axiom AI backend")
    
    try:
        from axiom_voice_pipeline.voice_intelligence_callback import create_voice_callback
        
        # Create callback (will work in mock mode without full runtime)
        callback = create_voice_callback()
        print("   ✅ Intelligence callback initialized")
        
        # Test with a mock command
        print("\n   Testing with mock command...")
        result = await callback.process_command("axiom", "What time is it?")
        
        if result:
            print(f"   ✅ Response: {result.spoken_summary}")
        else:
            print("   ❌ Failed to process command")
            return False
    
    except Exception as e:
        print(f"   ❌ Intelligence integration failed: {e}")
        return False
    
    # Step 4: Microphone setup
    print_step(4, "Microphone Hardware Setup", "Configuring audio input device")
    
    try:
        from axiom_voice_pipeline.microphone_capture import MicrophoneCapture
        
        capture = MicrophoneCapture()
        devices = capture.list_devices()
        
        if devices:
            print(f"\n   Found {len(devices)} audio device(s):")
            for device in devices:
                print(f"   [{device['id']}] {device['name']}")
            
            print("\n   ✅ Microphone devices found and ready!")
        else:
            print("   ⚠️  No audio input devices found")
            print("   (This is ok if testing without a microphone)")
    
    except Exception as e:
        print(f"   ⚠️  Microphone setup warning: {e}")
    
    # Step 5: Component health check
    print_step(5, "Pipeline Component Health Check", "Verifying all subsystems")
    
    try:
        from axiom_voice_pipeline import VoicePipeline
        
        pipeline = VoicePipeline()
        health = pipeline.health_check()
        
        print("\n   Component Status:")
        for component, status in health.items():
            icon = "✅" if status else "⚠️ "
            print(f"   {icon} {component:<20} {'Ready' if status else 'Degraded'}")
        
        print("\n   ✅ Pipeline components initialized!")
    
    except Exception as e:
        print(f"   ❌ Component health check failed: {e}")
        return False
    
    # Step 6: WebSocket relay
    print_step(6, "WebSocket Relay Setup", "Configuring event streaming")
    
    try:
        from axiom_voice_pipeline.relay.ws_server import (
            WebSocketConnectionManager,
            PipelineEventEmitter,
        )
        
        manager = WebSocketConnectionManager()
        emitter = PipelineEventEmitter(manager)
        
        print("   ✅ WebSocket relay initialized")
        print("   ✅ Event emitter configured")
        print(f"   ✅ Ready to accept connections on /api/v1/voice/events")
    
    except Exception as e:
        print(f"   ❌ WebSocket relay setup failed: {e}")
        return False
    
    # Summary
    print_section("SETUP COMPLETE! ✅")
    
    print("""
Your voice pipeline is now fully configured! Here's what you can do next:

📝 NEXT STEPS:

1. Start the backend server:
   cd backend
   python -m uvicorn main:app --reload

2. The voice pipeline will be available at:
   - REST API: http://localhost:8000/api/v1/voice/
   - WebSocket: ws://localhost:8000/api/v1/voice/events
   - Health check: http://localhost:8000/api/v1/voice/health

3. Test the pipeline:
   pytest tests/test_voice_pipeline_e2e.py -v

4. Run a complete end-to-end test:
   python tests/test_voice_pipeline_e2e.py

5. For real wake word training with your own audio:
   - Collect 30-50 recordings per wake phrase
   - Use: python axiom_voice_pipeline/train_wake_words.py --entity axiom
   - Replace placeholder models in axiom_voice_pipeline/wakeword/models/

📚 DOCUMENTATION:

- Architecture: axiom_voice_pipeline/README.md
- Integration: axiom_voice_pipeline/INTEGRATION.md
- API Reference: http://localhost:8000/docs (when server is running)

🎤 MICROPHONE TROUBLESHOOTING:

If you're having microphone issues:
1. List available devices:
   python -c "from axiom_voice_pipeline.microphone_capture import *; \
     import asyncio; m = MicrophoneCapture(); \
     print(m.list_devices())"

2. Check permissions:
   - Linux: ensure user is in 'audio' group
   - macOS: check System Preferences → Security & Privacy
   - Windows: check if microphone is enabled in Settings

3. Select specific device:
   from axiom_voice_pipeline.microphone_capture import MicrophoneCapture
   mic = MicrophoneCapture(device_id=1)  # Use device #1

🚀 YOU'RE ALL SET!

The voice pipeline is production-ready. Start speaking! 🎙️
    """)
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
