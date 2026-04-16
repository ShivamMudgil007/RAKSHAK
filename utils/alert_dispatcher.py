"""
RAKSHAK - Automatic Alert Dispatcher
Dispatches RED alerts via SMS/Email with simple cooldown protection.
"""

import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List

from dotenv import load_dotenv

from utils.email_client import email_client
from utils.twilio_client import twilio_sms

load_dotenv()

_LAST_SENT_AT: Dict[str, datetime] = {}
DEFAULT_RED_ALERT_RECIPIENTS = [
    "7982616036",
    "9310373304",
    "9891772509",
    "8867110748",
]
DEFAULT_RED_ALERT_EMAIL_RECIPIENTS = []


def _auto_sms_enabled() -> bool:
    """Check whether automatic RED-alert SMS is enabled."""
    return os.getenv("AUTO_SMS_ON_RED", "true").strip().lower() in {"1", "true", "yes", "on"}


def _auto_sms_recipients() -> List[str]:
    """Return configured RED-alert recipients from env or shared defaults."""
    raw = os.getenv("TWILIO_ALERT_RECIPIENTS", "")
    recipients = [item.strip() for item in raw.split(",") if item.strip()]
    return recipients or DEFAULT_RED_ALERT_RECIPIENTS


def _auto_email_enabled() -> bool:
    """Check whether automatic RED-alert email is enabled."""
    return os.getenv("AUTO_EMAIL_ON_RED", "true").strip().lower() in {"1", "true", "yes", "on"}


def _auto_email_recipients() -> List[str]:
    """Return configured RED-alert email recipients."""
    raw = os.getenv("ALERT_EMAIL_RECIPIENTS", "")
    recipients = [item.strip() for item in raw.split(",") if item.strip()]
    return recipients or DEFAULT_RED_ALERT_EMAIL_RECIPIENTS


def _cooldown_minutes() -> int:
    """Return cooldown window for duplicate RED alerts."""
    raw = os.getenv("RED_ALERT_COOLDOWN_MINUTES", "30").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 30


def _fingerprint_alert(alert: dict, region: str) -> str:
    """Create a stable alert fingerprint for cooldown checks."""
    key = "|".join([
        region or "",
        str(alert.get("type", "")),
        str(alert.get("severity", "")),
        str(alert.get("title", "")),
        str(alert.get("message", "")),
    ])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def dispatch_red_alerts(result: dict, region: str) -> List[dict]:
    """
    Automatically dispatch RED alerts through configured channels.
    Returns per-alert delivery status for observability.
    """
    alerts = result.get("alerts", []) or []
    red_alerts = [alert for alert in alerts if str(alert.get("severity", "")).upper() == "RED"]

    if not red_alerts:
        return []

    sms_enabled = _auto_sms_enabled()
    email_enabled = _auto_email_enabled()

    sms_recipients = _auto_sms_recipients() if sms_enabled else []
    email_recipients = _auto_email_recipients() if email_enabled else []

    if not sms_enabled and not email_enabled:
        return [{"status": "skipped", "reason": "all_auto_dispatch_disabled"}]
    if not sms_recipients and not email_recipients:
        return [{"status": "skipped", "reason": "no_recipients_configured"}]
    sms_ready = sms_enabled and bool(sms_recipients) and twilio_sms.is_configured()
    email_ready = email_enabled and bool(email_recipients) and email_client.is_configured()
    if not sms_ready and not email_ready:
        return [{"status": "skipped", "reason": "no_dispatch_channel_configured"}]

    statuses: List[dict] = []
    cooldown = timedelta(minutes=_cooldown_minutes())
    now = datetime.utcnow()

    for alert in red_alerts:
        fingerprint = _fingerprint_alert(alert, region)
        last_sent = _LAST_SENT_AT.get(fingerprint)
        if last_sent and now - last_sent < cooldown:
            statuses.append({
                "status": "skipped",
                "reason": "cooldown_active",
                "title": alert.get("title", ""),
            })
            continue

        sms_body = (
            f"[RAKSHAK RED ALERT] {region}: {alert.get('title', 'Emergency Alert')} | "
            f"{alert.get('message', '')} | Action: {alert.get('action', '')}"
        )[:1500]
        email_subject = f"RAKSHAK RED Alert - {region}"
        email_body = (
            f"RAKSHAK RED ALERT\n\n"
            f"Region: {region}\n"
            f"Title: {alert.get('title', 'Emergency Alert')}\n"
            f"Severity: {alert.get('severity', 'RED')}\n"
            f"Type: {alert.get('type', '')}\n"
            f"Message: {alert.get('message', '')}\n"
            f"Action: {alert.get('action', '')}\n"
            f"Timestamp: {alert.get('timestamp', '')}\n"
        )

        channel_results: Dict[str, List[dict]] = {}
        channel_meta: Dict[str, str] = {}

        if sms_enabled:
            if not sms_recipients:
                channel_meta["sms"] = "no_recipients_configured"
            elif not twilio_sms.is_configured():
                channel_meta["sms"] = "twilio_not_configured"
            else:
                channel_results["sms"] = twilio_sms.send_bulk_sms(sms_recipients, sms_body)

        if email_enabled:
            if not email_recipients:
                channel_meta["email"] = "no_recipients_configured"
            elif not email_client.is_configured():
                channel_meta["email"] = "smtp_not_configured"
            else:
                channel_results["email"] = email_client.send_bulk_email(email_recipients, email_subject, email_body)

        dispatched_any = any(channel_results.values())
        if dispatched_any:
            _LAST_SENT_AT[fingerprint] = now

        statuses.append({
            "status": "dispatched" if dispatched_any else "skipped",
            "title": alert.get("title", ""),
            "results": channel_results,
            "channel_status": channel_meta,
        })

    return statuses
