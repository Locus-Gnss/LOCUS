# LOCUS Master System Architecture

**Project Title**: LOCUS (Live Observation, Cybersecurity & Unified Security for GNSS)  
**System Flow**: End-to-End Cyber-Physical GNSS Defense Pipeline  

---

## 1. Architectural Flowchart

```
7Semi L89HA
     ↓
  Arduino
     ↓
 Raw NMEA
     ↓
NMEA Parsing
     ↓
Preprocessing
     ↓
Structured GNSS Dataset
     ↓
10-D Security Feature Vector
     ↓
Physical Rules
       +
Isolation Forest
       +
    XGBoost
       +
   LSTM/TCN
     ↓
Evidence Bundle
     ↓
3-Agent Security SOC  (Phase 6 - Next)
     ↓
      RAG             (Phase 7 - Future)
     ↓
  Final Query         (Phase 8 - Future)
```

---

## 2. Detailed Pipeline Stages

### Stage 1: Hardware Acquisition
- **Receiver**: 7Semi L89HA module containing the Quectel L89 multi-constellation GNSS engine (GPS, GLONASS, Galileo, BeiDou, QZSS).
- **Interface**: Microcontroller serial bridge (Arduino) operating over USB UART @ 115,200 baud, 1 Hz refresh rate.
- **Output**: Raw NMEA-0183 standard sentences (`$GNGGA`, `$GNRMC`, `$GNGSA`, `$GPGSV`, `$GLGSV`, `$GAGSV`, `$GBGSV`).

### Stage 2: NMEA Parsing & Preprocessing
- **Modular Parsing (`src/parsing/nmea_parser.py`)**: Individual sentence decoders extracting navigation fix quality, latitude, longitude, altitude, ground speed, course, dilution of precision (PDOP, HDOP, VDOP), and satellite signal strength ($C/N_0$).
- **Epoch Aggregator (`src/parsing/epoch_aggregator.py`)**: Aggregates multi-sentence talkers across 1-second epochs into unified records.
- **Session Segmentation & Timing (`src/locus_quality.py`)**: Identifies hardware cold starts and collection breaks ($\Delta t > 5.0\text{ s}$), resets differential features across session boundaries, and reconstructs atomic UTC timestamps (`YYYY-MM-DDTHH:MM:SS.sssZ`).

### Stage 3: Structured GNSS Dataset
- **Canonical Layer (`data/structured/locus_structured_gnss.csv`)**:
  - Decoupled, immutable observation tier separating low-level ingestion from downstream ML.
  - Standardized schema: Session ID, Epoch ID, Atomic UTC, WGS-84 Coordinates, DOP metrics, satellite counts, C/N0 statistics, and data quality flags (`FIX_VALID`, `DEGRADED_GEOMETRY`, `COLD_START`).

### Stage 4: 10-D Security Feature Vector
- **Feature Extractor (`src/features/security_features.py`)**:
  Computes the official 10-dimensional cybersecurity vector structured across three physical domains:
  1. `disp_haversine`: Great-circle geodesic displacement ($m$).
  2. `vel_kinematic`: Coordinate ground velocity ($m/s$).
  3. `acc_kinematic`: Kinematic acceleration ($m/s^2$).
  4. `jerk_kinematic`: Rate of acceleration change ($m/s^3$).
  5. `bearing_rate`: Normalized circular heading change rate ($^\circ/s$, handling $359^\circ \rightarrow 1^\circ$).
  6. `HDOP`: Horizontal Dilution of Precision.
  7. `VDOP`: Vertical Dilution of Precision.
  8. `fix_integrity`: Composite fix health index $[0.0, 1.0]$.
  9. `sat_count_tot`: Total satellites contributing to 3D navigation solution.
  10. `sat_churn`: Set-theoretic satellite constellation turnover rate ($sats/s$).

### Stage 5: Multi-Detector Quad & Evidence Fusion
- **Detector 1: Physical Rules Engine (`src/detection/physical_rules.py`)**:
  Deterministic hard boundaries derived from Newtonian physics ($|a| \le 10\text{ m/s}^2$, $|j| \le 25\text{ m/s}^3$, $v \le 85\text{ m/s}$) and geometric dilution ($\text{HDOP} \le 8.0$, $S_{\text{used}} \ge 4$).
- **Detector 2: Isolation Forest (`src/detection/isolation_forest.py`)**:
  Unsupervised spatial anomaly detector trained on baseline features, mapping raw decision offsets onto calibrated $[0.0, 1.0]$ anomaly scores via RobustScaler and median imputation.
- **Detector 3: Supervised XGBoost Classifier (`src/detection/xgboost_detector.py`)**:
  Multi-class attack classification infrastructure (Spoofing, Jamming, Meaconing, Multipath) with strict empirical provenance safeguards.
- **Detector 4: LSTM Autoencoder (`src/detection/temporal_model.py`)**:
  Sliding sequence window ($W=10$) PyTorch Autoencoder modeling temporal dynamics without cross-session data leakage, providing per-feature error attribution.
- **Evidence Fusion Engine (`src/evidence/evidence_bundle.py`)**:
  Fuses detector outputs, physical evaluations, raw observations, and data quality context into structured, immutable JSON Evidence Bundles.

---

## 3. Downstream Roadmap (Phases 6–8)

### Stage 6: 3-Agent Security SOC (Phase 6 - Next)
Consumes Evidence Bundles through a 3-agent hierarchy:
- **Agent 1 (Integrity Agent)**: Evaluates single-epoch physical validity and receiver geometry.
- **Agent 2 (Temporal Threat Agent)**: Tracks anomaly persistence and correlates IForest and LSTM reconstruction errors.
- **Agent 3 (Master SOC Orchestrator)**: Resolves consensus, assigns DEFCON severity levels, classifies attack vectors, and issues actionable mitigation directives.

### Stage 7: Regulatory RAG Knowledge Base (Phase 7 - Future)
Grounded retrieval engine linking detected incidents directly to international standards (ICAO Annex 10, RTCA DO-229E RAIM, CISA PNT Guidelines, MITRE ATT&CK for Space).

### Stage 8: Final SOC Query & Dashboard Interface (Phase 8 - Future)
Interactive operator CLI and real-time SOC dashboard for incident triage, timeline investigation, and threat monitoring.
