# GNSS Jamming & Radio Frequency Interference (RFI)

**Topic**: Radio Frequency Interference, Deliberate Jamming, Denial-of-Service  
**Standard Authorities**: ITU Radio Regulations, RTCA DO-235B, EUROCONTROL GNSS Interference Guidelines  
**Domain Tags**: `jamming`, `RFI`, `C/N0`, `signal_attenuation`, `starvation`, `loss_of_lock`

---

## 1. Nature of GNSS Signal Vulnerability to Jamming

GNSS signals travel over 20,000 km from medium Earth orbit (MEO). Upon reaching the Earth's surface, the received signal power is extremely faint:
$$P_{\text{rx}} \approx -160\text{ dBW} \quad (-130\text{ dBm})$$
This received power is approximately $20\text{ dB}$ below the ambient thermal noise floor ($-110\text{ dBm}$ across a 2 MHz bandwidth). Reception relies on Code Division Multiple Access (CDMA) correlation gain. Consequently, low-power transmitters (e.g. 10 mW to 1 W personal privacy devices) can easily overwhelm the front-end amplifier of a GNSS receiver over ranges from hundreds of meters to tens of kilometers.

---

## 2. Jamming Signatures & Physical Indicators

### 2.1 Carrier-to-Noise Density ($C/N_0$) Plunge
Under nominal conditions:
$$\text{mean } C/N_0 \in [35.0, 48.0]\text{ dB-Hz}$$
When wideband, pulsed, or swept-frequency chirp jamming begins:
- Carrier-to-noise ratio plummets precipitously:
  $$\text{mean } C/N_0 < 25.0\text{ dB-Hz} \implies \text{Severe Interference}$$
  $$\text{mean } C/N_0 < 20.0\text{ dB-Hz} \implies \text{Critical Jamming Floor / Impending Fix Loss}$$

### 2.2 Constellation Starvation & Cycle Slips
- Receiver Phase-Lock Loops (PLL) and Frequency-Lock Loops (FLL) lose tracking lock.
- Tracked satellite count ($S_{\text{used}}$) collapses from multi-constellation nominals ($18\text{ to }28\text{ satellites}$) down to $< 4$ satellites within 1 to 3 seconds.
- Geometric Dilution of Precision ($\text{HDOP}$) diverges exponentially:
  $$\text{HDOP} > 5.0 \implies \text{Extreme Dilution}$$
  $$\text{HDOP} \ge 8.0 \implies \text{Total Geometric Failure}$$

---

## 3. Operational Risk Levels & Actionable Directives

- **DEFCON 3 (Elevated / Low C/N0 Alert)**: $C/N_0 \in [20.0, 25.0]\text{ dB-Hz}$ with degraded DOP.
  - Action: Alert navigation supervisor, engage secondary GNSS frequency bands (L2C, L5, Galileo E5a), verify antenna cable shielding integrity.
- **DEFCON 2 (High Jamming Denial)**: $C/N_0 < 20.0\text{ dB-Hz}$ with progressive satellite drop.
  - Action: Assert GNSS denial state, engage RF notch filters or adaptive spatial filtering, switch to dead-reckoning.
- **DEFCON 1 (Complete Loss of PNT)**: $S_{\text{used}} < 4$ and fix quality drops to `0`.
  - Action: Total failover to non-GNSS navigation, log spectrum capture for regulatory investigation (FCC / ITU compliance reporting).
