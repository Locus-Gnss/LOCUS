# GNSS Integrity & Receiver Autonomous Integrity Monitoring (RAIM)

**Topic**: GNSS Integrity Assurance, Fault Detection and Exclusion (FDE)  
**Standard Authorities**: RTCA DO-229E (MOPS for GPS/WAAS), ICAO Annex 10 Vol I, FAA AC 20-138D  
**Domain Tags**: `integrity`, `RAIM`, `FDE`, `HPL`, `VPL`, `HAL`, `VAL`, `protection_level`

---

## 1. Concept of Navigation Integrity

Integrity is the measure of trust that can be placed in the correctness of the information supplied by the navigation system. Integrity includes the ability of the system to provide timely and valid warnings to users when the system must not be used for navigation.

Key integrity metrics defined in RTCA DO-229E:
- **Alert Limit (AL)**: The maximum permissible position error before an alert must be issued (e.g. Horizontal Alert Limit HAL, Vertical Alert Limit VAL).
- **Protection Level (PL)**: A statistical bound on the position error with a guaranteed integrity risk (e.g., $10^{-7}$ per flight hour). Computed as Horizontal Protection Level (HPL) and Vertical Protection Level (VPL).
- **Time-to-Alert (TTA)**: The maximum permissible elapsed time from when an unallowable condition occurs to when an alert is annunciated (typically 1.0 to 2.0 seconds for critical operations).

Integrity is compromised if the true position error exceeds the Protection Level, or if the Protection Level exceeds the Alert Limit ($\text{HPL} > \text{HAL}$).

---

## 2. RAIM Fault Detection and Exclusion (FDE)

Receiver Autonomous Integrity Monitoring (RAIM) performs consistency checks among redundant pseudo-range measurements:
- **Fault Detection (FD)** requires a minimum of **5 visible satellites** with acceptable geometry.
- **Fault Detection and Exclusion (FDE)** requires a minimum of **6 visible satellites** to isolate and reject the anomalous satellite without interrupting navigation.

### Parity Space Formulation
Linearized measurement model:
$$\mathbf{y} = \mathbf{G} \mathbf{x} + \mathbf{\epsilon}$$
where $\mathbf{G} \in \mathbb{R}^{n \times 4}$ is the geometry matrix ($n \ge 5$). The parity matrix $\mathbf{A} \in \mathbb{R}^{(n-4) \times n}$ satisfies $\mathbf{A} \mathbf{G} = \mathbf{0}$ and $\mathbf{A} \mathbf{A}^T = \mathbf{I}_{n-4}$.

The parity vector is:
$$\mathbf{p} = \mathbf{A} \mathbf{y} = \mathbf{A} \mathbf{\epsilon}$$
In the absence of satellite faults or spoofing, the test statistic $s = \|\mathbf{p}\|^2$ follows a central chi-squared distribution $\chi^2(n-4)$. If $s > T_{\text{RAIM}}$, a consistency fault is declared.

---

## 3. Physical Invariants and Fix Integrity Bounds

In the LOCUS framework, the composite metric `fix_integrity` quantifies single-epoch fix health:
$$\text{fix\_integrity} = \text{clip}\left(1.0 - \left( \frac{\text{HDOP}}{10.0} + 0.3 \cdot \mathbb{I}(\text{fix\_quality} = 0) + 0.2 \cdot \mathbb{I}(S_{\text{used}} < 5) \right), 0.0, 1.0\right)$$

- **Critical Integrity Breach**: $\text{fix\_integrity} < 0.20$ denotes an unviable or spoofed fix where pseudo-ranges and receiver geometry fail standard aeronautical tolerance.
- **Degraded Integrity**: $\text{fix\_integrity} \in [0.20, 0.45]$ requires immediate fallback checks against inertial sensors and cross-constellation corroboration.
