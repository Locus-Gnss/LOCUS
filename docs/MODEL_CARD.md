# LOCUS Model Cards — Phase 5 Detection Engines

This document provides formal model cards for the machine learning models and detection engines deployed in LOCUS Phase 5.

---

## 1. Physical Plausibility Rules Engine

- **Model Type**: Expert Knowledge & Kinematic Rules Engine
- **Module**: `src/detection/physical_rules.py`
- **Inputs**: Official 10-D Security Feature Vector
- **Output**: Deterministic violation flags, triggered rules, and 4-tier severity rating (`INFO`, `WARNING`, `HIGH`, `CRITICAL`).
- **Key Parameters**:
  - Max acceleration: $10.0\text{ m/s}^2$ (Critical), $4.0\text{ m/s}^2$ (Warning)
  - Max jerk: $25.0\text{ m/s}^3$ (Critical), $12.0\text{ m/s}^3$ (Warning)
  - Max velocity: $85.0\text{ m/s}$ (Critical), $50.0\text{ m/s}$ (Warning)
  - Max HDOP: $8.0$ (Critical), $4.0$ (Warning)
  - Min satellites: $4$ (Critical), $6$ (Warning)
- **Strengths**: Deterministic, zero false positives on known physics, instant execution time (< 0.1 ms).
- **Limitations**: Incapable of detecting stealthy, slowly-deviating spoofing attacks that stay within nominal kinematic bounds.

---

## 2. Isolation Forest Unsupervised Anomaly Detector

- **Model Type**: Ensemble Tree-Based Outlier Detection
- **Framework**: Scikit-Learn (`sklearn.ensemble.IsolationForest`)
- **Module**: `src/detection/isolation_forest.py`
- **Artifact**: `models/isolation_forest.joblib`
- **Training Data**: 9,382 locked baseline epochs from `data/features/locus_security_features.csv`.
- **Feature Vector**: All 10 dimensions of the official security feature vector.
- **Preprocessing**: Median Imputer (fill missing `sat_churn` with median) + `RobustScaler` (median-centered, IQR-scaled).
- **Hyperparameters**:
  - `n_estimators`: 200
  - `contamination`: 0.02 (2% assumed baseline anomaly rate)
  - `random_state`: 42
- **Scoring**: Raw `score_samples()` mapped to normalized $[0.0, 1.0]$ anomaly score via calibrated logistic sigmoid centered at decision boundary offset.
- **Strengths**: Excels at detecting unexpected, multi-dimensional correlations without requiring attack labels.

---

## 3. Supervised XGBoost Attack Classifier Infrastructure

- **Model Type**: Gradient Boosted Decision Trees (GBDT)
- **Framework**: XGBoost (`xgboost.XGBClassifier`)
- **Module**: `src/detection/xgboost_detector.py`
- **Taxonomy**:
  - `0`: Benign Nominal GNSS
  - `1`: Trajectory Injection / Spoofing
  - `2`: Wideband RF Jamming / Starvation
  - `3`: Meaconing / Replay Takeover
  - `4`: Multipath / Urban Reflection
- **Current Operational Status**: Infrastructure fully verified and tested. In adherence to cybersecurity provenance standards, no synthetic labels were fabricated for the real stationary baseline. The model reports `UNFITTED_PENDING_LABELLED_SCENARIOS` until scenario data is ingested.
- **Features**: 10-D Security Feature Vector with SimpleImputer and RobustScaler.

---

## 4. LSTM Temporal Sequence Autoencoder

- **Model Type**: Deep Recurrent Neural Network (LSTM Autoencoder)
- **Framework**: PyTorch (`torch.nn.LSTM`)
- **Module**: `src/detection/temporal_model.py`
- **Artifacts**:
  - Model weights: `models/temporal_model.pt`
  - Scaler & threshold metadata: `models/temporal_metadata.joblib`
- **Architecture**:
  - Input: Sequence window of shape $(W=10, D=10)$
  - Encoder: 1-layer LSTM ($10 \rightarrow 32$ hidden units)
  - Latent Bottleneck: 32-dimensional sequential context representation
  - Decoder: 1-layer LSTM ($32 \rightarrow 32$ hidden units) followed by Linear projection ($32 \rightarrow 10$)
- **Training Details**:
  - Sequence generation strictly respects session boundaries (zero cross-session windowing)
  - Chronological 80/20 train/validation split
  - Loss: Mean Squared Error (MSE)
  - Optimizer: Adam ($\text{lr} = 0.002$)
  - Epochs: 15
- **Inference & Attribution**:
  - Reconstruction error computed across sequence window
  - Per-feature MSE extracted to pinpoint exactly which physical dimensions failed temporal reconstruction (e.g. velocity drift vs. DOP spike).
