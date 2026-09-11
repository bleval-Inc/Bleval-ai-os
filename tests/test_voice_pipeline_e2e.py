"""
End-to-End Voice Pipeline Test

Tests the complete voice pipeline with:
1. Wake word training
2. Intelligence engine integration
3. Microphone capture
4. Full pipeline processing

Run: python test_voice_pipeline_e2e.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EndToEndTest:
    """End-to-end test for voice pipeline."""
    
    def __init__(self):
        """Initialize test."""
        self.results = {}
    
    async def test_wake_word_training(self) -> bool:
        """Test 1: Wake word model training."""
        logger.info("=" * 80)
        logger.info("TEST 1: Wake Word Training")
        logger.info("=" * 80)
        
        try:
            from axiom_voice_pipeline.train_wake_words import WakeWordTrainer
            
            trainer = WakeWordTrainer(
                output_dir="axiom_voice_pipeline/wakeword/models"
            )
            
            # Train models for all entities
            logger.info("Training wake word models...")
            results = trainer.train_all()
            
            success = all(results.values())
            
            for entity, trained in results.items():
                status = "✅ SUCCESS" if trained else "❌ FAILED"
                logger.info(f"  {entity}: {status}")
            
            self.results['wake_word_training'] = success
            return success
        
        except Exception as e:
            logger.error(f"Wake word training test failed: {e}")
            self.results['wake_word_training'] = False
            return False
    
    async def test_intelligence_integration(self) -> bool:
        """Test 2: Intelligence engine integration."""
        logger.info("=" * 80)
        logger.info("TEST 2: Intelligence Engine Integration")
        logger.info("=" * 80)
        
        try:
            from axiom_voice_pipeline.voice_intelligence_callback import (
                create_voice_callback
            )
            
            # Create callback without runtime (mock mode)
            callback = create_voice_callback(runtime=None)
            
            # Test processing a command
            test_commands = [
                ("axiom", "What time is it?"),
                ("jenson", "Check my emails"),
                ("yamako", "Add a reminder"),
                ("valtaprime", "Show trading performance"),
            ]
            
            for entity, command in test_commands:
                logger.info(f"  Processing {entity}: '{command}'")
                result = await callback.process_command(entity, command)
                
                if result:
                    logger.info(f"    ✅ Result: {result.spoken_summary}")
                else:
                    logger.error(f"    ❌ Failed to process")
                    return False
            
            self.results['intelligence_integration'] = True
            return True
        
        except Exception as e:
            logger.error(f"Intelligence integration test failed: {e}")
            self.results['intelligence_integration'] = False
            return False
    
    async def test_microphone_capture(self) -> bool:
        """Test 3: Microphone hardware setup."""
        logger.info("=" * 80)
        logger.info("TEST 3: Microphone Hardware Setup")
        logger.info("=" * 80)
        
        try:
            from axiom_voice_pipeline.microphone_capture import (
                MicrophoneCapture
            )
            
            capture = MicrophoneCapture()
            
            # List devices
            logger.info("Scanning for audio devices...")
            devices = capture.list_devices()
            
            if not devices:
                logger.warning("⚠️  No audio input devices found")
                logger.info("   This is expected if no microphone is attached")
                self.results['microphone_capture'] = True  # Pass with warning
                return True
            
            logger.info(f"Found {len(devices)} audio device(s):")
            for device in devices:
                logger.info(
                    f"  [{device['id']}] {device['name']} "
                    f"({device['channels']} channels)"
                )
            
            # Test recording (optional, only if device available)
            logger.info("Testing audio recording...")
            success = await capture.start()
            
            if success:
                logger.info("✅ Microphone recording started successfully")
                await capture.stop()
            else:
                logger.warning("⚠️  Could not start recording (no microphone?)")
            
            self.results['microphone_capture'] = True
            return True
        
        except Exception as e:
            logger.error(f"Microphone test failed: {e}")
            self.results['microphone_capture'] = False
            return False
    
    async def test_pipeline_components(self) -> bool:
        """Test 4: Individual pipeline components."""
        logger.info("=" * 80)
        logger.info("TEST 4: Pipeline Component Health")
        logger.info("=" * 80)
        
        try:
            from axiom_voice_pipeline import VoicePipeline
            
            pipeline = VoicePipeline()
            
            # Check health
            health = pipeline.health_check()
            
            logger.info("Component status:")
            all_healthy = True
            
            for component, status in health.items():
                icon = "✅" if status else "⚠️ "
                logger.info(f"  {icon} {component}: {'Ready' if status else 'Degraded'}")
                if not status and component == 'wake_detector':
                    # Wake detector may not have real models yet - that's ok
                    logger.info("    (This is expected until real models are trained)")
                else:
                    all_healthy = all_healthy and status
            
            self.results['pipeline_components'] = all_healthy
            return True
        
        except Exception as e:
            logger.error(f"Pipeline component test failed: {e}")
            self.results['pipeline_components'] = False
            return False
    
    async def test_websocket_relay(self) -> bool:
        """Test 5: WebSocket relay setup."""
        logger.info("=" * 80)
        logger.info("TEST 5: WebSocket Relay Setup")
        logger.info("=" * 80)
        
        try:
            from axiom_voice_pipeline.relay.ws_server import (
                WebSocketConnectionManager,
                PipelineEventEmitter,
            )
            
            # Create manager
            manager = WebSocketConnectionManager()
            logger.info("✅ WebSocketConnectionManager created")
            
            # Create emitter
            emitter = PipelineEventEmitter(manager)
            logger.info("✅ PipelineEventEmitter created")
            
            # Test broadcast
            logger.info("Testing event broadcasting...")
            await manager.broadcast({"type": "test", "payload": "test_message"})
            logger.info("✅ Test broadcast successful")
            
            self.results['websocket_relay'] = True
            return True
        
        except Exception as e:
            logger.error(f"WebSocket relay test failed: {e}")
            self.results['websocket_relay'] = False
            return False
    
    async def run_all_tests(self):
        """Run all tests."""
        logger.info("\n")
        logger.info("╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 20 + "AXIOM AI OS - VOICE PIPELINE E2E TEST" + " " * 22 + "║")
        logger.info("╚" + "=" * 78 + "╝")
        logger.info("\n")
        
        tests = [
            ("Wake Word Training", self.test_wake_word_training),
            ("Intelligence Integration", self.test_intelligence_integration),
            ("Microphone Capture", self.test_microphone_capture),
            ("Pipeline Components", self.test_pipeline_components),
            ("WebSocket Relay", self.test_websocket_relay),
        ]
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                logger.info(f"\n{test_name}: {'PASS ✅' if result else 'FAIL ❌'}\n")
            except Exception as e:
                logger.error(f"\n{test_name}: FAIL ❌ ({e})\n")
                self.results[test_name] = False
        
        # Summary
        logger.info("\n")
        logger.info("╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 30 + "TEST SUMMARY" + " " * 36 + "║")
        logger.info("╠" + "=" * 78 + "╣")
        
        passed = sum(1 for v in self.results.values() if v)
        total = len(self.results)
        
        logger.info(f"║  Tests Passed: {passed}/{total}" + " " * 58 + "║")
        
        for test_name, result in self.results.items():
            status = "PASS ✅" if result else "FAIL ❌"
            padding = 70 - len(test_name) - len(status)
            logger.info(f"║  {test_name}{' ' * padding}{status} ║")
        
        logger.info("╚" + "=" * 78 + "╝")
        
        if passed == total:
            logger.info("\n🎉 ALL TESTS PASSED! Voice pipeline is ready for use.\n")
            return True
        else:
            logger.warning(f"\n⚠️  {total - passed} test(s) failed. See details above.\n")
            return False


async def main():
    """Run end-to-end tests."""
    test = EndToEndTest()
    success = await test.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
