"""Slack Provider — Real-time messaging, channels, DMs, webhooks."""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

import aiohttp
from pydantic import BaseModel, Field, SecretStr

from axiom.data.models import (
    SlackMessage,
    MessageDirection,
    MessageStatus,
)
from axiom.integrations.layer import IntegrationLayer
from axiom.runtime.logging import RuntimeLogger


class SlackConfig(BaseModel):
    """Slack configuration."""

    bot_token: SecretStr
    signing_secret: SecretStr
    app_token: Optional[SecretStr] = None  # For Socket Mode
    client_id: Optional[str] = None
    client_secret: Optional[SecretStr] = None

    # Behavior
    enabled: bool = True
    socket_mode: bool = False
    auto_reconnect: bool = True
    reconnect_interval: int = 5

    # Subscriptions
    subscribe_channels: List[str] = Field(default_factory=list)  # Channel IDs
    subscribe_dm: bool = True
    subscribe_threads: bool = True

    # Rate limits
    rate_limit_rpm: int = 50

    # Webhook
    webhook_url: Optional[str] = None


class SlackEvent(BaseModel):
    """Parsed Slack event."""

    type: str
    event_ts: str
    channel_id: str
    channel_type: str  # channel, group, im, mpim
    user_id: Optional[str] = None
    text: Optional[str] = None
    blocks: Optional[List[Dict]] = None
    files: Optional[List[Dict]] = None
    thread_ts: Optional[str] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class SlackProvider:
    """Slack real-time messaging provider."""

    def __init__(
        self,
        integration_layer: IntegrationLayer,
        config: SlackConfig,
        repository,  # CommsRepository
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.config = config
        self.repository = repository
        self.logger = logger or RuntimeLogger()

        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._running = False
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._bot_user_id: Optional[str] = None
        self._channel_cache: Dict[str, Dict] = {}
        self._user_cache: Dict[str, Dict] = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.config.bot_token.get_secret_value()}"}
            )
        return self._session

    async def start(self):
        """Start Slack connection."""
        if self._running:
            return

        # Get bot info
        await self._auth_test()

        if self.config.socket_mode:
            await self._connect_socket_mode()
        else:
            await self._connect_events_api()

        self._running = True
        self.logger.info("Slack provider started")

    async def stop(self):
        """Stop Slack connection."""
        self._running = False
        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._session and not self._session.closed:
            await self._session.close()
        self.logger.info("Slack provider stopped")

    async def _auth_test(self):
        """Authenticate and get bot user ID."""
        session = await self._get_session()
        async with session.post("https://slack.com/api/auth.test") as resp:
            data = await resp.json()
            if data.get("ok"):
                self._bot_user_id = data.get("user_id")
                self.logger.info(f"Slack auth successful: {self._bot_user_id}")
            else:
                raise Exception(f"Slack auth failed: {data.get('error')}")

    async def _connect_socket_mode(self):
        """Connect via Socket Mode (WebSocket)."""
        session = await self._get_session()
        async with session.post(
            "https://slack.com/api/apps.connections.open",
            json={"app_token": self.config.app_token.get_secret_value()}
        ) as resp:
            data = await resp.json()
            if not data.get("ok"):
                raise Exception(f"Socket mode connection failed: {data.get('error')}")

            ws_url = data["url"]
            self._ws = await session.ws_connect(ws_url)

            asyncio.create_task(self._listen_socket_mode())

    async def _connect_events_api(self):
        """Connect via Events API (would need HTTPS endpoint)."""
        # Events API requires a public HTTPS endpoint for webhooks
        # This would be handled by the integration layer's HTTP server
        pass

    async def _listen_socket_mode(self):
        """Listen for events via Socket Mode."""
        async for msg in self._ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                await self._handle_socket_message(data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                self.logger.error(f"Slack WebSocket error: {self._ws.exception()}")
                break

        if self.config.auto_reconnect and self._running:
            await asyncio.sleep(self.config.reconnect_interval)
            await self._connect_socket_mode()

    async def _handle_socket_message(self, data: Dict[str, Any]):
        """Handle incoming socket message."""
        envelope_id = data.get("envelope_id")
        payload = data.get("payload", {})

        # Acknowledge receipt
        if envelope_id:
            await self._ws.send_json({"envelope_id": envelope_id})

        if payload.get("type") == "event_callback":
            event = payload.get("event", {})
            await self._process_event(event)

    async def _process_event(self, event: Dict[str, Any]):
        """Process Slack event."""
        event_type = event.get("type")

        # Skip bot's own messages unless explicitly handling
        if event.get("user") == self._bot_user_id:
            return

        # Filter by subscription
        channel_id = event.get("channel")
        channel_type = event.get("channel_type")

        if channel_type == "im" and not self.config.subscribe_dm:
            return
        if self.config.subscribe_channels and channel_id not in self.config.subscribe_channels:
            return

        # Parse event
        slack_event = SlackEvent(
            type=event_type,
            event_ts=event.get("event_ts", ""),
            channel_id=channel_id or "",
            channel_type=channel_type or "",
            user_id=event.get("user"),
            text=event.get("text"),
            blocks=event.get("blocks"),
            files=event.get("files"),
            thread_ts=event.get("thread_ts"),
            raw=event,
        )

        # Store message
        await self._store_message(slack_event)

        # Trigger handlers
        for handler in self._event_handlers.get(event_type, []):
            try:
                await handler(slack_event)
            except Exception as e:
                self.logger.error(f"Event handler error: {e}")

        # Generic handler
        for handler in self._event_handlers.get("*", []):
            try:
                await handler(slack_event)
            except Exception as e:
                self.logger.error(f"Generic handler error: {e}")

    async def _store_message(self, event: SlackEvent):
        """Store Slack message in repository."""
        # Get channel info
        channel_name = None
        if event.channel_id in self._channel_cache:
            channel_name = self._channel_cache[event.channel_id].get("name")

        # Get user info
        username = None
        display_name = None
        if event.user_id and event.user_id in self._user_cache:
            user = self._user_cache[event.user_id]
            username = user.get("name")
            display_name = user.get("profile", {}).get("display_name")

        message = SlackMessage(
            uuid=self._generate_uuid(),
            ts=event.event_ts,
            thread_ts=event.thread_ts,
            channel_id=event.channel_id,
            channel_name=channel_name,
            user_id=event.user_id or "",
            username=username,
            display_name=display_name,
            is_bot=event.raw.get("bot_id") is not None,
            bot_id=event.raw.get("bot_id"),
            text=event.text,
            blocks=event.blocks,
            attachments=event.raw.get("attachments"),
            files=event.files,
            reactions=event.raw.get("reactions"),
            direction=MessageDirection.INBOUND,
            status=MessageStatus.DELIVERED,
            permalink=event.raw.get("permalink"),
            posted_at=datetime.fromtimestamp(float(event.event_ts.split(".")[0])) if event.event_ts else datetime.utcnow(),
        )

        await self.repository.upsert_slack_message(message)

    def _generate_uuid(self) -> str:
        import uuid
        return str(uuid.uuid4())

    # ──────────────────────────────────────────────────────────────────────────────
    # Sending Messages
    # ──────────────────────────────────────────────────────────────────────────────

    async def send_message(
        self,
        channel_id: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
        thread_ts: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send a message to a channel."""
        session = await self._get_session()
        payload = {"channel": channel_id}
        if text:
            payload["text"] = text
        if blocks:
            payload["blocks"] = blocks
        if thread_ts:
            payload["thread_ts"] = thread_ts
        if attachments:
            payload["attachments"] = attachments

        async with session.post("https://slack.com/api/chat.postMessage", json=payload) as resp:
            data = await resp.json()
            if data.get("ok"):
                self.logger.debug(f"Message sent to {channel_id}")
                return data
            else:
                self.logger.error(f"Failed to send message: {data.get('error')}")
                return None

    async def send_dm(
        self,
        user_id: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Send a direct message."""
        # Open DM channel
        session = await self._get_session()
        async with session.post(
            "https://slack.com/api/conversations.open",
            json={"users": user_id}
        ) as resp:
            data = await resp.json()
            if data.get("ok"):
                channel_id = data["channel"]["id"]
                return await self.send_message(channel_id, text, blocks)
        return None

    async def reply_in_thread(
        self,
        channel_id: str,
        thread_ts: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Reply in a thread."""
        return await self.send_message(channel_id, text, blocks, thread_ts)

    async def update_message(
        self,
        channel_id: str,
        ts: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict]] = None,
    ) -> bool:
        """Update a message."""
        session = await self._get_session()
        payload = {"channel": channel_id, "ts": ts}
        if text:
            payload["text"] = text
        if blocks:
            payload["blocks"] = blocks

        async with session.post("https://slack.com/api/chat.update", json=payload) as resp:
            data = await resp.json()
            return data.get("ok", False)

    async def delete_message(self, channel_id: str, ts: str) -> bool:
        """Delete a message."""
        session = await self._get_session()
        async with session.post(
            "https://slack.com/api/chat.delete",
            json={"channel": channel_id, "ts": ts}
        ) as resp:
            data = await resp.json()
            return data.get("ok", False)

    async def add_reaction(self, channel_id: str, ts: str, reaction: str) -> bool:
        """Add reaction to message."""
        session = await self._get_session()
        async with session.post(
            "https://slack.com/api/reactions.add",
            json={"channel": channel_id, "timestamp": ts, "name": reaction}
        ) as resp:
            data = await resp.json()
            return data.get("ok", False)

    # ──────────────────────────────────────────────────────────────────────────────
    # Channel/ User Management
    # ──────────────────────────────────────────────────────────────────────────────

    async def get_channel_info(self, channel_id: str) -> Optional[Dict]:
        """Get channel information."""
        if channel_id in self._channel_cache:
            return self._channel_cache[channel_id]

        session = await self._get_session()
        async with session.get(
            "https://slack.com/api/conversations.info",
            params={"channel": channel_id}
        ) as resp:
            data = await resp.json()
            if data.get("ok"):
                self._channel_cache[channel_id] = data["channel"]
                return data["channel"]
        return None

    async def list_channels(self, types: str = "public_channel,private_channel") -> List[Dict]:
        """List channels."""
        session = await self._get_session()
        channels = []
        cursor = None

        while True:
            params = {"types": types, "limit": 200}
            if cursor:
                params["cursor"] = cursor

            async with session.get(
                "https://slack.com/api/conversations.list",
                params=params
            ) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    break

                channels.extend(data.get("channels", []))
                cursor = data.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break

        # Cache
        for ch in channels:
            self._channel_cache[ch["id"]] = ch

        return channels

    async def get_user_info(self, user_id: str) -> Optional[Dict]:
        """Get user information."""
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        session = await self._get_session()
        async with session.get(
            "https://slack.com/api/users.info",
            params={"user": user_id}
        ) as resp:
            data = await resp.json()
            if data.get("ok"):
                self._user_cache[user_id] = data["user"]
                return data["user"]
        return None

    async def invite_to_channel(self, channel_id: str, user_ids: List[str]) -> bool:
        """Invite users to channel."""
        session = await self._get_session()
        async with session.post(
            "https://slack.com/api/conversations.invite",
            json={"channel": channel_id, "users": ",".join(user_ids)}
        ) as resp:
            data = await resp.json()
            return data.get("ok", False)

    # ──────────────────────────────────────────────────────────────────────────────
    # Event Handlers
    # ──────────────────────────────────────────────────────────────────────────────

    def on_event(self, event_type: str):
        """Decorator to register event handler."""
        def decorator(func: Callable):
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(func)
            return func
        return decorator

    async def handle_message(self, event: SlackEvent):
        """Default message handler - can be overridden."""
        self.logger.debug(f"Message in {event.channel_id}: {event.text[:50] if event.text else 'no text'}")


class SlackWebhookHandler:
    """Handles incoming Slack webhooks (for non-Socket Mode)."""

    def __init__(self, provider: SlackProvider, logger: Optional[RuntimeLogger] = None):
        self.provider = provider
        self.logger = logger or RuntimeLogger()

    async def handle_request(self, request: Any) -> Dict[str, Any]:
        """Handle incoming HTTP request from Slack."""
        # Verify signature
        # Parse payload
        # Process event
        pass