import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
from datetime import timedelta

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="SCB Current Analysis",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# THEME & CONSTANTS
# =========================================================
NAVY_BG = "#0B1F33"
WHITE_BG = "#FFFFFF"
TEXT_LIGHT = "#F5F7FA"
TEXT_DARK = "#1F2937"

LOGO_URL = (
    "https://upload.wikimedia.org/wikipedia/en/thumb/e/e3/"
    "Azure_Power_logo.svg/500px-Azure_Power_logo.svg.png"
)

# =========================================================
# SESSION STATE
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = "WELCOME"

if "cb_df" not in st.session_state:
    st.session_state.cb_df = None

if "dc_df" not in st.session_state:
    st.session_state.dc_df = None

if "selected_scbs" not in st.session_state:
    st.session_state.selected_scbs = []

# =========================================================
# TEMPLATE GENERATORS
# =========================================================
def generate_cb_template():
    return pd.DataFrame({
        "Date": ["2025-01-01"],
        "Time": ["10:00:00"],
        "CB_CURRENT_1": [10.5],
        "CB_CURRENT_2": [10.8]
    })

def generate_dc_template():
    return pd.DataFrame({
        "CB_INDEX": ["CB_CURRENT_1", "CB_CURRENT_2"],
        "STRINGS": [24, 24]
    })

# =========================================================
# FILE VALIDATION
# =========================================================
def validate_cb_file(df):
    if not {"Date", "Time"}.issubset(df.columns):
        return False, "Missing Date or Time column"
    cb_cols = [c for c in df.columns if c.startswith("CB_CURRENT")]
    if not cb_cols:
        return False, "No CB_CURRENT columns found"
    return True, "Valid CB data file"

def validate_dc_file(df):
    if not {"CB_INDEX", "STRINGS"}.issubset(df.columns):
        return False, "Missing CB_INDEX or STRINGS column"
    if df["STRINGS"].isnull().any():
        return False, "STRINGS column contains empty values"
    return True, "Valid DC capacity file"

# =========================================================
# DATA LOADERS
# =========================================================
def load_cb_file(file):
    df = pd.read_csv(file) if file.name.endswith("csv") else pd.read_excel(file)
    df["DATETIME"] = pd.to_datetime(df["Date"] + " " + df["Time"])
    return df.drop(columns=["Date", "Time"])

def load_dc_file(file):
    df = pd.read_csv(file) if file.name.endswith("csv") else pd.read_excel(file)
    return df.set_index("CB_INDEX")

# =========================================================
# ANALYTICS HELPERS
# =========================================================
def get_scb_columns(df):
    return [c for c in df.columns if c.startswith("CB_CURRENT")]

def apply_threshold(df, scbs, threshold):
    df = df.copy()
    for scb in scbs:
        df[scb] = np.where(df[scb] > threshold, 0, df[scb])
    return df

def remove_inactive(df, scbs):
    return [s for s in scbs if not (df[s] == 0).all()]

def plot_timeseries(df, scbs):
    fig = go.Figure()
    for scb in scbs:
        fig.add_trace(go.Scatter(
            x=df["DATETIME"],
            y=df[scb],
            mode="lines",
            name=scb
        ))

    fig.update_layout(
        height=420,
        hovermode="x unified",
        legend=dict(x=1.02, y=1),
        margin=dict(l=40, r=260, t=20, b=40),
        plot_bgcolor=WHITE_BG,
        paper_bgcolor=WHITE_BG,
        font=dict(color=TEXT_DARK)
    )
    return fig

# =========================================================
# WELCOME PAGE
# =========================================================
def welcome_page():
    st.markdown("""
    <style>
    .welcome-box {
        max-width: 720px;
        margin: auto;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="welcome-box">', unsafe_allow_html=True)

    st.image(LOGO_URL, width=180)
    st.markdown("<h1>SCB Current Analysis</h1>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    st.subheader("Download Templates")

    cb_t = generate_cb_template()
    dc_t = generate_dc_template()

    c1, c2 = st.columns(2)

    with c1:
        st.download_button("⬇ CB Current Template (CSV)", cb_t.to_csv(index=False),
                           "cb_template.csv", "text/csv")
        buf = io.BytesIO()
        cb_t.to_excel(buf, index=False)
        st.download_button("⬇ CB Current Template (XLSX)", buf.getvalue(),
                           "cb_template.xlsx")

    with c2:
        st.download_button("⬇ DC Capacity Template (CSV)", dc_t.to_csv(index=False),
                           "dc_template.csv", "text/csv")
        buf = io.BytesIO()
        dc_t.to_excel(buf, index=False)
        st.download_button("⬇ DC Capacity Template (XLSX)", buf.getvalue(),
                           "dc_template.xlsx")

    st.markdown("<br>", unsafe_allow_html=True)

    cb_file = st.file_uploader("Upload Merged CB Data File", type=["csv", "xlsx"])
    dc_file = st.file_uploader("Upload DC Capacity File", type=["csv", "xlsx"])

    cb_ok = dc_ok = False

    if cb_file:
        try:
            df = pd.read_csv(cb_file) if cb_file.name.endswith("csv") else pd.read_excel(cb_file)
            ok, msg = validate_cb_file(df)
            if ok:
                st.success("✔ " + msg)
                st.session_state.cb_df = load_cb_file(cb_file)
                cb_ok = True
            else:
                st.error("❌ " + msg)
        except Exception as e:
            st.error(f"❌ Failed to read CB file: {e}")

    if dc_file:
        try:
            df = pd.read_csv(dc_file) if dc_file.name.endswith("csv") else pd.read_excel(dc_file)
            ok, msg = validate_dc_file(df)
            if ok:
                st.success("✔ " + msg)
                st.session_state.dc_df = load_dc_file(dc_file)
                dc_ok = True
            else:
                st.error("❌ " + msg)
        except Exception as e:
            st.error(f"❌ Failed to read DC file: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Proceed to Dashboard", disabled=not (cb_ok and dc_ok), use_container_width=True):
        st.session_state.page = "DASHBOARD"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# DASHBOARD PAGE
# =========================================================
def dashboard_page():
    # ---------- HEADER ----------
    st.markdown(f"""
    <div style="
        position:fixed;
        top:0; left:0; right:0;
        height:60px;
        background:{NAVY_BG};
        color:{TEXT_LIGHT};
        display:flex;
        align-items:center;
        padding-left:20px;
        z-index:1000;">
        <b>SCB Current Analysis</b>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:70px'></div>", unsafe_allow_html=True)

    # ---------- CSS (NO f-string HERE) ----------
    st.markdown("""
    <style>

    section[data-testid="stSidebar"] {
        background-color:#0B1F33;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color:#F5F7FA !important;
        font-weight:600;
    }

    /* Number input text */
    section[data-testid="stSidebar"] input {
        color:#000000 !important;
        background-color:#FFFFFF !important;
        font-weight:600;
    }

    /* + and − buttons */
    section[data-testid="stSidebar"] button[data-testid="stNumberInputStepUp"],
    section[data-testid="stSidebar"] button[data-testid="stNumberInputStepDown"] {
        color:#0B1F33 !important;
        background-color:#FDBA74
 !important;
        border-radius:0px;
    }

    /* Help (?) icon */
    section[data-testid="stSidebar"] svg {
        fill:#F5F7FA !important;
    }

    /* Selectbox selected text */
    section[data-testid="stSidebar"] div[data-baseweb="select"] span {
        color:#000000 !important;
        font-weight:600;
    }

    /* Greyish-blue boxes */
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] button {
        background-color:#FDBA74
 !important;
        color:#0B1F33 !important;
        border-radius:8px;
        font-weight:600;
        border:none;
    }

    section[data-testid="stSidebar"] button:hover {
        background-color:#D4E2F1 !important;
    }

    .block-container {
        padding-top:0.8rem;
    }

    div[data-testid="stRadio"] {
        margin-top:-10px;
    }

    div[data-testid="stRadio"] + div {
        margin-top:-10px;
    }

    </style>
    """, unsafe_allow_html=True)

    # ---------- SIDEBAR ----------
    with st.sidebar:
        st.image(LOGO_URL, width=140)
        st.markdown("## Filters")

        threshold = st.number_input(
            "Current Threshold",
            value=200.0,
            help="If Current > Threshold → value treated as 0"
        )

        date_option = st.selectbox(
            "Date Range",
            ["All", "Today", "Last 7 Days", "Last 15 Days", "Custom"]
        )

        df = st.session_state.cb_df.copy()

        if date_option == "Custom":
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
            df = df[
                (df["DATETIME"].dt.date >= start_date) &
                (df["DATETIME"].dt.date <= end_date)
            ]
        elif date_option != "All":
            max_dt = df["DATETIME"].max()
            days = {"Today": 0, "Last 7 Days": 7, "Last 15 Days": 15}[date_option]
            df = df[df["DATETIME"] >= max_dt - timedelta(days=days)]

        scbs = get_scb_columns(df)

        if st.checkbox("Remove Inactive SCBs"):
            scbs = remove_inactive(df, scbs)

        st.markdown("### Select SCBs")

        if st.button("Select All"):
            st.session_state.selected_scbs = scbs.copy()

        if st.button("Clear All"):
            st.session_state.selected_scbs = []

        st.markdown("<div style='max-height:280px; overflow-y:auto;'>", unsafe_allow_html=True)

        selected = []
        for scb in scbs:
            if st.checkbox(scb, value=scb in st.session_state.selected_scbs):
                selected.append(scb)

        st.markdown("</div>", unsafe_allow_html=True)
        st.session_state.selected_scbs = selected

        if st.button("Back to Home"):
            st.session_state.page = "WELCOME"
            st.rerun()

    # ---------- MAIN CONTENT ----------
    df = apply_threshold(df, st.session_state.selected_scbs, threshold)

    st.markdown("**View Mode**")

    mode = st.radio(
        "",
        ["Raw Current", "Normalized Current"],
        horizontal=True,
        label_visibility="collapsed"
    )

    plot_df = df.copy()

    if mode == "Normalized Current":
        for scb in st.session_state.selected_scbs:
            if scb in st.session_state.dc_df.index:
                plot_df[scb] /= st.session_state.dc_df.loc[scb, "STRINGS"]

    fig = plot_timeseries(plot_df, st.session_state.selected_scbs)

    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# ROUTER
# =========================================================
if st.session_state.page == "WELCOME":
    welcome_page()
else:
    dashboard_page()
