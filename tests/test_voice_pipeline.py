"""
Integration tests for the Axiom Voice Pipeline.

Tests core components: wake word detection, VAD, STT, routing, TTS, and orchestration.
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

# Add parent directory to path for imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from axiom_voice_pipeline.config import ENTITIES, IntentRouterConfig, WakeWordConfig
from axiom_voice_pipeline.models import (
    IntentRouterOutput,
    IntentType,
    TranscriptionComplete,
    WakeWordDetection,
)
from axiom_voice_pipeline.pipeline_orchestrator import VoicePipeline
from axiom_voice_pipeline.relay.ws_server import WebSocketConnectionManager
from axiom_voice_pipeline.router.intent_router import IntentRouter
from axiom_voice_pipeline.wakeword.vad import VoiceActivityDetector

logger = logging.getLogger(__name__)


class TestWakeWordDetector:
    """Tests for wake word detection."""
    
    def test_detector_initialization(self):
        """Test that detector initializes without errors."""
        from axiom_voice_pipeline.wakeword.detector import WakeWordDetector
        
        detector = WakeWordDetector()
        assert detector is not None
        assert detector.config is not None
    
    def test_get_loaded_entities(self):
        """Test getting list of loaded entities."""
        from axiom_voice_pipeline.wakeword.detector import WakeWordDetector
        
        detector = WakeWordDetector()
        entities = detector.get_loaded_entities()
        
        # Should be empty or contain valid entity names
        assert isinstance(entities, list)
        for entity in entities:
            assert entity in ENTITIES
    
    def test_health_check(self):
        """Test health check returns proper status."""
        from axiom_voice_pipeline.wakeword.detector import WakeWordDetector
        
        detector = WakeWordDetector()
        health = detector.health_check()
        
        assert isinstance(health, dict)
        for entity in ENTITIES:
            assert entity in health
            assert isinstance(health[entity], bool)


class TestVAD:
    """Tests for Voice Activity Detection."""
    
    def test_vad_initialization(self):
        """Test VAD initializes without errors."""
        vad = VoiceActivityDetector()
        assert vad is not None
        assert vad.engine is not None
    
    def test_vad_reset(self):
        """Test VAD state reset."""
        vad = VoiceActivityDetector()
        
        # Simulate some processing
        vad.in_speech = True
        vad.speech_frames = [np.array([1, 2, 3])]
        
        # Reset
        vad.reset()
        
        assert vad.in_speech is False
        assert len(vad.speech_frames) == 0
        assert vad.silence_frames == 0
    
    def test_vad_process_frame(self):
        """Test VAD processing a frame."""
        vad = VoiceActivityDetector()
        
        # Create a dummy audio frame
        audio_frame = np.zeros(16000, dtype=np.float32)
        
        has_speech, speech_ended = vad.process_frame(audio_frame)
        
        assert isinstance(has_speech, bool)
        assert isinstance(speech_ended, bool)


class TestIntentRouter:
    """Tests for intent routing."""
    
    def test_router_initialization(self):
        """Test router initializes without errors."""
        router = IntentRouter()
        assert router is not None
        assert router.config is not None
    
    def test_route_direct_entity(self):
        """Test direct routing to non-Axiom entity."""
        router = IntentRouter()
        
        result = router.route("jenson", "Check my emails")
        
        assert result is not None
        assert result.target_entity == "jenson"
        assert result.raw_text == "Check my emails"
        assert result.delegated_by is None
    
    def test_axiom_delegation(self):
        """Test Axiom delegation to subordinate."""
        router = IntentRouter()
        
        # Command with trading keywords should delegate to Valta Prime
        result = router.route("axiom", "Check my trading portfolio")
        
        assert result is not None
        assert result.target_entity == "valtaprime"
        assert result.delegated_by == "axiom"
    
    def test_axiom_no_delegation(self):
        """Test Axiom handling OS-level commands."""
        router = IntentRouter()
        
        result = router.route("axiom", "What time is it?")
        
        assert result is not None
        assert result.target_entity == "axiom"
        assert result.delegated_by is None
    
    def test_intent_classification(self):
        """Test intent type classification."""
        router = IntentRouter()
        
        # Search intent
        intent = router._classify_intent("Search for Bleval clients")
        assert intent == IntentType.SEARCH
        
        # Data query
        intent = router._classify_intent("Get my status report")
        assert intent == IntentType.DATA_QUERY
        
        # Action
        intent = router._classify_intent("Cancel my meeting")
        assert intent == IntentType.ACTION
    
    def test_invalid_entity(self):
        """Test routing with invalid entity."""
        router = IntentRouter()
        
        result = router.route("invalid_entity", "Some command")
        
        assert result is None


class TestTTSProvider:
    """Tests for TTS provider."""
    
    def test_provider_factory(self):
        """Test TTS provider factory."""
        from axiom_voice_pipeline.tts.provider_base import TTSProviderFactory
        
        # List providers
        providers = TTSProviderFactory.list_providers()
        assert "piper" in providers
    
    def test_piper_tts_initialization(self):
        """Test Piper TTS initializes."""
        from axiom_voice_pipeline.tts.piper_provider import PiperTTS
        
        tts = PiperTTS()
        assert tts is not None
        
        # Health check
        health = tts.health_check()
        assert isinstance(health, bool)


class TestWebSocketRelay:
    """Tests for WebSocket relay."""
    
    def test_connection_manager_initialization(self):
        """Test connection manager initializes."""
        manager = WebSocketConnectionManager()
        assert manager is not None
        assert manager.get_connection_count() == 0
    
    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting messages."""
        manager = WebSocketConnectionManager()
        
        # Mock websocket
        mock_ws = AsyncMock()
        manager.active_connections.add(mock_ws)
        
        # Broadcast
        await manager.broadcast({"test": "message"})
        
        # Check send was called
        mock_ws.send_text.assert_called_once()


class TestPipelineOrchestrator:
    """Tests for the main pipeline orchestrator."""
    
    def test_pipeline_initialization(self):
        """Test pipeline initializes with all components."""
        pipeline = VoicePipeline()
        
        assert pipeline is not None
        assert pipeline.wake_detector is not None
        assert pipeline.vad is not None
        assert pipeline.stt is not None
        assert pipeline.router is not None
        assert pipeline.tts_proxy is not None
    
    def test_pipeline_state(self):
        """Test pipeline state management."""
        pipeline = VoicePipeline()
        
        assert pipeline.state.is_listening is False
        assert pipeline.state.active_entity is None
        assert pipeline.state.current_phase == "idle"
    
    def test_pipeline_health_check(self):
        """Test pipeline health check."""
        pipeline = VoicePipeline()
        
        health = pipeline.health_check()
        
        assert isinstance(health, dict)
        assert "wake_detector" in health
        assert "stt" in health
        assert "router" in health
        assert "tts" in health


class TestEndToEndFlow:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_command_routing_flow(self):
        """Test complete command routing flow."""
        router = IntentRouter()
        
        # Simulate: User says "Jenson, check the campaign status"
        wake_entity = "jenson"
        command = "check the campaign status"
        
        result = router.route(wake_entity, command)
        
        assert result is not None
        assert result.target_entity == "jenson"
        assert result.intent_type in [
            IntentType.SEARCH,
            IntentType.DATA_QUERY,
            IntentType.ACTION,
            IntentType.GENERAL,
        ]
    
    @pytest.mark.asyncio
    async def test_axiom_delegation_flow(self):
        """Test Axiom's delegation capabilities."""
        router = IntentRouter()
        
        # Axiom delegates to Yamako for personal tasks
        result = router.route("axiom", "Add a reminder to my calendar")
        assert result.target_entity == "yamako"
        assert result.delegated_by == "axiom"
        
        # Axiom delegates to Jenson for agency work
        result = router.route("axiom", "What's the client status for Bleval?")
        assert result.target_entity == "jenson"
        assert result.delegated_by == "axiom"
        
        # Axiom delegates to Valta Prime for trading
        result = router.route("axiom", "Show me my trading performance")
        assert result.target_entity == "valtaprime"
        assert result.delegated_by == "axiom"


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def pipeline():
    """Fixture providing a VoicePipeline instance."""
    return VoicePipeline()


@pytest.fixture
def router():
    """Fixture providing an IntentRouter instance."""
    return IntentRouter()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
