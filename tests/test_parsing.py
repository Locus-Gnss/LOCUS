"""
test_parsing.py - Unit and Integration Tests for LOCUS Parsing and Preprocessing Modules.

Validates:
1. NMEAParser on GGA, GSA, GSV, RMC, and malformed strings.
2. PRN and multi-constellation extraction from GSV/GSA.
3. EpochAggregator multi-talker accumulation and state management.
4. GNSSPreprocessor quality flag taxonomy and schema compliance.
5. Structured dataset output integrity.
"""

from datetime import datetime, timezone
import os
import unittest
import numpy as np
import pandas as pd

from src.parsing.nmea_parser import NMEAParser, ParsedSentence
from src.parsing.epoch_aggregator import EpochAggregator, GNSSEpochObservation
from src.parsing.preprocessing import GNSSPreprocessor, QualityFlag


class TestNMEAParser(unittest.TestCase):
    def test_parse_gga(self):
        line = "$GPGGA,183248.098,2306.2574,N,07235.5492,E,1,18,0.86,66.1,M,-55.0,M,,*79"
        res = NMEAParser.parse_line(line)
        self.assertIsNotNone(res)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.sentence_type, "GGA")
        self.assertEqual(res.talker, "GP")
        self.assertEqual(res.fix_quality, 1)
        self.assertEqual(res.satellites_used, 18)
        self.assertAlmostEqual(res.hdop, 0.86, places=2)
        self.assertAlmostEqual(res.altitude_m, 66.1, places=1)
        self.assertAlmostEqual(res.latitude, 23.10429, delta=0.001)
        self.assertAlmostEqual(res.longitude, 72.59248, delta=0.001)

    def test_parse_gsa(self):
        line = "$GNGSA,A,3,01,03,06,07,09,11,14,17,19,28,30,,1.25,0.86,0.88*12"
        res = NMEAParser.parse_line(line)
        self.assertIsNotNone(res)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.sentence_type, "GSA")
        self.assertEqual(res.fix_type, 3)
        self.assertAlmostEqual(res.pdop, 1.25, places=2)
        self.assertAlmostEqual(res.hdop, 0.86, places=2)
        self.assertAlmostEqual(res.vdop, 0.88, places=2)
        # Verify active PRN extraction
        self.assertIn("GN01", res.active_prns)
        self.assertIn("GN30", res.active_prns)
        self.assertEqual(len(res.active_prns), 11)

    def test_parse_gsv_prns(self):
        line = "$GPGSV,3,1,11,01,65,045,42,03,45,123,38,06,12,089,28,07,33,210,35*78"
        res = NMEAParser.parse_line(line)
        self.assertIsNotNone(res)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.sentence_type, "GSV")
        self.assertEqual(res.talker, "GP")
        self.assertEqual(res.satellites_in_view_talker, 11)
        self.assertEqual(len(res.satellites_info), 4)
        # Check first satellite PRN and SNR
        sat1 = res.satellites_info[0]
        self.assertEqual(sat1.prn, "GP01")
        self.assertEqual(sat1.snr_dbhz, 42.0)
        self.assertEqual(sat1.elevation_deg, 65.0)

    def test_parse_rmc(self):
        line = "$GPRMC,183248.098,A,2306.2574,N,07235.5492,E,0.05,217.26,250926,,,A*65"
        res = NMEAParser.parse_line(line)
        self.assertIsNotNone(res)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.sentence_type, "RMC")
        self.assertEqual(res.status, "A")
        self.assertAlmostEqual(res.speed_kmh, 0.05 * 1.852, places=3)
        self.assertAlmostEqual(res.heading_deg, 217.26, places=2)
        self.assertIsNotNone(res.utc_datetime)

    def test_malformed_sentence_safety(self):
        # Corrupted checksum / invalid format
        line = "$GPGGA,INVALID,CORRUPTED*XX"
        res = NMEAParser.parse_line(line)
        self.assertIsNotNone(res)
        self.assertFalse(res.is_valid)
        self.assertIn("ParseError", res.error_message)


class TestEpochAggregator(unittest.TestCase):
    def test_multi_constellation_accumulation(self):
        aggregator = EpochAggregator()

        # 1. Feed GGA
        gga = NMEAParser.parse_line("$GPGGA,183248.098,2306.2574,N,07235.5492,E,1,18,0.86,66.1,M,-55.0,M,,*79")
        obs1 = aggregator.process_sentence(gga)
        self.assertIsNone(obs1)  # Epoch not complete yet

        # 2. Feed GPS GSV (11 in view)
        gsv_gp = NMEAParser.parse_line("$GPGSV,3,1,11,01,65,045,42,03,45,123,38,06,12,089,28,07,33,210,35*78")
        aggregator.process_sentence(gsv_gp)

        # 3. Feed GLONASS GSV (6 in view)
        gsv_gl = NMEAParser.parse_line("$GLGSV,2,1,06,65,45,030,40,66,22,110,32,67,15,220,30,68,50,310,36*7A")
        aggregator.process_sentence(gsv_gl)

        # 4. Feed RMC (Epoch completion trigger)
        rmc = NMEAParser.parse_line("$GPRMC,183248.098,A,2306.2574,N,07235.5492,E,0.05,217.26,250926,,,A*65")
        obs = aggregator.process_sentence(rmc, pc_timestamp="2026-09-25T10:32:48.100000")

        self.assertIsNotNone(obs)
        self.assertIsInstance(obs, GNSSEpochObservation)

        # Verify multi-constellation summation (11 GPS + 6 GLONASS = 17, bounded by sats_used = 18)
        self.assertGreaterEqual(obs.satellites_in_view, 18)

        # Verify PRN retention
        self.assertIn("GP01", obs.satellite_prns)
        self.assertIn("GL65", obs.satellite_prns)

        # Verify C/N0 calculation
        self.assertGreater(obs.avg_cno, 0.0)
        self.assertEqual(obs.max_cno, 42.0)


class TestPreprocessing(unittest.TestCase):
    def test_quality_flags_and_schema(self):
        structured_file = os.path.join("data", "structured", "locus_structured_gnss.csv")
        self.assertTrue(os.path.exists(structured_file), f"File {structured_file} not found.")

        df = pd.read_csv(structured_file)
        self.assertEqual(len(df), 10938)
        self.assertEqual(df.shape[1], 20)

        # Invariant checks
        self.assertEqual(df["session_id"].nunique(), 15)
        self.assertIn("timestamp_utc", df.columns)
        self.assertIn("timestamp_pc", df.columns)
        self.assertIn("data_quality_flag", df.columns)
        self.assertIn("satellite_prns", df.columns)

        # Verify within-session monotonic timestamp order
        for sid, grp in df.groupby("session_id"):
            pc_times = pd.to_datetime(grp["timestamp_pc"])
            self.assertTrue(pc_times.is_monotonic_increasing, f"Session {sid} timestamps not monotonic")

        # Verify explicit quality flags
        valid_rows = df[df["data_quality_flag"].str.contains(QualityFlag.VALID)]
        self.assertEqual(len(valid_rows), 9382)

        no_fix_rows = df[df["data_quality_flag"].str.contains(QualityFlag.NO_FIX)]
        self.assertEqual(len(no_fix_rows), 1556)

        # Verify missing-value preservation (not falsely zero-filled)
        self.assertEqual(df["latitude"].isna().sum(), 1476)
        self.assertEqual(df["longitude"].isna().sum(), 1476)
        self.assertEqual(df["altitude_m"].isna().sum(), 1556)
        self.assertEqual(df["hdop"].isna().sum(), 1555)


if __name__ == "__main__":
    unittest.main()
