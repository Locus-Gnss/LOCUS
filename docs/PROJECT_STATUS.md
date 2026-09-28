# LOCUS Project Status Report

**Project Title**: LOCUS (Live Observation, Cybersecurity & Unified Security for GNSS)  
**Repository**: [https://github.com/mahakagrawal7/LOCUS.git](https://github.com/mahakagrawal7/LOCUS.git)  
**Date of Audit**: September 28, 2026  
**Auditor**: Antigravity (AI Pair Programmer)  
**Current Milestone**: Completion of Phases 1 to 5  
**Next Phase**: Phase 6 — 3-Agent Agentic Security SOC  

---

## 1. Executive Summary & Completed Phases

LOCUS has completed Phases 1 through 5 of its end-to-end cyber-physical GNSS defense and threat attribution architecture. All implemented components are verified through automated unit and integration tests (100% pass rate).

| Phase | Description | Status | Verification & Deliverables |
| :--- | :--- | :---: | :--- |
| **Phase 1** | **GNSS Data Collection** | **COMPLETE** | 7Semi L89HA GNSS module + Arduino serial acquisition (115200 baud). 10,938 baseline epochs logged. |
| **Phase 2** | **NMEA Parsing & Preprocessing** | **COMPLETE** | Modular NMEA parser (`src/parsing/`), session boundary detection ($\Delta t > 5.0\text{s}$), atomic UTC reconstruction (`src/locus_quality.py`). Tested in `tests/test_parsing.py` & `tests/test_processing.py`. |
| **Phase 3** | **Structured GNSS Dataset** | **COMPLETE** | Canonical, immutable observation dataset generated: `data/structured/locus_structured_gnss.csv`. Schema defined in `docs/DATA_DICTIONARY.md`. |
| **Phase 4** | **Security Feature Engineering** | **COMPLETE** | Official 10-D security vector computed and validated: `data/features/locus_security_features.csv`. Tested in `tests/test_security_features.py`. |
| **Phase 5** | **Detection & Machine Learning** | **COMPLETE** | 4-detector quad: Physical Rules, Isolation Forest, XGBoost, and LSTM Autoencoder. Structured Evidence Bundles generated in `data/evidence/`. Tested in `tests/test_detection.py`. |
| **Phase 6** | **3-Agent Security SOC** | **NOT STARTED** | Next development milestone. |
| **Phase 7** | **RAG Knowledge Base** | **NOT STARTED** | Future phase. |
| **Phase 8** | **Final Query & SOC Dashboard** | **NOT STARTED** | Future phase. |

---

## 2. End-to-End System Architecture

```
7Semi L89HA (Multi-Constellation GNSS)
       ↓
    Arduino (Serial Bridge @ 115200 baud)
       ↓
   Raw NMEA Sentences (GGA, RMC, GSA, GSV)
       ↓
 NMEA Parsing & Session Segmentation (src/parsing/)
       ↓
 Preprocessing & Atomic UTC Timing (src/locus_quality.py)
       ↓
 Structured GNSS Dataset (data/structured/locus_structured_gnss.csv)
       ↓
 10-D Security Feature Vector (data/features/locus_security_features.csv)
       ↓
 Multi-Detector Quad (src/detection/):
   [1] Physical Plausibility Rules
   [2] Isolation Forest (Unsupervised)
   [3] Supervised XGBoost Infrastructure
   [4] LSTM Sequence Autoencoder (Temporal Dynamics)
       ↓
 Standardized Evidence Bundle (src/evidence/evidence_bundle.py → data/evidence/)
       ↓ [NEXT: Phase 6]
 3-Agent Security SOC Hierarchy:
   • Agent 1: GNSS Integrity Agent
   • Agent 2: Temporal Threat Correlation Agent
   • Agent 3: Master SOC Orchestrator
       ↓ [Future: Phase 7]
 Regulatory RAG Knowledge Base (ICAO, RTCA, CISA, MITRE)
       ↓ [Future: Phase 8]
 Final Query Interface & SOC Dashboard
```

---

## 3. Repository Folder Structure

```
locus_project/
├── README.md                                <- Master project documentation
├── requirements.txt                         <- Python dependencies
├── .gitignore                               <- Version control exclusions
├── .env.example                             <- Environment template
├── locus_collector.py                       <- Legacy monolithic serial collector
├── locus_features.py                        <- Deprecated legacy 10-feature script
├── locus_features_v2.py                     <- Phase 2 clean feature extraction engine
├── locus_quality.py                         <- Phase 2 quality & session segmentation
│
├── docs/                                    <- Architectural & technical documentation
│   ├── PROJECT_STATUS.md                    <- This document
│   ├── ARCHITECTURE.md                      <- Master system architecture
│   ├── IMPLEMENTATION_PROGRESS.md           <- Milestone and commit progress tracking
│   ├── DATA_DICTIONARY.md                   <- Structured observation schema
│   ├── SECURITY_FEATURE_DEFINITIONS.md      <- Official 10-D feature mathematical specs
│   ├── MODEL_CARD.md                        <- Machine learning model specifications
│   ├── DATA_AUDIT.md                        <- Phase 1 raw data defect audit
│   ├── PROCESSING_PIPELINE.md               <- Phase 2 pipeline documentation
│   ├── STRUCTURED_DATASET.md                <- Phase 3 dataset specification
│   ├── DETECTION_MODELS.md                  <- Phase 5 multi-detector & evidence docs
│   └── plots/                               <- Diagnostic visualizations
│
├── src/                                     <- Core framework source code
│   ├── parsing/                             <- NMEA & PRN parsing modules
│   │   ├── nmea_parser.py                   <- Modular sentence extractor
│   │   ├── epoch_aggregator.py              <- 1Hz multi-talker aggregation
│   │   └── preprocessing.py                 <- Data sanitation & session management
│   ├── features/                            <- Security feature extraction
│   │   ├── security_features.py             <- Official 10-D feature engine
│   │   └── generate_validation_plots.py     <- Verification plotting script
│   ├── detection/                           <- Multi-detector anomaly engines
│   │   ├── physical_rules.py                <- Path 1: Newtonian & DOP rule engine
│   │   ├── isolation_forest.py              <- Path 2: Unsupervised spatial detector
│   │   ├── xgboost_detector.py              <- Path 3: Supervised attack classifier
│   │   ├── temporal_model.py                <- Path 4: PyTorch LSTM Autoencoder
│   │   └── pipeline.py                      <- Phase 5 end-to-end training runner
│   └── evidence/                            <- Multi-detector evidence fusion
│       └── evidence_bundle.py               <- Standardized Evidence Bundle generator
│
├── data/                                    <- Data tiers (raw to evidence)
│   ├── raw/                                 <- Preserved raw serial baselines
│   ├── processed/                           <- Cleaned telemetry (locus_telemetry_clean.csv)
│   ├── structured/                          <- Canonical observations (locus_structured_gnss.csv)
│   ├── features/                            <- Security vectors (locus_security_features.csv)
│   └── evidence/                            <- Serialized JSON Evidence Bundles
│
├── models/                                  <- Trained model artifacts
│   ├── isolation_forest.joblib              <- Fitted Scikit-Learn Isolation Forest
│   ├── temporal_model.pt                    <- PyTorch LSTM Autoencoder weights
│   └── temporal_metadata.joblib             <- Temporal scaler & threshold metadata
│
└── tests/                                   <- Automated test suite
    ├── test_parsing.py                      <- Phase 2 NMEA unit tests
    ├── test_processing.py                   <- Phase 2 pipeline integration tests
    ├── test_security_features.py            <- Phase 4 10-D math & dataset tests
    └── test_detection.py                    <- Phase 5 multi-detector & evidence tests
```

---

## 4. Datasets & Model Inventory

### 4.1 Datasets
1. **Raw Telemetry Baseline**: `locus_telemetry_features.csv` (10,938 epochs, 16 raw NMEA fields).
2. **Clean Telemetry**: `data/processed/locus_telemetry_clean.csv` (10,938 epochs partitioned into 15 sessions).
3. **Structured Observation Dataset**: `data/structured/locus_structured_gnss.csv` (10,938 rows, immutable observation tier).
4. **Official Security Features**: `data/features/locus_security_features.csv` (9,382 locked epochs with all 10 security features).

### 4.2 Trained Models
1. **Isolation Forest**: `models/isolation_forest.joblib` (200 trees, 2% contamination, RobustScaler preprocessor).
2. **LSTM Autoencoder**: `models/temporal_model.pt` & `models/temporal_metadata.joblib` (Window size $W=10$, 32 hidden units, session-boundary safe).
3. **Physical Rules Configuration**: `src/detection/physical_rules.py` (Deterministic kinematic and geometric bounds).
4. **XGBoost Classifier Infrastructure**: `src/detection/xgboost_detector.py` (Supervised multi-class attack architecture with strict provenance safeguards).

### 4.3 Phase 5 Outputs
- Over 30 individual Evidence Bundle JSON files generated in `data/evidence/evidence_*.json`.
- Stream evidence artifact: `data/evidence/evidence_stream_sample.jsonl`.
- Diagnostic visualization: `docs/plots/isolation_forest_distribution.png`.

---

## 5. Official 10-D Feature Vector Verification

The repository strictly implements the official 10-dimensional cybersecurity feature vector across all detection engines:
1. `disp_haversine`: Great-circle geodesic displacement (meters).
2. `vel_kinematic`: Coordinate ground velocity ($\text{m/s}$).
3. `acc_kinematic`: Kinematic acceleration ($\text{m/s}^2$).
4. `jerk_kinematic`: Time derivative of acceleration ($\text{m/s}^3$).
5. `bearing_rate`: Normalized circular heading change rate ($\text{deg/s}$, correctly mapping $359^\circ \rightarrow 1^\circ = +2^\circ$).
6. `HDOP`: Horizontal Dilution of Precision.
7. `VDOP`: Vertical Dilution of Precision.
8. `fix_integrity`: Composite fix health index $[0.0, 1.0]$.
9. `sat_count_tot`: Total satellites contributing to 3D navigation solution.
10. `sat_churn`: Set-theoretic satellite constellation turnover rate ($\text{sats/s}$).

---

## 6. Known Limitations

1. **Stationary Baseline Data**: The 10,938 real-world epochs were collected from a fixed stationary rooftop/window mount ($\approx 23.1043^\circ\text{N}, 72.5925^\circ\text{E}$). Velocity, acceleration, and jerk in the baseline reflect receiver noise and multipath rather than vehicular motion.
2. **Historical PRN Tracking**: In the historical 10,938 records, satellite PRN IDs were not recorded by the legacy collector. Consequently, `sat_churn` is cleanly represented as `NaN` (without fabrication), while future runs will leverage the upgraded PRN-aware parser.
3. **No Fabricated Labels**: No synthetic attack labels were fabricated for the real stationary baseline. The XGBoost infrastructure is fully built and tested, reporting `UNFITTED_PENDING_LABELLED_SCENARIOS` until scenario logs are ingested.

---

## 7. Next Phase

**Phase 6: 3-Agent Agentic Security SOC**:
- Agent 1: GNSS Integrity Agent (Physical Rules + Observation Context)
- Agent 2: Temporal & Threat Correlation Agent (Isolation Forest + LSTM Sequence + XGBoost)
- Agent 3: Master SOC Orchestrator (Consensus resolution, DEFCON rating, root-cause attribution, mitigation actions)
