import os
import sys
import subprocess
import glob

import streamlit as st
import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
VIS_DIR = os.path.join(ROOT, "visualizations")
PER_PATIENT_DIR = os.path.join(VIS_DIR, "per_patient_hr")
ANOMALIES_CSV = os.path.join(ROOT, "gold", "anomalies.csv")
MASTER_CSV = os.path.join(ROOT, "silver", "patient_master.csv")
PYTHON = sys.executable

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HCL Health Pipeline Dashboard",
    page_icon="🏥",
    layout="wide",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0f1117; }
    .main-title {
        font-size: 2.4rem; font-weight: 800;
        background: linear-gradient(90deg, #4f9cff, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle { color: #8b9ab5; font-size: 1rem; margin-bottom: 1.5rem; }
    .metric-card {
        background: #1a1f2e; border: 1px solid #2d3748;
        border-radius: 12px; padding: 1.2rem 1.5rem; text-align: center;
    }
    .metric-val { font-size: 2rem; font-weight: 700; color: #4f9cff; }
    .metric-lbl { font-size: 0.85rem; color: #8b9ab5; margin-top: 0.2rem; }
    .section-hdr {
        font-size: 1.3rem; font-weight: 700; color: #e2e8f0;
        border-left: 4px solid #4f9cff; padding-left: 0.75rem;
        margin: 1.5rem 0 1rem 0;
    }
    .log-box {
        background: #0d1117; border: 1px solid #2d3748; border-radius: 8px;
        padding: 1rem; font-family: monospace; font-size: 0.8rem;
        color: #a0aec0; max-height: 300px; overflow-y: auto;
    }
    .badge-success { background:#065f46; color:#6ee7b7; padding:4px 12px; border-radius:20px; font-size:0.8rem; }
    .badge-fail    { background:#7f1d1d; color:#fca5a5; padding:4px 12px; border-radius:20px; font-size:0.8rem; }
    .badge-idle    { background:#1e3a5f; color:#93c5fd; padding:4px 12px; border-radius:20px; font-size:0.8rem; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Helper functions
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline():
    """Run main.py and yield log lines as they stream."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen(
        [PYTHON, os.path.join(ROOT, "main.py")],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        env=env,
    )
    for line in proc.stdout:
        yield line.rstrip()
    proc.wait()
    return proc.returncode


def get_patient_ids():
    """Return sorted list of patient IDs from per_patient_hr PNGs."""
    pngs = glob.glob(os.path.join(PER_PATIENT_DIR, "hr_patient_*.png"))
    ids = []
    for p in pngs:
        try:
            pid = int(os.path.basename(p).replace("hr_patient_", "").replace(".png", ""))
            ids.append(pid)
        except ValueError:
            pass
    return sorted(ids)


def load_anomalies():
    if os.path.exists(ANOMALIES_CSV):
        return pd.read_csv(ANOMALIES_CSV)
    return None


def load_master():
    if os.path.exists(MASTER_CSV):
        df = pd.read_csv(MASTER_CSV)
        return df
    return None


# ══════════════════════════════════════════════════════════════════════════════
# Sidebar — Pipeline control
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🏥 HCL Pipeline")
    st.markdown("---")

    run_btn = st.button("▶ Run Full Pipeline", use_container_width=True, type="primary")

    st.markdown("---")
    st.markdown("**Pipeline Stages**")
    stages = [
        ("🔶", "Bronze", "File Conversion"),
        ("🥈", "Silver", "Clean EHR / Vitals / Labs"),
        ("🥈", "Silver", "Patient Master"),
        ("🥇", "Gold", "Anomaly Detection"),
        ("📊", "Viz", "Generate Plots"),
    ]
    for icon, layer, desc in stages:
        st.markdown(f"{icon} **{layer}** — {desc}")

    st.markdown("---")
    st.caption("Pipeline output stored in `bronze/`, `silver/`, `gold/`, `visualizations/`")


# ══════════════════════════════════════════════════════════════════════════════
# Header
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="main-title">🏥 Health Data Pipeline Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">HCL Hackathon · Team Alpha · Real-time patient analytics</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Pipeline Runner
# ══════════════════════════════════════════════════════════════════════════════

if run_btn:
    st.markdown('<div class="section-hdr">⚙ Pipeline Execution Log</div>', unsafe_allow_html=True)

    log_placeholder = st.empty()
    status_placeholder = st.empty()

    log_lines = []
    success = True

    with st.spinner("Running pipeline..."):
        for line in run_pipeline():
            log_lines.append(line)
            # Show last 30 lines in the log box
            display = "\n".join(log_lines[-30:])
            log_placeholder.markdown(
                f'<div class="log-box">{display}</div>',
                unsafe_allow_html=True,
            )
            if "FAILED" in line:
                success = False

    if success:
        status_placeholder.markdown('<span class="badge-success">✓ Pipeline completed successfully</span>', unsafe_allow_html=True)
        st.balloons()
    else:
        status_placeholder.markdown('<span class="badge-fail">✗ Pipeline failed — check logs above</span>', unsafe_allow_html=True)

    st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# Quick Stats Row
# ══════════════════════════════════════════════════════════════════════════════

master_df = load_master()
anomaly_df = load_anomalies()

c1, c2, c3, c4 = st.columns(4)

with c1:
    total_patients = master_df["patient_id"].nunique() if master_df is not None else "—"
    st.markdown(f'<div class="metric-card"><div class="metric-val">{total_patients}</div><div class="metric-lbl">Total Patients</div></div>', unsafe_allow_html=True)

with c2:
    total_records = len(master_df) if master_df is not None else "—"
    st.markdown(f'<div class="metric-card"><div class="metric-val">{total_records:,}</div><div class="metric-lbl">Master Records</div></div>', unsafe_allow_html=True)

with c3:
    total_anomalies = len(anomaly_df) if anomaly_df is not None else "—"
    st.markdown(f'<div class="metric-card"><div class="metric-val">{total_anomalies}</div><div class="metric-lbl">Anomalies Detected</div></div>', unsafe_allow_html=True)

with c4:
    patient_plots = len(get_patient_ids())
    st.markdown(f'<div class="metric-card"><div class="metric-val">{patient_plots}</div><div class="metric-lbl">Patient HR Plots</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Tabs
# ══════════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Visualizations",
    "❤️ Patient HR Viewer",
    "⚠️ Anomalies",
    "📋 Patient Master",
    "📁 Data Upload",
])

# ─── Tab 1: Main Visualizations ───────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-hdr">📈 Pipeline Visualizations</div>', unsafe_allow_html=True)

    hr_path  = os.path.join(VIS_DIR, "hr_trend.png")
    ox_path  = os.path.join(VIS_DIR, "oxygen_distribution.png")
    anom_path = os.path.join(VIS_DIR, "anomaly_counts.png")

    if not any(os.path.exists(p) for p in [hr_path, ox_path, anom_path]):
        st.info("No visualizations found. Click **▶ Run Full Pipeline** in the sidebar to generate them.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            if os.path.exists(hr_path):
                st.markdown("**Heart Rate Trend (All Patients)**")
                st.image(hr_path, use_container_width=True)
        with col2:
            if os.path.exists(ox_path):
                st.markdown("**Oxygen Level Distribution**")
                st.image(ox_path, use_container_width=True)

        if os.path.exists(anom_path):
            st.markdown("**Anomaly Counts by Type**")
            st.image(anom_path, use_container_width=True)

# ─── Tab 2: Per-Patient HR Viewer ─────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-hdr">❤️ Patient Heart Rate Trend Viewer</div>', unsafe_allow_html=True)

    patient_ids = get_patient_ids()

    if not patient_ids:
        st.info("No per-patient plots found. Run the full pipeline first to generate individual HR charts.")
    else:
        col_search, col_select = st.columns([1, 3])

        with col_search:
            search_id = st.number_input(
                "Jump to Patient ID",
                min_value=int(min(patient_ids)),
                max_value=int(max(patient_ids)),
                value=int(patient_ids[0]),
                step=1,
            )
            jump_btn = st.button("Go", use_container_width=True)

        with col_select:
            selected_id = st.selectbox(
                "Select Patient",
                options=patient_ids,
                format_func=lambda x: f"Patient {x}",
                key="patient_selectbox",
            )

        # If user used the jump box, override selection
        active_id = search_id if jump_btn else selected_id

        png_path = os.path.join(PER_PATIENT_DIR, f"hr_patient_{active_id}.png")
        if os.path.exists(png_path):
            st.markdown(f"**Heart Rate Trend — Patient {active_id}**")
            st.image(png_path, use_container_width=True)
        else:
            st.warning(f"No HR plot found for Patient {active_id}.")

        # Show that patient's raw data if available
        if master_df is not None:
            patient_data = master_df[master_df["patient_id"] == active_id][
                ["vitals_timestamp", "hr", "ox", "sys", "dia"]
            ].copy()
            if not patient_data.empty:
                st.markdown(f"**Raw Vitals — Patient {active_id}**")
                st.dataframe(patient_data, use_container_width=True, hide_index=True)

# ─── Tab 3: Anomalies ─────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-hdr">⚠️ Detected Anomalies</div>', unsafe_allow_html=True)

    if anomaly_df is None:
        st.info("No anomalies file found. Run the pipeline first.")
    else:
        # Summary metrics
        breakdown = anomaly_df["anomaly"].value_counts()
        cols = st.columns(len(breakdown))
        for i, (atype, count) in enumerate(breakdown.items()):
            with cols[i]:
                st.metric(atype, count)

        st.markdown("---")

        # Filters
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            anom_types = ["All"] + list(anomaly_df["anomaly"].unique())
            selected_type = st.selectbox("Filter by Anomaly Type", anom_types)
        with filter_col2:
            pid_filter = st.text_input("Filter by Patient ID (optional)", "")

        filtered = anomaly_df.copy()
        if selected_type != "All":
            filtered = filtered[filtered["anomaly"] == selected_type]
        if pid_filter.strip():
            try:
                filtered = filtered[filtered["patient_id"] == int(pid_filter.strip())]
            except ValueError:
                st.warning("Please enter a valid numeric Patient ID.")

        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(filtered)} of {len(anomaly_df)} anomalies")

# ─── Tab 4: Patient Master ─────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-hdr">📋 Patient Master Table</div>', unsafe_allow_html=True)

    if master_df is None:
        st.info("Patient master table not found. Run the pipeline first.")
    else:
        # Search bar
        search = st.text_input("Search by Patient ID or Name", "")
        display_df = master_df.copy()
        if search.strip():
            mask = (
                display_df["patient_id"].astype(str).str.contains(search, case=False) |
                display_df["name"].astype(str).str.contains(search, case=False)
            )
            display_df = display_df[mask]

        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(display_df)} of {len(master_df)} records")

# ─── Tab 5: Data Upload ────────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-hdr">📁 Upload Raw Data Files</div>', unsafe_allow_html=True)
    st.info("Upload files here to save them to the `INPUT_DATA` folder. Supported formats: CSV, JSON, Excel, Word.")

    uploaded_files = st.file_uploader(
        "Choose files",
        accept_multiple_files=True,
        type=["csv", "json", "xlsx", "docx"],
        help="Files will be saved directly to the 'INPUT_DATA' directory."
    )

    if uploaded_files:
        st.markdown(f"**Selected {len(uploaded_files)} file(s):**")
        for f in uploaded_files:
            st.text(f"  • {f.name} ({f.size / 1024:.1f} KB)")

        if st.button("🚀 Save Files to INPUT_DATA", use_container_width=True):
            input_data_path = os.path.join(ROOT, "INPUT_DATA")
            os.makedirs(input_data_path, exist_ok=True)
            
            try:
                saved_count = 0
                for uploaded_file in uploaded_files:
                    target_path = os.path.join(input_data_path, uploaded_file.name)
                    with open(target_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    saved_count += 1
                
                st.success(f"✅ Successfully saved {saved_count} file(s) to `INPUT_DATA/`")
                st.info("You can now run the pipeline to process these files.")
            except Exception as e:
                st.error(f"❌ Failed to save files: {str(e)}")
