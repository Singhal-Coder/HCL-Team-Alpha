# Silver Layer - Data Cleaning & Standardization

## Overview

The Silver Layer is responsible for cleaning and standardizing raw data from the Bronze Layer. All transformations are applied while maintaining data integrity and logging changes for transparency.

---

## Data Cleaning Approach

### 1. EHR (Electronic Health Records) - `clean_ehr.py`

**Input:** `bronze/ehr.csv`  
**Output:** `silver/clean_ehr.csv`

#### Cleaning Steps:

| Step | Field | Approach | Rules |
|------|-------|----------|-------|
| 1 | **Column Names** | Standardize to lowercase & strip whitespace | patient_id, name, age, gender, admission_time |
| 2 | **patient_id** | Convert to numeric, remove invalid entries | Must be positive integer |
| 3 | **age** | Convert to numeric, validate range | Valid: 0-120 years; Fill NaN with median |
| 4 | **gender** | Normalize format & map variations | m→male, f→female, u/other→unknown |
| 5 | **admission_time** | Parse flexible datetime formats | Handle mixed formats (ISO, US, etc.) |
| 6 | **Duplicates** | Remove duplicates by patient_id | Keep latest record |
| 7 | **Sort & Index** | Sort by admission_time | Reset index for clean row numbering |

#### Data Quality Rules:
- ✓ Dynamic column validation (handles missing columns gracefully)
- ✓ Case-insensitive column matching
- ✓ Flexible date parsing for multiple timestamp formats
- ✓ Logs row removal/transformation counts
- ✓ Handles empty files and read errors

#### Example Transformations:
```
Input:  age="-5"          → Output: NaN (flagged as invalid)
Input:  gender="MALE"     → Output: "male"
Input:  age=NaN           → Output: median_age (imputed)
Input:  admission_time="01/15/2024" → Output: 2024-01-15 (standardized)
```

---

### 2. Vitals (Streaming Health Metrics) - `clean_vitals.py`

**Input:** `bronze/vitals.jsonl` (JSON Lines format)  
**Output:** `silver/clean_vitals.csv`

#### Cleaning Steps:

| Step | Field | Approach | Validation Rules |
|------|-------|----------|------------------|
| 1 | **Format** | Parse JSONL (1 JSON object per line) | Skip malformed JSON |
| 2 | **Column Names** | Standardize lowercase, rename patientId → patient_id | Dynamic discovery |
| 3 | **patient_id** | Convert to numeric integer | Remove rows with invalid IDs |
| 4 | **timestamp** | Convert UNIX timestamp to datetime | Handle seconds & milliseconds |
| 5 | **Heart Rate (hr)** | Convert to numeric, validate range | Valid: 30-200 bpm |
| 6 | **Oxygen Level (ox)** | Convert to numeric, validate range | Valid: 0-100% |
| 7 | **Systolic BP (sys)** | Convert to numeric, validate range | Valid: 50-250 mmHg |
| 8 | **Diastolic BP (dia)** | Convert to numeric, validate range | Valid: 30-150 mmHg |
| 9 | **Sort & Index** | Sort by patient_id, then timestamp | Reset index for clean row numbering |

#### Data Quality Rules:
- ✓ JSONL parsing with error tolerance (skips invalid lines)
- ✓ UNIX timestamp detection (auto-detects seconds vs milliseconds)
- ✓ Numeric field validation with realistic physiological bounds
- ✓ Removes rows with missing critical fields
- ✓ Logs all data quality issues

#### Example Transformations:
```
Input:  timestamp=1730001290 (UNIX) → Output: 2024-10-27 03:48:10
Input:  hr="118"                    → Output: 118 (numeric)
Input:  ox=91                       → Output: 91 (valid)
Input:  hr="999"                    → Output: NaN (removed - unrealistic)
Input:  patientId=101               → Output: patient_id=101 (renamed)
```

---

## Handling Data File Changes

Both scripts are designed to handle variations in input data:

### Flexibility Features:
1. **Dynamic Column Detection** — Discovers available columns instead of assuming structure
2. **Case-Insensitive** — All column names converted to lowercase
3. **Missing Column Handling** — Proceeds with available columns, logs warnings
4. **Flexible Date Parsing** — Handles multiple timestamp formats
5. **Numeric Coercion** — Attempts conversion; flags invalid values
6. **Error Tolerance** — JSONL parsing skips individual bad lines instead of failing entire file

### Robustness:
- File not found errors are caught with clear messages
- Empty files are detected and reported
- Each transformation logs row counts before/after
- Data quality report shows missing value counts per column
- Logging levels (INFO/WARNING) indicate operation status

---

## Output CSV Structure

### `clean_ehr.csv`
```
patient_id | name      | age | gender | admission_time
101        | John Doe  | 45  | male   | 2024-01-10 10:00:00
102        | Alice Roy | 31  | female | 2024-01-11 09:30:00
```

### `clean_vitals.csv`
```
patient_id | timestamp           | hr  | ox  | sys | dia
101        | 2024-01-10 10:15:00 | 118 | 91  | 150 | 98
102        | 2024-01-10 10:16:00 | 80  | 97  | 120 | 82
```

---

## Usage

Run individual scripts:
```bash
python silver/clean_ehr.py          # Cleans EHR data
python silver/clean_vitals.py       # Cleans vitals data
```

Or import as functions:
```python
from clean_ehr import clean_ehr
from clean_vitals import clean_vitals

ehr_df = clean_ehr()
vitals_df = clean_vitals()
```

---

## Logging Output

Both scripts log transformation details:
```
2024-01-15 10:30:45,123 - INFO - Successfully read file: bronze/ehr.csv
2024-01-15 10:30:45,234 - INFO - Initial shape: (300, 5)
2024-01-15 10:30:45,345 - WARNING - Removed 5 rows with invalid patient_id
2024-01-15 10:30:45,456 - WARNING - Removed 2 row with unrealistic age values
2024-01-15 10:30:45,567 - INFO - Final shape: (293, 5)
2024-01-15 10:30:45,678 - INFO - Clean EHR saved to: silver/clean_ehr.csv
```

---

## Data Quality Summary

| Metric | Value |
|--------|-------|
| **Records Processed** | Logged per script |
| **Invalid Records Removed** | Tracked by field |
| **Data Imputation** | Age: median fill |
| **Duplicate Handling** | Keep latest |
| **Timestamp Coverage** | 100% valid datetimes |

---

## Next Steps

After Silver Layer cleaning:
1. **Combine datasets** → `patient_master.py` (Join EHR + Vitals + Labs)
2. **Detect anomalies** → `anomaly_detection.py`
3. **Visualize trends** → `visualizations.py`
