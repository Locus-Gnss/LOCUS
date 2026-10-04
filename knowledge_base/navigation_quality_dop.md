# Navigation Quality & Dilution of Precision (DOP)

**Topic**: Geometry Metrics, Dilution of Precision, Fix Quality  
**Standard Authorities**: RTCA DO-229E, NMEA-0183 Standard, ICAO Annex 10 Vol I  
**Domain Tags**: `DOP`, `HDOP`, `VDOP`, `PDOP`, `GDOP`, `geometry`, `navigation_quality`

---

## 1. Mathematical Formulation of Dilution of Precision

Dilution of Precision (DOP) expresses the mathematical multiplier translating pseudo-range measurement errors ($\sigma_{\text{range}}$) into user position and time estimation errors ($\sigma_{\text{pos}}$):
$$\sigma_{\text{pos}} = \text{DOP} \cdot \sigma_{\text{range}}$$

Given unit line-of-sight direction vectors from user to satellite $i$:
$$\mathbf{u}_i = \left[ \frac{x_i - x}{\rho_i}, \frac{y_i - y}{\rho_i}, \frac{z_i - z}{\rho_i} \right]$$
The linearized geometry design matrix is:
$$\mathbf{G} = \begin{bmatrix}
\mathbf{u}_1 & 1 \\
\mathbf{u}_2 & 1 \\
\vdots & \vdots \\
\mathbf{u}_n & 1
\end{bmatrix} \in \mathbb{R}^{n \times 4}$$

The unweighted covariance matrix of the least-squares position and clock error is:
$$\mathbf{Q} = (\mathbf{G}^T \mathbf{G})^{-1} = \begin{bmatrix}
\sigma_{xx} & \sigma_{xy} & \sigma_{xz} & \sigma_{xt} \\
\sigma_{yx} & \sigma_{yy} & \sigma_{yz} & \sigma_{yt} \\
\sigma_{zx} & \sigma_{zy} & \sigma_{zz} & \sigma_{zt} \\
\sigma_{tx} & \sigma_{ty} & \sigma_{tz} & \sigma_{tt}
\end{bmatrix}$$

Individual DOP values are defined as:
- **Horizontal DOP (HDOP)**: $\text{HDOP} = \sqrt{\sigma_{xx} + \sigma_{yy}}$
- **Vertical DOP (VDOP)**: $\text{VDOP} = \sqrt{\sigma_{zz}}$
- **Position DOP (PDOP)**: $\text{PDOP} = \sqrt{\text{HDOP}^2 + \text{VDOP}^2} = \sqrt{\sigma_{xx} + \sigma_{yy} + \sigma_{zz}}$
- **Time DOP (TDOP)**: $\text{TDOP} = \sqrt{\sigma_{tt}}$
- **Geometric DOP (GDOP)**: $\text{GDOP} = \sqrt{\text{PDOP}^2 + \text{TDOP}^2}$

---

## 2. Operational Thresholds & Navigation Quality Tiers

| DOP Range | Navigation Quality | Operational Meaning |
| :---: | :---: | :--- |
| **$0.5 \le \text{HDOP} \le 1.5$** | **Optimal** | Superb satellite spatial dispersion across all 4 quadrants of the sky. Precision navigation supported. |
| **$1.5 < \text{HDOP} \le 2.5$** | **Nominal / Good** | Standard open-sky operational conditions. High confidence in coordinates. |
| **$2.5 < \text{HDOP} \le 4.0$** | **Moderate / Degraded** | Partial horizon obstruction (trees, light urban foliage). Coordinate error expanded by factor of 3–4. |
| **$4.0 < \text{HDOP} \le 8.0$** | **Poor / Unreliable** | Severe urban canyon or indoor masking. Warning annunciated; exclude from safety-critical automated maneuvers. |
| **$\text{HDOP} > 8.0$** | **Critical Navigation Failure** | Insufficient geometric baseline. Small pseudo-range errors explode into massive spatial deviations. |

---

## 3. Interaction Between DOP and Anomaly Detection

1. **Multipath & Building Reflections**: In urban canyons, building blockages inflate HDOP while generating delayed reflected signals (multipath), yielding apparent drift.
2. **Intentional Geometric Degradation**: An attacker jamming a specific azimuth or frequency band can blind satellites in one quadrant, forcing the receiver to rely on a co-linear subset of satellites and spiking HDOP.
3. **Plausibility Guard**: When evaluating an apparent coordinate displacement, the SOC agent must check if $\Delta \text{pos}$ coincided with a sudden surge in HDOP. An anomaly with high HDOP suggests physical geometric degradation rather than a stealthy spoofing attack.
