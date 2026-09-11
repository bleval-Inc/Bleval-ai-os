"""
WebSocket relay server for streaming voice pipeline events to frontend.

Receives pipeline events and broadcasts them to connected clients.
Supports audio streaming as base64-encoded data or external URLs.
"""

import base64
import json
import logging
from typing import Set

from fastapi import WebSocket, WebSocketDisconnect

from ..config import WebSocketConfig, websocket_config
from ..models import (
    DisplayResultEvent,
    ErrorEvent,
    EventType,
    ExecutiveSpeakingEvent,
    IdleEvent,
    ListeningStartedEvent,
    ProcessingEvent,
    TranscriptionCompleteEvent,
    WakeWordEvent,
)

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """Manages WebSocket client connections and event broadcasting."""
    
    def __init__(self, config: WebSocketConfig = None):
        """
        Initialize the connection manager.
        
        Args:
            config: WebSocketConfig instance
        """
        self.config = config or websocket_config
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """
        Accept a WebSocket connection.
        
        Args:
            websocket: WebSocket connection object
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection object
        """
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict | str):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message dict (will be JSON encoded) or JSON string
        """
        if isinstance(message, dict):
            try:
                # Convert Pydantic models to dict if needed
                if hasattr(message.get('payload'), 'dict'):
                    message['payload'] = message['payload'].dict()
                message_json = json.dumps(message, default=str)
            except Exception as e:
                logger.error(f"Error encoding message: {e}")
                return
        else:
            message_json = message
        
        disconnected_clients = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Error sending to client: {e}")
                disconnected_clients.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected_clients:
            await self.disconnect(conn)
    
    async def broadcast_event(
        self,
        event_type: str,
        payload: dict,
        metadata: dict = None,
    ):
        """
        Broadcast a typed event.
        
        Args:
            event_type: Type of event
            payload: Event payload
            metadata: Optional additional metadata
        """
        message = {
            "type": event_type,
            "payload": payload,
        }
        
        if metadata:
            message["metadata"] = metadata
        
        await self.broadcast(message)
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


class PipelineEventEmitter:
    """Emits pipeline events over WebSocket."""
    
    def __init__(self, connection_manager: WebSocketConnectionManager):
        """
        Initialize the emitter.
        
        Args:
            connection_manager: WebSocketConnectionManager instance
        """
        self.manager = connection_manager
    
    async def emit_wake_detected(self, event: WakeWordEvent):
        """Emit wake word detected event."""
        await self.manager.broadcast_event(
            EventType.WAKE_DETECTED,
            event.dict(),
        )
    
    async def emit_listening_started(self, event: ListeningStartedEvent):
        """Emit listening started event."""
        await self.manager.broadcast_event(
            EventType.LISTENING_STARTED,
            event.dict(),
        )
    
    async def emit_transcription_complete(self, event: TranscriptionCompleteEvent):
        """Emit transcription complete event."""
        await self.manager.broadcast_event(
            EventType.TRANSCRIPTION_COMPLETE,
            event.dict(),
        )
    
    async def emit_processing(self, event: ProcessingEvent):
        """Emit processing started event."""
        await self.manager.broadcast_event(
            EventType.PROCESSING,
            event.dict(),
        )
    
    async def emit_executive_speaking(self, event: ExecutiveSpeakingEvent):
        """
        Emit executive speaking event.
        
        Handles audio streaming as base64 if audio_bytes present.
        """
        event_dict = event.dict()
        
        # If audio bytes present, encode as base64
        if event_dict.get("audio", {}).get("audio_bytes"):
            audio_bytes = event_dict["audio"]["audio_bytes"]
            
            if isinstance(audio_bytes, bytes):
                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            else:
                audio_b64 = audio_bytes
            
            event_dict["audio"]["audio_data_base64"] = audio_b64
            event_dict["audio"]["audio_bytes"] = None  # Don't send raw bytes
        
        await self.manager.broadcast_event(
            EventType.EXECUTIVE_SPEAKING,
            event_dict,
        )
    
    async def emit_display_result(self, event: DisplayResultEvent):
        """Emit display result event."""
        await self.manager.broadcast_event(
            EventType.DISPLAY_RESULT,
            event.dict(),
        )
    
    async def emit_idle(self, event: IdleEvent):
        """Emit idle/ready event."""
        await self.manager.broadcast_event(
            EventType.IDLE,
            event.dict(),
        )
    
    async def emit_error(self, event: ErrorEvent):
        """Emit error event."""
        await self.manager.broadcast_event(
            EventType.ERROR,
            event.dict(),
        )
