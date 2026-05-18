import sys, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv; load_dotenv()

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from utils.session       import auth_guard
from engine.actuarial    import ActuarialEngine, UserProfile, SCENARIOS
from engine.data_fetcher import fetch_all_live_data
from pages._shared       import sidebar

st.set_page_config(page_title="Vantura — Stress Test", page_icon="⚜️",
                   layout="wide", initial_sidebar_state="expanded")
auth_guard()
if "user_profile" not in st.session_state:
    st.switch_page("pages/1_profil.py")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600&family=DM+Sans:wght@300;400;500&display=swap');
:root{--gold:#C9A84C;--gold-l:#E8C97A;--teal:#2DD4BF;--bg:#0A0D14;--bg2:#111520;
      --card:#161B2E;--tp:#F0EDE8;--ts:#9B97A0;--tm:#5A5768;
      --bdr:rgba(201,168,76,.18);--bdrs:rgba(255,255,255,.06);}
*,*::before,*::after{box-sizing:border-box;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"]{
    background:var(--bg)!important;color:var(--tp)!important;font-family:'DM Sans',sans-serif!important;}
[data-testid="stSidebar"]{background:var(--bg2)!important;border-right:1px solid var(--bdr)!important;}
[data-testid="stSidebar"] *{font-family:'DM Sans',sans-serif!important;color:var(--ts)!important;}
[data-testid="stHeader"]{background:transparent!important;}
h1,h2,h3{font-family:'Cormorant Garamond',serif!important;color:var(--tp)!important;}
.stButton>button{background:linear-gradient(135deg,var(--gold),#A8862E)!important;
    color:#0A0D14!important;border:none!important;border-radius:6px!important;
    font-weight:500!important;font-size:.875rem!important;padding:.6rem 1.4rem!important;}
.stSelectbox>div>div{background:var(--card)!important;color:var(--tp)!important;
    border:1px solid var(--bdrs)!important;}
label,[data-baseweb="label"]{color:var(--ts)!important;font-size:.78rem!important;
    letter-spacing:.07em!important;text-transform:uppercase!important;}
[data-testid="stMetricValue"]{color:var(--gold)!important;
    font-family:'Cormorant Garamond',serif!important;font-size:1.9rem!important;}
[data-testid="stMetricLabel"]{color:var(--ts)!important;font-size:.74rem!important;
    letter-spacing:.08em!important;text-transform:uppercase!important;}
.stMetric{background:var(--card)!important;border:1px solid var(--bdrs)!important;
    border-radius:10px!important;padding:1rem 1.2rem!important;}
::-webkit-scrollbar{width:5px;}::-webkit-scrollbar-track{background:var(--bg2);}
::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:3px;}
[data-testid="stSidebarNav"],[data-testid="stSidebarNavItems"],[data-testid="stSidebarNavSeparator"],[data-testid="collapsedControl"]{display:none!important;}
</style>""", unsafe_allow_html=True)

SC_COLORS = {
    "Normal":"#C9A84C","Hiperinflasi Medis":"#FF4757",
    "Market Crash -30%":"#FF6B35","Resesi Ekonomi":"#FFA502","Skenario Optimis":"#2DD4BF",
}
SC_DESC = {
    "Normal":             "Kondisi pasar normal. Inflasi 5%, return investasi 8.5%/thn.",
    "Hiperinflasi Medis": "Biaya kesehatan melonjak 3× lipat normal. Return investasi turun 15%. Terjadi saat wabah atau krisis kesehatan besar.",
    "Market Crash -30%":  "Nilai portofolio langsung turun 30% di awal, lalu pulih perlahan. Mirip krisis 2008 atau COVID-2020.",
    "Resesi Ekonomi":     "Inflasi tinggi (7.5%) + return investasi turun 40%. Skenario stagflasi seperti 1998.",
    "Skenario Optimis":   "Pertumbuhan ekonomi kuat, inflasi terkendali 3.5%, return investasi naik 25%.",
}

def rp(v):
    if abs(v)>=1e9: return f"Rp {v/1e9:.2f} M"
    if abs(v)>=1e6: return f"Rp {v/1e6:.1f} Jt"
    return f"Rp {v:,.0f}"

live = fetch_all_live_data()
sidebar(live)

st.markdown("""
<div style="margin-bottom:2rem;">
    <h1 style="font-family:'Cormorant Garamond',serif;font-size:2.2rem;font-weight:300;
         color:#F0EDE8;letter-spacing:.04em;line-height:1.2;margin-bottom:.3rem;">
        Stress Test <span style="color:#C9A84C;">Skenario Ekstrem</span></h1>
    <p style="color:#5A5768;font-size:.83rem;">
        Uji ketahanan rencana pensiun Anda terhadap berbagai kondisi ekonomi buruk</p>
</div>
""", unsafe_allow_html=True)

sel_sc = st.selectbox("Pilih Skenario", list(SCENARIOS.keys()), key="stress_sel")

base_profile: UserProfile = st.session_state["user_profile"]
results = {}
with st.spinner("Menjalankan semua skenario…"):
    for sk in SCENARIOS:
        pc_ = copy.copy(base_profile)
        pc_.scenario_key = sk
        results[sk] = ActuarialEngine(pc_).run()

sel   = results[sel_sc]
c_sel = SC_COLORS.get(sel_sc,"#C9A84C")

# Deskripsi skenario yang jelas
st.markdown(f"""
<div style="background:rgba(22,27,46,.7);border:1px solid {c_sel}44;
     border-radius:12px;padding:1.1rem 1.4rem;margin-bottom:1.2rem;">
    <div style="display:flex;gap:.8rem;align-items:flex-start;flex-wrap:wrap;">
        <div>
            <div style="font-family:'Cormorant Garamond',serif;font-size:1.3rem;
                 color:{c_sel};margin-bottom:.3rem;">{sel_sc}</div>
            <div style="font-size:.82rem;color:#9B97A0;line-height:1.6;max-width:600px;">
                {SC_DESC.get(sel_sc,'')}</div>
            <div style="font-size:.78rem;color:#9B97A0;margin-top:.6rem;">
                Inflasi: <b style="color:#FFA502;">{sel.eff_inflation*100:.1f}%</b> ·
                Inflasi Medis: <b style="color:#FF4757;">{sel.eff_medical_inflation*100:.1f}%</b> ·
                Return: <b style="color:#2DD4BF;">{sel.eff_annual_return*100:.1f}%</b> ·
                MC Sukses: <b style="color:{c_sel};">{sel.mc_success_rate:.0f}%</b></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

m1,m2,m3,m4 = st.columns(4)
with m1: st.metric("Skor Kesiapan", f"{sel.readiness_score:.0f}/100",
                   help="Skor 0–100 kesiapan pensiun. ≥85 = sangat siap, <40 = berisiko tinggi")
with m2: st.metric("Proyeksi Dana", rp(sel.nest_egg_at_retirement),
                   help="Estimasi total dana yang terkumpul saat usia pensiun dalam skenario ini")
with m3:
    bs = f"{sel.broke_age:.0f} thn" if sel.broke_age else "Tidak habis ✓"
    st.metric("Broke Age", bs,
              help="Usia saat dana pensiun habis. Jika kosong berarti dana cukup hingga akhir hayat — kondisi ideal")
with m4:
    sh = sel.shortfall
    st.metric("Kekurangan Dana", rp(sh) if sh>0 else "Surplus ✓",
              delta=f"Top-up: {rp(sel.monthly_top_up_needed)}/bln" if sh>0 else None,
              help="Selisih antara dana yang tersedia dan dana yang dibutuhkan. Surplus = lebih dari cukup")

# Narasi insight otomatis
if sel.broke_age and sel.broke_age < base_profile.retirement_age + 10:
    warn_txt = f"⚠️ Dalam skenario ini, dana habis hanya {sel.broke_age - base_profile.retirement_age:.0f} tahun setelah pensiun. Sangat rentan."
    warn_bg  = "rgba(255,71,87,.08)"; warn_bdr = "rgba(255,71,87,.3)"; warn_c = "#FF4757"
elif sel.mc_success_rate < 40:
    warn_txt = f"⚠️ Hanya {sel.mc_success_rate:.0f}% dari 1.000 simulasi yang berhasil. Rencana ini sangat berisiko dalam skenario tersebut."
    warn_bg  = "rgba(255,71,87,.08)"; warn_bdr = "rgba(255,71,87,.3)"; warn_c = "#FF4757"
elif sel.readiness_score >= 65:
    warn_txt = f"✓ Rencana Anda cukup tahan terhadap skenario ini. Skor {sel.readiness_score:.0f}/100 dengan MC sukses {sel.mc_success_rate:.0f}%."
    warn_bg  = "rgba(45,212,191,.07)"; warn_bdr = "rgba(45,212,191,.25)"; warn_c = "#2DD4BF"
else:
    warn_txt = f"Rencana perlu penguatan. Pertimbangkan tambahan investasi {rp(sel.monthly_top_up_needed)}/bulan untuk skenario ini."
    warn_bg  = "rgba(255,165,2,.07)"; warn_bdr = "rgba(255,165,2,.25)"; warn_c = "#FFA502"

st.markdown(f"""
<div style="background:{warn_bg};border-left:3px solid {warn_bdr};
     border-radius:0 8px 8px 0;padding:.7rem 1.1rem;margin-bottom:1.2rem;">
    <span style="color:{warn_c};font-size:.82rem;">{warn_txt}</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# Chart perbandingan semua skenario
fig_s = go.Figure()
for sk, r in results.items():
    is_sel = sk == sel_sc
    c = SC_COLORS.get(sk,"#888")
    fig_s.add_trace(go.Scatter(
        x=r.projection_ages, y=r.projection_wealth,
        mode="lines", name=sk,
        line=dict(color=c, width=2.5 if is_sel else 1.2),
        opacity=1.0 if is_sel else 0.35,
        hovertemplate=f"{sk}<br>Usia %{{x:.0f}}<br>%{{y:,.0f}}<extra></extra>"))
    if is_sel and r.broke_age:
        fig_s.add_trace(go.Scatter(
            x=[r.broke_age],y=[0],mode="markers+text",
            marker=dict(color="#FF4757",size=14,symbol="x-open",line=dict(width=3)),
            text=[f"Dana habis\nusia {r.broke_age:.0f}"],textposition="top right",
            textfont=dict(color="#FF4757",size=10),showlegend=False,name="Broke"))

fig_s.add_vline(x=base_profile.retirement_age,
                line=dict(color="#C9A84C",width=1,dash="dash"),
                annotation_text=f"Pensiun ({base_profile.retirement_age})",
                annotation_font=dict(color="#C9A84C",size=10))
fig_s.add_hline(y=0, line=dict(color="rgba(255,71,87,.4)",width=1))
fig_s.update_layout(height=420,
    paper_bgcolor="#161B2E", plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=70, b=40),
    font=dict(family="DM Sans", color="#9B97A0", size=11),
    title=dict(
        text="Perbandingan Semua Skenario"
             "<br><span style='font-size:10px;color:#5A5768;'>"
             "Garis tebal = skenario aktif · Garis tipis = skenario lain sebagai pembanding</span>",
        font=dict(family="Cormorant Garamond", size=18, color="#F0EDE8"),
        x=0.02, xanchor="left"),
    xaxis=dict(title=dict(text="Usia (tahun)",font=dict(size=10,color="#5A5768")),
               gridcolor="rgba(255,255,255,.04)",zeroline=False,tickfont=dict(size=9)),
    yaxis=dict(title=dict(text="Kekayaan (Rp)",font=dict(size=10,color="#5A5768")),
               gridcolor="rgba(255,255,255,.04)",
               zeroline=True,zerolinecolor="rgba(255,71,87,.3)",zerolinewidth=1,
               tickfont=dict(size=9),tickformat=",.0f"),
    legend=dict(orientation="h",y=-0.12,font=dict(size=10,color="#9B97A0"),bgcolor="rgba(0,0,0,0)"))
st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar":False})

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# Tabel dengan kondisional warna
tbl = []
for sk, r in results.items():
    broke_str = f"{r.broke_age:.0f} thn" if r.broke_age else "Tidak habis ✓"
    status = "🟢" if r.readiness_score >= 65 else ("🟡" if r.readiness_score >= 40 else "🔴")
    tbl.append({"":status, "Skenario":sk, "Skor":f"{r.readiness_score:.0f}/100",
                "Dana Pensiun":rp(r.nest_egg_at_retirement),
                "Broke Age":broke_str,
                "MC Sukses":f"{r.mc_success_rate:.0f}%",
                "Kekurangan":rp(r.shortfall) if r.shortfall>0 else "Surplus ✓"})

st.markdown("""
<div style="font-size:.68rem;color:#5A5768;margin-bottom:.4rem;">
    🟢 Aman (≥65)  ·  🟡 Perlu Perhatian (40–64)  ·  🔴 Berisiko (&lt;40)
</div>""", unsafe_allow_html=True)
st.dataframe(pd.DataFrame(tbl), use_container_width=True, hide_index=True)