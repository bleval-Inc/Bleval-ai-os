"""Slack Provider — Channels, messages, notifications, search, users."""

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


class SlackProvider(ExternalAPIProvider):
    """Slack provider for team communication.

    Capabilities:
    - Channel management (list, create, archive, info)
    - Message sending (text, blocks, threads, files)
    - Message search and history
    - User management (list, info, presence)
    - Notifications and mentions
    - Reactions and emoji
    - Webhook integration
    - App management
    """

    def __init__(
        self,
        config: ProviderModel,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        super().__init__(config, logger)
        self._bot_token = None
        self._user_token = None

    def get_tool_definitions(self) -> List[ProviderToolDefinition]:
        return [
            # Channels
            ProviderToolDefinition(
                tool_id="slack_list_channels",
                name="List Channels",
                description="List all channels",
                capability="slack_channel_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "types": {"type": "array", "items": {"type": "string", "enum": ["public_channel", "private_channel", "mpim", "im"]}, "default": ["public_channel"]},
                        "exclude_archived": {"type": "boolean", "default": True},
                        "limit": {"type": "integer", "default": 100},
                    },
                },
            ),
            ProviderToolDefinition(
                tool_id="slack_create_channel",
                name="Create Channel",
                description="Create a new channel",
                capability="slack_channel_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "is_private": {"type": "boolean", "default": False},
                    },
                    "required": ["name"],
                },
            ),
            ProviderToolDefinition(
                tool_id="slack_get_channel_info",
                name="Get Channel Info",
                description="Get detailed channel information",
                capability="slack_channel_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "channel_id": {"type": "string"},
                    },
                    "required": ["channel_id"],
                },
            ),
            ProviderToolDefinition(
                tool_id="slack_archive_channel",
                name="Archive Channel",
                description="Archive a channel",
                capability="slack_channel_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "channel_id": {"type": "string"},
                    },
                    "required": ["channel_id"],
                },
            ),
            # Messages
            ProviderToolDefinition(
                tool_id="slack_send_message",
                name="Send Message",
                description="Send a message to a channel or user",
                capability="slack_message_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "channel_id": {"type": "string"},
                        "text": {"type": "string"},
                        "blocks": {"type": "array", "description": "Block Kit blocks"},
                        "thread_ts": {"type": "string", "description": "Thread timestamp for replies"},
                        "attachments": {"type": "array"},
                        "as_user": {"type": "boolean", "default": True},
                    },
                    "required": ["channel_id", "text"],
                },
            ),
            ProviderToolDefinition(
                tool_id="slack_get_message_history",
                name="Get Message History",
                description="Get message history from a channel",
                capability="slack_message_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "channel_id": {"type": "string"},
                        "limit": {"type": "integer", "default": 50},
                        "oldest": {"type": "string"},
                        "latest": {"type": "string"},
                        "inclusive": {"type": "boolean", "default": False},
                    },
                    "required": ["channel_id"],
                },
            ),
            ProviderToolDefinition(
                tool_id="slack_search_messages",
                name="Search Messages",
                description="Search messages across workspace",
                capability="slack_message_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "sort": {"type": "string", "enum": ["score", "timestamp"], "default": "score"},
                        "sort_dir": {"type": "string", "enum": ["asc", "desc"], "default": "desc"},
                        "count": {"type": "integer", "default": 20},
                    },
                    "required": ["query"],
                },
            ),
            ProviderToolDefinition(
                tool_id="slack_update_message",
                name="Update Message",
                description="Update a sent message",
                capability="slack_message_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "channel_id": {"type": "string"},
                        "ts": {"type": "string"},
                        "text": {"type": "string"},
                        "blocks": {"type": "array"},
                    },
                    "required": ["channel_id", "ts"],
                },
            ),
            ProviderToolDefinition(
                tool_id="slack_delete_message",
                name="Delete Message",
                description="Delete a message",
                capability="slack_message_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "channel_id": {"type": "string"},
                        "ts": {"type": "string"},
                    },
                    "required": ["channel_id", "ts"],
                },
            ),
            # Reactions
            ProviderToolDefinition(
                tool_id="slack_add_reaction",
                name="Add Reaction",
                description="Add emoji reaction to message",
                capability="slack_reaction_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "channel_id": {"type": "string"},
                        "timestamp": {"type": "string"},
                        "name": {"type": "string"},
                    },
                    "required": ["channel_id", "timestamp", "name"],
                },
            ),
            # Users
            ProviderToolDefinition(
                tool_id="slack_list_users",
                name="List Users",
                description="List all workspace users",
                capability="slack_user_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 100},
                    },
                },
            ),
            ProviderToolDefinition(
                tool_id="slack_get_user_info",
                name="Get User Info",
                description="Get detailed user information",
                capability="slack_user_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                    },
                    "required": ["user_id"],
                },
            ),
            ProviderToolDefinition(
                tool_id="slack_get_user_presence",
                name="Get User Presence",
                description="Get user's presence status",
                capability="slack_user_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                    },
                    "required": ["user_id"],
                },
            ),
            # Files
            ProviderToolDefinition(
                tool_id="slack_upload_file",
                name="Upload File",
                description="Upload a file to Slack",
                capability="slack_file_write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "channels": {"type": "array", "items": {"type": "string"}},
                        "content": {"type": "string", "description": "Base64 encoded content"},
                        "filename": {"type": "string"},
                        "title": {"type": "string"},
                        "initial_comment": {"type": "string"},
                    },
                    "required": ["channels", "content", "filename"],
                },
            ),
        ]

    async def initialize(self) -> None:
        """Initialize Slack API client."""
        await super().initialize()

        self._bot_token = self._secrets.get_secret(self.config.auth.token_env_var or "SLACK_BOT_TOKEN")
        if not self._bot_token:
            raise RuntimeError("Slack bot token not configured")

        self._user_token = self._secrets.get_secret("SLACK_USER_TOKEN")

        self.base_url = "https://slack.com/api"
        self._default_headers = {
            "Authorization": f"Bearer {self._bot_token}",
            "Content-Type": "application/json; charset=utf-8",
        }
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

    # ── Channels ────────────────────────────────────────────────────────────

    async def _execute_slack_list_channels(self, params: Dict[str, Any]) -> ToolInvocationResult:
        types = params.get("types", ["public_channel"])
        exclude_archived = params.get("exclude_archived", True)
        limit = params.get("limit", 100)

        params_dict = {
            "types": ",".join(types),
            "exclude_archived": str(exclude_archived).lower(),
            "limit": limit,
        }

        result = await self._request("GET", "/conversations.list", params=params_dict)
        if result.get("ok"):
            return ToolInvocationResult(success=True, output=result.get("channels", []), provider_id=self.provider_id, tool_id="slack_list_channels")
        return ToolInvocationResult(success=False, error=result.get("error", "Unknown error"), provider_id=self.provider_id, tool_id="slack_list_channels")

    async def _execute_slack_create_channel(self, params: Dict[str, Any]) -> ToolInvocationResult:
        name = params["name"]
        is_private = params.get("is_private", False)

        result = await self._request("POST", "/conversations.create", json={"name": name, "is_private": is_private})
        if result.get("ok"):
            return ToolInvocationResult(success=True, output=result.get("channel", {}), provider_id=self.provider_id, tool_id="slack_create_channel")
        return ToolInvocationResult(success=False, error=result.get("error", "Unknown error"), provider_id=self.provider_id, tool_id="slack_create_channel")

    async def _execute_slack_get_channel_info(self, params: Dict[str, Any]) -> ToolInvocationResult:
        channel_id = params["channel_id"]

        result = await self._request("GET", "/conversations.info", params={"channel": channel_id})
        if result.get("ok"):
            return ToolInvocationResult(success=True, output=result.get("channel", {}), provider_id=self.provider_id, tool_id="slack_get_channel_info")
        return ToolInvocationResult(success=False, error=result.get("error", "Unknown error"), provider_id=self.provider_id, tool_id="slack_get_channel_info")

    async def _execute_slack_archive_channel(self, params: Dict[str, Any]) -> ToolInvocationResult:
        channel_id = params["channel_id"]

        result = await self._request("POST", "/conversations.archive", json={"channel": channel_id})
        if result.get("ok"):
            return ToolInvocationResult(success=True, output={"archived": True}, provider_id=self.provider_id, tool_id="slack_archive_channel")
        return ToolInvocationResult(success=False, error=result.get("error", "Unknown error"), provider_id=self.provider_id, tool_id="slack_archive_channel")

    # ── Messages ────────────────────────────────────────────────────────────

    async def _execute_slack_send_message(self, params: Dict[str, Any]) -> ToolInvocationResult:
        data = {
            "channel": params["channel_id"],
            "text": params["text"],
            "as_user": params.get("as_user", True),
        }

        if params.get("blocks"):
            data["blocks"] = params["blocks"]
        if params.get("thread_ts"):
            data["thread_ts"] = params["thread_ts"]
        if params.get("attachments"):
            data["attachments"] = params["attachments"]

        result = await self._request("POST", "/chat.postMessage", json=data)
        if result.get("ok"):
            return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="slack_send_message")
        return ToolInvocationResult(success=False, error=result.get("error", "Unknown error"), provider_id=self.provider_id, tool_id="slack_send_message")

    async def _execute_slack_get_message_history(self, params: Dict[str, Any]) -> ToolInvocationResult:
        channel_id = params["channel_id"]
        limit = params.get("limit", 50)

        query = {"channel": channel_id, "limit": limit}
        if params.get("oldest"):
            query["oldest"] = params["oldest"]
        if params.get("latest"):
            query["latest"] = params["latest"]
        if params.get("inclusive"):
            query["inclusive"] = str(params["inclusive"]).lower()

        result = await self._request("GET", "/conversations.history", params=query)
        if result.get("ok"):
            return ToolInvocationResult(success=True, output=result.get("messages", []), provider_id=self.provider_id, tool_id="slack_get_message_history")
        return ToolInvocationResult(success=False, error=result.get("error", "Unknown error"), provider_id=self.provider_id, tool_id="slack_get_message_history")

    async def _execute_slack_search_messages(self, params: Dict[str, Any]) -> ToolInvocationResult:
        query = params["query"]
        sort = params.get("sort", "score")
        sort_dir = params.get("sort_dir", "desc")
        count = params.get("count", 20)

        result = await self._request("GET", "/search.messages", params={
            "query": query,
            "sort": sort,
            "sort_dir": sort_dir,
            "count": count,
        })

        if result.get("ok"):
            return ToolInvocationResult(success=True, output=result.get("messages", {}).get("matches", []), provider_id=self.provider_id, tool_id="slack_search_messages")
        return ToolInvocationResult(success=False, error=result.get("error", "Unknown error"), provider_id=self.provider_id, tool_id="slack_search_messages")

    async def _execute_slack_update_message(self, params: Dict[str, Any]) -> ToolInvocationResult:
        channel_id = params["channel_id"]
        ts = params["ts"]

        data = {"channel": channel_id, "ts": ts}
        if params.get("text"):
            data["text"] = params["text"]
        if params.get("blocks"):
            data["blocks"] = params["blocks"]

        result = await self._request("POST", "/chat.update", json=data)
        if result.get("ok"):
            return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="slack_update_message")
        return ToolInvocationResult(success=False, error=result.get("error", "Unknown error"), provider_id=self.provider_id, tool_id="slack_update_message")

    async def _execute_slack_delete_message(self, params: Dict[str, Any]) -> ToolInvocationResult:
        channel_id = params["channel_id"]
        ts = params["ts"]

        result = await self._request("POST", "/chat.delete", json={"channel": channel_id, "ts": ts})
        if result.get("ok"):
            return ToolInvocationResult(success=True, output={"deleted": True}, provider_id=self.provider_id, tool_id="slack_delete_message")
        return ToolInvocationResult(success=False, error=result.get("error", "Unknown error"), provider_id=self.provider_id, tool_id="slack_delete_message")

    # ── Reactions ────────────────────────────────────────────────────────────

    async def _execute_slack_add_reaction(self, params: Dict[str, Any]) -> ToolInvocationResult:
        channel_id = params["channel_id"]
        timestamp = params["timestamp"]
        name = params["name"]

        result = await self._request("POST", "/reactions.add", json={"channel": channel_id, "timestamp": timestamp, "name": name})
        if result.get("ok"):
            return ToolInvocationResult(success=True, output={"added": True}, provider_id=self.provider_id, tool_id="slack_add_reaction")
        return ToolInvocationResult(success=False, error=result.get("error", "Unknown error"), provider_id=self.provider_id, tool_id="slack_add_reaction")

    # ── Users ────────────────────────────────────────────────────────────────

    async def _execute_slack_list_users(self, params: Dict[str, Any]) -> ToolInvocationResult:
        limit = params.get("limit", 100)

        result = await self._request("GET", "/users.list", params={"limit": limit})
        if result.get("ok"):
            return ToolInvocationResult(success=True, output=result.get("members", []), provider_id=self.provider_id, tool_id="slack_list_users")
        return ToolInvocationResult(success=False, error=result.get("error", "Unknown error"), provider_id=self.provider_id, tool_id="slack_list_users")

    async def _execute_slack_get_user_info(self, params: Dict[str, Any]) -> ToolInvocationResult:
        user_id = params["user_id"]

        result = await self._request("GET", "/users.info", params={"user": user_id})
        if result.get("ok"):
            return ToolInvocationResult(success=True, output=result.get("user", {}), provider_id=self.provider_id, tool_id="slack_get_user_info")
        return ToolInvocationResult(success=False, error=result.get("error", "Unknown error"), provider_id=self.provider_id, tool_id="slack_get_user_info")

    async def _execute_slack_get_user_presence(self, params: Dict[str, Any]) -> ToolInvocationResult:
        user_id = params["user_id"]

        result = await self._request("GET", "/users.getPresence", params={"user": user_id})
        if result.get("ok"):
            return ToolInvocationResult(success=True, output=result, provider_id=self.provider_id, tool_id="slack_get_user_presence")
        return ToolInvocationResult(success=False, error=result.get("error", "Unknown error"), provider_id=self.provider_id, tool_id="slack_get_user_presence")

    # ── Files ────────────────────────────────────────────────────────────────

    async def _execute_slack_upload_file(self, params: Dict[str, Any]) -> ToolInvocationResult:
        import base64

        channels = params["channels"]
        content = base64.b64decode(params["content"])
        filename = params["filename"]
        title = params.get("title", filename)
        initial_comment = params.get("initial_comment", "")

        # Use files.upload v2 API
        import aiohttp
        form = aiohttp.FormData()
        form.add_field("channels", ",".join(channels))
        form.add_field("file", content, filename=filename)
        form.add_field("title", title)
        if initial_comment:
            form.add_field("initial_comment", initial_comment)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/files.upload",
                headers={"Authorization": f"Bearer {self._bot_token}"},
                data=form,
            ) as resp:
                result = await resp.json()

        if result.get("ok"):
            return ToolInvocationResult(success=True, output=result.get("file", {}), provider_id=self.provider_id, tool_id="slack_upload_file")
        return ToolInvocationResult(success=False, error=result.get("error", "Unknown error"), provider_id=self.provider_id, tool_id="slack_upload_file")

    async def _health_check_impl(self) -> ProviderHealth:
        try:
            result = await self._request("GET", "/auth.test")
            if result.get("ok"):
                return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.HEALTHY)
            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.UNHEALTHY, error_message=result.get("error", "Auth failed"))
        except Exception as e:
            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.UNHEALTHY, error_message=str(e))