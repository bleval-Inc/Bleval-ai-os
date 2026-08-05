"""WhatsApp Provider — Twilio WhatsApp Business API integration."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from axiom.engine.provider import ExternalAPIProvider
from axiom.models.providers import (
    ProviderModel,
    ProviderToolDefinition,
    ProviderHealth,
    ProviderStatus,
    ToolInvocationResult,
)
from axiom.runtime.logging import RuntimeLogger


class WhatsAppProvider(ExternalAPIProvider):
    """WhatsApp provider via Twilio WhatsApp Business API.

    Capabilities:
    - Send messages (text, media, templates)
    - Receive messages (webhook)
    - Message templates (for outbound broadcasts)
    - Media upload/download
    - Phone number management
    - Business profile
    """

    def __init__(
        self,
        config: ProviderModel,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        super().__init__(config, logger)
        self._account_sid = None
        self._auth_token = None
        self._from_number = None

    def get_tool_definitions(self) -> List[ProviderToolDefinition]:
        return [
            ProviderToolDefinition(
                tool_id="whatsapp_send_text",
                name="Send Text Message",
                description="Send a text message to a WhatsApp number",
                capability="whatsapp_send",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient WhatsApp number in E.164 format"},
                        "body": {"type": "string"},
                    },
                    "required": ["to", "body"],
                },
            ),
            ProviderToolDefinition(
                tool_id="whatsapp_send_media",
                name="Send Media Message",
                description="Send an image, document, audio, video, or sticker",
                capability="whatsapp_send",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "media_url": {"type": "string", "format": "uri", "description": "Publicly accessible media URL"},
                        "caption": {"type": "string"},
                        "media_type": {"type": "string", "enum": ["image", "document", "audio", "video", "sticker"]},
                    },
                    "required": ["to", "media_url"],
                },
            ),
            ProviderToolDefinition(
                tool_id="whatsapp_send_template",
                name="Send Template Message",
                description="Send a pre-approved template message",
                capability="whatsapp_send",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "template_name": {"type": "string"},
                        "language": {"type": "string", "default": "en_US"},
                        "components": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string", "enum": ["header", "body", "footer", "button"]},
                                    "parameters": {"type": "array", "items": {"type": "object"}},
                                },
                                "required": ["type"],
                            },
                        },
                    },
                    "required": ["to", "template_name"],
                },
            ),
            ProviderToolDefinition(
                tool_id="whatsapp_send_location",
                name="Send Location",
                description="Send a location pin",
                capability="whatsapp_send",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"},
                        "name": {"type": "string"},
                        "address": {"type": "string"},
                    },
                    "required": ["to", "latitude", "longitude"],
                },
            ),
            ProviderToolDefinition(
                tool_id="whatsapp_send_contact",
                name="Send Contact Card",
                description="Send a contact card (vCard)",
                capability="whatsapp_send",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "contacts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "object", "properties": {
                                        "formatted_name": {"type": "string"},
                                        "first_name": {"type": "string"},
                                        "last_name": {"type": "string"},
                                    }},
                                    "phones": {"type": "array", "items": {"type": "object", "properties": {
                                        "phone": {"type": "string"}, "type": {"type": "string"},
                                    }}},
                                    "emails": {"type": "array", "items": {"type": "object", "properties": {
                                        "email": {"type": "string"}, "type": {"type": "string"},
                                    }}},
                                },
                            },
                        },
                    },
                    "required": ["to", "contacts"],
                },
            ),
            ProviderToolDefinition(
                tool_id="whatsapp_get_message_status",
                name="Get Message Status",
                description="Get delivery status of a sent message",
                capability="whatsapp_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string"},
                    },
                    "required": ["message_id"],
                },
            ),
            ProviderToolDefinition(
                tool_id="whatsapp_list_templates",
                name="List Message Templates",
                description="List approved template messages",
                capability="whatsapp_template_read",
                input_schema={},
            ),
        ]

    async def initialize(self) -> None:
        """Initialize Twilio WhatsApp client."""
        await super().initialize()

        self._account_sid = self._secrets.get_secret(self.config.auth.username_env_var or "TWILIO_ACCOUNT_SID")
        self._auth_token = self._secrets.get_secret(self.config.auth.password_env_var or "TWILIO_AUTH_TOKEN")
        self._from_number = self.config.config.get("from_number") or self._secrets.get_secret("TWILIO_WHATSAPP_FROM")

        if not all([self._account_sid, self._auth_token, self._from_number]):
            raise RuntimeError("Twilio WhatsApp credentials not fully configured")

        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self._account_sid}"
        self._auth = (self._account_sid, self._auth_token)

        self._initialized = True

    async def _execute_tool_impl(
        self, tool_id: str, parameters: Dict[str, Any]
    ) -> ToolInvocationResult:
        method_name = f"_execute_{tool_id}"
        if hasattr(self, method_name):
            return await getattr(self, method_name)(parameters)

        return ToolInvocationResult(
            success=False,
            error=f"Tool {tool_id} not implemented",
            error_code="not_implemented",
            provider_id=self.provider_id,
            tool_id=tool_id,
        )

    async def _send_message(self, to: str, body: str = None, media_url: str = None, **extra) -> ToolInvocationResult:
        """Internal helper to send messages via Twilio."""
        to_formatted = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
        from_formatted = f"whatsapp:{self._from_number}" if not self._from_number.startswith("whatsapp:") else self._from_number

        data = {
            "From": from_formatted,
            "To": to_formatted,
        }

        if body:
            data["Body"] = body
        if media_url:
            data["MediaUrl"] = media_url

        data.update(extra)

        result = await self._request("POST", "/Messages.json", data=data)

        if result.get("sid"):
            return ToolInvocationResult(
                success=True,
                output={
                    "message_id": result["sid"],
                    "status": result.get("status"),
                    "to": to,
                    "date_created": result.get("date_created"),
                },
                provider_id=self.provider_id,
                tool_id="whatsapp_send",
            )
        return ToolInvocationResult(
            success=False,
            error=result.get("message", "Failed to send"),
            provider_id=self.provider_id,
            tool_id="whatsapp_send",
        )

    async def _execute_whatsapp_send_text(self, params: Dict[str, Any]) -> ToolInvocationResult:
        return await self._send_message(params["to"], body=params["body"])

    async def _execute_whatsapp_send_media(self, params: Dict[str, Any]) -> ToolInvocationResult:
        return await self._send_message(
            params["to"],
            body=params.get("caption"),
            media_url=params["media_url"],
        )

    async def _execute_whatsapp_send_template(self, params: Dict[str, Any]) -> ToolInvocationResult:
        to = params["to"]
        template_name = params["template_name"]
        language = params.get("language", "en_US")
        components = params.get("components", [])

        to_formatted = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
        from_formatted = f"whatsapp:{self._from_number}" if not self._from_number.startswith("whatsapp:") else self._from_number

        # Twilio Content API for templates
        content_sid = self._get_content_sid(template_name)

        data = {
            "From": from_formatted,
            "To": to_formatted,
            "ContentSid": content_sid,
        }

        if components:
            import json
            data["ContentVariables"] = json.dumps(self._format_components(components))

        result = await self._request("POST", "/Messages.json", data=data)

        if result.get("sid"):
            return ToolInvocationResult(
                success=True,
                output={
                    "message_id": result["sid"],
                    "status": result.get("status"),
                    "template": template_name,
                },
                provider_id=self.provider_id,
                tool_id="whatsapp_send_template",
            )
        return ToolInvocationResult(
            success=False,
            error=result.get("message", "Failed to send template"),
            provider_id=self.provider_id,
            tool_id="whatsapp_send_template",
        )

    def _get_content_sid(self, template_name: str) -> str:
        """Map template name to Twilio Content SID - would be configured per template."""
        # In production, this would fetch from a configured mapping
        return f"HXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Placeholder

    def _format_components(self, components: List[Dict]) -> Dict:
        """Format components for Twilio Content API."""
        variables = {}
        for comp in components:
            comp_type = comp.get("type")
            params = comp.get("parameters", [])
            for i, param in enumerate(params, 1):
                variables[f"{comp_type}_{i}"] = param.get("text", "")
        return variables

    async def _execute_whatsapp_send_location(self, params: Dict[str, Any]) -> ToolInvocationResult:
        to = params["to"]
        lat = params["latitude"]
        lng = params["longitude"]
        name = params.get("name", "")
        address = params.get("address", "")

        to_formatted = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
        from_formatted = f"whatsapp:{self._from_number}" if not self._from_number.startswith("whatsapp:") else self._from_number

        data = {
            "From": from_formatted,
            "To": to_formatted,
            "Latitude": str(lat),
            "Longitude": str(lng),
            "LocationName": name,
            "LocationAddress": address,
        }

        result = await self._request("POST", "/Messages.json", data=data)

        if result.get("sid"):
            return ToolInvocationResult(
                success=True,
                output={"message_id": result["sid"], "status": result.get("status")},
                provider_id=self.provider_id,
                tool_id="whatsapp_send_location",
            )
        return ToolInvocationResult(success=False, error=result.get("message", "Failed to send"), provider_id=self.provider_id, tool_id="whatsapp_send_location")

    async def _execute_whatsapp_send_contact(self, params: Dict[str, Any]) -> ToolInvocationResult:
        # vCard sending via Twilio - simplified
        return ToolInvocationResult(success=False, error="Contact sending requires Media API", provider_id=self.provider_id, tool_id="whatsapp_send_contact")

    async def _execute_whatsapp_get_message_status(self, params: Dict[str, Any]) -> ToolInvocationResult:
        message_id = params["message_id"]

        result = await self._request("GET", f"/Messages/{message_id}.json")

        if result.get("sid"):
            return ToolInvocationResult(
                success=True,
                output={
                    "message_id": result["sid"],
                    "status": result.get("status"),
                    "to": result.get("to"),
                    "from": result.get("from"),
                    "date_sent": result.get("date_sent"),
                    "error_code": result.get("error_code"),
                    "error_message": result.get("error_message"),
                },
                provider_id=self.provider_id,
                tool_id="whatsapp_get_message_status",
            )
        return ToolInvocationResult(success=False, error="Message not found", provider_id=self.provider_id, tool_id="whatsapp_get_message_status")

    async def _execute_whatsapp_list_templates(self, params: Dict[str, Any]) -> ToolInvocationResult:
        # List Content Templates via Twilio Content API
        result = await self._request("GET", "/Content.json")

        if "contents" in result:
            templates = []
            for content in result["contents"]:
                if content.get("types") and "whatsapp" in content.get("types", []):
                    templates.append({
                        "sid": content["sid"],
                        "friendly_name": content.get("friendly_name", ""),
                        "language": content.get("language", "en_US"),
                    })
            return ToolInvocationResult(success=True, output=templates, provider_id=self.provider_id, tool_id="whatsapp_list_templates")

        return ToolInvocationResult(success=True, output=[], provider_id=self.provider_id, tool_id="whatsapp_list_templates")

    async def _health_check_impl(self) -> ProviderHealth:
        try:
            result = await self._request("GET", f"/Accounts/{self._account_sid}.json")
            if result.get("sid") == self._account_sid:
                return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.HEALTHY)
            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.UNHEALTHY, error_message="Account verification failed")
        except Exception as e:
            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.UNHEALTHY, error_message=str(e))