# Satellite Behaviour & Constellation Dynamics

**Topic**: Constellation Orbital Mechanics, Turnover Rate, Satellite Churn  
**Standard Authorities**: IS-GPS-200, Galileo OS SIS ICD, CISA PNT Integrity Guidelines  
**Domain Tags**: `satellite_behaviour`, `sat_churn`, `constellation`, `orbital_dynamics`, `turnover_rate`

---

## 1. Physical Satellite Orbital Dynamics

MEO GNSS satellites orbit Earth at altitudes approximately $20,200\text{ km}$ with orbital periods of approximately 11 hours 58 minutes (GPS) to 14 hours (Galileo).
From the perspective of a terrestrial stationary antenna:
- A single satellite traverses the visible horizon from rise (elevation $5^\circ$) to set over **4 to 8 hours**.
- The angular velocity across the celestial sphere is smooth and slow ($\le 0.03^\circ\text{ per second}$).
- Individual satellite acquisitions or drop events occur separated by intervals of **several minutes to hours**.

---

## 2. Set-Theoretic Satellite Churn ($\text{sat\_churn}$)

LOCUS defines the set-theoretic satellite churn rate as the symmetric difference of active satellite pseudo-random noise (PRN) identifier sets between consecutive epochs:

$$\text{sat\_churn}(t) = \frac{|\text{PRNs}_t \setminus \text{PRNs}_{t-1}| + |\text{PRNs}_{t-1} \setminus \text{PRNs}_t|}{\Delta t} \quad \left[\frac{\text{satellites}}{\text{second}}\right]$$

### Operational Churn Thresholds:
- **Nominal Baseline**: $\text{sat\_churn} \le 0.1\text{ sats/s}$. The set of tracked satellites is static over 1-second intervals, occasionally registering 1 acquisition or 1 loss over tens of minutes.
- **Moderate Constellation Turnover**: $\text{sat\_churn} \in (0.1, 0.4]\text{ sats/s}$. Occurs during dynamic platform maneuvers under partial canopy or building masking.
- **Anomalous Constellation Churn**: $\text{sat\_churn} > 0.4\text{ sats/s}$.
  - A sudden turnover of $\ge 3\text{ satellites}$ within a 1-second interval is physically impossible under standard orbital mechanics.
  - Primary causes:
    1. **Spoofer Capture / Handover**: The receiver locks onto a counterfeit constellation containing an entirely different set of PRNs.
    2. **Jamming Beam Sweeping**: Broad-spectrum RF sweep abruptly drops legitimate SVs.
    3. **Receiver Channel Crash**: Internal baseband correlator reset.

---

## 3. Total Satellite Counts & Constellation Starvation

Modern multi-GNSS receivers track signals concurrently across GPS, GLONASS, Galileo, and BeiDou:
- **Healthy Open-Sky Count**: $S_{\text{used}} \in [18, 32]\text{ satellites}$.
- **Degraded Visibility**: $S_{\text{used}} \in [8, 17]\text{ satellites}$.
- **Threshold of Starvation**: $S_{\text{used}} < 5\text{ satellites}$. A drop below 5 satellites prevents RAIM Fault Detection and Exclusion, leaving the navigation filter vulnerable to undetected manipulation.
