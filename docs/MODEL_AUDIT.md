# LOCUS Phase 5 — Model Architecture & Data Leakage Audit

**Audit Date**: October 2026  
**Audited Target**: LOCUS Phase 5 Detection & ML Pipeline (`src/detection/`, `src/evidence/`, `models/`)  
**Pipeline Components**: Physical Plausibility Rule Engine, Isolation Forest, XGBoost Classifier, LSTM Autoencoder, Evidence Fusion  
**Feature Space**: Official 10-D Security Feature Vector  

---

## 1. Executive Summary

This audit rigorously inspects the machine learning and deterministic detection components delivered in **LOCUS Phase 5** prior to embarking on **Phase 5.5 (Model Fine-Tuning and Optimization)**.

The audit identifies:
1. The mathematical and structural properties of the current 4 detector paths.
2. The current hyperparameter baselines.
3. Preprocessing, scaling, and sequence generation mechanisms.
4. Validation and testing practices, uncovering critical **data leakage** vulnerabilities.
5. Actionable remediation and optimization strategies for Phase 5.5.

---

## 2. Component-by-Component Architectural Inspection

### 2.1 Official 10-Dimensional Security Feature Vector
All models in LOCUS are bound to the strictly governed 10-D security vector defined in [`docs/SECURITY_FEATURE_DEFINITIONS.md`](SECURITY_FEATURE_DEFINITIONS.md):
1. `disp_haversine`: Great-circle epoch displacement (meters).
2. `vel_kinematic`: Kinematic velocity derived from consecutive positions (m/s).
3. `acc_kinematic`: Kinematic acceleration ($dv/dt$) (m/s²).
4. `jerk_kinematic`: Kinematic jerk ($da/dt$) (m/s³).
5. `bearing_rate`: Absolute heading turn rate ($d\theta/dt$) (deg/s).
6. `HDOP`: Horizontal Dilution of Precision.
7. `VDOP`: Vertical Dilution of Precision.
8. `fix_integrity`: Composite navigation fix health metric $[0.0, 1.0]$.
9. `sat_count_tot`: Total satellites tracked in fix.
10. `sat_churn`: Satellite constellation PRN turnover rate $[0.0, 1.0]$.

*Audit Check*: No feature substitutions, additions, or deletions are permitted. All models and preprocessors strictly preserve this 10-D vector.

---

### 2.2 Physical Plausibility Rule Engine
- **Implementation File**: [`src/detection/physical_rules.py`](../src/detection/physical_rules.py)
- **Role**: Deterministic physics-based invariant checker. This is **not an ML model** and must not be treated with statistical fitting; rather, it requires threshold calibration based on physical kinematics and sensor noise envelopes.
- **Current Hyperparameters / Configured Thresholds**:
  | Rule ID | Feature Evaluated | Warning Threshold | Critical Threshold | Physical Justification |
  | :--- | :--- | :--- | :--- | :--- |
  | `PR_ACC_001/002` | `acc_kinematic` | $4.0\text{ m/s}^2$ | $10.0\text{ m/s}^2$ | Terrestrial vehicle acceleration limit ($\approx 1.0g$) |
  | `PR_JERK_001/002`| `jerk_kinematic` | $12.0\text{ m/s}^3$ | $25.0\text{ m/s}^3$ | Drivetrain & suspension jerk limits |
  | `PR_VEL_001/002` | `vel_kinematic` | $50.0\text{ m/s}$ | $85.0\text{ m/s}$ | Terrestrial highway limit vs aircraft speed ($>306\text{ km/h}$) |
  | `PR_DISP_001/002`| `disp_haversine` | $50.0\text{ m}$ | $100.0\text{ m}$ | Coordinate jump per 1 Hz epoch |
  | `PR_BEAR_001` | `bearing_rate` | $90.0^\circ/\text{s}$ (if $v \ge 2.0\text{ m/s}$) | N/A | Steering geometry bound at speed |
  | `PR_HDOP_001/002`| `HDOP` | $4.0$ | $8.0$ | Horizontal geometric dilution severity |
  | `PR_VDOP_001/002`| `VDOP` | $5.0$ | $10.0$ | Vertical geometric dilution severity |
  | `PR_INT_001/002` | `fix_integrity` | $< 0.50$ | $< 0.20$ | Minimum navigation solution integrity |
  | `PR_SAT_001/002` | `sat_count_tot` | $< 6$ sats | $< 4$ sats | 3D mathematical trilateration minimum |
  | `PR_CHURN_001/002`| `sat_churn` | $> 0.35$ ($35\%$) | $> 0.60$ ($60\%$) | Constellation orbital turnover ceiling |
  | `PR_VEL_STAT` | `vel_kinematic` | $3.0\text{ m/s}$ (stat mode) | N/A | Stationary receiver pseudorange drift limit |

---

### 2.3 Isolation Forest Anomaly Detector
- **Implementation File**: [`src/detection/isolation_forest.py`](../src/detection/isolation_forest.py)
- **Model Artifact**: [`models/isolation_forest.joblib`](../models/isolation_forest.joblib)
- **Role**: Unsupervised multi-dimensional density-based outlier detection across the 10-D security space.
- **Current Hyperparameters**:
  - `n_estimators`: 200
  - `contamination`: 0.02 ($2.0\%$)
  - `max_samples`: 'auto' ($256$ in Scikit-Learn)
  - `max_features`: 1.0 ($10$ features)
  - `random_state`: 42
  - `n_jobs`: 1
- **Preprocessing Pipeline**:
  - `SimpleImputer(strategy="median", fill_value=0.0)`: Imputes unlogged features such as `sat_churn` where PRN tracking was unavailable in historical data.
  - `RobustScaler()`: Centers on median and scales by Interquartile Range (IQR), guarding against outlier distortion.
  - Normalized Anomaly Calibration: Sigmoid mapping around model offset:
    $$\text{score} = \frac{1}{1 + e^{-15 \cdot (\text{raw\_offset\_} - s_{\text{raw}})}}$$

---

### 2.4 XGBoost Supervised Attack Classifier
- **Implementation File**: [`src/detection/xgboost_detector.py`](../src/detection/xgboost_detector.py)
- **Role**: Supervised classification infrastructure for mapping multi-dimensional feature deviations to explicit attack taxonomy (Spoofing, Jamming, Replay, Multipath).
- **Current Hyperparameters**:
  - `max_depth`: 5
  - `n_estimators`: 200
  - `learning_rate`: 0.05
  - `subsample`: 0.8
  - `colsample_bytree`: 0.8
  - `random_state`: 42
  - `eval_metric`: `"logloss"`
  - `use_label_encoder`: False
- **Current Status**:
  - Evaluated on `data/features/locus_security_features.csv`.
  - The dataset consists entirely of empirical stationary baseline GNSS logs without synthetic or fabricated attack labels.
  - Status is cleanly reported as: `UNFITTED_PENDING_LABELLED_SCENARIOS`.
  - Strict cybersecurity integrity safeguard: Verified attack labels are **never hallucinated or manufactured out of thin air**.

---

### 2.5 LSTM Temporal Sequence Model
- **Implementation File**: [`src/detection/temporal_model.py`](../src/detection/temporal_model.py)
- **Model Artifacts**: [`models/temporal_model.pt`](../models/temporal_model.pt), [`models/temporal_metadata.joblib`](../models/temporal_metadata.joblib)
- **Role**: Sequence-to-sequence autoencoding of temporal windows to detect kinematic discontinuities, creeping drift, and sudden temporal disruptions.
- **Current Hyperparameters**:
  - `window_size`: 10 epochs (10 seconds at 1 Hz)
  - `input_dim`: 10
  - `hidden_dim`: 32
  - `num_layers`: 1
  - `epochs`: 15
  - `batch_size`: 64
  - `lr`: 0.002
  - `weight_decay`: 1e-5
  - `val_split`: 0.20
  - `error_threshold`: 98th percentile of validation reconstruction MSE ($\text{mean} + 3\sigma$)
- **Sequence Generation Principle**:
  - Sliding windows are strictly constrained within session boundaries (`group.groupby("session_id")`).
  - Windows NEVER cross session borders. Sessions shorter than 10 epochs (e.g., Session 9, $N=8$) are skipped.

---

### 2.6 Evidence Bundle Fusion Engine
- **Implementation File**: [`src/evidence/evidence_bundle.py`](../src/evidence/evidence_bundle.py)
- **Role**: Aggregates physical rule evaluations, Isolation Forest anomaly scores, XGBoost predictions, and LSTM reconstruction error vectors into an immutable JSON container.
- **Output Artifacts**: Sample bundles in [`data/evidence/`](../data/evidence/).
- **Audit Finding**: Currently, the Evidence Bundle records `model_versions` as string literals (e.g. `iforest-v1.0`, `prules-v1.0`, `lstm-temporal-v1.0`). To support Phase 5.5 production deployment, the bundle schema must be augmented with:
  - `model_version`: Distinguishing baseline vs tuned vs production models.
  - `model_training_date`: Timestamp of training/calibration run.
  - `feature_schema_version`: Guaranteeing 10-D schema compliance.

---

## 3. Data Audit & Partitioning Analysis

### 3.1 Training Data Profile
- Source: [`data/features/locus_security_features.csv`](../data/features/locus_security_features.csv)
- Total Epochs: 9,382 rows $\times$ 17 columns (10 security features + 7 metadata/positional fields).
- Session Distribution:
  | Session ID | Epoch Count | Share (%) | Duration | Note |
  | :--- | :--- | :--- | :--- | :--- |
  | Session 4 | 236 | 2.52% | ~3.9 min | Early baseline session |
  | Session 5 | 993 | 10.58% | ~16.5 min | Clean nominal tracking |
  | Session 9 | 8 | 0.09% | 8 sec | Truncated session ($N < 10$) |
  | Session 10 | 3,512 | 37.43% | ~58.5 min | Extensive stationary tracking |
  | Session 11 | 31 | 0.33% | 31 sec | Short baseline check |
  | Session 15 | 4,602 | 49.05% | ~76.7 min | Primary contiguous stationary run |
  | **Total** | **9,382** | **100.0%** | **~2.6 hours** | All baseline nominal GNSS |

---

## 4. Identification of Data Leakage & Methodological Vulnerabilities

The audit reveals four critical methodological flaws in the Phase 5 baseline implementation:

### Flaw 1: Absence of a Dedicated Held-Out Test Set
- **Current Behavior**:
  - Isolation Forest is fit on the entire dataset ($N=9382$) and evaluated on the same $N=9382$ records.
  - There is zero held-out test data. This makes it impossible to measure out-of-sample generalization.
- **Remediation**:
  - Implement a rigorous **Train (70%) / Validation (15%) / Test (15%)** split.
  - The **Test set must remain strictly untouched** during all hyperparameter tuning, model selection, and threshold calibration.

### Flaw 2: Feature Scaler & Imputer Leakage
- **Current Behavior**:
  - In `temporal_model.py` (`generate_sequences` and `fit`), `RobustScaler.fit_transform()` is called on the entire dataframe *before* splitting into train and validation sets:
    ```python
    # CURRENT FLAW in Phase 5:
    feat_scaled = self.scaler.fit_transform(feat_imp)  # Scaled on 100% of data
    train_seqs = sequences[:split_idx]
    val_seqs = sequences[split_idx:]
    ```
  - This leaks the global median and interquartile range (IQR) from future/validation sequences into the training representations.
- **Remediation**:
  - Scaler and imputer must be fit **exclusively on the training split**.
  - Validation and Test splits must be transformed using the fitted training parameters (`.transform()`).

### Flaw 3: Session-Aware Chronological Partitioning
- **Current Behavior**:
  - In `xgboost_detector.py`, the code uses `train_test_split(..., shuffle=True)`, which would randomly shuffle individual epochs if run on time series.
  - In `temporal_model.py`, the simple sequential split (`sequences[:split_idx]`) splits across Session 15, causing adjacent temporal windows (differing by only 1 second) to straddle the train/val boundary.
- **Remediation**:
  - Use **session-aware chronological partitioning**:
    - Allocate entire sessions to partitions where possible:
      - **Train**: Sessions 4, 5, 10 ($236 + 993 + 3512 = 4741$ epochs, $\approx 50.5\%$).
      - **Validation**: Early portion of Session 15 ($N=2320$ epochs, $\approx 24.7\%$).
      - **Test**: Later portion of Session 15 ($N=2282$ epochs, $\approx 24.3\%$, separated by a buffer gap to prevent overlapping sliding windows).
    - Under this protocol:
      1. No random epoch shuffling occurs.
      2. Temporal arrow-of-time is respected.
      3. The test set is completely held out until final model verification.

### Flaw 4: Single-Contamination Tuning Fallacy
- **Current Behavior**:
  - Isolation Forest contamination was set to a hardcoded $0.02$ without systematic validation or sensitivity analysis of score distributions under varying sample sizes or estimators.
- **Remediation**:
  - Perform hyperparameter optimization using validation anomaly score kurtosis, stability, and false-positive rates on nominal validation data.

---

## 5. Potential Tuning Parameters

| Model | Hyperparameters for Optimization | Search Space / Candidates | Optimization Criteria |
| :--- | :--- | :--- | :--- |
| **Isolation Forest** | `n_estimators`<br/>`max_samples`<br/>`max_features`<br/>`contamination`<br/>`random_state` | `n_estimators`: [100, 200, 300, 500]<br/>`max_samples`: [128, 256, 512, 'auto']<br/>`max_features`: [0.7, 0.85, 1.0]<br/>`contamination`: [0.005, 0.01, 0.015, 0.02, 0.03] | Score distribution stability, low false-positive rate on nominal val, separation margin |
| **XGBoost Classifier** | `n_estimators`<br/>`max_depth`<br/>`learning_rate`<br/>`min_child_weight`<br/>`subsample`<br/>`colsample_bytree`<br/>`gamma`<br/>`reg_alpha`<br/>`reg_lambda` | `n_estimators`: [100, 200, 300]<br/>`max_depth`: [3, 4, 5, 6]<br/>`learning_rate`: [0.01, 0.03, 0.05, 0.1]<br/>`subsample`: [0.7, 0.8, 0.9]<br/>`colsample_bytree`: [0.7, 0.8, 0.9]<br/>`reg_alpha`: [1e-3, 0.1, 1.0]<br/>`reg_lambda`: [1e-3, 0.1, 1.0] | Validation Macro F1, PR-AUC, multiclass logloss (when labels present) |
| **LSTM Temporal Model** | `window_size`<br/>`hidden_dim`<br/>`num_layers`<br/>`lr`<br/>`batch_size`<br/>`dropout`<br/>`early_stopping_patience` | `window_size`: [5, 10, 15]<br/>`hidden_dim`: [16, 32, 64]<br/>`num_layers`: [1, 2]<br/>`lr`: [1e-3, 2e-3, 5e-4]<br/>`batch_size`: [32, 64, 128]<br/>`dropout`: [0.0, 0.1, 0.2] | Validation Reconstruction MSE, early stopping convergence, latency |
| **Physical Rules** | Threshold calibration | Kinematic bounds, HDOP/VDOP tolerances, integrity thresholds | Nominal false-alarm rate $\le 0.1\%$ on validation data |

---

## 6. Recommended Phase 5.5 Execution Strategy

1. **Step 1: Leakage Elimination & Data Partitioning**
   - Implement clean chronological, session-aware Train / Validation / Test splitter.
   - Fit scalers and imputers solely on the Train partition.
   - Lock the Test partition until final evaluation.

2. **Step 2: Baseline Execution & Metrics Capture**
   - Execute existing baseline models on the clean partitions.
   - Record baseline metrics in `reports/baseline_metrics.json` and `reports/baseline_results.md`.

3. **Step 3: Threshold Calibration for Physical Rules**
   - Calibrate physical rule thresholds against the nominal validation distribution.
   - Document findings in `reports/rule_threshold_analysis.md`.

4. **Step 4: Isolation Forest Tuning**
   - Tune `n_estimators`, `max_samples`, `max_features`, and `contamination` on the validation set.
   - Save candidate models and output `reports/isolation_forest_tuning.json`.

5. **Step 5: Supervised XGBoost Optimization**
   - Honest evaluation of label provenance.
   - If no verified attack labels exist, document that supervised metrics cannot legitimately be calculated, and maintain reproducible search code.
   - If scenario data exists, tune with Optuna / RandomizedSearch.
   - Save candidate models and generate `reports/xgboost_tuning.json` and `reports/xgboost_evaluation.md`.

6. **Step 6: LSTM Temporal Model Tuning**
   - Tune window size, hidden dimensions, layers, learning rate, and dropout with early stopping.
   - Select best model based strictly on validation reconstruction error.
   - Save candidate models and generate `reports/temporal_model_tuning.json` and `reports/temporal_model_evaluation.md`.

7. **Step 7: Production Model Selection & Model Directory Hierarchy**
   - Establish clean `models/production/` vs `models/experiments/` structure.
   - Write comprehensive `reports/MODEL_COMPARISON.md`.

8. **Step 8: Evidence Bundle Update & End-to-End Verification**
   - Update `EvidenceBundle` schema with `model_version`, `model_training_date`, and `feature_schema_version`.
   - Run end-to-end integration tests on all test scenarios (normal, missing, invalid, sudden kinematic change, etc.).
   - Update documentation (`README.md`, `docs/IMPLEMENTATION_PROGRESS.md`, `docs/MODEL_CARD.md`, `docs/MODEL_FINE_TUNING.md`).
   - Create reproducible configuration `configs/model_training.yaml`.
   - Push commit to GitHub.
