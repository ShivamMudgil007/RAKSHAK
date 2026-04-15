# 🛡️ RAKSHAK
## Realtime · Alert · Knowledge · Surveillance · Hazard · Awareness · Kommunication

> AI-Powered Public Intelligence System for Disaster Management in India
> Focus: Floods & Earthquakes | Powered by **Sarvam AI**

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RAKSHAK SYSTEM ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  USER LAYER                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Streamlit UI (app.py)                                          │ │
│  │  • Intelligence Hub  • Risk Map  • AI Chat  • Knowledge Base   │ │
│  │  • Multilingual (Hindi/Tamil/Telugu/Kannada/Bengali)            │ │
│  └─────────────────────┬───────────────────────────────────────────┘ │
└────────────────────────┼─────────────────────────────────────────────┘
                         │ HTTP / Direct Call
┌────────────────────────▼─────────────────────────────────────────────┐
│  API LAYER                                                            │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  FastAPI Server (main.py)                                    │    │
│  │  POST /query  GET /weather/:region  GET /seismic/:region     │    │
│  │  POST /translate  POST /tts  POST /send-alert  GET /alerts   │    │
│  └──────────────────────┬───────────────────────────────────────┘    │
└─────────────────────────┼────────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────────┐
│  AGENTIC LAYER (LangGraph Workflow)                                   │
│                                                                       │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐   │
│  │ Weather  │───▶│ Seismic  │───▶│   RAG    │───▶│    Alert     │   │
│  │  Agent   │    │  Agent   │    │  Agent   │    │    Agent     │   │
│  └──────────┘    └──────────┘    └────┬─────┘    └──────┬───────┘   │
│                                       │                  │           │
│                                  ┌────▼──────────────────▼────────┐  │
│                                  │      Synthesizer Agent         │  │
│                                  │   (Sarvam LLM + Context)       │  │
│                                  └────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────────────┐
│  INTELLIGENCE LAYER                                                   │
│                                                                       │
│  ┌─────────────────────┐  ┌─────────────────────┐                   │
│  │   RAG Knowledge     │  │    Sarvam AI APIs    │                   │
│  │   Base (FAISS)      │  │                      │                   │
│  │                     │  │  • LLM (sarvam-m)    │                   │
│  │  • Flood data       │  │  • ASR (Speech→Text) │                   │
│  │  • Earthquake data  │  │  • TTS (Text→Speech) │                   │
│  │  • Historical events│  │  • Translation       │                   │
│  │  • Protocols        │  │  • Language Detect   │                   │
│  └─────────────────────┘  └─────────────────────┘                   │
│                                                                       │
│  ┌─────────────────────┐  ┌─────────────────────┐                   │
│  │   Weather/IMD Data  │  │   Seismic/USGS Data  │                   │
│  │   • Alert levels    │  │   • Zone mapping     │                   │
│  │   • Rainfall data   │  │   • Recent events    │                   │
│  │   • Forecasts       │  │   • Risk assessment  │                   │
│  └─────────────────────┘  └─────────────────────┘                   │
└──────────────────────────────────────────────────────────────────────┘
```

## 🔄 Agentic Workflow Diagram

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                   LangGraph Workflow                     │
│                                                          │
│  1. WEATHER AGENT                                        │
│     ├── Fetch IMD alert level (RED/ORANGE/YELLOW/GREEN)  │
│     ├── Get rainfall, wind, humidity data               │
│     └── Output: weather_data, flood_risk                │
│              │                                           │
│              ▼                                           │
│  2. SEISMIC AGENT                                        │
│     ├── Get seismic zone classification                 │
│     ├── Fetch recent earthquake events                  │
│     └── Output: seismic_data, risk_level                │
│              │                                           │
│              ▼                                           │
│  3. RAG AGENT                                            │
│     ├── Embed query → Vector search in FAISS            │
│     ├── Retrieve top-K relevant documents               │
│     └── Output: rag_context, retrieved_docs             │
│              │                                           │
│              ▼                                           │
│  4. ALERT AGENT                                          │
│     ├── Evaluate thresholds (rainfall, seismicity)      │
│     ├── Generate structured alerts with actions         │
│     └── Output: alerts[]                                │
│              │                                           │
│              ▼                                           │
│  5. SYNTHESIZER AGENT                                    │
│     ├── Combine: weather + seismic + RAG + alerts       │
│     ├── Call Sarvam LLM (sarvam-m model)                │
│     ├── Generate: analysis, recommendations             │
│     └── Output: final_response                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
    │
    ▼
Response → Streamlit UI / FastAPI
```

## 📁 Project Structure

```
rakshak/
├── app.py                    # Streamlit UI (main frontend)
├── main.py                   # FastAPI backend server
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
│
├── agents/
│   ├── __init__.py
│   └── workflow.py           # LangGraph agentic pipeline
│                             # (WeatherAgent → SeismicAgent → RAGAgent
│                             #  → AlertAgent → SynthesizerAgent)
│
├── rag/
│   ├── __init__.py
│   └── knowledge_base.py     # FAISS vector store + knowledge
│
└── utils/
    ├── __init__.py
    └── sarvam_client.py      # Sarvam AI API client
                              # (LLM, ASR, TTS, Translation, LID)
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd rakshak
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# .env is pre-configured with Sarvam API key
# Update SARVAM_API_KEY if needed
```

### 3. Run FastAPI Backend
```bash
python main.py
# API available at: http://localhost:8000
# Swagger docs at: http://localhost:8000/docs
```

### 4. Run Streamlit Frontend
```bash
streamlit run app.py
# UI available at: http://localhost:8501
```

## 🔑 Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Sarvam AI (sarvam-m) |
| Speech-to-Text | Sarvam AI ASR |
| Text-to-Speech | Sarvam AI TTS (Bulbul v1) |
| Translation | Sarvam AI (Mayura v1) |
| Agent Framework | LangGraph + LangChain |
| Vector DB | FAISS + sentence-transformers |
| UI | Streamlit |
| API | FastAPI + Uvicorn |
| Visualization | Plotly |

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | System info |
| GET | `/health` | Health check |
| POST | `/query` | Full AI analysis pipeline |
| GET | `/weather/{region}` | Weather/IMD data |
| GET | `/seismic/{region}` | Seismic risk data |
| GET | `/alerts` | All active alerts |
| POST | `/translate` | Text translation |
| POST | `/tts` | Text-to-speech |
| POST | `/send-alert` | Dispatch SMS/Email alerts |

## 🌐 Supported Languages
Hindi • Tamil • Telugu • Kannada • Malayalam • Bengali • English

## ⚠️ IMPORTANT SECURITY NOTE
The Sarvam API key visible in the screenshot is now in `.env`.
**Rotate your API key immediately** at https://dashboard.sarvam.ai
Never commit API keys to version control. Use environment variables or secrets management.

## 📋 Features
- ✅ Reactive: Answers NL queries about current disaster situations
- ✅ Proactive: Generates early warnings based on thresholds
- ✅ Multilingual: Supports 7 Indian languages via Sarvam AI
- ✅ RAG-powered: Retrieves from curated disaster management knowledge
- ✅ Multi-agent: LangGraph orchestrates specialized agents
- ✅ SMS/Email Alerts: Dispatch system for officials
- ✅ Visualization: Risk maps and trend charts
- ✅ API-first: FastAPI backend for integration
- 🔄 Self-improving: Feedback loop for model refinement (roadmap)
