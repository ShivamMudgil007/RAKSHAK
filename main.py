"""
RAKSHAK - FastAPI Backend
REST API server hosting the RAKSHAK intelligence pipeline
"""

import os
import sys
import json
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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
    channels: List[str] = ["sms", "email"]
    recipients: List[str] = ["9310373304"]


class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "en-IN"
    target_lang: str = "hi-IN"


class TTSRequest(BaseModel):
    text: str
    language: str = "hi-IN"
    speaker: str = "meera"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "system": "RAKSHAK",
        "fullName": "Realtime Alert, Knowledge, Surveillance, Hazard, Awareness & Kommunication",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "endpoints": ["/query", "/alerts", "/weather", "/seismic", "/translate", "/tts", "/health"],
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


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
    background_tasks.add_task(
        _dispatch_alert, req.region, req.message, req.severity, req.channels, req.recipients
    )
    return {
        "status": "dispatched",
        "region": req.region,
        "severity": req.severity,
        "channels": req.channels,
        "recipients": req.recipients,
        "message": "Alert queued for delivery",
    }


def _dispatch_alert(
    region: str,
    message: str,
    severity: str,
    channels: List[str],
    recipients: List[str],
):
    """Background task to dispatch alerts."""
    print(f"[ALERT DISPATCH] Region: {region} | Severity: {severity}")
    print(f"[ALERT DISPATCH] Message: {message}")
    print(f"[ALERT DISPATCH] Channels: {channels}")
    print(f"[ALERT DISPATCH] Recipients: {recipients}")

    alert_text = f"[RAKSHAK {severity}] {region}: {message}"

    if "sms" in channels:
        from utils.twilio_client import twilio_sms

        if not recipients:
            print("[TWILIO SMS] No recipients provided. Skipping SMS dispatch.")
        elif not twilio_sms.is_configured():
            print("[TWILIO SMS] Twilio is not configured. Check environment variables and dependency.")
        else:
            results = twilio_sms.send_bulk_sms(recipients, alert_text)
            for result in results:
                if result["status"] == "sent":
                    print(f"[TWILIO SMS SENT] To={result['to']} | SID={result['sid']}")
                else:
                    print(f"[TWILIO SMS FAILED] To={result['to']} | Error={result['error']}")


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("FASTAPI_HOST", "0.0.0.0"),
        port=int(os.getenv("FASTAPI_PORT", 8000)),
        reload=True,
    )
