import pandas as pd
import os
import logging

# Setup logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clean_ehr(input_path="bronze/ehr.csv",
              output_path="silver/clean_ehr.csv"):
   

    #Read Raw File with error handling
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Successfully read file: {input_path}")
        logger.info(f"Initial shape: {df.shape}")
    except FileNotFoundError:
        raise FileNotFoundError(f"EHR file not found at {input_path}")
    except pd.errors.EmptyDataError:
        raise ValueError(f"EHR file is empty: {input_path}")
    except Exception as e:
        raise Exception(f"Error reading EHR file: {str(e)}")

    # Step 2: Standardize Column Names (case-insensitive)
    df.columns = df.columns.str.strip().str.lower()
    logger.info(f"Available columns: {list(df.columns)}")

    # Step 3: Dynamic Schema Validation (with warnings for missing columns)
    required_columns = ["patient_id", "name", "age", "gender", "admission_time"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        available = [col for col in df.columns if col in required_columns]
        logger.warning(f"Missing columns: {missing_columns}. Proceeding with: {available}")
        required_columns = available
    
    if not required_columns:
        raise ValueError(f"No required columns found. Available: {list(df.columns)}")

    # Step 4: Clean patient_id (with validation)
    if "patient_id" in df.columns:
        initial_count = len(df)
        df["patient_id"] = pd.to_numeric(df["patient_id"], errors="coerce")
        df = df.dropna(subset=["patient_id"])
        df["patient_id"] = df["patient_id"].astype(int)
        removed = initial_count - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} rows with invalid patient_id")

    # Step 5: Clean age (with realistic bounds)
    if "age" in df.columns:
        initial_count = len(df)
        df["age"] = pd.to_numeric(df["age"], errors="coerce")
        invalid_age_mask = (df["age"] < 0) | (df["age"] > 120)
        df.loc[invalid_age_mask, "age"] = pd.NA
        removed = invalid_age_mask.sum()
        if removed > 0:
            logger.warning(f"Removed {removed} rows with unrealistic age values")
        
        # Fill missing age with median if available
        if df["age"].notna().sum() > 0:
            df["age"] = df["age"].fillna(df["age"].median())
        else:
            logger.warning("No valid age values found")

    # Step 6: Clean gender (flexible mapping)
    if "gender" in df.columns:
        df["gender"] = df["gender"].astype(str).str.strip().str.lower()
        
        # Handle various gender formats
        gender_mapping = {
            "m": "male", "male": "male", "1": "male",
            "f": "female", "female": "female", "2": "female",
            "u": "unknown", "unknown": "unknown", "0": "unknown"
        }
        
        df["gender"] = df["gender"].replace(gender_mapping)
        
        valid_genders = ["male", "female", "unknown"]
        invalid_mask = ~df["gender"].isin(valid_genders)
        df.loc[invalid_mask, "gender"] = "unknown"
        
        if invalid_mask.sum() > 0:
            logger.warning(f"Mapped {invalid_mask.sum()} invalid gender values to 'unknown'")

    # Step 7: Convert admission_time (flexible date parsing)
    if "admission_time" in df.columns:
        initial_count = len(df)
        df["admission_time"] = pd.to_datetime(
            df["admission_time"],
            errors="coerce",
            format="mixed"  # Handles multiple date formats
        )
        df = df.dropna(subset=["admission_time"])
        removed = initial_count - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} rows with invalid timestamps")

    # Step 8: Remove Duplicate Patients (keep latest)
    if "patient_id" in df.columns:
        initial_count = len(df)
        df = df.drop_duplicates(subset="patient_id", keep="last")
        removed = initial_count - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} duplicate patient records")

    # Step 9: Sort by admission_time (if available)
    if "admission_time" in df.columns:
        df = df.sort_values("admission_time").reset_index(drop=True)

    # Step 10: Data Quality Report
    logger.info(f"Final shape: {df.shape}")
    logger.info(f"Data quality: {df.notna().sum().to_dict()}")

    # Step 11: Save Clean File
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Clean EHR saved to: {output_path}")

    return df


if __name__ == "__main__":
    clean_ehr()