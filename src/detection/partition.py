"""
LOCUS Phase 5.5 — Data Partitioning & Leakage Prevention Module

Module: src.detection.partition
Implements strict, reproducible, leakage-free session-aware chronological partitioning
for tabular and temporal GNSS security models.

Guarantees:
1. Chronological order preserved: Train -> Validation -> Test.
2. Session boundary preservation: no cross-session sequence generation.
3. Buffer isolation: 30-epoch temporal gap between Validation and Test in Session 15
   to guarantee zero temporal sequence window overlap.
4. Strict Scaler/Imputer isolation: Scalers and imputers are fit EXCLUSIVELY on Train data.
   Validation and Test sets are transformed using .transform().
5. Final Test set isolation: Test partition remains strictly untouched during hyperparameter tuning.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler

from src.detection.isolation_forest import OFFICIAL_SECURITY_FEATURES


@dataclass
class DatasetSplits:
    train_df: pd.DataFrame
    val_df: pd.DataFrame
    test_df: pd.DataFrame
    imputer: SimpleImputer
    scaler: RobustScaler
    features: List[str]

    @property
    def summary(self) -> Dict[str, Any]:
        return {
            "train_epochs": len(self.train_df),
            "val_epochs": len(self.val_df),
            "test_epochs": len(self.test_df),
            "total_epochs": len(self.train_df) + len(self.val_df) + len(self.test_df),
            "train_sessions": sorted(self.train_df["session_id"].unique().tolist()),
            "val_sessions": sorted(self.val_df["session_id"].unique().tolist()),
            "test_sessions": sorted(self.test_df["session_id"].unique().tolist()),
            "features": self.features
        }


def partition_security_dataset(
    features_csv: str = "data/features/locus_security_features.csv",
    features: Optional[List[str]] = None,
    buffer_epochs: int = 30
) -> DatasetSplits:
    """
    Partition the 10-D GNSS security features chronologically and by session.
    
    Split Strategy:
    - Train (50.6%): Sessions 4, 5, 9, 10 (4,749 epochs)
    - Validation (24.5%): Session 11 (31 epochs) + Session 15 (first 2,270 epochs) -> 2,301 epochs
    - Safety Buffer: 30 epochs in Session 15 (skipped to prevent sliding window leakage)
    - Test (24.5%): Session 15 (remaining 2,302 epochs)
    
    Returns:
        DatasetSplits containing partitioned DataFrames, and fitted train-only imputer & scaler.
    """
    sec_features = features or list(OFFICIAL_SECURITY_FEATURES)
    df = pd.read_csv(features_csv)

    # 1. Train partition: Sessions 4, 5, 9, 10
    train_mask = df["session_id"].isin([4, 5, 9, 10])
    train_df = df[train_mask].copy().reset_index(drop=True)

    # 2. Validation partition: Session 11 + first part of Session 15
    sess11 = df[df["session_id"] == 11].copy()
    sess15 = df[df["session_id"] == 15].copy().sort_values("timestamp_pc").reset_index(drop=True)

    sess15_val_cutoff = 2270
    sess15_test_start = sess15_val_cutoff + buffer_epochs  # 2300

    sess15_val = sess15.iloc[:sess15_val_cutoff].copy()
    val_df = pd.concat([sess11, sess15_val], ignore_index=True)

    # 3. Test partition: Remaining part of Session 15 after buffer
    test_df = sess15.iloc[sess15_test_start:].copy().reset_index(drop=True)

    # 4. Strict Preprocessor fitting: fit ONLY on train_df
    imputer = SimpleImputer(strategy="median", fill_value=0.0)
    scaler = RobustScaler()

    X_train_raw = train_df[sec_features].to_numpy(dtype=np.float64)
    all_nan_mask = np.all(np.isnan(X_train_raw), axis=0)
    if np.any(all_nan_mask):
        X_train_raw[:, all_nan_mask] = 0.0

    X_train_imp = imputer.fit_transform(X_train_raw)
    scaler.fit(X_train_imp)

    return DatasetSplits(
        train_df=train_df,
        val_df=val_df,
        test_df=test_df,
        imputer=imputer,
        scaler=scaler,
        features=sec_features
    )


def transform_features(
    df: pd.DataFrame,
    splits: DatasetSplits
) -> np.ndarray:
    """
    Transform feature DataFrame using the strictly train-fitted imputer and scaler.
    """
    X_raw = df[splits.features].to_numpy(dtype=np.float64)
    all_nan_mask = np.all(np.isnan(X_raw), axis=0)
    if np.any(all_nan_mask):
        X_raw[:, all_nan_mask] = 0.0

    X_imp = splits.imputer.transform(X_raw)
    X_scaled = splits.scaler.transform(X_imp)
    return X_scaled
