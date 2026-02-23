"""
Task 4 — Rule-Based Anomaly Detection
======================================
Detects health anomalies from the patient master table.

Rules:
  - HR > 120              → High Heart Rate
  - OX < 92               → Low Oxygen
  - SYS > 160 or DIA > 100 → High Blood Pressure

Input:  silver/patient_master.csv
Output: gold/anomalies.csv
Format: patient_id, timestamp, anomaly, value

Re-run anytime to refresh.
"""

import os
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
MASTER_PATH = os.path.join(ROOT_DIR, "silver", "patient_master.csv")

# --- Load ---
master = pd.read_csv(MASTER_PATH)
print(f"Loaded {len(master)} records from patient_master.csv")

anomalies = []

for _, row in master.iterrows():
    pid = row["patient_id"]
    ts = row["vitals_timestamp"]

    # Rule 1: High Heart Rate
    if row["hr"] > 120:
        anomalies.append({
            "patient_id": pid,
            "timestamp": ts,
            "anomaly": "High Heart Rate",
            "value": row["hr"],
        })

    # Rule 2: Low Oxygen
    if row["ox"] < 92:
        anomalies.append({
            "patient_id": pid,
            "timestamp": ts,
            "anomaly": "Low Oxygen",
            "value": row["ox"],
        })

    # Rule 3: High Blood Pressure
    if row["sys"] > 160 or row["dia"] > 100:
        anomalies.append({
            "patient_id": pid,
            "timestamp": ts,
            "anomaly": "High Blood Pressure",
            "value": f"{row['sys']}/{row['dia']}",
        })

# --- Save ---
df = pd.DataFrame(anomalies)
output_path = os.path.join(SCRIPT_DIR, "anomalies.csv")
df.to_csv(output_path, index=False)

print(f"\n✓ Saved anomalies.csv ({len(df)} anomalies detected)")
if len(df) > 0:
    print(f"  Breakdown:")
    for atype, count in df["anomaly"].value_counts().items():
        print(f"    {atype}: {count}")
