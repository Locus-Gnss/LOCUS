# Security Concepts, Threat Attribution & Regulatory Frameworks

**Topic**: Cyber-Physical Security, MITRE ATT&CK for Space, Regulatory Standards  
**Standard Authorities**: MITRE ATT&CK for Space, CISA Resilient PNT Framework, ICAO Annex 10, RTCA DO-229E  
**Domain Tags**: `security_concepts`, `MITRE_ATTACK`, `CISA`, `DEFCON`, `regulatory_framework`, `mitigation`

---

## 1. Threat Frameworks: MITRE ATT&CK for Space Systems

In the MITRE ATT&CK for Space matrix, PNT interference and receiver disruption map to specific adversary techniques:
- **T0803 (Signal Manipulation / Spoofing)**: Adversaries broadcast counterfeit RF signals containing forged ephemeris or delayed pseudo-ranges to mislead position or timing calculations.
- **T0858 (Denial of Service / Jamming)**: Adversaries flood receiver RF bands with broadband or swept noise to saturate the low-noise amplifier (LNA), inducing loss of signal tracking.
- **T0859 (Eavesdropping / RF Signal Interception)**: Adversaries intercept unencrypted downlink signals to conduct reconnaissance on constellation geometry and active PRNs prior to launching synchronous lift-off attacks.
- **T0880 (Meaconing / Replay)**: Adversaries capture and delay genuine GNSS signals without decoding them, re-transmitting them to create controlled position offsets.

---

## 2. DEFCON Operational Threat Matrix

LOCUS synthesizes multi-detector evidence into a standardized 5-tier DEFCON readiness framework:

| Readiness Level | State Designation | Diagnostic Trigger | Mandated Action / Containment |
| :---: | :---: | :--- | :--- |
| **DEFCON 5** | **Nominal All-Clear** | All physical invariants respected; IForest $< 0.40$; LSTM within threshold. | Maintain standard GNSS navigation and autonomous operations. |
| **DEFCON 4** | **Guarded / Transient Noise** | Isolated single-epoch spike without persistence (streak $< 3$); minor DOP flutter. | Log telemetry epoch; increase observation frequency; continue monitoring. |
| **DEFCON 3** | **Elevated Threat** | Moderate DOP degradation ($> 3.0$); $C/N_0$ dip below 25 dB-Hz; or unconfirmed ML anomaly. | Warn navigation supervisor; cross-check multi-constellation consistency; prepare dead-reckoning. |
| **DEFCON 2** | **High Threat / Persistent Drift** | Sustained LSTM reconstruction error $> 3$ consecutive epochs; progressive coordinate drift. | Disengage GNSS from primary autopilot; switch to dead-reckoning; notify SOC operator. |
| **DEFCON 1** | **Critical Breach / Active Attack** | Hard physical rule violation (teleportation, $a > 10\text{ m/s}^2$); acute spoofing injection. | Immediate emergency fail-safe; isolate GNSS receiver; engage CRPA beam nulling; broadcast cyber incident report. |

---

## 3. Strict Compliance Guidelines for RAG Integration

1. **Non-Mutation of Telemetry**: The RAG engine functions exclusively as an informative, grounding, and explanatory system. It must **never** overwrite, interpolate, or fabricate raw sensor numbers.
2. **Citation Provenance**: Every generated mitigation or regulatory assessment must link directly to an indexed authority (e.g. `ICAO Annex 10`, `RTCA DO-229E`, `CISA PNT Levels`, `MITRE ATT&CK`).
3. **Explicit Insufficient Context Fallback**: If a query or anomaly vector does not match any indexed knowledge chunk with high semantic similarity, the RAG engine must explicitly state:
   > "Insufficient knowledge context retrieved for the specified query."
   It must never hallucinate external standards, fake document titles, or fabricate non-existent thresholds.
