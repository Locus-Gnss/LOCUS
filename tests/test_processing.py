"""
test_processing.py - Comprehensive Unit and Integration Test Suite for LOCUS Phase 2 Processing Pipeline.

Tests:
1. Session boundary detection and epoch numbering.
2. GNSS UTC timestamp reconstruction and monotonic continuity.
3. Multi-constellation satellite metric correction and dynamic usage ratio.
4. Session-aware feature boundary isolation (no cross-session leaks).
5. Mathematical sanity (Haversine, zero division protection, no NaNs/Infs).
6. File existence and schema conformity for generated artifacts.
"""

import math
import os
import unittest
import numpy as np
import pandas as pd

from src.locus_quality import (
    detect_sessions,
    reconstruct_gnss_timestamp,
    correct_satellite_metrics,
    clean_telemetry,
)
from src.locus_features_v2 import (
    haversine_distance_m,
    compute_session_features,
    extract_features_v2,
)


class TestLocusQuality(unittest.TestCase):
    def setUp(self):
        # Synthetic mini telemetry dataset simulating multiple sessions with gaps
        self.mock_data = pd.DataFrame(
            {
                "timestamp_pc": [
                    "2026-09-25T10:00:00.000000",
                    "2026-09-25T10:00:01.000000",
                    "2026-09-25T10:00:02.000000",
                    # 100-second session gap
                    "2026-09-25T10:01:42.000000",
                    "2026-09-25T10:01:43.000000",
                ],
                "timestamp_utc": [
                    "04:30:00+00:00",
                    "04:30:01+00:00",
                    "04:30:02+00:00",
                    "04:31:42+00:00",
                    "04:31:43+00:00",
                ],
                "fix_quality": [1, 1, 1, 1, 1],
                "latitude": [23.1040, 23.1040, 23.1041, 23.1045, 23.1045],
                "longitude": [72.5920, 72.5920, 72.5921, 72.5930, 72.5930],
                "altitude_m": [60.0, 60.1, 60.2, 75.0, 75.1],
                "speed_kmh": [0.0, 0.5, 0.4, 0.0, 0.2],
                "heading_deg": [0.0, 10.0, 12.0, 180.0, 185.0],
                "satellites_used": [18, 18, 19, 21, 21],
                "satellites_in_view": [2, 1, 3, 2, 4],  # Flawed single-talker counts
                "hdop": [0.9, 0.9, 0.85, 0.8, 0.8],
                "pdop": [1.2, 1.2, 1.15, 1.1, 1.1],
                "vdop": [0.8, 0.8, 0.8, 0.75, 0.75],
                "avg_cno": [28.0, 28.5, 29.0, 27.5, 28.0],
                "max_cno": [42.0, 42.0, 43.0, 41.0, 42.0],
                "min_cno": [12.0, 12.0, 11.0, 10.0, 11.0],
            }
        )

    def test_session_detection(self):
        """Verify that gaps > 5s increment session_id and epoch_id resets to 1."""
        df = detect_sessions(self.mock_data, max_gap_seconds=5.0)
        self.assertIn("session_id", df.columns)
        self.assertIn("epoch_id", df.columns)
        self.assertIn("is_session_start", df.columns)

        # Expected 2 sessions
        self.assertEqual(df["session_id"].nunique(), 2)
        self.assertEqual(df["session_id"].iloc[0], 1)
        self.assertEqual(df["session_id"].iloc[2], 1)
        self.assertEqual(df["session_id"].iloc[3], 2)
        self.assertEqual(df["session_id"].iloc[4], 2)

        # Expected epoch resets
        self.assertEqual(df["epoch_id"].iloc[0], 1)
        self.assertEqual(df["epoch_id"].iloc[2], 3)
        self.assertEqual(df["epoch_id"].iloc[3], 1)
        self.assertEqual(df["epoch_id"].iloc[4], 2)

        # Expected start flags
        self.assertTrue(df["is_session_start"].iloc[0])
        self.assertFalse(df["is_session_start"].iloc[1])
        self.assertTrue(df["is_session_start"].iloc[3])
        self.assertFalse(df["is_session_start"].iloc[4])

    def test_timestamp_reconstruction(self):
        """Verify GNSS UTC timestamp ISO format and delta dt calculation."""
        df = detect_sessions(self.mock_data, max_gap_seconds=5.0)
        df = reconstruct_gnss_timestamp(df, local_tz_offset_hours=5.5)

        self.assertIn("timestamp_gnss", df.columns)
        self.assertIn("primary_dt", df.columns)

        # Verify ISO string format
        self.assertTrue(df["timestamp_gnss"].str.startswith("2026-09-25T04:30:00").iloc[0])

        # Verify primary_dt within continuous 1-second epochs is 1.0s
        self.assertAlmostEqual(df["primary_dt"].iloc[1], 1.0, places=3)
        self.assertAlmostEqual(df["primary_dt"].iloc[2], 1.0, places=3)
        self.assertAlmostEqual(df["primary_dt"].iloc[4], 1.0, places=3)

    def test_satellite_metrics_correction(self):
        """Verify multi-constellation aggregation correction and invariant s_view >= s_used."""
        df = correct_satellite_metrics(self.mock_data)
        self.assertIn("satellites_in_view_clean", df.columns)

        s_used = df["satellites_used"]
        s_view_clean = df["satellites_in_view_clean"]

        # Invariant: satellites in view must strictly be greater than or equal to satellites used
        self.assertTrue((s_view_clean >= s_used).all())

        # Dynamic ratio test: ratio must be non-constant and < 1.0 for these rows
        ratio = s_used / s_view_clean
        self.assertGreater(ratio.std(), 0.0)
        self.assertTrue((ratio <= 1.0).all())
        self.assertTrue((ratio >= 0.5).all())


class TestLocusFeaturesV2(unittest.TestCase):
    def test_haversine_distance(self):
        """Verify Haversine formula on known geographic points."""
        # 1. Identical coordinates -> distance = 0
        d_zero = haversine_distance_m(23.1040, 72.5920, 23.1040, 72.5920)
        self.assertEqual(d_zero, 0.0)

        # 2. Known 1 degree latitude delta ~ 111.195 km = 111,195 m
        d_1deg = haversine_distance_m(0.0, 0.0, 1.0, 0.0)
        self.assertAlmostEqual(d_1deg, 111195.0, delta=200.0)

    def test_session_boundary_isolation(self):
        """Verify that differential features NEVER calculate across session boundaries."""
        session1 = pd.DataFrame(
            {
                "session_id": [1, 1],
                "epoch_id": [1, 2],
                "latitude": [23.1000, 23.1001],
                "longitude": [72.5900, 72.5900],
                "altitude_m": [60.0, 60.5],
                "speed_kmh": [0.0, 0.36],  # 0.1 m/s
                "heading_deg": [0.0, 10.0],
                "satellites_used": [18, 19],
                "satellites_in_view_clean": [24, 25],
                "hdop": [0.9, 0.85],
                "avg_cno": [28.0, 28.5],
                "max_cno": [40.0, 41.0],
                "min_cno": [12.0, 11.0],
                "primary_dt": [1.0, 1.0],
            }
        )

        session2 = pd.DataFrame(
            {
                "session_id": [2, 2],
                "epoch_id": [1, 2],
                # Coords jump by 500 meters from session 1!
                "latitude": [23.1050, 23.1051],
                "longitude": [72.5950, 72.5950],
                "altitude_m": [90.0, 90.2],
                "speed_kmh": [0.0, 0.18],
                "heading_deg": [180.0, 185.0],
                "satellites_used": [15, 15],  # Delta from session 1 row 2 would have been -4!
                "satellites_in_view_clean": [20, 20],
                "hdop": [1.2, 1.2],
                "avg_cno": [26.0, 26.2],
                "max_cno": [38.0, 39.0],
                "min_cno": [10.0, 10.0],
                "primary_dt": [1.0, 1.0],
            }
        )

        f1 = compute_session_features(session1)
        f2 = compute_session_features(session2)

        # Session 1 epoch 1 must have 0.0 for all differentials
        self.assertEqual(f1["feat_dist_jump_m"].iloc[0], 0.0)
        self.assertEqual(f1["feat_derived_speed_mps"].iloc[0], 0.0)
        self.assertEqual(f1["feat_delta_sats"].iloc[0], 0.0)

        # Session 2 epoch 1 MUST ALSO have 0.0 despite the 500m jump and -4 satellite drop
        self.assertEqual(f2["feat_dist_jump_m"].iloc[0], 0.0)
        self.assertEqual(f2["feat_derived_speed_mps"].iloc[0], 0.0)
        self.assertEqual(f2["feat_delta_sats"].iloc[0], 0.0)
        self.assertEqual(f2["feat_hdop_rate"].iloc[0], 0.0)
        self.assertEqual(f2["feat_heading_rate_deg_s"].iloc[0], 0.0)


class TestPipelineArtifacts(unittest.TestCase):
    def test_clean_telemetry_file(self):
        """Verify output of data/processed/locus_telemetry_clean.csv."""
        clean_path = os.path.join("data", "processed", "locus_telemetry_clean.csv")
        self.assertTrue(os.path.exists(clean_path), f"File {clean_path} does not exist.")

        df = pd.read_csv(clean_path)
        self.assertEqual(len(df), 10938)
        self.assertIn("session_id", df.columns)
        self.assertIn("epoch_id", df.columns)
        self.assertIn("timestamp_gnss", df.columns)
        self.assertIn("satellites_in_view_clean", df.columns)

        # Verify session count is exactly 15
        self.assertEqual(df["session_id"].nunique(), 15)

        # Verify clean satellites in view >= satellites used
        valid_rows = df[df["is_fix_valid"] == True]
        self.assertTrue((valid_rows["satellites_in_view_clean"] >= valid_rows["satellites_used"]).all())

    def test_features_v2_file(self):
        """Verify output of data/features/locus_features_v2.csv."""
        feat_path = os.path.join("data", "features", "locus_features_v2.csv")
        self.assertTrue(os.path.exists(feat_path), f"File {feat_path} does not exist.")

        df = pd.read_csv(feat_path)
        self.assertEqual(len(df), 9382)

        # Verify all 10 canonical features exist
        canonical_features = [
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
        for feat in canonical_features:
            self.assertIn(feat, df.columns)

        # Verify 0 NaNs and 0 Infs
        self.assertEqual(df.isna().sum().sum(), 0)
        for col in canonical_features:
            self.assertFalse(np.isinf(df[col]).any())

        # Verify feat_sat_usage_ratio is dynamic (std > 0)
        self.assertGreater(df["feat_sat_usage_ratio"].std(), 0.01)
        self.assertLess(df["feat_sat_usage_ratio"].max(), 1.0)

        # Verify distance jump does NOT exceed 10m (old max was 46.6m across session)
        self.assertLess(df["feat_dist_jump_m"].max(), 10.0)


if __name__ == "__main__":
    unittest.main()
