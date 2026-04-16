"""
RAKSHAK - FastAPI Backend
REST API server hosting the RAKSHAK intelligence pipeline
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from agents.workflow import run_rakshak_pipeline
from utils.sarvam_client import sarvam_client
from utils.alert_dispatcher import dispatch_red_alerts

# ── App Setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="RAKSHAK API",
    description="Realtime Alert, Knowledge, Surveillance, Hazard, Awareness & Kommunication System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request/Response Models ───────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    region: str = "India"
    language: str = "en-IN"
    disaster_type: str = "all"


class AlertRequest(BaseModel):
    region: str
    message: str
    severity: str = "HIGH"
    channels: List[str] = Field(default_factory=lambda: ["sms", "email"])
    recipients: List[str] = Field(default_factory=list)
    email_recipients: List[str] = Field(default_factory=list)
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    send_in_background: bool = False


class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "en-IN"
    target_lang: str = "hi-IN"


class TTSRequest(BaseModel):
    text: str
    language: str = "hi-IN"
    speaker: str = "meera"


def _normalize_recipients(values: List[str]) -> List[str]:
    """Strip empty recipient entries while preserving order."""
    seen = set()
    normalized = []
    for value in values:
        item = value.strip()
        if not item or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


def _normalize_channels(values: List[str]) -> List[str]:
    """Normalize user-selected delivery channels."""
    allowed = {"sms", "email"}
    normalized = []
    for value in values:
        channel = value.strip().lower()
        if channel in allowed and channel not in normalized:
            normalized.append(channel)
    return normalized


def _delivery_summary(channel_results: Dict[str, List[dict]]) -> Dict[str, dict]:
    """Summarize per-channel delivery attempts."""
    summary: Dict[str, dict] = {}
    for channel, results in channel_results.items():
        sent = sum(1 for item in results if item.get("status") == "sent")
        failed = sum(1 for item in results if item.get("status") == "failed")
        summary[channel] = {
            "attempted": len(results),
            "sent": sent,
            "failed": failed,
        }
    return summary


def alert_channel_configuration() -> Dict[str, dict]:
    """Expose non-secret alert configuration state for the UI and API."""
    from utils.email_client import email_client
    from utils.twilio_client import twilio_sms

    return {
        "sms": {
            "configured": twilio_sms.is_configured(),
            "has_from_number": bool(twilio_sms.from_number),
            "has_messaging_service_sid": bool(twilio_sms.messaging_service_sid),
        },
        "email": {
            "configured": email_client.is_configured(),
            "host": email_client.host,
            "port": email_client.port,
            "use_tls": email_client.use_tls,
            "use_ssl": email_client.use_ssl,
            "default_sender": email_client.sender_identity(),
        },
    }


def dispatch_alert_delivery(
    region: str,
    message: str,
    severity: str,
    channels: List[str],
    recipients: List[str],
    email_recipients: List[str],
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
) -> Dict[str, object]:
    """Dispatch an alert immediately and return structured delivery results."""
    from utils.email_client import email_client
    from utils.twilio_client import twilio_sms

    normalized_channels = _normalize_channels(channels)
    sms_recipients = _normalize_recipients(recipients)
    explicit_email_recipients = _normalize_recipients(email_recipients)
    derived_email_recipients = _normalize_recipients(
        [recipient for recipient in sms_recipients if "@" in recipient]
    )
    final_email_recipients = explicit_email_recipients or derived_email_recipients

    if not normalized_channels:
        raise ValueError("Select at least one delivery channel: sms or email.")

    alert_text = f"[RAKSHAK {severity}] {region}: {message}"
    email_subject = f"RAKSHAK {severity} Alert - {region}"
    email_body = (
        f"RAKSHAK Emergency Alert\n\n"
        f"Region: {region}\n"
        f"Severity: {severity}\n"
        f"Message: {message}\n"
        f"Timestamp: {datetime.now().isoformat()}\n"
    )

    channel_results: Dict[str, List[dict]] = {}
    channel_status: Dict[str, str] = {}

    if "sms" in normalized_channels:
        if not sms_recipients:
            channel_status["sms"] = "no_recipients_provided"
        elif not twilio_sms.is_configured():
            channel_status["sms"] = "twilio_not_configured"
        else:
            channel_results["sms"] = twilio_sms.send_bulk_sms(sms_recipients, alert_text)
            channel_status["sms"] = "dispatched"

    if "email" in normalized_channels:
        if not final_email_recipients:
            channel_status["email"] = "no_recipients_provided"
        elif not email_client.is_configured():
            channel_status["email"] = "smtp_not_configured"
        else:
            channel_results["email"] = email_client.send_bulk_email(
                final_email_recipients,
                email_subject,
                email_body,
                from_email=from_email,
                from_name=from_name,
            )
            channel_status["email"] = "dispatched"

    any_sent = any(
        result.get("status") == "sent"
        for results in channel_results.values()
        for result in results
    )

    return {
        "status": "sent" if any_sent else "skipped",
        "region": region,
        "severity": severity,
        "channels": normalized_channels,
        "message": message,
        "recipients": {
            "sms": sms_recipients,
            "email": final_email_recipients,
        },
        "channel_status": channel_status,
        "results": channel_results,
        "summary": _delivery_summary(channel_results),
        "sender": {
            "from_email": from_email,
            "from_name": from_name,
        },
        "timestamp": datetime.now().isoformat(),
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "system": "RAKSHAK",
        "fullName": "Realtime Alert, Knowledge, Surveillance, Hazard, Awareness & Kommunication",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "endpoints": ["/query", "/alerts", "/weather", "/seismic", "/translate", "/tts", "/health", "/alert-config", "/send-alert"],
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/alert-config")
def get_alert_config():
    """Expose whether SMS and email channels are ready without returning secrets."""
    return {
        "status": "success",
        "channels": alert_channel_configuration(),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/query")
def query_rakshak(req: QueryRequest):
    """
    Main intelligence endpoint.
    Runs the full LangGraph agentic pipeline and returns analysis.
    """
    try:
        result = run_rakshak_pipeline(
            query=req.query,
            region=req.region,
            language=req.language,
            disaster_type=req.disaster_type,
        )
        auto_sms_status = dispatch_red_alerts(result, req.region)
        return {
            "status": "success",
            "query": req.query,
            "region": req.region,
            "analysis": result.get("final_response", ""),
            "alerts": result.get("alerts", []),
            "recommendations": result.get("recommendations", []),
            "weather_data": result.get("weather_data", {}),
            "seismic_data": result.get("seismic_data", {}),
            "retrieved_docs": [
                {
                    "title": d["title"],
                    "category": d["category"],
                    "region": d["region"],
                    "source_url": d.get("source_url", ""),
                    "source_label": d.get("source_label", ""),
                    "source_note": d.get("source_note", ""),
                }
                for d in result.get("retrieved_docs", [])
            ],
            "agent_trace": result.get("messages", []),
            "auto_dispatch_status": auto_sms_status,
            "auto_sms_status": auto_sms_status,
            "timestamp": result.get("timestamp", datetime.now().isoformat()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/weather/{region}")
def get_weather(region: str):
    """Get weather/IMD data for a region."""
    from agents.workflow import get_weather_data
    data = get_weather_data(region)
    return {"region": region, "weather": data, "timestamp": datetime.now().isoformat()}


@app.get("/seismic/{region}")
def get_seismic(region: str):
    """Get seismic data for a region."""
    from agents.workflow import get_seismic_data
    data = get_seismic_data(region)
    return {"region": region, "seismic": data, "timestamp": datetime.now().isoformat()}


@app.get("/alerts")
def get_all_alerts():
    """Get current active alerts across India."""
    regions = ["Kerala", "Assam", "Gujarat", "Delhi", "Odisha"]
    all_alerts = []
    for region in regions:
        result = run_rakshak_pipeline(
            query=f"current disaster situation {region}",
            region=region,
        )
        all_alerts.extend(result.get("alerts", []))
    return {"alerts": all_alerts, "total": len(all_alerts), "timestamp": datetime.now().isoformat()}


@app.post("/translate")
def translate_text(req: TranslateRequest):
    """Translate text using Sarvam Translation API."""
    translated = sarvam_client.translate(req.text, req.source_lang, req.target_lang)
    return {
        "original": req.text,
        "translated": translated,
        "source_lang": req.source_lang,
        "target_lang": req.target_lang,
    }


@app.post("/tts")
def text_to_speech(req: TTSRequest):
    """Convert text to speech using Sarvam TTS API."""
    audio_bytes = sarvam_client.text_to_speech(req.text, req.language, req.speaker)
    if audio_bytes:
        import base64
        return {
            "status": "success",
            "audio_base64": base64.b64encode(audio_bytes).decode(),
            "language": req.language,
        }
    return {"status": "unavailable", "message": "TTS service temporarily unavailable"}


@app.post("/send-alert")
async def send_alert(req: AlertRequest, background_tasks: BackgroundTasks):
    """Send emergency alerts via SMS/Email."""
    try:
        if req.send_in_background:
            background_tasks.add_task(
                _dispatch_alert,
                req.region,
                req.message,
                req.severity,
                req.channels,
                req.recipients,
                req.email_recipients,
                req.from_email,
                req.from_name,
            )
            return {
                "status": "queued",
                "region": req.region,
                "severity": req.severity,
                "channels": _normalize_channels(req.channels),
                "recipients": {
                    "sms": _normalize_recipients(req.recipients),
                    "email": _normalize_recipients(req.email_recipients),
                },
                "sender": {
                    "from_email": req.from_email,
                    "from_name": req.from_name,
                },
                "config": alert_channel_configuration(),
                "message": "Alert queued for background delivery",
                "timestamp": datetime.now().isoformat(),
            }

        return dispatch_alert_delivery(
            req.region,
            req.message,
            req.severity,
            req.channels,
            req.recipients,
            req.email_recipients,
            req.from_email,
            req.from_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _dispatch_alert(
    region: str,
    message: str,
    severity: str,
    channels: List[str],
    recipients: List[str],
    email_recipients: List[str],
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
):
    """Background task to dispatch alerts."""
    delivery = dispatch_alert_delivery(
        region,
        message,
        severity,
        channels,
        recipients,
        email_recipients,
        from_email,
        from_name,
    )

    print(f"[ALERT DISPATCH] Region: {region} | Severity: {severity}")
    print(f"[ALERT DISPATCH] Channels: {delivery['channels']}")
    print(f"[ALERT DISPATCH] Summary: {delivery['summary']}")

    for channel, status in delivery["channel_status"].items():
        print(f"[ALERT DISPATCH] {channel.upper()} status={status}")

    for channel, results in delivery["results"].items():
        for result in results:
            if result["status"] == "sent":
                print(f"[{channel.upper()} SENT] To={result['to']}")
            else:
                print(f"[{channel.upper()} FAILED] To={result['to']} | Error={result['error']}")


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("FASTAPI_HOST", "0.0.0.0"),
        port=int(os.getenv("FASTAPI_PORT", 8000)),
        reload=True,
    )
