import pandas as pd
import os
import logging
from datetime import datetime

# Setup logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clean_vitals(input_path="bronze/vitals.csv",
                 output_path="silver/clean_vitals.csv"):
    """
    Cleans the vitals dataset (CSV format) and saves standardized CSV.
    
    Handles:
    - CSV format reading
    - UNIX timestamp conversion to datetime
    - Numeric field validation (hr, ox, sys, dia)
    - Case-insensitive column name standardization
    - Flexible data handling
    """

    # Step 1: Read CSV file with error handling
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Successfully read file: {input_path}")
        logger.info(f"Initial shape: {df.shape}")
        logger.info(f"Available columns: {list(df.columns)}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Vitals file not found at {input_path}")
    except pd.errors.EmptyDataError:
        raise ValueError(f"Vitals file is empty: {input_path}")
    except Exception as e:
        raise Exception(f"Error reading vitals file: {str(e)}")

    # Step 2: Standardize Column Names (case-insensitive)
    df.columns = df.columns.str.strip().str.lower()

    # Step 3: Dynamic Schema Validation
    required_columns = ["patientid", "timestamp", "hr", "ox", "sys", "dia"]
    available_cols = [col for col in required_columns if col in df.columns]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.warning(f"Missing columns: {missing_columns}. Proceeding with: {available_cols}")
    
    if not available_cols:
        raise ValueError(f"No required columns found. Available: {list(df.columns)}")

    # Step 4: Rename patientId → patient_id (handle both cases)
    if "patientid" in df.columns:
        df = df.rename(columns={"patientid": "patient_id"})
    elif "patient_id" not in df.columns:
        logger.warning("Neither patientId nor patient_id found")

    # Step 5: Clean patient_id
    if "patient_id" in df.columns:
        initial_count = len(df)
        df["patient_id"] = pd.to_numeric(df["patient_id"], errors="coerce")
        df = df.dropna(subset=["patient_id"])
        df["patient_id"] = df["patient_id"].astype(int)
        removed = initial_count - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} rows with invalid patient_id")

    # Step 6: Convert UNIX timestamp to datetime
    if "timestamp" in df.columns:
        initial_count = len(df)
        
        def parse_timestamp(ts):
            try:
                if pd.isna(ts):
                    return pd.NaT
                
                # Handle UNIX timestamps (seconds or milliseconds)
                ts_num = pd.to_numeric(ts, errors='coerce')
                if pd.isna(ts_num):
                    # Try parsing as string
                    return pd.to_datetime(ts, errors='coerce')
                
                # UNIX timestamp in seconds (typical range: 1970-2100)
                if ts_num > 1e10:  # Likely milliseconds
                    return pd.to_datetime(ts_num, unit='ms')
                else:  # Likely seconds
                    return pd.to_datetime(ts_num, unit='s')
            except:
                return pd.NaT
        
        df["timestamp"] = df["timestamp"].apply(parse_timestamp)
        df = df.dropna(subset=["timestamp"])
        removed = initial_count - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} rows with invalid timestamps")

    # Step 7: Clean Heart Rate (hr)
    if "hr" in df.columns:
        initial_count = len(df)
        df["hr"] = pd.to_numeric(df["hr"], errors="coerce")
        invalid_hr_mask = (df["hr"] < 30) | (df["hr"] > 200)
        df.loc[invalid_hr_mask, "hr"] = pd.NA
        removed = invalid_hr_mask.sum()
        if removed > 0:
            logger.warning(f"Flagged {removed} rows with unrealistic HR values")
        df = df.dropna(subset=["hr"])

    # Step 8: Clean Oxygen Level (ox)
    if "ox" in df.columns:
        initial_count = len(df)
        df["ox"] = pd.to_numeric(df["ox"], errors="coerce")
        invalid_ox_mask = (df["ox"] < 0) | (df["ox"] > 100)
        df.loc[invalid_ox_mask, "ox"] = pd.NA
        removed = invalid_ox_mask.sum()
        if removed > 0:
            logger.warning(f"Flagged {removed} rows with invalid O2 values")
        df = df.dropna(subset=["ox"])

    # Step 9: Clean Systolic Blood Pressure (sys)
    if "sys" in df.columns:
        initial_count = len(df)
        df["sys"] = pd.to_numeric(df["sys"], errors="coerce")
        invalid_sys_mask = (df["sys"] < 50) | (df["sys"] > 250)
        df.loc[invalid_sys_mask, "sys"] = pd.NA
        removed = invalid_sys_mask.sum()
        if removed > 0:
            logger.warning(f"Flagged {removed} rows with invalid systolic BP values")
        df = df.dropna(subset=["sys"])

    # Step 10: Clean Diastolic Blood Pressure (dia)
    if "dia" in df.columns:
        initial_count = len(df)
        df["dia"] = pd.to_numeric(df["dia"], errors="coerce")
        invalid_dia_mask = (df["dia"] < 30) | (df["dia"] > 150)
        df.loc[invalid_dia_mask, "dia"] = pd.NA
        removed = invalid_dia_mask.sum()
        if removed > 0:
            logger.warning(f"Flagged {removed} rows with invalid diastolic BP values")
        df = df.dropna(subset=["dia"])

    # Step 11: Sort by patient_id and timestamp
    if "patient_id" in df.columns and "timestamp" in df.columns:
        df = df.sort_values(["patient_id", "timestamp"]).reset_index(drop=True)

    # Step 12: Select Only Required Columns (drop any extra columns like datetime)
    required_output_cols = ["patient_id", "timestamp", "hr", "ox", "sys", "dia"]
    available_output_cols = [col for col in required_output_cols if col in df.columns]
    df = df[available_output_cols]
    logger.info(f"Selected output columns: {available_output_cols}")

    # Step 13: Data Quality Report
    logger.info(f"Final shape: {df.shape}")
    logger.info(f"Data quality: {df.notna().sum().to_dict()}")

    # Step 14: Save Clean File
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Clean vitals saved to: {output_path}")

    return df


if __name__ == "__main__":
    clean_vitals()
