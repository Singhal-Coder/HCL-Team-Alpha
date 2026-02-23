import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

VITALS_PATH = os.path.join(ROOT_DIR, "silver", "clean_vitals.csv")
ANOMALIES_PATH = os.path.join(ROOT_DIR, "gold", "anomalies.csv")
OUTPUT_DIR = SCRIPT_DIR

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"figure.dpi": 150, "savefig.bbox": "tight"})



# Heart Rate Trend — combined multi-line plot
def plot_hr_trend(vitals):
    vitals = vitals.copy()
    vitals["timestamp"] = pd.to_datetime(vitals["timestamp"])

    fig, ax = plt.subplots(figsize=(14, 6))

    for pid, grp in vitals.groupby("patient_id"):
        grp = grp.sort_values("timestamp")
        ax.plot(grp["timestamp"], grp["hr"],
                alpha=0.15, linewidth=0.8, color="#1976D2")

    ax.axhline(y=120, color="red", linestyle="--", linewidth=1.5,
               label="High HR Threshold (120 bpm)")

    sample_ids = sorted(vitals["patient_id"].unique())[::60][:5]
    colors = ["#E53935", "#43A047", "#FB8C00", "#8E24AA", "#00ACC1"]
    for pid, c in zip(sample_ids, colors):
        grp = vitals[vitals["patient_id"] == pid].sort_values("timestamp")
        ax.plot(grp["timestamp"], grp["hr"],
                marker="o", markersize=4, linewidth=1.8, color=c,
                label=f"Patient {pid}")

    ax.set_xlabel("Timestamp", fontsize=11)
    ax.set_ylabel("Heart Rate (bpm)", fontsize=11)
    ax.set_title("Heart Rate Trend — All Patients (Line Chart: Timestamp vs HR)", fontsize=13)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    fig.autofmt_xdate()

    path = os.path.join(OUTPUT_DIR, "hr_trend.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  ✓ {path}")



#Heart Rate Trend — one plot per patient

def plot_hr_per_patient(vitals):
    vitals = vitals.copy()
    vitals["timestamp"] = pd.to_datetime(vitals["timestamp"])

    out_dir = os.path.join(OUTPUT_DIR, "per_patient_hr")
    os.makedirs(out_dir, exist_ok=True)

    patient_ids = sorted(vitals["patient_id"].unique())
    print(f"  Generating {len(patient_ids)} per-patient HR plots...")

    for pid in patient_ids:
        grp = vitals[vitals["patient_id"] == pid].sort_values("timestamp")

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(grp["timestamp"], grp["hr"],
                marker="o", markersize=5, linewidth=1.5, color="#1976D2")
        ax.axhline(y=120, color="red", linestyle="--", linewidth=1, alpha=0.7,
                   label="Threshold (120)")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Heart Rate (bpm)")
        ax.set_title(f"Heart Rate Trend — Patient {pid}")
        ax.legend(fontsize=8)
        fig.autofmt_xdate()

        fig.savefig(os.path.join(out_dir, f"hr_patient_{pid}.png"))
        plt.close(fig)

    print(f"  ✓ Saved {len(patient_ids)} plots to per_patient_hr/")



# Oxygen Level Distribution — histogram + box plot

def plot_oxygen_distribution(vitals):
    fig = plt.figure(figsize=(12, 7))
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.08)

    ox = vitals["ox"]
    normal = ox[ox >= 92]
    low = ox[ox < 92]

    ax1 = fig.add_subplot(gs[0])
    ax1.hist(normal, bins=30, color="#4CAF50", alpha=0.8,
             edgecolor="white", label=f"Normal ≥ 92% ({len(normal)})")
    ax1.hist(low, bins=10, color="#F44336", alpha=0.85,
             edgecolor="white", label=f"Low < 92% ({len(low)})")
    ax1.axvline(x=92, color="red", linestyle="--", linewidth=2, label="Threshold (92%)")
    ax1.set_ylabel("Frequency", fontsize=11)
    ax1.set_title("Oxygen Level Distribution — Histogram & Box Plot", fontsize=13)
    ax1.legend(fontsize=9)
    ax1.set_xticklabels([])

    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax2.boxplot(ox, vert=False, widths=0.6,
                patch_artist=True,
                boxprops=dict(facecolor="#90CAF9", edgecolor="#1565C0"),
                medianprops=dict(color="#D32F2F", linewidth=2),
                flierprops=dict(marker="o", markerfacecolor="#F44336", markersize=5))
    ax2.axvline(x=92, color="red", linestyle="--", linewidth=2)
    ax2.set_xlabel("Oxygen Level (%)", fontsize=11)
    ax2.set_yticks([])

    path = os.path.join(OUTPUT_DIR, "oxygen_distribution.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  ✓ {path}")



# Bar Chart of Anomaly Counts

def plot_anomaly_counts(anomalies):
    fig, ax = plt.subplots(figsize=(9, 5))

    counts = anomalies["anomaly"].value_counts()
    colors = {
        "High Heart Rate": "#FF9800",
        "Low Oxygen": "#F44336",
        "High Blood Pressure": "#9C27B0",
    }
    bar_colors = [colors.get(a, "#2196F3") for a in counts.index]

    bars = ax.bar(counts.index, counts.values, color=bar_colors,
                  edgecolor="white", linewidth=1.5)

    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(val), ha="center", va="bottom", fontweight="bold", fontsize=12)

    ax.set_xlabel("Anomaly Type", fontsize=11)
    ax.set_ylabel("Number of Occurrences", fontsize=11)
    ax.set_title("Anomaly Counts by Type", fontsize=13)

    path = os.path.join(OUTPUT_DIR, "anomaly_counts.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  ✓ {path}")


if __name__ == "__main__":
    print("Generating visualizations...\n")

    vitals = pd.read_csv(VITALS_PATH)
    print(f"Loaded {len(vitals)} vitals records")

    plot_hr_trend(vitals)
    plot_hr_per_patient(vitals)
    plot_oxygen_distribution(vitals)

    if os.path.exists(ANOMALIES_PATH):
        anomalies = pd.read_csv(ANOMALIES_PATH)
        print(f"Loaded {len(anomalies)} anomalies")
        plot_anomaly_counts(anomalies)
    else:
        print(f"  [WARN] {ANOMALIES_PATH} not found — run gold/detect_anomalies.py first.")

    print("\nDone!")
