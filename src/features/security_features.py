"""
security_features.py - Official 10-Dimensional Security Feature Engineering Engine for LOCUS.

Computes the architecture-defined 10-D GNSS cybersecurity vector:
Kinematic / Physical Integrity:
1. disp_haversine
2. vel_kinematic
3. acc_kinematic
4. jerk_kinematic
5. bearing_rate

Navigation Quality:
6. HDOP
7. VDOP
8. fix_integrity

Satellite Behaviour:
9. sat_count_tot
10. sat_churn
"""

import math
import os
import sys
from typing import List, Optional, Set, Tuple
import numpy as np
import pandas as pd


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in meters using WGS-84 radius."""
    R = 6371000.0  # Earth mean radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def circular_bearing_diff_deg(bearing1: float, bearing2: float) -> float:
    """
    Normalized signed shortest circular difference between two compass bearings in degrees.
    Correctly handles wrap-around, e.g., 359° -> 1° = +2°, not 358°.
    """
    diff = (bearing2 - bearing1 + 180.0) % 360.0 - 180.0
    return diff


def compute_fix_integrity(fix_quality: int, pdop: float, avg_cno: float) -> float:
    """
    Deterministic navigation solution fix integrity indicator.
    Combines fix status, 3D geometric dilution (PDOP), and carrier signal strength (C/N0).

    Scaled to [0.0, 1.0].
    """
    if fix_quality <= 0 or pdop is None or np.isnan(pdop) or pdop <= 0:
        return 0.0

    # Base weight by fix quality (DGPS/SBAS = 1.0, SPS = 0.85)
    fix_weight = 1.0 if fix_quality >= 2 else 0.85

    # C/N0 factor: nominal strong signal is 35-40 dB-Hz
    cno_clamped = min(max(avg_cno, 0.0), 40.0) / 40.0

    # Geometry penalty: nominal PDOP is <= 2.0
    geom_factor = 1.0 / max(pdop / 1.5, 1.0)

    integrity = fix_weight * (0.6 * cno_clamped + 0.4 * geom_factor)
    return float(np.clip(integrity, 0.0, 1.0))


def compute_sat_churn(
    prns_prev: Optional[Set[str]], prns_curr: Optional[Set[str]], dt: float
) -> float:
    """
    Compute satellite constellation turnover rate (sat_churn) using active PRN sets:
    churn = (|PRNs_t \\ PRNs_{t-1}| + |PRNs_{t-1} \\ PRNs_t|) / dt

    If PRN data is unavailable (e.g. unlogged in historical feed), returns np.nan.
    Never fabricates churn from satellite counts.
    """
    if prns_prev is None or prns_curr is None:
        return np.nan
    if not isinstance(prns_prev, set) or not isinstance(prns_curr, set):
        return np.nan
    if len(prns_prev) == 0 and len(prns_curr) == 0:
        return np.nan
    if dt <= 0:
        return np.nan

    symmetric_diff = (prns_curr - prns_prev) | (prns_prev - prns_curr)
    return len(symmetric_diff) / dt


class SecurityFeatureExtractor:
    """
    Extracts the official 10-D security vector with strict session and gap isolation.
    """

    def __init__(self, max_gap_threshold_s: float = 5.0):
        self.max_gap_threshold_s = max_gap_threshold_s

    def extract_features(self, structured_df: pd.DataFrame) -> pd.DataFrame:
        """
        Process structured observation dataframe into official 10-D security features.

        Parameters
        ----------
        structured_df : pd.DataFrame
            Canonical observation dataset (from data/structured/locus_structured_gnss.csv).

        Returns
        -------
        pd.DataFrame
            Engineered 10-D security feature dataset for locked GNSS epochs.
        """
        df = structured_df.copy()

        # Filter strictly to valid locked fixes
        valid_df = df[
            (df["fix_quality"] > 0)
            & df["latitude"].notna()
            & df["longitude"].notna()
        ].copy()

        if len(valid_df) == 0:
            raise ValueError("No valid locked fixes available to compute security features.")

        # Ensure timestamps are parsed
        pc_dts = pd.to_datetime(valid_df["timestamp_pc"])
        gnss_dts = pd.to_datetime(valid_df["timestamp_utc"], utc=True)
        valid_df["_pc_dt"] = pc_dts
        valid_df["_gnss_dt"] = gnss_dts

        # Parse PRNs if present
        def parse_prn_str(val) -> Optional[Set[str]]:
            if pd.isna(val) or not str(val).strip():
                return None
            prns = {p.strip() for p in str(val).split(";") if p.strip()}
            return prns if len(prns) > 0 else None

        valid_df["_prn_set"] = valid_df["satellite_prns"].apply(parse_prn_str)

        session_groups = []
        for sid, group in valid_df.groupby("session_id", sort=True):
            session_features = self._process_single_session(group)
            session_groups.append(session_features)

        result_df = pd.concat(session_groups, ignore_index=True)

        # Assemble official schema
        canonical_columns = [
            "epoch_id",
            "session_id",
            "timestamp_utc",
            "timestamp_pc",
            "latitude",
            "longitude",
            "altitude_m",
            # The Official 10-D Security Feature Vector
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

        out_df = result_df[canonical_columns].copy()
        return out_df

    def _process_single_session(self, grp: pd.DataFrame) -> pd.DataFrame:
        """Process a single continuous session with gap detection and boundary resets."""
        df = grp.copy().reset_index(drop=True)
        n = len(df)

        # Output feature arrays
        disp_haversine = np.zeros(n, dtype=float)
        vel_kinematic = np.zeros(n, dtype=float)
        acc_kinematic = np.zeros(n, dtype=float)
        jerk_kinematic = np.zeros(n, dtype=float)
        bearing_rate = np.zeros(n, dtype=float)
        hdop_out = np.zeros(n, dtype=float)
        vdop_out = np.zeros(n, dtype=float)
        fix_integrity_out = np.zeros(n, dtype=float)
        sat_count_tot_out = np.zeros(n, dtype=int)
        sat_churn_out = np.full(n, np.nan, dtype=float)

        lats = df["latitude"].to_numpy(dtype=float)
        lons = df["longitude"].to_numpy(dtype=float)
        headings = df["heading_deg"].fillna(0.0).to_numpy(dtype=float)
        gnss_times = df["_gnss_dt"]
        pc_times = df["_pc_dt"]
        fix_quals = df["fix_quality"].to_numpy(dtype=int)
        sats_used = df["satellites_used"].to_numpy(dtype=int)
        hdops = df["hdop"].fillna(1.0).to_numpy(dtype=float)
        vdops = df["vdop"].fillna(1.0).to_numpy(dtype=float)
        pdops = df["pdop"].fillna(1.25).to_numpy(dtype=float)
        avg_cnos = df["avg_cno"].fillna(0.0).to_numpy(dtype=float)
        prn_sets = df["_prn_set"].tolist()

        for i in range(n):
            # 6. HDOP & 7. VDOP
            hdop_out[i] = hdops[i]
            vdop_out[i] = vdops[i]

            # 8. fix_integrity
            fix_integrity_out[i] = compute_fix_integrity(fix_quals[i], pdops[i], avg_cnos[i])

            # 9. sat_count_tot (satellites_used in PVT solution)
            sat_count_tot_out[i] = sats_used[i]

            if i == 0:
                # Session boundary start: all differential features initialize to 0.0
                continue

            # Calculate elapsed time dt from GNSS UTC clock
            dt_delta = gnss_times.iloc[i] - gnss_times.iloc[i - 1]
            dt_sec = dt_delta.total_seconds() if hasattr(dt_delta, "total_seconds") else float(dt_delta)

            # If GNSS time is invalid, fall back to PC time
            if dt_sec <= 0.05 or dt_sec > self.max_gap_threshold_s or np.isnan(dt_sec):
                dt_pc_delta = pc_times.iloc[i] - pc_times.iloc[i - 1]
                dt_sec = dt_pc_delta.total_seconds() if hasattr(dt_pc_delta, "total_seconds") else float(dt_pc_delta)

            # Gap check: if gap exceeds threshold, treat epoch i as a track restart
            if dt_sec > self.max_gap_threshold_s or dt_sec <= 0.0:
                continue

            # Safe clamped dt (avoid divide-by-zero, nominal 1.0s)
            dt = dt_sec if dt_sec >= 0.05 else 1.0

            # 1. disp_haversine
            d = haversine_m(lats[i - 1], lons[i - 1], lats[i], lons[i])
            disp_haversine[i] = d

            # 2. vel_kinematic
            v = d / dt
            vel_kinematic[i] = v

            # 3. acc_kinematic
            a = (v - vel_kinematic[i - 1]) / dt
            acc_kinematic[i] = a

            # 4. jerk_kinematic
            if i >= 2:
                j = (a - acc_kinematic[i - 1]) / dt
                jerk_kinematic[i] = j

            # 5. bearing_rate (normalized circular rate)
            d_bearing = circular_bearing_diff_deg(headings[i - 1], headings[i])
            bearing_rate[i] = abs(d_bearing) / dt

            # 10. sat_churn (using PRN sets if available)
            churn = compute_sat_churn(prn_sets[i - 1], prn_sets[i], dt)
            sat_churn_out[i] = churn

        df["disp_haversine"] = disp_haversine
        df["vel_kinematic"] = vel_kinematic
        df["acc_kinematic"] = acc_kinematic
        df["jerk_kinematic"] = jerk_kinematic
        df["bearing_rate"] = bearing_rate
        df["HDOP"] = hdop_out
        df["VDOP"] = vdop_out
        df["fix_integrity"] = fix_integrity_out
        df["sat_count_tot"] = sat_count_tot_out
        df["sat_churn"] = sat_churn_out
        return df


def generate_security_features_file(
    input_path: str, output_path: str
) -> pd.DataFrame:
    """
    Main driver to compute official 10-D security features and write CSV.
    """
    print(f"[*] Ingesting structured observations from: {input_path}")
    raw_obs = pd.read_csv(input_path)
    print(f"[*] Total observations: {len(raw_obs)}")

    extractor = SecurityFeatureExtractor(max_gap_threshold_s=5.0)
    features_df = extractor.extract_features(raw_obs)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    features_df.to_csv(output_path, index=False)
    print(f"[+] Official 10-D security features exported to: {output_path}")
    print(f"[+] Total feature vectors: {len(features_df)}")
    return features_df


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    in_file = os.path.join(base_dir, "data", "structured", "locus_structured_gnss.csv")
    out_file = os.path.join(base_dir, "data", "features", "locus_security_features.csv")
    generate_security_features_file(in_file, out_file)
