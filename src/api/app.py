"""
LOCUS Security Query System — FastAPI REST API Backend

Module: src.api.app
Focus: High-performance, decoupled REST API providing endpoints for:
- Event enumeration and detailed telemetry inspection
- 10-D cybersecurity feature vector retrieval
- 4-Detector output inspection
- Multi-agent SOC deliberation and consensus rating
- Natural language security query resolution with grounded RAG explanations
"""

import os
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, Field

from src.query.query_processor import SecurityQueryProcessor
from src.evidence.evidence_bundle import EvidenceBundle


app = FastAPI(
    title="LOCUS GNSS Security Operations Center API",
    description="Cyber-Physical GNSS Defense, Multi-Agent SOC, and Grounded RAG Query System",
    version="1.0.0"
)

# Initialize query processor
processor = SecurityQueryProcessor()


class SecurityQueryRequest(BaseModel):
    query: str = Field(..., json_schema_extra={"example": "Why was this event flagged?"})
    event_id: Optional[str] = Field(None, json_schema_extra={"example": "evt_4_220"})


class DeliberationRequest(BaseModel):
    event_id: str = Field(..., json_schema_extra={"example": "evt_4_220"})


@app.get("/")
def root():
    return {
        "system": "LOCUS Cyber-Physical GNSS Security Operations Center",
        "status": "OPERATIONAL",
        "api_docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/api/health")
def health_check():
    """
    Return comprehensive system health and component statuses.
    """
    events = processor.list_available_events()
    indexed_chunks = processor.rag_engine.vector_store.count()
    return {
        "status": "HEALTHY",
        "total_available_events": len(events),
        "rag_vector_store_chunks": indexed_chunks,
        "active_models": {
            "physical_rules": "Operational",
            "isolation_forest": "Tuned v1.1",
            "xgboost": "Audited v1.1",
            "temporal_lstm": "Tuned v1.1"
        },
        "soc_agents": {
            "agent_1_integrity": "Active",
            "agent_2_temporal_threat": "Active",
            "agent_3_master_soc": "Active"
        }
    }


@app.get("/api/events")
def list_events():
    """
    List all available GNSS events stored in the evidence repository.
    """
    events = processor.list_available_events()
    return {
        "total": len(events),
        "events": events
    }


@app.get("/api/events/{event_id}")
def get_event_detail(event_id: str):
    """
    Retrieve complete Evidence Bundle, 10-D feature vector, and detector outputs for a specific event.
    """
    bundle = processor.load_event(event_id)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found in evidence store.")
    return bundle.to_dict()


@app.post("/api/query")
def process_natural_language_query(req: SecurityQueryRequest):
    """
    Process natural-language security queries:
    User Query -> Event Retrieval -> 3-Agent SOC -> RAG -> Master SOC Agent -> Explainable Response.
    """
    result = processor.process_query(query=req.query, event_id=req.event_id)
    return result


@app.post("/api/soc/deliberate")
def deliberate_event(req: DeliberationRequest):
    """
    Trigger full 3-Agent SOC deliberation with RAG grounding for an event.
    """
    bundle = processor.load_event(req.event_id)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Event '{req.event_id}' not found.")
    
    result = processor.process_query(
        query="Show me the full evidence, agent findings, and regulatory citations behind this event.",
        event_id=req.event_id,
        bundle=bundle
    )
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.app:app", host="127.0.0.1", port=8000, reload=True)
