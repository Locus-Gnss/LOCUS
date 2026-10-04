# LOCUS Model Cards — Phase 5.5 Production Detection Engines

This document provides formal model cards for the fine-tuned, optimized, and validated machine learning models and deterministic engines deployed in **LOCUS Phase 5.5**.

All models operate strictly on the official **10-D GNSS Security Feature Vector**:
`disp_haversine`, `vel_kinematic`, `acc_kinematic`, `jerk_kinematic`, `bearing_rate`, `HDOP`, `VDOP`, `fix_integrity`, `sat_count_tot`, `sat_churn`.

---

## 1. Physical Plausibility Rules Engine

- **Model Tier**: **PRODUCTION** (`prules-v1.1`) | Baseline: `prules-v1.0`
- **Model Type**: Deterministic Kinematic Invariant & Physics Boundary Engine
- **Module**: [`src/detection/physical_rules.py`](../src/detection/physical_rules.py)
- **Inputs**: Official 10-D Security Feature Vector
- **Output**: Structured evaluation per rule, triggered violation list, and 4-tier severity rating (`INFO`, `WARNING`, `HIGH`, `CRITICAL`).
- **Calibrated Production Thresholds**:
  - Kinematic Acceleration: Warning $4.0\text{ m/s}^2$, Critical $10.0\text{ m/s}^2$ ($|a|$ magnitude)
  - Kinematic Jerk: Warning $15.0\text{ m/s}^3$, Critical $25.0\text{ m/s}^3$ ($|j|$ magnitude)
  - Ground Speed: Warning $50.0\text{ m/s}$, Critical $85.0\text{ m/s}$
  - Single-Epoch Displacement: Warning $50.0\text{ m}$, Critical $100.0\text{ m}$
  - Angular Turn Rate: $90.0^\circ/\text{s}$ (conditioned on $v \ge 2.0\text{ m/s}$ to filter micro-speed jitter)
  - HDOP / VDOP: Warning $4.0$ / $5.0$, Critical $8.0$ / $10.0$
  - Fix Integrity: Warning $< 0.45$, Critical $< 0.20$
  - Satellite Count: Warning $< 6$, Critical $< 4$ satellites
- **Performance**:
  - Validation Nominal False Alarm Rate: **0.00%**
  - Held-out Test Nominal False Alarm Rate: **0.00%**
  - Latency: $< 0.005\text{ ms}$/epoch
- **Strengths**: Zero false positives on nominal physics, instantaneous execution, 100% deterministic explainability.
- **Limitations**: Cannot detect slow, continuous coordinate drift below physical velocity limits.

---

## 2. Isolation Forest Unsupervised Anomaly Detector

- **Model Tier**: **PRODUCTION** (`iforest-tuned-v1.1`) | Baseline: `iforest-v1.0`
- **Model Type**: Ensemble Density & Tree-Based Outlier Detection
- **Framework**: Scikit-Learn (`sklearn.ensemble.IsolationForest`)
- **Module**: [`src/detection/isolation_forest.py`](../src/detection/isolation_forest.py)
- **Artifacts**:
  - Production Artifact: [`models/production/isolation_forest/isolation_forest.joblib`](../models/production/isolation_forest/isolation_forest.joblib)
  - Tuned Artifact: [`models/isolation_forest/isolation_forest_tuned.joblib`](../models/isolation_forest/isolation_forest_tuned.joblib)
  - Experimental Baseline: [`models/experiments/isolation_forest_baseline.joblib`](../models/experiments/isolation_forest_baseline.joblib)
- **Training Protocol**:
  - Partition: Fit strictly on Train partition ($N=4,749$ epochs from Sessions 4, 5, 9, 10).
  - Scaler / Imputer: `RobustScaler` (median-centered, IQR-scaled) fit strictly on Train split. Non-finites sanitized to NaN.
- **Optimized Hyperparameters**:
  - `n_estimators`: 150 (tuned down from baseline 200 for lower latency and peak score contrast)
  - `max_samples`: 256
  - `max_features`: 1.0 (all 10 security features)
  - `contamination`: 0.01 (calibrated to 1% baseline outlier ceiling)
  - `random_state`: 42
- **Scoring & Performance**:
  - Sigmoid-calibrated anomaly score $[0.0, 1.0]$ centered at model offset.
  - Decision Offset: `-0.6462`
  - Score Margin: `0.2570` (25% improvement over baseline `0.2055`)
  - Validation Nominal False Positive Rate: **0.00%** (0 / 2,301 epochs)
  - Held-Out Test Nominal False Positive Rate: **0.00%** (0 / 2,302 epochs)
  - Inference Latency: $0.021\text{ ms}$/epoch

---

## 3. Supervised XGBoost Attack Classifier Infrastructure

- **Model Tier**: **PRODUCTION WRAPPER & AUDITED INFRASTRUCTURE** (`xgb-ready-v1.1`)
- **Model Type**: Extreme Gradient Boosted Decision Trees (XGBoost)
- **Module**: [`src/detection/xgboost_detector.py`](../src/detection/xgboost_detector.py)
- **Artifacts**: [`models/production/xgboost/`](../models/production/xgboost/)
- **Target Threat Taxonomy**:
  - `0`: Benign Nominal GNSS
  - `1`: Trajectory Injection / Spoofing
  - `2`: Wideband RF Jamming / Starvation
  - `3`: Meaconing / Replay Takeover
  - `4`: Multipath / Urban Reflection
- **Provenance Safeguard & Audit**:
  - Real-world baseline GNSS data contains no verified attack labels.
  - In strict compliance with scientific honesty, **no fake spoofing/jamming labels were fabricated**.
  - Status is cleanly reported as: `UNFITTED_PENDING_LABELLED_SCENARIOS`.
  - Supervised metrics (Accuracy, F1, ROC-AUC) are legitimately reported as uncalculable for unlabelled nominal data.
- **Search & Optimization Infrastructure**:
  - Validated Optuna / RandomizedSearch search space across `n_estimators` [100-300], `max_depth` [3-6], `learning_rate` [0.01-0.1], `subsample` [0.7-0.9], `colsample_bytree` [0.7-0.9], `reg_alpha`, `reg_lambda`.

---

## 4. LSTM Temporal Sequence Autoencoder

- **Model Tier**: **PRODUCTION** (`lstm-temporal-tuned-v1.1`) | Baseline: `lstm-temporal-v1.0`
- **Model Type**: Deep Recurrent Neural Network (LSTM Autoencoder)
- **Framework**: PyTorch (`torch.nn.LSTM`)
- **Module**: [`src/detection/temporal_model.py`](../src/detection/temporal_model.py)
- **Artifacts**:
  - Production Weights: [`models/production/temporal/temporal_model.pt`](../models/production/temporal/temporal_model.pt)
  - Production Metadata: [`models/production/temporal/temporal_metadata.joblib`](../models/production/temporal/temporal_metadata.joblib)
  - Experimental Baseline: [`models/experiments/temporal_model_baseline.pt`](../models/experiments/temporal_model_baseline.pt)
- **Architecture**:
  - Input: Sliding sequence window of shape $(W=10, D=10)$
  - Encoder: 1-layer LSTM ($10 \rightarrow 64$ hidden units)
  - Latent Representation: 64-dimensional context vector
  - Decoder: 1-layer LSTM ($64 \rightarrow 64$) followed by Linear projection ($64 \rightarrow 10$)
- **Training Details**:
  - Strict session boundary preservation: sliding windows never cross session borders.
  - 30-epoch buffer gap between Validation and Test segments in Session 15.
  - Optimizer: Adam ($\text{lr} = 0.001$, weight decay $1\times 10^{-5}$)
  - Early stopping patience: 4 epochs on Validation Loss
- **Performance**:
  - Validation MSE: **1.3979** (15.3% reduction vs baseline 1.6495)
  - Held-out Test MSE: **0.8571** (32.1% reduction vs baseline 1.2631)
  - Calibrated Error Threshold: `1.4434`
  - Held-out Test Nominal False Alarm Rate: **0.87%** (down from baseline 2.05%)
  - Inference Latency: $0.082\text{ ms}$/window

---

## 5. Model Tier Taxonomy Summary

| Path | Baseline (Phase 5) | Tuned (Phase 5.5) | Production Deployed |
| :--- | :--- | :--- | :--- |
| **Physical Rules** | `prules-v1.0` | `prules-v1.1` | **`prules-v1.1`** |
| **Isolation Forest** | `iforest-v1.0` | `iforest-tuned-v1.1` | **`models/production/isolation_forest/`** |
| **XGBoost Classifier** | `xgb-v1.0` | `xgb-ready-v1.1` | **`models/production/xgboost/`** |
| **Temporal LSTM** | `lstm-temporal-v1.0` | `lstm-temporal-tuned-v1.1` | **`models/production/temporal/`** |
