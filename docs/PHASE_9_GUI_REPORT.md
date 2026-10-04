# LOCUS Phase 9 — GUI / SOC Dashboard Technical Report

## 1. Objective
The objective of Phase 9 was to construct the user-facing **Security Operations Center (SOC) Dashboard** for the complete LOCUS GNSS security framework. The GUI serves as a consolidated operational command console that integrates hardware ingestion, NMEA stream preprocessing, 10-D cybersecurity feature engineering, multi-detector anomaly classification, immutable Evidence Bundles, a 3-agent deliberative SOC hierarchy, and standards-grounded Retrieval-Augmented Generation (RAG).

---

## 2. Existing System Integration
The GUI strictly operates as a presentation and control layer over the completed Phases 1–8 architecture without moving core business logic into the frontend:
- **Phase 1 & 2 (Hardware & Parsing)**: Telemetry records flow directly from `locus_telemetry_clean.csv` or live COM serial streams through `SOCDataService`.
- **Phase 3 & 4 (Features)**: Evaluates the canonical 10-D feature dataset `locus_security_features.csv` without renaming or substituting features.
- **Phase 5 & 5.5 (Detection Quad)**: Visualizes deterministic Physical Rules, tuned Isolation Forest, audited XGBoost, and Temporal LSTM Autoencoder outputs.
- **Phase 6 (Agentic SOC)**: Direct deliberation with Agent 1 (Integrity), Agent 2 (Temporal Threat), and Agent 3 (Master SOC Orchestrator).
- **Phase 7 (Regulatory RAG)**: Live grounding against vectorized standards (ICAO Annex 10, RTCA DO-229E, CISA Resilient PNT, MITRE ATT&CK for Space).
- **Phase 8 (Query Engine & REST API)**: Consumes `SecurityQueryProcessor` and FastAPI endpoints.

---

## 3. GUI Architecture
- **Framework**: Streamlit (`v1.63+`) paired with Plotly (`v7.1+`) for interactive data visualization.
- **Styling**: Cyber SOC dark theme (`#0b0f19` background, `#0f172a` container cards, `#334155` subtle borders, and semantic green/amber/red indicators).
- **Modular Component Layout**:
  ```
  src/ui/
  ├── dashboard.py               # Master entrypoint orchestrator
  ├── data_service.py            # Central data provider and caching layer
  └── components/
      ├── navbar.py              # Top header with connection & mode indicator
      ├── kpis.py                # 6 primary executive KPI cards
      ├── telemetry_panel.py     # Live/Replay telemetry charts (Speed, HDOP, Sats, etc.)
      ├── map_panel.py           # OpenStreetMap geospatial trajectory track
      ├── features_panel.py      # Canonical 10-D feature monitor with bounds
      ├── detection_panel.py     # 4-Detector quad output cards
      ├── alert_center.py        # Filterable incident dispatch queue
      ├── evidence_panel.py      # Evidence Bundle audit viewer & timeline
      ├── agent_soc_panel.py     # 3-Agent deliberative workflow
      ├── rag_panel.py           # Regulatory RAG knowledge explorer
      ├── query_terminal.py      # Natural-language SOC assistant
      ├── health_panel.py        # Real-time architectural health matrix
      └── theme.py               # Dark cybersecurity stylesheet
  ```

---

## 4. Main Dashboard
- **Header Bar**: Live UTC clock, system health indicator, mode badge (`LIVE SENSOR STREAM` vs `HISTORICAL / REPLAY MODE`), and data provenance notice.
- **Top 6 KPI Cards**:
  1. `GNSS Status`: `CONNECTED` (Replay/Live) or `NO LIVE DATA`.
  2. `Security Status`: `NORMAL`, `WARNING`, or `CRITICAL` with DEFCON rating (`DEFCON 1` to `DEFCON 5`).
  3. `Satellites`: Number of space vehicles actively used and visible in sky view.
  4. `HDOP`: Horizontal Dilution of Precision with color-coded geometry thresholds.
  5. `Speed`: Current kinematic velocity in km/h and m/s.
  6. `Active Alerts`: Count of active forensic threat incidents.

---

## 5. Live GNSS Monitoring
Provides time-series trend analysis across adjustable historical windows (50 to 1,000 epochs) using dark-themed Plotly charts:
- **Speed & Altitude vs. Time**: Dual-axis trajectory dynamics.
- **HDOP & VDOP vs. Time**: Receiver geometry degradation with RTCA DO-229E alert thresholds ($HDOP = 4.0$).
- **Satellite Count vs. Time**: Constellation visibility with the critical 4-satellite starvation limit.
- **Heading Angle vs. Time**: Receiver orientation tracking.

---

## 6. 10-D Security Feature Monitoring
Monitors the exact canonical 10-D vector:
1. `disp_haversine` (m)
2. `vel_kinematic` (m/s)
3. `acc_kinematic` (m/s²)
4. `jerk_kinematic` (m/s³)
5. `bearing_rate` (deg/s)
6. `HDOP` (unitless)
7. `VDOP` (unitless)
8. `fix_integrity` (score 0–1)
9. `sat_count_tot` (count)
10. `sat_churn` (ratio)

Thresholds are read directly from `configs/model_training.yaml` to flag features as `NORMAL`, `WARNING`, or `CRITICAL`.

---

## 7. Detection & Machine Learning
Visualizes outputs across the four-detector quad:
- **Physical Rules Engine**: Invariant breaches (Mach 1 velocity, 4g acceleration, jump boundaries).
- **Isolation Forest**: Unsupervised spatial outlier classification with tree-path score.
- **Supervised XGBoost Classifier**: Multi-class attack probability estimation.
- **Temporal LSTM Autoencoder**: Reconstruction error across $W=10$ sequence windows.
- **Final Decision**: Agentic consensus rating and risk level.

---

## 8. Evidence Bundle & Audit Details
Presents complete Evidence Bundles without fabrication:
- Event ID, timestamp, and source provenance.
- Raw and structured telemetry references.
- 10-D feature snapshot.
- Triggered rule violations with exact numeric delta.
- Temporal sequence observations rendered on a vertical timeline.
- Full raw JSON inspection.

---

## 9. Agentic Security SOC
Renders the visual multi-agent workflow:
$$\text{Telemetry} \longrightarrow \text{Integrity Agent} \longrightarrow \text{Temporal Threat Agent} \longrightarrow \text{Master SOC Orchestrator} \longrightarrow \text{Binding Verdict}$$
- **Agent 1**: Kinematic health, geometry health, discard flags.
- **Agent 2**: Multi-epoch persistence streaks, drift classification, detector convergence.
- **Agent 3**: Consensus ratio, conflict resolution, binding DEFCON level, and mitigation directives.

---

## 10. Regulatory RAG Subsystem
- Technical grounding against approved documents: ICAO Annex 10, RTCA DO-229E, CISA PNT Best Practices, MITRE ATT&CK for Space.
- Operator search terminal for ad-hoc technical inquiries.
- Enforces strict architectural invariant: **RAG is contextual only and never overwrites sensor telemetry**.

---

## 11. Final Query / SOC Assistant
Interactive terminal executing natural language security queries:
- `"Why was this event flagged?"`
- `"What features caused the anomaly?"`
- `"Is the anomaly persistent?"`
- `"Show me the evidence behind this alert."`
- `"What did the temporal model detect?"`
- `"Explain the navigation-quality degradation."`
Displays full step-by-step audit: `USER QUERY` $\to$ `LOCUS ANALYSIS` $\to$ `EVIDENCE` $\to$ `AGENT FINDINGS` $\to$ `RAG CONTEXT` $\to$ `FINAL ANSWER`.

---

## 12. System Health Matrix
Audits 14 real pipeline components:
1. 7Semi L89HA Receiver
2. NMEA Sentence Parser
3. Preprocessing & Quality Filters
4. 10-D Security Feature Pipeline
5. Physical Rules Engine
6. Isolation Forest Detector
7. XGBoost Classifier
8. Temporal LSTM Autoencoder
9. Evidence Bundle Repository
10. GNSS Integrity Agent
11. Temporal Threat Agent
12. Master SOC Orchestrator
13. Regulatory RAG Vector Store
14. FastAPI REST Backend

---

## 13. Error Handling & Zero-Fabrication Guarantees
- Gracefully handles disconnected hardware: sets `HISTORICAL / REPLAY MODE` instead of crashing.
- Fallback on missing telemetry: displays `"NO LIVE DATA"` instead of generating mock coordinates.
- Empty dataset handling: returns safe empty states and descriptive warning notices.
- Insufficient RAG context: explicitly notes when no regulatory documents match an inquiry.

---

## 14. Testing & Verification
- Unit & integration tests in `tests/test_gui_integration.py` (15/15 passed).
- Complete test suite in `tests/` (98/98 passed in 9.01s, 100% pass rate).
- Validated REST API endpoints:
  - `GET /api/telemetry/latest`
  - `GET /api/telemetry/history`
  - `GET /api/features/latest`
  - `GET /api/alerts`
  - `GET /api/alerts/{id}`
  - `GET /api/evidence/{id}`
  - `GET /api/agents/status`
  - `POST /api/rag/query`

---

## 15. Deployment Instructions
```bash
# 1. Run the FastAPI REST Backend
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# 2. Launch the Streamlit SOC Dashboard
python -m streamlit run dashboard.py --server.port 8501
```

---

## 16. Limitations
- Physical serial connection depends on platform COM port enumeration (`pyserial`).
- When running in offline or demo environments, historical telemetry replay replaces real-time RF reception.

---

## 17. Future Improvements
- Multi-receiver spatial clustering across synchronized base stations.
- WebSocket streaming for sub-second telemetry broadcast to web clients.
- Automated alert push notifications to external SIEM/Syslog platforms.
