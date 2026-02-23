import os
import json
import logging
from typing import Tuple

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  
import matplotlib.pyplot as plt


### Configuration here

HR_THRESHOLD = 120
OX_THRESHOLD = 92
SYS_THRESHOLD = 160
DIA_THRESHOLD = 100

BRONZE_DIR = "bronze"
SILVER_DIR = "silver"
GOLD_DIR = "gold"
VIS_DIR = "visualizations"
INPUT_DIR = "INPUT_DATA"  


## Setup Logging here

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

## Utility Functions


def create_directories():
    for folder in [BRONZE_DIR, SILVER_DIR, GOLD_DIR, VIS_DIR]:
        os.makedirs(folder, exist_ok=True)


# Bronze Layer to store raw files

def load_and_store_bronze():
    logging.info("Loading raw files into Bronze layer...")

    # EHR
    ehr_path = os.path.join(INPUT_DIR, "ehr.csv")
    ehr_df = pd.read_csv(ehr_path)
    ehr_df.to_csv(f"{BRONZE_DIR}/ehr.csv", index=False)

    # Vitals: support both .json (array) and .jsonl (lines)
    vitals_jsonl = os.path.join(INPUT_DIR, "vitals.jsonl")
    vitals_json = os.path.join(INPUT_DIR, "vitals.json")
    if os.path.isfile(vitals_jsonl):
        vitals_df = pd.read_json(vitals_jsonl, lines=True)
    elif os.path.isfile(vitals_json):
        vitals_df = pd.read_json(vitals_json)  # JSON array
    else:
        raise FileNotFoundError(f"Neither {vitals_jsonl} nor {vitals_json} found.")
    vitals_df.to_csv(f"{BRONZE_DIR}/vitals.csv", index=False)

    # Labs JSON
    labs_path = os.path.join(INPUT_DIR, "labs.json")
    with open(labs_path) as f:
        labs_data = json.load(f)
    labs_df = pd.DataFrame(labs_data)
    labs_df.to_csv(f"{BRONZE_DIR}/labs.csv", index=False)

    return ehr_df, vitals_df, labs_df


# Silver Layer  


def clean_vitals(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Cleaning vitals data...")

    df = df.rename(columns={"patientId": "patient_id"})
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

    numeric_cols = ["hr", "ox", "sys", "dia"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.drop_duplicates()
    df = df.dropna()

    # Remove impossible values
    df = df[(df["hr"] > 0) & (df["ox"] <= 100) & (df["sys"] > 0) & (df["dia"] > 0)]

    df.to_csv(f"{SILVER_DIR}/clean_vitals.csv", index=False)
    return df


def clean_labs(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Cleaning labs data...")

    rename_map = {"test": "lab_test", "value": "lab_value"}
    if "patientId" in df.columns:
        rename_map["patientId"] = "patient_id"
    df = df.rename(columns=rename_map)

   
    ts = df["timestamp"]
    if pd.api.types.is_numeric_dtype(ts):
        df["timestamp"] = pd.to_datetime(ts, unit="s")
    else:
        df["timestamp"] = pd.to_datetime(ts)
    df["lab_value"] = pd.to_numeric(df["lab_value"], errors="coerce")

    df = df.drop_duplicates()
    df = df.dropna(subset=["patient_id", "lab_test", "lab_value"])

    df = df[df["lab_value"] > 0]

    df.to_csv(f"{SILVER_DIR}/clean_labs.csv", index=False)
    return df


## Gold Layer


def create_patient_master(ehr_df, vitals_df, labs_df):
    logging.info("Creating patient master table...")

    latest_vitals = (
        vitals_df.sort_values("timestamp")
        .groupby("patient_id")
        .tail(1)
    )

    latest_labs = (
        labs_df.sort_values("timestamp")
        .groupby(["patient_id", "lab_test"])
        .tail(1)
    )

    latest_labs = latest_labs.pivot(
        index="patient_id",
        columns="lab_test",
        values="lab_value"
    ).reset_index()

    master = (
        ehr_df
        .merge(latest_vitals, on="patient_id", how="left")
        .merge(latest_labs, on="patient_id", how="left")
    )

    master.to_csv(f"{SILVER_DIR}/patient_master.csv", index=False)
    return master


# Anomaly Detection

def detect_anomalies(vitals_df: pd.DataFrame):
    logging.info("Detecting anomalies...")

    df = vitals_df.copy()
    rows = []

    for _, row in df.iterrows():
        if row["hr"] > HR_THRESHOLD:
            rows.append({
                "patient_id": row["patient_id"],
                "timestamp": row["timestamp"],
                "anomaly": "High Heart Rate",
                "value": row["hr"],
            })
        if row["ox"] < OX_THRESHOLD:
            rows.append({
                "patient_id": row["patient_id"],
                "timestamp": row["timestamp"],
                "anomaly": "Low Oxygen",
                "value": row["ox"],
            })
        if row["sys"] > SYS_THRESHOLD or row["dia"] > DIA_THRESHOLD:
            # Value: the one that triggered (prefer sys if both)
            val = row["sys"] if row["sys"] > SYS_THRESHOLD else row["dia"]
            rows.append({
                "patient_id": row["patient_id"],
                "timestamp": row["timestamp"],
                "anomaly": "High Blood Pressure",
                "value": val,
            })

    anomaly_df = pd.DataFrame(rows)
    anomaly_df.to_csv(f"{GOLD_DIR}/anomalies.csv", index=False)


# Visualization

def generate_visualizations(vitals_df: pd.DataFrame, anomalies_path: str):
    logging.info("Generating visualizations...")

    # Heart Rate Trend
    for pid, group in vitals_df.groupby("patient_id"):
        plt.figure()
        plt.plot(group["timestamp"], group["hr"])
        plt.title(f"Heart Rate Trend - {pid}")
        plt.xlabel("Timestamp")
        plt.ylabel("Heart Rate")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{VIS_DIR}/hr_trend_{pid}.png")
        plt.close()

    # Oxygen Distribution — highlight low oxygen (ox < 92)
    plt.figure()
    low_ox = vitals_df[vitals_df["ox"] < OX_THRESHOLD]["ox"]
    normal_ox = vitals_df[vitals_df["ox"] >= OX_THRESHOLD]["ox"]
    plt.hist([normal_ox, low_ox], bins=15, label=["Normal (ox ≥ 92)", "Low oxygen (ox < 92)"], color=["steelblue", "coral"])
    plt.axvline(OX_THRESHOLD, color="red", linestyle="--", label=f"Threshold ({OX_THRESHOLD})")
    plt.title("Oxygen Level Distribution")
    plt.xlabel("Oxygen Saturation (%)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{VIS_DIR}/oxygen_distribution.png")
    plt.close()

    # Anomaly Counts (x = anomaly type, y = number of occurrences)
    anomaly_df = pd.read_csv(anomalies_path)

    plt.figure()
    anomaly_df["anomaly"].value_counts().plot(kind="bar")
    plt.title("Anomaly Counts")
    plt.xlabel("Anomaly Type")
    plt.ylabel("Number of Occurrences")
    plt.tight_layout()
    plt.savefig(f"{VIS_DIR}/anomaly_counts.png")
    plt.close()

#### Main Execution

def main():
    create_directories()

    ehr_df, vitals_df, labs_df = load_and_store_bronze()

    vitals_clean = clean_vitals(vitals_df)
    labs_clean = clean_labs(labs_df)

    master = create_patient_master(ehr_df, vitals_clean, labs_clean)

    detect_anomalies(vitals_clean)

    generate_visualizations(vitals_clean, f"{GOLD_DIR}/anomalies.csv")

    logging.info("Pipeline execution completed successfully")


if __name__ == "__main__":
    main()