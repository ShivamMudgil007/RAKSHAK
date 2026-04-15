"""
RAKSHAK - RAG Knowledge Base
Retrieval-Augmented Generation for disaster management data
Uses FAISS for vector storage with sentence-transformers embeddings
"""

import os
import json
from typing import List, Dict, Any

import pandas as pd

FLOOD_HISTORY_PATH = os.getenv(
    "RAKSHAK_FLOOD_HISTORY_PATH",
    r"C:\Users\vmadmin\Downloads\files\India_Flood_Data_2020_2025.xlsx",
)
EARTHQUAKE_HISTORY_PATH = os.getenv(
    "RAKSHAK_EARTHQUAKE_HISTORY_PATH",
    r"C:\Users\vmadmin\Downloads\files\India_Earthquake_Data_2020_2025.xlsx",
)

# ── Static Knowledge Base (used when vector DB is not available) ──────────────
DISASTER_KNOWLEDGE = [
    {
        "id": "flood_001",
        "title": "Kerala Flood Management Protocol",
        "content": (
            "Kerala experiences severe monsoon flooding, particularly in districts like "
            "Alappuzha, Thrissur, and Ernakulam. The State Disaster Management Authority (SDMA) "
            "coordinates response through district collectors. Early warning systems include "
            "IMD alerts, CWC river gauges, and community-level SMS alerts. Evacuation routes "
            "are pre-mapped with identified relief camps. Historical data shows 2018 floods "
            "affected 5.4 million people across 14 districts."
        ),
        "category": "flood",
        "region": "kerala",
        "severity": "high",
    },
    {
        "id": "flood_002",
        "title": "Assam Brahmaputra Flood Risk",
        "content": (
            "The Brahmaputra river basin in Assam floods annually between June and September. "
            "Districts most at risk: Dhubri, Bongaigaon, Barpeta, Morigaon, Nagaon, Jorhat. "
            "The Central Water Commission (CWC) monitors 15 gauge stations. Warning levels: "
            "Alert (danger -2m), Warning (danger -1m), Danger (exceeds danger mark), "
            "Extreme Danger (exceeds HFL). NDRF teams pre-positioned at Guwahati base."
        ),
        "category": "flood",
        "region": "assam",
        "severity": "high",
    },
    {
        "id": "earthquake_001",
        "title": "Delhi NCR Seismic Risk Assessment",
        "content": (
            "Delhi falls in seismic Zone IV (high damage risk). The region sits near the "
            "Himalayan Frontal Thrust fault system. Historical events: 2011 Sikkim earthquake "
            "(6.9M) felt strongly in Delhi. Building codes IS 1893:2016 mandatory for new "
            "construction. Emergency response: NDRF 8th Battalion at Ghaziabad, SDRF Delhi. "
            "Hospital preparedness: AIIMS, Safdarjung, RML designated disaster hospitals."
        ),
        "category": "earthquake",
        "region": "delhi",
        "severity": "medium",
    },
    {
        "id": "earthquake_002",
        "title": "Gujarat Seismic History and Preparedness",
        "content": (
            "Gujarat experienced the devastating 2001 Bhuj earthquake (7.7M) killing 20,000+. "
            "Kutch district remains Zone V (very high seismic risk). GSDMA established post-2001 "
            "with model disaster preparedness. Seismic microzonation completed for major cities. "
            "Search and rescue: NDRF 6th Battalion at Vadodara. Early warning via USGS and IMD "
            "National Seismological Network (NSN) with 115 broadband stations."
        ),
        "category": "earthquake",
        "region": "gujarat",
        "severity": "very_high",
    },
    {
        "id": "flood_003",
        "title": "Mumbai Urban Flood Risk",
        "content": (
            "Mumbai receives 2200mm average annual rainfall. Critical flood-prone areas: "
            "Dharavi, Kurla, Sion, Hindmata, Milan Subway. The 2005 floods (944mm in 24hrs) "
            "killed 1000+ people. BMC operates 45 pumping stations. Early warning: IMD Doppler "
            "radar at Colaba and Santacruz, 6-hour advance alerts. MCGM Disaster Control Room "
            "at 1916. Evacuation: Identified 280 flood shelters across 24 wards."
        ),
        "category": "flood",
        "region": "maharashtra",
        "severity": "high",
    },
    {
        "id": "cyclone_001",
        "title": "Odisha Cyclone Preparedness",
        "content": (
            "Odisha coast is highly cyclone-prone (Bay of Bengal). OSDMA is globally recognized "
            "for Zero Casualty policy. 879 cyclone shelters built along coast. Early warning: "
            "IMD provides 5-day track forecast, 3-day landfall prediction. Mass evacuation "
            "protocol: 24-48hrs before landfall. NDRF pre-positioning: 32 teams deployed "
            "during Cyclone Fani 2019 — record 1.2 million evacuated in 48 hours."
        ),
        "category": "cyclone",
        "region": "odisha",
        "severity": "very_high",
    },
    {
        "id": "general_001",
        "title": "India National Disaster Response Framework",
        "content": (
            "India's DM architecture: National level - NDMA (National Disaster Management Authority), "
            "NDRF (National Disaster Response Force) 16 battalions. State level - SDMA, SDRF. "
            "District level - District Disaster Management Authority (DDMA) under DM/Collector. "
            "NDMA Helpline: 1078. PM-AASHA scheme for relief. Disaster Risk Reduction aligned "
            "with Sendai Framework 2015-2030 and SDGs."
        ),
        "category": "general",
        "region": "india",
        "severity": "reference",
    },
    {
        "id": "alert_001",
        "title": "IMD Color-Coded Warning System",
        "content": (
            "IMD uses four-color coded warnings: GREEN - No warning, normal weather. "
            "YELLOW - Watch, severe weather possible, be aware. ORANGE - Alert, "
            "severe weather likely, be prepared. RED - Warning, extremely severe weather "
            "imminent/ongoing, take action. Warnings issued for: Heavy Rainfall, "
            "Thunderstorm, Cyclone, Heat Wave, Cold Wave, Fog, Strong Winds."
        ),
        "category": "general",
        "region": "india",
        "severity": "reference",
    },
    {
        "id": "source_001",
        "title": "Copernicus Data Space Ecosystem",
        "content": (
            "Copernicus Data Space Ecosystem is a reference source for Earth observation "
            "imagery, Sentinel satellite products, land monitoring, and rapid geospatial "
            "analysis useful for disaster response. It can support flood extent review, "
            "change detection, exposure assessment, and situational awareness using satellite "
            "data products relevant to India and global events."
        ),
        "category": "general",
        "region": "global",
        "severity": "reference",
        "source_url": "https://dataspace.copernicus.eu/",
    },
    {
        "id": "source_002",
        "title": "Google Earth Engine",
        "content": (
            "Google Earth Engine is a cloud-based geospatial analysis platform that can be used "
            "for satellite image processing, flood mapping, rainfall and land-cover analysis, "
            "burn scar monitoring, and large-scale disaster intelligence workflows. It is useful "
            "for combining remote sensing datasets with hazard models and regional monitoring."
        ),
        "category": "general",
        "region": "global",
        "severity": "reference",
        "source_url": "https://earthengine.google.com/",
    },
    {
        "id": "source_003",
        "title": "USGS EarthExplorer",
        "content": (
            "USGS EarthExplorer is a source for discovering and downloading satellite imagery, "
            "elevation products, aerial data, and historical remote sensing datasets. It is "
            "helpful for earthquake damage review, flood comparison, terrain analysis, and "
            "historical disaster assessment using Landsat, DEM, and other geospatial archives."
        ),
        "category": "general",
        "region": "global",
        "severity": "reference",
        "source_url": "https://earthexplorer.usgs.gov/",
    },
    {
        "id": "source_004",
        "title": "NASA LANCE Flood Mapping",
        "content": (
            "NASA LANCE flood products provide near-real-time flood mapping support using MODIS "
            "and related rapid observation workflows. This source is especially relevant for "
            "flood monitoring, inundation tracking, emergency response coordination, and quick "
            "situational updates during active flood events."
        ),
        "category": "flood",
        "region": "global",
        "severity": "reference",
        "source_url": "https://lance.modaps.eosdis.nasa.gov/flood/",
    },
    {
        "id": "source_005",
        "title": "ISRO Disaster and Earth Observation Resources",
        "content": (
            "The Indian Space Research Organisation (ISRO) is a key reference source for satellite "
            "missions, remote sensing applications, disaster support, and space-based monitoring. "
            "Its data, missions, and operational updates are useful for flood assessment, cyclone "
            "tracking, national geospatial intelligence, and rapid situational awareness in India."
        ),
        "category": "general",
        "region": "india",
        "severity": "reference",
        "source_url": "https://www.isro.gov.in/",
    },
    {
        "id": "source_006",
        "title": "Central Water Commission Flood Monitoring",
        "content": (
            "The Central Water Commission (CWC) is an authoritative source for river levels, flood "
            "forecasts, basin monitoring, reservoir information, and inundation-related hydrology "
            "inputs across India. It is especially relevant for flood early warning, gauge-based "
            "monitoring, river basin risk assessment, and district-level flood preparedness."
        ),
        "category": "flood",
        "region": "india",
        "severity": "reference",
        "source_url": "https://cwc.gov.in/",
    },
    {
        "id": "source_007",
        "title": "India Meteorological Department",
        "content": (
            "The India Meteorological Department (IMD) is the primary official source for weather "
            "warnings, rainfall forecasts, cyclone bulletins, heatwave advisories, and severe weather "
            "monitoring in India. It supports multi-hazard preparedness through forecast guidance, "
            "color-coded alerts, district-level warnings, and nowcasting relevant to disaster response."
        ),
        "category": "general",
        "region": "india",
        "severity": "reference",
        "source_url": "https://imd.gov.in/",
    },
    {
        "id": "source_008",
        "title": "Bhuvan Geoportal",
        "content": (
            "Bhuvan, developed by NRSC/ISRO, provides Indian geospatial layers, satellite imagery, "
            "thematic maps, and disaster-support mapping services. It is valuable for flood extent "
            "visualization, terrain review, infrastructure mapping, land-use interpretation, and "
            "India-specific geospatial decision support during emergencies."
        ),
        "category": "general",
        "region": "india",
        "severity": "reference",
        "source_url": "https://bhuvan.nrsc.gov.in/",
    },
    {
        "id": "source_009",
        "title": "National Institute of Disaster Management",
        "content": (
            "The National Institute of Disaster Management (NIDM) is a reference source for disaster "
            "management training materials, institutional frameworks, guidelines, capacity building, "
            "and preparedness resources in India. It is especially useful for planning, response "
            "protocols, mitigation frameworks, and official disaster management knowledge."
        ),
        "category": "general",
        "region": "india",
        "severity": "reference",
        "source_url": "https://nidm.gov.in/",
    },
]


def _safe_str(value: Any, default: str = "N/A") -> str:
    """Convert spreadsheet values to readable strings."""
    if value is None or (hasattr(pd, "isna") and pd.isna(value)):
        return default
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _normalize_region(value: Any) -> str:
    """Normalize region names for search."""
    text = _safe_str(value, "india")
    return text.lower().replace("&", "and")


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Trim spreadsheet headers."""
    df = df.copy()
    df.columns = [_safe_str(col, "").strip() for col in df.columns]
    return df.dropna(how="all")


def _to_slug(value: str) -> str:
    """Create a basic slug for synthetic document IDs."""
    return (
        value.lower()
        .replace("/", "_")
        .replace("&", "and")
        .replace(" ", "_")
        .replace("-", "_")
    )


def _load_flood_history_documents(path: str) -> List[Dict[str, Any]]:
    """Load flood history workbook into KB documents."""
    if not os.path.exists(path):
        return []

    docs: List[Dict[str, Any]] = []
    dataset_name = os.path.basename(path)

    try:
        events_df = _normalize_columns(pd.read_excel(path, sheet_name="Flood Records", header=3))
        for _, row in events_df.iterrows():
            event_id = _safe_str(row.get("Event ID"), "")
            if not event_id:
                continue

            state = _safe_str(row.get("State / UT"), "India")
            docs.append({
                "id": f"hist_flood_{_to_slug(event_id)}",
                "title": f"Historical Flood Event {event_id} - {state}",
                "content": (
                    f"Historical flood event from {_safe_str(row.get('Start Date'))} to {_safe_str(row.get('End Date'))} "
                    f"in {state}, affecting {_safe_str(row.get('District(s) Affected'))}. Cause: {_safe_str(row.get('Cause'))}. "
                    f"Severity: {_safe_str(row.get('Severity'))}. Area affected: {_safe_str(row.get('Area Affected (km²)'))} km². "
                    f"Rainfall: {_safe_str(row.get('Rainfall (mm/day)'))} mm/day. Deaths: {_safe_str(row.get('Deaths'))}. "
                    f"Missing: {_safe_str(row.get('Missing'))}. Displaced: {_safe_str(row.get('Displaced (lakhs)'))} lakhs. "
                    f"Houses damaged: {_safe_str(row.get('Houses Damaged'))}. Economic loss: ₹{_safe_str(row.get('Economic Loss (₹ Cr)'))} Cr. "
                    f"Remarks: {_safe_str(row.get('Remarks'))}."
                ),
                "category": "flood",
                "region": _normalize_region(state),
                "severity": _normalize_region(row.get("Severity")),
                "source_url": "https://cwc.gov.in/",
                "source_label": "CWC / Imported flood dataset",
                "source_note": dataset_name,
            })

        year_df = _normalize_columns(pd.read_excel(path, sheet_name="Summary by Year", header=1))
        for _, row in year_df.iterrows():
            year = _safe_str(row.get("Year"), "")
            if not year:
                continue

            docs.append({
                "id": f"hist_flood_year_{_to_slug(year)}",
                "title": f"India Flood Annual Summary {year}",
                "content": (
                    f"In {year}, India recorded {_safe_str(row.get('Events'))} flood events with "
                    f"{_safe_str(row.get('Deaths'))} deaths, {_safe_str(row.get('Missing'))} missing persons, "
                    f"{_safe_str(row.get('Displaced (lakhs)'))} lakhs displaced, {_safe_str(row.get('Houses Damaged'))} houses damaged, "
                    f"economic losses of ₹{_safe_str(row.get('Economic Loss (₹ Cr)'))} Cr, and "
                    f"{_safe_str(row.get('Extreme Events'))} extreme flood events."
                ),
                "category": "flood",
                "region": "india",
                "severity": "reference",
                "source_url": "https://cwc.gov.in/",
                "source_label": "CWC / Flood annual summary dataset",
                "source_note": dataset_name,
            })

        state_df = _normalize_columns(pd.read_excel(path, sheet_name="Summary by State", header=1))
        for _, row in state_df.iterrows():
            state = _safe_str(row.get("State / UT"), "")
            if not state:
                continue

            docs.append({
                "id": f"hist_flood_state_{_to_slug(state)}",
                "title": f"{state} Flood Summary (2020-2025)",
                "content": (
                    f"Between 2020 and 2025, {state} recorded {_safe_str(row.get('Total Events'))} major flood events, "
                    f"{_safe_str(row.get('Total Deaths'))} deaths, {_safe_str(row.get('Displaced (lakhs)'))} lakhs displaced, "
                    f"and economic losses of ₹{_safe_str(row.get('Economic Loss (₹ Cr)'))} Cr. "
                    f"Primary rivers: {_safe_str(row.get('Primary River(s)'))}. Risk category: {_safe_str(row.get('Risk Category'))}."
                ),
                "category": "flood",
                "region": _normalize_region(state),
                "severity": _normalize_region(row.get("Risk Category")),
                "source_url": "https://cwc.gov.in/",
                "source_label": "CWC / Flood state summary dataset",
                "source_note": dataset_name,
            })
    except Exception:
        return []

    return docs


def _load_earthquake_history_documents(path: str) -> List[Dict[str, Any]]:
    """Load earthquake history workbook into KB documents."""
    if not os.path.exists(path):
        return []

    docs: List[Dict[str, Any]] = []
    dataset_name = os.path.basename(path)

    try:
        events_df = _normalize_columns(pd.read_excel(path, sheet_name="Earthquake Records", header=3))
        for _, row in events_df.iterrows():
            event_id = _safe_str(row.get("Event ID"), "")
            if not event_id:
                continue

            state = _safe_str(row.get("State / UT"), "India")
            docs.append({
                "id": f"hist_eq_{_to_slug(event_id)}",
                "title": f"Historical Earthquake Event {event_id} - {state}",
                "content": (
                    f"Historical earthquake recorded on {_safe_str(row.get('Date'))} at {_safe_str(row.get('Time (IST)'))} in "
                    f"{state}, district/region {_safe_str(row.get('District / Region'))}. Coordinates: "
                    f"{_safe_str(row.get('Latitude (°N)'))}°N, {_safe_str(row.get('Longitude (°E)'))}°E. "
                    f"Depth: {_safe_str(row.get('Depth (km)'))} km. Magnitude: {_safe_str(row.get('Magnitude (Mw)'))} Mw. "
                    f"Seismic zone: {_safe_str(row.get('Seismic Zone'))}. Deaths: {_safe_str(row.get('Deaths'))}. "
                    f"Injuries: {_safe_str(row.get('Injuries'))}. Economic loss: ₹{_safe_str(row.get('Economic Loss (₹ Cr)'))} Cr. "
                    f"Remarks: {_safe_str(row.get('Remarks'))}."
                ),
                "category": "earthquake",
                "region": _normalize_region(state),
                "severity": "reference",
                "source_url": "https://imd.gov.in/",
                "source_label": "IMD / Imported earthquake dataset",
                "source_note": dataset_name,
            })

        year_df = _normalize_columns(pd.read_excel(path, sheet_name="Summary by Year", header=1))
        for _, row in year_df.iterrows():
            year = _safe_str(row.get("Year"), "")
            if not year:
                continue

            docs.append({
                "id": f"hist_eq_year_{_to_slug(year)}",
                "title": f"India Earthquake Annual Summary {year}",
                "content": (
                    f"In {year}, India recorded {_safe_str(row.get('Total Events'))} earthquake events, "
                    f"{_safe_str(row.get('Deaths'))} deaths, {_safe_str(row.get('Injuries'))} injuries, "
                    f"economic losses of ₹{_safe_str(row.get('Economic Loss (₹ Cr)'))} Cr, a maximum magnitude of "
                    f"{_safe_str(row.get('Max Magnitude'))}, and {_safe_str(row.get('High Severity (≥5.0)'))} high-severity events."
                ),
                "category": "earthquake",
                "region": "india",
                "severity": "reference",
                "source_url": "https://imd.gov.in/",
                "source_label": "IMD / Earthquake annual summary dataset",
                "source_note": dataset_name,
            })

        state_df = _normalize_columns(pd.read_excel(path, sheet_name="Summary by State", header=1))
        for _, row in state_df.iterrows():
            state = _safe_str(row.get("State / UT"), "")
            if not state:
                continue

            docs.append({
                "id": f"hist_eq_state_{_to_slug(state)}",
                "title": f"{state} Earthquake Summary (2020-2025)",
                "content": (
                    f"Between 2020 and 2025, {state} recorded {_safe_str(row.get('Total Events'))} earthquake events, "
                    f"{_safe_str(row.get('Deaths'))} deaths, {_safe_str(row.get('Injuries'))} injuries, and a maximum magnitude of "
                    f"{_safe_str(row.get('Max Magnitude'))}. Primary seismic zone: {_safe_str(row.get('Primary Seismic Zone'))}."
                ),
                "category": "earthquake",
                "region": _normalize_region(state),
                "severity": _safe_str(row.get("Primary Seismic Zone"), "reference").lower(),
                "source_url": "https://imd.gov.in/",
                "source_label": "IMD / Earthquake state summary dataset",
                "source_note": dataset_name,
            })
    except Exception:
        return []

    return docs


def load_historical_documents() -> List[Dict[str, Any]]:
    """Load all external historical datasets available to the project."""
    docs: List[Dict[str, Any]] = []
    docs.extend(_load_flood_history_documents(FLOOD_HISTORY_PATH))
    docs.extend(_load_earthquake_history_documents(EARTHQUAKE_HISTORY_PATH))
    return docs


class RAGKnowledgeBase:
    """
    Retrieval-Augmented Generation knowledge base for disaster management.
    Uses keyword-based retrieval as primary method with optional vector search.
    """

    def __init__(self):
        self.documents = DISASTER_KNOWLEDGE + load_historical_documents()
        self.use_vectors = False
        self._try_init_vectors()

    def _try_init_vectors(self):
        """Try to initialize FAISS vector store (optional)."""
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
            texts = [d["title"] + " " + d["content"] for d in self.documents]
            self.embeddings = self.encoder.encode(texts, show_progress_bar=False)
            self.use_vectors = True
        except Exception:
            self.use_vectors = False

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query."""
        if self.use_vectors:
            return self._vector_retrieve(query, top_k)
        return self._keyword_retrieve(query, top_k)

    def _vector_retrieve(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Vector similarity retrieval."""
        try:
            import numpy as np
            q_emb = self.encoder.encode([query])
            scores = np.dot(self.embeddings, q_emb.T).flatten()
            top_idx = scores.argsort()[-top_k:][::-1]
            return [
                {**self.documents[i], "score": float(scores[i])}
                for i in top_idx
            ]
        except Exception:
            return self._keyword_retrieve(query, top_k)

    def _keyword_retrieve(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Keyword-based retrieval fallback."""
        query_lower = query.lower()
        keywords = query_lower.split()
        scored = []
        for doc in self.documents:
            text = (doc["title"] + " " + doc["content"] + " " + doc["category"] + " " + doc["region"]).lower()
            score = sum(1 for kw in keywords if kw in text)
            # Boost by category match
            if any(cat in query_lower for cat in ["flood", "earthquake", "cyclone"]):
                if doc["category"] in query_lower:
                    score += 3
            scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {**doc, "score": score}
            for score, doc in scored[:top_k]
            if score > 0
        ] or self.documents[:top_k]  # Always return something

    def format_context(self, docs: List[Dict[str, Any]]) -> str:
        """Format retrieved documents as context for LLM."""
        if not docs:
            return "No specific knowledge retrieved."
        parts = []
        for doc in docs:
            source_line = ""
            if doc.get("source_url") and doc.get("source_label"):
                source_line = f"\nSource: {doc['source_label']} - {doc['source_url']}"
            elif doc.get("source_url"):
                source_line = f"\nSource: {doc['source_url']}"
            elif doc.get("source_note"):
                source_line = f"\nSource: {doc['source_note']}"
            parts.append(
                f"[{doc['category'].upper()} - {doc['region'].upper()}]\n"
                f"Title: {doc['title']}\n"
                f"{doc['content']}{source_line}"
            )
        return "\n\n---\n\n".join(parts)

    def list_sources(self, docs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Return unique source references for a set of documents."""
        sources: List[Dict[str, str]] = []
        seen = set()

        for doc in docs:
            url = doc.get("source_url", "")
            note = doc.get("source_note", "")
            label = doc.get("source_label") or doc.get("title", "Source")
            key = url or note or label
            if not key or key in seen:
                continue
            seen.add(key)
            sources.append({
                "label": label,
                "url": url,
                "note": note,
            })

        return sources

    def add_document(self, title: str, content: str, category: str, region: str):
        """Add a new document to the knowledge base."""
        new_doc = {
            "id": f"custom_{len(self.documents)}",
            "title": title,
            "content": content,
            "category": category,
            "region": region,
            "severity": "medium",
        }
        self.documents.append(new_doc)
        if self.use_vectors:
            self._try_init_vectors()  # Re-index


# Singleton
rag_kb = RAGKnowledgeBase()
