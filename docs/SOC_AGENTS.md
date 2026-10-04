# LOCUS Phase 6 — Agentic Security SOC Layer

## Executive Overview
Phase 6 establishes the autonomous **Agentic Security SOC Layer** atop the LOCUS multi-detector Evidence Bundle. The architecture implements a tripartite hierarchy designed for deterministic verification, temporal threat correlation, and multi-agent incident orchestration.

```
       +--------------------------------------------------------+
       |             Phase 5/5.5 Evidence Bundle                |
       |  (10-D Security Features, Rules, IF, LSTM, XGBoost)   |
       +---------------------------+----------------------------+
                                   |
                   +---------------+---------------+
                   | (Read-Only)                   | (Read-Only)
                   v                               v
+------------------------------------+  +------------------------------------+
|    Agent 1: GNSS Integrity Agent   |  |  Agent 2: Temporal / Threat Agent  |
|  (src/agents/integrity_agent.py)   |  | (src/agents/temporal_threat_agent) |
|  - Physical plausibility           |  |  - Persistent sequence tracking    |
|  - Fix integrity                   |  |  - Multi-detector convergence      |
|  - Navigation geometry (HDOP/VDOP) |  |  - LSTM error attribution          |
|  - Satellite churn & starvation    |  |  - XGBoost status handling         |
|  - 10-D feature-level anomalies    |  |  - Historical session buffer       |
+-----------------+------------------+  +-----------------+------------------+
                  |                                        |
                  | Integrity Assessment                   | Temporal Assessment
                  +-------------------+--------------------+
                                      |
                                      v
            +----------------------------------------------------+
            |        Agent 3: Master SOC Agent Orchestrator       |
            |          (src/agents/master_soc_agent.py)          |
            |  - Evidence synthesis & grounded citations         |
            |  - Inter-agent conflict resolution                 |
            |  - DEFCON 1-5 Risk Assessment                      |
            |  - RAG regulatory context integration              |
            |  - Actionable mitigation recommendations           |
            +-------------------------+--------------------------+
                                      |
                                      v
                        SOCOrchestrationResult (JSON)
```

---

## Strict Core Invariants

1. **Zero Sensor Mutation (Read-Only Enforcement)**:
   - Agents never alter, overwrite, or mutate raw sensor telemetry or Evidence Bundles.
   - Strictly verified via automated regression tests (`test_invariants_sensor_data_immutability`).
2. **Zero Evidence Fabrication**:
   - Agents are forbidden from hallucinating or inventing sensor readings or metric values.
   - All factual claims and justifications cite verified feature keys and numeric values.
3. **Calibrated Confidence**:
   - Confidence drops when satellite count $< 6$, when dilution of precision is elevated ($HDOP > 4.0$), or when detector signals conflict.
   - Certainty is never claimed when observations are insufficient.

---

## Agent Specifications

### Agent 1 — GNSS Integrity Agent (`src/agents/integrity_agent.py`)
- **Responsibilities**:
  - **Physical Plausibility**: Evaluates kinematic boundaries ($acc > 10.0\text{ m/s}^2$, $jerk > 25.0\text{ m/s}^3$, $vel > 85.0\text{ m/s}$, $disp > 100.0\text{ m}$).
  - **Fix Integrity**: Verifies carrier-phase and pseudo-range consistency (`fix_integrity < 0.20` critical).
  - **Navigation Quality**: Evaluates geometry dilution ($HDOP > 8.0$, $VDOP > 10.0$).
  - **Satellite Behaviour**: Detects constellation starvation ($sats < 4$) and sudden churn ($churn > 0.60$).
  - **Feature-Level Anomalies**: Generates granular per-feature violation records with thresholds and observed numbers.
- **Output Schema**:
  - `integrity_assessment`: `INTEGRITY_NOMINAL`, `GEOMETRY_DEGRADED`, `KINEMATIC_VIOLATION`, `CRITICAL_INVARIANT_BREACH`.
  - `supporting_evidence`: List of exact cited features, values, and thresholds.
  - `confidence`: $[0.0, 1.0]$.
  - `explanation`: Human-readable and auditable rationale.
  - `discard_recommended`: Boolean directive for immediate epoch exclusion.

### Agent 2 — Temporal / Threat Correlation Agent (`src/agents/temporal_threat_agent.py`)
- **Responsibilities**:
  - **Persistent Anomalies**: Tracks rolling temporal windows (default 10 epochs) and consecutive anomaly streaks.
  - **Temporal Sequence Modeling**: Evaluates LSTM Autoencoder reconstruction errors and identifies top feature error contributors.
  - **Supervised Correlation**: Ingests XGBoost supervised status.
  - **Multi-Detector Convergence**: Computes weighted agreement across Physical Rules, Isolation Forest, and LSTM Autoencoder.
  - **Session Memory**: Maintains session-isolated history buffers with explicit reset capabilities.
- **Output Schema**:
  - `temporal_assessment`: `BENIGN`, `TRANSIENT_ANOMALY`, `PERSISTENT_DRIFT`, `RF_JAMMING_DEGRADATION`, `SPOOFING_COORDINATE_STEP`, `SPOOFING_TRAJECTORY_INJECTION`.
  - `pattern_description`: Detailed temporal sequence analysis.
  - `supporting_evidence`: List of detector errors, streaks, and convergence percentages.
  - `detector_convergence`: $[0.0, 1.0]$.
  - `primary_feature_contributors`: Top reconstructed features driving LSTM error.

### Agent 3 — Master SOC Agent / Evidence Orchestrator (`src/agents/master_soc_agent.py`)
- **Responsibilities**:
  - **Evidence Synthesis**: Combines Evidence Bundle, Agent 1 findings, Agent 2 findings, and optional RAG context.
  - **Conflict Resolution**:
    - Acute physical invariant violations (e.g. teleportation) take immediate priority over temporal buffering delays $\to$ resolves immediately as `DEFCON_1_CRITICAL` (`CONFIRMED_ATTACK`).
    - Isolated transient spikes with zero persistence resolve as `DEFCON_4_GUARDED` (`TRANSIENT_NOISE`).
    - Multi-detector convergence on sustained drift resolves as `DEFCON_2_HIGH` or `DEFCON_1_CRITICAL`.
  - **RAG Context Integration**: Cross-references regulatory frameworks (ICAO Annex 10 SARPs, RTCA DO-229, IMO MSC.401).
- **Structured Output Schema**:
  ```json
  {
    "event_id": "evt_sess_1_ep_10",
    "status": "CONFIRMED_ATTACK",
    "risk_level": "DEFCON_1_CRITICAL",
    "confidence": 0.98,
    "summary": "CRITICAL EMERGENCY: Catastrophic physical invariant violation confirmed. [Evidence cited: disp_haversine = 150.0 (threshold: 100.0)] | Agent 1 (CRITICAL_INVARIANT_BREACH), Agent 2 (SPOOFING_COORDINATE_STEP, streak: 1).",
    "evidence": {
      "event_id": "evt_sess_1_ep_10",
      "timestamp_utc": "2026-03-30T12:00:00Z",
      "session_id": 1,
      "epoch_id": 10,
      "location": { "latitude": 37.7749, "longitude": -122.4194, "altitude_m": 15.0 },
      "security_features": {
        "disp_haversine": 150.0,
        "vel_kinematic": 12.5,
        "acc_kinematic": 0.8,
        "jerk_kinematic": 0.2,
        "bearing_rate": 1.5,
        "HDOP": 1.2,
        "VDOP": 1.8,
        "fix_integrity": 0.95,
        "sat_count_tot": 10,
        "sat_churn": 0.05
      },
      "detector_metrics": {
        "physical_rules_triggered_count": 1,
        "physical_rules_max_severity": "CRITICAL",
        "isolation_forest_anomaly_score": 0.72,
        "isolation_forest_is_anomaly": true,
        "lstm_reconstruction_error": 0.25,
        "lstm_error_threshold": 0.08,
        "lstm_is_anomaly": true,
        "xgboost_status": "UNFITTED_PENDING_LABELLED_SCENARIOS"
      }
    },
    "agent_findings": {
      "integrity_agent": { ... },
      "temporal_threat_agent": { ... },
      "rag_context": null
    },
    "recommended_next_action": [
      "EMERGENCY_GNSS_LOCKOUT",
      "SWITCH_TO_INERTIAL_DEAD_RECKONING",
      "REJECT_EPOCH_MEASUREMENT",
      "BROADCAST_SECURITY_ALERT"
    ]
  }
  ```

---

## Test Verification
- Complete test suite: `tests/test_agents.py` (14 unit and integration tests passing).
- Whole project verification: 63 out of 63 tests passing across all test files with 100% coverage of Phase 1 through Phase 6.
