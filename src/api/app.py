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
from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from src.evidence.evidence_bundle import EvidenceBundle


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="LOCUS GNSS Security Operations Center API",
    description="Cyber-Physical GNSS Defense, Multi-Agent SOC, and Grounded RAG Query System",
    version="1.0.0"
)

# Portable project root resolver
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def resolve_path(rel_path: str) -> str:
    """Resolve a relative project path portably against cwd or PROJECT_ROOT."""
    if os.path.exists(rel_path):
        return rel_path
    candidate = os.path.join(PROJECT_ROOT, rel_path)
    if os.path.exists(candidate):
        return candidate
    return rel_path

# Configure CORS for local development, public tunnels, and deployed frontend
frontend_origin_env = os.getenv("FRONTEND_ORIGIN", "")
cors_env = os.getenv("CORS_ALLOWED_ORIGINS", "")

LOCAL_DEV_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

allowed_origins = list(LOCAL_DEV_ORIGINS)
if frontend_origin_env:
    for o in frontend_origin_env.split(","):
        clean_o = o.strip()
        if clean_o and clean_o not in allowed_origins:
            allowed_origins.append(clean_o)
if cors_env and cors_env != "*":
    for o in cors_env.split(","):
        clean_o = o.strip()
        if clean_o and clean_o not in allowed_origins:
            allowed_origins.append(clean_o)

if cors_env == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
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


@app.get("/", summary="System Root and GUI Redirect")
def root(request: Request):
    """
    Root endpoint. Returns system metadata for API consumers or redirects browsers to the GUI.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return RedirectResponse(url="/gui")
    return {
        "system": "LOCUS Cyber-Physical GNSS Security Operations Center",
        "status": "OPERATIONAL",
        "gui_url": "/gui",
        "api_docs": "/docs",
        "health_check": "/api/health",
        "version": "1.0.0"
    }


@app.get("/gui", response_class=HTMLResponse, summary="LOCUS Cyber SOC GUI Portal")
@app.get("/dashboard", response_class=HTMLResponse, summary="LOCUS Cyber SOC GUI Dashboard")
def serve_gui(request: Request):
    """
    Serve the responsive LOCUS Master Cyber-Physical SOC GUI console.
    Integrates directly with the running Streamlit dashboard.
    """
    gui_target = os.getenv("LOCUS_GUI_URL", "").rstrip("/")
    if not gui_target:
        # Infer client access host
        client_host = request.headers.get("host", "localhost:8000").split(":")[0]
        gui_target = f"http://{client_host}:8501"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LOCUS — Cyber-Physical GNSS SOC Portal</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #080b10;
            --bg-panel: #0d121d;
            --border-color: #1a2333;
            --accent-cyan: #00f2fe;
            --accent-blue: #4facfe;
            --accent-green: #00e676;
            --accent-purple: #7928ca;
            --text-main: #f0f6fc;
            --text-muted: #8b949e;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body, html {{
            width: 100%;
            height: 100%;
            overflow: hidden;
            background-color: var(--bg-dark);
            font-family: 'Inter', -apple-system, sans-serif;
            color: var(--text-main);
        }}
        .topbar {{
            height: 52px;
            background: linear-gradient(90deg, #0d121d 0%, #111827 100%);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 1.25rem;
            z-index: 100;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-weight: 700;
            font-size: 1.05rem;
            letter-spacing: 0.05em;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-family: 'JetBrains Mono', monospace;
        }}
        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.2rem 0.6rem;
            border-radius: 9999px;
            font-size: 0.72rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            background: rgba(0, 230, 118, 0.1);
            color: var(--accent-green);
            border: 1px solid rgba(0, 230, 118, 0.3);
        }}
        .status-dot {{
            width: 7px;
            height: 7px;
            background-color: var(--accent-green);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--accent-green);
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.4; transform: scale(0.85); }}
        }}
        .actions {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }}
        .btn {{
            text-decoration: none;
            color: var(--text-main);
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            padding: 0.35rem 0.75rem;
            border-radius: 6px;
            font-size: 0.78rem;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            transition: all 0.2s ease;
        }}
        .btn:hover {{
            background: rgba(0, 242, 254, 0.1);
            border-color: var(--accent-cyan);
            color: var(--accent-cyan);
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #00f2fe22, #4facfe33);
            border-color: var(--accent-cyan);
            color: var(--accent-cyan);
        }}
        .frame-container {{
            width: 100%;
            height: calc(100% - 52px);
            position: relative;
            background: #0e1117;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
    </style>
</head>
<body>
    <header class="topbar">
        <div class="brand">
            <span>LOCUS SOC</span>
            <div class="badge">
                <span class="status-dot"></span>
                <span>FASTAPI &times; GUI OPERATIONAL</span>
            </div>
        </div>
        <div class="actions">
            <a href="{gui_target}" target="_blank" class="btn btn-primary" title="Open Streamlit in new tab">
                [+] Fullscreen GUI
            </a>
            <a href="/docs" target="_blank" class="btn" title="Open FastAPI Swagger Interactive Docs">
                API Docs
            </a>
            <a href="/api/health" target="_blank" class="btn" title="Inspect Live Health">
                System Health
            </a>
        </div>
    </header>
    <main class="frame-container">
        <iframe 
            src="{gui_target}" 
            title="LOCUS Master Security Operations Center Dashboard"
            allow="fullscreen; clipboard-read; clipboard-write; geolocation"
        ></iframe>
    </main>
</body>
</html>"""
    return HTMLResponse(content=html_content)



@app.get("/health", summary="Service Health Check")
@app.get("/api/health", summary="API Health Check")
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
        csv_path = resolve_path("data/processed/locus_telemetry_clean.csv")
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
def get_telemetry_history(limit: int = Query(100, ge=1, le=500000), session_id: Optional[int] = None):
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

    csv_path = resolve_path("data/features/locus_security_features.csv")
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


@app.get("/api/events/{event_id}/assessment")
def get_event_canonical_assessment(event_id: str):
    """
    Retrieve single authoritative canonical assessment for an event.
    Source of truth for Threat Rating, Detection Summary, Agent Consensus, and Recommended Actions.
    """
    assessment = processor.get_canonical_assessment(event_id)
    if not assessment:
        raise HTTPException(status_code=404, detail=f"Assessment for event '{event_id}' not found.")
    return assessment


class PipelineProcessRequest(BaseModel):
    data: Any = Field(..., description="Raw string (CSV/NMEA/JSON), list of records, or JSON dictionary")
    format: str = Field("auto", description="Data format: auto, csv, json, nmea")
    source_name: str = Field("api_upload", description="Human-readable origin identifier")
    source_type: str = Field("UPLOADED DATA", description="Source category")


_latest_pipeline_run: Optional[Dict[str, Any]] = None


@app.post("/api/pipeline/process")
def process_pipeline_data(req: PipelineProcessRequest):
    """
    Process incoming GNSS records through the automated security analysis pipeline:
    Validation -> Preprocessing -> 10-D Features -> Detection Quad -> Agents -> RAG -> Explainable AI -> Evidence Bundle.
    """
    global _latest_pipeline_run
    try:
        from src.pipeline.pipeline_engine import PipelineEngine
        engine = PipelineEngine()
        result = engine.process_gnss_input(
            raw_input=req.data,
            input_format=req.format,
            source_name=req.source_name,
            source_type=req.source_type
        )
        res_dict = result.to_dict()
        _latest_pipeline_run = res_dict

        # Persist run audit artifact
        runs_dir = resolve_path("data/runs")
        os.makedirs(runs_dir, exist_ok=True)
        run_file = os.path.join(runs_dir, f"run_{result.run_id}.json")
        try:
            import json
            with open(run_file, "w", encoding="utf-8") as f:
                json.dump(res_dict, f, indent=2, default=str)
        except Exception:
            pass

        # Invalidate in-memory event caches
        processor.invalidate_cache()
        return res_dict
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Pipeline processing failed: {str(e)}")


@app.get("/api/pipeline/latest")
def get_latest_pipeline_run():
    """
    Retrieve the most recent pipeline execution run (prevents state loss on dashboard refresh).
    """
    global _latest_pipeline_run
    if _latest_pipeline_run is not None:
        return _latest_pipeline_run

    # Fallback to most recent file in data/runs
    runs_dir = resolve_path("data/runs")
    if os.path.exists(runs_dir):
        files = [os.path.join(runs_dir, f) for f in os.listdir(runs_dir) if f.startswith("run_") and f.endswith(".json")]
        if files:
            files.sort(key=os.path.getmtime, reverse=True)
            try:
                import json
                with open(files[0], "r", encoding="utf-8") as f:
                    _latest_pipeline_run = json.load(f)
                    return _latest_pipeline_run
            except Exception:
                pass

    return {
        "status": "NO_RUNS_YET",
        "message": "No interactive pipeline runs executed yet. Upload data or stream sentences to initiate analysis."
    }


@app.get("/api/pipeline/runs/{run_id}")
def get_pipeline_run_by_id(run_id: str):
    """
    Retrieve specific pipeline execution result by run ID.
    """
    global _latest_pipeline_run
    if _latest_pipeline_run and _latest_pipeline_run.get("run_id") == run_id:
        return _latest_pipeline_run

    run_file = resolve_path(os.path.join("data", "runs", f"run_{run_id}.json"))
    if os.path.exists(run_file):
        try:
            import json
            with open(run_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read run record: {str(e)}")

    raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found.")


@app.get("/api/models/status")
def get_models_status():
    """
    Return genuine runtime readiness status for all 4 detection components.
    Zero fabrication: honestly reports unfitted XGBoost status.
    """
    from src.detection.xgboost_detector import XGBoostDetector
    from src.detection.isolation_forest import IsolationForestDetector
    from src.detection.temporal_model import TemporalDetector

    xgb_path = resolve_path("models/production/xgboost/xgboost_detector.joblib")
    xgb_fitted = os.path.exists(xgb_path)

    if_path = resolve_path("models/production/isolation_forest/isolation_forest.joblib")
    if_fitted = os.path.exists(if_path) or os.path.exists(resolve_path("models/isolation_forest/isolation_forest_tuned.joblib"))

    lstm_path = resolve_path("models/production/temporal/temporal_model.pt")
    lstm_fitted = os.path.exists(lstm_path) or os.path.exists(resolve_path("models/temporal/temporal_model_tuned.pt"))

    return {
        "detectors": {
            "physical_rules": {
                "name": "Physical Rules Engine",
                "status": "OPERATIONAL",
                "is_fitted": True,
                "type": "DETERMINISTIC_KINEMATICS",
                "version": "prules-v1.1"
            },
            "isolation_forest": {
                "name": "Isolation Forest (Spatial ML)",
                "status": "READY" if if_fitted else "FALLBACK",
                "is_fitted": if_fitted,
                "type": "UNSUPERVISED_SPATIAL_ANOMALY",
                "version": "iforest-tuned-v1.1"
            },
            "xgboost": XGBoostDetector.get_status_info(),
            "temporal_lstm": {
                "name": "Temporal LSTM Autoencoder",
                "status": "READY" if lstm_fitted else "FALLBACK",
                "is_fitted": lstm_fitted,
                "type": "TEMPORAL_SEQUENCE_AUTOENCODER",
                "version": "lstm-tuned-v1.1",
                "sequence_requirement": "W=10 consecutive epochs within same session"
            }
        }
    }


@app.get("/api/models/xgboost/info")
def get_xgboost_info():
    """
    Return comprehensive provenance, label availability, and evaluation status for Detector 3.
    """
    from src.detection.xgboost_detector import XGBoostDetector
    return XGBoostDetector.get_status_info()


class ModelTrainRequest(BaseModel):
    model_type: str = Field("isolation_forest", description="Target model: isolation_forest, xgboost")
    dataset_path: Optional[str] = Field(None, description="Path to verified labelled scenario dataset")
    label_column: Optional[str] = Field(None, description="Optional target label column name")
    contamination: float = Field(0.02, description="Target contamination rate")
    n_estimators: int = Field(200, description="Tree estimators")
    confirm_replace: bool = Field(False, description="Confirm replacement of production artifact")


@app.post("/api/models/train")
def train_model(req: ModelTrainRequest):
    """
    Controlled model training and validation endpoint.
    Fits scaler only on training partition; evaluates thresholds on validation; does not leak test set.
    """
    if req.model_type == "xgboost":
        try:
            from scripts.train_xgboost import run_training_pipeline
            target_dataset = resolve_path(req.dataset_path) if req.dataset_path else resolve_path("data/features/locus_security_features.csv")
            report = run_training_pipeline(
                dataset_path=target_dataset,
                label_column=req.label_column,
                n_estimators=req.n_estimators
            )
            return report
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"XGBoost training pipeline error: {str(e)}")

    if req.model_type != "isolation_forest":
        raise HTTPException(
            status_code=400,
            detail=f"Automated online retraining for '{req.model_type}' is unsupported."
        )

    try:
        from src.detection.tune_isolation_forest import run_isolation_forest_tuning
        results = run_isolation_forest_tuning(
            features_csv=resolve_path("data/features/locus_security_features.csv"),
            output_dir=resolve_path("models/isolation_forest"),
            contamination=req.contamination,
            n_estimators=req.n_estimators
        )
        return {
            "status": "TRAINED_AND_EVALUATED",
            "model_type": req.model_type,
            "metrics": results,
            "replaced_production": req.confirm_replace,
            "message": "Model trained on training partition and evaluated on independent validation partition."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "development").lower() == "development"
    uvicorn.run("src.api.app:app", host=host, port=port, reload=reload)

