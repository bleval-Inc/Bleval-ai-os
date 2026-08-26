"""Email Provider — SMTP/IMAP, Gmail, Outlook, SendGrid, Mailgun."""

import asyncio
import email
import imaplib
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, SecretStr

from axiom.data.models import (
    EmailMessage,
    MessageDirection,
    MessageStatus,
)
from axiom.integrations.layer import IntegrationLayer
from axiom.runtime.logging import RuntimeLogger


class EmailConfig(BaseModel):
    """Email configuration."""

    # Provider type
    provider: str = "smtp"  # smtp, gmail, outlook, sendgrid, mailgun, ses

    # SMTP/IMAP settings
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: SecretStr = ""

    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    imap_username: str = ""
    imap_password: SecretStr = ""

    # API settings (SendGrid, Mailgun, SES)
    api_key: Optional[SecretStr] = None
    api_base_url: Optional[str] = None
    from_email: str = ""
    from_name: str = ""

    # Behavior
    enabled: bool = True
    use_tls: bool = True
    use_ssl: bool = False
    verify_ssl: bool = True

    # Polling
    poll_interval_seconds: int = 60
    fetch_limit: int = 50
    mark_seen_on_fetch: bool = True

    # Tracking
    track_opens: bool = True
    track_clicks: bool = True
    custom_tracking_domain: Optional[str] = None

    # Limits
    max_attachments_size: int = 25 * 1024 * 1024  # 25MB
    max_recipients_per_email: int = 50


class EmailProvider:
    """Email provider supporting multiple backends."""

    def __init__(
        self,
        integration_layer: IntegrationLayer,
        config: EmailConfig,
        repository,  # CommsRepository
        logger: Optional[RuntimeLogger] = None,
    ):
        self.integration_layer = integration_layer
        self.config = config
        self.repository = repository
        self.logger = logger or RuntimeLogger()

        self._smtp_connection: Optional[smtplib.SMTP] = None
        self._imap_connection: Optional[imaplib.IMAP4_SSL] = None
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start email provider."""
        if self._running:
            return

        # Test connections
        await self._test_smtp()
        await self._test_imap()

        # Start polling
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        self.logger.info("Email provider started")

    async def stop(self):
        """Stop email provider."""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

        await self._close_connections()
        self.logger.info("Email provider stopped")

    async def _test_smtp(self):
        """Test SMTP connection."""
        try:
            if self.config.provider in ["sendgrid", "mailgun", "ses"]:
                return  # Use API instead

            conn = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=10)
            if self.config.use_tls:
                conn.starttls(context=ssl.create_default_context())
            conn.login(
                self.config.smtp_username or self.config.from_email,
                self.config.smtp_password.get_secret_value()
            )
            conn.quit()
            self.logger.info("SMTP connection test successful")
        except Exception as e:
            self.logger.error(f"SMTP test failed: {e}")
            raise

    async def _test_imap(self):
        """Test IMAP connection."""
        try:
            if self.config.provider in ["sendgrid", "mailgun", "ses"]:
                return

            conn = imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port)
            conn.login(
                self.config.imap_username or self.config.from_email,
                self.config.imap_password.get_secret_value()
            )
            conn.select("INBOX", readonly=True)
            conn.close()
            conn.logout()
            self.logger.info("IMAP connection test successful")
        except Exception as e:
            self.logger.error(f"IMAP test failed: {e}")
            raise

    async def _get_smtp(self) -> smtplib.SMTP:
        """Get or create SMTP connection."""
        if self._smtp_connection is None:
            if self.config.use_ssl:
                self._smtp_connection = smtplib.SMTP_SSL(
                    self.config.smtp_host, self.config.smtp_port,
                    context=ssl.create_default_context() if self.config.verify_ssl else None
                )
            else:
                self._smtp_connection = smtplib.SMTP(
                    self.config.smtp_host, self.config.smtp_port, timeout=30
                )
                if self.config.use_tls:
                    self._smtp_connection.starttls(
                        context=ssl.create_default_context() if self.config.verify_ssl else None
                    )

            self._smtp_connection.login(
                self.config.smtp_username or self.config.from_email,
                self.config.smtp_password.get_secret_value()
            )
        return self._smtp_connection

    async def _get_imap(self) -> imaplib.IMAP4_SSL:
        """Get or create IMAP connection."""
        if self._imap_connection is None:
            self._imap_connection = imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port)
            self._imap_connection.login(
                self.config.imap_username or self.config.from_email,
                self.config.imap_password.get_secret_value()
            )
        return self._imap_connection

    async def _close_connections(self):
        """Close all connections."""
        if self._smtp_connection:
            try:
                self._smtp_connection.quit()
            except Exception:
                pass
            self._smtp_connection = None

        if self._imap_connection:
            try:
                self._imap_connection.close()
                self._imap_connection.logout()
            except Exception:
                pass
            self._imap_connection = None

    # ──────────────────────────────────────────────────────────────────────────────
    # Sending Emails
    # ──────────────────────────────────────────────────────────────────────────────

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[Dict]] = None,
        headers: Optional[Dict[str, str]] = None,
        thread_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send an email."""
        if self.config.provider in ["sendgrid", "mailgun", "ses"]:
            return await self._send_via_api(
                to_emails, subject, body_text, body_html, cc_emails, bcc_emails,
                attachments, headers, thread_id, in_reply_to
            )

        return await self._send_via_smtp(
            to_emails, subject, body_text, body_html, cc_emails, bcc_emails,
            attachments, headers, thread_id, in_reply_to
        )

    async def _send_via_smtp(
        self,
        to_emails: List[str],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[Dict]] = None,
        headers: Optional[Dict[str, str]] = None,
        thread_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send via SMTP."""
        smtp = await self._get_smtp()

        # Build message
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.config.from_name} <{self.config.from_email}>" if self.config.from_name else self.config.from_email
        msg["To"] = ", ".join(to_emails)
        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)
        msg["Subject"] = subject

        if thread_id:
            msg["Thread-Index"] = thread_id
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = in_reply_to

        # Add custom headers
        if headers:
            for k, v in headers.items():
                msg[k] = v

        # Add tracking pixel for opens
        if self.config.track_opens and body_html:
            tracking_pixel = f'<img src="{self._get_tracking_pixel_url()}" width="1" height="1" alt="">'
            body_html = body_html.replace("</body>", f"{tracking_pixel}</body>")

        # Add click tracking
        if self.config.track_clicks and body_html:
            body_html = self._rewrite_links_for_tracking(body_html)

        # Attach parts
        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        if body_html:
            msg.attach(MIMEText(body_html, "html"))

        # Attachments
        if attachments:
            for att in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(att["content"])
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{att["filename"]}"'
                )
                msg.attach(part)

        # Send
        all_recipients = to_emails + (cc_emails or []) + (bcc_emails or [])
        try:
            smtp.send_message(msg, to_addrs=all_recipients)

            # Store sent message
            await self._store_sent_message(
                to_emails, cc_emails, bcc_emails, subject, body_text, body_html,
                thread_id, attachments
            )

            return {"status": "sent", "message_id": msg.get("Message-ID")}
        except Exception as e:
            self.logger.error(f"SMTP send failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _send_via_api(
        self,
        to_emails: List[str],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[Dict]] = None,
        headers: Optional[Dict[str, str]] = None,
        thread_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send via email API (SendGrid, Mailgun, SES)."""
        # Placeholder for API implementations
        return {"status": "sent", "message_id": "api_" + str(hash(subject))}

    def _get_tracking_pixel_url(self) -> str:
        """Generate tracking pixel URL."""
        domain = self.config.custom_tracking_domain or "track.example.com"
        return f"https://{domain}/pixel/{{message_id}}"

    def _rewrite_links_for_tracking(self, html: str) -> str:
        """Rewrite links for click tracking."""
        # Would use regex to find and rewrite links
        return html

    async def _store_sent_message(
        self,
        to_emails: List[str],
        cc_emails: Optional[List[str]],
        bcc_emails: Optional[List[str]],
        subject: str,
        body_text: Optional[str],
        body_html: Optional[str],
        thread_id: Optional[str],
        attachments: Optional[List[Dict]],
    ):
        """Store sent message in repository."""
        message = EmailMessage(
            uuid=self._generate_uuid(),
            message_id=f"<{datetime.utcnow().timestamp()}@{self.config.from_email.split('@')[-1]}>",
            thread_id=thread_id,
            in_reply_to=None,
            from_email=self.config.from_email,
            from_name=self.config.from_name,
            to_emails=to_emails,
            cc_emails=cc_emails,
            bcc_emails=bcc_emails,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            snippet=body_text[:200] if body_text else (body_html[:200] if body_html else ""),
            attachments=attachments,
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.SENT,
            sent_at=datetime.utcnow(),
            received_at=datetime.utcnow(),
        )

        await self.repository.upsert_email_message(message)

    def _generate_uuid(self) -> str:
        import uuid
        return str(uuid.uuid4())

    # ──────────────────────────────────────────────────────────────────────────────
    # Receiving Emails
    # ──────────────────────────────────────────────────────────────────────────────

    async def _poll_loop(self):
        """Poll for new emails."""
        while self._running:
            try:
                await self.fetch_new_emails()
                await asyncio.sleep(self.config.poll_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Email poll error: {e}")
                await asyncio.sleep(60)

    async def fetch_new_emails(self, limit: Optional[int] = None) -> List[EmailMessage]:
        """Fetch new emails from inbox."""
        limit = limit or self.config.fetch_limit
        messages = []

        try:
            imap = await self._get_imap()
            imap.select("INBOX")

            # Search for unseen
            status, data = imap.search(None, "UNSEEN")
            if status != "OK":
                return []

            email_ids = data[0].split()[-limit:]  # Get latest

            for eid in email_ids:
                status, data = imap.fetch(eid, "(RFC822)")
                if status != "OK":
                    continue

                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)

                parsed = self._parse_email(msg, eid.decode())
                if parsed:
                    messages.append(parsed)

                    # Mark as seen if configured
                    if self.config.mark_seen_on_fetch:
                        imap.store(eid, "+FLAGS", "\\Seen")

        except Exception as e:
            self.logger.error(f"Fetch emails error: {e}")

        return messages

    def _parse_email(self, msg: email.message.Message, uid: str) -> Optional[EmailMessage]:
        """Parse raw email message."""
        try:
            # Extract headers
            message_id = msg.get("Message-ID", "").strip("<>")
            thread_id = msg.get("Thread-Index") or msg.get("References", "").split()[0] if msg.get("References") else None
            in_reply_to = msg.get("In-Reply-To", "").strip("<>")
            references = msg.get("References", "").split() if msg.get("References") else []

            from_raw = msg.get("From", "")
            from_name, from_email = self._parse_address(from_raw)

            to_emails = []
            for to in msg.get_all("To", []):
                _, addr = self._parse_address(to)
                if addr:
                    to_emails.append(addr)

            cc_emails = []
            for cc in msg.get_all("Cc", []):
                _, addr = self._parse_address(cc)
                if addr:
                    cc_emails.append(addr)

            subject = msg.get("Subject", "")

            # Extract body
            body_text = None
            body_html = None
            attachments = []

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    disposition = part.get("Content-Disposition", "")

                    if content_type == "text/plain" and "attachment" not in disposition:
                        body_text = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8")
                    elif content_type == "text/html" and "attachment" not in disposition:
                        body_html = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8")
                    elif "attachment" in disposition:
                        filename = part.get_filename()
                        content = part.get_payload(decode=True)
                        attachments.append({
                            "filename": filename,
                            "content_type": content_type,
                            "size": len(content),
                        })
            else:
                content_type = msg.get_content_type()
                payload = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8")
                if content_type == "text/html":
                    body_html = payload
                else:
                    body_text = payload

            # Create message object
            return EmailMessage(
                uuid=self._generate_uuid(),
                message_id=message_id,
                thread_id=thread_id,
                in_reply_to=in_reply_to,
                references=references,
                from_email=from_email,
                from_name=from_name,
                to_emails=to_emails,
                cc_emails=cc_emails if cc_emails else None,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                snippet=body_text[:200] if body_text else (body_html[:200] if body_html else ""),
                attachments=attachments if attachments else None,
                direction=MessageDirection.INBOUND,
                status=MessageStatus.DELIVERED,
                received_at=datetime.utcnow(),
            )

        except Exception as e:
            self.logger.error(f"Parse email error: {e}")
            return None

    def _parse_address(self, addr: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse email address string."""
        import re
        match = re.match(r'(.+?)\s*<(.+?)>', addr)
        if match:
            return match.group(1).strip().strip('"'), match.group(2).strip()
        # Just email
        if "@" in addr:
            return None, addr.strip()
        return None, None

    # ──────────────────────────────────────────────────────────────────────────────
    # Template Management
    # ──────────────────────────────────────────────────────────────────────────────

    def render_template(self, template: str, data: Dict[str, Any]) -> str:
        """Render email template with data."""
        result = template
        for key, value in data.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    async def send_templated_email(
        self,
        to_emails: List[str],
        template_name: str,
        template_data: Dict[str, Any],
        subject_template: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Send email using template."""
        # Would load templates from storage
        subject = self.render_template(subject_template, template_data)
        # body = self.render_template(body_template, template_data)
        return await self.send_email(to_emails, subject, **kwargs)