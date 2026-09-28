# LOCUS Data Dictionary — Structured GNSS Observations

**Dataset Path**: [`data/structured/locus_structured_gnss.csv`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/data/structured/locus_structured_gnss.csv)  
**Schema Version**: 1.0 (Phase 2 Refactor)  
**Total Records**: 10,938  
**Domain**: Raw and Preprocessed GNSS Physical Observations (NOT Machine Learning Features)  

---

## 1. Overview & Architectural Role

[`locus_structured_gnss.csv`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/data/structured/locus_structured_gnss.csv) serves as the **immutable observation layer** for the LOCUS cybersecurity framework. It decouples low-level serial NMEA ingestion from downstream security feature engineering and agentic anomaly detection.

Every record represents a **1-second physical observation epoch** captured from the Quectel L89HA multi-GNSS receiver.

---

## 2. Field Definitions & Schema

| # | Column Name | Data Type | Physical Unit | Permissible Range | Nullable | Description & Security Significance |
| :-: | :--- | :---: | :---: | :---: | :---: | :--- |
| **1** | `epoch_id` | `int64` | Counter | $[1, \infty)$ | No | Sequential 1-indexed epoch counter within the current session. Resets to 1 at every session boundary. |
| **2** | `session_id` | `int64` | Identifier | $[1, \infty)$ | No | Unique identifier for continuous logging periods separated by time gaps $> 5.0\text{ s}$. Prevents cross-session differential contamination. |
| **3** | `timestamp_gnss` | `string` | ISO-8601 (UTC) | `YYYY-MM-DDTHH:MM:SS.sssZ` | No | Reconstructed atomic GNSS UTC timestamp. Synchronized with satellite atomic clocks; primary time base for physical $\Delta t$ and velocity calculations. |
| **4** | `timestamp_pc` | `string` | ISO-8601 (Local) | `YYYY-MM-DDTHH:MM:SS.ffffff` | No | Host PC operating system receipt timestamp (+05:30 IST). Serves as monotonic audit time and tracks system-level arrival delays. |
| **5** | `latitude` | `float64` | Degrees North | $[-90.0, 90.0]$ | Yes | WGS-84 geodetic latitude. Null during fix search (`fix_quality == 0`). Validated against boundary bounds. |
| **6** | `longitude` | `float64` | Degrees East | $[-180.0, 180.0]$ | Yes | WGS-84 geodetic longitude. Null during fix search (`fix_quality == 0`). Validated against boundary bounds. |
| **7** | `altitude_m` | `float64` | Meters | $[-500.0, 50000.0]$ | Yes | Antenna altitude above mean sea level (orthometric height from GGA). Null during fix search. |
| **8** | `speed_kmh` | `float64` | km/h | $[0.0, 1000.0]$ | No | Ground speed measured by receiver via Doppler shift on carrier frequency. Independent from coordinate-derived speed. |
| **9** | `heading_deg` | `float64` | Degrees True | $[0.0, 360.0)$ | No | True track heading over ground from RMC. |
| **10** | `fix_quality` | `int64` | Enum Code | $\{0, 1, 2, 4, 5\}$ | No | NMEA GGA fix quality status: `0` = Invalid/Searching, `1` = Autonomous GPS SPS, `2` = Differential GPS / SBAS corrected. |
| **11** | `satellites_used` | `int64` | Count | $[0, 36]$ | No | Number of active satellites contributing to the position-velocity-time (PVT) navigation solution from GGA. |
| **12** | `satellites_in_view` | `int64` | Count | $[0, 60]$ | No | Total visible satellites above the horizon across all constellations (GPS, GLONASS, Galileo, BeiDou). Summed across multi-talker GSV messages. |
| **13** | `satellite_prns` | `string` | Semicolon Delimited | e.g. `"GP01;GP03;GL07"` | Yes | Sorted list of active satellite pseudo-random noise (PRN) identifiers. Essential for set-theoretic `sat_churn` calculation. |
| **14** | `hdop` | `float64` | Ratio | $[0.5, 50.0]$ | Yes | Horizontal Dilution of Precision. Geometric satellite distribution quality in the horizontal plane (lower is better). |
| **15** | `vdop` | `float64` | Ratio | $[0.5, 50.0]$ | Yes | Vertical Dilution of Precision. Satellite geometry in the vertical axis. |
| **16** | `pdop` | `float64` | Ratio | $[0.5, 50.0]$ | Yes | 3D Position Dilution of Precision: $\text{PDOP} = \sqrt{\text{HDOP}^2 + \text{VDOP}^2}$. |
| **17** | `avg_cno` | `float64` | dB-Hz | $[0.0, 60.0]$ | No | Arithmetic mean of Carrier-to-Noise density ratio ($C/N_0$) across all tracking channels in the epoch. Primary indicator of RF jamming. |
| **18** | `max_cno` | `float64` | dB-Hz | $[0.0, 60.0]$ | No | Peak signal strength observed among visible satellites. |
| **19** | `min_cno` | `float64` | dB-Hz | $[0.0, 60.0]$ | No | Lowest usable signal strength observed among visible satellites. |
| **20** | `data_quality_flag`| `string` | Bitmask / Tags | Pipe-delimited | No | Explicit observation health classification (e.g., `"VALID\|PRN_UNAVAILABLE"`). Prevents silent deletion of flawed rows. |

---

## 3. Data Quality Flag Taxonomy (`data_quality_flag`)

Rather than silently dropping unfixable or searching records, LOCUS marks every epoch with human-readable, pipe-delimited quality flags:

| Quality Flag Tag | Condition / Trigger | Operational Interpretation |
| :--- | :--- | :--- |
| `VALID` | `fix_quality > 0` and valid WGS-84 coordinates | Nominal locked GNSS fix suitable for security feature extraction. |
| `NO_FIX` | `fix_quality == 0` or missing coordinates | Receiver in signal acquisition, cold-start, or complete RF blockage. |
| `INVALID_COORDS` | Lat $\notin [-90, 90]$ or Lon $\notin [-180, 180]$ | Malformed coordinates or uninitialized buffer corruption. |
| `DEGRADED_DOP` | $\text{HDOP} > 3.0$ or $\text{PDOP} > 5.0$ | Severe geometric dilution (e.g. indoor/canyon masking). Low integrity. |
| `LOW_CNO` | $0 < \text{avg\_cno} < 20.0\text{ dB-Hz}$ | Weak signal reception; potential RF jamming or heavy attenuation. |
| `SESSION_START` | $\Delta t_{\text{PC}} > 5.0\text{ s}$ or `epoch_id == 1` | First epoch of a new session. Differential features must initialize to 0.0. |
| `DUPLICATE_EPOCH` | Identical timestamp to previous row | Serial buffer duplicate; excluded from velocity differentials. |
| `PRN_UNAVAILABLE` | `satellite_prns` is empty/null | Individual satellite IDs were not recorded in the raw telemetry stream. |

### Quality Flag Distribution in Baseline Dataset (N = 10,938)
- `VALID|PRN_UNAVAILABLE`: **9,253** (84.60%) — Clean locked fixes.
- `NO_FIX|PRN_UNAVAILABLE`: **1,373** (12.55%) — Clean acquisition periods.
- `NO_FIX|LOW_CNO|PRN_UNAVAILABLE`: **168** (1.54%) — Cold-start weak signal search.
- `VALID|LOW_CNO|PRN_UNAVAILABLE`: **129** (1.18%) — Locked fixes with attenuated signal.
- `SESSION_START|NO_FIX|PRN_UNAVAILABLE`: **15** (0.14%) — Session demarcation initializers.

---

## 4. Satellite PRN Availability & Churn Strategy

### 4.1 Historical Dataset Limitation
- **Status**: `satellite_prns = null` across all 10,938 historical records.
- **Root Cause**: The initial hardware logger [`locus_collector.py`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/locus_collector.py) parsed GSV signal strengths (`snr_1`..`snr_4`) but did not store satellite PRN identifiers (`sv_prn_num_*`) in the raw CSV schema.
- **Mitigation for Historical Baseline**: When computing Phase 4 security features on historical data, `sat_churn` will be computed via the empirical **satellite flux proxy**:
  $$\text{sat\_churn}_{\text{proxy}}(t) = \frac{|\Delta S_{\text{used}}| + \text{clip}\left(\frac{|\Delta \text{avg\_cno}|}{3.0}, 0, 2\right)}{\Delta t}$$

### 4.2 Upgraded Collection Pipeline (Future Recordings)
- [`src/parsing/nmea_parser.py`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/src/parsing/nmea_parser.py) and [`src/parsing/epoch_aggregator.py`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/src/parsing/epoch_aggregator.py) now parse:
  - GSV: `sv_prn_num_1` through `sv_prn_num_4` with constellation talker prefix (`GP`, `GL`, `GA`, `BD`).
  - GSA: `sv_id01` through `sv_id12` active channels.
- When new collection runs are conducted, `satellite_prns` will populate automatically with semicolon-delimited PRN strings (e.g., `"GP01;GP03;GL07;GA05"`), enabling true set-theoretic Jaccard churn calculation:
  $$\text{sat\_churn}_{\text{set}}(t) = \frac{|\text{PRNs}_t \setminus \text{PRNs}_{t-1}| + |\text{PRNs}_{t-1} \setminus \text{PRNs}_t|}{\Delta t}$$

---

## 5. Distinction: Observations vs. Features

It is critical to distinguish between this observation dataset and the downstream security feature vector:

| Aspect | Structured Observations ([`locus_structured_gnss.csv`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/data/structured/locus_structured_gnss.csv)) | Security Features ([`locus_security_features.csv`](file:///c:/Users/New/Downloads/Logs/Logs/Task/locus_project/data/features/locus_security_features.csv)) |
| :--- | :--- | :--- |
| **Phase** | Phase 2 Refactor & Phase 3 Dataset | Phase 4 Feature Engineering |
| **Content** | Direct sensor measurements (lat, lon, alt, DOP, C/N0, sats) | Engineered differentials (kinematic velocity, acceleration, jerk, bearing rate, churn) |
| **Normalization** | Physical engineering units (meters, degrees, dB-Hz) | Standardized, bounded security metrics |
| **Filtering** | Retains all epochs (including `fix_quality == 0` with flags) | Filters strictly to valid epochs for ML/threat detection |

---

*Document compiled and verified autonomously as part of LOCUS Phase 2 Refactoring.*
