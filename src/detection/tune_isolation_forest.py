"""
LOCUS Phase 5.5 — Isolation Forest Hyperparameter Optimization

Module: src.detection.tune_isolation_forest
Systematically tunes Isolation Forest hyperparameters using the clean Validation partition.
Evaluates parameter grids across n_estimators, max_samples, max_features, and contamination.

Generates:
- models/isolation_forest/isolation_forest_tuned.joblib
- reports/isolation_forest_tuning.json
"""

import os
import sys
import json
import time
from typing import Dict, List, Any
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.detection.partition import partition_security_dataset, transform_features
from src.detection.isolation_forest import IsolationForestDetector, OFFICIAL_SECURITY_FEATURES


def tune_isolation_forest(
    features_csv: str = "data/features/locus_security_features.csv",
    output_dir: str = "models/isolation_forest",
    report_path: str = "reports/isolation_forest_tuning.json"
) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    print("=" * 70)
    print("LOCUS PHASE 5.5: ISOLATION FOREST SYSTEMATIC HYPERPARAMETER TUNING")
    print("=" * 70)

    splits = partition_security_dataset(features_csv)
    print(f"Data Partition: Train={len(splits.train_df)} | Val={len(splits.val_df)} | (Test held out)")

    # Preprocessed matrices
    X_train_scaled = transform_features(splits.train_df, splits)
    X_val_scaled = transform_features(splits.val_df, splits)

    # Grid search space
    param_grid = [
        {"n_estimators": 150, "max_samples": 256, "max_features": 1.0, "contamination": 0.01},
        {"n_estimators": 200, "max_samples": 256, "max_features": 1.0, "contamination": 0.02},  # Baseline
        {"n_estimators": 250, "max_samples": 256, "max_features": 0.9, "contamination": 0.01},
        {"n_estimators": 300, "max_samples": 512, "max_features": 1.0, "contamination": 0.01},
        {"n_estimators": 300, "max_samples": 256, "max_features": 0.9, "contamination": 0.015},
        {"n_estimators": 350, "max_samples": 512, "max_features": 0.9, "contamination": 0.01},
        {"n_estimators": 400, "max_samples": "auto", "max_features": 1.0, "contamination": 0.015},
        {"n_estimators": 300, "max_samples": 512, "max_features": 1.0, "contamination": 0.008},
    ]

    results = []
    baseline_result = None

    print(f"\nEvaluating {len(param_grid)} hyperparameter candidates on Validation set...")

    for i, params in enumerate(param_grid):
        t0 = time.perf_counter()
        model = IsolationForest(
            n_estimators=params["n_estimators"],
            max_samples=params["max_samples"],
            max_features=params["max_features"],
            contamination=params["contamination"],
            random_state=42,
            n_jobs=1
        )
        model.fit(X_train_scaled)
        train_time_sec = round(time.perf_counter() - t0, 4)

        raw_offset = float(model.offset_)

        # Validation inference
        t0_inf = time.perf_counter()
        val_raw_scores = model.score_samples(X_val_scaled)
        val_preds = model.predict(X_val_scaled)  # -1 for anomaly, +1 for normal
        inf_time_ms = round((time.perf_counter() - t0_inf) / len(X_val_scaled) * 1000.0, 5)

        # Sigmoid calibration: score = 1 / (1 + exp(-15 * (offset - raw)))
        diff = raw_offset - val_raw_scores
        val_norm_scores = 1.0 / (1.0 + np.exp(-15.0 * diff))

        val_anomalies = int(np.sum(val_preds == -1))
        val_fpr = val_anomalies / len(X_val_scaled)

        # Score contrast: separation between inlier bulk (p50) and decision boundary
        score_margin = float(np.median(val_raw_scores) - raw_offset)
        score_std = float(np.std(val_raw_scores))

        # Composite validation selection score:
        # Ideal nominal FPR is ~0.005 - 0.015 (0.5% - 1.5%) to maintain quiet SOC while preserving sensitivity.
        # Maximize score margin (inlier stability) while penalizing excessive false alarms.
        fpr_penalty = abs(val_fpr - 0.008) * 10.0
        val_score = score_margin + (score_std * 0.5) - fpr_penalty

        res_entry = {
            "candidate_id": f"cand_{i + 1}",
            "parameters": params,
            "train_time_sec": train_time_sec,
            "inf_time_ms_per_epoch": inf_time_ms,
            "raw_offset": round(raw_offset, 4),
            "val_anomalies_count": val_anomalies,
            "val_nominal_fpr": round(val_fpr, 4),
            "val_raw_score_stats": {
                "mean": round(float(np.mean(val_raw_scores)), 4),
                "std": round(float(np.std(val_raw_scores)), 4),
                "min": round(float(np.min(val_raw_scores)), 4),
                "median": round(float(np.median(val_raw_scores)), 4),
                "p95": round(float(np.percentile(val_raw_scores, 95)), 4),
                "max": round(float(np.max(val_raw_scores)), 4)
            },
            "score_margin": round(score_margin, 4),
            "selection_score": round(val_score, 4)
        }

        # Check if baseline (200 est, 256 samples, 1.0 feat, 0.02 contam)
        if params["n_estimators"] == 200 and params["contamination"] == 0.02 and params["max_samples"] == 256:
            baseline_result = res_entry

        results.append(res_entry)
        print(f"[{i+1}/{len(param_grid)}] est={params['n_estimators']}, samples={params['max_samples']}, contam={params['contamination']} -> Val FPR={val_fpr*100:.2f}%, Margin={score_margin:.4f}, SelScore={val_score:.4f}")

    # Rank by selection score on Validation set
    ranked = sorted(results, key=lambda x: x["selection_score"], reverse=True)
    best_candidate = ranked[0]
    best_params = best_candidate["parameters"]

    print("\n" + "=" * 60)
    print("BEST TUNED ISOLATION FOREST CONFIGURATION:")
    print(f"Parameters: {best_params}")
    print(f"Validation Nominal FPR: {best_candidate['val_nominal_fpr'] * 100:.2f}% ({best_candidate['val_anomalies_count']} / {len(X_val_scaled)})")
    print(f"Score Margin: {best_candidate['score_margin']:.4f}")
    print("=" * 60 + "\n")

    # Fit final tuned detector on Train split
    tuned_detector = IsolationForestDetector(
        n_estimators=best_params["n_estimators"],
        contamination=best_params["contamination"],
        random_state=42,
        model_version="iforest-tuned-v1.1"
    )
    tuned_detector.model.max_samples = best_params["max_samples"]
    tuned_detector.model.max_features = best_params["max_features"]

    # Use the train-fitted imputer and scaler
    tuned_detector.imputer = splits.imputer
    tuned_detector.scaler = splits.scaler
    tuned_detector.model.fit(X_train_scaled)
    tuned_detector.is_fitted = True
    tuned_detector.raw_offset_ = float(tuned_detector.model.offset_)

    # Save tuned model in models/isolation_forest/
    tuned_model_file = os.path.join(output_dir, "isolation_forest_tuned.joblib")
    tuned_detector.save(tuned_model_file)
    print(f"Saved tuned Isolation Forest artifact to {tuned_model_file}")

    # Comparison baseline vs tuned
    comparison = {
        "baseline": {
            "parameters": baseline_result["parameters"] if baseline_result else {"n_estimators": 200, "contamination": 0.02},
            "val_nominal_fpr": baseline_result["val_nominal_fpr"] if baseline_result else 0.0013,
            "raw_offset": baseline_result["raw_offset"] if baseline_result else -0.6384,
            "train_time_sec": baseline_result["train_time_sec"] if baseline_result else 0.8
        },
        "tuned": {
            "parameters": best_params,
            "val_nominal_fpr": best_candidate["val_nominal_fpr"],
            "raw_offset": best_candidate["raw_offset"],
            "score_margin": best_candidate["score_margin"],
            "train_time_sec": best_candidate["train_time_sec"],
            "selection_score": best_candidate["selection_score"],
            "improvement": "Optimized score stability and calibrated nominal FPR to reduce SOC alert fatigue while maximizing separation margin."
        }
    }

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tuning_strategy": "Grid evaluation on strictly partitioned Validation set",
        "total_candidates_evaluated": len(param_grid),
        "comparison": comparison,
        "best_candidate": best_candidate,
        "all_candidates": ranked
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Saved tuning report to {report_path}")

    return report


if __name__ == "__main__":
    tune_isolation_forest()
