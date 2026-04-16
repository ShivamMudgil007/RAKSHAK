"""
RAKSHAK - Streamlit UI
Realtime Alert, Knowledge, Surveillance, Hazard, Awareness & Kommunication
"""

import os
import sys
import json
import time
import re
from html import escape
import requests
from datetime import datetime
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Add project root
sys.path.insert(0, os.path.dirname(__file__))

# ── Page Config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="RAKSHAK — Disaster Intelligence System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&family=Exo+2:wght@300;400;600;800&display=swap');

/* ── Root & Background ── */
:root {
    --crimson: #c0392b;
    --orange: #e67e22;
    --yellow: #f39c12;
    --green: #27ae60;
    --blue: #2980b9;
    --dark: #0a0f1e;
    --darker: #060b14;
    --panel: #0d1526;
    --border: #1e3a5f;
    --text: #cdd9e5;
    --accent: #3498db;
    --glow: rgba(52, 152, 219, 0.3);
}

html, body, .stApp {
    background: var(--darker) !important;
    color: var(--text) !important;
    font-family: 'Exo 2', sans-serif !important;
}

/* ── Hide Streamlit Defaults ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1rem 2rem 2rem !important; max-width: 1400px !important; }

/* ── Header Banner ── */
.rakshak-header {
    background: linear-gradient(135deg, #0a0f1e 0%, #0d1f3c 50%, #0a1628 100%);
    border: 1px solid var(--border);
    border-bottom: 3px solid var(--crimson);
    border-radius: 8px 8px 0 0;
    padding: 1.5rem 2rem;
    margin-bottom: 0;
    position: relative;
    overflow: hidden;
}

.rakshak-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        90deg,
        transparent,
        transparent 50px,
        rgba(52, 152, 219, 0.03) 50px,
        rgba(52, 152, 219, 0.03) 51px
    );
}

.header-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 3rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: 6px;
    text-transform: uppercase;
    text-shadow: 0 0 30px rgba(192, 57, 43, 0.8), 0 0 60px rgba(192, 57, 43, 0.4);
    margin: 0;
    line-height: 1;
}

.header-subtitle {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: var(--accent);
    letter-spacing: 3px;
    margin-top: 0.4rem;
    opacity: 0.9;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(39, 174, 96, 0.15);
    border: 1px solid rgba(39, 174, 96, 0.4);
    color: #2ecc71;
    padding: 4px 12px;
    border-radius: 20px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 1px;
}

.pulse-dot {
    width: 8px; height: 8px;
    background: #2ecc71;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(1.3); }
}

/* ── Alert Cards ── */
.alert-card {
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    border-left: 4px solid;
    font-family: 'Exo 2', sans-serif;
    position: relative;
}

.alert-red { background: rgba(192,57,43,0.12); border-color: #c0392b; }
.alert-orange { background: rgba(230,126,34,0.12); border-color: #e67e22; }
.alert-yellow { background: rgba(243,156,18,0.12); border-color: #f39c12; }
.alert-green { background: rgba(39,174,96,0.12); border-color: #27ae60; }
.alert-blue { background: rgba(52,152,219,0.12); border-color: #3498db; }

.alert-title {
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}

.alert-meta {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    opacity: 0.7;
    margin-top: 0.4rem;
}

/* ── Metric Panels ── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin: 1rem 0;
}

.metric-panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.metric-panel::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
}

.metric-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: #fff;
    line-height: 1;
}

.metric-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: var(--text);
    letter-spacing: 2px;
    margin-top: 0.4rem;
    opacity: 0.7;
}

/* ── Panel Containers ── */
.data-panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.2rem;
    margin: 0.5rem 0;
}

.panel-header {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Chat Interface ── */
.chat-message {
    padding: 0.8rem 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    font-size: 0.9rem;
    line-height: 1.6;
}

.chat-user {
    background: rgba(52,152,219,0.1);
    border: 1px solid rgba(52,152,219,0.3);
    border-radius: 8px 8px 2px 8px;
    margin-left: 20%;
    text-align: right;
}

.chat-assistant {
    background: rgba(13,21,38,0.8);
    border: 1px solid var(--border);
    border-radius: 2px 8px 8px 8px;
    margin-right: 10%;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--panel) !important;
    border-right: 1px solid var(--border) !important;
}

section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] p {
    color: var(--text) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 1px !important;
}

/* ── Streamlit Widget Overrides ── */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: #0a1220 !important;
    border: 1px solid var(--border) !important;
    color: #fff !important;
    font-family: 'Exo 2', sans-serif !important;
    border-radius: 4px !important;
}

.stButton button {
    background: linear-gradient(135deg, #c0392b, #922b21) !important;
    color: #fff !important;
    border: none !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    padding: 0.6rem 2rem !important;
    border-radius: 4px !important;
    transition: all 0.2s !important;
}

.stButton button:hover {
    background: linear-gradient(135deg, #e74c3c, #c0392b) !important;
    box-shadow: 0 0 20px rgba(192, 57, 43, 0.5) !important;
    transform: translateY(-1px) !important;
}

/* Agent Trace */
.agent-trace {
    background: #060b14;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.8rem;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    color: #2ecc71;
    max-height: 150px;
    overflow-y: auto;
    line-height: 1.8;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    font-size: 0.8rem !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
}

.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ──────────────────────────────────────────────────────────

def get_alert_color(severity: str) -> str:
    mapping = {"RED": "red", "ORANGE": "orange", "YELLOW": "yellow",
                "HIGH": "red", "MEDIUM": "orange", "LOW": "green", "INFO": "blue"}
    return mapping.get(severity.upper(), "blue")


def severity_emoji(severity: str) -> str:
    mapping = {"RED": "🔴", "ORANGE": "🟠", "YELLOW": "🟡",
                "HIGH": "🔴", "VERY HIGH": "🚨", "MEDIUM": "🟠", "LOW": "🟢", "INFO": "🔵"}
    return mapping.get(severity.upper(), "⚪")


def render_source_references(retrieved_docs: list) -> str:
    """Render unique source references for the analysis panel."""
    if not retrieved_docs:
        return ""

    seen = set()
    items = []
    for doc in retrieved_docs:
        label = escape(str(doc.get("source_label") or doc.get("title") or "Source"))
        url = str(doc.get("source_url") or "").strip()
        note = escape(str(doc.get("source_note") or "").strip())
        key = url or note or label
        if not key or key in seen:
            continue
        seen.add(key)

        if url:
            item = (
                f'<li style="margin-bottom:0.45rem;">'
                f'<a href="{escape(url)}" target="_blank" style="color:#58a6ff; text-decoration:none;">{label}</a>'
            )
            if note:
                item += f'<span style="color:#7f8c8d;"> ({note})</span>'
            item += "</li>"
        else:
            item = f'<li style="margin-bottom:0.45rem; color:#cdd9e5;">{label}'
            if note:
                item += f'<span style="color:#7f8c8d;"> ({note})</span>'
            item += "</li>"

        items.append(item)

    if not items:
        return ""

    return f"""
    <div class="data-panel" style="margin-top:0.8rem;">
        <div style="font-family:'Rajdhani',sans-serif; letter-spacing:2px; color:#58a6ff; margin-bottom:0.5rem;">
            SOURCES
        </div>
        <ul style="margin:0; padding-left:1.2rem; line-height:1.7; font-size:0.85rem;">
            {''.join(items)}
        </ul>
    </div>
    """


def detect_audio_mime(audio_bytes: bytes) -> str:
    """Best-effort MIME detection for generated audio."""
    if audio_bytes.startswith(b"RIFF"):
        return "audio/wav"
    if audio_bytes.startswith(b"ID3") or audio_bytes[:2] == b"\xff\xfb":
        return "audio/mpeg"
    if audio_bytes.startswith(b"OggS"):
        return "audio/ogg"
    if audio_bytes.startswith(b"fLaC"):
        return "audio/flac"
    return "audio/wav"


def build_user_message(text_query: str, transcript: str) -> str:
    """Format user-visible query text for chat history."""
    text_query = text_query.strip()
    transcript = transcript.strip()

    if text_query and transcript and text_query != transcript:
        return f"{text_query}\n\n[Audio transcript] {transcript}"
    if transcript:
        return f"[Audio] {transcript}"
    return text_query


def sanitize_text_for_tts(text: str, limit: int = 450) -> tuple[str, bool]:
    """Convert markdown-heavy assistant text into plain speech-friendly text."""
    cleaned = text.replace("\r", "\n")
    cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"__([^_]+)__", r"\1", cleaned)
    cleaned = re.sub(r"^[#>\-\*\u2022]+\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if len(cleaned) <= limit:
        return cleaned, False

    truncated = cleaned[:limit].rsplit(" ", 1)[0].strip()
    if truncated and truncated[-1] not in ".!?":
        truncated += "."
    return truncated, True


def generate_audio_reply(text: str, language: str) -> dict | None:
    """Generate audio for assistant output."""
    from utils.sarvam_client import sarvam_client

    tts_text, truncated = sanitize_text_for_tts(text)
    if not tts_text:
        return None

    audio_bytes = sarvam_client.text_to_speech(tts_text, language, "meera")
    if not audio_bytes:
        return None

    return {
        "bytes": audio_bytes,
        "format": detect_audio_mime(audio_bytes),
        "language": language,
        "preview_text": tts_text,
        "truncated": truncated,
        "error": sarvam_client.last_tts_error,
    }


SARVAM_LANGUAGE_OPTIONS = {
    "English": "en-IN",
    "Assamese": "as-IN",
    "Bengali": "bn-IN",
    "Bodo": "brx-IN",
    "Dogri": "doi-IN",
    "Gujarati": "gu-IN",
    "Hindi": "hi-IN",
    "Kannada": "kn-IN",
    "Kashmiri": "ks-IN",
    "Konkani": "kok-IN",
    "Maithili": "mai-IN",
    "Malayalam": "ml-IN",
    "Manipuri": "mni-IN",
    "Marathi": "mr-IN",
    "Nepali": "ne-IN",
    "Odia": "od-IN",
    "Punjabi": "pa-IN",
    "Sanskrit": "sa-IN",
    "Santali": "sat-IN",
    "Sindhi": "sd-IN",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
    "Urdu": "ur-IN",
}

TTS_SUPPORTED_LANGUAGES = {
    "en-IN",
    "bn-IN",
    "gu-IN",
    "hi-IN",
    "kn-IN",
    "ml-IN",
    "mr-IN",
    "od-IN",
    "pa-IN",
    "ta-IN",
    "te-IN",
}


def can_generate_audio(language: str) -> bool:
    """Return True when Sarvam TTS supports the selected language."""
    return language in TTS_SUPPORTED_LANGUAGES


def run_pipeline(query: str, region: str, language: str, disaster_type: str) -> dict:
    """Run the RAKSHAK pipeline (direct or via API)."""
    try:
        from agents.workflow import run_rakshak_pipeline
        from utils.alert_dispatcher import dispatch_red_alerts
        result = run_rakshak_pipeline(query, region, language, disaster_type)
        result["auto_sms_status"] = dispatch_red_alerts(result, region)
        return result
    except Exception as e:
        return {
            "final_response": f"Analysis running... ({str(e)[:50]})",
            "alerts": [{"type": "INFO", "severity": "LOW", "title": "System Starting",
                         "message": "RAKSHAK is initializing. Please try again.", "action": "Wait"}],
            "recommendations": ["System initializing", "Check API connectivity"],
            "weather_data": {},
            "seismic_data": {},
            "retrieved_docs": [],
            "messages": [],
            "auto_sms_status": [],
        }


def parse_recipient_input(raw_text: str) -> list[str]:
    """Parse comma or newline separated recipients."""
    values = []
    for chunk in raw_text.replace("\r", "\n").split("\n"):
        values.extend(item.strip() for item in chunk.split(","))
    return [item for item in values if item]


def get_alert_channel_status() -> dict:
    """Load non-secret alert channel readiness details."""
    from main import alert_channel_configuration

    return alert_channel_configuration()


def send_manual_alert(
    region: str,
    message: str,
    severity: str,
    channels: list[str],
    sms_recipients: list[str],
    email_recipients: list[str],
    from_email: str,
    from_name: str,
) -> dict:
    """Send a manual alert and return structured results."""
    from main import dispatch_alert_delivery

    return dispatch_alert_delivery(
        region=region,
        message=message,
        severity=severity,
        channels=channels,
        recipients=sms_recipients,
        email_recipients=email_recipients,
        from_email=from_email.strip() or None,
        from_name=from_name.strip() or None,
    )


# ── Session State Init ────────────────────────────────────────────────────────

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "selected_region" not in st.session_state:
    st.session_state.selected_region = "Kerala"
if "last_audio_response" not in st.session_state:
    st.session_state.last_audio_response = None
if "last_manual_alert" not in st.session_state:
    st.session_state.last_manual_alert = None


# ── Header ────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="rakshak-header">
    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
            <div class="header-title">🛡️ RAKSHAK</div>
            <div class="header-subtitle">
                REALTIME · ALERT · KNOWLEDGE · SURVEILLANCE · HAZARD · AWARENESS · KOMMUNICATION
            </div>
        </div>
        <div style="text-align:right;">
            <div class="status-badge">
                <div class="pulse-dot"></div>
                SYSTEM OPERATIONAL
            </div>
            <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem; color:#7f8c8d; margin-top:6px;">
                {datetime.now().strftime("%d %b %Y  |  %H:%M IST")}
            </div>
            <div style="font-family:'Share Tech Mono',monospace; font-size:0.6rem; color:#3498db; margin-top:2px;">
                Powered by Sarvam AI · LangGraph · RAG
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1rem 0; border-bottom:1px solid #1e3a5f; margin-bottom:1rem;">
        <div style="font-family:'Rajdhani',sans-serif; font-size:1.4rem; font-weight:700; color:#fff; letter-spacing:4px;">
            🛡️ RAKSHAK
        </div>
        <div style="font-family:'Share Tech Mono',monospace; font-size:0.6rem; color:#3498db; letter-spacing:2px;">
            CONTROL PANEL
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**REGION SELECTION**")
    region = st.selectbox(
        "Region",
        ["Kerala", "Assam", "Gujarat", "Delhi", "Odisha", "Maharashtra", "Uttarakhand", "Himachal Pradesh", "All India"],
        key="region_select",
        label_visibility="collapsed",
    )

    st.markdown("**DISASTER TYPE**")
    disaster_type = st.selectbox(
        "Type",
        ["All Hazards", "Flood", "Earthquake", "Cyclone", "Landslide"],
        label_visibility="collapsed",
    )

    st.markdown("**LANGUAGE**")
    language_label = st.selectbox("Language", list(SARVAM_LANGUAGE_OPTIONS.keys()), label_visibility="collapsed")
    language = SARVAM_LANGUAGE_OPTIONS[language_label]

    st.markdown("---")

    st.markdown("**QUICK ALERTS**")
    if st.button("🚨 Generate Alert Report", use_container_width=True):
        st.session_state.trigger_alert = True

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.session_state.last_result = None
        st.rerun()

    st.markdown("---")

    st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace; font-size:0.6rem; color:#7f8c8d; line-height:2;">
    NDMA HELPLINE: 1078<br>
    NDRF: 011-24363260<br>
    IMD: 1800-180-1717<br>
    EARTHQUAKE: 1092
    </div>
    """, unsafe_allow_html=True)


# ── Main Tabs ─────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📡  INTELLIGENCE HUB",
    "🗺️  RISK MAP",
    "💬  AI ASSISTANT",
    "📋  KNOWLEDGE BASE",
    "🚨  ALERT CENTER",
])


# ── TAB 1: Intelligence Hub ───────────────────────────────────────────────────

with tab1:
    col_left, col_right = st.columns([3, 2], gap="medium")

    with col_left:
        # Query Input
        st.markdown("""
        <div class="panel-header">🔍 SITUATION QUERY</div>
        """, unsafe_allow_html=True)

        query_input = st.text_area(
            "Query",
            placeholder=f"e.g., What is the current flood risk in {region}? Should we evacuate?",
            height=90,
            label_visibility="collapsed",
        )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            analyze_btn = st.button("⚡ ANALYZE SITUATION", use_container_width=True)
        with col_btn2:
            sample_queries = {
                "Kerala": "What is the current flood situation in Kerala? Which districts need immediate evacuation?",
                "Gujarat": "Assess earthquake preparedness in Kutch. Any recent seismic activity?",
                "Assam": "Brahmaputra water level status and flood risk assessment for Assam",
                "Delhi": "Seismic risk assessment for Delhi NCR. Are hospitals prepared?",
                "Odisha": "Cyclone risk assessment for Odisha coastline this season",
            }
            if st.button("🎲 SAMPLE QUERY", use_container_width=True):
                st.session_state["sample_q"] = sample_queries.get(region, sample_queries["Kerala"])
                st.rerun()

        if "sample_q" in st.session_state and st.session_state["sample_q"]:
            st.info(f"Sample: *{st.session_state['sample_q']}*")

        # Run pipeline
        if analyze_btn and (query_input or st.session_state.get("sample_q")):
            actual_query = query_input or st.session_state.get("sample_q", "")
            with st.spinner("⚡ RAKSHAK agents analyzing..."):
                result = run_pipeline(actual_query, region, language, disaster_type.lower())
                st.session_state.last_result = result
                st.session_state.chat_history.append({"role": "user", "content": actual_query})
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": result.get("final_response", "Analysis complete.")
                })

        # Display Results
        result = st.session_state.get("last_result")

        if result:
            # Active Alerts
            alerts = result.get("alerts", [])
            if alerts:
                st.markdown("""
                <div class="panel-header">🚨 ACTIVE ALERTS</div>
                """, unsafe_allow_html=True)
                for alert in alerts:
                    color = get_alert_color(alert.get("severity", "LOW"))
                    emoji = severity_emoji(alert.get("severity", "LOW"))
                    st.markdown(f"""
                    <div class="alert-card alert-{color}">
                        <div class="alert-title">{emoji} {alert.get('title', '')}</div>
                        <div style="margin:0.3rem 0;">{alert.get('message', '')}</div>
                        <div style="color:#3498db; font-size:0.85rem;">⚡ {alert.get('action', '')}</div>
                        <div class="alert-meta">⏱ {alert.get('timestamp', '')} | TYPE: {alert.get('type', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)

            auto_dispatch_status = result.get("auto_dispatch_status", result.get("auto_sms_status", []))
            if auto_dispatch_status:
                with st.expander("Alert Dispatch Status"):
                    for item in auto_dispatch_status:
                        st.write(item)

            # Analysis
            analysis = result.get("final_response", "")
            if analysis:
                source_refs_html = render_source_references(result.get("retrieved_docs", []))
                st.markdown("""
                <div class="panel-header">🧠 AI ANALYSIS</div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="data-panel" style="line-height:1.8; font-size:0.9rem;">
                {analysis.replace(chr(10), '<br>')}
                </div>
                {source_refs_html}
                """, unsafe_allow_html=True)

            # Agent Trace
            messages = result.get("messages", [])
            if messages:
                with st.expander("🔬 Agent Execution Trace"):
                    trace_html = "<br>".join([f"$ {m}" for m in messages])
                    st.markdown(f'<div class="agent-trace">{trace_html}</div>', unsafe_allow_html=True)

        else:
            st.markdown("""
            <div class="data-panel" style="text-align:center; padding:3rem; color:#7f8c8d;">
                <div style="font-size:3rem;">🛡️</div>
                <div style="font-family:'Rajdhani',sans-serif; font-size:1.2rem; letter-spacing:3px; margin-top:1rem;">
                    RAKSHAK READY
                </div>
                <div style="font-size:0.8rem; margin-top:0.5rem;">
                    Enter a query or select a sample to begin intelligence analysis
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        # Weather Panel
        st.markdown("""<div class="panel-header">🌩️ WEATHER STATUS</div>""", unsafe_allow_html=True)

        from agents.workflow import get_weather_data, get_seismic_data
        weather = get_weather_data(region)
        seismic = get_seismic_data(region)

        alert_colors = {"RED": "#c0392b", "ORANGE": "#e67e22", "YELLOW": "#f39c12", "GREEN": "#27ae60"}
        al_color = alert_colors.get(weather.get("alert_level", "GREEN"), "#27ae60")

        st.markdown(f"""
        <div class="data-panel">
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.8rem;">
                <div style="text-align:center; background:{al_color}22; border:1px solid {al_color}55; border-radius:6px; padding:0.8rem;">
                    <div style="font-family:'Rajdhani',sans-serif; font-size:1.8rem; font-weight:700; color:{al_color};">
                        {weather.get('alert_level','N/A')}
                    </div>
                    <div style="font-size:0.65rem; letter-spacing:2px; color:#aaa;">IMD ALERT</div>
                </div>
                <div style="text-align:center; background:#1e3a5f33; border:1px solid #1e3a5f; border-radius:6px; padding:0.8rem;">
                    <div style="font-family:'Rajdhani',sans-serif; font-size:1.8rem; font-weight:700; color:#3498db;">
                        {weather.get('rainfall_24h',0)}mm
                    </div>
                    <div style="font-size:0.65rem; letter-spacing:2px; color:#aaa;">24H RAINFALL</div>
                </div>
                <div style="text-align:center; background:#1e3a5f33; border:1px solid #1e3a5f; border-radius:6px; padding:0.8rem;">
                    <div style="font-family:'Rajdhani',sans-serif; font-size:1.8rem; font-weight:700; color:#9b59b6;">
                        {weather.get('wind_speed',0)}km/h
                    </div>
                    <div style="font-size:0.65rem; letter-spacing:2px; color:#aaa;">WIND SPEED</div>
                </div>
                <div style="text-align:center; background:#1e3a5f33; border:1px solid #1e3a5f; border-radius:6px; padding:0.8rem;">
                    <div style="font-family:'Rajdhani',sans-serif; font-size:1.8rem; font-weight:700; color:#1abc9c;">
                        {weather.get('humidity',0)}%
                    </div>
                    <div style="font-size:0.65rem; letter-spacing:2px; color:#aaa;">HUMIDITY</div>
                </div>
            </div>
            <div style="margin-top:0.8rem; padding:0.6rem; background:#060b14; border-radius:4px; font-family:'Share Tech Mono',monospace; font-size:0.72rem; color:#3498db;">
                📡 {weather.get('imd_warning','No active warnings')}
            </div>
            <div style="margin-top:0.5rem; font-size:0.82rem; color:#aaa; line-height:1.5;">
                {weather.get('forecast','')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Seismic Panel
        st.markdown("""<div class="panel-header">⚡ SEISMIC STATUS</div>""", unsafe_allow_html=True)
        risk_col = {"VERY HIGH": "#c0392b", "HIGH": "#e67e22", "MODERATE": "#f39c12", "LOW": "#27ae60"}.get(
            seismic.get("risk_level", "LOW"), "#27ae60")

        recent_eq = seismic.get("recent_events", [])
        eq_html = ""
        for eq in recent_eq:
            m = eq.get("magnitude", 0)
            m_color = "#c0392b" if m >= 4 else "#e67e22" if m >= 3 else "#f39c12"
            eq_html += f"""
            <div style="display:flex; align-items:center; gap:0.5rem; margin:0.3rem 0; 
                         background:#060b14; border-radius:4px; padding:0.4rem 0.6rem;">
                <span style="font-family:'Rajdhani',sans-serif; font-size:1.1rem; font-weight:700; color:{m_color};">M{m}</span>
                <span style="font-size:0.78rem; color:#aaa;">{eq.get('location','')} · {eq.get('depth',0)}km deep · {eq.get('time','')}</span>
            </div>"""

        st.markdown(f"""
        <div class="data-panel">
            <div style="display:flex; gap:1rem; margin-bottom:0.8rem;">
                <div style="flex:1; text-align:center; background:{risk_col}22; border:1px solid {risk_col}55; border-radius:6px; padding:0.7rem;">
                    <div style="font-family:'Rajdhani',sans-serif; font-size:1.5rem; font-weight:700; color:{risk_col};">
                        ZONE {seismic.get('seismic_zone','N/A')}
                    </div>
                    <div style="font-size:0.6rem; letter-spacing:2px; color:#aaa;">SEISMIC ZONE</div>
                </div>
                <div style="flex:1; text-align:center; background:{risk_col}22; border:1px solid {risk_col}55; border-radius:6px; padding:0.7rem;">
                    <div style="font-family:'Rajdhani',sans-serif; font-size:1rem; font-weight:700; color:{risk_col};">
                        {seismic.get('risk_level','N/A')}
                    </div>
                    <div style="font-size:0.6rem; letter-spacing:2px; color:#aaa;">RISK LEVEL</div>
                </div>
            </div>
            {'<div style="font-size:0.78rem; color:#aaa; margin-bottom:0.5rem;">RECENT SEISMIC EVENTS</div>' + eq_html if eq_html else
             '<div style="color:#27ae60; font-size:0.8rem; padding:0.5rem; text-align:center;">✓ No significant recent seismic activity</div>'}
            <div style="margin-top:0.5rem; font-size:0.75rem; color:#7f8c8d; font-family:\'Share Tech Mono\',monospace;">
                🔬 {seismic.get('tectonic_activity','N/A')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Recommendations
        if result and result.get("recommendations"):
            st.markdown("""<div class="panel-header">📋 RECOMMENDED ACTIONS</div>""", unsafe_allow_html=True)
            recs_html = ""
            for i, rec in enumerate(result["recommendations"][:5], 1):
                recs_html += f"""
                <div style="display:flex; align-items:flex-start; gap:0.5rem; margin:0.4rem 0; 
                             padding:0.5rem; background:#060b14; border-radius:4px;">
                    <span style="color:#c0392b; font-family:'Rajdhani',sans-serif; font-weight:700; min-width:20px;">{i}.</span>
                    <span style="font-size:0.85rem; line-height:1.4;">{rec}</span>
                </div>"""
            st.markdown(f'<div class="data-panel">{recs_html}</div>', unsafe_allow_html=True)


# ── TAB 2: Risk Map ───────────────────────────────────────────────────────────

with tab2:
    st.markdown("""<div class="panel-header">🗺️ INDIA DISASTER RISK MAP</div>""", unsafe_allow_html=True)

    # India state risk data
    risk_data = pd.DataFrame({
        "State": ["Kerala", "Assam", "Gujarat", "Delhi", "Odisha", "Maharashtra",
                  "Uttarakhand", "Himachal Pradesh", "Tamil Nadu", "Andhra Pradesh",
                  "West Bengal", "Bihar", "Uttar Pradesh", "Rajasthan", "Karnataka"],
        "Flood Risk": [9, 9, 5, 4, 8, 7, 7, 6, 7, 7, 8, 8, 7, 3, 5],
        "Earthquake Risk": [4, 7, 9, 8, 4, 5, 9, 9, 4, 5, 6, 6, 6, 5, 4],
        "Cyclone Risk": [5, 3, 6, 1, 9, 5, 1, 1, 8, 8, 7, 2, 1, 1, 4],
        "Overall Risk": [8, 8, 7, 7, 9, 7, 8, 7, 7, 7, 8, 7, 7, 4, 5],
    })

    col_m1, col_m2 = st.columns([2, 1])

    with col_m1:
        fig = go.Figure(data=go.Bar(
            x=risk_data["State"],
            y=risk_data["Overall Risk"],
            marker=dict(
                color=risk_data["Overall Risk"],
                colorscale=[[0, "#27ae60"], [0.5, "#e67e22"], [1, "#c0392b"]],
                showscale=True,
                colorbar=dict(title="Risk Level", tickfont=dict(color="#aaa")),
            ),
            text=risk_data["Overall Risk"],
            textposition="outside",
            textfont=dict(color="#fff", size=11),
        ))
        fig.update_layout(
            title=dict(text="Overall Disaster Risk by State", font=dict(color="#fff", size=14, family="Rajdhani")),
            paper_bgcolor="#0a0f1e",
            plot_bgcolor="#0d1526",
            xaxis=dict(tickangle=-45, tickfont=dict(color="#aaa", size=10), gridcolor="#1e3a5f"),
            yaxis=dict(range=[0, 11], tickfont=dict(color="#aaa"), gridcolor="#1e3a5f", title="Risk Score (1-10)"),
            height=350,
            margin=dict(l=0, r=0, t=40, b=80),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_m2:
        fig2 = go.Figure(data=go.Scatterpolar(
            r=[
                risk_data[risk_data["State"] == region]["Flood Risk"].values[0] if region in risk_data["State"].values else 5,
                risk_data[risk_data["State"] == region]["Earthquake Risk"].values[0] if region in risk_data["State"].values else 5,
                risk_data[risk_data["State"] == region]["Cyclone Risk"].values[0] if region in risk_data["State"].values else 5,
                risk_data[risk_data["State"] == region]["Overall Risk"].values[0] if region in risk_data["State"].values else 5,
                risk_data[risk_data["State"] == region]["Flood Risk"].values[0] if region in risk_data["State"].values else 5,
            ],
            theta=["Flood", "Earthquake", "Cyclone", "Overall", "Flood"],
            fill="toself",
            fillcolor="rgba(192,57,43,0.2)",
            line=dict(color="#c0392b", width=2),
            name=region,
        ))
        fig2.update_layout(
            title=dict(text=f"Risk Profile: {region}", font=dict(color="#fff", size=13, family="Rajdhani")),
            polar=dict(
                bgcolor="#0d1526",
                radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(color="#aaa", size=9), gridcolor="#1e3a5f"),
                angularaxis=dict(tickfont=dict(color="#fff", size=11), gridcolor="#1e3a5f"),
            ),
            paper_bgcolor="#0a0f1e",
            showlegend=False,
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Multi-hazard comparison
    fig3 = go.Figure()
    for hazard, color in [("Flood Risk", "#3498db"), ("Earthquake Risk", "#e67e22"), ("Cyclone Risk", "#9b59b6")]:
        fig3.add_trace(go.Scatter(
            x=risk_data["State"], y=risk_data[hazard],
            mode="lines+markers",
            name=hazard,
            line=dict(color=color, width=2),
            marker=dict(size=7),
        ))
    fig3.update_layout(
        title=dict(text="Multi-Hazard Risk Comparison", font=dict(color="#fff", size=14, family="Rajdhani")),
        paper_bgcolor="#0a0f1e",
        plot_bgcolor="#0d1526",
        xaxis=dict(tickangle=-45, tickfont=dict(color="#aaa", size=10), gridcolor="#1e3a5f"),
        yaxis=dict(tickfont=dict(color="#aaa"), gridcolor="#1e3a5f", range=[0, 11]),
        legend=dict(font=dict(color="#fff"), bgcolor="#0d1526", bordercolor="#1e3a5f"),
        height=280,
        margin=dict(l=0, r=0, t=40, b=80),
    )
    st.plotly_chart(fig3, use_container_width=True)


# ── TAB 3: AI Assistant ───────────────────────────────────────────────────────

with tab3:
    st.markdown("""<div class="panel-header">💬 RAKSHAK AI ASSISTANT</div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace; font-size:0.72rem; color:#7f8c8d; margin-bottom:1rem; padding:0.5rem; background:#060b14; border-radius:4px;">
    Multilingual conversational AI powered by Sarvam AI · Ask in English, Hindi, Tamil, or any Indian language
    </div>
    """, unsafe_allow_html=True)

    # Chat history display
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align:center; padding:2rem; color:#7f8c8d;">
                <div style="font-size:2rem;">🛡️</div>
                <div style="font-family:'Rajdhani',sans-serif; letter-spacing:3px; margin-top:0.5rem;">
                    RAKSHAK AI READY
                </div>
                <div style="font-size:0.8rem; margin-top:0.5rem;">
                    Ask about flood risk, earthquake preparedness, evacuation protocols, or any disaster management query
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message chat-user">
                        <div style="font-size:0.72rem; color:#3498db; margin-bottom:0.3rem; letter-spacing:1px;">YOU</div>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message chat-assistant">
                        <div style="font-size:0.72rem; color:#c0392b; margin-bottom:0.3rem; letter-spacing:1px;">🛡️ RAKSHAK</div>
                        {msg['content'].replace(chr(10), '<br>')}
                    </div>
                    """, unsafe_allow_html=True)

    # Chat input
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'Share Tech Mono',monospace; font-size:0.72rem; color:#7f8c8d; margin-bottom:0.75rem;">
        Submit a typed query, record audio with your microphone, upload audio, or use both. Responses come back as text, with an optional generated audio reply.
    </div>
    """, unsafe_allow_html=True)
    col_ci, col_cb = st.columns([5, 1])
    with col_ci:
        chat_input = st.text_input(
            "Chat",
            placeholder="Type your query in English, Hindi, or any Indian language...",
            label_visibility="collapsed",
            key="chat_input_field",
        )
    with col_cb:
        send_btn = st.button("SEND ▶", use_container_width=True)

    record_col, upload_col = st.columns(2)
    with record_col:
        recorded_query = st.audio_input(
            "Record Audio Query",
            help="Record a short audio query directly from your microphone.",
            key="audio_query_recording",
        )
        if recorded_query is not None:
            st.audio(recorded_query.getvalue(), format=recorded_query.type or "audio/wav")

    with upload_col:
        audio_query = st.file_uploader(
            "Upload Audio Query",
            type=["wav", "mp3", "ogg", "flac", "aac", "m4a", "webm"],
            help="Upload a short audio query for transcription.",
            key="audio_query_file",
        )
        if audio_query is not None:
            st.audio(audio_query.getvalue(), format=audio_query.type or "audio/wav")

    generate_audio_output = st.checkbox("Generate audio reply for the assistant response", value=False)
    if generate_audio_output and not can_generate_audio(language):
        st.caption("Audio reply is currently available for English, Bengali, Gujarati, Hindi, Kannada, Malayalam, Marathi, Odia, Punjabi, Tamil, and Telugu.")

    selected_audio_query = recorded_query or audio_query

    if send_btn and (chat_input.strip() or selected_audio_query is not None):
        from utils.sarvam_client import sarvam_client

        transcript = ""
        effective_query = chat_input.strip()

        if selected_audio_query is not None:
            with st.spinner("Transcribing audio query..."):
                transcription = sarvam_client.speech_to_text(
                    audio_bytes=selected_audio_query.getvalue(),
                    filename=getattr(selected_audio_query, "name", "recorded_query.wav"),
                    mime_type=getattr(selected_audio_query, "type", "application/octet-stream") or "application/octet-stream",
                )
                transcript = transcription.get("transcript", "").strip()

            if not effective_query:
                effective_query = transcript

        if effective_query:
            st.session_state.chat_history.append({
                "role": "user",
                "content": build_user_message(chat_input, transcript),
            })
            st.session_state.last_audio_response = None

            with st.spinner("RAKSHAK thinking..."):
                result = run_pipeline(effective_query, region, language, "all")
                response = result.get("final_response", "Analysis complete.")
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.session_state.last_result = result

            if generate_audio_output and can_generate_audio(language):
                from utils.sarvam_client import sarvam_client
                with st.spinner("Generating audio reply..."):
                    st.session_state.last_audio_response = generate_audio_reply(response, language)
                if not st.session_state.last_audio_response:
                    error_detail = sarvam_client.last_tts_error or "Unknown TTS error."
                    st.warning(f"Audio reply could not be generated right now. Details: {error_detail}")
            elif generate_audio_output:
                st.info("Text response was generated in the selected language. Audio reply is not available for that language yet.")

            st.rerun()
        else:
            st.warning("I could not extract text from that audio file. Try a shorter or clearer recording.")

    col_cc1, col_cc2, col_cc3 = st.columns(3)
    with col_cc1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.last_audio_response = None
            st.rerun()
    with col_cc2:
        if st.button("🌐 Translate Last Response", use_container_width=True):
            if st.session_state.chat_history:
                last_resp = [m for m in st.session_state.chat_history if m["role"] == "assistant"]
                if last_resp:
                    from utils.sarvam_client import sarvam_client
                    source_text = last_resp[-1]["content"][:500]
                    translated = sarvam_client.translate(source_text, "auto", language)
                    if translated.strip() == source_text.strip():
                        st.info(f"The last response may already be in {language_label}, or translation is unavailable right now.")
                    else:
                        st.info(f"**Translated ({language_label}):** {translated}")
    with col_cc3:
        if st.button("Audio Reply", use_container_width=True):
            last_resp = [m for m in st.session_state.chat_history if m["role"] == "assistant"]
            if last_resp:
                if can_generate_audio(language):
                    from utils.sarvam_client import sarvam_client
                    with st.spinner("Generating audio reply..."):
                        st.session_state.last_audio_response = generate_audio_reply(last_resp[-1]["content"], language)
                    if not st.session_state.last_audio_response:
                        error_detail = sarvam_client.last_tts_error or "Unknown TTS error."
                        st.warning(f"Audio reply could not be generated right now. Details: {error_detail}")
                else:
                    st.info("Audio reply is not available for the currently selected language yet.")
            else:
                st.info("No assistant response available yet.")

    if st.session_state.last_audio_response:
        st.markdown("""<div class="panel-header">AUDIO RESPONSE</div>""", unsafe_allow_html=True)
        if st.session_state.last_audio_response.get("truncated"):
            st.caption("Audio reply was generated from a shortened plain-text version of the assistant response for better TTS reliability.")
        st.audio(
            st.session_state.last_audio_response["bytes"],
            format=st.session_state.last_audio_response["format"],
        )
        st.download_button(
            "Download Audio Reply",
            data=st.session_state.last_audio_response["bytes"],
            file_name="rakshak_response.wav",
            mime=st.session_state.last_audio_response["format"],
            use_container_width=True,
        )

# ── TAB 4: Knowledge Base ─────────────────────────────────────────────────────

with tab4:
    st.markdown("""<div class="panel-header">📋 DISASTER KNOWLEDGE BASE</div>""", unsafe_allow_html=True)

    from rag.knowledge_base import rag_kb

    col_kb1, col_kb2 = st.columns([2, 1])

    with col_kb1:
        search_query = st.text_input(
            "Search KB",
            placeholder="Search knowledge base... (e.g., 'Kerala flood evacuation')",
            label_visibility="collapsed",
        )

        docs_to_show = rag_kb.retrieve(search_query, top_k=5) if search_query else rag_kb.documents[:5]

        for doc in docs_to_show:
            cat_colors = {"flood": "#3498db", "earthquake": "#e67e22",
                          "cyclone": "#9b59b6", "general": "#27ae60"}
            cat_color = cat_colors.get(doc.get("category", ""), "#7f8c8d")

            with st.expander(f"📄 {doc['title']}"):
                source_markup = ""
                if doc.get("source_url") or doc.get("source_note"):
                    link_markup = ""
                    if doc.get("source_url"):
                        link_label = escape(str(doc.get("source_label") or doc["source_url"]))
                        link_url = escape(str(doc["source_url"]))
                        link_markup = f"""
                        <a href="{link_url}" target="_blank" style="color:#58a6ff; text-decoration:none;">
                            {link_label}
                        </a>
                        """
                    note_markup = ""
                    if doc.get("source_note"):
                        note_markup = f"""
                        <div style="color:#7f8c8d; font-size:0.72rem; margin-top:0.2rem;">
                            {escape(str(doc['source_note']))}
                        </div>
                        """
                    source_markup = f"""
                    <div style="margin-top:0.75rem; font-size:0.78rem;">
                        <span style="color:#7f8c8d;">Source:</span>
                        {link_markup or '<span style="color:#cdd9e5;">Imported dataset</span>'}
                        {note_markup}
                    </div>
                    """
                st.markdown(f"""
                <div style="display:flex; gap:0.5rem; margin-bottom:0.5rem;">
                    <span style="background:{cat_color}33; color:{cat_color}; border:1px solid {cat_color}55;
                                 padding:2px 8px; border-radius:3px; font-size:0.7rem; letter-spacing:1px;">
                        {doc.get('category','').upper()}
                    </span>
                    <span style="background:#1e3a5f33; color:#3498db; border:1px solid #1e3a5f;
                                 padding:2px 8px; border-radius:3px; font-size:0.7rem; letter-spacing:1px;">
                        {doc.get('region','').upper()}
                    </span>
                </div>
                <div style="font-size:0.88rem; line-height:1.7; color:#cdd9e5;">
                    {doc.get('content','')}
                </div>
                {source_markup}
                """, unsafe_allow_html=True)

    with col_kb2:
        st.markdown("""<div class="panel-header">➕ ADD DOCUMENT</div>""", unsafe_allow_html=True)
        with st.form("add_doc"):
            doc_title = st.text_input("Title")
            doc_content = st.text_area("Content", height=100)
            doc_category = st.selectbox("Category", ["flood", "earthquake", "cyclone", "landslide", "general"])
            doc_region = st.text_input("Region")
            submitted = st.form_submit_button("ADD TO KB")
            if submitted and doc_title and doc_content:
                rag_kb.add_document(doc_title, doc_content, doc_category, doc_region)
                st.success(f"✅ Added: {doc_title}")

        st.markdown(f"""
        <div class="data-panel" style="margin-top:1rem;">
            <div class="panel-header">📊 KB STATS</div>
            <div style="font-family:'Share Tech Mono',monospace; font-size:0.75rem; line-height:2.2;">
                📄 Total Documents: <b style="color:#fff;">{len(rag_kb.documents)}</b><br>
                🌊 Flood: <b style="color:#3498db;">{sum(1 for d in rag_kb.documents if d['category']=='flood')}</b><br>
                ⚡ Earthquake: <b style="color:#e67e22;">{sum(1 for d in rag_kb.documents if d['category']=='earthquake')}</b><br>
                🌀 Cyclone: <b style="color:#9b59b6;">{sum(1 for d in rag_kb.documents if d['category']=='cyclone')}</b><br>
                📋 General: <b style="color:#27ae60;">{sum(1 for d in rag_kb.documents if d['category']=='general')}</b><br>
                🔍 Vector Search: <b style="color:{'#27ae60' if rag_kb.use_vectors else '#e67e22'};">
                    {'ENABLED' if rag_kb.use_vectors else 'KEYWORD MODE'}
                </b>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown("""
<div style="text-align:center; padding:1.5rem; border-top:1px solid #1e3a5f; margin-top:2rem;
             font-family:'Share Tech Mono',monospace; font-size:0.65rem; color:#7f8c8d; letter-spacing:2px;">
    🛡️ RAKSHAK · REALTIME ALERT KNOWLEDGE SURVEILLANCE HAZARD AWARENESS KOMMUNICATION<br>
    <span style="color:#3498db;">Powered by Sarvam AI · LangGraph · LangChain · RAG · FastAPI · Streamlit</span><br>
    Built for India's Disaster Management Sector · NDMA Compliant
</div>
""", unsafe_allow_html=True)

with tab5:
    st.markdown("""<div class="panel-header">ALERT CENTER</div>""", unsafe_allow_html=True)

    channel_status = get_alert_channel_status()
    sms_status = channel_status.get("sms", {})
    email_status = channel_status.get("email", {})

    col_status_1, col_status_2 = st.columns(2)
    with col_status_1:
        st.markdown(f"""
        <div class="data-panel">
            <div class="panel-header">SMS CHANNEL</div>
            <div style="font-size:0.9rem; line-height:1.9;">
                Status: <b style="color:{'#2ecc71' if sms_status.get('configured') else '#e67e22'};">
                    {'READY' if sms_status.get('configured') else 'NOT READY'}
                </b><br>
                From Number Present: <b style="color:#fff;">{sms_status.get('has_from_number')}</b><br>
                Messaging Service SID: <b style="color:#fff;">{sms_status.get('has_messaging_service_sid')}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_status_2:
        st.markdown(f"""
        <div class="data-panel">
            <div class="panel-header">EMAIL CHANNEL</div>
            <div style="font-size:0.9rem; line-height:1.9;">
                Status: <b style="color:{'#2ecc71' if email_status.get('configured') else '#e67e22'};">
                    {'READY' if email_status.get('configured') else 'NOT READY'}
                </b><br>
                SMTP Host: <b style="color:#fff;">{email_status.get('host') or 'Not set'}</b><br>
                Port / TLS / SSL: <b style="color:#fff;">{email_status.get('port')} / {email_status.get('use_tls')} / {email_status.get('use_ssl')}</b><br>
                Default Sender: <b style="color:#fff;">{email_status.get('default_sender') or 'Not set'}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.caption("Use commas or new lines to enter multiple recipients.")

    available_regions = [
        "Kerala",
        "Assam",
        "Gujarat",
        "Delhi",
        "Odisha",
        "Maharashtra",
        "Uttarakhand",
        "Himachal Pradesh",
        "All India",
    ]

    with st.form("manual_alert_form"):
        form_col_1, form_col_2 = st.columns(2)
        with form_col_1:
            manual_region = st.selectbox(
                "Alert Region",
                available_regions,
                index=available_regions.index(region) if region in available_regions else 0,
            )
            manual_severity = st.selectbox(
                "Severity",
                ["RED", "HIGH", "ORANGE", "MEDIUM", "YELLOW", "LOW", "INFO"],
                index=1,
            )
            manual_channels = st.multiselect("Channels", ["sms", "email"], default=["sms", "email"])
            manual_from_name = st.text_input("Sender Name Override", value="RAKSHAK Control Room")
            manual_from_email = st.text_input("Sender Email Override", value="")
        with form_col_2:
            manual_sms_recipients = st.text_area(
                "SMS Recipients",
                height=110,
                placeholder="+919876543210\n+919812345678",
            )
            manual_email_recipients = st.text_area(
                "Email Recipients",
                height=110,
                placeholder="ops@example.com\nadmin@example.com",
            )
        manual_message = st.text_area(
            "Alert Message",
            height=130,
            placeholder="Heavy rainfall expected in low-lying areas. Keep emergency teams on standby and advise residents to avoid river crossings.",
        )
        send_manual_alert_btn = st.form_submit_button("SEND ALERT NOW", use_container_width=True)

    if send_manual_alert_btn:
        sms_recipients = parse_recipient_input(manual_sms_recipients)
        email_recipients = parse_recipient_input(manual_email_recipients)

        if not manual_message.strip():
            st.error("Enter an alert message before sending.")
        elif not manual_channels:
            st.error("Select at least one delivery channel.")
        else:
            try:
                with st.spinner("Dispatching alert..."):
                    st.session_state.last_manual_alert = send_manual_alert(
                        region=manual_region,
                        message=manual_message.strip(),
                        severity=manual_severity,
                        channels=manual_channels,
                        sms_recipients=sms_recipients,
                        email_recipients=email_recipients,
                        from_email=manual_from_email,
                        from_name=manual_from_name,
                    )
                if st.session_state.last_manual_alert.get("status") == "sent":
                    st.success("Alert sent through at least one channel.")
                else:
                    st.warning("Alert was processed, but no delivery succeeded. Check the delivery details below.")
            except Exception as exc:
                st.session_state.last_manual_alert = {"status": "failed", "error": str(exc)}
                st.error(f"Alert dispatch failed: {exc}")

    manual_result = st.session_state.get("last_manual_alert")
    if manual_result:
        st.markdown("""<div class="panel-header">DELIVERY RESULTS</div>""", unsafe_allow_html=True)
        if manual_result.get("error"):
            st.error(manual_result["error"])
        else:
            summary = manual_result.get("summary", {})
            col_res_1, col_res_2 = st.columns(2)
            with col_res_1:
                sms_summary = summary.get("sms", {})
                st.markdown(f"""
                <div class="data-panel">
                    <div class="panel-header">SMS SUMMARY</div>
                    Attempted: <b>{sms_summary.get('attempted', 0)}</b><br>
                    Sent: <b>{sms_summary.get('sent', 0)}</b><br>
                    Failed: <b>{sms_summary.get('failed', 0)}</b><br>
                    Channel State: <b>{manual_result.get('channel_status', {}).get('sms', 'not_selected')}</b>
                </div>
                """, unsafe_allow_html=True)
            with col_res_2:
                email_summary = summary.get("email", {})
                st.markdown(f"""
                <div class="data-panel">
                    <div class="panel-header">EMAIL SUMMARY</div>
                    Attempted: <b>{email_summary.get('attempted', 0)}</b><br>
                    Sent: <b>{email_summary.get('sent', 0)}</b><br>
                    Failed: <b>{email_summary.get('failed', 0)}</b><br>
                    Channel State: <b>{manual_result.get('channel_status', {}).get('email', 'not_selected')}</b>
                </div>
                """, unsafe_allow_html=True)

            with st.expander("Per-recipient delivery details"):
                st.json(manual_result)
