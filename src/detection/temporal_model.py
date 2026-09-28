"""
LOCUS Phase 5 — LSTM Temporal Sequence Anomaly Detector

Module: src.detection.temporal_model
Implements sequential temporal anomaly detection using an LSTM Autoencoder
on sliding windows of the official 10-D GNSS security feature vector.

Key Architectural Guarantees:
1. Strict session boundary preservation: sliding windows NEVER cross session boundaries.
2. Chronological data splitting: no random temporal window shuffling to prevent data leakage.
3. Feature consistency: utilizes exclusively the 10-D official security feature vector.
4. Explainable temporal attribution: per-feature reconstruction error tracking.
"""

import os
import json
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
import pandas as pd
import joblib

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import RobustScaler
from sklearn.impute import SimpleImputer

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

DEFAULT_MODEL_WEIGHTS = os.path.join("models", "temporal_model.pt")
DEFAULT_METADATA_PATH = os.path.join("models", "temporal_metadata.joblib")


class GNSSSequenceDataset(Dataset):
    """PyTorch Dataset for GNSS temporal feature sequences."""

    def __init__(self, sequences: np.ndarray):
        self.sequences = torch.tensor(sequences, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, idx: int) -> torch.Tensor:
        return self.sequences[idx]


class LSTMAutoencoder(nn.Module):
    """
    LSTM Autoencoder for temporal anomaly detection in GNSS time-series.
    Encodes a temporal sequence (W, 10) into a latent representation
    and decodes back to (W, 10). Anomalous temporal dynamics produce elevated reconstruction error.
    """

    def __init__(self, input_dim: int = 10, hidden_dim: int = 32, num_layers: int = 1):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # Encoder
        self.encoder = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True
        )

        # Decoder
        self.decoder = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True
        )
        self.output_layer = nn.Linear(hidden_dim, input_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch_size, seq_len, input_dim)
        batch_size, seq_len, _ = x.shape

        # Encode: get hidden state of last time-step
        _, (h_n, _) = self.encoder(x)
        # h_n shape: (num_layers, batch_size, hidden_dim)
        latent = h_n[-1]  # (batch_size, hidden_dim)

        # Repeat latent vector across time steps for decoding
        repeated = latent.unsqueeze(1).repeat(1, seq_len, 1)  # (batch_size, seq_len, hidden_dim)

        # Decode
        decoded, _ = self.decoder(repeated)
        reconstruction = self.output_layer(decoded)  # (batch_size, seq_len, input_dim)

        return reconstruction


class TemporalDetector:
    """
    Manages preprocessing, training, persistence, and sequential inference
    for the GNSS LSTM Autoencoder.
    """

    def __init__(
        self,
        window_size: int = 10,
        hidden_dim: int = 32,
        num_layers: int = 1,
        features: Optional[List[str]] = None,
        model_version: str = "lstm-temporal-v1.0",
        device: Optional[str] = None
    ):
        self.window_size = window_size
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.features = features or list(OFFICIAL_SECURITY_FEATURES)
        self.model_version = model_version
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.imputer = SimpleImputer(strategy="median", fill_value=0.0)
        self.scaler = RobustScaler()
        self.model = LSTMAutoencoder(
            input_dim=len(self.features),
            hidden_dim=hidden_dim,
            num_layers=num_layers
        ).to(self.device)

        self.is_fitted = False
        self.error_threshold = 0.5
        self.mean_error = 0.1
        self.std_error = 0.1

        # Real-time streaming buffer for single-epoch inference
        self._current_session_id = None
        self._streaming_buffer: List[np.ndarray] = []

    def generate_sequences(
        self, df: pd.DataFrame, fit_preprocessor: bool = False
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Extract sliding windows of length window_size respecting session boundaries.
        Windows NEVER span across session boundaries.
        """
        # Ensure official features exist
        data = df.copy()
        for f in self.features:
            if f not in data.columns:
                data[f] = np.nan

        # Impute and scale features
        feat_matrix = data[self.features].to_numpy(dtype=np.float64)
        all_nan_mask = np.all(np.isnan(feat_matrix), axis=0)
        if np.any(all_nan_mask):
            feat_matrix[:, all_nan_mask] = 0.0

        if fit_preprocessor:
            feat_imp = self.imputer.fit_transform(feat_matrix)
            feat_scaled = self.scaler.fit_transform(feat_imp)
        else:
            feat_imp = self.imputer.transform(feat_matrix)
            feat_scaled = self.scaler.transform(feat_imp)

        scaled_df = pd.DataFrame(feat_scaled, columns=self.features)
        scaled_df["session_id"] = data["session_id"].values
        if "epoch_id" in data.columns:
            scaled_df["epoch_id"] = data["epoch_id"].values
        if "timestamp_utc" in data.columns:
            scaled_df["timestamp_utc"] = data["timestamp_utc"].values

        sequences = []
        metadata = []

        # Group by session_id to guarantee zero cross-session leakage
        for sess_id, group in scaled_df.groupby("session_id", sort=False):
            n_epochs = len(group)
            if n_epochs < self.window_size:
                continue

            vals = group[self.features].to_numpy()
            for i in range(n_epochs - self.window_size + 1):
                win = vals[i : i + self.window_size]
                sequences.append(win)

                final_epoch = group.iloc[i + self.window_size - 1]
                meta = {
                    "session_id": sess_id,
                    "window_end_idx": i + self.window_size - 1,
                    "epoch_id": final_epoch.get("epoch_id", None),
                    "timestamp_utc": final_epoch.get("timestamp_utc", None)
                }
                metadata.append(meta)

        return np.array(sequences, dtype=np.float32), metadata

    def fit(
        self,
        df: pd.DataFrame,
        epochs: int = 15,
        batch_size: int = 64,
        lr: float = 0.002,
        val_split: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train the LSTM Autoencoder on clean sequential windows.
        Splits chronologically by session / time to respect temporal ordering.
        """
        # Fit preprocessor on full data or training partition
        sequences, meta = self.generate_sequences(df, fit_preprocessor=True)
        if len(sequences) == 0:
            raise ValueError(f"Insufficient data to form windows of size {self.window_size}")

        # Chronological train/val split (no shuffling of sequences)
        split_idx = int(len(sequences) * (1.0 - val_split))
        train_seqs = sequences[:split_idx]
        val_seqs = sequences[split_idx:]

        train_loader = DataLoader(GNSSSequenceDataset(train_seqs), batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(GNSSSequenceDataset(val_seqs), batch_size=batch_size, shuffle=False)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr, weight_decay=1e-5)
        criterion = nn.MSELoss()

        self.model.train()
        history = {"train_loss": [], "val_loss": []}

        for epoch in range(epochs):
            self.model.train()
            total_train_loss = 0.0
            for batch in train_loader:
                batch = batch.to(self.device)
                optimizer.zero_grad()
                recon = self.model(batch)
                loss = criterion(recon, batch)
                loss.backward()
                optimizer.step()
                total_train_loss += loss.item() * len(batch)

            avg_train_loss = total_train_loss / len(train_seqs)

            # Validation
            self.model.eval()
            total_val_loss = 0.0
            with torch.no_grad():
                for batch in val_loader:
                    batch = batch.to(self.device)
                    recon = self.model(batch)
                    val_loss = criterion(recon, batch)
                    total_val_loss += val_loss.item() * len(batch)

            avg_val_loss = total_val_loss / len(val_seqs) if len(val_seqs) > 0 else avg_train_loss
            history["train_loss"].append(round(avg_train_loss, 5))
            history["val_loss"].append(round(avg_val_loss, 5))

        # Calibrate reconstruction error threshold on validation set
        self.model.eval()
        all_val_errors = []
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(self.device)
                recon = self.model(batch)
                # MSE per sequence
                errs = torch.mean((recon - batch) ** 2, dim=(1, 2)).cpu().numpy()
                all_val_errors.extend(errs)

        val_err_arr = np.array(all_val_errors) if len(all_val_errors) > 0 else np.array([avg_train_loss])
        self.mean_error = float(np.mean(val_err_arr))
        self.std_error = float(np.std(val_err_arr))
        # Threshold: 98th percentile or mean + 3*std
        self.error_threshold = float(np.percentile(val_err_arr, 98) if len(val_err_arr) > 50 else (self.mean_error + 3 * self.std_error))

        self.is_fitted = True
        return {
            "status": "trained",
            "epochs": epochs,
            "train_loss_final": history["train_loss"][-1],
            "val_loss_final": history["val_loss"][-1],
            "mean_reconstruction_error": round(self.mean_error, 4),
            "std_reconstruction_error": round(self.std_error, 4),
            "error_threshold": round(self.error_threshold, 4),
            "total_sequences": len(sequences),
            "train_sequences": len(train_seqs),
            "val_sequences": len(val_seqs)
        }

    def predict_window(self, window_matrix: np.ndarray) -> Dict[str, Any]:
        """
        Evaluate a single (W, 10) unscaled window matrix.
        Returns:
            reconstruction_error: float
            temporal_anomaly_score: float in [0, 1]
            is_anomaly: bool
            feature_errors: dict of per-feature errors
        """
        if not self.is_fitted:
            raise RuntimeError("TemporalDetector is not fitted or loaded.")

        # Impute and scale
        win_clean = window_matrix.copy()
        nan_mask = np.isnan(win_clean)
        if np.any(nan_mask):
            win_clean[nan_mask] = 0.0
        win_imp = self.imputer.transform(win_clean)
        win_scaled = self.scaler.transform(win_imp)

        tensor_in = torch.tensor(win_scaled, dtype=torch.float32).unsqueeze(0).to(self.device)
        self.model.eval()
        with torch.no_grad():
            recon = self.model(tensor_in)
            diff = (recon - tensor_in).squeeze(0).cpu().numpy()

        # Mean squared error across window
        total_mse = float(np.mean(diff ** 2))
        per_feature_mse = {
            self.features[i]: round(float(np.mean(diff[:, i] ** 2)), 4)
            for i in range(len(self.features))
        }

        # Calibrate anomaly score to [0, 1] around threshold
        diff_from_thresh = total_mse - self.error_threshold
        # Logistic sigmoid scaling
        anomaly_score = 1.0 / (1.0 + np.exp(-10.0 * diff_from_thresh / max(self.std_error, 1e-4)))

        return {
            "is_anomaly": total_mse > self.error_threshold,
            "reconstruction_error": round(total_mse, 4),
            "temporal_anomaly_score": round(float(anomaly_score), 4),
            "error_threshold": round(self.error_threshold, 4),
            "feature_errors": per_feature_mse,
            "model_version": self.model_version
        }

    def predict_sequences_batch(self, scaled_sequences: np.ndarray, batch_size: int = 256) -> List[Dict[str, Any]]:
        """
        High-performance vectorized batch inference across temporal sequence windows.
        """
        if not self.is_fitted:
            raise RuntimeError("TemporalDetector is not fitted.")
        if len(scaled_sequences) == 0:
            return []

        results = []
        self.model.eval()
        with torch.no_grad():
            for i in range(0, len(scaled_sequences), batch_size):
                batch = torch.tensor(scaled_sequences[i : i + batch_size], dtype=torch.float32).to(self.device)
                recon = self.model(batch)
                diff = (recon - batch).cpu().numpy()
                total_mses = np.mean(diff ** 2, axis=(1, 2))
                feat_mses = np.mean(diff ** 2, axis=1)

                for b in range(len(batch)):
                    mse_val = float(total_mses[b])
                    diff_thresh = mse_val - self.error_threshold
                    anom_score = 1.0 / (1.0 + np.exp(-10.0 * diff_thresh / max(self.std_error, 1e-4)))
                    pfeat = {
                        self.features[j]: round(float(feat_mses[b, j]), 4)
                        for j in range(len(self.features))
                    }
                    results.append({
                        "status": "INFERRED",
                        "is_anomaly": mse_val > self.error_threshold,
                        "reconstruction_error": round(mse_val, 4),
                        "temporal_anomaly_score": round(float(anom_score), 4),
                        "error_threshold": round(self.error_threshold, 4),
                        "feature_errors": pfeat,
                        "model_version": self.model_version
                    })
        return results

    def reset_buffer(self) -> None:
        """Explicitly clear internal streaming buffer and reset session tracking."""
        self._current_session_id = None
        self._streaming_buffer.clear()

    def process_epoch_stream(self, epoch: Union[Dict[str, Any], pd.Series]) -> Dict[str, Any]:
        """
        Ingest a single epoch from a real-time stream.
        Maintains sequential buffer per session.
        Returns evaluation once window is filled.
        """
        sess_id = epoch.get("session_id")
        if sess_id != self._current_session_id:
            # Session changed: reset buffer to prevent cross-session leakage
            self._current_session_id = sess_id
            self._streaming_buffer.clear()

        # Extract 10-D vector
        row_vals = []
        for f in self.features:
            v = epoch.get(f, None) if isinstance(epoch, dict) else (epoch.get(f, None) if hasattr(epoch, "get") else epoch[f])
            if v is None or v != v:  # NaN check
                row_vals.append(0.0)
            else:
                try:
                    row_vals.append(float(v))
                except (ValueError, TypeError):
                    row_vals.append(0.0)
        self._streaming_buffer.append(np.array(row_vals, dtype=np.float64))

        if len(self._streaming_buffer) < self.window_size:
            return {
                "status": "BUFFERING",
                "buffer_fill": len(self._streaming_buffer),
                "window_size": self.window_size,
                "is_anomaly": False,
                "temporal_anomaly_score": 0.0,
                "reconstruction_error": 0.0,
                "model_version": self.model_version
            }

        # Maintain sliding window of size window_size
        if len(self._streaming_buffer) > self.window_size:
            self._streaming_buffer.pop(0)

        window_mat = np.array(self._streaming_buffer, dtype=np.float64)
        result = self.predict_window(window_mat)
        result["status"] = "INFERRED"
        result["session_id"] = sess_id
        return result

    def save(
        self,
        weights_path: str = DEFAULT_MODEL_WEIGHTS,
        meta_path: str = DEFAULT_METADATA_PATH
    ) -> Tuple[str, str]:
        """Save PyTorch weights and preprocessing metadata."""
        if not self.is_fitted:
            raise RuntimeError("Cannot save an unfitted model.")
        os.makedirs(os.path.dirname(weights_path), exist_ok=True)

        torch.save(self.model.state_dict(), weights_path)

        metadata = {
            "window_size": self.window_size,
            "hidden_dim": self.hidden_dim,
            "num_layers": self.num_layers,
            "features": self.features,
            "model_version": self.model_version,
            "imputer": self.imputer,
            "scaler": self.scaler,
            "error_threshold": self.error_threshold,
            "mean_error": self.mean_error,
            "std_error": self.std_error
        }
        joblib.dump(metadata, meta_path)
        return weights_path, meta_path

    @classmethod
    def load(
        cls,
        weights_path: str = DEFAULT_MODEL_WEIGHTS,
        meta_path: str = DEFAULT_METADATA_PATH,
        device: Optional[str] = None
    ) -> "TemporalDetector":
        """Load trained model and preprocessing pipeline."""
        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"Model weights not found at: {weights_path}")
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Metadata not found at: {meta_path}")

        meta = joblib.load(meta_path)
        detector = cls(
            window_size=meta.get("window_size", 10),
            hidden_dim=meta.get("hidden_dim", 32),
            num_layers=meta.get("num_layers", 1),
            features=meta.get("features", OFFICIAL_SECURITY_FEATURES),
            model_version=meta.get("model_version", "lstm-temporal-v1.0"),
            device=device
        )
        detector.imputer = meta["imputer"]
        detector.scaler = meta["scaler"]
        detector.error_threshold = meta.get("error_threshold", 0.5)
        detector.mean_error = meta.get("mean_error", 0.1)
        detector.std_error = meta.get("std_error", 0.1)

        state_dict = torch.load(weights_path, map_location=detector.device)
        detector.model.load_state_dict(state_dict)
        detector.model.eval()
        detector.is_fitted = True
        return detector


def train_temporal_model(
    features_csv: str = "data/features/locus_security_features.csv",
    weights_path: str = DEFAULT_MODEL_WEIGHTS,
    meta_path: str = DEFAULT_METADATA_PATH,
    epochs: int = 15
) -> TemporalDetector:
    """
    Train and save LSTM Autoencoder on clean baseline GNSS time-series.
    """
    df = pd.read_csv(features_csv)
    print(f"Loaded {len(df)} epochs from {features_csv} for LSTM temporal training.")

    detector = TemporalDetector(window_size=10, hidden_dim=32, num_layers=1)
    train_res = detector.fit(df, epochs=epochs, batch_size=64)
    print(f"Training completed: {train_res}")

    detector.save(weights_path, meta_path)
    print(f"Saved temporal model weights to {weights_path} and metadata to {meta_path}")
    return detector


if __name__ == "__main__":
    train_temporal_model()
