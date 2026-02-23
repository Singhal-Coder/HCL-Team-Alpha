"""
main.py — Full Data Pipeline
==============================
Runs the entire pipeline in order:
  1. Bronze  — Convert raw files from INPUT_DATA to CSV
  2. Silver  — Clean EHR, Vitals, Labs + build patient master
  3. Gold    — Detect anomalies from patient master
  4. Viz     — Generate all visualizations

Usage:
  python main.py
"""

import os
import sys
import subprocess
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable  # uses the same python that ran main.py


def run_step(label, script_path):
    """Run a script and stream its output. Exits on failure."""
    full_path = os.path.join(ROOT_DIR, script_path)
    logging.info(f"{'─'*50}")
    logging.info(f"▶ {label}")
    logging.info(f"  Script: {script_path}")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [PYTHON, full_path],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )

    if result.stdout:
        for line in result.stdout.strip().splitlines():
            print(f"    {line}")

    if result.returncode != 0:
        logging.error(f"✗ FAILED: {script_path}")
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                print(f"    [ERR] {line}")
        sys.exit(1)

    logging.info(f"✓ {label} complete")


def main():
    start = time.time()
    logging.info("=" * 50)
    logging.info("  HCL HACKATHON — DATA PIPELINE")
    logging.info("=" * 50)

    # Ensure output directories exist
    for d in ["bronze", "silver", "gold", "visualizations"]:
        os.makedirs(os.path.join(ROOT_DIR, d), exist_ok=True)

    # BRONZE ── Convert raw files to CSV
    run_step("BRONZE: File Conversion", os.path.join("bronze", "file_conversion.py"))

    #  SILVER ── Clean individual datasets
    run_step("SILVER: Clean EHR",    os.path.join("silver", "clean_ehr.py"))
    run_step("SILVER: Clean Vitals", os.path.join("silver", "clean_vitals.py"))
    run_step("SILVER: Clean Labs",   os.path.join("silver", "clean_labs.py"))

    #  SILVER ── Build patient master dataset
    run_step("SILVER: Build Patient Master", os.path.join("silver", "build_patient_master.py"))

    #  GOLD ── Anomaly detection
    run_step("GOLD: Detect Anomalies", os.path.join("gold", "detect_anomalies.py"))

    #  VISUALIZATIONS ── Generate plots
    run_step("VISUALIZATIONS: Generate Plots", os.path.join("visualizations", "generate_plots.py"))

    elapsed = time.time() - start
    logging.info("─" * 50)
    logging.info(f"✓ PIPELINE COMPLETE in {elapsed:.1f}s")
    logging.info("─" * 50)


if __name__ == "__main__":
    main()