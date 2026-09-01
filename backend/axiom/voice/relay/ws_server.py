"""WebSocket relay server for voice pipeline events."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("axiom.voice.relay.ws_server")


class VoiceRelayServer:
    """
    WebSocket server for relaying voice pipeline events to frontend.
    
    Event types emitted:
    - wake_detected: Wake word detected
    - listening_started: VAD capture started
    - transcription_started: STT started
    - transcription_complete: STT finished
    - processing: Command being processed
    - synthesizing: TTS synthesis started
    - executive_speaking: TTS complete, audio ready
    - display_result: Full result for workstation display
    - idle: Executive returned to idle
    - error: Error occurred
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
    ):
        self.host = host
        self.port = port
        self._app: Optional[FastAPI] = None
        self._server: Optional[Any] = None
        self._running = False
        self._clients: Set[WebSocket] = set()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
    def create_app(self) -> FastAPI:
        """Create the FastAPI application."""
        app = FastAPI(title="Axiom Voice Relay", version="1.0.0")
        
        # CORS for frontend
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.get("/health")
        async def health():
            return {"status": "ok", "clients": len(self._clients)}
        
        @app.websocket("/voice/ws")
        async def voice_websocket(websocket: WebSocket):
            await self._handle_client(websocket)
        
        @app.websocket("/voice/ws/{client_id}")
        async def voice_websocket_client(websocket: WebSocket, client_id: str):
            await self._handle_client(websocket, client_id)
        
        self._app = app
        return app
    
    async def _handle_client(self, websocket: WebSocket, client_id: str = None) -> None:
        """Handle a WebSocket client connection."""
        await websocket.accept()
        
        if client_id is None:
            client_id = f"client_{id(websocket)}"
        
        self._clients.add(websocket)
        logger.info(f"Voice WS client connected: {client_id} (total: {len(self._clients)})")
        
        try:
            # Send welcome message
            await websocket.send_text(json.dumps({
                "event": "connected",
                "client_id": client_id,
                "message": "Connected to Axiom Voice Relay",
            }))
            
            # Keep connection alive, handle incoming messages
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    await self._handle_client_message(websocket, client_id, message)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {client_id}: {data}")
                    
        except WebSocketDisconnect:
            logger.info(f"Voice WS client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Voice WS error for {client_id}: {e}")
        finally:
            self._clients.discard(websocket)
    
    async def _handle_client_message(self, websocket: WebSocket, client_id: str, message: Dict) -> None:
        """Handle incoming message from client."""
        msg_type = message.get("type")
        
        if msg_type == "ping":
            await websocket.send_text(json.dumps({"type": "pong"}))
        elif msg_type == "push_to_talk":
            # Client requests push-to-talk activation
            entity = message.get("entity", "axiom")
            # This would trigger the pipeline's push_to_talk
            # For now, just acknowledge
            await websocket.send_text(json.dumps({
                "type": "push_to_talk_ack",
                "entity": entity,
                "status": "triggered",
            }))
        elif msg_type == "stop_listening":
            # Client requests to stop listening
            await websocket.send_text(json.dumps({
                "type": "stop_listening_ack",
                "status": "stopped",
            }))
    
    async def broadcast_event(self, event: Any) -> None:
        """Broadcast a voice event to all connected clients."""
        if not self._clients:
            return
        
        # Convert event to dict
        if hasattr(event, '__dict__'):
            event_dict = {
                "event": event.event_type,
                "entity": event.entity,
                "timestamp": event.timestamp,
                "data": event.data,
            }
        else:
            event_dict = event
        
        # Encode audio data as base64 if present
        if "audio_data" in event_dict.get("data", {}) and isinstance(event_dict["data"]["audio_data"], bytes):
            event_dict["data"]["audio_base64"] = base64.b64encode(event_dict["data"]["audio_data"]).decode("ascii")
            del event_dict["data"]["audio_data"]
        
        message = json.dumps(event_dict)
        
        # Send to all clients
        disconnected = set()
        for client in self._clients:
            try:
                await client.send_text(message)
            except Exception:
                disconnected.add(client)
        
        # Clean up disconnected clients
        for client in disconnected:
            self._clients.discard(client)
    
    async def send_to_client(self, client_id: str, event: Dict) -> bool:
        """Send event to specific client (not implemented - would need client tracking)."""
        # Would need a client_id -> websocket mapping
        return False
    
    def start(self) -> None:
        """Start the WebSocket server in background."""
        if self._running:
            return
        
        self._running = True
        
        # Create app if not exists
        if self._app is None:
            self.create_app()
        
        # Run in background thread
        import threading
        import uvicorn
        
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        
        # Wait for server to start
        time.sleep(0.5)
        logger.info(f"Voice relay server started on {self.host}:{self.port}")
    
    def _run_server(self) -> None:
        """Run the uvicorn server."""
        import uvicorn
        
        config = uvicorn.Config(
            self._app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=False,
        )
        server = uvicorn.Server(config)
        self._server = server
        
        # Run in new event loop
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(server.serve())
    
    def stop(self) -> None:
        """Stop the WebSocket server."""
        if not self._running:
            return
        
        self._running = False
        
        if self._server:
            self._server.should_exit = True
        
        if self._thread:
            self._thread.join(timeout=2.0)
        
        logger.info("Voice relay server stopped")
    
    @property
    def client_count(self) -> int:
        return len(self._clients)


# For backward compatibility
import time