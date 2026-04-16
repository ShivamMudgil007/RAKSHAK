"""
RAKSHAK - SMTP Email Client
Handles email dispatch for alert notifications.
"""

import os
import smtplib
from email.message import EmailMessage
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()


class SMTPEmailClient:
    """Simple SMTP wrapper for alert email dispatch."""

    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "").strip()
        self.port = int(os.getenv("SMTP_PORT", "587").strip() or "587")
        self.username = os.getenv("SMTP_USERNAME", "").strip()
        self.password = os.getenv("SMTP_PASSWORD", "").strip()
        self.from_email = os.getenv("SMTP_FROM_EMAIL", self.username).strip()
        self.from_name = os.getenv("SMTP_FROM_NAME", "RAKSHAK").strip()
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"}
        self.use_ssl = os.getenv("SMTP_USE_SSL", "false").strip().lower() in {"1", "true", "yes", "on"}

    def is_configured(self) -> bool:
        """Return True when SMTP credentials and sender config exist."""
        return bool(self.host and self.port and self.from_email)

    def sender_identity(self, from_email: Optional[str] = None, from_name: Optional[str] = None) -> str:
        """Return the effective sender identity for email headers."""
        effective_from_email = (from_email or self.from_email).strip()
        effective_from_name = (from_name or self.from_name).strip()
        if effective_from_name:
            return f"{effective_from_name} <{effective_from_email}>"
        return effective_from_email

    def _build_message(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.sender_identity(from_email=from_email, from_name=from_name)
        message["To"] = to_email.strip()
        message.set_content(body)
        return message

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> str:
        """Send a single email and return the recipient on success."""
        if not self.is_configured():
            raise RuntimeError("SMTP email is not configured.")

        message = self._build_message(
            to_email,
            subject,
            body,
            from_email=from_email,
            from_name=from_name,
        )

        if self.use_ssl:
            with smtplib.SMTP_SSL(self.host, self.port, timeout=30) as server:
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(message)
        else:
            with smtplib.SMTP(self.host, self.port, timeout=30) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(message)

        return to_email.strip()

    def send_bulk_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> List[dict]:
        """Send email to multiple recipients and return per-recipient results."""
        results = []
        for recipient in recipients:
            try:
                delivered_to = self.send_email(
                    recipient,
                    subject,
                    body,
                    from_email=from_email,
                    from_name=from_name,
                )
                results.append({"to": delivered_to, "status": "sent"})
            except Exception as exc:
                results.append({"to": recipient, "status": "failed", "error": str(exc)})
        return results


email_client = SMTPEmailClient()
