import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

st.set_page_config(
    page_title="Vantura — Actuarial Wealth Intelligence",
    page_icon="⚜️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_global_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=DM+Sans:wght@300;400;500&family=JetBrains+Mono:wght@300;400&display=swap');
    :root{
        --gold:#C9A84C;--gold-l:#E8C97A;--gold-d:rgba(201,168,76,.15);
        --teal:#2DD4BF;--teal-d:rgba(45,212,191,.12);
        --bg:#0A0D14;--bg2:#111520;--card:#161B2E;
        --tp:#F0EDE8;--ts:#9B97A0;--tm:#5A5768;
        --bdr:rgba(201,168,76,.18);--bdrs:rgba(255,255,255,.06);
        --err:#FF4757;--ok:#2DD4BF;--warn:#FFA502;
    }
    *,*::before,*::after{box-sizing:border-box;}
    html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"]{
        background:var(--bg)!important;color:var(--tp)!important;
        font-family:'DM Sans',sans-serif!important;}
    [data-testid="stSidebar"]{background:var(--bg2)!important;
        border-right:1px solid var(--bdr)!important;}
    [data-testid="stSidebar"] * {font-family:'DM Sans',sans-serif!important;}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {color:var(--ts);}
    
    [data-testid="stSidebar"] * {font-family:'DM Sans',sans-serif!important;}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {color:var(--ts);}
    
    /* 1. Membuat Kotak Background Emas */
    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] .stButton > button {
        background-color: var(--gold) !important;
        border-radius: 8px !important;
        border: none !important;
        margin-bottom: 6px !important;
        padding-left: 10px !important;
        text-decoration: none !important;
    }

    /* 2. MEMAKSA Semua Teks dan Icon Jadi Hitam Pekat */
    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] a *,
    [data-testid="stSidebar"] a p,
    [data-testid="stSidebar"] a span,
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stButton > button *,
    [data-testid="stSidebar"] .stButton > button p,
    [data-testid="stSidebar"] .stButton > button span {
        color: #000000 !important; 
        font-weight: 800 !important;
    }

    /* 3. Efek Emas Terang Saat Disorot Mouse */
    [data-testid="stSidebar"] a:hover,
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: var(--gold-l) !important;
    }
    [data-testid="stHeader"]{background:transparent!important;}
    h1,h2,h3{font-family:'Cormorant Garamond',serif!important;color:var(--tp)!important;}
    .stButton>button{background:linear-gradient(135deg,var(--gold),#A8862E)!important;
        color:#0A0D14!important;border:none!important;border-radius:6px!important;
        font-family:'DM Sans',sans-serif!important;font-weight:500!important;
        font-size:.875rem!important;letter-spacing:.05em!important;
        padding:.6rem 1.4rem!important;transition:all .2s ease!important;}
    .stButton>button:hover{background:linear-gradient(135deg,var(--gold-l),var(--gold))!important;
        transform:translateY(-1px)!important;
        box-shadow:0 4px 20px rgba(201,168,76,.30)!important;}
    .stTextInput>div>div>input,.stNumberInput>div>div>input{
        background:var(--card)!important;color:var(--tp)!important;
        border:1px solid var(--bdrs)!important;border-radius:6px!important;
        font-family:'DM Sans',sans-serif!important;}
    .stTextInput>div>div>input:focus,.stNumberInput>div>div>input:focus{
        border-color:var(--gold)!important;box-shadow:0 0 0 2px var(--gold-d)!important;}
    .stSelectbox>div>div{background:var(--card)!important;color:var(--tp)!important;
        border:1px solid var(--bdrs)!important;}
    label,[data-baseweb="label"]{color:var(--ts)!important;font-size:.78rem!important;
        letter-spacing:.07em!important;text-transform:uppercase!important;}
    [data-testid="stMetricValue"]{color:var(--gold)!important;
        font-family:'Cormorant Garamond',serif!important;font-size:2rem!important;}
    [data-testid="stMetricLabel"]{color:var(--ts)!important;font-size:.75rem!important;
        letter-spacing:.08em!important;text-transform:uppercase!important;}
    .stMetric{background:var(--card)!important;border:1px solid var(--bdrs)!important;
        border-radius:10px!important;padding:1rem 1.2rem!important;}
    div[data-testid="stCheckbox"] label{text-transform:none!important;
        letter-spacing:normal!important;font-size:.88rem!important;}
    ::-webkit-scrollbar{width:5px;height:5px;}
    ::-webkit-scrollbar-track{background:var(--bg2);}
    ::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:3px;}
    .v-card{background:var(--card);border:1px solid var(--bdrs);
        border-radius:12px;padding:1.5rem;}
    .v-card-gold{border-color:var(--bdr)!important;}
    .alert-danger{background:rgba(255,71,87,.08);border:1px solid rgba(255,71,87,.3);
        border-radius:10px;padding:1rem 1.3rem;}
    .alert-warn{background:rgba(255,165,2,.08);border:1px solid rgba(255,165,2,.3);
        border-radius:10px;padding:1rem 1.3rem;}
    .alert-ok{background:rgba(45,212,191,.08);border:1px solid rgba(45,212,191,.3);
        border-radius:10px;padding:1rem 1.3rem;}
    </style>
    """, unsafe_allow_html=True)


inject_global_css()

try:
    st.switch_page("pages/0_login.py")
except Exception:
    st.switch_page("pages/1_profil.py")