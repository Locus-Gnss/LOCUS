"""
LOCUS Phase 5 — XGBoost Supervised Attack Classifier Infrastructure

Module: src.detection.xgboost_detector
Builds the supervised classification infrastructure for GNSS spoofing and tampering
detection using XGBoost on the official 10-D security feature vector.

Official 10-D features:
1. disp_haversine
2. vel_kinematic
3. acc_kinematic
4. jerk_kinematic
5. bearing_rate
6. HDOP
7. VDOP
8. fix_integrity
9. sat_count_tot
10. sat_churn

Important Architectural Constraint:
Verified attack labels are NEVER fabricated or synthesized without empirical or
scenario simulation provenance. If no verified labels are detected in the dataset,
the infrastructure reports that supervised training requires labelled scenarios,
provides the complete training and inference pipeline, and waits for scenario data.
"""

import os
import json
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
import pandas as pd
import joblib
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix, precision_recall_fscore_support
import xgboost as xgb

OFFICIAL_SECURITY_FEATURES = [
    "disp_haversine",
    "vel_kinematic",
    "acc_kinematic",
    "jerk_kinematic",
    "bearing_rate",
    "HDOP",
    "VDOP",
    "fix_integrity",
    "sat_count_tot",
    "sat_churn",
]

DEFAULT_XGB_MODEL_PATH = os.path.join("models", "xgboost_detector.joblib")
DEFAULT_IMPORTANCE_PATH = os.path.join("models", "xgboost_feature_importance.json")


class XGBoostDetector:
    """
    Supervised XGBoost classifier for GNSS cyber-attack classification.
    """

    def __init__(
        self,
        features: Optional[List[str]] = None,
        max_depth: int = 5,
        n_estimators: int = 200,
        learning_rate: float = 0.05,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        random_state: int = 42,
        model_version: str = "xgb-v1.0"
    ):
        self.features = features or list(OFFICIAL_SECURITY_FEATURES)
        self.model_version = model_version
        self.imputer = SimpleImputer(strategy="median", fill_value=0.0)
        self.scaler = RobustScaler()

        self.classifier = xgb.XGBClassifier(
            max_depth=max_depth,
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            random_state=random_state,
            eval_metric="logloss",
            use_label_encoder=False
        )
        self.is_fitted = False
        self.feature_importances_: Dict[str, float] = {}

    def _preprocess(self, df: pd.DataFrame, fit_preprocessor: bool = False) -> np.ndarray:
        data = df.copy()
        for col in self.features:
            if col not in data.columns:
                data[col] = np.nan

        X = data[self.features].to_numpy(dtype=np.float64)
        all_nan_mask = np.all(np.isnan(X), axis=0)
        if np.any(all_nan_mask):
            X[:, all_nan_mask] = 0.0

        if fit_preprocessor:
            X_imp = self.imputer.fit_transform(X)
            X_scaled = self.scaler.fit_transform(X_imp)
        else:
            X_imp = self.imputer.transform(X)
            X_scaled = self.scaler.transform(X_imp)
        return X_scaled

    def fit(
        self,
        X_df: pd.DataFrame,
        y: np.ndarray,
        eval_set: Optional[Tuple[pd.DataFrame, np.ndarray]] = None
    ) -> Dict[str, Any]:
        """
        Train XGBoost on verified labelled scenarios.
        """
        X_scaled = self._preprocess(X_df, fit_preprocessor=True)
        eval_data = None
        if eval_set is not None:
            eval_X, eval_y = eval_set
            eval_scaled = self._preprocess(eval_X, fit_preprocessor=False)
            eval_data = [(eval_scaled, eval_y)]

        self.classifier.fit(
            X_scaled,
            y,
            eval_set=eval_data,
            verbose=False
        )
        self.is_fitted = True

        # Extract feature importances
        raw_importances = self.classifier.feature_importances_
        self.feature_importances_ = {
            feat: float(raw_importances[i]) for i, feat in enumerate(self.features)
        }

        return {
            "status": "trained",
            "model_version": self.model_version,
            "feature_importances": self.feature_importances_
        }

    def evaluate(self, X_df: pd.DataFrame, y_true: np.ndarray) -> Dict[str, Any]:
        """Compute comprehensive evaluation metrics on test set."""
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted.")

        X_scaled = self._preprocess(X_df, fit_preprocessor=False)
        y_pred = self.classifier.predict(X_scaled)
        y_proba = self.classifier.predict_proba(X_scaled)[:, 1] if len(np.unique(y_true)) > 1 else y_pred

        prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)
        cm = confusion_matrix(y_true, y_pred).tolist()

        roc_auc = None
        if len(np.unique(y_true)) > 1:
            try:
                roc_auc = float(roc_auc_score(y_true, y_proba))
            except Exception:
                roc_auc = None

        return {
            "precision": float(prec),
            "recall": float(rec),
            "f1_score": float(f1),
            "roc_auc": roc_auc,
            "confusion_matrix": cm,
            "classification_report": classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        }

    def predict_epoch(self, epoch: Union[Dict[str, Any], pd.Series]) -> Dict[str, Any]:
        """
        Evaluate single epoch.
        If model is unfitted because no labelled attack data exists yet,
        returns transparent uncalibrated/unfitted status.
        """
        if not self.is_fitted:
            return {
                "available": False,
                "status": "UNFITTED_PENDING_LABELLED_SCENARIOS",
                "attack_probability": None,
                "predicted_label": None,
                "model_version": self.model_version,
                "note": "Supervised XGBoost requires verified labelled attack scenario data."
            }

        row_df = pd.DataFrame([epoch])
        X_scaled = self._preprocess(row_df, fit_preprocessor=False)

        pred = int(self.classifier.predict(X_scaled)[0])
        probas = self.classifier.predict_proba(X_scaled)[0]
        attack_prob = float(probas[1]) if len(probas) > 1 else float(pred)

        return {
            "available": True,
            "status": "INFERRED",
            "attack_probability": round(attack_prob, 4),
            "predicted_label": pred,
            "model_version": self.model_version
        }

    def save(
        self,
        filepath: str = DEFAULT_XGB_MODEL_PATH,
        importance_path: str = DEFAULT_IMPORTANCE_PATH
    ) -> Tuple[str, str]:
        """Serialize trained model and feature importances."""
        if not self.is_fitted:
            raise RuntimeError("Cannot save unfitted XGBoost detector.")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        bundle = {
            "classifier": self.classifier,
            "imputer": self.imputer,
            "scaler": self.scaler,
            "features": self.features,
            "model_version": self.model_version,
            "feature_importances": self.feature_importances_
        }
        joblib.dump(bundle, filepath)

        with open(importance_path, "w", encoding="utf-8") as f:
            json.dump(self.feature_importances_, f, indent=2)

        return filepath, importance_path

    @classmethod
    def load(cls, filepath: str = DEFAULT_XGB_MODEL_PATH) -> "XGBoostDetector":
        """Load trained model."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"XGBoost model artifact not found at {filepath}")
        bundle = joblib.load(filepath)
        detector = cls(
            features=bundle.get("features", OFFICIAL_SECURITY_FEATURES),
            model_version=bundle.get("model_version", "xgb-v1.0")
        )
        detector.classifier = bundle["classifier"]
        detector.imputer = bundle["imputer"]
        detector.scaler = bundle["scaler"]
        detector.feature_importances_ = bundle.get("feature_importances", {})
        detector.is_fitted = True
        return detector


def inspect_and_train_xgboost(
    features_csv: str = "data/features/locus_security_features.csv",
    label_column_candidates: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Inspect whether labelled scenario data exists in the security features dataset.
    If no verified labels exist, build training infrastructure, do not fabricate labels,
    and clearly report that supervised training requires labelled scenarios.
    When labelled data exists, train XGBoost, evaluate, save model, and save feature importance.
    """
    if label_column_candidates is None:
        label_column_candidates = ["attack_label", "label", "is_attack", "scenario_label", "attack_type"]

    if not os.path.exists(features_csv):
        raise FileNotFoundError(f"Feature dataset not found: {features_csv}")

    df = pd.read_csv(features_csv)
    print(f"Inspecting dataset: {features_csv} ({len(df)} records)")

    found_label_col = None
    for candidate in label_column_candidates:
        if candidate in df.columns:
            found_label_col = candidate
            break

    if found_label_col is None:
        report = {
            "status": "NO_LABELS_DETECTED",
            "message": "Dataset contains real baseline GNSS observations only. No attack label column detected.",
            "available_columns": list(df.columns),
            "label_candidates_checked": label_column_candidates,
            "action_taken": "Built full XGBoost training & inference infrastructure without fabricating labels.",
            "requirement": "Supervised training requires verified labelled attack scenario data (e.g. spoofing/jamming injected scenarios)."
        }
        print("\n" + "=" * 60)
        print("XGBOOST SUPERVISED TRAINING AUDIT REPORT:")
        print(f"- Status: {report['status']}")
        print(f"- Finding: {report['message']}")
        print(f"- Action: {report['action_taken']}")
        print(f"- Requirement: {report['requirement']}")
        print("=" * 60 + "\n")
        return report

    # If label column is present, check class distribution
    labels = df[found_label_col]
    unique_classes = labels.dropna().unique()
    print(f"Detected label column: '{found_label_col}' with classes: {unique_classes}")

    if len(unique_classes) < 2:
        report = {
            "status": "SINGLE_CLASS_ONLY",
            "message": f"Label column '{found_label_col}' contains only a single class ({unique_classes}). Supervised classification requires at least 2 distinct classes (benign vs attack).",
            "action_taken": "Maintained training infrastructure without fitting model on degenerate single-class data."
        }
        print(f"XGBoost Audit: {report['message']}")
        return report

    # Verified multi-class / binary scenario data exists: Train supervised model
    print(f"Training XGBoost on {len(df)} labelled records...")
    X = df[OFFICIAL_SECURITY_FEATURES]
    y = labels.to_numpy()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    detector = XGBoostDetector()
    detector.fit(X_train, y_train, eval_set=(X_test, y_test))

    metrics = detector.evaluate(X_test, y_test)
    model_path, imp_path = detector.save()

    print(f"Trained and evaluated XGBoost detector.")
    print(f"Weighted F1: {metrics['f1_score']:.4f}, Precision: {metrics['precision']:.4f}, Recall: {metrics['recall']:.4f}")
    print(f"Saved model to {model_path} and feature importance to {imp_path}")

    return {
        "status": "TRAINED",
        "metrics": metrics,
        "model_path": model_path,
        "importance_path": imp_path
    }


if __name__ == "__main__":
    inspect_and_train_xgboost()
