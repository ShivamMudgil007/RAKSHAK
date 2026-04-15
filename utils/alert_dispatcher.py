"""
RAKSHAK - Automatic Alert Dispatcher
Dispatches RED alerts via Twilio with simple cooldown protection.
"""

import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List

from dotenv import load_dotenv

from utils.twilio_client import twilio_sms

load_dotenv()

_LAST_SENT_AT: Dict[str, datetime] = {}
DEFAULT_RED_ALERT_RECIPIENTS = [
    "7982616036",
    "9310373304",
    "9891772509",
    "8867110748",
]


def _auto_sms_enabled() -> bool:
    """Check whether automatic RED-alert SMS is enabled."""
    return os.getenv("AUTO_SMS_ON_RED", "true").strip().lower() in {"1", "true", "yes", "on"}


def _auto_sms_recipients() -> List[str]:
    """Return configured RED-alert recipients from env or shared defaults."""
    raw = os.getenv("TWILIO_ALERT_RECIPIENTS", "")
    recipients = [item.strip() for item in raw.split(",") if item.strip()]
    return recipients or DEFAULT_RED_ALERT_RECIPIENTS


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
    Automatically dispatch RED alerts through Twilio.
    Returns per-alert delivery status for observability.
    """
    alerts = result.get("alerts", []) or []
    red_alerts = [alert for alert in alerts if str(alert.get("severity", "")).upper() == "RED"]

    if not red_alerts:
        return []
    if not _auto_sms_enabled():
        return [{"status": "skipped", "reason": "auto_sms_disabled"}]

    recipients = _auto_sms_recipients()
    if not recipients:
        return [{"status": "skipped", "reason": "no_recipients_configured"}]
    if not twilio_sms.is_configured():
        return [{"status": "skipped", "reason": "twilio_not_configured"}]

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

        body = (
            f"[RAKSHAK RED ALERT] {region}: {alert.get('title', 'Emergency Alert')} | "
            f"{alert.get('message', '')} | Action: {alert.get('action', '')}"
        )[:1500]
        results = twilio_sms.send_bulk_sms(recipients, body)
        _LAST_SENT_AT[fingerprint] = now
        statuses.append({
            "status": "dispatched",
            "title": alert.get("title", ""),
            "results": results,
        })

    return statuses
