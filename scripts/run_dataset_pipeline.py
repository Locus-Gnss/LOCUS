"""
run_dataset_pipeline.py - Complete LOCUS Architecture Dataset Ingestion & Processing Pipeline

Executes the official 6-tier LOCUS GNSS processing pipeline:
1. Telemetry Cleaning & Atomic UTC Reconstruction (src/locus_quality.py)
2. Differential Features Extraction (src/locus_features_v2.py)
3. Structured GNSS Observation Tier (src/parsing/preprocessing.py)
4. Canonical 10-D Security Feature Vector (src/features/security_features.py)
5. Multi-Detector Training & Evidence Fusion (src/detection/pipeline.py)
6. 3-Agent Security SOC Deliberation & Incident Stream (src/soc/soc_pipeline.py)
"""

import os
import sys
import time

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(base_dir)
sys.path.insert(0, base_dir)

print("=" * 70)
print("LOCUS COMPLETE DATASET PIPELINE ARCHITECTURE RUNNER")
print(f"Working Directory: {base_dir}")
print("=" * 70)

t0 = time.time()

# ----------------------------------------------------
# Step 1: Telemetry Cleaning & Quality Inspection
# ----------------------------------------------------
print("\n>>> [1/6] Running Telemetry Cleaning & Quality Engine (src/locus_quality.py)...")
from src.locus_quality import clean_telemetry

raw_csv = os.path.join(base_dir, "data", "raw", "locus_telemetry_features.csv")
clean_csv = os.path.join(base_dir, "data", "processed", "locus_telemetry_clean.csv")

df_clean = clean_telemetry(raw_csv, clean_csv)
n_clean = len(df_clean)
n_sessions = df_clean["session_id"].nunique()
n_valid = int(df_clean["is_fix_valid"].sum())
print(f"[+] Step 1 Complete: {n_clean} total epochs across {n_sessions} sessions ({n_valid} locked fixes).")

# ----------------------------------------------------
# Step 2: Features v2 Differential Extraction
# ----------------------------------------------------
print("\n>>> [2/6] Running Features v2 Extraction Engine (src/locus_features_v2.py)...")
from src.locus_features_v2 import extract_features_v2

feat_v2_csv = os.path.join(base_dir, "data", "features", "locus_features_v2.csv")
df_v2 = extract_features_v2(clean_csv, feat_v2_csv)
print(f"[+] Step 2 Complete: {len(df_v2)} feature vectors extracted (0 NaNs: {df_v2.isna().sum().sum() == 0}).")

# ----------------------------------------------------
# Step 3: Structured GNSS Observation Dataset
# ----------------------------------------------------
print("\n>>> [3/6] Running Structured GNSS Preprocessor (src/parsing/preprocessing.py)...")
from src.parsing.preprocessing import GNSSPreprocessor

struct_csv = os.path.join(base_dir, "data", "structured", "locus_structured_gnss.csv")
preprocessor = GNSSPreprocessor()
df_struct = preprocessor.process_file(raw_csv, struct_csv)
print(f"[+] Step 3 Complete: {len(df_struct)} structured observations generated.")

# ----------------------------------------------------
# Step 4: Canonical 10-D Security Feature Engineering
# ----------------------------------------------------
print("\n>>> [4/6] Running 10-D Security Feature Extractor (src/features/security_features.py)...")
from src.features.security_features import generate_security_features_file

sec_feat_csv = os.path.join(base_dir, "data", "features", "locus_security_features.csv")
df_sec = generate_security_features_file(struct_csv, sec_feat_csv)
print(f"[+] Step 4 Complete: {len(df_sec)} 10-D security feature vectors extracted.")

# ----------------------------------------------------
# Step 5: Multi-Detector ML & Evidence Fusion Engine
# ----------------------------------------------------
print("\n>>> [5/6] Running Detection & Evidence Fusion Pipeline (src/detection/pipeline.py)...")
from src.detection.pipeline import run_phase_5_pipeline

run_phase_5_pipeline()
print("[+] Step 5 Complete: Models trained and Evidence Bundles generated.")

# ----------------------------------------------------
# Step 6: 3-Agent Security SOC Pipeline Runner
# ----------------------------------------------------
print("\n>>> [6/6] Running 3-Agent Security SOC Deliberation (src/soc/soc_pipeline.py)...")
from src.soc.soc_pipeline import run_phase_6_pipeline

incidents, summary = run_phase_6_pipeline()
print(f"[+] Step 6 Complete: {summary['total_epochs_processed']} epochs deliberated across SOC hierarchy.")

elapsed = time.time() - t0
print("\n" + "=" * 70)
print(f"PIPELINE RUN COMPLETED SUCCESSFULLY in {elapsed:.2f} seconds!")
print("=" * 70)
