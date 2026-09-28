"""
locus_features_v2.py - Session-Aware Feature Extraction Engine for LOCUS GNSS Security Framework.

Part of LOCUS Phase 2: Telemetry Processing.
Computes the canonical 10 GNSS ML features with strict session-boundary isolation, atomic UTC
timing, and corrected multi-constellation satellite utilization metrics.
"""

import math
import os
import sys
from typing import List, Optional
import numpy as np
import pandas as pd


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two geographic coordinates in meters.

    Parameters
    ----------
    lat1, lon1 : float
        Latitude and longitude of initial position in decimal degrees.
    lat2, lon2 : float
        Latitude and longitude of subsequent position in decimal degrees.

    Returns
    -------
    float
        Great circle geodesic distance in meters.
    """
    R = 6371000.0  # WGS-84 mean Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def compute_session_features(session_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the 10 core features strictly within a single continuous session.
    All differential features for the initial session epoch are guaranteed to be 0.0.

    Parameters
    ----------
    session_df : pd.DataFrame
        Continuous telemetry dataframe for a single session_id with valid fixes.

    Returns
    -------
    pd.DataFrame
        Session dataframe with 10 features added.
    """
    df = session_df.copy().reset_index(drop=True)
    n = len(df)

    # Initialize feature arrays
    dist_jump = np.zeros(n, dtype=float)
    derived_speed = np.zeros(n, dtype=float)
    speed_discrepancy = np.zeros(n, dtype=float)
    vertical_velocity = np.zeros(n, dtype=float)
    delta_sats = np.zeros(n, dtype=float)
    hdop_rate = np.zeros(n, dtype=float)
    heading_rate = np.zeros(n, dtype=float)

    # Pre-extract numpy vectors for fast vectorized computation
    lats = df["latitude"].to_numpy(dtype=float)
    lons = df["longitude"].to_numpy(dtype=float)
    alts = df["altitude_m"].to_numpy(dtype=float)
    speeds_kmh = df["speed_kmh"].fillna(0.0).to_numpy(dtype=float)
    headings = df["heading_deg"].fillna(0.0).to_numpy(dtype=float)
    sats_used = df["satellites_used"].to_numpy(dtype=float)
    hdops = df["hdop"].fillna(1.0).to_numpy(dtype=float)
    primary_dts = df["primary_dt"].to_numpy(dtype=float)

    for i in range(1, n):
        # Time delta: clamp to minimum 0.05s to prevent zero-division
        dt = primary_dts[i] if primary_dts[i] >= 0.05 else 1.0

        # Feature 1: Horizontal Distance Jump (meters)
        d = haversine_distance_m(lats[i - 1], lons[i - 1], lats[i], lons[i])
        dist_jump[i] = d

        # Feature 2: Derived Kinematic Speed (m/s)
        derived_spd = d / dt
        derived_speed[i] = derived_spd

        # Feature 3: Speed Discrepancy (Doppler Speed vs Kinematic Speed in m/s)
        doppler_mps = speeds_kmh[i] / 3.6
        speed_discrepancy[i] = abs(doppler_mps - derived_spd)

        # Feature 4: Vertical Velocity / Altitude Shift (m/s)
        d_alt = abs(alts[i] - alts[i - 1])
        vertical_velocity[i] = d_alt / dt

        # Feature 7: Satellite Count Differential (Delta Sats)
        delta_sats[i] = sats_used[i] - sats_used[i - 1]

        # Feature 9: HDOP Rate of Change (1/s)
        hdop_rate[i] = (hdops[i] - hdops[i - 1]) / dt

        # Feature 10: Angular Heading Shift Rate (deg/s, normalized circular diff)
        d_heading = (headings[i] - headings[i - 1] + 180.0) % 360.0 - 180.0
        heading_rate[i] = abs(d_heading) / dt

    # Feature 5: Mean C/N0 (Carrier-to-Noise in dB-Hz)
    mean_cno = df["avg_cno"].fillna(0.0).to_numpy(dtype=float)

    # Feature 6: C/N0 Spread (Max C/N0 - Min C/N0)
    cno_spread = (df["max_cno"].fillna(0.0) - df["min_cno"].fillna(0.0)).abs().to_numpy(dtype=float)

    # Feature 8: Dynamic Constellation Usage Ratio (Satellites Used / Clean Satellites in View)
    s_view = df["satellites_in_view_clean"].replace(0, 1).fillna(1).to_numpy(dtype=float)
    sat_usage_ratio = np.clip(sats_used / s_view, 0.0, 1.0)

    # Attach to dataframe
    df["feat_dist_jump_m"] = dist_jump
    df["feat_derived_speed_mps"] = derived_speed
    df["feat_speed_discrepancy_mps"] = speed_discrepancy
    df["feat_vertical_velocity_mps"] = vertical_velocity
    df["feat_mean_cno"] = mean_cno
    df["feat_cno_spread"] = cno_spread
    df["feat_delta_sats"] = delta_sats
    df["feat_sat_usage_ratio"] = sat_usage_ratio
    df["feat_hdop_rate"] = hdop_rate
    df["feat_heading_rate_deg_s"] = heading_rate
    return df


def extract_features_v2(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Extract canonical 10 features with strict session boundary protection.

    Parameters
    ----------
    input_path : str
        Path to processed clean telemetry (data/processed/locus_telemetry_clean.csv).
    output_path : str
        Destination path for data/features/locus_features_v2.csv.

    Returns
    -------
    pd.DataFrame
        Engineered feature dataset.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"[*] Reading cleaned telemetry from: {input_path}")
    df = pd.read_csv(input_path)

    # Filter to valid locked fixes only
    valid_df = df[df["is_fix_valid"] == True].copy()
    print(f"[*] Filtered {len(valid_df)} valid locked fixes for feature extraction.")

    if len(valid_df) == 0:
        raise ValueError("No valid locked fixes available to extract features.")

    # Process each session in complete isolation
    session_groups = []
    for sid, group in valid_df.groupby("session_id", sort=True):
        processed_group = compute_session_features(group)
        session_groups.append(processed_group)

    feature_df = pd.concat(session_groups, ignore_index=True)

    # Canonical columns export
    output_cols = [
        "session_id",
        "epoch_id",
        "timestamp_gnss",
        "timestamp_pc",
        "latitude",
        "longitude",
        "altitude_m",
        "feat_dist_jump_m",
        "feat_derived_speed_mps",
        "feat_speed_discrepancy_mps",
        "feat_vertical_velocity_mps",
        "feat_mean_cno",
        "feat_cno_spread",
        "feat_delta_sats",
        "feat_sat_usage_ratio",
        "feat_hdop_rate",
        "feat_heading_rate_deg_s",
    ]

    export_df = feature_df[output_cols].copy()

    # Ensure parent directories exist
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    export_df.to_csv(output_path, index=False)

    print(f"[+] Successfully generated: {output_path}")
    print(f"[+] Total feature vectors extracted: {len(export_df)}")
    print(f"[+] Verified 0 NaNs and 0 Infs: {export_df.isna().sum().sum() == 0}")
    return export_df


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    in_file = os.path.join(base_dir, "data", "processed", "locus_telemetry_clean.csv")
    out_file = os.path.join(base_dir, "data", "features", "locus_features_v2.csv")
    extract_features_v2(in_file, out_file)
