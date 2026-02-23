# Silver Layer — Data Cleaning & Patient Master

## Overview

The Silver Layer cleans raw Bronze data and produces a combined **Patient Master Table**. All scripts are re-runnable — just execute them again when data is refreshed.

---

## Scripts

### 1. `clean_ehr.py` — EHR Cleaning

**Input:** `bronze/ehr.csv` → **Output:** `silver/clean_ehr.csv`

| Step | Field          | Rule                              |
| ---- | -------------- | --------------------------------- |
| 1    | Column names   | Lowercase, strip whitespace       |
| 2    | patient_id     | Must be positive integer          |
| 3    | age            | Range 0–120; NaN → median         |
| 4    | gender         | Normalize (m→male, f→female)      |
| 5    | admission_time | Parse flexible datetime formats   |
| 6    | Duplicates     | Remove by patient_id, keep latest |

---

### 2. `clean_labs.py` — Lab Results Cleaning

**Input:** `bronze/labs.csv` → **Output:** `silver/clean_labs.csv`

| Step | Field        | Rule                     |
| ---- | ------------ | ------------------------ |
| 1    | Column names | Standardize to lowercase |
| 2    | patient_id   | Must be valid integer    |
| 3    | test         | Standardize test names   |
| 4    | value        | Convert to numeric       |
| 5    | timestamp    | Parse to datetime        |

**Tests tracked:** Hemoglobin, AST, ALT, Creatinine

---

### 3. `clean_vitals.py` — Vitals Cleaning

**Input:** `bronze/vitals.csv` → **Output:** `silver/clean_vitals.csv`

| Step | Field              | Valid Range        |
| ---- | ------------------ | ------------------ |
| 1    | hr (Heart Rate)    | 30–200 bpm         |
| 2    | ox (Oxygen)        | 0–100%             |
| 3    | sys (Systolic BP)  | 50–250 mmHg        |
| 4    | dia (Diastolic BP) | 30–150 mmHg        |
| 5    | timestamp          | Parsed to datetime |

---

### 4. `build_patient_master.py` — Combined Patient Master

**Input:** `clean_ehr.csv` + `clean_vitals.csv` + `clean_labs.csv`  
**Output:** `silver/patient_master.csv`

Joins all three datasets into **one row per patient** with:

- EHR demographics (name, age, gender, admission_time)
- **Latest vitals** (most recent hr, ox, sys, dia)
- **Latest lab values** (pivoted: latest_hemoglobin, latest_ast, latest_alt, latest_creatinine)

**Columns (14):**

```
patient_id, name, age, gender, admission_time,
vitals_timestamp, latest_hr, latest_ox, latest_sys, latest_dia,
latest_alt, latest_ast, latest_creatinine, latest_hemoglobin
```

---

## Output Summary

| File                 | Records | Description                  |
| -------------------- | ------- | ---------------------------- |
| `clean_ehr.csv`      | 300     | Cleaned patient demographics |
| `clean_labs.csv`     | 900     | Cleaned lab test results     |
| `clean_vitals.csv`   | 1,500   | Cleaned vital signs          |
| `patient_master.csv` | 300     | Combined master table        |

---

## Usage

```bash
# Clean individual datasets
python silver/clean_ehr.py
python silver/clean_labs.py
python silver/clean_vitals.py

# Build combined patient master
python silver/build_patient_master.py
```

Re-run any script to refresh outputs from latest bronze data.
