#!/usr/bin/env python3
"""Test B4 imports and basic functionality"""

import sys
import os

# Add the backend directory to the path so we can import axiom modules
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from axiom.voice.models import AcknowledgingEvent, CapturingEvent, EventType
    print("✓ SUCCESS: New event classes import correctly")
    print(f"  EventType.ACKNOWLEDGING = {EventType.ACKNOWLEDGING}")
    print(f"  EventType.CAPTURING = {EventType.CAPTURING}")

    # Test creating instances
    ack_event = AcknowledgingEvent(wake_entity="axiom")
    cap_event = CapturingEvent(wake_entity="jenson")
    print("✓ SUCCESS: Can instantiate new event classes")
    print(f"  AcknowledgingEvent: {ack_event}")
    print(f"  CapturingEvent: {cap_event}")

except Exception as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

try:
    from axiom.voice.pipeline_orchestrator import VoicePipelineOrchestrator
    print("✓ SUCCESS: Pipeline orchestrator imports correctly")

    # Test instantiation
    pipeline = VoicePipelineOrchestrator(use_mock=True)
    print("✓ SUCCESS: Can instantiate VoicePipelineOrchestrator")

except Exception as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

try:
    from axiom.voice.relay.ws_server import WebSocketConnectionManager, PipelineEventEmitter
    print("✓ SUCCESS: WebSocket relay imports correctly")

    # Test instantiation
    manager = WebSocketConnectionManager()
    emitter = PipelineEventEmitter(manager)
    print("✓ SUCCESS: Can instantiate WebSocketConnectionManager and PipelineEventEmitter")

except Exception as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

print("\n🎉 All B4 import tests passed!")