"""
RAKSHAK - Twilio SMS Client
Handles Twilio SMS dispatch for alert notifications.
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

try:
    from twilio.rest import Client
except Exception:  # pragma: no cover - optional dependency until installed
    Client = None


class TwilioSMSClient:
    """Simple Twilio SMS wrapper for alert dispatch."""

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER", "")
        self.messaging_service_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID", "")
        self.client = None

        if Client and self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)

    def is_configured(self) -> bool:
        """Return True when Twilio credentials and sender config exist."""
        return bool(
            self.client and (self.from_number or self.messaging_service_sid)
        )

    def _normalize_to_e164(self, phone_number: str) -> str:
        """Normalize numbers for Twilio. Defaults 10-digit numbers to India (+91)."""
        digits = "".join(ch for ch in phone_number if ch.isdigit())
        if phone_number.strip().startswith("+"):
            return phone_number.strip()
        if len(digits) == 10:
            return f"+91{digits}"
        if len(digits) > 10:
            return f"+{digits}"
        return phone_number.strip()

    def send_sms(self, to_number: str, body: str) -> str:
        """Send a single SMS and return the Twilio message SID."""
        if not self.is_configured():
            raise RuntimeError("Twilio SMS is not configured.")

        payload = {
            "to": self._normalize_to_e164(to_number),
            "body": body,
        }
        if self.messaging_service_sid:
            payload["messaging_service_sid"] = self.messaging_service_sid
        else:
            payload["from_"] = self.from_number

        message = self.client.messages.create(**payload)
        return message.sid

    def send_bulk_sms(self, recipients: List[str], body: str) -> List[dict]:
        """Send SMS to multiple recipients and return per-recipient results."""
        results = []
        for recipient in recipients:
            try:
                sid = self.send_sms(recipient, body)
                results.append({"to": recipient, "status": "sent", "sid": sid})
            except Exception as exc:
                results.append({"to": recipient, "status": "failed", "error": str(exc)})
        return results


twilio_sms = TwilioSMSClient()
