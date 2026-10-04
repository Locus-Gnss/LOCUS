# GNSS Spoofing Attacks & Threat Attribution

**Topic**: GNSS False Signal Injection, Meaconing, and Spoofing Detection  
**Standard Authorities**: CISA Resilient PNT Conformance Framework, ICAO Doc 9849, MITRE ATT&CK for Space  
**Domain Tags**: `spoofing`, `meaconing`, `signal_injection`, `teleportation`, `velocity_discrepancy`, `mitigation`

---

## 1. Threat Taxonomy & Attack Classes

GNSS spoofing is the deliberate transmission of counterfeit radio frequency signals designed to deceive a target receiver into calculating an incorrect position, velocity, or time (PVT).

Major attack categories:
1. **Asynchronous / Simplistic Spoofing**: The attacker broadcasts unaligned counterfeit signals with higher power ($> 3\text{ to }10\text{ dB}$ above legitimate satellite signals). Causes sudden tracking loop unlock and abrupt re-acquisition at a counterfeit coordinate.
2. **Synchronous / Intermediate (Lift-Off) Spoofing**: The attacker aligns counterfeit code phase and carrier frequency with authentic satellite signals, gradually ramps up power to capture receiver tracking loops (delay-locked loops and phase-locked loops), and slowly steers coordinates away from ground truth.
3. **Meaconing (Record and Replay)**: Delay and re-broadcast of genuine RF signals. Introduces an artificial pseudo-range offset corresponding to the delay and re-transmitter baseline.
4. **Coordinated Multi-Target Spoofing**: Coordinated manipulation of multi-constellation channels to mimic legitimate receiver motion while redirecting a target asset.

---

## 2. Key Physical Detection Signatures

Empirical investigations identify four critical physical signatures of spoofing attacks:

### 2.1 Kinematic Teleportation & Step Discontinuities
When an unsophisticated spoofer seizes tracking loops, the estimated coordinate jumps instantaneously. Across a 1-second interval $\Delta t = 1.0\text{s}$, a position jump exceeding Newtonian constraints ($v > 85\text{ m/s}$, $a > 10\text{ m/s}^2$, or $j > 25\text{ m/s}^3$) violates physical plausibility for terrestrial vehicular receivers.

### 2.2 Doppler vs. Coordinate Velocity Discrepancy
Authentic receivers measure velocity through Doppler shift on incoming carrier frequencies ($v_{\text{carrier}}$) independent of numerical differences between consecutive coordinates ($v_{\text{coord}} = \Delta \text{pos} / \Delta t$).
$$\text{velocity\_discrepancy} = \| v_{\text{carrier}} - v_{\text{coord}} \|$$
In authentic operation, $\text{velocity\_discrepancy} \le 0.5\text{ m/s}$. During spoofing injection, counterfeit coordinates steer away while Doppler shift reflects the fixed or divergent spoofer antenna motion, creating an unmistakable discrepancy ($> 3.0\text{ m/s}$).

### 2.3 Unnatural Carrier-to-Noise ($C/N_0$) Homogeneity & Elevation Inversion
Authentic satellites exhibit varying signal powers ($C/N_0 \in [20, 48]\text{ dB-Hz}$) correlated with elevation angle (low elevation satellites suffer heavier atmospheric attenuation). Counterfeit spoofers transmitted from a single antenna typically exhibit uniform signal strengths across all channels and unnaturally strong signals for low-elevation satellites.

---

## 3. Recommended Containment & Mitigation Directives

According to CISA Resilient PNT Guidelines (Levels 3 & 4):
1. **Immediate PNT Disqualification**: Mark GNSS fix as untrusted (`DEFCON_1_CRITICAL`).
2. **Sensor Decoupling**: Decouple GNSS receiver input from navigation Kalman filters (autopilot, flight management system, or power grid synchrophasor).
3. **Failover to Inertial / Dead-Reckoning**: Transition to INS, wheel odometry, visual odometry, or alternate terrestrial signals.
4. **RF Forensics & Antenna Nulling**: Trigger adaptive beamforming / controlled reception pattern antennas (CRPA) to place nulls in the direction of the interference source.
