import pandas as pd
import os
import logging
from datetime import datetime

#logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clean_vitals(input_path="bronze/vitals.csv",
                 output_path="silver/clean_vitals.csv"):
    

    #Read CSV file
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

    #Standardize Column Names
    df.columns = df.columns.str.strip().str.lower()

    #Dynamic Schema Validation
    required_columns = ["patientid", "timestamp", "hr", "ox", "sys", "dia"]
    available_cols = [col for col in required_columns if col in df.columns]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.warning(f"Missing columns: {missing_columns}. Proceeding with: {available_cols}")
    
    if not available_cols:
        raise ValueError(f"No required columns found. Available: {list(df.columns)}")

    #Rename patientId → patient_id
    if "patientid" in df.columns:
        df = df.rename(columns={"patientid": "patient_id"})
    elif "patient_id" not in df.columns:
        logger.warning("Neither patientId nor patient_id found")

    #Clean patient_id
    if "patient_id" in df.columns:
        initial_count = len(df)
        df["patient_id"] = pd.to_numeric(df["patient_id"], errors="coerce")
        df = df.dropna(subset=["patient_id"])
        df["patient_id"] = df["patient_id"].astype(int)
        removed = initial_count - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} rows with invalid patient_id")

    #Timestamp to datetime
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

    #Clean Heart Rate
    if "hr" in df.columns:
        initial_count = len(df)
        df["hr"] = pd.to_numeric(df["hr"], errors="coerce")
        invalid_hr_mask = (df["hr"] < 30) | (df["hr"] > 200)
        df.loc[invalid_hr_mask, "hr"] = pd.NA
        removed = invalid_hr_mask.sum()
        if removed > 0:
            logger.warning(f"Flagged {removed} rows with unrealistic HR values")
        df = df.dropna(subset=["hr"])

    #Clean Oxygen Level
    if "ox" in df.columns:
        initial_count = len(df)
        df["ox"] = pd.to_numeric(df["ox"], errors="coerce")
        invalid_ox_mask = (df["ox"] < 0) | (df["ox"] > 100)
        df.loc[invalid_ox_mask, "ox"] = pd.NA
        removed = invalid_ox_mask.sum()
        if removed > 0:
            logger.warning(f"Flagged {removed} rows with invalid O2 values")
        df = df.dropna(subset=["ox"])

    #Clean Systolic Blood Pressure
    if "sys" in df.columns:
        initial_count = len(df)
        df["sys"] = pd.to_numeric(df["sys"], errors="coerce")
        invalid_sys_mask = (df["sys"] < 50) | (df["sys"] > 250)
        df.loc[invalid_sys_mask, "sys"] = pd.NA
        removed = invalid_sys_mask.sum()
        if removed > 0:
            logger.warning(f"Flagged {removed} rows with invalid systolic BP values")
        df = df.dropna(subset=["sys"])

    #Clean Diastolic Blood Pressure
    if "dia" in df.columns:
        initial_count = len(df)
        df["dia"] = pd.to_numeric(df["dia"], errors="coerce")
        invalid_dia_mask = (df["dia"] < 30) | (df["dia"] > 150)
        df.loc[invalid_dia_mask, "dia"] = pd.NA
        removed = invalid_dia_mask.sum()
        if removed > 0:
            logger.warning(f"Flagged {removed} rows with invalid diastolic BP values")
        df = df.dropna(subset=["dia"])

    #Sort by patient_id and timestamp
    if "patient_id" in df.columns and "timestamp" in df.columns:
        df = df.sort_values(["patient_id", "timestamp"]).reset_index(drop=True)

    # Select Only Required Columns (drop any extra columns like datetime)
    required_output_cols = ["patient_id", "timestamp", "hr", "ox", "sys", "dia"]
    available_output_cols = [col for col in required_output_cols if col in df.columns]
    df = df[available_output_cols]
    logger.info(f"Selected output columns: {available_output_cols}")

    #Data Quality Report
    logger.info(f"Final shape: {df.shape}")
    logger.info(f"Data quality: {df.notna().sum().to_dict()}")

    #Save Clean File
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Clean vitals saved to: {output_path}")

    return df


if __name__ == "__main__":
    clean_vitals()
