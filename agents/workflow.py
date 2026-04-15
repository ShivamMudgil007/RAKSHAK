"""
RAKSHAK - LangGraph Agentic Workflow
Multi-agent system for disaster management intelligence
Agents: Coordinator → [Weather, Seismic, RAG, Alert] → Synthesizer
"""

import json
import asyncio
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime
import operator

# ── State Definition ──────────────────────────────────────────────────────────

class RAKSHAKState(TypedDict):
    """Shared state across all agents in the workflow."""
    query: str
    language: str
    region: str
    disaster_type: str

    # Agent outputs
    weather_data: Dict[str, Any]
    seismic_data: Dict[str, Any]
    rag_context: str
    retrieved_docs: List[Dict]

    # Generated content
    alerts: List[Dict[str, Any]]
    analysis: str
    recommendations: List[str]
    final_response: str

    # Metadata
    messages: Annotated[List[str], operator.add]
    error: Optional[str]
    timestamp: str


# ── Mock Data Providers (replace with live APIs in production) ────────────────

def get_weather_data(region: str) -> Dict[str, Any]:
    """Fetch weather/IMD data for the region."""
    region_lower = region.lower()

    weather_db = {
        "kerala": {
            "alert_level": "RED",
            "rainfall_24h": 185,
            "forecast": "Heavy to very heavy rainfall expected for next 48 hours",
            "wind_speed": 45,
            "humidity": 94,
            "flood_risk": "VERY HIGH",
            "imd_warning": "Red Alert issued for Ernakulam, Thrissur, Palakkad",
        },
        "assam": {
            "alert_level": "ORANGE",
            "rainfall_24h": 120,
            "forecast": "Moderate to heavy rainfall, Brahmaputra above danger mark",
            "wind_speed": 30,
            "humidity": 88,
            "flood_risk": "HIGH",
            "imd_warning": "Orange Alert for 10 districts",
        },
        "gujarat": {
            "alert_level": "YELLOW",
            "rainfall_24h": 45,
            "forecast": "Light rainfall, improving conditions",
            "wind_speed": 20,
            "humidity": 72,
            "flood_risk": "LOW",
            "imd_warning": "Yellow Alert for Kutch, Banaskantha",
        },
        "delhi": {
            "alert_level": "GREEN",
            "rainfall_24h": 5,
            "forecast": "Clear skies, hot weather",
            "wind_speed": 15,
            "humidity": 55,
            "flood_risk": "LOW",
            "imd_warning": "Heat wave warning for NCR",
        },
    }

    for key, data in weather_db.items():
        if key in region_lower:
            return data

    return {
        "alert_level": "YELLOW",
        "rainfall_24h": 60,
        "forecast": "Moderate rainfall expected",
        "wind_speed": 25,
        "humidity": 78,
        "flood_risk": "MEDIUM",
        "imd_warning": "Monitor IMD bulletins",
    }


def get_seismic_data(region: str) -> Dict[str, Any]:
    """Fetch seismic/earthquake data for the region."""
    region_lower = region.lower()

    seismic_db = {
        "gujarat": {
            "seismic_zone": "V",
            "risk_level": "VERY HIGH",
            "recent_events": [
                {"magnitude": 3.2, "depth": 15, "location": "45km NE of Bhuj", "time": "2 hours ago"},
                {"magnitude": 2.8, "depth": 10, "location": "Morbi", "time": "6 hours ago"},
            ],
            "tectonic_activity": "HIGH - Katrol Hill Fault active",
        },
        "delhi": {
            "seismic_zone": "IV",
            "risk_level": "HIGH",
            "recent_events": [
                {"magnitude": 2.1, "depth": 8, "location": "Bahadurgarh", "time": "1 day ago"},
            ],
            "tectonic_activity": "MODERATE - Mathura Fault proximity",
        },
        "kerala": {
            "seismic_zone": "III",
            "risk_level": "MODERATE",
            "recent_events": [],
            "tectonic_activity": "LOW",
        },
    }

    for key, data in seismic_db.items():
        if key in region_lower:
            return data

    return {
        "seismic_zone": "III",
        "risk_level": "MODERATE",
        "recent_events": [],
        "tectonic_activity": "LOW",
    }


# ── Agent Functions ───────────────────────────────────────────────────────────

def weather_agent(state: RAKSHAKState) -> RAKSHAKState:
    """Agent: Fetches and analyzes weather/IMD data."""
    try:
        region = state.get("region", "india")
        weather = get_weather_data(region)
        return {
            **state,
            "weather_data": weather,
            "messages": [f"[WeatherAgent] Fetched data for {region}: Alert={weather['alert_level']}"],
        }
    except Exception as e:
        return {**state, "weather_data": {}, "error": str(e),
                "messages": [f"[WeatherAgent] Error: {e}"]}


def seismic_agent(state: RAKSHAKState) -> RAKSHAKState:
    """Agent: Fetches seismic/earthquake risk data."""
    try:
        region = state.get("region", "india")
        seismic = get_seismic_data(region)
        return {
            **state,
            "seismic_data": seismic,
            "messages": [f"[SeismicAgent] Zone {seismic['seismic_zone']} - Risk: {seismic['risk_level']}"],
        }
    except Exception as e:
        return {**state, "seismic_data": {}, "error": str(e),
                "messages": [f"[SeismicAgent] Error: {e}"]}


def rag_agent(state: RAKSHAKState) -> RAKSHAKState:
    """Agent: Retrieves relevant knowledge from vector DB."""
    try:
        from rag.knowledge_base import rag_kb
        query = state.get("query", "")
        region = state.get("region", "")
        full_query = f"{query} {region} disaster management"
        docs = rag_kb.retrieve(full_query, top_k=3)
        context = rag_kb.format_context(docs)
        return {
            **state,
            "rag_context": context,
            "retrieved_docs": docs,
            "messages": [f"[RAGAgent] Retrieved {len(docs)} knowledge documents"],
        }
    except Exception as e:
        return {**state, "rag_context": "Knowledge base unavailable.",
                "retrieved_docs": [], "messages": [f"[RAGAgent] Error: {e}"]}


def alert_agent(state: RAKSHAKState) -> RAKSHAKState:
    """Agent: Generates structured alerts based on data."""
    alerts = []
    weather = state.get("weather_data", {})
    seismic = state.get("seismic_data", {})
    region = state.get("region", "India")

    # Weather alerts
    if weather.get("alert_level") in ("RED", "ORANGE"):
        alerts.append({
            "type": "WEATHER",
            "severity": weather["alert_level"],
            "title": f"IMD {weather['alert_level']} Alert - {region}",
            "message": weather.get("imd_warning", "Severe weather warning"),
            "action": "Evacuate low-lying areas. Avoid river banks.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
        })

    if weather.get("flood_risk") in ("HIGH", "VERY HIGH"):
        alerts.append({
            "type": "FLOOD",
            "severity": "HIGH",
            "title": f"Flood Risk Warning - {region}",
            "message": f"24h rainfall: {weather.get('rainfall_24h', 0)}mm. Flood risk: {weather.get('flood_risk')}",
            "action": "Pre-position NDRF teams. Open relief camps. Activate evacuation protocol.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
        })

    # Seismic alerts
    recent = seismic.get("recent_events", [])
    for event in recent:
        if event.get("magnitude", 0) >= 3.0:
            alerts.append({
                "type": "EARTHQUAKE",
                "severity": "MEDIUM",
                "title": f"Seismic Activity Detected - M{event['magnitude']}",
                "message": f"Magnitude {event['magnitude']} at {event['location']}, depth {event['depth']}km",
                "action": "Inspect critical infrastructure. Alert hospital EOCs.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
            })

    if not alerts:
        alerts.append({
            "type": "INFO",
            "severity": "LOW",
            "title": "Normal Conditions",
            "message": "No significant disaster alerts for the selected region.",
            "action": "Continue routine monitoring.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
        })

    return {
        **state,
        "alerts": alerts,
        "messages": [f"[AlertAgent] Generated {len(alerts)} alert(s)"],
    }


def synthesizer_agent(state: RAKSHAKState) -> RAKSHAKState:
    """Agent: Synthesizes all data into final response using Sarvam LLM."""
    try:
        from utils.sarvam_client import sarvam_client

        weather = state.get("weather_data", {})
        seismic = state.get("seismic_data", {})
        rag_ctx = state.get("rag_context", "")
        alerts = state.get("alerts", [])
        query = state.get("query", "")
        region = state.get("region", "India")

        system_prompt = """You are RAKSHAK, an expert AI system for disaster management in India.
You analyze weather, seismic, and historical data to provide actionable insights to disaster management officials.
Be precise, structured, and actionable. Use Indian context. Always provide:
1. Situation Assessment
2. Immediate Recommendations
3. Resource Deployment Suggestions
4. Proactive Warnings"""

        context_summary = f"""
Query: {query}
Region: {region}
Weather Alert: {weather.get('alert_level', 'N/A')} | Rainfall: {weather.get('rainfall_24h', 0)}mm/24h
Flood Risk: {weather.get('flood_risk', 'N/A')}
IMD Warning: {weather.get('imd_warning', 'None')}
Seismic Zone: {seismic.get('seismic_zone', 'N/A')} | Risk: {seismic.get('risk_level', 'N/A')}
Recent Earthquakes: {len(seismic.get('recent_events', []))} events
Active Alerts: {len(alerts)}

Knowledge Base Context:
{rag_ctx[:800]}
"""

        messages = [{"role": "user", "content": context_summary}]
        analysis = sarvam_client.chat(messages, system_prompt)

        recommendations = [
            "Activate district-level Emergency Operations Centers (EOC)",
            f"Pre-position NDRF teams in high-risk {region} zones",
            "Broadcast early warnings via Common Alerting Protocol (CAP)",
            "Coordinate with hospitals for mass casualty preparedness",
            "Ensure relief camp readiness with food, water, medicine stockpiles",
        ]

        return {
            **state,
            "analysis": analysis,
            "recommendations": recommendations,
            "final_response": analysis,
            "messages": ["[Synthesizer] Final response generated"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M IST"),
        }

    except Exception as e:
        fallback = (
            f"RAKSHAK Analysis for {state.get('region', 'India')}:\n\n"
            f"Based on available data:\n"
            f"• Weather Alert Level: {state.get('weather_data', {}).get('alert_level', 'N/A')}\n"
            f"• Flood Risk: {state.get('weather_data', {}).get('flood_risk', 'N/A')}\n"
            f"• Seismic Zone: {state.get('seismic_data', {}).get('seismic_zone', 'N/A')}\n\n"
            f"Immediate Actions Required based on current conditions."
        )
        return {
            **state,
            "analysis": fallback,
            "final_response": fallback,
            "recommendations": ["Monitor IMD alerts", "Activate EOC", "Pre-position NDRF"],
            "messages": [f"[Synthesizer] Fallback response: {e}"],
        }


# ── Graph Builder ─────────────────────────────────────────────────────────────

def build_rakshak_graph():
    """Build the LangGraph workflow. Falls back to sequential if LangGraph unavailable."""
    try:
        from langgraph.graph import StateGraph, END

        workflow = StateGraph(RAKSHAKState)
        workflow.add_node("weather", weather_agent)
        workflow.add_node("seismic", seismic_agent)
        workflow.add_node("rag", rag_agent)
        workflow.add_node("alerts", alert_agent)
        workflow.add_node("synthesizer", synthesizer_agent)

        workflow.set_entry_point("weather")
        workflow.add_edge("weather", "seismic")
        workflow.add_edge("seismic", "rag")
        workflow.add_edge("rag", "alerts")
        workflow.add_edge("alerts", "synthesizer")
        workflow.add_edge("synthesizer", END)

        return workflow.compile()

    except Exception:
        # Return a simple callable if LangGraph not available
        class SimpleWorkflow:
            def invoke(self, state):
                state = weather_agent(state)
                state = seismic_agent(state)
                state = rag_agent(state)
                state = alert_agent(state)
                state = synthesizer_agent(state)
                return state

        return SimpleWorkflow()


def run_rakshak_pipeline(
    query: str,
    region: str = "India",
    language: str = "en-IN",
    disaster_type: str = "all",
) -> RAKSHAKState:
    """Main entry point to run the RAKSHAK agentic pipeline."""
    initial_state = RAKSHAKState(
        query=query,
        language=language,
        region=region,
        disaster_type=disaster_type,
        weather_data={},
        seismic_data={},
        rag_context="",
        retrieved_docs=[],
        alerts=[],
        analysis="",
        recommendations=[],
        final_response="",
        messages=[],
        error=None,
        timestamp=datetime.now().isoformat(),
    )

    graph = build_rakshak_graph()
    result = graph.invoke(initial_state)
    return result
