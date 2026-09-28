import math
import os
import sys
import pandas as pd

# -------------------------------------------------------------
# Force UTF-8 on Windows terminal to prevent UnicodeEncodeError
# -------------------------------------------------------------
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

INPUT_FILE = "locus_telemetry_features.csv"
OUTPUT_FILE = "locus_ml_dataset.csv"


def haversine_distance_m(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] Input file '{INPUT_FILE}' not found in current directory.")
        sys.exit(1)

    print(f"[*] Reading telemetry rows from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)

    if df.empty:
        print("[ERROR] Input CSV is empty.")
        sys.exit(1)

    print(f"[*] Processing {len(df)} telemetry rows...")

    # Filter only locked GPS fixes (fix_quality > 0) and valid coordinates
    df = df[df["fix_quality"] > 0].copy()
    df = df.dropna(subset=["latitude", "longitude", "timestamp_pc"]).copy()

    if len(df) < 2:
        print("[ERROR] Not enough valid GPS locked rows to compute differentials (minimum 2 needed).")
        sys.exit(1)

    # 1. Parse timestamps and compute dt (seconds)
    df["dt_sec"] = pd.to_datetime(df["timestamp_pc"]).diff().dt.total_seconds()
    # Avoid zero-division: clamp minimum dt to 0.1s
    df["dt_sec"] = df["dt_sec"].apply(lambda x: x if (pd.notnull(x) and x > 0.05) else 1.0)

    # -------------------------------------------------------------
    # 10 CORE FEATURES FOR SPOOFING & JAMMING DETECTION
    # -------------------------------------------------------------

    # Feature 1: Horizontal Distance Jump (meters)
    dist_list = [0.0]
    for i in range(1, len(df)):
        d = haversine_distance_m(
            df.iloc[i - 1]["latitude"],
            df.iloc[i - 1]["longitude"],
            df.iloc[i]["latitude"],
            df.iloc[i]["longitude"],
        )
        dist_list.append(d)
    df["feat_dist_jump_m"] = dist_list

    # Feature 2: Kinematic Speed derived from Position (m/s)
    df["feat_derived_speed_mps"] = df["feat_dist_jump_m"] / df["dt_sec"]

    # Feature 3: Speed Discrepancy (Doppler Speed vs Kinematic Speed)
    # speed_kmh / 3.6 = speed_mps
    doppler_speed_mps = df["speed_kmh"].fillna(0.0) / 3.6
    df["feat_speed_discrepancy_mps"] = (doppler_speed_mps - df["feat_derived_speed_mps"]).abs()

    # Feature 4: Vertical Velocity / Altitude Jump (m/s)
    alt_diff = df["altitude_m"].diff().fillna(0.0)
    df["feat_vertical_velocity_mps"] = (alt_diff / df["dt_sec"]).abs()

    # Feature 5: Carrier-to-Noise Ratio (Mean C/N0 in dB-Hz) -> Jamming Indicator
    df["feat_mean_cno"] = df["avg_cno"].fillna(0.0)

    # Feature 6: C/N0 Spread (Max C/N0 - Min C/N0) -> Spoofing Indicator (Spoofers tend to transmit uniform power)
    df["feat_cno_spread"] = (df["max_cno"].fillna(0.0) - df["min_cno"].fillna(0.0)).abs()

    # Feature 7: Satellite Count Differential (Delta Sats) -> Rapid drop = Jamming
    df["feat_delta_sats"] = df["satellites_used"].diff().fillna(0.0)

    # Feature 8: Constellation Usage Ratio (Satellites Used / Satellites in View)
    sats_view = df["satellites_in_view"].replace(0, 1).fillna(1)
    df["feat_sat_usage_ratio"] = (df["satellites_used"] / sats_view).clip(0.0, 1.0)

    # Feature 9: HDOP Rate of Change (Delta HDOP / dt)
    hdop_diff = df["hdop"].diff().fillna(0.0)
    df["feat_hdop_rate"] = hdop_diff / df["dt_sec"]

    # Feature 10: Angular Heading Shift Rate (deg/s)
    heading_diff = df["heading_deg"].diff().fillna(0.0)
    # Normalize circular jump across 0-360 degrees
    heading_diff = (heading_diff + 180.0) % 360.0 - 180.0
    df["feat_heading_rate_deg_s"] = (heading_diff.abs() / df["dt_sec"]).fillna(0.0)

    # -------------------------------------------------------------
    # Select Columns & Save Dataset
    # -------------------------------------------------------------
    feature_cols = [
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

    export_df = df[feature_cols].copy()
    export_df.to_csv(OUTPUT_FILE, index=False)

    print(f"[OK] Successfully generated {OUTPUT_FILE} with 10 ML features!")
    print(f"[OK] Total feature vectors extracted: {len(export_df)}")


if __name__ == "__main__":
    main()
    