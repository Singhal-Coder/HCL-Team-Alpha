"""
Bronze Layer - Convert INPUT_DATA files to CSV
===============================================
Reads from INPUT_DATA/ and writes CSVs to bronze/.
Just re-run this script whenever INPUT_DATA files are updated.

Usage:  python bronze/file_conversion.py
"""

import os
import json
import csv
import pandas as pd


# --- Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
INPUT_DIR = os.path.join(ROOT_DIR, "INPUT_DATA")
OUTPUT_DIR = SCRIPT_DIR  # bronze/


def json_to_csv(input_json, output_csv):
    """Convert a JSON file (array of objects) to CSV."""
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    return len(data)


def csv_to_csv(input_csv, output_csv):
    """Copy/normalize a CSV file."""
    df = pd.read_csv(input_csv)
    df.to_csv(output_csv, index=False, encoding="utf-8")
    return len(df)


if __name__ == "__main__":
    print("=" * 50)
    print("Converting INPUT_DATA -> bronze/ (CSV)")
    print("=" * 50)

    # INPUT file -> OUTPUT csv name
    conversions = [
        ("ehr.csv",     "ehr.csv"),
        ("labs.json",   "labs.csv"),
        ("vitals.json", "vitals.csv"),
    ]

    for src_name, dst_name in conversions:
        src = os.path.join(INPUT_DIR, src_name)
        dst = os.path.join(OUTPUT_DIR, dst_name)
        ext = os.path.splitext(src_name)[1].lower()

        try:
            if ext == ".json":
                rows = json_to_csv(src, dst)
            elif ext == ".csv":
                rows = csv_to_csv(src, dst)
            elif ext in (".xlsx", ".xls"):
                df = pd.read_excel(src)
                df.to_csv(dst, index=False, encoding="utf-8")
                rows = len(df)
            else:
                print(f"  [SKIP] Unsupported: {src_name}")
                continue
            print(f"  ✓ {src_name} -> {dst_name}  ({rows} rows)")
        except Exception as e:
            print(f"  ✗ {src_name} FAILED: {e}")

    print("\nDone!")