# LOCUS Phase 1 — Comprehensive Data Quality Audit Report

**Audit Date**: September 28, 2026  
**Auditor**: Antigravity (AI Pair Programmer)  
**Target Datasets**:
- [`locus_telemetry_features.csv`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/locus_telemetry_features.csv) (Raw / Semi-processed telemetry)
- [`locus_ml_dataset.csv`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/locus_ml_dataset.csv) (10-feature ML dataset)

---

## 1. Executive Summary

This audit establishes the empirical baseline for the LOCUS GNSS security and threat detection framework. All evaluations were performed directly on existing collected data without modification or retraining.

### Key Audit Findings:
1. **Dataset Volume**: 10,938 raw telemetry records collected via Quectel L89HA GNSS receiver, yielding 9,382 locked GNSS epochs (`fix_quality = 1`).
2. **Session Continuity Issue (Critical)**: The dataset contains **15 distinct collection sessions** spanning September 25 to September 27, 2026, separated by gaps up to 24.6 hours. **Feature calculations in [`locus_features.py`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/locus_features.py) currently cross session gaps without resets**, creating severe false jumps (e.g., maximum distance jump of 46.65m and delta satellite count of -14).
3. **Degenerate Feature Bug (`feat_sat_usage_ratio`)**: `feat_sat_usage_ratio` is **100% constant at 1.0** across all 9,382 rows ($\sigma = 0.0$). The root cause is multi-constellation GSV parsing in [`locus_collector.py`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/locus_collector.py), which overwrites total satellites in view with single-talker counts (0–5) against multi-GNSS tracked satellites (mean 21.2).
4. **Data Integrity**: **Zero infinite values and zero missing values** exist in [`locus_ml_dataset.csv`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/locus_ml_dataset.csv). Duplicate rows are 0.

---

## 2. Record Counts & Fix Quality Breakdown

### 2.1 Telemetry Records (`locus_telemetry_features.csv`)
- **Total Records Logged**: `10,938`
- **Valid Locked Fixes (`fix_quality > 0`)**: `9,382` (**85.77%**)
- **Invalid / Searching Fixes (`fix_quality == 0`)**: `1,556` (**14.23%**)

| Fix Quality Code | Meaning | Record Count | Percentage |
| :--- | :--- | :--- | :--- |
| `0` | Invalid / No Fix (Acquisition / Cold Start) | 1,556 | 14.23% |
| `1` | Autonomous GNSS SPS Fix | 9,382 | 85.77% |
| `2` | Differential GPS (DGPS) | 0 | 0.00% |
| `4/5` | RTK Fixed / Float | 0 | 0.00% |

### 2.2 ML Dataset Records (`locus_ml_dataset.csv`)
- **Total Feature Vectors**: `9,382`
- **Selection Criterion**: Exactly matches all locked fixes (`fix_quality > 0`) filtered from the telemetry log.

---

## 3. Missing & Duplicate Values

### 3.1 Missing Value Analysis
| Column Name | Telemetry Nulls | Telemetry Null % | ML Dataset Nulls | ML Dataset Null % | Root Cause / Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `timestamp_pc` | 0 | 0.00% | 0 | 0.00% | System wall-clock logged on every epoch |
| `timestamp_utc` | 0 | 0.00% | N/A | N/A | String formatted time; never null |
| `fix_quality` | 0 | 0.00% | N/A | N/A | Integer status flag |
| `latitude` | **1,476** | 13.50% | 0 | 0.00% | Null only during `fix_quality == 0` |
| `longitude` | **1,476** | 13.50% | 0 | 0.00% | Null only during `fix_quality == 0` |
| `altitude_m` | **1,556** | 14.23% | 0 | 0.00% | Null only during `fix_quality == 0` |
| `speed_kmh` | 0 | 0.00% | N/A | N/A | Defaults to `0.0` when uncomputed |
| `heading_deg` | 0 | 0.00% | N/A | N/A | Defaults to `0.0` when uncomputed |
| `satellites_used` | 0 | 0.00% | N/A | N/A | Defaults to `0` when uncomputed |
| `satellites_in_view` | 0 | 0.00% | N/A | N/A | Defaults to `0` when uncomputed |
| `hdop` | **1,555** | 14.22% | N/A | N/A | Missing during fix acquisition |
| `pdop` | **1,555** | 14.22% | N/A | N/A | Missing during fix acquisition |
| `vdop` | **1,555** | 14.22% | N/A | N/A | Missing during fix acquisition |
| `avg_cno` | 0 | 0.00% | 0 (`feat_mean_cno`) | 0.00% | 258 zero-values during cold start |
| `max_cno` | 0 | 0.00% | N/A | N/A | Defaults to `0.0` when uncomputed |
| `min_cno` | 0 | 0.00% | N/A | N/A | Defaults to `0.0` when uncomputed |
| *All 10 ML Features* | N/A | N/A | **0** | **0.00%** | Completely clean in ML dataset |

### 3.2 Duplicate Analysis
- **Exact Duplicate Rows**: `0` in telemetry, `0` in ML dataset.
- **Timestamp (`timestamp_pc`) Duplicates**: `0` in telemetry, `0` in ML dataset.

---

## 4. Timestamp & Session Analysis

### 4.1 PC Timestamp Interval Distribution
Inspection of consecutive epoch differences ($\Delta t = t_i - t_{i-1}$) in `timestamp_pc`:

| Metric | Seconds | Notes |
| :--- | :--- | :--- |
| **Minimum $\Delta t$** | `0.0054 s` (5.4 ms) | Serial UART buffer batch reads / burst flush |
| **Percentile 1% ($P_{01}$)** | `0.7837 s` | Buffer timing jitter |
| **Percentile 25% ($P_{25}$)**| `0.9981 s` | Stable 1 Hz operation |
| **Median ($P_{50}$)** | `0.9999 s` | Nominal 1 Hz receiver output rate |
| **Percentile 75% ($P_{75}$)**| `1.0018 s` | Stable 1 Hz operation |
| **Percentile 99% ($P_{99}$)**| `1.0333 s` | Negligible operating jitter |
| **Maximum $\Delta t$** | `88,706.94 s` | ~24.64 hours (Overnight collection pause) |

### 4.2 Identified Data Collection Sessions
Using a standard session demarcation threshold ($\Delta t > 5.0\text{ seconds}$), the collected data naturally divides into **15 distinct sessions**:

| Session ID | Start PC Time | End PC Time | Total Records | Valid Fixes | Gap to Next Session | Operational Context |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **1** | 2026-09-25 00:03:48 | 2026-09-25 00:11:20 | 452 | 0 | 10.01 hours | Initial hardware bring-up (no lock) |
| **2** | 2026-09-25 10:11:56 | 2026-09-25 10:12:29 | 33 | 0 | 87.99 s | Brief restart |
| **3** | 2026-09-25 10:13:57 | 2026-09-25 10:19:48 | 354 | 0 | 12.33 mins | Warm-up search |
| **4** | 2026-09-25 10:32:08 | 2026-09-25 10:40:52 | 527 | 236 | **24.64 hours** | First satellite lock achieved |
| **5** | 2026-09-26 11:19:19 | 2026-09-26 11:36:00 | 1,003 | 993 | **24.29 hours** | Day 2 continuous logging |
| **6** | 2026-09-27 11:53:28 | 2026-09-27 11:53:40 | 12 | 0 | 6.62 mins | Day 3 power-on |
| **7** | 2026-09-27 12:00:17 | 2026-09-27 12:00:17 | 1 | 0 | 55.26 s | Reconnect test |
| **8** | 2026-09-27 12:01:12 | 2026-09-27 12:02:06 | 65 | 0 | 14.80 s | Reconnect test |
| **9** | 2026-09-27 12:02:21 | 2026-09-27 12:03:37 | 87 | 8 | 36.15 mins | Lock acquired |
| **10** | 2026-09-27 12:39:46 | 2026-09-27 13:38:54 | 3,555 | 3,512 | 63.00 s | Major daytime baseline session |
| **11** | 2026-09-27 13:39:57 | 2026-09-27 13:40:28 | 32 | 31 | **8.21 hours** | Short continuation |
| **12** | 2026-09-27 21:52:52 | 2026-09-27 21:53:39 | 62 | 0 | 83.66 s | Night-time session restart |
| **13** | 2026-09-27 21:55:03 | 2026-09-27 21:55:08 | 6 | 0 | 20.18 s | Cold start check |
| **14** | 2026-09-27 21:55:28 | 2026-09-27 21:55:34 | 12 | 0 | 29.88 s | Cold start check |
| **15** | 2026-09-27 21:56:04 | 2026-09-27 23:15:00 | 4,737 | 4,602 | N/A | Major night-time baseline session |

---

## 5. Physical Range Metrics (Valid Locked Fixes, N = 9,382)

| Metric | Min | $P_{01}$ | $P_{05}$ | Median | Mean | $P_{95}$ | $P_{99}$ | Max | Std Dev |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Latitude (°N)** | 23.1039 | 23.1039 | 23.1039 | 23.1043 | 23.1043 | 23.1044 | 23.1044 | 23.1045 | 0.0001° (~11m) |
| **Longitude (°E)** | 72.5923 | 72.5923 | 72.5924 | 72.5925 | 72.5925 | 72.5926 | 72.5926 | 72.5927 | 0.00007° (~7m) |
| **Altitude (m)** | 53.41 | 56.76 | 57.97 | 67.03 | 66.12 | 74.04 | 84.16 | 106.48 | 5.40 m |
| **Speed (km/h)** | 0.00 | 0.00 | 0.00 | 0.09 | 0.22 | 0.78 | 2.07 | 4.37 | 0.39 km/h |
| **Heading (°)** | 0.00 | 0.97 | 30.10 | 217.26 | 205.41 | 350.07 | 350.43 | 356.05 | 127.77° |
| **Satellites Used** | 5.0 | 8.8 | 12.0 | 22.0 | 21.24 | 26.0 | 27.0 | 27.0 | 4.57 sats |
| **Sats in View (Raw)**| 0.0 | 0.0 | 0.0 | 1.0 | 1.24 | 4.0 | 4.0 | 5.0 | 1.40 sats |
| **HDOP** | 0.63 | 0.64 | 0.67 | 0.86 | 0.95 | 1.51 | 1.97 | 2.67 | 0.27 |
| **PDOP** | 0.87 | 0.89 | 1.02 | 1.25 | 1.34 | 1.90 | 2.86 | 3.36 | 0.32 |
| **VDOP** | 0.60 | 0.60 | 0.75 | 0.88 | 0.93 | 1.20 | 2.35 | 2.93 | 0.22 |
| **Avg C/N0 (dB-Hz)**| 11.11 | 19.42 | 21.75 | 27.80 | 27.35 | 31.08 | 35.00 | 36.67 | 2.80 dB-Hz |
| **Max C/N0 (dB-Hz)**| 17.00 | 31.00 | 35.00 | 41.00 | 40.67 | 44.00 | 45.00 | 45.00 | 3.24 dB-Hz |
| **Min C/N0 (dB-Hz)**| 4.00 | 6.00 | 7.00 | 11.00 | 11.63 | 17.00 | 27.00 | 29.00 | 3.62 dB-Hz |

### Physical Interpretation:
- The receiver was placed at a fixed stationary location ($\approx 23.1043^\circ\text{N}, 72.5925^\circ\text{E}$, elevation $\approx 66\text{ m}$).
- Ground speed from Doppler (`speed_kmh`) is strictly stationary noise ($\le 0.78\text{ km/h}$ at 95th percentile, maximum 4.37 km/h).
- Satellite geometry is outstanding ($99\%$ of HDOP is below $1.97$), and tracked satellite counts reach up to 27 satellites, confirming multi-GNSS tracking (GPS + GLONASS + Galileo + BeiDou).

---

## 6. Ten Core ML Feature Statistics (`locus_ml_dataset.csv`)

| Feature Column | Min | $P_{05}$ | $P_{50}$ (Median) | Mean | $P_{95}$ | $P_{99}$ | Max | Std Dev |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `feat_dist_jump_m` | 0.000 | 0.000 | 0.033 | 0.081 | 0.231 | 0.784 | **46.649** | 0.611 m |
| `feat_derived_speed_mps` | 0.000 | 0.000 | 0.033 | 0.071 | 0.228 | 0.765 | **6.995** | 0.157 m/s |
| `feat_speed_discrepancy_mps` | 0.000 | 0.000 | 0.017 | 0.041 | 0.139 | 0.347 | **6.311** | 0.114 m/s |
| `feat_vertical_velocity_mps` | 0.000 | 0.000 | 0.010 | 0.050 | 0.169 | 0.350 | **22.542** | 0.301 m/s |
| `feat_mean_cno` | 11.11 | 21.75 | 27.80 | 27.35 | 31.08 | 35.00 | 36.67 | 2.80 dB-Hz |
| `feat_cno_spread` | 8.00 | 20.00 | 30.00 | 29.04 | 35.00 | 37.00 | 40.00 | 4.75 dB-Hz |
| `feat_delta_sats` | **-14.00** | -1.00 | 0.00 | 0.002 | 1.00 | 1.00 | 3.00 | 0.37 sats |
| `feat_sat_usage_ratio` | **1.000** | **1.000** | **1.000** | **1.000** | **1.000** | **1.000** | **1.000** | **0.000** |
| `feat_hdop_rate` | -0.949 | -0.010 | 0.000 | -0.0003 | 0.000 | 0.190 | 0.670 | 0.046 |
| `feat_heading_rate_deg_s` | 0.000 | 0.000 | 0.000 | 0.762 | 0.000 | 14.443 | 179.952 | 8.383 °/s |

---

## 7. In-Depth Investigations

### Investigation 1: GNSS UTC Timestamp vs. PC Timestamp
- **Current Observation**: In [`locus_collector.py`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/locus_collector.py), `timestamp_utc` is extracted using `getattr(msg, "timestamp", None)` from RMC sentences. In `pynmea2`, `msg.timestamp` provides only `datetime.time(hh, mm, ss.sss)`. It **omits the calendar date**.
- **Buffer Delays**: `timestamp_pc` suffers from serial UART buffer burst-reads, occasionally producing inter-record delays of 5–30 ms when reading backlogged lines, followed by clamping to `1.0` in [`locus_features.py`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/locus_features.py).
- **Audit Verdict**:
  1. Full GNSS UTC datetime (`msg.datetime` combining `datestamp` and `timestamp`) must be captured in the collector.
  2. For epoch differentials ($\Delta t$) during locked tracking, GNSS UTC time is strictly superior because it is synchronized with satellite atomic clocks and has zero operating system jitter.
  3. `timestamp_pc` should remain in the schema as the monotonic audit time to track system arrival and manage inter-session breaks.

---

### Investigation 2: Whether Feature Calculations Cross Session Gaps
- **Audit Verdict**: **YES, feature calculations directly cross session gaps.**
- **Evidence from Raw Data**:
  - **Row 235** was logged on `2026-09-25T10:39:38.996764`.
  - **Row 236** was logged on `2026-09-26T11:19:24.043912`.
  - The gap is **88,785.05 seconds** (24.66 hours).
  - Because [`locus_features.py`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/locus_features.py) iterates sequentially without checking session boundaries, Row 236 was compared against Row 235:
    - `feat_dist_jump_m` calculated: **46.65 meters** (the maximum in the entire dataset!).
    - `feat_delta_sats` calculated: **-4 satellites**.
  - Similarly, Row 1228 to 1229 crossed a 24.46-hour gap, producing an artificial distance jump of **27.72 meters**.
  - At Row 4780, crossing a 29,868-second gap produced `feat_delta_sats = -14`.
- **Impact**: Cross-session differentials contaminate the normal baseline and would trigger false-positive physical integrity alerts at the start of every session.
- **Remediation**: Session segmentation must be introduced into the feature pipeline. Differentials for the first row of any new session must be set to `0.0`.

---

### Investigation 3: Why `feat_sat_usage_ratio` Appears Constant
- **Audit Verdict**: `feat_sat_usage_ratio` is completely invariant ($\text{mean}=1.0, \text{std}=0.0$) due to a clipping artifact caused by a collector bug.
- **Mathematical Demonstration**:
  - In [`locus_features.py` (L100-101)](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/locus_features.py#L100-L101):
    ```python
    sats_view = df["satellites_in_view"].replace(0, 1).fillna(1)
    df["feat_sat_usage_ratio"] = (df["satellites_used"] / sats_view).clip(0.0, 1.0)
    ```
  - In [`locus_collector.py`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/locus_collector.py), `satellites_in_view` is defective and holds values between `0` and `5` (mean: 1.24).
  - Meanwhile, `satellites_used` (from GGA) correctly tracks multi-GNSS satellites (mean: 21.24, range: 5 to 27).
  - For every single locked row, $\text{satellites\_used} \ge \text{sats\_view}$.
  - The unclipped ratio is always $\ge 1.0$ (ranging from $2.0$ to $27.0$), which `.clip(0.0, 1.0)` clamps to **1.000** for $100\%$ of records.

---

### Investigation 4 & 5: Calculation of `satellites_in_view` and GSV Aggregation
- **Audit Verdict**: `satellites_in_view` is **incorrectly calculated** due to multi-constellation NMEA sentence overwriting.
- **Technical Explanation**:
  - The Quectel L89HA module concurrently receives GPS, GLONASS, Galileo, and BeiDou signals.
  - In NMEA 0183, each constellation transmits its own GSV sentences:
    - `$GPGSV` (GPS)
    - `$GLGSV` (GLONASS)
    - `$GAGSV` (Galileo)
    - `$GBGSV` (BeiDou)
  - Each GSV sentence contains `num_sv_in_view` for *that specific constellation only* (e.g., 5 Galileo satellites).
  - In [`locus_collector.py` (L148-151)](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/locus_collector.py#L148-L151):
    ```python
    elif stype == "GSV":
        siv = getattr(msg, "num_sv_in_view", None)
        if siv and str(siv).isdigit():
            aggregator.sats_in_view = int(siv)
    ```
  - As each GSV sentence arrives, `aggregator.sats_in_view` is repeatedly **overwritten** rather than summed across constellations.
  - When the RMC epoch triggers `export_row()`, `satellites_in_view` simply contains whichever constellation was parsed last (frequently BeiDou or Galileo with 0 to 5 satellites).
  - In 4,643 rows (42.4%), `satellites_in_view` logged as `0` because the trailing GSV talker had 0 satellites in view.
- **GSV C/N0 Aggregation**:
  - `aggregator.cno_list` correctly appends carrier-to-noise values across all incoming GSV sentences within an epoch and clears them after `RMC`. This explains why `avg_cno` (mean: 27.35 dB-Hz) and `max_cno` (mean: 40.67 dB-Hz) are valid.

---

### Investigation 6: Presence of Invalid or Infinite Values
- **Audit Verdict**:
  - **Mathematical Inf / NaN**: **0 infinite values and 0 NaN values** exist in [`locus_ml_dataset.csv`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/locus_ml_dataset.csv).
  - **Physically Contaminated Values**:
    - `feat_dist_jump_m`: Values of `46.65m` and `27.72m` are invalid physical artifacts caused by crossing 24-hour session boundaries.
    - `feat_derived_speed_mps`: The maximum of `6.995 m/s` (25.2 km/h) occurred at Row 237 immediately following cold-start lock acquisition as the internal receiver filter converged.
    - `feat_vertical_velocity_mps`: The maximum of `22.54 m/s` occurred similarly during initial altitude lock stabilization.
    - `feat_sat_usage_ratio`: Degenerate constant column ($1.0$).

---

## 8. Concrete Recommendations for Phase 2 Pipeline

1. **Session Boundary Detection**:
   - Implement automatic session demarcation in the processing pipeline: any interval where $\Delta t > 5.0\text{ s}$ or where UTC date increments initiates a new `session_id`.
   - Initialize differential metrics (`feat_dist_jump_m`, `feat_derived_speed_mps`, `feat_delta_sats`, `feat_hdop_rate`, `feat_heading_rate_deg_s`) to `0.0` at the start of each session.
2. **Correct Multi-Constellation GSV Aggregation**:
   - Update the epoch aggregator to store satellites in view per constellation talker (`dict[talker, sv_count]`).
   - Total `satellites_in_view` should equal $\sum_{\text{constellations}} \text{sv\_count}$.
   - This will restore `feat_sat_usage_ratio` to a genuine dynamic ratio ($\approx 21 / 28 = 0.75$).
3. **Capture Full GNSS Datetime**:
   - Update NMEA ingestion to parse `msg.datetime` from RMC to maintain full UTC timestamp continuity.

---

*Report generated and validated autonomously as part of LOCUS Phase 1.*
