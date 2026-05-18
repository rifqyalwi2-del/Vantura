import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv; load_dotenv()

import streamlit as st
import plotly.graph_objects as go

from utils.session        import init_session
from engine.actuarial     import ActuarialEngine, UserProfile, PROFESSION_ADJ, DOMICILE_ADJ
from engine.data_fetcher  import fetch_all_live_data
from engine.validators    import validate_profile_inputs
from pages._shared        import sidebar

st.set_page_config(page_title="Vantura — Simulasi Cepat", page_icon="⚜️",
                   layout="wide", initial_sidebar_state="expanded")
init_session()
is_auth = st.session_state.get("authenticated", False)

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600&family=DM+Sans:wght@300;400;500&display=swap');
:root{--gold:#C9A84C;--gold-l:#E8C97A;--teal:#2DD4BF;--bg:#0A0D14;--bg2:#111520;
      --card:#161B2E;--tp:#F0EDE8;--ts:#9B97A0;--bdr:rgba(201,168,76,.18);--bdrs:rgba(255,255,255,.06);}
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
.stNumberInput>div>div>input,.stTextInput>div>div>input{background:var(--card)!important;
    color:var(--tp)!important;border:1px solid var(--bdrs)!important;border-radius:6px!important;}
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
div[data-testid="stCheckbox"] label{text-transform:none!important;
    letter-spacing:normal!important;font-size:.88rem!important;}
::-webkit-scrollbar{width:5px;}::-webkit-scrollbar-track{background:var(--bg2);}
::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:3px;}
[data-testid="stSidebarNav"],[data-testid="stSidebarNavItems"],[data-testid="stSidebarNavSeparator"],[data-testid="collapsedControl"]{display:none!important;}
</style>""", unsafe_allow_html=True)

live = fetch_all_live_data()
if is_auth:
    sidebar(live)

def rp(v):
    if abs(v)>=1e9: return f"Rp {v/1e9:.2f} M"
    if abs(v)>=1e6: return f"Rp {v/1e6:.1f} Jt"
    return f"Rp {v:,.0f}"

if not is_auth:
    st.markdown("""
    <div style="background:rgba(201,168,76,.07);border:1px solid rgba(201,168,76,.2);
         border-radius:12px;padding:1.2rem 1.6rem;margin-bottom:1.5rem;">
        <div style="font-family:'Cormorant Garamond',serif;font-size:1.3rem;
             color:#F0EDE8;margin-bottom:.4rem;">🎯 Simulasi Gratis — Tanpa Login</div>
        <p style="color:#9B97A0;font-size:.83rem;margin:0;line-height:1.6;">
            Coba kalkulator aktuaria Vantura tanpa perlu mendaftar.
            <b style="color:#C9A84C;">Daftar gratis</b> untuk analisis lengkap,
            grafik Monte Carlo, PDF laporan, dan simpan profil Anda.
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Daftar Gratis — Buka Semua Fitur", key="cta_reg"):
        st.switch_page("pages/0_login.py")

st.markdown("""
<div style="margin-bottom:2rem;">
    <h1 style="font-family:'Cormorant Garamond',serif;font-size:2.2rem;font-weight:300;
         color:#F0EDE8;letter-spacing:.04em;line-height:1.2;margin-bottom:.3rem;">
        Simulasi <span style="color:#C9A84C;">Cepat</span></h1>
    <p style="color:#5A5768;font-size:.83rem;">
        Estimasi kesiapan pensiun dalam 30 detik — tanpa akun</p>
</div>
""", unsafe_allow_html=True)

with st.expander("⚡ Input Simulasi", expanded=True):
    q1, q2, q3 = st.columns(3)
    with q1:
        q_age    = st.number_input("Usia Saat Ini", 20, 70, 35, key="q_age")
        q_ret    = st.number_input("Usia Pensiun", int(q_age)+1, 80, 60, key="q_ret")
        q_gender = st.selectbox("Gender", ["pria","wanita"],
                                format_func=lambda x:"Pria" if x=="pria" else "Wanita",
                                key="q_gen")
    with q2:
        q_sal  = st.number_input("Gaji Bulanan (Rp)", 0, value=8_000_000,
                                 step=500_000, key="q_sal")
        q_sav  = st.number_input("Total Aset (Rp)", 0, value=30_000_000,
                                 step=1_000_000, key="q_sav")
        q_rate = st.slider("% Menabung dari Gaji", 0, 80, 15, key="q_rate",
                           help="Rekomendasi: minimal 15–20% dari gaji bersih")
        rate_color = "#2DD4BF" if q_rate>=15 else ("#FFA502" if q_rate>=8 else "#FF4757")
        rate_label = "✓ Baik" if q_rate>=15 else ("⚠ Cukup" if q_rate>=8 else "✗ Rendah")
        st.markdown(f"<div style='font-size:.75rem;color:{rate_color};margin-top:-.4rem;'>"
                    f"{rate_label} · Ideal ≥15%</div>", unsafe_allow_html=True)
    with q3:
        q_prof = st.selectbox("Profesi", list(PROFESSION_ADJ.keys()), index=1, key="q_prof")
        q_dom  = st.selectbox("Domisili", list(DOMICILE_ADJ.keys()), index=0, key="q_dom")
        q_tap  = st.checkbox("Kena Tapera 2.5%", value=True, key="q_tap",
                             help="Tapera = potongan wajib 2.5% gaji untuk pekerja formal")

    vr = validate_profile_inputs(int(q_age),int(q_ret),float(q_sal),
                                 float(q_sav),float(q_rate),0.0)
    if not vr.valid:
        for e in vr.errors: st.warning(f"⚠ {e}")

    _, bc = st.columns([3,1])
    with bc:
        sim_btn = st.button("Hitung Sekarang →", use_container_width=True,
                            disabled=not vr.valid, key="sim_go")

if sim_btn and vr.valid:
    st.session_state["sim_done"] = True
    st.session_state["sim_profile"] = UserProfile(
        gender=q_gender, current_age=int(q_age), retirement_age=int(q_ret),
        monthly_salary=float(q_sal), current_savings=float(q_sav),
        savings_rate_pct=float(q_rate), profession=q_prof,
        domicile=q_dom, tapera_enabled=q_tap, scenario_key="Normal",
        inflation_rate=live["cpi"]/100, medical_inf_rate=live["medical"]/100)

if st.session_state.get("sim_done") and "sim_profile" in st.session_state:
    sp  = st.session_state["sim_profile"]
    res = ActuarialEngine(sp).run()
    sc_col = res.readiness_color
    pct = (res.nest_egg_at_retirement/res.required_nest_egg*100) if res.required_nest_egg>0 else 0

    if not is_auth:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        broke_html = (f'Broke Age: <b style="color:#FF4757;">{int(res.broke_age)} thn</b>'
                      f' — dana habis sebelum akhir hayat'
                      if res.broke_age else
                      '<b style="color:#2DD4BF;">Dana tidak habis ✓</b>')
        score_meaning = ("Sangat Siap" if res.readiness_score>=85 else
                         "Cukup Siap" if res.readiness_score>=65 else
                         "Perlu Perhatian" if res.readiness_score>=40 else "Berisiko Tinggi")
        st.markdown(f"""
        <div style="text-align:center;padding:2rem;background:#161B2E;
             border:1px solid rgba(255,255,255,.06);border-radius:14px;margin-bottom:1.2rem;">
            <div style="font-size:.7rem;letter-spacing:.2em;text-transform:uppercase;
                 color:#5A5768;margin-bottom:.6rem;">RETIREMENT READINESS SCORE</div>
            <div style="font-family:'Cormorant Garamond',serif;font-size:5rem;
                 font-weight:600;color:{sc_col};line-height:1;">{res.readiness_score:.0f}</div>
            <div style="font-size:1.1rem;color:{sc_col};margin-top:.3rem;">
                {res.readiness_label} — {score_meaning}</div>
            <div style="font-size:.82rem;color:#9B97A0;margin-top:.8rem;">
                Dana tercapai: <b>{pct:.0f}%</b> dari target ·
                Harapan Hidup: <b>{res.life_expectancy:.1f} thn</b></div>
            <div style="font-size:.82rem;color:#9B97A0;margin-top:.3rem;">{broke_html}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="background:rgba(201,168,76,.07);border:1px solid rgba(201,168,76,.2);
             border-radius:12px;padding:1.3rem 1.6rem;text-align:center;">
            <div style="font-family:'Cormorant Garamond',serif;font-size:1.2rem;
                 color:#F0EDE8;margin-bottom:.5rem;">🔒 Buka Analisis Lengkap</div>
            <div style="color:#9B97A0;font-size:.82rem;margin-bottom:1rem;">
                Grafik proyeksi · Monte Carlo 1.000 simulasi · Peer benchmarking · PDF laporan
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("✨ Daftar Gratis Sekarang", key="cta_reg2"):
            st.switch_page("pages/0_login.py")

    else:
        m1,m2,m3,m4 = st.columns(4)
        with m1: st.metric("Readiness Score", f"{res.readiness_score:.0f}/100",
                           help="Skor kesiapan pensiun 0–100. ≥65 = cukup siap, <40 = berisiko")
        with m2:
            dv = res.nest_egg_at_retirement-res.required_nest_egg
            st.metric("Proyeksi Dana", rp(res.nest_egg_at_retirement),
                      delta=f"{'+' if dv>=0 else ''}{rp(dv)}",
                      help=f"Tercapai {pct:.0f}% dari target {rp(res.required_nest_egg)}")
        with m3:
            bs = f"{res.broke_age:.0f} thn" if res.broke_age else "Tidak habis ✓"
            st.metric("Broke Age", bs,
                      help="Usia saat dana habis. Idealnya tidak ada (kosong = aman)")
        with m4:
            mc_lbl = "aman" if res.mc_success_rate>=70 else "berisiko"
            st.metric("Monte Carlo", f"{res.mc_success_rate:.0f}%",
                      delta=mc_lbl,
                      help="% dari 1.000 simulasi pasar yang berhasil. ≥70% = aman")

        # Insight narasi
        if res.readiness_score < 40:
            ins_c = "#FF4757"
            ins_t = f"Dana baru {pct:.0f}% dari target. Pertimbangkan menabung lebih banyak atau menunda usia pensiun."
        elif res.readiness_score < 65:
            ins_c = "#FFA502"
            ins_t = f"Dana {pct:.0f}% dari target. Tambah investasi {rp(res.monthly_top_up_needed)}/bulan untuk menutup kekurangan."
        else:
            ins_c = "#2DD4BF"
            ins_t = f"Dana {pct:.0f}% dari target. Rencana sudah cukup kuat. Pertahankan konsistensi menabung."

        st.markdown(f"""
        <div style="background:rgba(22,27,46,.8);border-left:3px solid {ins_c};
             border-radius:0 8px 8px 0;padding:.7rem 1.1rem;margin-bottom:1rem;margin-top:.5rem;">
            <span style="color:{ins_c};font-size:.8rem;font-weight:600;">💡 </span>
            <span style="color:#9B97A0;font-size:.8rem;">{ins_t}</span>
        </div>
        """, unsafe_allow_html=True)

        ages  = res.projection_ages
        wealth= res.projection_wealth
        ret_a = sp.retirement_age
        acc_x = [a for a in ages if a<=ret_a]
        acc_y = [w for a,w in zip(ages,wealth) if a<=ret_a]
        dec_x = [a for a in ages if a>ret_a]
        dec_y = [w for a,w in zip(ages,wealth) if a>ret_a]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=acc_x, y=acc_y, mode="lines", name="Fase Akumulasi",
            line=dict(color="#C9A84C",width=2.5),
            fill="tozeroy", fillcolor="rgba(201,168,76,.06)",
            hovertemplate="Usia %{x:.0f}<br>%{y:,.0f}<extra>Akumulasi</extra>"))
        if dec_x:
            fig.add_trace(go.Scatter(x=dec_x, y=dec_y, mode="lines", name="Fase Pensiun",
                line=dict(color="#2DD4BF",width=2.5,dash="dot"),
                fill="tozeroy", fillcolor="rgba(45,212,191,.04)",
                hovertemplate="Usia %{x:.0f}<br>%{y:,.0f}<extra>Pensiun</extra>"))
        fig.add_vline(x=ret_a, line=dict(color="#C9A84C",width=1,dash="dash"),
                      annotation_text=f"Pensiun ({ret_a})",
                      annotation_font=dict(color="#C9A84C",size=10))
        if res.broke_age:
            fig.add_trace(go.Scatter(x=[res.broke_age],y=[0],mode="markers+text",
                name="Broke Age",
                marker=dict(color="#FF4757",size=13,symbol="x-open",line=dict(width=3)),
                text=[f"Dana habis\nusia {res.broke_age:.0f}"],textposition="top right",
                textfont=dict(color="#FF4757",size=10)))
        fig.update_layout(height=380,
            paper_bgcolor="#161B2E", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10,r=10,t=65,b=10),
            font=dict(family="DM Sans",color="#9B97A0",size=11),
            title=dict(
                text="Proyeksi Lintasan Kekayaan"
                     f"<br><span style='font-size:10px;color:#5A5768;'>"
                     f"Garis emas = akumulasi · Garis teal = penarikan saat pensiun</span>",
                font=dict(family="Cormorant Garamond",size=18,color="#F0EDE8"),
                x=0.02, xanchor="left"),
            xaxis=dict(title="Usia (tahun)",titlefont=dict(size=10,color="#5A5768"),
                       gridcolor="rgba(255,255,255,.04)",zeroline=False,tickfont=dict(size=9)),
            yaxis=dict(title="Kekayaan (Rp)",titlefont=dict(size=10,color="#5A5768"),
                       gridcolor="rgba(255,255,255,.04)",zeroline=True,
                       zerolinecolor="rgba(255,71,87,.3)",zerolinewidth=1,
                       tickfont=dict(size=9),tickformat=",.0f"),
            legend=dict(orientation="h",y=-0.10,font=dict(size=10,color="#9B97A0"),
                        bgcolor="rgba(0,0,0,0)"),
)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        if st.button("💾 Simpan & Analisis Lengkap →", key="save_sim"):
            st.session_state["user_profile"] = sp
            st.switch_page("pages/2_dashboard.py")

st.markdown("""
<div style="text-align:center;margin-top:3rem;color:#2A2A3E;font-size:.7rem;letter-spacing:.08em;">
    VANTURA v2.0 © 2025 · Simulasi aktuaria · Bukan saran investasi resmi
</div>""", unsafe_allow_html=True)