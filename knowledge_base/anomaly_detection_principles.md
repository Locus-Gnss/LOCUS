# Anomaly Detection Principles for Cyber-Physical GNSS Systems

**Topic**: Multi-Detector Quad, Kinematic Invariants, Machine Learning Detection  
**Standard Authorities**: RTCA DO-229E, CISA PNT Guidelines, IEEE Aerospace Systems  
**Domain Tags**: `anomaly_detection`, `physical_rules`, `isolation_forest`, `LSTM`, `XGBoost`, `multi_detector`

---

## 1. Multi-Tier Anomaly Detection Architecture

Relying on a single detection methodology introduces unacceptable vulnerability in safety-critical cyber-physical systems. LOCUS integrates four complementary detection paths:

1. **Path 1: Physical Plausibility Rules (Deterministic Hard Boundaries)**:
   - Grounded directly in Newtonian kinematics and receiver hardware constraints.
   - Zero training data requirement; invariant across all operational domains.
2. **Path 2: Unsupervised Spatial Outliers (Isolation Forest)**:
   - Evaluates multi-dimensional feature co-occurrences without requiring labeled attack examples.
   - Detects subtle out-of-distribution shifts in signal strength, DOP, and satellite counts.
3. **Path 3: Supervised Multi-Class Classifier (XGBoost)**:
   - Explicitly trained to separate specific attack signatures (Spoofing, Jamming, Meaconing, Multipath).
   - Provenance safeguard: Must not emit ungrounded probabilities on uncalibrated data.
4. **Path 4: Deep Temporal Autoencoder (LSTM Sequence Model)**:
   - Sliding sequence window ($W=10$) tracking temporal correlations and creeping drifts.
   - Computes reconstruction errors per feature, pinpointing the exact mathematical channel driving the anomaly.

---

## 2. Newtonian Kinematic Invariants

For terrestrial ground assets and standard civilian platforms, the laws of classical mechanics enforce hard physical limits on coordinate displacements:

| Metric | Form | Nominal Threshold | Maximum Physical Invariant | Violation Diagnosis |
| :--- | :---: | :---: | :---: | :--- |
| **Ground Velocity ($v$)** | $\Delta \text{pos} / \Delta t$ | $\le 30.0\text{ m/s}$ (108 km/h) | $\le 85.0\text{ m/s}$ (306 km/h) | Instantaneous coordinate teleportation (Spoofing) |
| **Kinematic Acceleration ($a$)** | $\Delta v / \Delta t$ | $\le 4.0\text{ m/s}^2$ | $\le 10.0\text{ m/s}^2$ (~1.02 G) | Unphysical vehicular propulsion (Spoofing / Multipath) |
| **Kinematic Jerk ($j$)** | $\Delta a / \Delta t$ | $\le 10.0\text{ m/s}^3$ | $\le 25.0\text{ m/s}^3$ | Step position injection (Spoofing) |
| **Bearing Rate ($\dot{\theta}$)** | Normalized circular $\Delta \theta$ | $\le 45.0^\circ\text{/s}$ | $\le 180.0^\circ\text{/s}$ | Abrupt unphysical course pivot |

Any violation of maximum physical invariants represents a deterministic cyber-physical breach, triggering immediate DEFCON 1 escalation regardless of statistical ML model outputs.

---

## 3. Evidence Fusion & Grounded Deliberation

The Evidence Fusion Engine aggregates detector findings into structured, immutable JSON containers (`EvidenceBundle`).
- **No Direct Actuation by Detectors**: Individual detectors do not make operational decisions; they compile evidence.
- **Evidence Immutability**: Evidence bundles preserve raw observation metrics alongside computed detector outputs.
- **SOC Agent Deliberation**: The autonomous 3-agent SOC inspects the Evidence Bundle, cites exact numbers, cross-references regulatory RAG context, and issues auditable operational directives.
