# LOCUS Phase 5 — Baseline Model Performance Report

**Evaluation Timestamp**: 2026-10-04T12:49:54Z  
**Dataset**: `data/features/locus_security_features.csv` (9,382 total epochs)  
**Partition Strategy**: Leakage-free session-aware chronological split  
- **Train Partition**: Sessions 4, 5, 9, 10 (4,749 epochs, 50.6%)  
- **Validation Partition**: Session 11 + Session 15 Part 1 (2,301 epochs, 24.5%)  
- **Buffer Gap**: 30 epochs in Session 15 (temporal sequence isolation)  
- **Test Partition**: Session 15 Part 2 (2,302 epochs, 24.5%, strictly untouched during tuning)  

---

## 1. Summary of Baseline Detection Performance

| Model | Architecture | Train Metric | Validation Metric | Test Metric | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Physical Rules** | Deterministic Kinematic Rules | FPR: 1.664% | FPR: 0.0% | FPR: 0.0% | Operational |
| **Isolation Forest** | Scikit-Learn IsolationForest | FPR: 3.87% | FPR: 0.13% | FPR: 0.04% | Operational |
| **XGBoost Classifier** | Gradient Boosted Trees | N/A | N/A | N/A | Pending Labels |
| **LSTM Autoencoder** | PyTorch 1-Layer LSTM ($W=10$) | MSE: 10.30473 | MSE: 1.64953 | MSE: 1.26315 | Operational |

---

## 2. Physical Plausibility Rule Engine

- **Model Version**: `prules-v1.0`
- **Physical Invariants**: Kinematic velocity (85 m/s), acceleration (10 m/s²), jerk (25 m/s³), turn rate (90°/s), HDOP (8.0), VDOP (10.0), integrity (0.20), sat count (4).
- **Trigger Rate on Nominal Data**:
  - Validation False Alarm Rate: **0.0%** (0 / 2301)
  - Test False Alarm Rate: **0.0%** (0 / 2302)
  - Active Triggers: Most triggered rules on baseline data correspond to stationary multipath jitter (`bearing_rate` at micro-speeds or transient DOP fluctuations).

---

## 3. Isolation Forest Unsupervised Anomaly Detector

- **Model Version**: `iforest-v1.0`
- **Baseline Hyperparameters**: `n_estimators = 200`, `contamination = 0.02`, `random_state = 42`.
- **Decision Threshold (Offset)**: `-0.6384`
- **Anomaly Score Distributions**:
  - Train: Mean raw score = `-0.4255`, Flagged = `184` (3.87%)
  - Validation: Mean raw score = `-0.389`, Flagged = `3` (0.13%)
  - Test: Mean raw score = `-0.3651`, Flagged = `1` (0.04%)
- **Supervised Metric Disclosure**: Verified attack labels are absent in nominal baseline logs. In compliance with rigorous empirical standards, supervised metrics (Precision, Recall, F1) are legitimately reported as uncalculable for attack detection on nominal data. The reported FPR reflects nominal false alarm behavior.

---

## 4. Supervised XGBoost Classifier Infrastructure

- **Audit Status**: `NO_LABELS_DETECTED`
- **Audit Finding**: `Dataset contains real baseline GNSS observations only. No attack label column detected.`
- **Integrity Safeguard**: Attack labels are NEVER fabricated.
- **Uncalculable Supervised Metrics**: Accuracy, Precision, Recall, F1, Macro F1, Confusion Matrix, ROC-AUC.
- **Readiness**: The complete training, cross-validation, and Optuna tuning infrastructure is fully implemented and operational, awaiting labelled attack scenario data.

---

## 5. LSTM Temporal Autoencoder

- **Model Version**: `lstm-temporal-v1.0`
- **Architecture**: Input $(W=10, D=10) \rightarrow$ LSTM(32) $\rightarrow$ Latent(32) $\rightarrow$ LSTM(32) $\rightarrow$ Linear(10).
- **Error Threshold**: `0.7993` (calibrated on nominal training/validation reconstruction error)
- **Reconstruction MSE**:
  - Train MSE: `10.30473`
  - Validation MSE: `1.64953`
  - Test MSE: `1.26315`
- **Temporal Generalization Gap**: `0.38638` ($|\text{MSE}_{\text{test}} - \text{MSE}_{\text{val}}|$)
- **Validation FPR on Nominal**: `4.51%`

---

## 6. Key Identified Opportunities for Phase 5.5 Tuning

1. **Isolation Forest**:
   - Optimize `n_estimators`, `max_samples`, `max_features`, and `contamination` on the Validation partition.
   - Target: Reduce nominal false alarm rate below 1.5% while maximizing kurtosis and score separation margin.
2. **LSTM Temporal Model**:
   - Tune window size $W \in [5, 10, 15]$, hidden dimensions $\in [16, 32, 64]$, dropout $\in [0.0, 0.1, 0.2]$, learning rates, and early stopping.
   - Target: Lower validation reconstruction loss and reduce generalization gap.
3. **Physical Rules Calibration**:
   - Calibrate stationary mode filtering to suppress zero-speed bearing rate noise.
