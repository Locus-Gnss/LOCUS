# LOCUS — AI-Powered GNSS Security Monitoring and Detection System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/Phases%201--5-COMPLETE-brightgreen.svg)]()
[![Next Phase](https://img.shields.io/badge/Phase%206-NEXT-orange.svg)]()
[![Tests](https://img.shields.io/badge/Tests-100%25%20Passing-success.svg)]()

---

## 1. Project Overview

**LOCUS** (Live Observation, Cybersecurity & Unified Security for GNSS) is a modular, cyber-physical intrusion detection and threat attribution framework designed to safeguard civil and industrial Global Navigation Satellite System (GNSS) receivers. 

By unifying hardware-level telemetry, multi-sentence NMEA stream processing, Newtonian kinematic constraints, machine learning anomaly detection, and deep temporal modeling, LOCUS defends critical positioning, navigation, and timing (PNT) infrastructure against hostile radio-frequency threats including **spoofing (trajectory injection and drag-off)**, **wideband jamming**, **meaconing/replay**, and **multipath reflections**.

---

## 2. Problem Statement & Objectives

### The Problem
Modern civilian infrastructure—ranging from autonomous transport, maritime shipping, and commercial aviation to electrical power grids and cellular towers—relies unconditionally on civilian GNSS signals (GPS, GLONASS, Galileo, BeiDou). However, civilian GNSS broadcast signals are unencrypted, unauthenticated, and arrive at Earth's surface with extremely low signal power (typically around $-130\text{ dBm}$ to $-160\text{ dBm}$). This makes GNSS receivers acutely vulnerable to:
- **RF Jamming**: High-power noise that suppresses satellite signals, causing receiver starvation and complete loss of lock.
- **GNSS Spoofing**: Transmission of synthetic satellite signals with counterfeit pseudoranges to hijack the receiver's position, velocity, and time (PVT) solution.
- **Cognitive Drag-Off**: Subtle, gradual manipulation of coordinates that evades crude threshold filters by remaining within plausible speed limits while progressively deviating vehicle course.

### Objectives
1. **Decouple Physical Observation from Feature Analysis**: Transform raw serial NMEA stream buffers into standardized, immutable epoch observations.
2. **Physically Grounded 10-D Security Feature Representation**: Formulate a strict 10-dimensional cybersecurity vector capturing Newtonian kinematics, receiver dilution of precision, and constellation dynamics.
3. **Multi-Detector Consensus Defense**: Combine deterministic physical rules, unsupervised spatial isolation forests, supervised classification infrastructure, and deep LSTM autoencoders.
4. **Structured Evidence Generation**: Assemble detector findings into tamper-evident, standardized **Evidence Bundles** ready for autonomous AI SOC investigation and incident response.

---

## 3. Master System Architecture

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
3-Agent Security SOC  (Phase 6 — COMPLETE)
     ↓
      RAG             (Phase 7 — NEXT)
     ↓
  Final Query         (Phase 8 — Future)
```

---

## 4. Current Implementation Status

LOCUS is engineered through an 8-phase developmental lifecycle. **Phases 1 through 6 are fully implemented, verified, and complete.**

| Phase | Phase Title | Status | Scope & Deliverables |
| :---: | :--- | :---: | :--- |
| **Phase 1** | **GNSS Data Collection** | **COMPLETE** | 7Semi L89HA receiver + Arduino serial bridge (115,200 baud). 10,938 baseline epochs logged. |
| **Phase 2** | **NMEA Parsing & Preprocessing** | **COMPLETE** | Modular parsing (`src/parsing/`), session segmentation ($\Delta t > 5.0\text{s}$), atomic UTC reconstruction, GSV multi-constellation fix. |
| **Phase 3** | **Structured GNSS Dataset** | **COMPLETE** | Canonical, immutable observation layer (`data/structured/locus_structured_gnss.csv`). |
| **Phase 4** | **10-D Security Feature Engineering** | **COMPLETE** | Official 10-D vector computation (`src/features/security_features.py` → `data/features/locus_security_features.csv`). |
| **Phase 5** | **Detection & Machine Learning** | **COMPLETE** | Physical Rules + Isolation Forest + XGBoost + LSTM Autoencoder + Evidence Fusion (`data/evidence/`). |
| **Phase 6** | **3-Agent Security SOC** | **COMPLETE** | Autonomous 3-tier agent hierarchy (`src/soc/`): Integrity, Temporal Threat, Master SOC Orchestrator (`data/incidents/`). |
| **Phase 7** | **RAG Knowledge Base** | **NEXT** | Grounding knowledge base (ICAO Annex 10, RTCA DO-229E, CISA, MITRE). |
| **Phase 8** | **Final Query & SOC Dashboard** | **FUTURE** | Interactive SOC query CLI and real-time dashboard. |

---

## 5. Technical Deep-Dive (Phases 1–5)

### 5.1 Hardware & Data Collection (Phase 1)
- **GNSS Module**: 7Semi L89HA featuring Quectel L89 multi-GNSS receiver engine.
- **Constellations Tracked**: GPS, GLONASS, Galileo, BeiDou, and QZSS.
- **Serial Interface**: Arduino hardware serial bridge operating over USB UART @ 115,200 baud, 1 Hz refresh rate.
- **Baseline Dataset**: 10,938 real-world epochs collected from a rooftop/window stationary baseline.

### 5.2 NMEA Parsing & Preprocessing (Phases 2 & 3)
- **Decoupled Architecture**: Individual sentence parsing (`GGA`, `RMC`, `GSA`, `GSV`) decoupled from file writes and serial reading.
- **Session Boundary Segmentation**: Automatic session demarcation using $\Delta t_{\text{PC}} > 5.0\text{ s}$ threshold. All differential features zero-initialized on `epoch_id == 1`, completely eliminating overnight position jump false alarms.
- **Atomic UTC Timing**: Reconstructs atomic UTC ISO-8601 timestamps (`YYYY-MM-DDTHH:MM:SS.sssZ`) by combining receiver local calendar date with GNSS time-of-day.
- **Structured Observation Dataset**: Canonical observation table stored in `data/structured/locus_structured_gnss.csv`.

### 5.3 Official 10-D Security Feature Vector (Phase 4)
The legacy 10 features have been deprecated in favor of the official architecture-defined 10-dimensional cybersecurity vector:

| # | Feature Name | Domain | Formula / Description |
| :-: | :--- | :--- | :--- |
| **1** | `disp_haversine` | Kinematics | Geodesic great-circle distance between consecutive epochs ($m$). |
| **2** | `vel_kinematic` | Kinematics | Ground speed derived from coordinate displacement ($\Delta d / \Delta t$). |
| **3** | `acc_kinematic` | Kinematics | Kinematic acceleration ($\Delta v / \Delta t$). Catches spoofer step jumps. |
| **4** | `jerk_kinematic` | Kinematics | Rate of acceleration change ($\Delta a / \Delta t$). Catches non-smooth trajectory injection. |
| **5** | `bearing_rate` | Kinematics | Normalized circular heading change rate ($^\circ/s$, correctly maps $359^\circ \rightarrow 1^\circ = +2^\circ$). |
| **6** | `HDOP` | Geometry | Horizontal Dilution of Precision (direct receiver measurement). |
| **7** | `VDOP` | Geometry | Vertical Dilution of Precision (direct receiver measurement). |
| **8** | `fix_integrity` | Fix Health | Composite health score: $\text{clip}\left(\frac{\text{fix\_qual} \times \text{avg\_cno}}{\text{PDOP} \times 30.0}, 0.0, 1.0\right)$. |
| **9** | `sat_count_tot` | Satellite Scale | Total satellites used in 3D navigation solution ($S_{\text{used}}$). |
| **10** | `sat_churn` | Constellation | Set-theoretic turnover rate: $\frac{|\text{PRNs}_t \setminus \text{PRNs}_{t-1}| + |\text{PRNs}_{t-1} \setminus \text{PRNs}_t|}{\Delta t}$. |

### 5.4 Multi-Detector Machine Learning Quad & Evidence Fusion (Phase 5)
1. **Physical Plausibility Rules Engine (`src/detection/physical_rules.py`)**:
   Deterministic boundary evaluation grounded in Newtonian physics ($|a| \le 10\text{ m/s}^2$, $|j| \le 25\text{ m/s}^3$, $v \le 85\text{ m/s}$) and antenna geometry ($\text{HDOP} \le 8.0$, $S_{\text{used}} \ge 4$). Output mapped to 4-tier severity levels: `INFO`, `WARNING`, `HIGH`, `CRITICAL`.
2. **Isolation Forest (`src/detection/isolation_forest.py`)**:
   Unsupervised spatial outlier detector trained on 9,382 baseline records (200 trees, 2% contamination) with `RobustScaler` and median imputation. Decision offsets calibrated to a normalized $[0.0, 1.0]$ anomaly score.
3. **Supervised XGBoost Classifier (`src/detection/xgboost_detector.py`)**:
   Multi-class threat classifier infrastructure (Spoofing, Jamming, Meaconing, Multipath). Follows strict empirical provenance: reports `UNFITTED_PENDING_LABELLED_SCENARIOS` on real baseline data until verified attack scenario logs are ingested.
4. **Temporal LSTM Autoencoder (`src/detection/temporal_model.py`)**:
   Sliding sequence window ($W=10$) PyTorch Autoencoder modeling temporal time-series dynamics without cross-session window leakage. Provides per-feature reconstruction error attribution.
5. **Evidence Fusion Engine (`src/evidence/evidence_bundle.py`)**:
   Aggregates raw coordinates, quality flags, and outputs from all 4 detection paths into standardized, immutable JSON Evidence Bundles stored in `data/evidence/`.

---

## 6. Repository Layout

```
LOCUS/
├── README.md                                <- Master project documentation
├── requirements.txt                         <- Python dependencies
├── .gitignore                               <- Git exclusion rules
├── .env.example                             <- Environment configuration template
│
├── docs/                                    <- Architectural & technical documentation
│   ├── PROJECT_STATUS.md                    <- Detailed project status audit
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
│   ├── parsing/                             <- NMEA sentence parsing & aggregation
│   │   ├── nmea_parser.py                   <- Sentence extractor
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
│   │   └── pipeline.py                      <- Phase 5 training & fusion runner
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
└── tests/                                   <- Automated test suite (100% passing)
    ├── test_parsing.py                      <- Phase 2 NMEA unit tests
    ├── test_processing.py                   <- Phase 2 pipeline integration tests
    ├── test_security_features.py            <- Phase 4 10-D math & dataset tests
    └── test_detection.py                    <- Phase 5 multi-detector & evidence tests
```

---

## 7. Technology Stack

- **Languages**: Python 3.10+
- **Machine Learning & Deep Learning**: PyTorch (`torch`), Scikit-Learn (`scikit-learn`), XGBoost (`xgboost`)
- **Numerical & Data Processing**: NumPy, Pandas, SciPy, Joblib
- **Visualization**: Matplotlib, Seaborn
- **GNSS & Serial Communication**: PySerial, PyNMEA2
- **Testing**: Python `unittest` suite (31 automated unit and integration tests)

---

## 8. Installation & Quickstart

### Prerequisites
- Python 3.10 or higher
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/mahakagrawal7/LOCUS.git
cd LOCUS

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Verification Tests
Execute the full automated test suite covering Phases 1–6:
```bash
python -m unittest tests.test_parsing tests.test_processing tests.test_security_features tests.test_detection tests.test_soc_agents
```

### Running Phase 5 Multi-Detector Training & Evidence Generation
```bash
python -m src.detection.pipeline
```

### Running Phase 6 3-Agent Security SOC Pipeline
```bash
python -m src.soc.soc_pipeline
```

---

## 9. Known Limitations

1. **Stationary Baseline Data**: The 10,938 real-world baseline epochs were collected from a fixed stationary mount ($\approx 23.1043^\circ\text{N}, 72.5925^\circ\text{E}$). Kinematic acceleration and jerk reflect receiver noise and multipath rather than vehicle motion.
2. **Historical PRN Tracking**: In the historical 10,938 records, individual satellite PRN/IDs were not logged by the legacy collector. Consequently, `sat_churn` is cleanly represented as `NaN` (without fabrication), while future runs leverage the upgraded PRN-aware parser.
3. **Empirical Label Integrity**: In strict adherence to scientific integrity, attack labels are never fabricated. Supervised XGBoost models remain unfitted until real or simulated scenario attack logs are ingested.

---

## 10. Future Phases

- **Phase 7: Regulatory RAG Knowledge Base (NEXT)**
  Vectorized grounding knowledge base linking detected anomalies directly to ICAO Annex 10, RTCA DO-229E (RAIM FDE), CISA PNT Guidelines, and MITRE ATT&CK for Space.
- **Phase 8: Final Query Interface & Real-Time SOC Dashboard**
  Interactive command-line query engine and live dashboard for security operations center analysts.
