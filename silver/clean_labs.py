import pandas as pd
import os
import logging

# Setup logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clean_labs(input_path="bronze/labs.csv",
               output_path="silver/clean_labs.csv"):
    """
    Cleans the lab results dataset (CSV format) and saves standardized CSV.
    
    Handles:
    - CSV format reading
    - Numeric field validation (value)
    - Case-insensitive column name standardization
    - Flexible date parsing
    """

    # Step 1: Read CSV file with error handling
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Successfully read file: {input_path}")
        logger.info(f"Initial shape: {df.shape}")
        logger.info(f"Available columns: {list(df.columns)}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Labs file not found at {input_path}")
    except pd.errors.EmptyDataError:
        raise ValueError(f"Labs file is empty: {input_path}")
    except Exception as e:
        raise Exception(f"Error reading labs file: {str(e)}")

    # Step 2: Standardize Column Names (case-insensitive)
    df.columns = df.columns.str.strip().str.lower()
    logger.info(f"Standardized columns: {list(df.columns)}")

    # Step 3: Dynamic Schema Validation
    required_columns = ["patient_id", "test", "value", "timestamp"]
    available_cols = [col for col in required_columns if col in df.columns]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.warning(f"Missing columns: {missing_columns}. Proceeding with: {available_cols}")
    
    if not available_cols:
        raise ValueError(f"No required columns found. Available: {list(df.columns)}")

    # Step 4: Clean patient_id
    if "patient_id" in df.columns:
        initial_count = len(df)
        df["patient_id"] = pd.to_numeric(df["patient_id"], errors="coerce")
        df = df.dropna(subset=["patient_id"])
        df["patient_id"] = df["patient_id"].astype(int)
        removed = initial_count - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} rows with invalid patient_id")

    # Step 5: Clean test field (ensure non-empty string)
    if "test" in df.columns:
        initial_count = len(df)
        df["test"] = df["test"].astype(str).str.strip()
        df = df[df["test"] != ""]
        df = df[df["test"] != "nan"]
        removed = initial_count - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} rows with empty test field")

    # Step 6: Clean lab value (numeric validation)
    if "value" in df.columns:
        initial_count = len(df)
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        
        # Remove rows with NaN values
        df = df.dropna(subset=["value"])
        removed = initial_count - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} rows with invalid lab values")

    # Step 7: Convert timestamp to datetime (flexible parsing)
    if "timestamp" in df.columns:
        initial_count = len(df)
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
            format="mixed"  # Handles multiple date formats
        )
        df = df.dropna(subset=["timestamp"])
        removed = initial_count - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} rows with invalid timestamps")

    # Step 8: Remove Duplicate Lab Results (keep latest per patient per test)
    if "patient_id" in df.columns and "test" in df.columns and "timestamp" in df.columns:
        initial_count = len(df)
        df = df.sort_values("timestamp").drop_duplicates(
            subset=["patient_id", "test"],
            keep="last"
        )
        removed = initial_count - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} duplicate lab records (kept latest per patient/test)")

    # Step 9: Sort by patient_id and timestamp
    if "patient_id" in df.columns and "timestamp" in df.columns:
        df = df.sort_values(["patient_id", "timestamp"]).reset_index(drop=True)

    # Step 10: Select Only Required Columns
    required_output_cols = ["patient_id", "test", "value", "timestamp"]
    available_output_cols = [col for col in required_output_cols if col in df.columns]
    df = df[available_output_cols]
    logger.info(f"Selected output columns: {available_output_cols}")

    # Step 11: Data Quality Report
    logger.info(f"Final shape: {df.shape}")
    logger.info(f"Data quality: {df.notna().sum().to_dict()}")
    logger.info(f"Unique patients: {df['patient_id'].nunique() if 'patient_id' in df.columns else 'N/A'}")
    logger.info(f"Unique tests: {df['test'].nunique() if 'test' in df.columns else 'N/A'}")

    # Step 12: Save Clean File
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Clean labs saved to: {output_path}")

    return df


if __name__ == "__main__":
    clean_labs()