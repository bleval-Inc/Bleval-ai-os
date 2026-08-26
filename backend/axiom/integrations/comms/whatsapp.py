"""WhatsApp Provider — Twilio WhatsApp Business API."""

import asyncio
import hashlib
import hmac
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel, Field, SecretStr

from axiom.data.models import (
    WhatsAppMessage,
    MessageDirection,
    MessageStatus,
)
from axiom.integrations.layer import IntegrationLayer
from axiom.runtime.logging import RuntimeLogger


class WhatsAppConfig(BaseModel):
    """WhatsApp configuration."""

    # Twilio credentials
    account_sid: str
    auth_token: SecretStr
    whatsapp_number: str  # e.g., whatsapp:+14155238886

    # Webhook
    webhook_url: str
    webhook_secret: Optional[SecretStr] = None

    # Behavior
    enabled: bool = True
    session_timeout_minutes: int = 24 * 60  # 24 hours

    # Templates
    template_namespace: Optional[str] = None

    # Rate limits
    rate_limit_rpm: int = 60


class WhatsAppProvider:
    """WhatsApp Business API provider via Twilio."""

    def __init__(
        self,
        integration_layer: IntegrationLayer,
        config: WhatsAppConfig,
        repository,  # CommsRepository
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.config = config
        self.repository = repository
        self.logger = logger or RuntimeLogger()

        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._webhook_handlers: Dict[str, List] = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            auth = aiohttp.BasicAuth(
                self.config.account_sid,
                self.config.auth_token.get_secret_value()
            )
            self._session = aiohttp.ClientSession(auth=auth)
        return self._session

    async def start(self):
        """Start WhatsApp provider."""
        if self._running:
            return
        self._running = True
        self.logger.info("WhatsApp provider started")

    async def stop(self):
        """Stop WhatsApp provider."""
        self._running = False
        if self._session and not self._session.closed:
            await self._session.close()
        self.logger.info("WhatsApp provider stopped")

    # ──────────────────────────────────────────────────────────────────────────────
    # Sending Messages
    # ──────────────────────────────────────────────────────────────────────────────

    async def send_message(
        self,
        to_number: str,
        body: str,
        media_urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send a text message."""
        session = await self._get_session()

        payload = {
            "From": self.config.whatsapp_number,
            "To": f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number,
            "Body": body,
        }

        if media_urls:
            payload["MediaUrl"] = media_urls[0]  # Twilio takes first

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.config.account_sid}/Messages.json"

        async with session.post(url, data=payload) as resp:
            data = await resp.json()
            if resp.status == 201:
                return {"status": "sent", "message_sid": data.get("sid")}
            else:
                return {"status": "failed", "error": data.get("message", "Unknown error")}

    async def send_template(
        self,
        to_number: str,
        template_name: str,
        language: str = "en",
        variables: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send a template message."""
        session = await self._get_session()

        payload = {
            "From": self.config.whatsapp_number,
            "To": f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number,
            "ContentSid": template_name,  # Content SID for approved templates
        }

        if variables:
            # Variables would be formatted per template
            payload["ContentVariables"] = json.dumps({"1": variables[0]})  # Simplified

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.config.account_sid}/Messages.json"

        async with session.post(url, data=payload) as resp:
            data = await resp.json()
            if resp.status == 201:
                return {"status": "sent", "message_sid": data.get("sid")}
            else:
                return {"status": "failed", "error": data.get("message")}

    async def send_media(
        self,
        to_number: str,
        media_url: str,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send media message."""
        session = await self._get_session()

        payload = {
            "From": self.config.whatsapp_number,
            "To": f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number,
            "MediaUrl": media_url,
        }
        if caption:
            payload["Body"] = caption

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.config.account_sid}/Messages.json"

        async with session.post(url, data=payload) as resp:
            data = await resp.json()
            if resp.status == 201:
                return {"status": "sent", "message_sid": data.get("sid")}
            else:
                return {"status": "failed", "error": data.get("message")}

    async def send_location(
        self,
        to_number: str,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send location message."""
        # Would use Twilio's location messaging
        pass

    # ──────────────────────────────────────────────────────────────────────────────
    # Receiving Messages (Webhook)
    # ──────────────────────────────────────────────────────────────────────────────

    async def handle_webhook(self, request: Any) -> Dict[str, Any]:
        """Handle incoming webhook from Twilio."""
        # Verify signature
        if self.config.webhook_secret:
            if not self._verify_signature(request):
                return {"status": "unauthorized"}

        # Parse form data
        form = await request.form() if hasattr(request, "form") else request

        message_sid = form.get("MessageSid")
        account_sid = form.get("AccountSid")
        from_number = form.get("From", "").replace("whatsapp:", "")
        to_number = form.get("To", "").replace("whatsapp:", "")
        body = form.get("Body", "")
        num_media = int(form.get("NumMedia", "0"))
        message_type = form.get("MessageType", "text")

        # Media URLs
        media_urls = []
        media_content_type = None
        for i in range(num_media):
            media_url = form.get(f"MediaUrl{i}")
            content_type = form.get(f"MediaContentType{i}")
            if media_url:
                media_urls.append(media_url)
                if not media_content_type:
                    media_content_type = content_type

        # Create message object
        message = WhatsAppMessage(
            uuid=self._generate_uuid(),
            message_sid=message_sid,
            account_sid=account_sid,
            from_number=from_number,
            to_number=to_number,
            body=body if body else None,
            media_urls=media_urls if media_urls else None,
            media_content_type=media_content_type,
            num_media=num_media,
            message_type=message_type,
            direction=MessageDirection.INBOUND,
            status=MessageStatus.DELIVERED,
            conversation_id=self._get_conversation_id(from_number, to_number),
        )

        # Store
        await self.repository.upsert_whatsapp_message(message)

        # Trigger handlers
        await self._trigger_handlers("message", message)

        return {"status": "ok"}

    async def handle_status_callback(self, request: Any) -> Dict[str, Any]:
        """Handle message status callback."""
        form = await request.form() if hasattr(request, "form") else request

        message_sid = form.get("MessageSid")
        status = form.get("MessageStatus")  # queued, sent, delivered, read, failed
        error_code = form.get("ErrorCode")
        error_message = form.get("ErrorMessage")

        # Update message status
        await self.repository.update_whatsapp_status(
            message_sid,
            MessageStatus(status),
            delivered_at=datetime.utcnow() if status == "delivered" else None,
            read_at=datetime.utcnow() if status == "read" else None,
            error_code=error_code,
            error_message=error_message,
        )

        return {"status": "ok"}

    def _verify_signature(self, request: Any) -> bool:
        """Verify Twilio webhook signature."""
        # Implementation would validate X-Twilio-Signature header
        return True

    def _get_conversation_id(self, from_num: str, to_num: str) -> str:
        """Generate consistent conversation ID."""
        # Sort to ensure same ID regardless of direction
        sorted_nums = sorted([from_num, to_number])
        return hashlib.md5("".join(sorted_nums).encode()).hexdigest()[:16]

    def _generate_uuid(self) -> str:
        import uuid
        return str(uuid.uuid4())

    # ──────────────────────────────────────────────────────────────────────────────
    # Message Management
    # ──────────────────────────────────────────────────────────────────────────────

    async def get_message_history(
        self,
        from_number: str,
        to_number: str,
        limit: int = 50,
    ) -> List[WhatsAppMessage]:
        """Get conversation history."""
        return await self.repository.get_whatsapp_conversation(
            self._get_conversation_id(from_number, to_number), limit
        )

    async def mark_as_read(self, message_sid: str) -> bool:
        """Mark message as read (send read receipt)."""
        # Would use Twilio's read receipts if available
        return True

    # ──────────────────────────────────────────────────────────────────────────────
    # Template Management
    # ──────────────────────────────────────────────────────────────────────────────

    async def list_templates(self) -> List[Dict]:
        """List approved templates."""
        # Would call Twilio API
        return []

    async def create_template(
        self,
        name: str,
        category: str,
        language: str,
        components: List[Dict],
    ) -> Dict:
        """Submit template for approval."""
        # Would call Twilio API
        pass

    # ──────────────────────────────────────────────────────────────────────────────
    # Event Handlers
    # ──────────────────────────────────────────────────────────────────────────────

    def on_message(self, handler):
        """Register message handler."""
        if "message" not in self._webhook_handlers:
            self._webhook_handlers["message"] = []
        self._webhook_handlers["message"].append(handler)

    async def _trigger_handlers(self, event_type: str, data: Any):
        """Trigger registered handlers."""
        handlers = self._webhook_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                self.logger.error(f"Handler error: {e}")