# Hospital Health Monitoring Mini-Pipeline

A modular, production-style data pipeline for hospital health monitoring. It ingests EHR, vitals, and lab data from multiple sources, cleans and standardizes them using a **Bronze → Silver → Gold** medallion architecture, detects rule-based anomalies, and generates publication-ready visualizations.

**Built for the HCL Hackathon — Team Alpha**

## Overview

| Aspect | Description |
|--------|-------------|
| **Goal** | Read hospital data → clean & combine → detect anomalies → visualize trends |
| **Tools** | Python, pandas, matplotlib, seaborn, json |
| **Design** | Single entry point (`main.py`) orchestrating stage-specific scripts |
| **Output** | Clean CSVs in `silver/`, anomalies in `gold/`, charts in `visualizations/` |

---

## Prerequisites & Installation

- **Python:** 3.8+
- **Dependencies:** See `requirements.txt`

```bash
# From project root
pip install -r requirements.txt
```

| Package | Purpose |
|---------|---------|
| `pandas` | Data loading, cleaning, merging |
| `matplotlib` | Plotting |
| `seaborn` | Styled visualizations |
| `openpyxl` | Excel support (optional, for bronze) |
| `python-docx` | Document support (optional) |

---

## Project Structure

```
HCL-Team-Alpha/
├── main.py                    # Entry point — runs full pipeline in order
├── requirements.txt           # Python dependencies
├── README.md                  # This file
│
├── INPUT_DATA/                # Source data (place files here)
│   ├── ehr.csv                # Electronic Health Records
│   ├── vitals.json            # Streaming vitals (JSON array)
│   └── labs.json              # Lab results (JSON array)
│
├── bronze/                    # Raw layer — CSV copies of input
│   ├── file_conversion.py     # Converts INPUT_DATA → bronze/*.csv
│   ├── ehr.csv
│   ├── vitals.csv
│   └── labs.csv
│
├── silver/                    # Cleaned & joined data
│   ├── clean_ehr.py           # Clean EHR → clean_ehr.csv
│   ├── clean_vitals.py        # Clean vitals → clean_vitals.csv
│   ├── clean_labs.py          # Clean labs → clean_labs.csv
│   ├── build_patient_master.py # Join → patient_master.csv
│   ├── clean_ehr.csv
│   ├── clean_vitals.csv
│   ├── clean_labs.csv
│   └── patient_master.csv
│
├── gold/                      # Analytics layer
│   ├── detect_anomalies.py     # Rule-based anomalies → anomalies.csv
│   └── anomalies.csv
│
└── visualizations/            # Generated charts
    ├── generate_plots.py      # Creates all plots
    ├── hr_trend.png           # Combined HR trend (timestamp vs HR)
    ├── oxygen_distribution.png
    ├── anomaly_counts.png
    └── per_patient_hr/        # One HR trend plot per patient
        └── hr_patient_*.png
```

---

## How to Run

**Full pipeline (recommended):**

```bash
python main.py
```

This runs, in order:

1. Bronze: file conversion  
2. Silver: clean EHR, vitals, labs → build patient master  
3. Gold: detect anomalies  
4. Visualizations: generate all plots  

**Run individual stages** (e.g. for debugging):

```bash
python bronze/file_conversion.py
python silver/clean_ehr.py
python silver/clean_vitals.py
python silver/clean_labs.py
python silver/build_patient_master.py
python gold/detect_anomalies.py
python visualizations/generate_plots.py
```

Ensure `INPUT_DATA/` contains `ehr.csv`, `vitals.json`, and `labs.json` before running.

---

## Pipeline Stages

### 1. Bronze — Raw Storage

| Script | Action |
|--------|--------|
| `bronze/file_conversion.py` | Reads `INPUT_DATA/ehr.csv`, `vitals.json`, `labs.json`; writes `bronze/ehr.csv`, `bronze/vitals.csv`, `bronze/labs.csv`. No transformations — format conversion only (JSON → CSV where needed). |

### 2. Silver — Cleaning & Standardization

| Script | Input | Output | Summary |
|--------|--------|--------|---------|
| `silver/clean_ehr.py` | `bronze/ehr.csv` | `silver/clean_ehr.csv` | Standardize columns, validate patient_id/age/gender/admission_time, drop duplicates. |
| `silver/clean_vitals.py` | `bronze/vitals.csv` | `silver/clean_vitals.csv` | Rename `patientId`→`patient_id`, parse timestamps (Unix/ISO), coerce hr/ox/sys/dia to numeric, drop invalid rows. |
| `silver/clean_labs.py` | `bronze/labs.csv` | `silver/clean_labs.csv` | Validate patient_id, test, value, timestamp; coerce types; keep latest per patient per test; output standard columns. |
| `silver/build_patient_master.py` | `clean_ehr`, `clean_vitals`, `clean_labs` | `silver/patient_master.csv` | Join all three on `patient_id` (inner). Timestamp columns renamed to `vitals_timestamp`, `labs_timestamp` to avoid clashes. |

### 3. Gold — Anomaly Detection

| Script | Input | Output |
|--------|--------|--------|
| `gold/detect_anomalies.py` | `silver/patient_master.csv` | `gold/anomalies.csv` |

### 4. Visualizations

| Script | Inputs | Outputs |
|--------|--------|--------|
| `visualizations/generate_plots.py` | `silver/clean_vitals.csv`, `gold/anomalies.csv` | `hr_trend.png`, `per_patient_hr/*.png`, `oxygen_distribution.png`, `anomaly_counts.png` |

---

## Data Cleaning

### EHR (`clean_ehr.py`)

- **Column names:** Lowercased and stripped.
- **patient_id:** Coerced to numeric; invalid/NaN dropped; cast to int.
- **age:** Coerced to numeric; values &lt; 0 or &gt; 120 set to NA; missing filled with median when available.
- **gender:** Standardized to `male` / `female` / `unknown` (handles M/F, 1/2, etc.).
- **admission_time:** Parsed with `pd.to_datetime(..., format="mixed")`; invalid rows dropped.
- **Duplicates:** One row per `patient_id`, keep last; sorted by `admission_time`.

### Vitals (`clean_vitals.py`)

- **Columns:** `patientId` → `patient_id`; timestamps and numeric fields validated.
- **Timestamp:** Supports Unix (seconds/ms) and ISO strings via a small parser.
- **Numeric:** `hr`, `ox`, `sys`, `dia` coerced to numeric; invalid rows dropped.
- **Sanity:** Optional filters (e.g. hr &gt; 0, ox ≤ 100) to drop impossible values.
- **Output columns:** `patient_id`, `timestamp`, `hr`, `ox`, `sys`, `dia`.

### Labs (`clean_labs.py`)

- **Columns:** Lowercased; required: `patient_id`, `test`, `value`, `timestamp`.
- **patient_id:** Coerced to numeric; invalid dropped; int.
- **test:** Non-empty string; empty/NaN dropped.
- **value:** Coerced to numeric; NaN dropped.
- **timestamp:** `pd.to_datetime(..., format="mixed")`; invalid dropped.
- **Deduplication:** Latest per `(patient_id, test)` kept; sorted by `patient_id`, `timestamp`.
- **Output columns:** `patient_id`, `test`, `value`, `timestamp`.

---

## Joins & Patient Master

**Strategy:** Inner join on `patient_id`.

1. **clean_ehr** — base table (one row per patient after dedup).
2. **clean_vitals** — timestamp column renamed to `vitals_timestamp`; joined on `patient_id`.
3. **clean_labs** — timestamp renamed to `labs_timestamp`; joined on `patient_id`.

Result: `silver/patient_master.csv` with demographics, vitals, and lab columns; one row per combination of patient × vital × lab (or one row per patient if vitals/labs were already aggregated to one row per patient). Used as the single source for **gold** anomaly detection.

---

## Anomaly Detection

**Source:** Each row of `silver/patient_master.csv` (vitals columns: `hr`, `ox`, `sys`, `dia`).

**Rules:**

| Anomaly | Condition | Output `value` |
|---------|-----------|----------------|
| **High Heart Rate** | `hr > 120` | HR value |
| **Low Oxygen** | `ox < 92` | OX value |
| **High Blood Pressure** | `sys > 160` OR `dia > 100` | `"sys/dia"` (e.g. `"165/98"`) |

**Output:** `gold/anomalies.csv` with columns:

- `patient_id`, `timestamp` (vitals_timestamp), `anomaly`, `value`

One row per triggered rule per master row (a patient can appear multiple times if multiple rules fire or multiple master rows exist).

---

## Visualizations

All generated under `visualizations/` by `visualizations/generate_plots.py`.

| Figure | Description |
|--------|-------------|
| **hr_trend.png** | Multi-line plot: timestamp (x) vs Heart Rate (y). All patients as faint lines; 5 sample patients highlighted with legend. Red dashed line at 120 bpm (anomaly threshold). |
| **per_patient_hr/hr_patient_&lt;id&gt;.png** | One line chart per patient: timestamp vs HR, with 120 bpm threshold. |
| **oxygen_distribution.png** | Histogram of oxygen levels with normal (≥ 92%) and low (&lt; 92%) highlighted; box plot below; threshold line at 92%. |
| **anomaly_counts.png** | Bar chart: anomaly type (x) vs number of occurrences (y), with counts labeled on bars. |

---

## Input Data

Place these in `INPUT_DATA/`:

| File | Format | Expected fields |
|------|--------|------------------|
| **ehr.csv** | CSV | `patient_id`, `name`, `age`, `gender`, `admission_time` |
| **vitals.json** | JSON array | `patientId`, `timestamp` (Unix or ISO), `hr`, `ox`, `sys`, `dia` |
| **labs.json** | JSON array | `patient_id`, `test`, `value`, `timestamp` |

- **ehr.csv:** One row per patient (e.g. 300 rows).
- **vitals:** Multiple readings per patient (e.g. 5 per patient); timestamps often Unix.
- **labs:** Multiple tests per patient (e.g. 3); timestamps often ISO strings.
- Data may contain natural variation and mild anomalies for detection.

---

## Architecture

```
┌──────────────────┐
│   INPUT_DATA/    │  ehr.csv, vitals.json, labs.json
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│      BRONZE      │────▶│      SILVER     │────▶│       GOLD       │
│  (raw CSV copy)  │     │ (cleaned + join) │     │   (anomalies)    │
│                  │     │                  │     │                  │
│ file_conversion  │     │ clean_ehr        │     │ detect_anomalies │
│ → ehr, vitals,  │     │ clean_vitals     │     │ → anomalies.csv  │
│   labs.csv      │     │ clean_labs       │     └────────┬─────────┘
└──────────────────┘     │ patient_master  │              │
                         └────────┬────────┘              │
                                  │                       ▼
                                  │              ┌──────────────────┐
                                  └─────────────▶│  VISUALIZATIONS   │
                                                 │  hr_trend, oxygen, │
                                                 │  anomaly_counts,   │
                                                 │  per_patient_hr/   │
                                                 └───────────────────┘
```

- **Bronze:** Immutable raw copy; format normalization only.  
- **Silver:** Cleaned, validated, and joined for analytics.  
- **Gold:** Rule-based anomaly table.  
- **Visualizations:** Charts for reporting and judging.

---

## Judging Criteria

| Category | Weight | Coverage in this project |
|----------|--------|---------------------------|
| Data Cleaning & Transformations | 30% | Bronze file conversion; Silver clean_ehr, clean_vitals, clean_labs |
| Pipeline Logic & Joins | 25% | build_patient_master (EHR + vitals + labs on patient_id) |
| Visualizations | 20% | HR trend, oxygen distribution, anomaly counts, per-patient HR |
| Anomaly Detection | 15% | Rule-based (HR, OX, BP) → gold/anomalies.csv |
| Code Quality & README | 10% | Modular scripts, logging, this README |

---


