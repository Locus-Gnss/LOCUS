"""
LOCUS Phase 5 — Model Training & Evidence Generation Pipeline Runner

Module: src.detection.pipeline
Executes training for all detection paths:
1. Physical Plausibility Rules (configured)
2. Isolation Forest (trained & persisted, distribution plotted)
3. XGBoost (audited for labels, infrastructure validated)
4. LSTM Temporal Model (trained with strict session boundary preservation)
5. Evidence Fusion (generates multi-detector evidence bundles in data/evidence/)
"""

import os
import sys
import pandas as pd

from src.detection.physical_rules import PhysicalRulesEngine, PhysicalRulesConfig
from src.detection.isolation_forest import IsolationForestDetector, train_and_evaluate_isolation_forest
from src.detection.xgboost_detector import XGBoostDetector, inspect_and_train_xgboost
from src.detection.temporal_model import TemporalDetector, train_temporal_model
from src.evidence.evidence_bundle import EvidenceFusionEngine


def run_phase_5_pipeline():
    features_csv = "data/features/locus_security_features.csv"
    structured_csv = "data/structured/locus_structured_gnss.csv"
    models_dir = "models"
    evidence_dir = "data/evidence"
    plots_dir = "docs/plots"

    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(evidence_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)

    print("=" * 70)
    print("LOCUS PHASE 5: DETECTION & MACHINE LEARNING PIPELINE EXECUTION")
    print("=" * 70)

    # 1. Physical Plausibility Rule Engine
    print("\n--- [Step 1/5] Initializing Physical Plausibility Rule Engine ---")
    rules_cfg = PhysicalRulesConfig()
    rules_engine = PhysicalRulesEngine(config=rules_cfg)
    sample_rules = rules_engine.evaluate_epoch({f: 1.0 for f in [
        "disp_haversine", "vel_kinematic", "acc_kinematic", "jerk_kinematic",
        "bearing_rate", "HDOP", "VDOP", "fix_integrity", "sat_count_tot", "sat_churn"
    ]})
    print(f"Physical Rules Engine initialized with {len(sample_rules)} configurable rule evaluations.")

    # 2. Isolation Forest
    print("\n--- [Step 2/5] Training Isolation Forest Anomaly Detector ---")
    iforest_model_path = os.path.join(models_dir, "isolation_forest.joblib")
    iforest_plot_path = os.path.join(plots_dir, "isolation_forest_distribution.png")
    iforest_detector, df_if_eval = train_and_evaluate_isolation_forest(
        features_csv=features_csv,
        model_output_path=iforest_model_path,
        plot_output_path=iforest_plot_path
    )

    # 3. XGBoost Detector
    print("\n--- [Step 3/5] Auditing & Preparing Supervised XGBoost Classifier ---")
    xgb_audit = inspect_and_train_xgboost(features_csv=features_csv)
    xgb_detector = XGBoostDetector()
    print(f"XGBoost detector initialized. Status: {xgb_audit['status']}")

    # 4. LSTM Temporal Model
    print("\n--- [Step 4/5] Training LSTM Temporal Sequence Anomaly Detector ---")
    temporal_weights_path = os.path.join(models_dir, "temporal_model.pt")
    temporal_meta_path = os.path.join(models_dir, "temporal_metadata.joblib")
    temporal_detector = train_temporal_model(
        features_csv=features_csv,
        weights_path=temporal_weights_path,
        meta_path=temporal_meta_path,
        epochs=15
    )

    # 5. Evidence Fusion Engine
    print("\n--- [Step 5/5] Executing Evidence Fusion Engine ---")
    fusion_engine = EvidenceFusionEngine(
        rules_engine=rules_engine,
        iforest_detector=iforest_detector,
        xgb_detector=xgb_detector,
        temporal_detector=temporal_detector
    )

    bundles = fusion_engine.process_features_csv(
        features_csv=features_csv,
        structured_csv=structured_csv,
        output_dir=evidence_dir,
        sample_size=150
    )

    print("\n" + "=" * 70)
    print(f"PHASE 5 EXECUTION COMPLETE: Generated {len(bundles)} Evidence Bundles.")
    print("=" * 70)


if __name__ == "__main__":
    run_phase_5_pipeline()
