import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv; load_dotenv()

import streamlit as st
import plotly.graph_objects as go
import numpy as np

from utils.session       import auth_guard
from engine.actuarial    import ActuarialEngine, UserProfile
from engine.data_fetcher import fetch_all_live_data
from pages._shared       import sidebar

st.set_page_config(page_title="Vantura — Dashboard", page_icon="⚜️",
                   layout="wide", initial_sidebar_state="expanded")
auth_guard()

if not st.session_state.get("user_profile"):
    email = st.session_state.get("user_email","")
    if email:
        from utils.db import load_profile
        saved = load_profile(email)
        if saved:
            st.session_state["user_profile"] = UserProfile.from_dict(saved)
        else:
            st.info("Silakan isi profil terlebih dahulu.")
            st.switch_page("pages/1_profil.py")
    else:
        st.switch_page("pages/1_profil.py")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600&family=DM+Sans:wght@300;400;500&family=JetBrains+Mono:wght@300;400&display=swap');
:root{--gold:#C9A84C;--gold-l:#E8C97A;--gold-d:rgba(201,168,76,.15);--teal:#2DD4BF;
      --bg:#0A0D14;--bg2:#111520;--card:#161B2E;--tp:#F0EDE8;--ts:#9B97A0;--tm:#5A5768;
      --bdr:rgba(201,168,76,.18);--bdrs:rgba(255,255,255,.06);
      --err:#FF4757;--ok:#2DD4BF;--warn:#FFA502;}
*,*::before,*::after{box-sizing:border-box;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"]{
    background:var(--bg)!important;color:var(--tp)!important;font-family:'DM Sans',sans-serif!important;}
[data-testid="stSidebar"]{background:var(--bg2)!important;border-right:1px solid var(--bdr)!important;}
[data-testid="stSidebar"] *{font-family:'DM Sans',sans-serif!important;color:var(--ts)!important;}
[data-testid="stHeader"]{background:transparent!important;}
h1,h2,h3{font-family:'Cormorant Garamond',serif!important;color:var(--tp)!important;}
.stButton>button{background:linear-gradient(135deg,var(--gold),#A8862E)!important;
    color:#0A0D14!important;border:none!important;border-radius:6px!important;
    font-weight:500!important;font-size:.875rem!important;padding:.6rem 1.4rem!important;
    transition:all .2s ease!important;}
.stButton>button:hover{background:linear-gradient(135deg,var(--gold-l),var(--gold))!important;
    transform:translateY(-1px)!important;box-shadow:0 4px 20px rgba(201,168,76,.30)!important;}
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

live = fetch_all_live_data()
sidebar(live)

profile: UserProfile = st.session_state["user_profile"]
engine = ActuarialEngine(profile)
res    = engine.run()

def rp(v):
    if abs(v)>=1e9: return f"Rp {v/1e9:.2f} M"
    if abs(v)>=1e6: return f"Rp {v/1e6:.1f} Jt"
    return f"Rp {v:,.0f}"

# ── Smart Alert ────────────────────────────────────────────────────────────────
if res.broke_age and res.broke_age < res.life_expectancy and not st.session_state.get("alert_shown"):
    gap = res.life_expectancy - res.broke_age
    st.markdown(f"""
    <div style="background:rgba(255,71,87,.08);border:1px solid rgba(255,71,87,.35);
         border-radius:10px;padding:1rem 1.4rem;margin-bottom:1.2rem;display:flex;
         align-items:center;gap:1rem;">
        <div style="font-size:1.5rem;">⚠️</div>
        <div>
            <div style="color:#FF4757;font-weight:600;font-size:.9rem;margin-bottom:.2rem;">
                Peringatan Dana Pensiun</div>
            <div style="color:#9B97A0;font-size:.82rem;">
                Dana diproyeksikan habis usia <b style="color:#FF4757;">{res.broke_age:.0f} tahun</b>,
                yaitu <b>{gap:.0f} tahun</b> sebelum harapan hidup ({res.life_expectancy:.1f} thn).
                Perlu tambahan investasi <b style="color:#C9A84C;">{rp(res.monthly_top_up_needed)}/bulan</b>.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Mengerti, Sembunyikan", key="dismiss_alert"):
        st.session_state.alert_shown = True
        st.rerun()
elif res.readiness_score >= 85:
    st.markdown(f"""
    <div style="background:rgba(45,212,191,.07);border:1px solid rgba(45,212,191,.25);
         border-radius:10px;padding:.9rem 1.4rem;margin-bottom:1.2rem;">
        <span style="color:#2DD4BF;font-weight:600;">✦ Excellent!</span>
        <span style="color:#9B97A0;font-size:.83rem;margin-left:.5rem;">
            Skor {res.readiness_score:.0f}/100 — Rencana pensiun Anda dalam kondisi sangat baik.
            Monte Carlo sukses rate: <b style="color:#2DD4BF;">{res.mc_success_rate:.0f}%</b></span>
    </div>
    """, unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:1.5rem;">
    <h1 style="font-family:'Cormorant Garamond',serif;font-size:2.2rem;font-weight:300;
         color:#F0EDE8;letter-spacing:.04em;line-height:1.2;margin-bottom:.3rem;">
        Dashboard <span style="color:#C9A84C;">Proyeksi</span></h1>
    <p style="color:#5A5768;font-size:.83rem;">
        Skenario: <span style="color:#C9A84C;">{profile.scenario_key}</span> ·
        Harapan Hidup: <span style="color:#C9A84C;">{res.life_expectancy:.1f} thn</span> ·
        Monte Carlo: <span style="color:{'#2DD4BF' if res.mc_success_rate>=70 else '#FF4757'};">{res.mc_success_rate:.0f}% sukses</span></p>
</div>
""", unsafe_allow_html=True)

# ── KPI ────────────────────────────────────────────────────────────────────────
m1,m2,m3,m4,m5 = st.columns(5)
with m1: st.metric("Harapan Hidup", f"{res.life_expectancy:.1f} thn",
                   help="Estimasi usia berdasarkan jenis kelamin, profesi, dan domisili (data BPS Indonesia)")
with m2:
    dv = res.nest_egg_at_retirement - res.required_nest_egg
    pct = (res.nest_egg_at_retirement / res.required_nest_egg * 100) if res.required_nest_egg > 0 else 0
    st.metric("Proyeksi Dana", rp(res.nest_egg_at_retirement),
              delta=f"{'+' if dv>=0 else ''}{rp(dv)} vs target",
              help=f"Dana yang terkumpul saat pensiun. Tercapai {pct:.0f}% dari target {rp(res.required_nest_egg)}")
with m3: st.metric("Target Dana", rp(res.required_nest_egg),
                   help="Dana minimum yang dibutuhkan agar pensiun nyaman hingga akhir hayat, dihitung dari proyeksi pengeluaran + inflasi medis")
with m4:
    bs = f"{res.broke_age:.0f} thn" if res.broke_age else "Tidak habis"
    bd = None
    if res.broke_age:
        d = res.broke_age - res.life_expectancy
        bd = f"✓ {d:.0f}thn lebih" if d>0 else f"⚠ {abs(d):.0f}thn sebelum wafat"
    st.metric("Broke Age", bs, delta=bd,
              help="Usia saat saldo dana pensiun Anda mencapai nol. Idealnya: tidak ada (dana cukup sampai akhir hayat)")
with m5:
    mc_label = "aman" if res.mc_success_rate>=70 else ("waspada" if res.mc_success_rate>=40 else "berisiko tinggi")
    st.metric("Monte Carlo", f"{res.mc_success_rate:.0f}%",
              delta=mc_label,
              help="Dari 1.000 simulasi pasar acak, berapa % yang dana Anda tidak habis. ≥70% = aman, <40% = berisiko tinggi")

# ── Insight bar ────────────────────────────────────────────────────────────────
pct_achieved = (res.nest_egg_at_retirement / res.required_nest_egg * 100) if res.required_nest_egg > 0 else 0
if res.readiness_score < 40:
    insight_col, insight_txt = "#FF4757", f"Dana hanya {pct_achieved:.0f}% dari target. Tingkatkan tabungan bulanan atau tunda usia pensiun."
elif res.readiness_score < 65:
    insight_col, insight_txt = "#FFA502", f"Dana {pct_achieved:.0f}% dari target. Tambah {rp(res.monthly_top_up_needed)}/bln untuk menutup kekurangan."
elif res.readiness_score < 85:
    insight_col, insight_txt = "#C9A84C", f"Dana {pct_achieved:.0f}% dari target. Pertahankan dan optimalkan alokasi aset."
else:
    insight_col, insight_txt = "#2DD4BF", f"Dana {pct_achieved:.0f}% dari target. Rencana Anda sangat kuat."

st.markdown(f"""
<div style="background:rgba(22,27,46,.8);border-left:3px solid {insight_col};
     border-radius:0 8px 8px 0;padding:.7rem 1.1rem;margin-bottom:1rem;">
    <span style="color:{insight_col};font-size:.8rem;font-weight:600;">💡 Insight: </span>
    <span style="color:#9B97A0;font-size:.8rem;">{insight_txt}</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# ── Charts ─────────────────────────────────────────────────────────────────────
gc, pc = st.columns([1, 2])

with gc:
    sc    = res.readiness_score
    gc_c  = res.readiness_color
    score_desc = ("Sangat baik" if sc>=85 else "Cukup baik" if sc>=65
                  else "Perlu perbaikan" if sc>=40 else "Berisiko tinggi")

    fig_g = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sc,
        number={"suffix":"/100","font":{"size":34,"color":gc_c,"family":"Cormorant Garamond"}},
        title={"text":f"<b>{res.readiness_label}</b><br><span style='font-size:10px;color:#5A5768;'>{score_desc}</span>",
               "font":{"size":12,"color":"#9B97A0"}},
        gauge={
            "axis":{"range":[0,100],"tickwidth":1,"tickcolor":"#5A5768",
                    "tickfont":{"size":9,"color":"#5A5768"},"nticks":6},
            "bar":{"color":gc_c,"thickness":.34},
            "bgcolor":"rgba(22,27,46,.8)","borderwidth":0,
            "steps":[
                {"range":[0,40],  "color":"rgba(255,71,87,.12)"},
                {"range":[40,65], "color":"rgba(255,165,2,.10)"},
                {"range":[65,85], "color":"rgba(45,212,191,.08)"},
                {"range":[85,100],"color":"rgba(45,212,191,.16)"},
            ],
            "threshold":{"line":{"color":"#C9A84C","width":2},"thickness":.85,"value":65},
        },
    ))
    fig_g.update_layout(height=270, paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="DM Sans",color="#9B97A0",size=11),
                        margin=dict(l=10,r=10,t=30,b=10))
    st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar":False})

    # Skor breakdown
    reasons = []
    if res.mc_success_rate < 40:   reasons.append(f"MC hanya {res.mc_success_rate:.0f}% sukses")
    if pct_achieved < 50:          reasons.append(f"Dana baru {pct_achieved:.0f}% dari target")
    if res.broke_age and res.broke_age < res.life_expectancy:
        reasons.append(f"Dana habis {res.life_expectancy - res.broke_age:.0f} thn lebih awal")
    if profile.savings_rate_pct < 10: reasons.append(f"Tabungan {profile.savings_rate_pct:.0f}% terlalu rendah")
    if reasons:
        bullets = "".join([f"<div style='display:flex;gap:.4rem;margin-bottom:.25rem;'><span style='color:#FF4757;'>▸</span><span>{r}</span></div>" for r in reasons])
        st.markdown(f"""
        <div style="background:rgba(255,71,87,.05);border:1px solid rgba(255,71,87,.15);
             border-radius:8px;padding:.7rem .9rem;margin-bottom:.6rem;">
            <div style="font-size:.67rem;color:#5A5768;letter-spacing:.12em;
                 text-transform:uppercase;margin-bottom:.4rem;">Kenapa skor ini?</div>
            <div style="font-size:.78rem;color:#9B97A0;">{bullets}</div>
        </div>
        """, unsafe_allow_html=True)

    # Glide path pie
    fig_pie = go.Figure(go.Pie(
        labels=["Saham","Obligasi","Emas","Kas"],
        values=[res.glide_path_equity,res.glide_path_bonds,
                res.glide_path_gold,res.glide_path_cash],
        hole=0.55,
        marker=dict(colors=["#C9A84C","#2DD4BF","#E8C97A","#5A5768"],
                    line=dict(color="#0A0D14",width=2)),
        textfont=dict(size=9,color="#F0EDE8"),
        hovertemplate="%{label}: %{value:.0f}%<extra></extra>",
    ))
    fig_pie.update_layout(
        height=200, showlegend=True,
        title=dict(text="Alokasi Aset Ideal",font=dict(size=11,color="#9B97A0"),x=0.5),
        legend=dict(orientation="h",y=-0.05,font=dict(size=8,color="#9B97A0"),
                    bgcolor="rgba(0,0,0,0)"),
        annotations=[dict(text="<b>Alokasi</b>",x=0.5,y=0.5,showarrow=False,
                         font=dict(size=11,color="#C9A84C"))],
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans",color="#9B97A0",size=11),
        margin=dict(l=10,r=10,t=30,b=10))
    st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar":False})

    st.markdown(f"""
    <div style="background:rgba(45,212,191,.06);border:1px solid rgba(45,212,191,.15);
         border-radius:8px;padding:.8rem;text-align:center;">
        <div style="font-size:.65rem;color:#5A5768;letter-spacing:.15em;
             text-transform:uppercase;margin-bottom:.3rem;">Peer Benchmark</div>
        <div style="font-size:1.2rem;font-family:'Cormorant Garamond',serif;
             color:#2DD4BF;font-weight:600;">{res.peer_percentile}</div>
        <div style="font-size:.73rem;color:#9B97A0;margin-top:.2rem;">
            Dibanding orang usia {profile.current_age} tahun di Indonesia</div>
    </div>
    """, unsafe_allow_html=True)

with pc:
    ages   = res.projection_ages
    wealth = res.projection_wealth
    ret_a  = profile.retirement_age
    life_e = res.life_expectancy
    broke  = res.broke_age

    acc_x = [a for a in ages if a <= ret_a]
    acc_y = [w for a,w in zip(ages,wealth) if a <= ret_a]
    dec_x = [a for a in ages if a > ret_a]
    dec_y = [w for a,w in zip(ages,wealth) if a > ret_a]

    fig_l = go.Figure()
    if res.mc_confidence_band_lo and res.mc_confidence_band_hi:
        band_ages = ages[:len(res.mc_confidence_band_lo)]
        fig_l.add_trace(go.Scatter(
            x=band_ages + band_ages[::-1],
            y=res.mc_confidence_band_hi + res.mc_confidence_band_lo[::-1],
            fill="toself", fillcolor="rgba(201,168,76,.06)",
            line=dict(color="rgba(0,0,0,0)"),
            name="Rentang MC (min-maks)", showlegend=True, hoverinfo="skip"))

    fig_l.add_trace(go.Scatter(x=acc_x, y=acc_y, mode="lines", name="Fase Akumulasi",
        line=dict(color="#C9A84C",width=2.5),
        fill="tozeroy", fillcolor="rgba(201,168,76,.05)",
        hovertemplate="Usia %{x:.0f}<br>%{y:,.0f}<extra>Akumulasi</extra>"))
    if dec_x:
        fig_l.add_trace(go.Scatter(x=dec_x, y=dec_y, mode="lines", name="Fase Pensiun",
            line=dict(color="#2DD4BF",width=2.5,dash="dot"),
            fill="tozeroy", fillcolor="rgba(45,212,191,.04)",
            hovertemplate="Usia %{x:.0f}<br>%{y:,.0f}<extra>Pensiun</extra>"))

    fig_l.add_vline(x=ret_a, line=dict(color="#C9A84C",width=1,dash="dash"),
                    annotation_text=f"Pensiun ({ret_a})",
                    annotation_font=dict(color="#C9A84C",size=10))
    fig_l.add_vline(x=life_e, line=dict(color="#9B97A0",width=1,dash="dot"),
                    annotation_text=f"Harapan Hidup ({life_e:.0f})",
                    annotation_font=dict(color="#9B97A0",size=10))
    if broke:
        fig_l.add_trace(go.Scatter(x=[broke],y=[0],mode="markers+text",name="Broke Age",
            marker=dict(color="#FF4757",size=13,symbol="x-open",line=dict(width=3,color="#FF4757")),
            text=[f"Dana habis\nusia {broke:.0f}"],textposition="top right",
            textfont=dict(color="#FF4757",size=10)))
    fig_l.add_hline(y=res.required_nest_egg,
                    line=dict(color="rgba(255,165,2,.4)",width=1,dash="dash"),
                    annotation_text="Target Dana Minimum",
                    annotation_font=dict(color="#FFA502",size=9))

    fig_l.update_layout(height=460,
        paper_bgcolor="#161B2E", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=70, b=40),
        font=dict(family="DM Sans", color="#9B97A0", size=11),
        title=dict(
            text="Lintasan Kekayaan & Monte Carlo Band"
                 f"<br><span style='font-size:10px;color:#5A5768;'>"
                 f"Skenario: <span style='color:#C9A84C;'>{profile.scenario_key.upper()}</span>"
                 f" · Area emas = rentang hasil 1.000 simulasi pasar</span>",
            font=dict(family="Cormorant Garamond", size=18, color="#F0EDE8"),
            x=0.02, xanchor="left"),
        xaxis=dict(title=dict(text="Usia (tahun)",font=dict(size=10,color="#5A5768")),
                   gridcolor="rgba(255,255,255,.04)",zeroline=False,tickfont=dict(size=9)),
        yaxis=dict(title=dict(text="Kekayaan (Rp)",font=dict(size=10,color="#5A5768")),
                   gridcolor="rgba(255,255,255,.04)",
                   zeroline=True,zerolinecolor="rgba(255,71,87,.3)",zerolinewidth=1,
                   tickfont=dict(size=9),tickformat=",.0f"),
        legend=dict(orientation="h",y=-0.10,font=dict(size=10,color="#9B97A0"),
                    bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_l, use_container_width=True, config={"displayModeBar":False})

# ── Bottom row metrics ─────────────────────────────────────────────────────────
st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
b1,b2,b3,b4,b5 = st.columns(5)
with b1: st.metric("Inflasi Efektif", f"{res.eff_inflation*100:.1f}%",
                   help="Inflasi umum yang dipakai dalam proyeksi, disesuaikan skenario")
with b2: st.metric("Inflasi Medis", f"{res.eff_medical_inflation*100:.1f}%",
                   help="Biaya kesehatan naik lebih cepat dari inflasi umum — komponen penting proyeksi pensiun")
with b3: st.metric("Return Investasi", f"{res.eff_annual_return*100:.1f}%/thn",
                   help="Estimasi return portofolio per tahun sesuai skenario yang dipilih")
with b4: st.metric("MC P10 Dana", rp(res.mc_p10_wealth),
                   help="Skenario terburuk ke-10%: 10% kemungkinan dana Anda hanya sebesar ini saat pensiun")
with b5: st.metric("MC P90 Dana", rp(res.mc_p90_wealth),
                   help="Skenario terbaik ke-90%: 10% kemungkinan dana Anda mencapai angka ini saat pensiun")