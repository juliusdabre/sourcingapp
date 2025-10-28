
# ======================================================
#  PropWealth Next AI - v1.0 (Fixed for Streamlit 1.50.0)
# ======================================================

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="PropWealth Next AI", layout="wide", initial_sidebar_state="expanded")

NAVY = "#0B1F3B"
GOLD = "#D4AF37"

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
            st.rerun()  # fixed
        else:
            st.error("Invalid credentials")
    st.stop()

if "user" not in st.session_state:
    login()

st.sidebar.title(f"Welcome, {st.session_state.user.title()}")
menu = st.sidebar.radio("Navigation", ["Upload Data", "Scoring Engine", "Dashboard", "Export", "Admin Settings"])

def compute_props_metrics(props: pd.DataFrame) -> pd.DataFrame:
    props = props.copy()
    props["Growth_5Y"] = ((1 + (props["Infrastructure Score"]/100))**5 - 1)*100
    props["Growth_10Y"] = ((1 + (props["Infrastructure Score"]/100))**10 - 1)*100
    props["Yield%"] = (props["Expected Rent"]*52/props["Price"])*100
    return props

def get_default_weights():
    return {"Budget":0.2,"Yield":0.2,"Vacancy":0.15,"Infra":0.1,"Socio":0.1,"Finance":0.15,"Urgency":0.1,"Risk":0.1}

def match_score(c,p,w):
    score=0
    mid=(c["Budget Max"]+c["Budget Min"])/2
    if c["Budget Min"]<=p["Price"]<=c["Budget Max"]: score+=100*w["Budget"]
    else:
        diff=abs((p["Price"]-mid)/max(c["Budget Max"],1))
        score+=max(0,(1-diff))*100*w["Budget"]
    score+=min(p["Yield%"]/10,1)*100*w["Yield"]
    score+=(1-(p["Vacancy Rate"]/5))*100*w["Vacancy"]
    score+=(p["Infrastructure Score"]/10)*100*w["Infra"]
    score+=(p["Socioeconomic Score"]/10)*100*w["Socio"]
    score+=(1 if c["Finance Approved"]=="Yes" else 0.5)*100*w["Finance"]
    score+=(1 if c["Urgency"]=="High" else 0.7 if c["Urgency"]=="Medium" else 0.4)*100*w["Urgency"]
    score+=0.5*100*w["Risk"]
    return round(score,1)

def build_matches_df(clients,props,weights):
    props=compute_props_metrics(props)
    out=[]
    for _,c in clients.iterrows():
        for _,p in props.iterrows():
            out.append({
                "Client":c["Client Name"],"Property":p["Property Name"],"Suburb":p["Suburb"],"State":p["State"],
                "Price":p["Price"],"Yield%":round(p["Yield%"],2),"5Y Growth%":round(p["Growth_5Y"],1),
                "10Y Growth%":round(p["Growth_10Y"],1),"Match Score":match_score(c,p,weights),
                "Status":p.get("Property Status","Ready to Present"),"Lead":p.get("Source Lead","")
            })
    return pd.DataFrame(out)

if menu=="Upload Data":
    st.header("📁 Upload Client and Property Data")
    c1,c2=st.columns(2)
    with c1: client_file=st.file_uploader("Upload Clients CSV",type="csv")
    with c2: prop_file=st.file_uploader("Upload Properties CSV",type="csv")
    if client_file and prop_file:
        st.session_state.clients=pd.read_csv(client_file)
        st.session_state.props=pd.read_csv(prop_file)
        st.success("✅ Files uploaded successfully")
        st.dataframe(st.session_state.clients.head())
        st.dataframe(st.session_state.props.head())
    else: st.info("Upload both CSVs.")

if menu=="Scoring Engine":
    st.header("⚙️ Weight Configuration")
    with st.form("weights"):
        w_budget=st.slider("Budget Fit (%)",0,30,20)
        w_yield=st.slider("Yield/Growth (%)",0,30,20)
        w_vacancy=st.slider("Vacancy (%)",0,20,15)
        w_infra=st.slider("Infrastructure (%)",0,20,10)
        w_socio=st.slider("Socioeconomic (%)",0,20,10)
        w_fin=st.slider("Finance Approved (%)",0,20,15)
        w_urg=st.slider("Urgency (%)",0,20,10)
        w_risk=st.slider("Risk Appetite (%)",0,20,10)
        if st.form_submit_button("Save Weights"):
            total=sum([w_budget,w_yield,w_vacancy,w_infra,w_socio,w_fin,w_urg,w_risk])
            st.session_state.weights={
                "Budget":w_budget/total,"Yield":w_yield/total,"Vacancy":w_vacancy/total,"Infra":w_infra/total,
                "Socio":w_socio/total,"Finance":w_fin/total,"Urgency":w_urg/total,"Risk":w_risk/total
            }
            st.success("Weights saved!")

if menu=="Dashboard":
    st.header("📊 Property Match Dashboard")
    if "clients" not in st.session_state or "props" not in st.session_state:
        st.warning("Please upload data first."); st.stop()
    clients=st.session_state.clients; props=st.session_state.props
    w=st.session_state.get("weights",get_default_weights())
    df=build_matches_df(clients,props,w)
    st.session_state.matches_df=df
    st.markdown(f"<div style='background-color:{NAVY};color:{GOLD};padding:10px;border-radius:5px;'>🧍 Clients: <b>{df['Client'].nunique()}</b> | 🏘 Ready: <b>{(df['Status']=='Ready to Present').sum()}</b> | 📈 Avg Match: <b>{round(df['Match Score'].mean(),1)}%</b> | 🎯 Target: 28/40</div>",unsafe_allow_html=True)
    st.dataframe(df,use_container_width=True)

if menu=="Export":
    st.header("📤 Export Results")
    if "matches_df" in st.session_state:
        csv=st.session_state.matches_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV",csv,"match_results.csv","text/csv")
    else: st.info("Generate dashboard first.")

if menu=="Admin Settings" and st.session_state.role=="admin":
    st.header("🔒 Admin Settings")
    st.write("Users:",list(USERS.keys()))
