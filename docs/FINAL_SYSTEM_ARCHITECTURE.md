# LOCUS Final System Architecture & Security SOC Interface

## 1. Executive Overview

The **LOCUS Final Security Query System** is an enterprise-grade, explainable Security Operations Center (SOC) platform for GNSS (Global Navigation Satellite System) signal assurance, threat detection, and forensic analysis.

It integrates physics-based kinematic rules, machine learning anomaly detectors (Isolation Forest, Supervised XGBoost, Temporal LSTM Autoencoder), a 3-agent deliberative SOC hierarchy (Integrity Agent, Temporal/Threat Agent, Master SOC Orchestrator), and a standards-grounded Retrieval-Augmented Generation (RAG) subsystem into a decoupled **FastAPI REST backend** and a modern **Streamlit SOC Dashboard**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            OPERATOR / SOC ANALYST                           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Natural-Language Query / Event Selection
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI SERVICE LAYER                             │
│                  Endpoints: /api/events, /api/query, /api/soc/deliberate    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SECURITY QUERY PROCESSOR ENGINE                       │
│ 1. Intent Classification (Alert Cause, Culprit Features, Persistence, etc.)  │
│ 2. Telemetry & Evidence Bundle Retrieval (Zero-copy cached bundles)         │
│ 3. 3-Agent SOC Deliberation Layer                                           │
│    ├─ Agent 1: GNSS Integrity Agent (Physics, DOP, Churn, Fix Quality)      │
│    ├─ Agent 2: Temporal Threat Agent (Streak, Reconstruction, Convergence)  │
│    └─ Agent 3: Master SOC Orchestrator (DEFCON Consensus & Conflict Res)   │
│ 4. Regulatory RAG Subsystem (ICAO, RTCA DO-229E, CISA PNT, MITRE ATLAS)    │
│ 5. Strict Response Assembly (Zero fabrication, explicit evidence boundaries) │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FINAL EXPLAINABLE SOC RESPONSE                       │
│ • Event ID & Timestamp              • Multi-Detector Outputs               │
│ • DEFCON Level & Status (CRITICAL)   • 3-Agent Structured Findings          │
│ • Confidence Score                  • RAG Regulatory Grounding Citations   │
│ • Evidence Bundle Itemized Records  • Grounded Natural Language Explanation │
│ • 10-D Security Feature Vector      • Recommended Operational Next Actions │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. End-to-End Query Workflow

The query architecture executes deterministically through six sequential stages:

```
User Query
    ↓
Query Processor
    ↓
Relevant Event / Evidence Retrieval
    ↓
Agentic SOC (Agent 1 + Agent 2)
    ↓
RAG (Vector Store & Regulatory Knowledge Base)
    ↓
Master SOC Agent (Agent 3 Synthesis & Conflict Resolution)
    ↓
Final Explainable Response
```

### Stage 1: Query Processor & Intent Parsing
The `SecurityQueryProcessor` parses incoming queries and maps them to operational intents:
1. **Flagged Root Cause**: `"Why was this event flagged?"`
2. **Feature Attribution**: `"What features caused the anomaly?"`
3. **Temporal Persistence**: `"Is the anomaly persistent?"`
4. **Evidence Audit**: `"Show me the evidence behind this alert."`
5. **Temporal Model Metrics**: `"What did the temporal model detect?"`
6. **Geometry & Signal Quality**: `"Explain the navigation-quality degradation."`
7. **Forensic Deep Dive**: Complex queries detailing spoofing vs. multipath signatures.

### Stage 2: Event & Evidence Retrieval
The processor retrieves the telemetry epoch from `data/telemetry_clean.csv` and loads or dynamically reconstructs the corresponding `EvidenceBundle` from the multi-detector pipeline. If the requested event ID does not exist, the processor immediately halts with an explicit error rather than guessing.

### Stage 3: Three-Agent Deliberative SOC
- **Agent 1 (GNSS Integrity Agent)**: Inspects kinematic physical plausibility, fix integrity, satellite counts, and DOP dilution of precision.
- **Agent 2 (Temporal / Threat Agent)**: Tracks multi-epoch persistence streaks, LSTM reconstruction errors, and multi-detector convergence.
- **Agent 3 (Master SOC Orchestrator)**: Weighs findings, arbitrates conflicts (physics breaches override ML, single-detector transient spikes downgraded), and assigns the final DEFCON level (1 to 5).

### Stage 4: Technical Grounding via RAG
The `SecurityRAGEngine` retrieves regulatory context from indexed aviation and infrastructure standards:
- **RTCA DO-229E**: Airborne GPS/SBAS integrity standards.
- **ICAO Annex 10**: GNSS navigation service specifications.
- **CISA PNT Best Practices**: Critical infrastructure spoofing/jamming resilience.
- **MITRE ATLAS**: Adversarial threat tactics against PNT ML models.
- **NMEA-0183 / Satellite Constellation Norms**: Geometry and constellation churn thresholds.

### Stage 5: Final Response Synthesis
The Master SOC Agent synthesizes a structured output strictly adhering to verified data:
- **Zero Fabrication**: If sensor telemetry, temporal sequences, or RAG sources are missing or below threshold, the response explicitly declares: `"Insufficient evidence: [reason]"`.
- **Read-Only Invariant**: Sensor data and detector outputs are immutable and cannot be rewritten by agents or RAG.

---

## 3. Official 10-D Security Feature Vector

The system evaluates and visualizes the standardized LOCUS 10-D feature vector for every event:

| # | Feature Name | Dimension / Unit | Physical Meaning | Normal Range | Alert Threshold |
|---|--------------|------------------|------------------|--------------|-----------------|
| 1 | `disp_haversine` | meters (m) | Great-circle displacement over epoch $\Delta t$ | $0.0 - 50.0$ m | $> 500$ m (Mach jump) |
| 2 | `vel_kinematic` | m/s | Kinematic velocity ($\Delta d / \Delta t$) | $0.0 - 45.0$ m/s | $> 340$ m/s (Supersonic) |
| 3 | `acc_kinematic` | m/s² | Rate of change of kinematic velocity | $-15.0 - 15.0$ m/s² | $> 40.0$ m/s² ($>4g$) |
| 4 | `jerk_kinematic` | m/s³ | Third derivative of position | $-20.0 - 20.0$ m/s³ | $> 100.0$ m/s³ |
| 5 | `bearing_rate` | deg/s | Heading angular rate of change | $-45.0 - 45.0$ deg/s | $> 180.0$ deg/s |
| 6 | `HDOP` | unitless | Horizontal Dilution of Precision | $0.8 - 2.5$ | $> 4.0$ (Degraded), $> 20.0$ (Starved) |
| 7 | `VDOP` | unitless | Vertical Dilution of Precision | $1.0 - 3.5$ | $> 6.0$ |
| 8 | `fix_integrity` | score ($0.0 - 1.0$) | Weighted fix quality + active PRN ratio | $0.8 - 1.0$ | $< 0.40$ |
| 9 | `sat_count_tot` | integer | Total visible space vehicles across constellations | $12 - 32$ | $< 4$ (Critical starvation) |
| 10 | `sat_churn` | count / epoch | PRNs added or lost between consecutive epochs | $0 - 2$ | $> 5$ (Constellation reset) |

---

## 4. Multi-Detector Quad Architecture

Every epoch is evaluated across four distinct detection layers:

1. **Physical Rules Engine (`PhysicalRulesEngine`)**:
   - Zero-shot physical invariant verification.
   - Evaluates speed of sound, gravitational acceleration boundaries ($g \le 4.0$), teleportation jumps, geometry starvation, and constellation churn resets.
2. **Isolation Forest Detector (`IsolationForestDetector`)**:
   - Unsupervised spatial out-of-distribution detection.
   - Computes tree path length anomaly scores across scaled 10-D feature vectors.
3. **XGBoost Supervised Classifier (`XGBoostDetectorInfrastructure`)**:
   - Supervised gradient-boosted decision trees.
   - Predicts attack probabilities (`p_spoofing`, `p_jamming`, `p_multipath`).
4. **Temporal LSTM Autoencoder (`TemporalLSTMDetector`)**:
   - Sequence-aware deep learning across sliding temporal windows ($W = 10$).
   - Computes MSE reconstruction error vector:
     $$\mathcal{L}_{recon} = \frac{1}{D} \sum_{i=1}^{10} (x_i - \hat{x}_i)^2$$
   - Flags gradual trajectory drift and coordinate step discontinuities.

---

## 5. Security Query System API Specification (FastAPI)

The backend exposes clean REST endpoints decoupled from the user interface:

### 1. `GET /api/health`
Returns system status, active models, RAG vector store size, and uptime.
```json
{
  "status": "healthy",
  "rag_documents_indexed": 30,
  "loaded_events_count": 5
}
```

### 2. `GET /api/events`
Lists all available GNSS security events with high-level classifications.
```json
{
  "events": [
    {
      "event_id": "EVT-2026-0001",
      "timestamp_utc": "2026-03-29T10:14:22Z",
      "status": "NOMINAL",
      "risk_level": "DEFCON_5"
    },
    {
      "event_id": "EVT-2026-0002",
      "timestamp_utc": "2026-03-29T10:14:23Z",
      "status": "CRITICAL_SPOOFING",
      "risk_level": "DEFCON_1"
    }
  ]
}
```

### 3. `GET /api/events/{event_id}`
Returns complete forensic data for a single event: 10-D features, detector outputs, and raw evidence.

### 4. `POST /api/query`
Executes natural-language queries against a specific event.
**Request Body:**
```json
{
  "event_id": "EVT-2026-0002",
  "query": "Why was this event flagged?"
}
```
**Response Body (Compliant with Official SOC Schema):**
```json
{
  "event": "EVT-2026-0002",
  "current_status": "CRITICAL_SPOOFING",
  "risk_level": "DEFCON_1",
  "confidence": 0.98,
  "evidence": [
    {
      "type": "physical_rule_violation",
      "rule": "VELOCITY_EXCEEDS_MACH1",
      "severity": "CRITICAL",
      "detail": "Observed velocity 1240.5 m/s exceeds Mach 1 threshold (340.0 m/s)."
    }
  ],
  "feature_values": {
    "disp_haversine": 1240.5,
    "vel_kinematic": 1240.5,
    "acc_kinematic": 850.2,
    "jerk_kinematic": 340.0,
    "bearing_rate": 180.0,
    "HDOP": 1.2,
    "VDOP": 1.5,
    "fix_integrity": 1.0,
    "sat_count_tot": 16,
    "sat_churn": 0
  },
  "model_outputs": {
    "physical_rules": { "status": "VIOLATED", "violations_count": 2 },
    "isolation_forest": { "is_anomaly": true, "anomaly_score": 0.8841 },
    "xgboost": { "is_anomaly": true, "predicted_label": "SPOOFING" },
    "temporal_model": { "is_anomaly": true, "reconstruction_error": 0.3421 }
  },
  "agent_findings": {
    "agent_1_integrity": {
      "assessment": "CRITICAL_ANOMALY",
      "kinematic_health": 0.0,
      "geometry_health": 1.0
    },
    "agent_2_temporal_threat": {
      "assessment": "SPOOFING_COORDINATE_STEP",
      "persistence_count": 4,
      "detector_convergence": 1.0
    },
    "agent_3_master_soc": {
      "verdict": "CRITICAL_SPOOFING",
      "consensus_ratio": 1.0,
      "conflict_resolved": true
    }
  },
  "rag_sources": [
    {
      "source_document": "rtca_do_229e_gps_sbas.md",
      "authority": "RTCA / FAA",
      "section": "Kinematic Integrity & Pseudorange Rate Limits",
      "relevance_score": 0.892
    }
  ],
  "explanation": "Event 'EVT-2026-0002' was flagged as CRITICAL_SPOOFING (DEFCON_1) because: Agent 1 detected 2 physical rule breach(es): Observed kinematic velocity of 1240.50 m/s violates the physical Mach 1 limit; Isolation Forest flagged spatial out-of-distribution state with score 0.8841. Citing standards: RTCA DO-229E.",
  "recommended_next_action": [
    "REJECT_GNSS_SOLUTION",
    "TRANSITION_TO_INERTIAL_DEAD_RECKONING",
    "RAISE_OPERATOR_ALARM"
  ]
}
```

### 5. `POST /api/soc/deliberate`
Triggers full multi-agent SOC deliberation on arbitrary custom evidence bundles without requiring natural-language prompts.

---

## 6. Streamlit SOC Dashboard Implementation

The front-end (`src/ui/dashboard.py` and `dashboard.py`) is designed with high visual impact, cybersecurity SOC aesthetics, glassmorphism containers, and interactive telemetry exploration.

### Core Visual Sections:
1. **Header & Navigation Bar**: Real-time status badge, selected event identifier, DEFCON status alert.
2. **Top Executive KPI Bar**:
   - Event Status (`CRITICAL_SPOOFING`, `PERSISTENT_DRIFT`, `NOMINAL`).
   - Risk Level (`DEFCON 1` to `DEFCON 5`).
   - Analytic Confidence ($95.0\% - 99.0\%$).
   - Consensus Ratio ($100\%$ quad convergence).
3. **10-D Security Feature Grid**:
   - Custom metric cards displaying exact values and color-coded status (Normal vs. Violated).
4. **Multi-Detector Status Quad**:
   - Side-by-side cards for Physical Rules, Isolation Forest, XGBoost Classifier, and Temporal LSTM Autoencoder.
5. **Interactive Natural-Language Security Query Terminal**:
   - Pre-loaded one-click queries:
     - `Why was this event flagged?`
     - `What features caused the anomaly?`
     - `Is the anomaly persistent?`
     - `Show me the evidence behind this alert.`
     - `What did the temporal model detect?`
     - `Explain the navigation-quality degradation.`
   - Freeform custom prompt input.
   - Real-time generation of explainable synthesis with explicit RAG grounding citations.
6. **Forensic Evidence & Agent Findings Accordions**:
   - Deep inspection of Agent 1, Agent 2, and Agent 3 deliberation payloads.
   - Raw JSON Evidence Bundle viewer.
7. **Standards-Grounded RAG Inspector**:
   - Full citation cards showing authority (ICAO, RTCA, CISA, MITRE), document source, relevance score, and verified technical text.

---

## 7. Decoupled Execution Guide

### Starting the Backend REST API:
```bash
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger documentation is available at:
`http://localhost:8000/docs`

### Starting the Streamlit SOC Dashboard:
```bash
python -m streamlit run dashboard.py
```
Or directly from the internal module:
```bash
python -m streamlit run src/ui/dashboard.py
```

### Running Test Verification:
```bash
python -m pytest tests/test_query_system.py -v
```
All 11 unit and integration tests validate:
- Response schema compliance.
- Natural-language query execution for all required prompt types.
- Insufficient evidence handling without hallucinations.
- FastAPI endpoints `/api/health`, `/api/events`, `/api/query`, and `/api/soc/deliberate`.
