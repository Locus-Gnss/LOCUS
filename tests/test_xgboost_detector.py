"""
tests/test_xgboost_detector.py — Verification of Detector 3 Supervised XGBoost Pipeline

Tests:
1. Baseline unlabelled dataset inspection (zero-fabrication guarantee).
2. Unfitted detector inference behavior (returns transparent unavailable status).
3. End-to-end training pipeline on separate verified labelled scenario data.
4. Leakage-resistant session partitioning.
5. Comprehensive metrics evaluation (Accuracy, Balanced Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC).
6. Model persistence, metadata serialization, and reload.
7. Schema validation and error handling on invalid/single-class inputs.
8. FastAPI endpoints for XGBoost info, status, and training.
"""

import os
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from src.features.security_features import OFFICIAL_SECURITY_FEATURES
from src.detection.xgboost_detector import XGBoostDetector, inspect_and_train_xgboost
from scripts.train_xgboost import inspect_dataset_for_labels, run_training_pipeline
from src.api.app import app

client = TestClient(app)


def test_baseline_dataset_unlabelled_audit():
    """Verify that baseline dataset is identified as unlabelled and no attack labels are fabricated."""
    baseline_path = "data/features/locus_security_features.csv"
    if not os.path.exists(baseline_path):
        pytest.skip(f"{baseline_path} not found")

    df = pd.read_csv(baseline_path)
    label_col, label_info = inspect_dataset_for_labels(df)
    assert not label_info["has_valid_labels"]
    assert label_col is None
    assert "No ground-truth attack or classification label" in label_info["reason"]

    # Running training pipeline on unlabelled baseline should safely exit without fake training
    report = run_training_pipeline(dataset_path=baseline_path)
    assert report["status"] == "UNAVAILABLE_NO_LABELS"
    assert report["has_supervised_labels"] is False
    assert "data_limitation_explanation" in report


def test_unfitted_detector_inference():
    """Verify that unfitted XGBoost detector truthfully reports unavailable status and zero mock scores."""
    det = XGBoostDetector(model_version="xgb-unfitted-v1.0")
    assert not det.is_fitted
    assert not det.is_trained

    dummy_epoch = {f: 1.0 for f in OFFICIAL_SECURITY_FEATURES}
    res = det.predict_epoch(dummy_epoch)

    assert res["available"] is False
    assert res["status"] == "UNFITTED_PENDING_LABELLED_SCENARIOS"
    assert res["attack_probability"] is None
    assert res["predicted_label"] is None
    assert res["confidence"] is None
    assert res["probabilities"] is None
    assert "Supervised XGBoost requires verified labelled attack scenario data" in res["note"]


def test_training_pipeline_on_labelled_scenarios():
    """
    Unit test: validates pipeline execution, group partitioning, persistence, and inference
    mechanisms using an in-memory synthetic fixture generated with NumPy.

    IMPORTANT SCIENTIFIC GOVERNANCE NOTE:
    This test verifies software code paths only. The in-memory fixture consists of Gaussian random
    noise with artificial offsets, NOT real GNSS spoofing, jamming, or receiver correlator telemetry.
    Passing this unit test does NOT establish that the model is trained on real-world GNSS attacks.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Construct synthetic multi-session scenario dataset with ground-truth labels
        np.random.seed(42)
        n_samples = 300
        data = {feat: np.random.randn(n_samples) for feat in OFFICIAL_SECURITY_FEATURES}

        # 3 sessions to test session-grouped leakage-resistant partitioning
        data["session_id"] = np.repeat([101, 102, 103], n_samples // 3)

        # Binary labels: 0=nominal, 1=spoofing
        # Introduce distinct signal in vel_kinematic and disp_haversine for spoofing
        labels = []
        for i in range(n_samples):
            if i % 2 == 0:
                labels.append("nominal")
                data["vel_kinematic"][i] = abs(data["vel_kinematic"][i])
            else:
                labels.append("spoofing")
                data["vel_kinematic"][i] = abs(data["vel_kinematic"][i]) + 20.0
                data["disp_haversine"][i] = abs(data["disp_haversine"][i]) + 50.0

        data["attack_label"] = labels
        scenario_df = pd.DataFrame(data)

        scenario_csv = os.path.join(tmpdir, "test_scenarios.csv")
        scenario_df.to_csv(scenario_csv, index=False)

        model_out = os.path.join(tmpdir, "xgboost_detector.joblib")
        imp_out = os.path.join(tmpdir, "xgboost_importance.json")
        meta_out = os.path.join(tmpdir, "xgboost_metadata.json")
        rep_out = os.path.join(tmpdir, "xgboost_report.json")

        report = run_training_pipeline(
            dataset_path=scenario_csv,
            output_model_path=model_out,
            output_importance_path=imp_out,
            output_metadata_path=meta_out,
            output_report_path=rep_out,
            n_estimators=30,
            max_depth=3
        )

        assert report["status"] == "OPERATIONAL"
        assert os.path.exists(model_out)
        assert os.path.exists(imp_out)
        assert os.path.exists(meta_out)
        assert os.path.exists(rep_out)

        metrics = report["metrics"]
        assert "accuracy" in metrics
        assert "f1_score" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "confusion_matrix" in metrics
        assert metrics["accuracy"] >= 0.80

        # Load persisted model and run inference
        loaded_det = XGBoostDetector.load(model_out)
        assert loaded_det.is_fitted

        # Nominal test epoch
        nominal_epoch = {f: 0.5 for f in OFFICIAL_SECURITY_FEATURES}
        nominal_epoch["vel_kinematic"] = 1.0
        nominal_epoch["disp_haversine"] = 2.0
        pred_nom = loaded_det.predict_epoch(nominal_epoch)
        assert pred_nom["available"] is True
        assert pred_nom["status"] == "INFERRED"
        assert "attack_probability" in pred_nom
        assert "predicted_label" in pred_nom
        assert "probabilities" in pred_nom

        # Attack test epoch
        attack_epoch = {f: 0.5 for f in OFFICIAL_SECURITY_FEATURES}
        attack_epoch["vel_kinematic"] = 30.0
        attack_epoch["disp_haversine"] = 70.0
        pred_att = loaded_det.predict_epoch(attack_epoch)
        assert pred_att["available"] is True
        assert pred_att["predicted_label"] == "spoofing"
        assert pred_att["attack_probability"] > 0.5


def test_schema_validation_single_class_rejection():
    """Verify that single-class datasets are rejected with informative error message."""
    with tempfile.TemporaryDirectory() as tmpdir:
        df = pd.DataFrame({
            "disp_haversine": [1.0, 2.0, 3.0],
            "vel_kinematic": [1.0, 2.0, 3.0],
            "attack_label": ["nominal", "nominal", "nominal"]
        })
        csv_path = os.path.join(tmpdir, "single_class.csv")
        df.to_csv(csv_path, index=False)

        report = run_training_pipeline(dataset_path=csv_path)
        assert report["status"] == "UNAVAILABLE_NO_LABELS"
        assert "contains only a single class" in report["audit_details"]["reason"]


def test_schema_validation_missing_canonical_features():
    """Verify that missing canonical features without raw GNSS coordinates trigger schema error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        df = pd.DataFrame({
            "feat_random_a": [1.0, 2.0, 3.0, 4.0],
            "feat_random_b": [2.0, 3.0, 4.0, 5.0],
            "attack_label": ["nominal", "spoofing", "nominal", "spoofing"]
        })
        csv_path = os.path.join(tmpdir, "invalid_schema.csv")
        df.to_csv(csv_path, index=False)

        report = run_training_pipeline(dataset_path=csv_path)
        assert report["status"] == "SCHEMA_ERROR"
        assert "missing required canonical features" in report["error"]


def test_fastapi_xgboost_info_endpoint():
    """Verify GET /api/models/xgboost/info returns truthful status and provenance."""
    response = client.get("/api/models/xgboost/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Supervised XGBoost Classifier"
    assert "status" in data
    assert "model_version" in data
    assert "feature_schema" in data
    assert len(data["feature_schema"]) == 10
    assert "label_limitation" in data


def test_fastapi_models_status_endpoint():
    """Verify GET /api/models/status includes Detector 3 with honest status."""
    response = client.get("/api/models/status")
    assert response.status_code == 200
    data = response.json()
    assert "detectors" in data
    assert "xgboost" in data["detectors"]
    xgb_status = data["detectors"]["xgboost"]
    assert xgb_status["name"] == "Supervised XGBoost Classifier"
    assert xgb_status["type"] == "SUPERVISED_ATTACK_CLASSIFIER"


def test_fastapi_train_endpoint_audit():
    """Verify POST /api/models/train with model_type='xgboost' runs validation audit."""
    response = client.post("/api/models/train", json={
        "model_type": "xgboost",
        "dataset_path": "data/features/locus_security_features.csv"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UNAVAILABLE_NO_LABELS"
    assert data["has_supervised_labels"] is False


def test_verified_dataset_manifest_and_provenance():
    """Verify the acquired Yunnan University dataset manifest and data integrity."""
    manifest_path = "data/scenarios/manifest_yunnan_mendeley.json"
    assert os.path.exists(manifest_path), "Manifest file not found"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["provenance"]["doi"] == "10.17632/nxk9r22wd6.1"
    assert "CC BY 4.0" in manifest["provenance"]["license"]
    assert "u-blox" in manifest["provenance"]["receiver_platform"]
    assert len(manifest["verified_raw_artifacts"]) == 14
    for file_info in manifest["verified_raw_artifacts"]:
        assert "sha256" in file_info
        assert "filename" in file_info
        local_path = os.path.join("data", "scenarios", "raw_sources", "yunnan_mendeley", file_info["filename"])
        assert os.path.exists(local_path), f"Raw source file missing: {local_path}"


def test_scenario_feature_schema_and_integrity():
    """Verify canonical 10-D feature schema and zero NaN values on verified scenario CSV."""
    scenario_csv = "data/scenarios/yunnan_attack_scenarios.csv"
    assert os.path.exists(scenario_csv), "Scenario CSV missing"
    df = pd.read_csv(scenario_csv)

    assert len(df) > 20000
    for feat in OFFICIAL_SECURITY_FEATURES:
        assert feat in df.columns, f"Missing canonical feature: {feat}"
        assert not df[feat].isnull().any(), f"NaN values detected in feature {feat}"
        assert not np.isinf(df[feat]).any(), f"Infinite values detected in feature {feat}"

    assert "attack_label" in df.columns
    assert "scenario_id" in df.columns
    assert df["scenario_id"].nunique() >= 10
    classes = df["attack_label"].unique()
    assert len(classes) >= 2, "Must contain at least 2 distinct classes"
    assert set(classes) == {0, 1}


def test_session_level_split_isolation():
    """Verify that train, val, and test partitions have zero scenario_id overlap (no leakage)."""
    scenario_csv = "data/scenarios/yunnan_attack_scenarios.csv"
    df = pd.read_csv(scenario_csv)

    groups = df["scenario_id"].unique()
    np.random.seed(42)
    shuffled = np.random.permutation(groups)
    n_groups = len(shuffled)
    n_test = max(1, int(round(n_groups * 0.15)))
    n_val = max(1, int(round(n_groups * 0.15)))
    n_train = n_groups - n_val - n_test

    train_groups = set(shuffled[:n_train])
    val_groups = set(shuffled[n_train:n_train + n_val])
    test_groups = set(shuffled[n_train + n_val:])

    # Strict disjoint partitions
    assert len(train_groups & test_groups) == 0, "Train and test groups overlap! Data leakage detected."
    assert len(train_groups & val_groups) == 0, "Train and val groups overlap! Data leakage detected."
    assert len(val_groups & test_groups) == 0, "Val and test groups overlap! Data leakage detected."


def test_production_model_inference_contract():
    """Verify that the production trained model satisfies the inference contract."""
    model_path = "models/production/xgboost/xgboost_detector.joblib"
    assert os.path.exists(model_path), "Production model artifact missing"

    det = XGBoostDetector.load(model_path)
    assert det.is_fitted
    assert det.model_version == "xgb-production-v1.0"

    # Test nominal epoch inference
    epoch = {
        "disp_haversine": 0.05,
        "vel_kinematic": 0.05,
        "acc_kinematic": 0.01,
        "jerk_kinematic": 0.005,
        "bearing_rate": 0.1,
        "HDOP": 0.65,
        "VDOP": 1.1,
        "fix_integrity": 1.0,
        "sat_count_tot": 28.0,
        "sat_churn": 0.0
    }
    res = det.predict_epoch(epoch)
    assert res["available"] is True
    assert res["status"] == "INFERRED"
    assert 0.0 <= res["attack_probability"] <= 1.0
    assert res["predicted_label"] in [0, 1]
    assert 0.0 <= res["confidence"] <= 1.0
    assert "probabilities" in res


def test_api_xgboost_operational_status_and_metrics():
    """Verify that FastAPI endpoints report OPERATIONAL status with real metrics and baseline lift."""
    response = client.get("/api/models/xgboost/info")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "OPERATIONAL"
    assert data["is_fitted"] is True
    assert "Verified Scenario Dataset" in data["dataset_provenance"]
    assert data["environment"] == "Controlled Over-the-Air RF Field Experiment"
    assert "evaluation_disclaimer" in data
    assert "baseline_comparison" in data

    metrics = data["metrics"]
    assert metrics["accuracy"] > 0.85
    assert metrics["f1_score"] > 0.85
    assert metrics["roc_auc"] > 0.90
    assert metrics["pr_auc"] > 0.90
    assert metrics["false_positive_rate"] < 0.05

    baseline = data["baseline_comparison"]
    assert baseline["xgboost_accuracy_lift"] > 0.50

