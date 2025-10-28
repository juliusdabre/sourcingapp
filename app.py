# PropWealth Next AI app code - paste full code from chat here

# ======================================================
#  PropWealth Next AI - v1.0  (Demo Build)
#  Author: Julius Dabre | Date: Oct 2025
# ======================================================

import streamlit as st
import pandas as pd
import numpy as np

# --------------------------
# PAGE CONFIG
# --------------------------
st.set_page_config(
    page_title="PropWealth Next AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

NAVY = "#0B1F3B"
GOLD = "#D4AF37"

# --------------------------
# AUTHENTICATION
# --------------------------
USERS = {
    "julius": {"password": "propwealth123", "role": "admin"},
    "megha": {"password": "sourcing123", "role": "sourcing"},
    "sunit": {"password": "sourcing123", "role": "sourcing"},
}

def login():
    st.markdown(f"<h2 style='color:{GOLD};text-align:center;'>PropWealth Next AI</h2>", unsafe_allow_html=True)
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if user in USERS and USERS[user]["password"] == pwd:
            st.session_state.user = user
            st.session_state.role = USERS[user]["role"]
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

if "user" not in st.session_state:
    login()

# --------------------------
# SIDEBAR NAVIGATION
# --------------------------
st.sidebar.title(f"Welcome, {st.session_state.user.title()}")
menu = st.sidebar.radio("Navigation", [
    "Upload Data", "Scoring Engine", "Dashboard", "Export", "Admin Settings"
])

# --------------------------
# HELPERS
# --------------------------
def compute_props_metrics(props: pd.DataFrame) -> pd.DataFrame:
    props = props.copy()
    # Growth derived from infrastructure score (demo logic)
    props["Growth_5Y"] = ((1 + (props["Infrastructure Score"] / 100)) ** 5 - 1) * 100
    props["Growth_10Y"] = ((1 + (props["Infrastructure Score"] / 100)) ** 10 - 1) * 100
    # Gross yield from weekly rent
    props["Yield%"] = (props["Expected Rent"] * 52 / props["Price"]) * 100
    return props

def get_default_weights():
    return {"Budget":0.2,"Yield":0.2,"Vacancy":0.15,"Infra":0.1,"Socio":0.1,"Finance":0.15,"Urgency":0.1,"Risk":0.1}

def match_score(c: pd.Series, p: pd.Series, weights: dict) -> float:
    score = 0.0
    w = weights or get_default_weights()
    # Budget fit (within range full points, else linear penalty)
    mid_budget = (c["Budget Max"] + c["Budget Min"]) / 2
    if c["Budget Min"] <= p["Price"] <= c["Budget Max"]:
        score += 100 * w["Budget"]
    else:
        denom = max(c["Budget Max"], 1)
        diff = abs((p["Price"] - mid_budget) / denom)
        score += max(0, (1 - diff)) * 100 * w["Budget"]
    # Yield alignment (cap at 10% for demo scaling)
    score += min(p["Yield%"] / 10, 1) * 100 * w["Yield"]
    # Vacancy impact (assume 0-5% typical range; lower is better)
    score += max(0, (1 - (p["Vacancy Rate"] / 5))) * 100 * w["Vacancy"]
    # Infra + Socio (0-10 scale to 0-100)
    score += (p["Infrastructure Score"] / 10) * 100 * w["Infra"]
    score += (p["Socioeconomic Score"] / 10) * 100 * w["Socio"]
    # Finance approved
    score += (1 if str(c["Finance Approved"]).strip().lower() == "yes" else 0.5) * 100 * w["Finance"]
    # Urgency
    u = str(c["Urgency"]).strip().lower()
    score += (1 if u == "high" else 0.7 if u == "medium" else 0.4) * 100 * w["Urgency"]
    # Risk appetite (demo constant until advanced mapping is added)
    score += 0.5 * 100 * w["Risk"]
    return round(float(score), 1)

def build_matches_df(clients: pd.DataFrame, props: pd.DataFrame, weights: dict) -> pd.DataFrame:
    props = compute_props_metrics(props)
    rows = []
    for _, c in clients.iterrows():
        for _, p in props.iterrows():
            rows.append({
                "Client": c["Client Name"],
                "Property": p["Property Name"],
                "Suburb": p["Suburb"],
                "State": p["State"],
                "Price": p["Price"],
                "Yield%": round(p["Yield%"], 2),
                "5Y Growth%": round(p["Growth_5Y"], 1),
                "10Y Growth%": round(p["Growth_10Y"], 1),
                "Match Score": match_score(c, p, weights),
                "Status": p.get("Property Status", "Ready to Present"),
                "Lead": p.get("Source Lead", "")
            })
    return pd.DataFrame(rows)

# --------------------------
# UPLOAD DATA SECTION
# --------------------------
if menu == "Upload Data":
    st.header("📁 Upload Client and Property Data")
    col1, col2 = st.columns(2)
    with col1:
        client_file = st.file_uploader("Upload Clients CSV", type="csv", help="Columns: Client Name, Budget Min, Budget Max, Strategy, Risk Appetite, Finance Approved, Urgency, Notes")
    with col2:
        property_file = st.file_uploader("Upload Properties CSV", type="csv", help="Columns: Property Name, Suburb, State, Price, Expected Rent, Vacancy Rate, Infrastructure Score, Socioeconomic Score, Source Lead, Property Status")
    if client_file and property_file:
        clients = pd.read_csv(client_file)
        props = pd.read_csv(property_file)
        st.session_state.clients = clients
        st.session_state.props = props
        st.success("✅ Files uploaded successfully")
        st.subheader("Clients Preview")
        st.dataframe(clients.head(), use_container_width=True)
        st.subheader("Properties Preview")
        st.dataframe(props.head(), use_container_width=True)
    else:
        st.info("Upload both CSV files to continue.")

# --------------------------
# SCORING ENGINE SLIDERS
# --------------------------
if menu == "Scoring Engine":
    st.header("⚙️ Weight Configuration")
    with st.form("weights"):
        col1, col2 = st.columns(2)
        with col1:
            w_budget = st.slider("Budget Fit Weight (%)", 0, 30, 20, help="Higher value prioritises listings closer to client budget.")
            w_yield  = st.slider("Yield/Growth Alignment (%)", 0, 30, 20, help="Emphasise cashflow vs growth alignment.")
            w_vacancy= st.slider("Vacancy Impact (%)", 0, 20, 15, help="Lower vacancy → higher score.")
            w_infra  = st.slider("Infrastructure Score (%)", 0, 20, 10, help="Upcoming projects & spend uplift growth.")
        with col2:
            w_socio  = st.slider("Socioeconomic Score (%)", 0, 20, 10, help="Education, income, stability indicators.")
            w_fin    = st.slider("Finance Approved (%)", 0, 20, 15, help="Finance-ready clients get priority.")
            w_urg    = st.slider("Urgency (%)", 0, 20, 10, help="Speed to transact.")
            w_risk   = st.slider("Risk Appetite (%)", 0, 20, 10, help="Future: map Regional/Metro preferences.")
        submitted = st.form_submit_button("Save Weights")
        if submitted:
            total = max(sum([w_budget,w_yield,w_vacancy,w_infra,w_socio,w_fin,w_urg,w_risk]), 1)
            weights = {
                "Budget": w_budget/total,
                "Yield":  w_yield/total,
                "Vacancy":w_vacancy/total,
                "Infra":  w_infra/total,
                "Socio":  w_socio/total,
                "Finance":w_fin/total,
                "Urgency":w_urg/total,
                "Risk":   w_risk/total
            }
            st.session_state.weights = weights
            st.success("Weights saved!")

# --------------------------
# DASHBOARD
# --------------------------
if menu == "Dashboard":
    st.header("📊 Property Match Dashboard")

    if "clients" not in st.session_state or "props" not in st.session_state:
        st.warning("Please upload client and property data first.")
        st.stop()

    clients = st.session_state.clients
    props = st.session_state.props
    weights = st.session_state.get("weights", get_default_weights())

    df = build_matches_df(clients, props, weights)

    # Analytics summary bar
    total_clients = df["Client"].nunique()
    ready = (df["Status"] == "Ready to Present").sum()
    avg_match = round(df["Match Score"].mean(), 1) if not df.empty else 0.0
    st.markdown(f"""
    <div style="background-color:{NAVY};color:{GOLD};padding:12px;border-radius:8px;margin-bottom:12px;">
    🧍 Clients: <b>{total_clients}</b> &nbsp; | &nbsp; 🏘️ Ready: <b>{ready}</b> &nbsp; | &nbsp; 📈 Avg Match: <b>{avg_match}%</b> &nbsp; | &nbsp; 🎯 Target: <b>28 / 40 Deals</b>
    </div>
    """, unsafe_allow_html=True)

    # Filters
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        statuses = df["Status"].dropna().unique().tolist()
        status_filter = st.multiselect("Filter by Status", options=statuses, default=statuses)
    with c2:
        states = df["State"].dropna().unique().tolist()
        state_filter = st.multiselect("Filter by State", options=states, default=states)
    with c3:
        leads = df["Lead"].dropna().unique().tolist()
        lead_filter = st.multiselect("Filter by Lead", options=leads, default=leads)
    with c4:
        clients_filter = st.multiselect("Filter by Client", options=df["Client"].unique().tolist(), default=df["Client"].unique().tolist())

    mask = (
        df["Status"].isin(status_filter) &
        df["State"].isin(state_filter) &
        df["Lead"].isin(lead_filter) &
        df["Client"].isin(clients_filter)
    )
    st.dataframe(df[mask].sort_values(["Client","Match Score"], ascending=[True, False]), use_container_width=True)

    # Store df for export step
    st.session_state.matches_df = df

# --------------------------
# EXPORT
# --------------------------
if menu == "Export":
    st.header("📤 Export Results")

    if "clients" in st.session_state and "props" in st.session_state:
        weights = st.session_state.get("weights", get_default_weights())
        df = st.session_state.get("matches_df")
        if df is None:
            # recompute if needed
            df = build_matches_df(st.session_state.clients, st.session_state.props, weights)
        st.write("Preview", df.head())

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Match Results CSV", csv_bytes, "match_results.csv", "text/csv", use_container_width=True)
    else:
        st.info("Upload data and view dashboard first.")

# --------------------------
# ADMIN SETTINGS (Julius only)
# --------------------------
if menu == "Admin Settings" and st.session_state.role == "admin":
    st.header("🔒 Admin Settings")
    st.info("Manage users and defaults (placeholder for future release).")
    st.write("Current users:", list(USERS.keys()))
else:
    if menu == "Admin Settings":
        st.warning("Admin access only.")
