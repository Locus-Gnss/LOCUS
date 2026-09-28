"""
LOCUS Phase 5 — Isolation Forest Unsupervised Anomaly Detector

Module: src.detection.isolation_forest
Implements unsupervised anomaly detection using Scikit-Learn's Isolation Forest
on the official 10-D GNSS security feature vector.

Features:
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
"""

import os
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

# Official 10-D security feature vector definition
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

DEFAULT_MODEL_PATH = os.path.join("models", "isolation_forest.joblib")


class IsolationForestDetector:
    """
    Isolation Forest anomaly detector for GNSS security feature vectors.
    """

    def __init__(
        self,
        n_estimators: int = 200,
        contamination: float = 0.02,
        random_state: int = 42,
        features: Optional[List[str]] = None,
        model_version: str = "iforest-v1.0"
    ):
        self.features = features or list(OFFICIAL_SECURITY_FEATURES)
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model_version = model_version

        # Preprocessor: Median Imputer (imputes sat_churn when PRNs unlogged) + RobustScaler
        self.imputer = SimpleImputer(strategy="median", fill_value=0.0)
        self.scaler = RobustScaler()
        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=1
        )
        self.is_fitted = False
        self.threshold_score = 0.5  # Will be calibrated during training

    def _extract_and_preprocess(self, df: pd.DataFrame, fit_preprocessor: bool = False) -> np.ndarray:
        """Extract 10-D features and apply imputation and scaling, preserving all 10 dimensions."""
        data = df.copy()
        for col in self.features:
            if col not in data.columns:
                data[col] = np.nan

        X = data[self.features].to_numpy(dtype=np.float64)

        # In historical data where PRNs were unlogged, sat_churn is entirely NaN.
        # Impute entirely NaN columns with 0.0 baseline to guarantee strict 10-D preservation.
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

    def fit(self, df: pd.DataFrame) -> "IsolationForestDetector":
        """
        Fit Isolation Forest model on feature DataFrame.
        """
        X_scaled = self._extract_and_preprocess(df, fit_preprocessor=True)
        self.model.fit(X_scaled)
        self.is_fitted = True

        # Calculate anomaly scores on training set to establish baseline threshold
        raw_scores = self.model.score_samples(X_scaled)  # Negative values; lower = anomalous
        # Sklearn: offset_ is the decision threshold for predict == -1
        # Raw score < offset_ means outlier
        self.raw_offset_ = float(self.model.offset_)
        return self

    def _compute_normalized_score(self, raw_scores: np.ndarray) -> np.ndarray:
        """
        Convert sklearn score_samples into normalized [0, 1] anomaly score.
        In sklearn, score_samples is roughly in range [-1.0, 0.0], where lower = anomaly.
        We map it such that 0.0 = completely normal, 1.0 = highly anomalous.
        """
        # score_samples: typically around -0.35 (normal) down to -0.85 (extreme outlier)
        # Using sigmoid/linear calibration around the model offset:
        # If score == offset_, anomaly score is 0.50 (the decision boundary)
        diff = self.raw_offset_ - raw_scores  # positive if anomalous
        # Logistic transformation centered at offset with scale 0.1
        anomaly_scores = 1.0 / (1.0 + np.exp(-15.0 * diff))
        return np.clip(anomaly_scores, 0.0, 1.0)

    def predict_epoch(self, epoch: Union[Dict[str, Any], pd.Series]) -> Dict[str, Any]:
        """
        Evaluate single GNSS epoch with fast vector extraction.
        Returns:
            anomaly_score: float in [0, 1] (higher = more anomalous)
            is_anomaly: bool
            raw_score: float
            model_version: str
        """
        if not self.is_fitted:
            raise RuntimeError("IsolationForestDetector has not been fitted or loaded.")

        vals = []
        for feat in self.features:
            v = epoch.get(feat, np.nan) if isinstance(epoch, dict) else (epoch.get(feat, np.nan) if hasattr(epoch, "get") else epoch[feat])
            try:
                vals.append(float(v) if pd.notna(v) else 0.0)
            except (ValueError, TypeError):
                vals.append(0.0)

        X = np.array([vals], dtype=np.float64)
        X_imp = self.imputer.transform(X)
        X_scaled = self.scaler.transform(X_imp)

        raw_score = float(self.model.score_samples(X_scaled)[0])
        pred = int(self.model.predict(X_scaled)[0])  # +1 for inlier, -1 for outlier
        anomaly_score = float(self._compute_normalized_score(np.array([raw_score]))[0])

        return {
            "is_anomaly": pred == -1,
            "anomaly_score": round(anomaly_score, 4),
            "raw_score": round(raw_score, 4),
            "decision_offset": round(self.raw_offset_, 4),
            "model_version": self.model_version
        }

    def predict_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run inference on entire DataFrame, returning dataframe with anomaly scores and flags.
        """
        if not self.is_fitted:
            raise RuntimeError("IsolationForestDetector has not been fitted or loaded.")

        X_scaled = self._extract_and_preprocess(df, fit_preprocessor=False)
        raw_scores = self.model.score_samples(X_scaled)
        preds = self.model.predict(X_scaled)
        norm_scores = self._compute_normalized_score(raw_scores)

        res = df.copy()
        res["if_raw_score"] = np.round(raw_scores, 4)
        res["if_anomaly_score"] = np.round(norm_scores, 4)
        res["if_is_anomaly"] = preds == -1
        return res

    def save(self, filepath: str = DEFAULT_MODEL_PATH) -> str:
        """Serialize trained detector artifact."""
        if not self.is_fitted:
            raise RuntimeError("Cannot save an unfitted model.")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        bundle = {
            "model": self.model,
            "imputer": self.imputer,
            "scaler": self.scaler,
            "features": self.features,
            "contamination": self.contamination,
            "n_estimators": self.n_estimators,
            "random_state": self.random_state,
            "model_version": self.model_version,
            "raw_offset_": self.raw_offset_
        }
        joblib.dump(bundle, filepath)
        return filepath

    @classmethod
    def load(cls, filepath: str = DEFAULT_MODEL_PATH) -> "IsolationForestDetector":
        """Load serialized detector artifact."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found at: {filepath}")
        bundle = joblib.load(filepath)
        detector = cls(
            n_estimators=bundle.get("n_estimators", 200),
            contamination=bundle.get("contamination", 0.02),
            random_state=bundle.get("random_state", 42),
            features=bundle.get("features", OFFICIAL_SECURITY_FEATURES),
            model_version=bundle.get("model_version", "iforest-v1.0")
        )
        detector.model = bundle["model"]
        detector.imputer = bundle["imputer"]
        detector.scaler = bundle["scaler"]
        detector.raw_offset_ = bundle.get("raw_offset_", float(detector.model.offset_))
        detector.is_fitted = True
        return detector


def train_and_evaluate_isolation_forest(
    features_csv: str = "data/features/locus_security_features.csv",
    model_output_path: str = DEFAULT_MODEL_PATH,
    plot_output_path: str = "docs/plots/isolation_forest_distribution.png"
) -> Tuple[IsolationForestDetector, pd.DataFrame]:
    """
    Train Isolation Forest on clean baseline security features, save model artifact,
    and generate distribution plot.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    df = pd.read_csv(features_csv)
    print(f"Loaded {len(df)} epochs from {features_csv} for Isolation Forest training.")

    detector = IsolationForestDetector(contamination=0.02, random_state=42)
    detector.fit(df)
    detector.save(model_output_path)
    print(f"Saved Isolation Forest model to {model_output_path}")

    # Evaluate
    df_eval = detector.predict_dataframe(df)
    anomaly_count = int(df_eval["if_is_anomaly"].sum())
    total_count = len(df_eval)
    pct = (anomaly_count / total_count) * 100.0
    print(f"Evaluated {total_count} records: {anomaly_count} flagged as anomaly ({pct:.2f}%).")

    # Generate distribution plot
    os.makedirs(os.path.dirname(plot_output_path), exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Raw score histogram
    ax1.hist(df_eval["if_raw_score"], bins=50, color="#2563eb", alpha=0.7, edgecolor="black")
    ax1.axvline(detector.raw_offset_, color="#dc2626", linestyle="--", linewidth=2,
                label=f"Decision Boundary ({detector.raw_offset_:.3f})")
    ax1.set_title("Isolation Forest Raw Decision Score Distribution", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Score Samples (Lower = More Anomalous)")
    ax1.set_ylabel("Epoch Count")
    ax1.legend(loc="upper left")
    ax1.grid(True, linestyle=":", alpha=0.5)

    # Calibrated Anomaly Score histogram
    ax2.hist(df_eval["if_anomaly_score"], bins=50, color="#10b981", alpha=0.7, edgecolor="black")
    ax2.axvline(0.5, color="#dc2626", linestyle="--", linewidth=2, label="Anomaly Threshold (0.50)")
    ax2.set_title("Calibrated Anomaly Score Distribution [0.0 - 1.0]", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Normalized Anomaly Score")
    ax2.set_ylabel("Epoch Count")
    ax2.legend(loc="upper right")
    ax2.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    plt.savefig(plot_output_path, dpi=300)
    plt.close()
    print(f"Generated Isolation Forest distribution plot at {plot_output_path}")

    return detector, df_eval


if __name__ == "__main__":
    train_and_evaluate_isolation_forest()
