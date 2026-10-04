"""
preprocessing.py - Data Validation, Quality Flagging, and Structured GNSS Dataset Exporter.

Part of LOCUS Phase 2: NMEA Parsing & Preprocessing Refactor.
Transforms raw telemetry/observations into standardized data/structured/locus_structured_gnss.csv
with explicit quality flags, session demarcation, and atomic UTC time synchronization.
"""

from enum import Flag, auto
import os
import sys
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd


class QualityFlag:
    """Explicit data quality classification tags."""
    VALID = "VALID"                     # Fix is locked and within physical bounds
    NO_FIX = "NO_FIX"                   # Fix quality 0 / searching
    INVALID_COORDS = "INVALID_COORDS"   # Coordinates out of WGS-84 boundaries
    DEGRADED_DOP = "DEGRADED_DOP"       # HDOP > 3.0 or PDOP > 5.0 (poor geometry)
    LOW_CNO = "LOW_CNO"                 # Average C/N0 < 20 dB-Hz (weak signal / noise)
    SESSION_START = "SESSION_START"     # First epoch after session gap (> 5.0s)
    DUPLICATE_EPOCH = "DUPLICATE_EPOCH" # Identical timestamp to preceding epoch
    PRN_UNAVAILABLE = "PRN_UNAVAILABLE" # Satellite PRN identities missing from raw feed


class GNSSPreprocessor:
    """
    Validates, enriches, and structures raw GNSS telemetry into canonical observation datasets.
    """

    def __init__(self, session_gap_threshold_s: float = 5.0, local_tz_offset_h: float = 5.5):
        self.session_gap_threshold_s = session_gap_threshold_s
        self.local_tz_offset_h = local_tz_offset_h

    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """Verify coordinates fall within valid WGS-84 bounding boxes."""
        if lat is None or lon is None or np.isnan(lat) or np.isnan(lon):
            return False
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return False
        # Treat exactly 0.0, 0.0 as invalid (Null Island) unless verified
        if abs(lat) < 1e-6 and abs(lon) < 1e-6:
            return False
        return True

    def process_telemetry_df(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Ingest raw telemetry dataframe and generate the canonical structured GNSS dataset.

        Parameters
        ----------
        raw_df : pd.DataFrame
            Raw telemetry dataframe (from locus_telemetry_features.csv).

        Returns
        -------
        pd.DataFrame
            Structured GNSS observation dataframe.
        """
        df = raw_df.copy()
        n = len(df)

        # 1. Parse PC timestamps & detect sessions
        pc_dts = pd.to_datetime(df["timestamp_pc"])
        pc_diffs = pc_dts.diff().dt.total_seconds()
        is_new_session = (pc_diffs > self.session_gap_threshold_s) | pc_diffs.isna()
        df["session_id"] = is_new_session.cumsum()
        df["epoch_id"] = df.groupby("session_id").cumcount() + 1
        df["is_session_start"] = is_new_session

        # 2. Reconstruct high-precision GNSS UTC timestamps
        utc_dates = (pc_dts - pd.Timedelta(hours=self.local_tz_offset_h)).dt.strftime("%Y-%m-%d")
        clean_time_str = df["timestamp_utc"].astype(str).str.replace("+00:00", "", regex=False).str.strip()

        gnss_iso_strings = []
        for idx, (d_str, t_str, fix) in enumerate(zip(utc_dates, clean_time_str, df["fix_quality"])):
            if fix > 0 and t_str and t_str != "nan":
                gnss_iso_strings.append(f"{d_str}T{t_str}Z")
            else:
                approx_dt = pc_dts.iloc[idx] - pd.Timedelta(hours=self.local_tz_offset_h)
                gnss_iso_strings.append(approx_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

        parsed_gnss = pd.to_datetime(gnss_iso_strings, format="ISO8601", utc=True)
        df["timestamp_gnss"] = parsed_gnss.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # 3. Handle satellite PRNs and in-view correction
        if "satellite_prns" in df.columns:
            has_prn_data = df["satellite_prns"].dropna().str.len().gt(0).any()
        else:
            df["satellite_prns"] = ""
            has_prn_data = False

        s_used = df["satellites_used"].astype(int)
        s_view_raw = df["satellites_in_view"].astype(int)
        hdop_vals = pd.to_numeric(df["hdop"], errors="coerce").fillna(1.0)

        # Apply multi-constellation correction if raw satellites in view is truncated
        is_truncated = (s_view_raw < s_used) | (s_view_raw <= 5)
        extra_sats = np.maximum(2.0, np.round(s_used * 0.22 + (hdop_vals - 0.9).clip(lower=0) * 2.0))
        s_view_clean = np.where(is_truncated & (s_used > 0), s_used + extra_sats, s_view_raw)
        df["satellites_in_view_clean"] = np.maximum(s_view_clean, s_used).astype(int)

        # 4. Detect duplicate epochs
        is_duplicate = df["timestamp_pc"].duplicated(keep="first")

        # 5. Build explicit quality flags per record
        quality_flags = []
        for i in range(n):
            flags = []
            fix = df["fix_quality"].iloc[i]
            lat = df["latitude"].iloc[i]
            lon = df["longitude"].iloc[i]
            hdop = df["hdop"].iloc[i]
            pdop = df["pdop"].iloc[i]
            avg_cno = df["avg_cno"].iloc[i]
            is_start = df["is_session_start"].iloc[i]
            is_dup = is_duplicate.iloc[i]

            if is_dup:
                flags.append(QualityFlag.DUPLICATE_EPOCH)

            if is_start:
                flags.append(QualityFlag.SESSION_START)

            if fix == 0:
                flags.append(QualityFlag.NO_FIX)
            else:
                # Validate coordinates
                if not self.validate_coordinates(lat, lon):
                    flags.append(QualityFlag.INVALID_COORDS)
                else:
                    flags.append(QualityFlag.VALID)

            # Check geometry degradation
            if (pd.notnull(hdop) and hdop > 3.0) or (pd.notnull(pdop) and pdop > 5.0):
                flags.append(QualityFlag.DEGRADED_DOP)

            # Check signal degradation
            if pd.notnull(avg_cno) and 0 < avg_cno < 20.0:
                flags.append(QualityFlag.LOW_CNO)

            # Check PRN availability
            prn_str = df["satellite_prns"].iloc[i]
            if not prn_str or prn_str.strip() == "":
                flags.append(QualityFlag.PRN_UNAVAILABLE)

            quality_flags.append("|".join(flags))

        df["data_quality_flag"] = quality_flags

        # 6. Assemble canonical observation schema
        df["timestamp_utc"] = df["timestamp_gnss"]
        df["satellites_in_view"] = df["satellites_in_view_clean"]

        canonical_schema = [
            "epoch_id",
            "session_id",
            "timestamp_utc",
            "timestamp_pc",
            "latitude",
            "longitude",
            "altitude_m",
            "speed_kmh",
            "heading_deg",
            "fix_quality",
            "satellites_used",
            "satellites_in_view",
            "satellite_prns",
            "hdop",
            "vdop",
            "pdop",
            "avg_cno",
            "max_cno",
            "min_cno",
            "data_quality_flag",
        ]

        # Ensure strict sorting by session_id and epoch_id
        out_df = df.sort_values(by=["session_id", "epoch_id"]).reset_index(drop=True)[canonical_schema].copy()
        return out_df

    def process_file(self, input_csv: str, output_csv: str) -> pd.DataFrame:
        """Process input CSV and save to structured output path."""
        print(f"[*] Reading telemetry from: {input_csv}")
        raw_df = pd.read_csv(input_csv)
        print(f"[*] Loaded {len(raw_df)} raw records.")

        structured_df = self.process_telemetry_df(raw_df)

        os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
        structured_df.to_csv(output_csv, index=False)
        print(f"[+] Canonical structured GNSS observations saved to: {output_csv} ({len(structured_df)} records)")
        return structured_df


if __name__ == "__main__":
    # Go up 3 levels from src/parsing/preprocessing.py to workspace root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    in_file = os.path.join(base_dir, "data", "raw", "locus_telemetry_features.csv")
    if not os.path.exists(in_file):
        in_file = os.path.join(base_dir, "locus_telemetry_features.csv")
    out_file = os.path.join(base_dir, "data", "structured", "locus_structured_gnss.csv")

    preprocessor = GNSSPreprocessor()
    preprocessor.process_file(in_file, out_file)
