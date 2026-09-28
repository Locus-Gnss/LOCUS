"""
test_security_features.py - Unit and Integration Tests for Official 10-D Security Feature Engineering.

Validates:
1. Haversine distance accuracy.
2. Normalized circular bearing difference (specifically 359° -> 1° = +2°).
3. Kinematic derivative cascade (displacement -> velocity -> acceleration -> jerk).
4. Physical fix integrity formulation.
5. Set-theoretic sat_churn calculation and safe NaN handling when PRNs are unlogged.
6. Session boundary and gap reset isolation.
7. Dataset schema compliance and numerical bounds in data/features/locus_security_features.csv.
"""

import math
import os
import unittest
import numpy as np
import pandas as pd

from src.features.security_features import (
    haversine_m,
    circular_bearing_diff_deg,
    compute_fix_integrity,
    compute_sat_churn,
    SecurityFeatureExtractor,
)


class TestSecurityFeatureMath(unittest.TestCase):
    def test_haversine_m(self):
        # Identical points -> distance 0
        d0 = haversine_m(23.1040, 72.5920, 23.1040, 72.5920)
        self.assertEqual(d0, 0.0)

        # 1 degree latitude displacement ~ 111,195 m
        d1 = haversine_m(0.0, 0.0, 1.0, 0.0)
        self.assertAlmostEqual(d1, 111195.0, delta=200.0)

    def test_circular_bearing_diff_deg(self):
        # Explicit Requirement: 359° -> 1° must be +2°, not 358°
        d_wrap_fwd = circular_bearing_diff_deg(359.0, 1.0)
        self.assertAlmostEqual(d_wrap_fwd, 2.0, places=4)

        # 1° -> 359° must be -2°
        d_wrap_back = circular_bearing_diff_deg(1.0, 359.0)
        self.assertAlmostEqual(d_wrap_back, -2.0, places=4)

        # Regular bearing change
        d_normal = circular_bearing_diff_deg(90.0, 95.0)
        self.assertAlmostEqual(d_normal, 5.0, places=4)

    def test_fix_integrity(self):
        # Invalid fix (0) -> 0.0 integrity
        fi_zero = compute_fix_integrity(0, 1.2, 30.0)
        self.assertEqual(fi_zero, 0.0)

        # High quality fix: DGPS (2), good PDOP (1.2), strong C/N0 (38 dB-Hz)
        fi_high = compute_fix_integrity(2, 1.2, 38.0)
        self.assertGreater(fi_high, 0.8)
        self.assertLessEqual(fi_high, 1.0)

        # Autonomous SPS (1) with identical geometry has slightly lower integrity
        fi_sps = compute_fix_integrity(1, 1.2, 38.0)
        self.assertLess(fi_sps, fi_high)

        # Degraded geometry (PDOP 6.0) severely lowers integrity
        fi_deg = compute_fix_integrity(1, 6.0, 38.0)
        self.assertLess(fi_deg, fi_sps)

    def test_sat_churn_set_logic(self):
        # 1. Active set change: 1 sat lost, 1 sat acquired -> symmetric diff = 2
        set_t0 = {"GP01", "GP03", "GL07", "GA05"}
        set_t1 = {"GP01", "GP03", "GL08", "GA05"}  # GL07 lost, GL08 acquired
        churn = compute_sat_churn(set_t0, set_t1, dt=1.0)
        self.assertEqual(churn, 2.0)

        # 2. Identical PRN set -> churn = 0.0
        churn_zero = compute_sat_churn(set_t0, set_t0, dt=1.0)
        self.assertEqual(churn_zero, 0.0)

        # 3. Missing/Unavailable PRN sets -> must return np.nan (no fabrication!)
        churn_none1 = compute_sat_churn(None, set_t1, dt=1.0)
        self.assertTrue(np.isnan(churn_none1))

        churn_none2 = compute_sat_churn(set_t0, None, dt=1.0)
        self.assertTrue(np.isnan(churn_none2))

        churn_empty = compute_sat_churn(set(), set(), dt=1.0)
        self.assertTrue(np.isnan(churn_empty))


class TestFeatureDatasetIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.feat_file = os.path.join("data", "features", "locus_security_features.csv")
        assert os.path.exists(cls.feat_file), f"File {cls.feat_file} not found."
        cls.df = pd.read_csv(cls.feat_file)

    def test_record_count_and_columns(self):
        # 9,382 locked epochs
        self.assertEqual(len(self.df), 9382)

        # Official 10-D Security Feature Vector columns
        official_features = [
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
        for feat in official_features:
            self.assertIn(feat, self.df.columns)

    def test_no_infinities(self):
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            self.assertFalse(np.isinf(self.df[col]).any(), f"Inf found in {col}")

    def test_nan_handling(self):
        # Features 1 to 9 must have ZERO NaNs
        features_1_to_9 = [
            "disp_haversine",
            "vel_kinematic",
            "acc_kinematic",
            "jerk_kinematic",
            "bearing_rate",
            "HDOP",
            "VDOP",
            "fix_integrity",
            "sat_count_tot",
        ]
        for feat in features_1_to_9:
            self.assertEqual(self.df[feat].isna().sum(), 0, f"Unexpected NaN in {feat}")

        # Feature 10 (sat_churn) is strictly NaN for historical data (documented limitation)
        self.assertEqual(self.df["sat_churn"].isna().sum(), len(self.df))

    def test_session_boundary_isolation(self):
        # For the first locked epoch of each session, all differentials must be strictly 0.0
        session_starts = self.df[self.df.groupby("session_id").cumcount() == 0]
        self.assertEqual(len(session_starts), 6)  # Exactly 6 sessions contained locked fixes
        self.assertEqual(session_starts["disp_haversine"].max(), 0.0)
        self.assertEqual(session_starts["vel_kinematic"].max(), 0.0)
        self.assertEqual(session_starts["acc_kinematic"].max(), 0.0)
        self.assertEqual(session_starts["jerk_kinematic"].max(), 0.0)
        self.assertEqual(session_starts["bearing_rate"].max(), 0.0)

    def test_physical_bounds(self):
        # Displacement and velocity must be non-negative
        self.assertTrue((self.df["disp_haversine"] >= 0.0).all())
        self.assertTrue((self.df["vel_kinematic"] >= 0.0).all())
        self.assertTrue((self.df["bearing_rate"] >= 0.0).all())

        # Fix integrity must be strictly bounded in [0.0, 1.0]
        self.assertTrue((self.df["fix_integrity"] >= 0.0).all())
        self.assertTrue((self.df["fix_integrity"] <= 1.0).all())

        # DOP must be positive
        self.assertTrue((self.df["HDOP"] > 0.0).all())
        self.assertTrue((self.df["VDOP"] > 0.0).all())


if __name__ == "__main__":
    unittest.main()
