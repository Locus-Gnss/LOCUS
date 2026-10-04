"""
LOCUS Phase 5.5 — Baseline Model Evaluation Runner

Module: src.detection.run_baseline_evaluation
Evaluates existing Phase 5 baseline detection models without modification across
the leakage-free Train, Validation, and Test splits.

Generates:
- reports/baseline_metrics.json
- reports/baseline_results.md
"""

import os
import sys
import json
import time
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import pandas as pd
import torch

from src.detection.partition import partition_security_dataset, DatasetSplits
from src.detection.physical_rules import PhysicalRulesEngine, PhysicalRulesConfig
from src.detection.isolation_forest import IsolationForestDetector, OFFICIAL_SECURITY_FEATURES
from src.detection.xgboost_detector import XGBoostDetector, inspect_and_train_xgboost
from src.detection.temporal_model import TemporalDetector, LSTMAutoencoder


def evaluate_baseline_pipeline(
    features_csv: str = "data/features/locus_security_features.csv",
    iforest_path: str = "models/isolation_forest.joblib",
    temporal_weights: str = "models/temporal_model.pt",
    temporal_meta: str = "models/temporal_metadata.joblib",
    output_json: str = "reports/baseline_metrics.json",
    output_md: str = "reports/baseline_results.md"
) -> Dict[str, Any]:
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    os.makedirs(os.path.dirname(output_md), exist_ok=True)

    print("=" * 70)
    print("LOCUS PHASE 5.5: BASELINE MODEL RIGOROUS EVALUATION")
    print("=" * 70)

    # 1. Dataset Partitioning (Strictly Leakage-Free)
    splits = partition_security_dataset(features_csv)
    print(f"Data Partitions: Train={len(splits.train_df)}, Val={len(splits.val_df)}, Test={len(splits.test_df)}")

    metrics_bundle: Dict[str, Any] = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "partitions": splits.summary,
        "models": {}
    }

    # -------------------------------------------------------------------------
    # 2. Physical Rules Baseline Evaluation
    # -------------------------------------------------------------------------
    print("\n--- Evaluating Baseline Physical Rule Engine ---")
    rules_cfg = PhysicalRulesConfig()
    rules_engine = PhysicalRulesEngine(config=rules_cfg)

    def evaluate_rules_df(df: pd.DataFrame) -> Dict[str, Any]:
        rule_evals = rules_engine.evaluate_dataframe(df)
        total = len(df)
        anom_count = sum(1 for e in rule_evals if e["is_anomalous"])
        rule_trigger_counts: Dict[str, int] = {}
        severity_counts = {"INFO": 0, "WARNING": 0, "HIGH": 0, "CRITICAL": 0}

        for e in rule_evals:
            severity_counts[e["max_severity"]] = severity_counts.get(e["max_severity"], 0) + 1
            for r in e["triggered_rules"]:
                rid = r["rule_id"]
                rule_trigger_counts[rid] = rule_trigger_counts.get(rid, 0) + 1

        return {
            "total_epochs": total,
            "anomalous_epochs": anom_count,
            "anomaly_rate_pct": round(anom_count / total * 100.0, 3) if total > 0 else 0.0,
            "severity_distribution": severity_counts,
            "rule_trigger_counts": rule_trigger_counts
        }

    rules_train = evaluate_rules_df(splits.train_df)
    rules_val = evaluate_rules_df(splits.val_df)
    rules_test = evaluate_rules_df(splits.test_df)

    metrics_bundle["models"]["physical_rules"] = {
        "model_type": "Deterministic Kinematic Invariant Engine",
        "model_version": "prules-v1.0",
        "train_metrics": rules_train,
        "val_metrics": rules_val,
        "test_metrics": rules_test,
        "note": "Evaluated against nominal stationary data. Anomalies represent nominal false-alarm rates."
    }

    # -------------------------------------------------------------------------
    # 3. Isolation Forest Baseline Evaluation
    # -------------------------------------------------------------------------
    print("\n--- Evaluating Baseline Isolation Forest ---")
    if os.path.exists(iforest_path):
        if_detector = IsolationForestDetector.load(iforest_path)
        print(f"Loaded existing Isolation Forest from {iforest_path} (n_estimators={if_detector.n_estimators}, contamination={if_detector.contamination})")
    else:
        print("Existing Isolation Forest artifact not found, fitting baseline...")
        if_detector = IsolationForestDetector(n_estimators=200, contamination=0.02, random_state=42)
        if_detector.fit(splits.train_df)
        if_detector.save(iforest_path)

    def evaluate_if_df(df: pd.DataFrame) -> Dict[str, Any]:
        preds_df = if_detector.predict_dataframe(df)
        raw_scores = preds_df["if_raw_score"].values
        norm_scores = preds_df["if_anomaly_score"].values
        flags = preds_df["if_is_anomaly"].values

        anom_count = int(np.sum(flags))
        total = len(df)
        fpr_nominal = anom_count / total if total > 0 else 0.0

        return {
            "total_epochs": total,
            "flagged_anomalies": anom_count,
            "false_positive_rate_nominal": round(fpr_nominal, 4),
            "raw_score_stats": {
                "mean": round(float(np.mean(raw_scores)), 4),
                "std": round(float(np.std(raw_scores)), 4),
                "min": round(float(np.min(raw_scores)), 4),
                "p25": round(float(np.percentile(raw_scores, 25)), 4),
                "median": round(float(np.median(raw_scores)), 4),
                "p75": round(float(np.percentile(raw_scores, 75)), 4),
                "p95": round(float(np.percentile(raw_scores, 95)), 4),
                "max": round(float(np.max(raw_scores)), 4)
            },
            "calibrated_score_stats": {
                "mean": round(float(np.mean(norm_scores)), 4),
                "std": round(float(np.std(norm_scores)), 4),
                "min": round(float(np.min(norm_scores)), 4),
                "median": round(float(np.median(norm_scores)), 4),
                "p95": round(float(np.percentile(norm_scores, 95)), 4),
                "max": round(float(np.max(norm_scores)), 4)
            },
            "decision_offset": round(if_detector.raw_offset_, 4)
        }

    t0_if = time.perf_counter()
    if_train = evaluate_if_df(splits.train_df)
    if_val = evaluate_if_df(splits.val_df)
    if_test = evaluate_if_df(splits.test_df)
    t1_if = time.perf_counter()

    metrics_bundle["models"]["isolation_forest"] = {
        "model_type": "Unsupervised Isolation Forest",
        "model_version": if_detector.model_version,
        "parameters": {
            "n_estimators": if_detector.n_estimators,
            "contamination": if_detector.contamination,
            "random_state": if_detector.random_state
        },
        "train_metrics": if_train,
        "val_metrics": if_val,
        "test_metrics": if_test,
        "inference_time_ms_per_epoch": round((t1_if - t0_if) / (len(splits.train_df) + len(splits.val_df) + len(splits.test_df)) * 1000.0, 4),
        "note": "Ground truth attack labels do not exist in nominal dataset; supervised Precision/Recall/F1 cannot legitimately be calculated. Nominal false-alarm rate is reported as FPR."
    }

    # -------------------------------------------------------------------------
    # 4. Supervised XGBoost Baseline Audit
    # -------------------------------------------------------------------------
    print("\n--- Auditing Supervised XGBoost Baseline ---")
    xgb_audit = inspect_and_train_xgboost(features_csv=features_csv)

    metrics_bundle["models"]["xgboost"] = {
        "model_type": "Supervised Gradient Boosted Decision Tree (XGBoost)",
        "model_version": "xgb-v1.0",
        "status": xgb_audit.get("status", "UNFITTED_PENDING_LABELLED_SCENARIOS"),
        "reason": xgb_audit.get("message", "Dataset contains real baseline GNSS observations only without attack labels."),
        "parameters": {
            "max_depth": 5,
            "n_estimators": 200,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42
        },
        "supervised_metrics_available": False,
        "uncalculable_metrics": [
            "Accuracy", "Precision", "Recall", "F1-Score", "Macro F1", "Weighted F1", "Confusion Matrix", "ROC-AUC", "PR-AUC"
        ],
        "audit_note": "Verified attack labels are strictly preserved without fabrication. Supervised classification requires verified labelled attack scenario data."
    }

    # -------------------------------------------------------------------------
    # 5. Temporal LSTM Model Baseline Evaluation
    # -------------------------------------------------------------------------
    print("\n--- Evaluating Baseline Temporal LSTM Model ---")
    temp_detector = TemporalDetector(window_size=10, hidden_dim=32, num_layers=1)

    if os.path.exists(temporal_weights) and os.path.exists(temporal_meta):
        temp_detector = TemporalDetector.load(temporal_weights, temporal_meta)
        print(f"Loaded existing Temporal Detector from {temporal_weights}")
    else:
        print("Existing Temporal Detector artifact not found, fitting baseline on Train split...")
        temp_detector.fit(splits.train_df, epochs=15, batch_size=64, lr=0.002, val_split=0.2)
        temp_detector.save(temporal_weights, temporal_meta)

    def evaluate_temporal_df(df: pd.DataFrame) -> Dict[str, Any]:
        seqs, metas = temp_detector.generate_sequences(df, fit_preprocessor=False)
        if len(seqs) == 0:
            return {"total_sequences": 0}

        results = temp_detector.predict_sequences_batch(seqs, batch_size=256)
        recon_errors = np.array([r["reconstruction_error"] for r in results])
        anom_scores = np.array([r["temporal_anomaly_score"] for r in results])
        flags = np.array([r["is_anomaly"] for r in results])

        anom_count = int(np.sum(flags))
        total = len(results)

        return {
            "total_sequences": total,
            "flagged_anomalies": anom_count,
            "false_positive_rate_nominal": round(anom_count / total, 4) if total > 0 else 0.0,
            "reconstruction_loss_mse": round(float(np.mean(recon_errors)), 5),
            "reconstruction_error_stats": {
                "mean": round(float(np.mean(recon_errors)), 4),
                "std": round(float(np.std(recon_errors)), 4),
                "min": round(float(np.min(recon_errors)), 4),
                "median": round(float(np.median(recon_errors)), 4),
                "p95": round(float(np.percentile(recon_errors, 95)), 4),
                "p98": round(float(np.percentile(recon_errors, 98)), 4),
                "max": round(float(np.max(recon_errors)), 4)
            },
            "temporal_anomaly_score_stats": {
                "mean": round(float(np.mean(anom_scores)), 4),
                "median": round(float(np.median(anom_scores)), 4),
                "p95": round(float(np.percentile(anom_scores, 95)), 4),
                "max": round(float(np.max(anom_scores)), 4)
            },
            "error_threshold": round(temp_detector.error_threshold, 4)
        }

    t0_t = time.perf_counter()
    temp_train = evaluate_temporal_df(splits.train_df)
    temp_val = evaluate_temporal_df(splits.val_df)
    temp_test = evaluate_temporal_df(splits.test_df)
    t1_t = time.perf_counter()

    val_loss = temp_val.get("reconstruction_loss_mse", 0.0)
    test_loss = temp_test.get("reconstruction_loss_mse", 0.0)
    gen_gap = round(abs(test_loss - val_loss), 5)

    metrics_bundle["models"]["temporal_lstm"] = {
        "model_type": "PyTorch LSTM Autoencoder",
        "model_version": temp_detector.model_version,
        "parameters": {
            "window_size": temp_detector.window_size,
            "hidden_dim": temp_detector.hidden_dim,
            "num_layers": temp_detector.num_layers
        },
        "train_metrics": temp_train,
        "val_metrics": temp_val,
        "test_metrics": temp_test,
        "temporal_generalization_gap": gen_gap,
        "inference_time_ms_per_window": round((t1_t - t0_t) / max(1, (temp_train.get("total_sequences", 0) + temp_val.get("total_sequences", 0) + temp_test.get("total_sequences", 0))) * 1000.0, 4),
        "note": "Reconstruction error measures deviation from learned normal temporal dynamics. Generalization gap is |Test MSE - Val MSE|."
    }

    # -------------------------------------------------------------------------
    # 6. Save Baseline Metrics JSON
    # -------------------------------------------------------------------------
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(metrics_bundle, f, indent=2)
    print(f"\nSaved baseline metrics JSON to {output_json}")

    # -------------------------------------------------------------------------
    # 7. Generate Baseline Results Markdown
    # -------------------------------------------------------------------------
    md_content = f"""# LOCUS Phase 5 — Baseline Model Performance Report

**Evaluation Timestamp**: {metrics_bundle["evaluation_timestamp"]}  
**Dataset**: `{features_csv}` (9,382 total epochs)  
**Partition Strategy**: Leakage-free session-aware chronological split  
- **Train Partition**: Sessions 4, 5, 9, 10 ({splits.summary['train_epochs']:,} epochs, 50.6%)  
- **Validation Partition**: Session 11 + Session 15 Part 1 ({splits.summary['val_epochs']:,} epochs, 24.5%)  
- **Buffer Gap**: 30 epochs in Session 15 (temporal sequence isolation)  
- **Test Partition**: Session 15 Part 2 ({splits.summary['test_epochs']:,} epochs, 24.5%, strictly untouched during tuning)  

---

## 1. Summary of Baseline Detection Performance

| Model | Architecture | Train Metric | Validation Metric | Test Metric | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Physical Rules** | Deterministic Kinematic Rules | FPR: {rules_train['anomaly_rate_pct']}% | FPR: {rules_val['anomaly_rate_pct']}% | FPR: {rules_test['anomaly_rate_pct']}% | Operational |
| **Isolation Forest** | Scikit-Learn IsolationForest | FPR: {if_train['false_positive_rate_nominal'] * 100:.2f}% | FPR: {if_val['false_positive_rate_nominal'] * 100:.2f}% | FPR: {if_test['false_positive_rate_nominal'] * 100:.2f}% | Operational |
| **XGBoost Classifier** | Gradient Boosted Trees | N/A | N/A | N/A | Pending Labels |
| **LSTM Autoencoder** | PyTorch 1-Layer LSTM ($W=10$) | MSE: {temp_train.get('reconstruction_loss_mse', 'N/A')} | MSE: {temp_val.get('reconstruction_loss_mse', 'N/A')} | MSE: {temp_test.get('reconstruction_loss_mse', 'N/A')} | Operational |

---

## 2. Physical Plausibility Rule Engine

- **Model Version**: `prules-v1.0`
- **Physical Invariants**: Kinematic velocity (85 m/s), acceleration (10 m/s²), jerk (25 m/s³), turn rate (90°/s), HDOP (8.0), VDOP (10.0), integrity (0.20), sat count (4).
- **Trigger Rate on Nominal Data**:
  - Validation False Alarm Rate: **{rules_val['anomaly_rate_pct']}%** ({rules_val['anomalous_epochs']} / {rules_val['total_epochs']})
  - Test False Alarm Rate: **{rules_test['anomaly_rate_pct']}%** ({rules_test['anomalous_epochs']} / {rules_test['total_epochs']})
  - Active Triggers: Most triggered rules on baseline data correspond to stationary multipath jitter (`bearing_rate` at micro-speeds or transient DOP fluctuations).

---

## 3. Isolation Forest Unsupervised Anomaly Detector

- **Model Version**: `{if_detector.model_version}`
- **Baseline Hyperparameters**: `n_estimators = 200`, `contamination = 0.02`, `random_state = 42`.
- **Decision Threshold (Offset)**: `{if_detector.raw_offset_:.4f}`
- **Anomaly Score Distributions**:
  - Train: Mean raw score = `{if_train['raw_score_stats']['mean']}`, Flagged = `{if_train['flagged_anomalies']}` ({if_train['false_positive_rate_nominal'] * 100:.2f}%)
  - Validation: Mean raw score = `{if_val['raw_score_stats']['mean']}`, Flagged = `{if_val['flagged_anomalies']}` ({if_val['false_positive_rate_nominal'] * 100:.2f}%)
  - Test: Mean raw score = `{if_test['raw_score_stats']['mean']}`, Flagged = `{if_test['flagged_anomalies']}` ({if_test['false_positive_rate_nominal'] * 100:.2f}%)
- **Supervised Metric Disclosure**: Verified attack labels are absent in nominal baseline logs. In compliance with rigorous empirical standards, supervised metrics (Precision, Recall, F1) are legitimately reported as uncalculable for attack detection on nominal data. The reported FPR reflects nominal false alarm behavior.

---

## 4. Supervised XGBoost Classifier Infrastructure

- **Audit Status**: `{xgb_audit.get('status')}`
- **Audit Finding**: `{xgb_audit.get('message')}`
- **Integrity Safeguard**: Attack labels are NEVER fabricated.
- **Uncalculable Supervised Metrics**: Accuracy, Precision, Recall, F1, Macro F1, Confusion Matrix, ROC-AUC.
- **Readiness**: The complete training, cross-validation, and Optuna tuning infrastructure is fully implemented and operational, awaiting labelled attack scenario data.

---

## 5. LSTM Temporal Autoencoder

- **Model Version**: `{temp_detector.model_version}`
- **Architecture**: Input $(W=10, D=10) \\rightarrow$ LSTM(32) $\\rightarrow$ Latent(32) $\\rightarrow$ LSTM(32) $\\rightarrow$ Linear(10).
- **Error Threshold**: `{temp_detector.error_threshold:.4f}` (calibrated on nominal training/validation reconstruction error)
- **Reconstruction MSE**:
  - Train MSE: `{temp_train.get('reconstruction_loss_mse', 'N/A')}`
  - Validation MSE: `{temp_val.get('reconstruction_loss_mse', 'N/A')}`
  - Test MSE: `{temp_test.get('reconstruction_loss_mse', 'N/A')}`
- **Temporal Generalization Gap**: `{gen_gap}` ($|\\text{{MSE}}_{{\\text{{test}}}} - \\text{{MSE}}_{{\\text{{val}}}}|$)
- **Validation FPR on Nominal**: `{temp_val.get('false_positive_rate_nominal', 0) * 100:.2f}%`

---

## 6. Key Identified Opportunities for Phase 5.5 Tuning

1. **Isolation Forest**:
   - Optimize `n_estimators`, `max_samples`, `max_features`, and `contamination` on the Validation partition.
   - Target: Reduce nominal false alarm rate below 1.5% while maximizing kurtosis and score separation margin.
2. **LSTM Temporal Model**:
   - Tune window size $W \\in [5, 10, 15]$, hidden dimensions $\\in [16, 32, 64]$, dropout $\\in [0.0, 0.1, 0.2]$, learning rates, and early stopping.
   - Target: Lower validation reconstruction loss and reduce generalization gap.
3. **Physical Rules Calibration**:
   - Calibrate stationary mode filtering to suppress zero-speed bearing rate noise.
"""

    with open(output_md, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Saved baseline results report to {output_md}")

    return metrics_bundle


if __name__ == "__main__":
    evaluate_baseline_pipeline()
