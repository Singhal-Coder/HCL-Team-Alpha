import os
import json
import logging
from typing import Tuple

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==============================
# Configuration
# ==============================

HR_THRESHOLD = 120
OX_THRESHOLD = 92
SYS_THRESHOLD = 160
DIA_THRESHOLD = 100

BRONZE_DIR = "bronze"
SILVER_DIR = "silver"
GOLD_DIR = "gold"
VIS_DIR = "visualizations"

# ==============================
# Setup Logging
# ==============================

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# ==============================
# Utility Functions
# ==============================

def create_directories():
    for folder in [BRONZE_DIR, SILVER_DIR, GOLD_DIR, VIS_DIR]:
        os.makedirs(folder, exist_ok=True)


# ==============================
# Bronze Layer
# ==============================

def load_and_store_bronze():
    logging.info("Loading raw files into Bronze layer...")

    # EHR
    ehr_df = pd.read_csv("ehr.csv")
    ehr_df.to_csv(f"{BRONZE_DIR}/ehr.csv", index=False)

    # Vitals JSONL
    vitals_df = pd.read_json("vitals.jsonl", lines=True)
    vitals_df.to_csv(f"{BRONZE_DIR}/vitals.csv", index=False)

    # Labs JSON
    with open("labs.json") as f:
        labs_data = json.load(f)
    labs_df = pd.DataFrame(labs_data)
    labs_df.to_csv(f"{BRONZE_DIR}/labs.csv", index=False)

    return ehr_df, vitals_df, labs_df


# ==============================
# Silver Layer – Cleaning
# ==============================

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

    df = df.rename(columns={
        "patientId": "patient_id",
        "test": "lab_test",
        "value": "lab_value"
    })

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df["lab_value"] = pd.to_numeric(df["lab_value"], errors="coerce")

    df = df.drop_duplicates()
    df = df.dropna(subset=["patient_id", "lab_test", "lab_value"])

    df = df[df["lab_value"] > 0]

    df.to_csv(f"{SILVER_DIR}/clean_labs.csv", index=False)
    return df


# ==============================
# Gold Layer – Master Table
# ==============================

def create_patient_master(ehr_df, vitals_df, labs_df):
    logging.info("Creating patient master table...")

    # Latest vitals
    latest_vitals = (
        vitals_df.sort_values("timestamp")
        .groupby("patient_id")
        .tail(1)
    )

    # Latest labs per patient per test
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


# ==============================
# Anomaly Detection
# ==============================

def detect_anomalies(vitals_df: pd.DataFrame):
    logging.info("Detecting anomalies...")

    df = vitals_df.copy()

    df["high_hr"] = df["hr"] > HR_THRESHOLD
    df["low_ox"] = df["ox"] < OX_THRESHOLD
    df["high_bp"] = (df["sys"] > SYS_THRESHOLD) | (df["dia"] > DIA_THRESHOLD)

    anomaly_df = df[
        df[["high_hr", "low_ox", "high_bp"]].any(axis=1)
    ].copy()

    anomaly_df = anomaly_df.melt(
        id_vars=["patient_id", "timestamp"],
        value_vars=["high_hr", "low_ox", "high_bp"],
        var_name="anomaly_type",
        value_name="flag"
    )

    anomaly_df = anomaly_df[anomaly_df["flag"] == True]
    anomaly_df = anomaly_df.drop(columns=["flag"])

    anomaly_df.to_csv(f"{GOLD_DIR}/anomalies.csv", index=False)


# ==============================
# Visualization
# ==============================

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

    # Oxygen Distribution
    plt.figure()
    plt.hist(vitals_df["ox"])
    plt.axvline(OX_THRESHOLD)
    plt.title("Oxygen Level Distribution")
    plt.xlabel("Oxygen")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(f"{VIS_DIR}/oxygen_distribution.png")
    plt.close()

    # Anomaly Counts
    anomaly_df = pd.read_csv(anomalies_path)

    plt.figure()
    anomaly_df["anomaly_type"].value_counts().plot(kind="bar")
    plt.title("Anomaly Counts")
    plt.xlabel("Anomaly Type")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(f"{VIS_DIR}/anomaly_counts.png")
    plt.close()


# ==============================
# Main Execution
# ==============================

def main():
    create_directories()

    ehr_df, vitals_df, labs_df = load_and_store_bronze()

    vitals_clean = clean_vitals(vitals_df)
    labs_clean = clean_labs(labs_df)

    master = create_patient_master(ehr_df, vitals_clean, labs_clean)

    detect_anomalies(vitals_clean)

    generate_visualizations(vitals_clean, f"{GOLD_DIR}/anomalies.csv")

    logging.info("Pipeline execution completed successfully.")


if __name__ == "__main__":
    main()