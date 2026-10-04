# LOCUS — AI-Powered GNSS Security Monitoring and Detection System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/Phases%201--5.5-COMPLETE-brightgreen.svg)]()
[![Phase 6 Status](https://img.shields.io/badge/Phase%206-READY-blue.svg)]()
[![Tests](https://img.shields.io/badge/Tests-49%20Passing%20(100%25)-success.svg)]()

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
4. **Model Optimization & Leakage Elimination (Phase 5.5)**: Systematically tune hyperparameters using leakage-free chronological partitioning and calibrate physical invariant thresholds.
5. **Structured Evidence Generation**: Assemble detector findings into tamper-evident, standardized **Evidence Bundles** ready for autonomous AI SOC investigation and incident response.

---

## 3. Master System Architecture

```
7Semi L89HA Receiver
     ↓
Arduino Microcontroller
     ↓
Raw NMEA Stream
     ↓
NMEA Parsing & Temporal Preprocessing
     ↓
Structured GNSS Dataset (locus_structured_gnss.csv)
     ↓
10-D Security Feature Vector (locus_security_features.csv)
     ↓
Phase 5.5 Multi-Detector Quad (Production Models):
  ├── Physical Rules Engine (prules-v1.1)
  ├── Isolation Forest (iforest-tuned-v1.1, n=150, contam=0.01)
  ├── XGBoost Supervised Infrastructure (xgb-ready-v1.1)
  └── LSTM Temporal Autoencoder (lstm-temporal-tuned-v1.1, H=64)
     ↓
Evidence Fusion Engine (evidence_*.json)
     ↓
READY FOR PHASE 6 (Agentic Security SOC)
```

### Technology Stack
- **Languages**: Python 3.10+
- **Machine Learning & Deep Learning**: PyTorch (`torch`), Scikit-Learn (`scikit-learn`), XGBoost (`xgboost`)
- **Numerical & Data Processing**: NumPy, Pandas, SciPy, Joblib
- **Testing**: Python `pytest` & `unittest` suite (49 automated unit and integration tests passing 100%)

---

## 4. Installation & Quickstart

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
