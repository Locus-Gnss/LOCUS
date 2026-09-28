"""
generate_validation_plots.py - Generate validation plots for LOCUS Phase 4 Official 10-D Security Features.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

features_file = "data/features/locus_security_features.csv"
output_dir = "docs/plots"
os.makedirs(output_dir, exist_ok=True)

df = pd.read_csv(features_file)
print(f"[*] Loaded {len(df)} feature records for validation plotting.")

# Set clean styling
plt.rcParams.update({
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "figure.titlesize": 14,
    "grid.alpha": 0.3,
})

# -------------------------------------------------------------
# PLOT 1: Kinematic / Physical Integrity
# -------------------------------------------------------------
fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

axes[0].plot(df["disp_haversine"], color="#1f77b4", lw=0.8, alpha=0.85)
axes[0].set_ylabel("Disp (m)")
axes[0].set_title("LOCUS Official 10-D Features — Kinematic & Physical Integrity (Stationary Baseline)")
axes[0].grid(True)
axes[0].set_ylim(-0.2, 3.0)

axes[1].plot(df["vel_kinematic"], color="#2ca02c", lw=0.8, alpha=0.85)
axes[1].set_ylabel("Vel (m/s)")
axes[1].grid(True)
axes[1].set_ylim(-0.2, 3.0)

axes[2].plot(df["acc_kinematic"], color="#ff7f0e", lw=0.8, alpha=0.85)
axes[2].set_ylabel("Acc (m/s²)")
axes[2].grid(True)
axes[2].set_ylim(-2.0, 2.0)

axes[3].plot(df["jerk_kinematic"], color="#d62728", lw=0.8, alpha=0.85)
axes[3].set_ylabel("Jerk (m/s³)")
axes[3].set_xlabel("Epoch Sequence Number")
axes[3].grid(True)
axes[3].set_ylim(-4.0, 4.0)

plt.tight_layout()
p1_path = os.path.join(output_dir, "kinematic_integrity.png")
plt.savefig(p1_path, dpi=200)
plt.close()
print(f"[+] Saved: {p1_path}")

# -------------------------------------------------------------
# PLOT 2: Navigation Quality & Satellite Behaviour
# -------------------------------------------------------------
fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

axes[0].plot(df["HDOP"], color="#9467bd", lw=0.8, label="HDOP")
axes[0].plot(df["VDOP"], color="#8c564b", lw=0.8, alpha=0.7, label="VDOP")
axes[0].set_ylabel("DOP Ratio")
axes[0].set_title("LOCUS Official 10-D Features — Navigation Quality & Constellation Behaviour")
axes[0].legend(loc="upper right")
axes[0].grid(True)
axes[0].set_ylim(0.5, 3.5)

axes[1].plot(df["fix_integrity"], color="#17becf", lw=0.8)
axes[1].set_ylabel("Fix Integrity [0-1]")
axes[1].grid(True)
axes[1].set_ylim(0.2, 1.0)

axes[2].plot(df["sat_count_tot"], color="#e377c2", lw=0.8)
axes[2].set_ylabel("Sats Used")
axes[2].grid(True)
axes[2].set_ylim(0, 30)

axes[3].plot(df["bearing_rate"], color="#7f7f7f", lw=0.8)
axes[3].set_ylabel("Bearing Rate (°/s)")
axes[3].set_xlabel("Epoch Sequence Number")
axes[3].grid(True)
axes[3].set_ylim(-5, 45)

plt.tight_layout()
p2_path = os.path.join(output_dir, "navigation_quality.png")
plt.savefig(p2_path, dpi=200)
plt.close()
print(f"[+] Saved: {p2_path}")

# -------------------------------------------------------------
# PLOT 3: Feature Distributions & Session Boundary Protection
# -------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# Subplot A: Displacement Distribution (log scale)
axes[0, 0].hist(df["disp_haversine"], bins=50, color="#1f77b4", edgecolor="black", alpha=0.7, log=True)
axes[0, 0].set_title("Displacement Distribution (log)")
axes[0, 0].set_xlabel("disp_haversine (m)")
axes[0, 0].set_ylabel("Frequency")
axes[0, 0].grid(True)

# Subplot B: Acceleration Distribution
axes[0, 1].hist(df["acc_kinematic"].clip(-1.0, 1.0), bins=50, color="#ff7f0e", edgecolor="black", alpha=0.7)
axes[0, 1].set_title("Acceleration Distribution (centered at 0)")
axes[0, 1].set_xlabel("acc_kinematic (m/s²)")
axes[0, 1].set_ylabel("Frequency")
axes[0, 1].grid(True)

# Subplot C: Fix Integrity Distribution
axes[1, 0].hist(df["fix_integrity"], bins=50, color="#17becf", edgecolor="black", alpha=0.7)
axes[1, 0].set_title("Fix Integrity Distribution")
axes[1, 0].set_xlabel("fix_integrity [0.0 - 1.0]")
axes[1, 0].set_ylabel("Frequency")
axes[1, 0].grid(True)

# Subplot D: Satellite Count Distribution
axes[1, 1].hist(df["sat_count_tot"], bins=25, color="#e377c2", edgecolor="black", alpha=0.7)
axes[1, 1].set_title("Total Satellites Used Distribution")
axes[1, 1].set_xlabel("sat_count_tot")
axes[1, 1].set_ylabel("Frequency")
axes[1, 1].grid(True)

plt.tight_layout()
p3_path = os.path.join(output_dir, "feature_distributions.png")
plt.savefig(p3_path, dpi=200)
plt.close()
print(f"[+] Saved: {p3_path}")
print("[+] All validation plots successfully generated!")
