"""
LOCUS Phase 5 — Evidence Fusion Engine

Module: src.evidence.evidence_bundle
Combines outputs from the four LOCUS detection paths:
1. Physical Plausibility Rules
2. Isolation Forest (Unsupervised)
3. XGBoost (Supervised Infrastructure)
4. LSTM Autoencoder (Temporal Dynamics)
together with raw GNSS location and data quality flags into an immutable,
structured Evidence Bundle for downstream SOC investigation.

CRITICAL PRINCIPLE:
Do NOT make a final SOC decision here.
The output of this phase is EVIDENCE, not the final verdict or explanation.
Final explanation and attribution will be handled by Phase 6 (AI Agents).
"""

import os
import uuid
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Union, Any
import numpy as np
import pandas as pd

DEFAULT_EVIDENCE_DIR = os.path.join("data", "evidence")


@dataclass
class LocationData:
    latitude: Optional[float]
    longitude: Optional[float]
    altitude_m: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceBundle:
    """
    Standardized, structured container for multi-detector GNSS security evidence.
    """
    event_id: str
    timestamp_utc: Optional[str]
    timestamp_pc: Optional[str]
    session_id: int
    epoch_id: Optional[int]
    location: Dict[str, Any]
    security_features: Dict[str, Optional[float]]
    physical_rules: Dict[str, Any]
    isolation_forest: Dict[str, Any]
    xgboost: Dict[str, Any]
    temporal_model: Dict[str, Any]
    data_quality: Dict[str, Any]
    model_versions: Dict[str, str]
    model_version: str = "locus-production-v5.5"
    model_training_date: str = "2026-10-04"
    feature_schema_version: str = "locus-sec-v2.0-10d"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def save(self, filepath: str) -> str:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        return filepath


class EvidenceFusionEngine:
    """
    Orchestrates the 4 detection paths and constructs structured Evidence Bundles
    using final tuned production models.
    """

    def __init__(
        self,
        rules_engine: Optional[Any] = None,
        iforest_detector: Optional[Any] = None,
        xgb_detector: Optional[Any] = None,
        temporal_detector: Optional[Any] = None,
        pipeline_tier: str = "PRODUCTION"
    ):
        from src.detection.physical_rules import PhysicalRulesEngine
        from src.detection.isolation_forest import IsolationForestDetector
        from src.detection.xgboost_detector import XGBoostDetector
        from src.detection.temporal_model import TemporalDetector

        self.rules_engine = rules_engine or PhysicalRulesEngine()
        self.pipeline_tier = pipeline_tier

        # 1. Load Isolation Forest (Production -> Tuned -> Baseline)
        if iforest_detector is not None:
            self.iforest_detector = iforest_detector
        else:
            candidates = [
                os.path.join("models", "production", "isolation_forest", "isolation_forest.joblib"),
                os.path.join("models", "isolation_forest", "isolation_forest_tuned.joblib"),
                os.path.join("models", "isolation_forest.joblib")
            ]
            self.iforest_detector = None
            for p in candidates:
                if os.path.exists(p):
                    self.iforest_detector = IsolationForestDetector.load(p)
                    break

        # 2. XGBoost Detector
        self.xgb_detector = xgb_detector or XGBoostDetector(model_version="xgb-ready-v1.1")

        # 3. Load Temporal Model (Production -> Tuned -> Baseline)
        if temporal_detector is not None:
            self.temporal_detector = temporal_detector
        else:
            temp_candidates = [
                (os.path.join("models", "production", "temporal", "temporal_model.pt"),
                 os.path.join("models", "production", "temporal", "temporal_metadata.joblib")),
                (os.path.join("models", "temporal", "temporal_model_tuned.pt"),
                 os.path.join("models", "temporal", "temporal_metadata_tuned.joblib")),
                (os.path.join("models", "temporal_model.pt"),
                 os.path.join("models", "temporal_metadata.joblib"))
            ]
            self.temporal_detector = None
            for w, m in temp_candidates:
                if os.path.exists(w) and os.path.exists(m):
                    self.temporal_detector = TemporalDetector.load(w, m)
                    break

    def build_bundle(
        self,
        epoch_data: Union[Dict[str, Any], pd.Series],
        event_id: Optional[str] = None,
        precomputed_if: Optional[Dict[str, Any]] = None,
        precomputed_temp: Optional[Dict[str, Any]] = None
    ) -> EvidenceBundle:
        """
        Evaluate a single epoch against all four detection engines and assemble the bundle.
        Supports fast precomputed inference dictionaries for batch processing.
        """
        row = epoch_data.to_dict() if isinstance(epoch_data, pd.Series) else dict(epoch_data)

        # 1. Identifiers & Timestamps
        evt_id = event_id or f"evt_{uuid.uuid4().hex[:12]}"
        ts_utc = str(row.get("timestamp_utc", "")) if pd.notna(row.get("timestamp_utc")) else None
        ts_pc = str(row.get("timestamp_pc", "")) if pd.notna(row.get("timestamp_pc")) else None
        sess_id = int(row.get("session_id", 0))
        ep_id = int(row["epoch_id"]) if "epoch_id" in row and pd.notna(row["epoch_id"]) else None

        # 2. Location
        lat = float(row["latitude"]) if "latitude" in row and pd.notna(row["latitude"]) else None
        lon = float(row["longitude"]) if "longitude" in row and pd.notna(row["longitude"]) else None
        alt = float(row["altitude_m"]) if "altitude_m" in row and pd.notna(row["altitude_m"]) else None
        location = {"latitude": lat, "longitude": lon, "altitude_m": alt}

        # 3. Security Features (Official 10-D Vector)
        sec_features = {}
        for feat in OFFICIAL_SECURITY_FEATURES:
            val = row.get(feat, None)
            if val is not None and pd.notna(val):
                try:
                    fval = float(val)
                    sec_features[feat] = round(fval, 4) if np.isfinite(fval) else None
                except (ValueError, TypeError):
                    sec_features[feat] = None
            else:
                sec_features[feat] = None

        # 4. Detector 1: Physical Rules Engine
        rule_evals = self.rules_engine.evaluate_epoch(row)
        rules_summary = self.rules_engine.get_summary(rule_evals)

        # 5. Detector 2: Isolation Forest
        if precomputed_if is not None:
            if_out = precomputed_if
        elif self.iforest_detector is not None and self.iforest_detector.is_fitted:
            if_out = self.iforest_detector.predict_epoch(row)
        else:
            if_out = {
                "is_anomaly": False,
                "anomaly_score": None,
                "raw_score": None,
                "model_version": "iforest-unloaded",
                "status": "UNAVAILABLE"
            }

        # 6. Detector 3: XGBoost Supervised
        xgb_out = self.xgb_detector.predict_epoch(row)

        # 7. Detector 4: Temporal Model (LSTM)
        if precomputed_temp is not None:
            temp_out = precomputed_temp
        elif self.temporal_detector is not None and self.temporal_detector.is_fitted:
            temp_out = self.temporal_detector.process_epoch_stream(row)
        else:
            temp_out = {
                "status": "UNAVAILABLE",
                "is_anomaly": False,
                "temporal_anomaly_score": None,
                "reconstruction_error": None,
                "model_version": "lstm-unloaded"
            }

        # 8. Data Quality Context
        dq_context = {
            "fix_quality": int(row["fix_quality"]) if "fix_quality" in row and pd.notna(row["fix_quality"]) else None,
            "satellites_used": int(row["satellites_used"]) if "satellites_used" in row and pd.notna(row["satellites_used"]) else None,
            "satellites_in_view": int(row["satellites_in_view"]) if "satellites_in_view" in row and pd.notna(row["satellites_in_view"]) else None,
            "hdop": float(row["hdop"]) if "hdop" in row and pd.notna(row["hdop"]) else (sec_features.get("HDOP")),
            "avg_cno": float(row["avg_cno"]) if "avg_cno" in row and pd.notna(row["avg_cno"]) else None,
            "data_quality_flag": str(row["data_quality_flag"]) if "data_quality_flag" in row and pd.notna(row["data_quality_flag"]) else "VALID"
        }

        # 9. Model Versions & Metadata
        model_versions = {
            "physical_rules_version": "prules-v1.1",
            "isolation_forest_version": if_out.get("model_version", "unknown"),
            "xgboost_version": xgb_out.get("model_version", "unknown"),
            "temporal_model_version": temp_out.get("model_version", "unknown"),
            "pipeline_tier": self.pipeline_tier
        }

        return EvidenceBundle(
            event_id=evt_id,
            timestamp_utc=ts_utc,
            timestamp_pc=ts_pc,
            session_id=sess_id,
            epoch_id=ep_id,
            location=location,
            security_features=sec_features,
            physical_rules=rules_summary,
            isolation_forest=if_out,
            xgboost=xgb_out,
            temporal_model=temp_out,
            data_quality=dq_context,
            model_versions=model_versions,
            model_version=f"locus-{self.pipeline_tier.lower()}-v5.5",
            model_training_date="2026-10-04",
            feature_schema_version="locus-sec-v2.0-10d"
        )

    def process_features_csv(
        self,
        features_csv: str = "data/features/locus_security_features.csv",
        structured_csv: Optional[str] = "data/structured/locus_structured_gnss.csv",
        output_dir: str = DEFAULT_EVIDENCE_DIR,
        sample_size: int = 100
    ) -> List[EvidenceBundle]:
        """
        Process the security feature dataset, join raw data quality columns from structured data if available,
        and generate sample evidence bundles using high-performance vectorized detector evaluation.
        """
        os.makedirs(output_dir, exist_ok=True)
        df_feat = pd.read_csv(features_csv)

        # Merge with structured dataset to enrich location & raw quality fields if available
        if structured_csv and os.path.exists(structured_csv):
            df_struct = pd.read_csv(structured_csv)
            merge_cols = [c for c in df_struct.columns if c not in df_feat.columns or c in ["session_id", "epoch_id"]]
            if "epoch_id" in df_feat.columns and "epoch_id" in df_struct.columns:
                df = pd.merge(df_feat, df_struct[merge_cols], on=["session_id", "epoch_id"], how="left")
            else:
                df = df_feat
        else:
            df = df_feat

        print(f"Generating Evidence Bundles for {len(df)} epochs...")

        # 1. Vectorized Isolation Forest evaluation across full dataset
        if_lookup = {}
        if self.iforest_detector is not None and self.iforest_detector.is_fitted:
            print("Running vectorized Isolation Forest inference across dataset...")
            if_eval_df = self.iforest_detector.predict_dataframe(df)
            raw_scores = if_eval_df["if_raw_score"].values
            anom_scores = if_eval_df["if_anomaly_score"].values
            is_anoms = if_eval_df["if_is_anomaly"].values
            for i in range(len(df)):
                if_lookup[i] = {
                    "is_anomaly": bool(is_anoms[i]),
                    "anomaly_score": round(float(anom_scores[i]), 4),
                    "raw_score": round(float(raw_scores[i]), 4),
                    "decision_offset": round(float(self.iforest_detector.raw_offset_), 4),
                    "model_version": self.iforest_detector.model_version
                }

        # 2. Vectorized Temporal Sequence Model evaluation across sessions
        temp_lookup = {}
        if self.temporal_detector is not None and self.temporal_detector.is_fitted:
            print("Running vectorized Temporal Sequence Model inference across sessions...")
            seqs, metas = self.temporal_detector.generate_sequences(df, fit_preprocessor=False)
            if len(seqs) > 0:
                temp_results = self.temporal_detector.predict_sequences_batch(seqs, batch_size=256)
                for meta, res in zip(metas, temp_results):
                    key = (meta["session_id"], meta.get("epoch_id"))
                    temp_lookup[key] = res

        records = df.to_dict(orient="records")
        bundles: List[EvidenceBundle] = []

        # Process sequential epochs with precomputed ML inference
        for idx, row in enumerate(records):
            sess_id = int(row.get("session_id", 0))
            ep_id = int(row["epoch_id"]) if "epoch_id" in row and pd.notna(row["epoch_id"]) else None

            p_if = if_lookup.get(idx, None)
            p_temp = temp_lookup.get((sess_id, ep_id), None)
            if p_temp is None:
                p_temp = {
                    "status": "BUFFERING",
                    "buffer_fill": min(idx + 1, self.temporal_detector.window_size if self.temporal_detector else 10),
                    "window_size": self.temporal_detector.window_size if self.temporal_detector else 10,
                    "is_anomaly": False,
                    "temporal_anomaly_score": 0.0,
                    "reconstruction_error": 0.0,
                    "model_version": getattr(self.temporal_detector, "model_version", "unknown")
                }

            bundle = self.build_bundle(
                row,
                event_id=f"evt_{sess_id}_{ep_id or idx}",
                precomputed_if=p_if,
                precomputed_temp=p_temp
            )
            bundles.append(bundle)

        # Save individual sample bundles (first 10, middle 10, and any anomalous ones)
        sample_indices = set(range(min(15, len(bundles))))
        # Find any epochs where rules or isolation forest triggered
        anomalous_indices = [
            i for i, b in enumerate(bundles)
            if b.physical_rules["is_anomalous"] or b.isolation_forest.get("is_anomaly", False) or b.temporal_model.get("is_anomaly", False)
        ]
        sample_indices.update(anomalous_indices[:30])

        samples_saved = 0
        for i in sorted(sample_indices):
            sample_bundle = bundles[i]
            fname = f"evidence_{sample_bundle.session_id}_{sample_bundle.epoch_id or i}.json"
            sample_bundle.save(os.path.join(output_dir, fname))
            samples_saved += 1

        # Also write a consolidated JSONL stream of all generated evidence
        jsonl_path = os.path.join(output_dir, "evidence_stream_sample.jsonl")
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for b in bundles[:sample_size]:
                f.write(json.dumps(b.to_dict(), default=str) + "\n")

        print(f"Generated {len(bundles)} total evidence bundles.")
        print(f"Saved {samples_saved} individual JSON bundles to {output_dir}")
        print(f"Saved consolidated stream sample ({sample_size} epochs) to {jsonl_path}")

        return bundles
