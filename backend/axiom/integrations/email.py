"""Email Provider — IMAP/SMTP and Gmail API for email operations."""

import asyncio
import email
import imaplib
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional

from axiom.engine.provider import Provider
from axiom.models.providers import (
    ProviderModel,
    ProviderToolDefinition,
    ProviderHealth,
    ProviderStatus,
    ToolInvocationResult,
    RateLimitConfig,
)
from axiom.runtime.logging import RuntimeLogger


class EmailProvider(Provider):
    """Email provider supporting IMAP/SMTP and Gmail API.

    Capabilities:
    - Read emails (inbox, sent, folders, search)
    - Send emails (with attachments, HTML, templates)
    - Organize emails (labels, folders, archive, delete)
    - Email sequences/campaigns
    - Track responses and opens
    """

    def __init__(
        self,
        config: ProviderModel,
        logger: Optional[RuntimeLogger] = None,
    ) -> None:
        super().__init__(config, logger)
        self._imap_conn: Optional[imaplib.IMAP4_SSL] = None
        self._smtp_conn: Optional[smtplib.SMTP] = None
        self._use_gmail_api = config.config.get("use_gmail_api", False)
        self._gmail_service = None

    def get_tool_definitions(self) -> List[ProviderToolDefinition]:
        return [
            ProviderToolDefinition(
                tool_id="email_read_inbox",
                name="Read Inbox",
                description="Read emails from inbox or folder",
                capability="email_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "folder": {"type": "string", "default": "INBOX"},
                        "limit": {"type": "integer", "default": 20},
                        "unread_only": {"type": "boolean", "default": True},
                        "since_days": {"type": "integer"},
                        "search_query": {"type": "string"},
                    },
                },
            ),
            ProviderToolDefinition(
                tool_id="email_send",
                name="Send Email",
                description="Send an email with optional attachments",
                capability="email_send",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "array", "items": {"type": "string"}},
                        "cc": {"type": "array", "items": {"type": "string"}},
                        "bcc": {"type": "array", "items": {"type": "string"}},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                        "html_body": {"type": "string"},
                        "attachments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "filename": {"type": "string"},
                                    "content_base64": {"type": "string"},
                                    "content_type": {"type": "string"},
                                },
                                "required": ["filename", "content_base64"],
                            },
                        },
                    },
                    "required": ["to", "subject", "body"],
                },
                risk_level="low",
            ),
            ProviderToolDefinition(
                tool_id="email_send_template",
                name="Send Email from Template",
                description="Send email using a predefined template with variables",
                capability="email_send",
                input_schema={
                    "type": "object",
                    "properties": {
                        "template_id": {"type": "string"},
                        "to": {"type": "array", "items": {"type": "string"}},
                        "variables": {"type": "object"},
                    },
                    "required": ["template_id", "to"],
                },
            ),
            ProviderToolDefinition(
                tool_id="email_search",
                name="Search Emails",
                description="Search emails with IMAP search criteria",
                capability="email_search",
                input_schema={
                    "type": "object",
                    "properties": {
                        "folder": {"type": "string", "default": "INBOX"},
                        "from_addr": {"type": "string"},
                        "to_addr": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                        "since_days": {"type": "integer"},
                        "before_days": {"type": "integer"},
                        "has_attachment": {"type": "boolean"},
                        "limit": {"type": "integer", "default": 50},
                    },
                },
            ),
            ProviderToolDefinition(
                tool_id="email_organize",
                name="Organize Email",
                description="Move, label, archive, or delete emails",
                capability="email_organize",
                input_schema={
                    "type": "object",
                    "properties": {
                        "message_ids": {"type": "array", "items": {"type": "string"}},
                        "action": {"type": "string", "enum": ["move", "label", "archive", "delete", "mark_read", "mark_unread", "flag", "unflag"]},
                        "target_folder": {"type": "string"},
                        "labels": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["message_ids", "action"],
                },
            ),
            ProviderToolDefinition(
                tool_id="email_get_thread",
                name="Get Email Thread",
                description="Get full conversation thread",
                capability="email_read",
                input_schema={
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string"},
                    },
                    "required": ["message_id"],
                },
            ),
            ProviderToolDefinition(
                tool_id="email_create_draft",
                name="Create Draft",
                description="Create an email draft",
                capability="email_draft",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "array", "items": {"type": "string"}},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                        "html_body": {"type": "string"},
                    },
                    "required": ["to", "subject", "body"],
                },
            ),
            ProviderToolDefinition(
                tool_id="email_list_folders",
                name="List Folders",
                description="List all mail folders/labels",
                capability="email_read",
                input_schema={},
            ),
        ]

    async def initialize(self) -> None:
        """Initialize IMAP/SMTP connections."""
        await self._connect_imap()
        await self._connect_smtp()
        self._initialized = True

    async def _connect_imap(self) -> None:
        """Connect to IMAP server."""
        host = self.config.config.get("imap_host", "imap.gmail.com")
        port = self.config.config.get("imap_port", 993)
        username = self._secrets.get_secret(self.config.auth.username_env_var or "EMAIL_USERNAME")
        password = self._secrets.get_secret(self.config.auth.password_env_var or "EMAIL_PASSWORD")

        if not username or not password:
            raise RuntimeError("Email credentials not configured")

        self._imap_conn = imaplib.IMAP4_SSL(host, port)
        await asyncio.get_event_loop().run_in_executor(
            None, self._imap_conn.login, username, password
        )

    async def _connect_smtp(self) -> None:
        """Connect to SMTP server."""
        host = self.config.config.get("smtp_host", "smtp.gmail.com")
        port = self.config.config.get("smtp_port", 587)
        username = self._secrets.get_secret(self.config.auth.username_env_var or "EMAIL_USERNAME")
        password = self._secrets.get_secret(self.config.auth.password_env_var or "EMAIL_PASSWORD")

        self._smtp_conn = smtplib.SMTP(host, port)
        await asyncio.get_event_loop().run_in_executor(
            None, self._smtp_conn.starttls, ssl.create_default_context()
        )
        await asyncio.get_event_loop().run_in_executor(
            None, self._smtp_conn.login, username, password
        )

    async def shutdown(self) -> None:
        """Close connections."""
        if self._imap_conn:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._imap_conn.logout
                )
            except Exception:
                pass
        if self._smtp_conn:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._smtp_conn.quit
                )
            except Exception:
                pass

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

    # ── Tool Implementations ──────────────────────────────────────────────

    async def _execute_email_read_inbox(self, params: Dict[str, Any]) -> ToolInvocationResult:
        folder = params.get("folder", "INBOX")
        limit = params.get("limit", 20)
        unread_only = params.get("unread_only", True)
        since_days = params.get("since_days")

        await asyncio.get_event_loop().run_in_executor(None, self._imap_conn.select, folder)

        # Build search criteria
        criteria = ["UNSEEN"] if unread_only else ["ALL"]
        if since_days:
            from datetime import timedelta
            since_date = (datetime.now() - timedelta(days=since_days)).strftime("%d-%b-%Y")
            criteria.append(f'SINCE "{since_date}"')

        criteria_str = " ".join(criteria)
        status, messages = await asyncio.get_event_loop().run_in_executor(
            None, self._imap_conn.search, None, criteria_str
        )

        if status != "OK":
            return ToolInvocationResult(
                success=False,
                error="Search failed",
                provider_id=self.provider_id,
                tool_id="email_read_inbox",
            )

        email_ids = messages[0].split()[-limit:]  # Get latest
        emails = []

        for eid in reversed(email_ids):  # Most recent first
            status, msg_data = await asyncio.get_event_loop().run_in_executor(
                None, self._imap_conn.fetch, eid, "(RFC822)"
            )
            if status == "OK":
                raw = msg_data[0][1]
                parsed = email.message_from_bytes(raw)
                emails.append(self._parse_email(parsed, eid.decode()))

        return ToolInvocationResult(
            success=True,
            output=emails,
            provider_id=self.provider_id,
            tool_id="email_read_inbox",
        )

    def _parse_email(self, msg: email.message.Message, msg_id: str) -> Dict[str, Any]:
        """Parse email message to dict."""
        return {
            "id": msg_id,
            "subject": msg.get("Subject", ""),
            "from": msg.get("From", ""),
            "to": msg.get("To", ""),
            "cc": msg.get("Cc", ""),
            "date": msg.get("Date", ""),
            "body": self._get_body(msg),
            "attachments": self._get_attachments(msg),
        }

    def _get_body(self, msg: email.message.Message) -> str:
        """Extract text body from email."""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode(errors="ignore")
        else:
            return msg.get_payload(decode=True).decode(errors="ignore")
        return ""

    def _get_attachments(self, msg: email.message.Message) -> List[Dict[str, Any]]:
        """Extract attachments from email."""
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            "filename": filename,
                            "content_type": part.get_content_type(),
                            "size": len(part.get_payload(decode=True) or b""),
                        })
        return attachments

    async def _execute_email_send(self, params: Dict[str, Any]) -> ToolInvocationResult:
        msg = MIMEMultipart("alternative")
        msg["From"] = self._secrets.get_secret(self.config.auth.username_env_var or "EMAIL_USERNAME")
        msg["To"] = ", ".join(params["to"])
        if params.get("cc"):
            msg["Cc"] = ", ".join(params["cc"])
        if params.get("bcc"):
            msg["Bcc"] = ", ".join(params["bcc"])
        msg["Subject"] = params["subject"]

        # Attach body
        text_part = MIMEText(params["body"], "plain")
        msg.attach(text_part)

        if params.get("html_body"):
            html_part = MIMEText(params["html_body"], "html")
            msg.attach(html_part)

        # Attachments
        for att in params.get("attachments", []):
            import base64
            from email.mime.base import MIMEBase
            from email import encoders

            part = MIMEBase("application", "octet-stream")
            part.set_payload(base64.b64decode(att["content_base64"]))
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{att["filename"]}"',
            )
            msg.attach(part)

        # Send
        all_recipients = params["to"] + params.get("cc", []) + params.get("bcc", [])
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._smtp_conn.send_message(msg, to_addrs=all_recipients)
        )

        return ToolInvocationResult(
            success=True,
            output={"message": "Email sent", "recipients": all_recipients},
            provider_id=self.provider_id,
            tool_id="email_send",
        )

    async def _execute_email_search(self, params: Dict[str, Any]) -> ToolInvocationResult:
        folder = params.get("folder", "INBOX")
        limit = params.get("limit", 50)

        await asyncio.get_event_loop().run_in_executor(None, self._imap_conn.select, folder)

        # Build IMAP search criteria
        criteria_parts = []
        if params.get("from_addr"):
            criteria_parts.append(f'FROM "{params["from_addr"]}"')
        if params.get("to_addr"):
            criteria_parts.append(f'TO "{params["to_addr"]}"')
        if params.get("subject"):
            criteria_parts.append(f'SUBJECT "{params["subject"]}"')
        if params.get("body"):
            criteria_parts.append(f'BODY "{params["body"]}"')
        if params.get("since_days"):
            from datetime import timedelta
            since = (datetime.now() - timedelta(days=params["since_days"])).strftime("%d-%b-%Y")
            criteria_parts.append(f'SINCE "{since}"')
        if params.get("before_days"):
            from datetime import timedelta
            before = (datetime.now() - timedelta(days=params["before_days"])).strftime("%d-%b-%Y")
            criteria_parts.append(f'BEFORE "{before}"')
        if params.get("has_attachment"):
            criteria_parts.append("HAS attachment")

        criteria = " ".join(criteria_parts) if criteria_parts else "ALL"
        status, messages = await asyncio.get_event_loop().run_in_executor(
            None, self._imap_conn.search, None, criteria
        )

        if status != "OK":
            return ToolInvocationResult(
                success=False,
                error="Search failed",
                provider_id=self.provider_id,
                tool_id="email_search",
            )

        email_ids = messages[0].split()[-limit:]
        emails = []

        for eid in reversed(email_ids):
            status, msg_data = await asyncio.get_event_loop().run_in_executor(
                None, self._imap_conn.fetch, eid, "(RFC822)"
            )
            if status == "OK":
                raw = msg_data[0][1]
                parsed = email.message_from_bytes(raw)
                emails.append(self._parse_email(parsed, eid.decode()))

        return ToolInvocationResult(
            success=True,
            output=emails,
            provider_id=self.provider_id,
            tool_id="email_search",
        )

    async def _execute_email_organize(self, params: Dict[str, Any]) -> ToolInvocationResult:
        action = params["action"]
        message_ids = params["message_ids"]

        for msg_id in message_ids:
            if action in ["move", "archive"]:
                target = params.get("target_folder", "Archive" if action == "archive" else "INBOX")
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._imap_conn.copy(msg_id, target)
                )
                if action == "move" or action == "archive":
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        self._imap_conn.store, msg_id, "+FLAGS", "(\\Deleted)"
                    )
            elif action == "delete":
                await asyncio.get_event_loop().run_in_executor(
                    None, self._imap_conn.store, msg_id, "+FLAGS", "(\\Deleted)"
                )
            elif action in ["mark_read", "mark_unread"]:
                flag = "\\Seen" if action == "mark_read" else "\\Unseen"
                op = "+" if action == "mark_read" else "-"
                await asyncio.get_event_loop().run_in_executor(
                    None, self._imap_conn.store, msg_id, f"{op}FLAGS", f"({flag})"
                )
            elif action in ["flag", "unflag"]:
                op = "+" if action == "flag" else "-"
                await asyncio.get_event_loop().run_in_executor(
                    None, self._imap_conn.store, msg_id, f"{op}FLAGS", "(\\Flagged)"
                )

        # Expunge deleted
        if action in ["move", "archive", "delete"]:
            await asyncio.get_event_loop().run_in_executor(None, self._imap_conn.expunge)

        return ToolInvocationResult(
            success=True,
            output={"message": f"Organized {len(message_ids)} emails"},
            provider_id=self.provider_id,
            tool_id="email_organize",
        )

    async def _execute_email_get_thread(self, params: Dict[str, Any]) -> ToolInvocationResult:
        # For IMAP, we search by References/In-Reply-To headers
        # This is a simplified implementation
        msg_id = params["message_id"]
        await asyncio.get_event_loop().run_in_executor(None, self._imap_conn.select, "INBOX")

        status, msg_data = await asyncio.get_event_loop().run_in_executor(
            None, self._imap_conn.fetch, msg_id.encode(), "(BODY[HEADER.FIELDS (MESSAGE-ID REFERENCES IN-REPLY-TO SUBJECT)])"
        )

        if status != "OK":
            return ToolInvocationResult(
                success=False,
                error="Failed to get thread",
                provider_id=self.provider_id,
                tool_id="email_get_thread",
            )

        return ToolInvocationResult(
            success=True,
            output={"message": "Thread retrieval requires Gmail API for full support"},
            provider_id=self.provider_id,
            tool_id="email_get_thread",
        )

    async def _execute_email_create_draft(self, params: Dict[str, Any]) -> ToolInvocationResult:
        # Drafts folder special handling
        await asyncio.get_event_loop().run_in_executor(None, self._imap_conn.select, "[Gmail]/Drafts")

        # Create message
        msg = MIMEMultipart("alternative")
        msg["From"] = self._secrets.get_secret(self.config.auth.username_env_var or "EMAIL_USERNAME")
        msg["To"] = ", ".join(params["to"])
        msg["Subject"] = params["subject"]

        text_part = MIMEText(params["body"], "plain")
        msg.attach(text_part)

        if params.get("html_body"):
            html_part = MIMEText(params["html_body"], "html")
            msg.attach(html_part)

        # Append to Drafts
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._imap_conn.append("[Gmail]/Drafts", "", imaplib.Time2Internaldate(datetime.now()), msg.as_bytes())
        )

        return ToolInvocationResult(
            success=True,
            output={"message": "Draft created"},
            provider_id=self.provider_id,
            tool_id="email_create_draft",
        )

    async def _execute_email_list_folders(self, params: Dict[str, Any]) -> ToolInvocationResult:
        status, folders = await asyncio.get_event_loop().run_in_executor(
            None, self._imap_conn.list
        )

        if status != "OK":
            return ToolInvocationResult(
                success=False,
                error="Failed to list folders",
                provider_id=self.provider_id,
                tool_id="email_list_folders",
            )

        folder_list = []
        for f in folders:
            folder_list.append(f.decode())

        return ToolInvocationResult(
            success=True,
            output=folder_list,
            provider_id=self.provider_id,
            tool_id="email_list_folders",
        )

    async def _health_check_impl(self) -> ProviderHealth:
        try:
            # Test IMAP connection
            await asyncio.get_event_loop().run_in_executor(None, self._imap_conn.noop)
            return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.HEALTHY)
        except Exception as e:
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.UNHEALTHY,
                error_message=str(e),
            )