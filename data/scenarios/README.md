# LOCUS — Supervised Attack Scenario Dataset Repository

## Purpose
This directory (`data/scenarios/`) is the designated repository for importing **verified, labelled GNSS cyber-physical security scenarios** (such as TEXBAT, Spirent hardware-in-the-loop, or laboratory RF simulations) for training and validating **Detector 3 (XGBoost Classifier)**.

---

## Architectural & Non-Fabrication Constraint

The primary LOCUS GNSS dataset (`data/features/locus_security_features.csv`, ~27,687 records) consists exclusively of benign baseline telemetry collected from an L89HA module during normal terrestrial navigation. **No ground-truth attack labels exist in the baseline dataset.**

In accordance with strict cybersecurity engineering principles:
- **Zero Fabrication:** The LOCUS system **never** fabricates fake attack labels or synthesizes fake attack records to make the classifier appear trained.
- **Supervised Classifier Gate:** Detector 3 remains in its honest state:
  `UNAVAILABLE — MODEL NOT TRAINED`
  until verified ground-truth labelled attack scenarios are imported here.

---

## Expected Dataset Schema

A valid scenario dataset should be provided in CSV format. It must satisfy either of the two schema modes:

### Mode 1: Pre-Engineered Canonical 10-D Security Features (Recommended)

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `disp_haversine` | `float` | Haversine epoch-to-epoch displacement (meters) |
| `vel_kinematic` | `float` | Kinematic derived velocity ($m/s$) |
| `acc_kinematic` | `float` | Kinematic derived acceleration ($m/s^2$) |
| `jerk_kinematic` | `float` | Derivative of acceleration ($m/s^3$) |
| `bearing_rate` | `float` | Rate of change of trajectory bearing ($^\circ/s$) |
| `HDOP` | `float` | Horizontal Dilution of Precision |
| `VDOP` | `float` | Vertical Dilution of Precision |
| `fix_integrity` | `float` | Receiver fix integrity status indicator |
| `sat_count_tot` | `float` | Total number of tracked satellites |
| `sat_churn` | `float` | Satellite constellation churn rate |
| `scenario_id` or `session_id` | `str` / `int` | Independent trajectory or session grouping (used for leakage-resistant partitioning) |
| `attack_label` or `label` | `int` / `str` | Ground-truth class: `0` / `nominal` vs `1` / `spoofing` / `jamming` |

### Mode 2: Raw GNSS Telemetry

If raw telemetry is supplied, the training pipeline will automatically invoke `SecurityFeatureExtractor` to compute the canonical 10-D features while preserving your label column. Required raw columns:
- `latitude`
- `longitude`
- `altitude_m`
- `timestamp_utc`
- `session_id` or `scenario_id`
- `attack_label` or `label`

---

## How to Train XGBoost with Imported Scenarios

### Option A: Via Command-Line Interface (CLI)

```bash
# Navigate to LOCUS root
cd d:\LOCUS\LOCUS-main

# Run reproducible training pipeline
python scripts/train_xgboost.py --dataset data/scenarios/my_labelled_scenario.csv
```

CLI Arguments:
- `--dataset`: Path to your labelled CSV file.
- `--label-col`: (Optional) Explicit name of your target column (auto-detected if omitted).
- `--model-out`: Destination path for trained model artifact (default: `models/production/xgboost/xgboost_detector.joblib`).
- `--report-out`: Destination path for evaluation report (default: `reports/xgboost_evaluation_report.json`).

### Option B: Via FastAPI REST API

Send a `POST` request to `http://127.0.0.1:8000/api/models/train`:

```json
{
  "model_type": "xgboost",
  "dataset_path": "data/scenarios/my_labelled_scenario.csv"
}
```

The API will execute the validation pipeline, fit the model on leakage-resistant partitions, save artifacts, and immediately reload the singleton inference model without requiring a server restart.
