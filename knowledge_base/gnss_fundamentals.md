# GNSS Fundamentals & Signal Structure

**Topic**: Global Navigation Satellite Systems (GNSS) Principles  
**Standard Authorities**: ICAO Annex 10 Vol I, IS-GPS-200, Galileo OS SIS ICD  
**Domain Tags**: `GNSS`, `trilateration`, `pseudo_range`, `carrier_phase`, `constellations`

---

## 1. Principles of Satellite Navigation

Global Navigation Satellite Systems (GNSS) comprise constellations of Earth-orbiting satellites providing global positioning, navigation, and timing (PNT) services. Major civilian constellations include:
- **GPS (Global Positioning System)**: United States (L1: 1575.42 MHz, L2: 1227.60 MHz, L5: 1176.45 MHz).
- **GLONASS**: Russian Federation (FDMA channels centered around G1: 1602 MHz, G2: 1246 MHz, CDMA L3).
- **Galileo**: European Union (E1: 1575.42 MHz, E5a: 1176.45 MHz, E5b: 1207.14 MHz).
- **BeiDou (BDS)**: China (B1I: 1561.098 MHz, B1C: 1575.42 MHz, B2a: 1176.45 MHz).
- **QZSS**: Japan regional augmentation constellation.

GNSS receivers determine position by measuring the time-of-flight of radio-frequency signals transmitted simultaneously by at least four satellites with precisely synchronized atomic clocks.

---

## 2. Ranging Measurements: Pseudo-Range & Carrier Phase

A receiver measures two fundamental observable metrics:
1. **Pseudo-Range ($P_i$)**: The apparent distance between the receiver antenna and satellite $i$, derived from code-phase time-of-flight measurements:
   $$P_i = \rho_i + c \cdot (\delta t_r - \delta t_s) + I_i + T_i + \epsilon_{P,i}$$
   where $\rho_i$ is true geometric distance, $c$ is light speed, $\delta t_r$ is receiver clock bias, $\delta t_s$ is satellite clock offset, $I_i$ is ionospheric delay, $T_i$ is tropospheric delay, and $\epsilon_{P,i}$ represents multipath and thermal noise.
2. **Carrier-Phase ($\Phi_i$)**: The accumulated phase of the incoming radio carrier frequency wave, providing millimeter-level precision but subject to an unknown integer cycle ambiguity $N_i$:
   $$\Phi_i = \frac{1}{\lambda} \rho_i + \frac{c}{\lambda} (\delta t_r - \delta t_s) + N_i - \frac{I_i}{\lambda} + \frac{T_i}{\lambda} + \epsilon_{\Phi,i}$$

---

## 3. Position, Velocity, and Time (PVT) Solution

Solving for receiver position $(x_r, y_r, z_r)$ and receiver clock bias $b_r = c \cdot \delta t_r$ requires linearizing the pseudo-range equations around an estimated state via Taylor series expansion and solving iteratively via Weighted Least Squares (WLS) or Extended Kalman Filtering (EKF).

Velocity is computed through Doppler shift measurements on the received carrier frequencies, reflecting the relative line-of-sight velocity vector between the satellite and receiver:
$$f_D = - \frac{1}{\lambda} (\mathbf{v}_s - \mathbf{v}_r) \cdot \mathbf{u}_{sr}$$
where $\mathbf{u}_{sr}$ is the unit vector pointing from receiver to satellite. Doppler velocity is independent of coordinate differential positions and provides a critical cross-check against position displacement.
