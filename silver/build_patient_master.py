"""
Task 3 — Combined Patient Master Table (Natural Join)
=====================================================
Natural join of clean_ehr + clean_vitals + clean_labs on patient_id.
Output: silver/patient_master.csv

Re-run anytime to refresh.
"""

import os
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Load clean data ---
ehr = pd.read_csv(os.path.join(SCRIPT_DIR, "clean_ehr.csv"))
vitals = pd.read_csv(os.path.join(SCRIPT_DIR, "clean_vitals.csv"))
labs = pd.read_csv(os.path.join(SCRIPT_DIR, "clean_labs.csv"))

print(f"Loaded: EHR={len(ehr)}, Vitals={len(vitals)}, Labs={len(labs)}")

# --- Rename timestamp columns to avoid clash ---
vitals = vitals.rename(columns={"timestamp": "vitals_timestamp"})
labs = labs.rename(columns={"timestamp": "labs_timestamp"})

# --- Natural join (inner) on patient_id ---
master = ehr.merge(vitals, on="patient_id", how="inner")
master = master.merge(labs, on="patient_id", how="inner")

# --- Sort ---
master = master.sort_values(["patient_id", "vitals_timestamp", "labs_timestamp"]).reset_index(drop=True)

# --- Save ---
output_path = os.path.join(SCRIPT_DIR, "patient_master.csv")
master.to_csv(output_path, index=False)
print(f"\n✓ Saved patient_master.csv ({len(master)} rows, {len(master.columns)} columns)")
print(f"  Columns: {list(master.columns)}")
print(f"  Unique patients: {master['patient_id'].nunique()}")
