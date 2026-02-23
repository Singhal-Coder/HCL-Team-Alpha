# 🏥 Hospital Health Monitoring Mini-Pipeline

A Python-based data processing pipeline that reads hospital data from multiple sources, cleans and combines it, detects anomalies in patient vitals, and visualizes key health trends — built using a **Bronze → Silver → Gold** lakehouse architecture.

---

## 📁 Project Structure

```
project/
├── bronze/                  # Raw, unprocessed data (Task 1)
│   ├── vitals.csv
│   ├── ehr.csv
│   └── labs.csv
├── silver/                  # Cleaned & standardized data (Tasks 2–3)
│   ├── clean_vitals.csv
│   ├── clean_labs.csv
│   └── patient_master.csv
├── gold/                    # Analytical outputs (Task 4)
│   └── anomalies.csv
├── visualizations/          # Charts & graphs (Task 5)
│   ├── hr_trend.png
│   ├── oxygen_distribution.png
│   └── anomaly_counts.png
├── main.py                  # Entry point — runs the full pipeline
└── README.md                # This file
```

---

## 🔧 Tools & Dependencies

| Library      | Purpose                              |
| ------------ | ------------------------------------ |
| `pandas`     | Data loading, cleaning, and merging  |
| `numpy`      | Numeric operations and type coercion |
| `matplotlib` | Plotting and chart generation        |
| `seaborn`    | Statistical visualizations           |
| `json`       | Parsing JSON and JSONL input files   |

### Installation

```bash
pip install pandas numpy matplotlib seaborn
```

---

## 🚀 How to Run

```bash
python main.py
```

This single command executes the entire pipeline end-to-end, from raw ingestion to visualization output.

---

## 📝 Pipeline Tasks — Detailed Breakdown

---

### Task 1 — Bronze Layer (Raw Storage)

**Goal:** Ingest all three source files and store them as-is in `bronze/`.

| Source File    | Format     | Records | Description                               |
| -------------- | ---------- | ------- | ----------------------------------------- |
| `vitals.jsonl` | JSON Lines | 1,500   | Streaming vitals (5 readings per patient) |
| `ehr.csv`      | CSV        | 300     | Electronic Health Records master file     |
| `labs.json`    | JSON List  | 900     | Lab test results (3 tests per patient)    |

**Process:**

- **vitals.jsonl** → Read line-by-line, parse each JSON object, and write to `bronze/vitals.csv` without modification.
- **ehr.csv** → Read directly with `pandas.read_csv()` and write to `bronze/ehr.csv` as-is.
- **labs.json** → Parse the JSON list with `json.load()` and write to `bronze/labs.csv` row-by-row.

> **No transformations, cleaning, or corrections are applied at this layer.** The bronze layer preserves the raw data exactly as received for auditability and reproducibility.

---

### Task 2 — Silver Layer (Cleaning & Standardization)

**Goal:** Clean and standardize bronze data to produce analysis-ready datasets.

#### Cleaning `vitals.csv` → `silver/clean_vitals.csv`

| Step | Transformation        | Details                                                                 |
| ---- | --------------------- | ----------------------------------------------------------------------- |
| 1    | Rename columns        | `patientId` → `patient_id`                                              |
| 2    | Convert timestamps    | UNIX epoch (`1730001290`) → `datetime` (`pd.to_datetime(ts, unit='s')`) |
| 3    | Coerce numeric fields | `hr`, `ox`, `sys`, `dia` cast via `pd.to_numeric(errors='coerce')`      |
| 4    | Drop invalid rows     | Remove rows where any critical vital is `NaN` after coercion            |

**Output columns:** `patient_id`, `timestamp`, `hr`, `ox`, `sys`, `dia`

#### Cleaning `labs.csv` → `silver/clean_labs.csv`

| Step | Transformation        | Details                                                                |
| ---- | --------------------- | ---------------------------------------------------------------------- |
| 1    | Rename columns        | `patientId` → `patient_id`, `test` → `lab_test`, `value` → `lab_value` |
| 2    | Convert timestamps    | String datetime → `pd.to_datetime()`                                   |
| 3    | Coerce numeric fields | `lab_value` cast via `pd.to_numeric(errors='coerce')`                  |
| 4    | Drop invalid rows     | Remove rows where `lab_value` is `NaN` after coercion                  |

**Output columns:** `patient_id`, `timestamp`, `lab_test`, `lab_value`

---

### Task 3 — Combined Patient Master Table

**Goal:** Create a unified patient view by joining EHR data with the **latest** vitals and **latest** lab results for each patient.

#### Join Strategy

```
patient_master = EHR ← LEFT JOIN → Latest Vitals ← LEFT JOIN → Latest Labs (pivoted)
```

| Step | Operation                 | Details                                                                                                                                                    |
| ---- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | **Latest Vitals**         | Sort `clean_vitals` by `timestamp` descending, then `groupby('patient_id').first()` to get the most recent reading per patient                             |
| 2    | **Latest Labs (Pivoted)** | Sort `clean_labs` by `timestamp` descending, `groupby(['patient_id', 'lab_test']).first()`, then `pivot` on `lab_test` so each test becomes its own column |
| 3    | **Merge**                 | Left join EHR → Latest Vitals on `patient_id`, then left join → Pivoted Labs on `patient_id`                                                               |

**Output:** `silver/patient_master.csv`

This table provides a single-row-per-patient snapshot containing demographics, most recent vitals, and latest lab values — ideal for dashboards and downstream analytics.

---

### Task 4 — Anomaly Detection (Rule-Based)

**Goal:** Flag patients exhibiting abnormal vital signs using clinically-inspired thresholds.

#### Detection Rules

| Anomaly                 | Condition                       | Clinical Significance                  |
| ----------------------- | ------------------------------- | -------------------------------------- |
| **High Heart Rate**     | `hr > 120` bpm                  | Tachycardia — potential cardiac stress |
| **Low Oxygen**          | `ox < 92` %                     | Hypoxemia — respiratory concern        |
| **High Blood Pressure** | `sys > 160` OR `dia > 100` mmHg | Hypertensive crisis risk               |

#### Process

1. Iterate over every row in `silver/clean_vitals.csv`
2. Apply each rule independently (a single reading can trigger **multiple** anomalies)
3. Collect all flagged records into a list

#### Output: `gold/anomalies.csv`

```
patient_id, timestamp, anomaly, value
101, 2024-10-27 03:14:50, High Heart Rate, 125
101, 2024-10-27 03:14:50, High Blood Pressure, 165
203, 2024-10-27 03:15:10, Low Oxygen, 89
```

---

### Task 5 — Visualizations

**Goal:** Generate insightful charts to communicate health trends and anomaly patterns.

All visualizations are saved to the `visualizations/` directory.

#### 1. Heart Rate Trend — `hr_trend.png`

- **Type:** Multi-line chart
- **X-axis:** Timestamp
- **Y-axis:** Heart Rate (bpm)
- **Details:** One line per patient (or a representative subset), showing HR fluctuation over time. A horizontal reference line at `hr = 120` marks the anomaly threshold.

#### 2. Oxygen Level Distribution — `oxygen_distribution.png`

- **Type:** Histogram with threshold highlight
- **X-axis:** Oxygen Saturation (%)
- **Y-axis:** Frequency
- **Details:** Distribution of all SpO₂ readings. Readings below `ox = 92` are highlighted (e.g., in red) to visually flag low-oxygen events.

#### 3. Anomaly Counts — `anomaly_counts.png`

- **Type:** Bar chart
- **X-axis:** Anomaly type (`High Heart Rate`, `Low Oxygen`, `High Blood Pressure`)
- **Y-axis:** Number of occurrences
- **Details:** Grouped count of each anomaly type from `gold/anomalies.csv`, providing a quick overview of the most prevalent health risks.

---

## 🧪 Input Data Summary

| File           | Format     | Records | Key Fields                                              |
| -------------- | ---------- | ------- | ------------------------------------------------------- |
| `vitals.jsonl` | JSON Lines | 1,500   | `patientId`, `timestamp`, `hr`, `ox`, `sys`, `dia`      |
| `ehr.csv`      | CSV        | 300     | `patient_id`, `name`, `age`, `gender`, `admission_time` |
| `labs.json`    | JSON List  | 900     | `patientId`, `test`, `value`, `timestamp`               |

- **300 unique patients**, each with **5 vitals readings** and **3 lab tests**.
- Vitals use **UNIX timestamps**; labs use **ISO datetime strings**.
- Data contains **natural variation** with **mild anomalies** seeded for detection.

---

## 🏗️ Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   BRONZE    │     │   SILVER    │     │    GOLD     │
│  (Raw Data) │────▶│  (Cleaned)  │────▶│ (Analytics) │
│             │     │             │     │             │
│ vitals.csv  │     │clean_vitals │     │anomalies.csv│
│ ehr.csv     │     │clean_labs   │     └──────┬──────┘
│ labs.csv    │     │patient_master│            │
└─────────────┘     └─────────────┘     ┌──────▼──────┐
                                        │VISUALIZATIONS│
                                        │  hr_trend    │
                                        │  oxygen_dist │
                                        │  anomaly_cnt │
                                        └──────────────┘
```

This follows the **Medallion Architecture** pattern:

- **Bronze** — Raw, immutable data lake
- **Silver** — Cleaned, conformed, and enriched datasets
- **Gold** — Business-level aggregates and analytical outputs

---

## 📊 Judging Criteria

| Category                        | Weight | Coverage                             |
| ------------------------------- | ------ | ------------------------------------ |
| Data Cleaning & Transformations | 30%    | Tasks 1–2 (Bronze + Silver layers)   |
| Pipeline Logic & Joins          | 25%    | Task 3 (Patient Master Table)        |
| Visualizations                  | 20%    | Task 5 (Charts in `visualizations/`) |
| Anomaly Detection               | 15%    | Task 4 (Rule-based flags in `gold/`) |
| Code Quality & README           | 10%    | Clean code + this documentation      |

---

## 👥 Team

**HCL Team Alpha**

---

## 📜 License

This project was built as part of the **HCL Hackathon** challenge.
