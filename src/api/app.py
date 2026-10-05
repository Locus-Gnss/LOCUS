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

from src.evidence.evidence_bundle import EvidenceBundle


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="LOCUS GNSS Security Operations Center API",
    description="Cyber-Physical GNSS Defense, Multi-Agent SOC, and Grounded RAG Query System",
    version="1.0.0"
)

# Configure CORS for development and frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy singleton for query processor to prevent heavy imports during startup
_processor = None

def get_processor():
    global _processor
    if _processor is None:
        from src.query.query_processor import SecurityQueryProcessor
        _processor = SecurityQueryProcessor()
    return _processor

class _LazyProcessorProxy:
    def __getattr__(self, name):
        return getattr(get_processor(), name)

processor = _LazyProcessorProxy()


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
        "count": len(events),
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


@app.get("/api/evidence/{event_id}")
def get_evidence_bundle(event_id: str):
    """
    Retrieve Evidence Bundle representation directly by event ID.
    """
    bundle = processor.load_event(event_id)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Evidence for '{event_id}' not found.")
    return bundle.to_dict()


_cached_telemetry_valid = None

def _get_telemetry_valid_df():
    global _cached_telemetry_valid
    if _cached_telemetry_valid is None:
        csv_path = "data/processed/locus_telemetry_clean.csv"
        if not os.path.exists(csv_path):
            return None
        import pandas as pd
        df = pd.read_csv(csv_path)
        if "is_fix_valid" in df.columns:
            _cached_telemetry_valid = df[df["is_fix_valid"] == True].copy()
        else:
            _cached_telemetry_valid = df
    return _cached_telemetry_valid


@app.get("/api/telemetry/latest")
def get_latest_telemetry():
    """
    Return the most recent GNSS telemetry fix from real recorded data or live sensor.
    """
    valid = _get_telemetry_valid_df()
    if valid is None:
        return {
            "mode": "NO LIVE DATA",
            "is_live": False,
            "message": "Telemetry dataset not found. Awaiting sensor stream."
        }
    try:
        if valid.empty:
            return {"mode": "NO FIX", "is_live": False}
        last_row = valid.iloc[-1].to_dict()
        return {
            "mode": "HISTORICAL / REPLAY MODE",
            "provenance": "REAL GNSS TELEMETRY",
            "is_live": False,
            "telemetry": {
                "timestamp_utc": str(last_row.get("timestamp_gnss") or last_row.get("timestamp_pc")),
                "session_id": int(last_row.get("session_id", 0)),
                "epoch_id": int(last_row.get("epoch_id", 0)),
                "latitude": float(last_row.get("latitude", 0.0)),
                "longitude": float(last_row.get("longitude", 0.0)),
                "altitude_m": float(last_row.get("altitude_m", 0.0)),
                "speed_kmh": float(last_row.get("speed_kmh", 0.0)),
                "heading_deg": float(last_row.get("heading_deg", 0.0)),
                "satellites_used": int(last_row.get("satellites_used", 0)),
                "satellites_in_view": int(last_row.get("satellites_in_view_clean", 0)),
                "hdop": float(last_row.get("hdop", 0.0)),
                "vdop": float(last_row.get("vdop", 0.0)),
                "fix_quality": int(last_row.get("fix_quality", 0))
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read telemetry: {str(e)}")


@app.get("/api/telemetry/history")
def get_telemetry_history(limit: int = Query(100, ge=10, le=1000), session_id: Optional[int] = None):
    """
    Return recent telemetry trajectory history for charts and mapping.
    """
    valid = _get_telemetry_valid_df()
    if valid is None:
        return {"records": [], "count": 0, "mode": "NO LIVE DATA"}
    try:
        filtered = valid
        if session_id is not None:
            filtered = filtered[filtered["session_id"] == session_id]
        tail = filtered.tail(limit)
        records = []
        for _, row in tail.iterrows():
            records.append({
                "timestamp": str(row.get("timestamp_gnss") or row.get("timestamp_pc")),
                "epoch_id": int(row.get("epoch_id", 0)),
                "session_id": int(row.get("session_id", 0)),
                "latitude": float(row.get("latitude", 0.0)),
                "longitude": float(row.get("longitude", 0.0)),
                "altitude_m": float(row.get("altitude_m", 0.0)),
                "speed_kmh": float(row.get("speed_kmh", 0.0)),
                "heading_deg": float(row.get("heading_deg", 0.0)),
                "satellites_used": int(row.get("satellites_used", 0)),
                "hdop": float(row.get("hdop", 0.0)),
                "vdop": float(row.get("vdop", 0.0))
            })
        return {
            "mode": "HISTORICAL / REPLAY MODE",
            "provenance": "REAL GNSS TELEMETRY",
            "count": len(records),
            "records": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read history: {str(e)}")


_cached_features_payload = None

def _get_latest_features_payload():
    global _cached_features_payload
    if _cached_features_payload is not None:
        return _cached_features_payload

    csv_path = "data/features/locus_security_features.csv"
    if not os.path.exists(csv_path):
        return {"features": {}, "status": "NO DATA"}

    import pandas as pd
    df = pd.read_csv(csv_path)
    last_row = df.iloc[-1].to_dict()
    canonical_features = {
        "disp_haversine": float(last_row.get("disp_haversine", 0.0)),
        "vel_kinematic": float(last_row.get("vel_kinematic", 0.0)),
        "acc_kinematic": float(last_row.get("acc_kinematic", 0.0)),
        "jerk_kinematic": float(last_row.get("jerk_kinematic", 0.0)),
        "bearing_rate": float(last_row.get("bearing_rate", 0.0)),
        "HDOP": float(last_row.get("HDOP", 0.0)),
        "VDOP": float(last_row.get("VDOP", 0.0)),
        "fix_integrity": float(last_row.get("fix_integrity", 0.0)),
        "sat_count_tot": int(last_row.get("sat_count_tot", 0)),
        "sat_churn": float(last_row.get("sat_churn", 0.0)) if pd.notna(last_row.get("sat_churn")) else 0.0
    }
    bounds = {
        "disp_haversine": {"unit": "m", "warn": 50.0, "crit": 100.0},
        "vel_kinematic": {"unit": "m/s", "warn": 50.0, "crit": 85.0},
        "acc_kinematic": {"unit": "m/s²", "warn": 4.0, "crit": 10.0},
        "jerk_kinematic": {"unit": "m/s³", "warn": 15.0, "crit": 25.0},
        "bearing_rate": {"unit": "deg/s", "warn": 90.0, "crit": 180.0},
        "HDOP": {"unit": "unitless", "warn": 4.0, "crit": 8.0},
        "VDOP": {"unit": "unitless", "warn": 5.0, "crit": 10.0},
        "fix_integrity": {"unit": "score", "warn": 0.45, "crit": 0.20},
        "sat_count_tot": {"unit": "count", "warn": 6, "crit": 4},
        "sat_churn": {"unit": "ratio", "warn": 0.35, "crit": 0.60}
    }
    status_eval = {}
    for feat, val in canonical_features.items():
        b = bounds.get(feat, {})
        status = "NORMAL"
        if feat in ["fix_integrity", "sat_count_tot"]:
            if val <= b["crit"]: status = "CRITICAL"
            elif val <= b["warn"]: status = "WARNING"
        else:
            if abs(val) >= b["crit"]: status = "CRITICAL"
            elif abs(val) >= b["warn"]: status = "WARNING"
        status_eval[feat] = {
            "value": val,
            "unit": b.get("unit", ""),
            "warning_threshold": b.get("warn"),
            "critical_threshold": b.get("crit"),
            "status": status
        }
    _cached_features_payload = {
        "epoch_id": int(last_row.get("epoch_id", 0)),
        "session_id": int(last_row.get("session_id", 0)),
        "timestamp_utc": str(last_row.get("timestamp_utc", "")),
        "provenance": "10-D SECURITY FEATURE ENGINEERING",
        "features": canonical_features,
        "status_evaluation": status_eval
    }
    return _cached_features_payload


@app.get("/api/features/latest")
def get_latest_features():
    """
    Return the latest canonical 10-D security feature vector with calibrated threshold limits.
    """
    try:
        return _get_latest_features_payload()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read features: {str(e)}")


_cached_alerts_payload = None

@app.get("/api/alerts")
def get_alerts():
    """
    List all detected alerts and anomalous incidents from evidence bundles (cached in memory).
    """
    global _cached_alerts_payload
    if _cached_alerts_payload is not None:
        return _cached_alerts_payload

    events = processor.list_available_events()
    alerts = []
    for ev in events:
        bundle = processor.load_event(ev["event_id"])
        if not bundle:
            continue
        # Evaluate severity
        pr = bundle.physical_rules
        ifo = bundle.isolation_forest
        temp = bundle.temporal_model
        
        has_viol = pr.get("status") == "VIOLATED" or pr.get("triggered_count", 0) > 0
        has_ifo = ifo.get("is_anomaly", False)
        has_temp = temp.get("is_anomaly", False)

        severity = "INFO"
        if has_viol and pr.get("max_severity") == "CRITICAL":
            severity = "CRITICAL"
        elif has_viol or (has_ifo and has_temp):
            severity = "HIGH"
        elif has_ifo or has_temp:
            severity = "WARNING"

        affected = []
        if has_viol:
            for rule in pr.get("triggered_rules", []):
                affected.extend(rule.get("features", []))
        if not affected and has_ifo:
            affected.append("spatial_outlier")
        if temp.get("feature_attribution"):
            affected.extend(list(temp.get("feature_attribution", {}).keys())[:2])

        alerts.append({
            "alert_id": f"ALT-{bundle.event_id}",
            "event_id": bundle.event_id,
            "timestamp": bundle.timestamp_utc or "N/A",
            "severity": severity,
            "event_type": "KINEMATIC_VIOLATION" if has_viol else ("SEQUENCE_ANOMALY" if has_temp else "SPATIAL_OUTLIER"),
            "status": "UNRESOLVED" if severity in ["HIGH", "CRITICAL"] else "MONITORED",
            "detection_source": "Physical Rules + Multi-Detector Quad",
            "anomaly_score": float(ifo.get("anomaly_score", 0.0)),
            "affected_features": list(set(affected)),
            "location": bundle.location
        })
    _cached_alerts_payload = {
        "count": len(alerts),
        "alerts": alerts
    }
    return _cached_alerts_payload


@app.get("/api/alerts/{alert_id}")
def get_alert_detail(alert_id: str):
    """
    Retrieve specific alert by alert_id or event_id.
    """
    clean_id = alert_id.replace("ALT-", "")
    bundle = processor.load_event(clean_id)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")
    return bundle.to_dict()


@app.get("/api/agents/status")
def get_agents_status():
    """
    Return operational status, responsibilities, and latest active state for the 3 SOC agents.
    """
    return {
        "agents": {
            "agent_1_integrity": {
                "name": "GNSS Integrity Agent",
                "role": "Physical Invariants, Fix Quality, Satellite Churn & DOP Analysis",
                "status": "ACTIVE_READY",
                "input": "10-D Security Feature Vector + Physical Invariant Rules",
                "output": "IntegrityAssessment (Kinematic Health, Geometry Health, Discard Flag)"
            },
            "agent_2_temporal_threat": {
                "name": "Temporal / Threat Agent",
                "role": "Sequence Persistence Tracking, LSTM Reconstruction Error, Multi-Detector Convergence",
                "status": "ACTIVE_READY",
                "input": "Rolling Window Telemetry (W=10) + Detector Anomaly Scores",
                "output": "TemporalAssessment (Persistence Streak, Drift Classification, Convergence)"
            },
            "agent_3_master_soc": {
                "name": "Master SOC Orchestrator",
                "role": "Consensus Rating, Conflict Resolution, DEFCON Assignment, Mitigation Directives",
                "status": "ACTIVE_READY",
                "input": "Agent 1 Findings + Agent 2 Findings + Regulatory RAG Grounding Context",
                "output": "MasterSOCVerdict (DEFCON 1-5, Consensus Ratio, Mandatory Next Actions)"
            }
        }
    }


class RAGQueryRequest(BaseModel):
    query: str = Field(..., json_schema_extra={"example": "What are the RTCA DO-229E limits on HDOP?"})
    top_k: int = Field(3, ge=1, le=10)


@app.post("/api/rag/query")
def query_rag_knowledge_base(req: RAGQueryRequest):
    """
    Directly query the regulatory RAG knowledge base for technical definitions, standards, and citations.
    """
    try:
        res = processor.rag_engine.query(text=req.query, top_k=req.top_k)
        return {
            "query": req.query,
            "is_grounded": res.get("is_grounded", False),
            "citations_count": len(res.get("citations", [])),
            "citations": res.get("citations", []),
            "regulatory_standards": res.get("regulatory_standards", []),
            "provenance": "RAG REGULATORY KNOWLEDGE BASE",
            "insufficient_context": res.get("insufficient_context", False),
            "message": res.get("insufficient_context_message")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")


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
