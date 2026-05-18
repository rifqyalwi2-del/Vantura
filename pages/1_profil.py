import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv; load_dotenv()

import streamlit as st
from utils.session         import auth_guard, init_session
from utils.db              import save_profile, load_profile, save_history_entry
from engine.actuarial      import UserProfile, PROFESSION_ADJ, DOMICILE_ADJ
from engine.data_fetcher   import fetch_all_live_data
from engine.validators     import validate_profile_inputs
from pages._shared         import sidebar

st.set_page_config(page_title="Vantura — Profil", page_icon="⚜️",
                   layout="wide", initial_sidebar_state="expanded")
auth_guard()

CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600&family=DM+Sans:wght@300;400;500&display=swap');
:root{--gold:#C9A84C;--gold-l:#E8C97A;--gold-d:rgba(201,168,76,.15);--teal:#2DD4BF;
      --bg:#0A0D14;--bg2:#111520;--card:#161B2E;--tp:#F0EDE8;--ts:#9B97A0;--tm:#5A5768;
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
    font-weight:500!important;font-size:.875rem!important;padding:.6rem 1.4rem!important;
    transition:all .2s ease!important;}
.stButton>button:hover{background:linear-gradient(135deg,var(--gold-l),var(--gold))!important;
    transform:translateY(-1px)!important;box-shadow:0 4px 20px rgba(201,168,76,.30)!important;}
.stTextInput>div>div>input,.stNumberInput>div>div>input{
    background:var(--card)!important;color:var(--tp)!important;
    border:1px solid var(--bdrs)!important;border-radius:6px!important;}
.stTextInput>div>div>input:focus,.stNumberInput>div>div>input:focus{
    border-color:var(--gold)!important;box-shadow:0 0 0 2px var(--gold-d)!important;}
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
.step-badge{display:inline-block;background:var(--gold);color:#0A0D14;border-radius:50%;
    width:24px;height:24px;text-align:center;line-height:24px;
    font-size:.75rem;font-weight:700;margin-right:.5rem;}
</style>"""
st.markdown(CSS, unsafe_allow_html=True)

with st.spinner("Memuat data ekonomi…"):
    live = fetch_all_live_data()
sidebar(live)

email = st.session_state.get("user_email","")
saved = load_profile(email) if email else None
prev  = UserProfile.from_dict(saved) if saved else UserProfile()

def rp(v):
    if abs(v)>=1e9: return f"Rp {v/1e9:.1f} M"
    if abs(v)>=1e6: return f"Rp {v/1e6:.1f} Jt"
    return f"Rp {v:,.0f}"

# ── Onboarding banner ──────────────────────────────────────────────────────────
if not st.session_state.get("onboarded") and not saved:
    st.markdown("""
    <div style="background:rgba(201,168,76,.07);border:1px solid rgba(201,168,76,.2);
         border-radius:12px;padding:1.2rem 1.6rem;margin-bottom:1.5rem;">
        <div style="font-family:'Cormorant Garamond',serif;font-size:1.2rem;
             color:#F0EDE8;margin-bottom:.5rem;">🎉 Selamat datang di Vantura!</div>
        <p style="color:#9B97A0;font-size:.84rem;line-height:1.7;margin:0;">
            Isi profil finansial Anda untuk mendapatkan proyeksi aktuaria personal.
            Proses hanya ~2 menit dan data tersimpan aman.
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Mengerti, Mulai Isi Profil!", key="onboard_ok"):
        st.session_state.onboarded = True
        st.rerun()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:2rem;">
    <h1 style="font-family:'Cormorant Garamond',serif;font-size:2.4rem;font-weight:300;
         color:#F0EDE8;letter-spacing:.04em;line-height:1.2;margin-bottom:.3rem;">
        Profil <span style="color:#C9A84C;">Finansial</span></h1>
    <p style="color:#5A5768;font-size:.84rem;letter-spacing:.04em;">
        CPI Indonesia {live['year']}: <span style="color:#C9A84C;">{live['cpi']:.1f}%</span> ·
        Inflasi Medis est.: <span style="color:#FF4757;">{live['medical']:.1f}%</span> ·
        Emas: <span style="color:#E8C97A;">Rp {live['gold_idr']:,.0f}/gr</span></p>
</div>
""", unsafe_allow_html=True)

# ── Form ───────────────────────────────────────────────────────────────────────
with st.expander("⚙️  Data Lengkap Profil Saya", expanded=True):
    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

    form_col, summary_col = st.columns([3, 1])

    with form_col:
        st.markdown("""
        <div style="display:flex;gap:.6rem;margin-bottom:1.2rem;align-items:center;">
            <div style="display:flex;align-items:center;gap:.4rem;">
                <span style="background:#C9A84C;color:#0A0D14;border-radius:50%;
                     width:22px;height:22px;text-align:center;line-height:22px;
                     font-size:.72rem;font-weight:700;">1</span>
                <span style="font-size:.78rem;color:#C9A84C;font-weight:500;">Demografi</span>
            </div>
            <div style="height:1px;flex:1;background:rgba(255,255,255,.08);"></div>
            <div style="display:flex;align-items:center;gap:.4rem;">
                <span style="background:#C9A84C;color:#0A0D14;border-radius:50%;
                     width:22px;height:22px;text-align:center;line-height:22px;
                     font-size:.72rem;font-weight:700;">2</span>
                <span style="font-size:.78rem;color:#C9A84C;font-weight:500;">Finansial</span>
            </div>
            <div style="height:1px;flex:1;background:rgba(255,255,255,.08);"></div>
            <div style="display:flex;align-items:center;gap:.4rem;">
                <span style="background:#C9A84C;color:#0A0D14;border-radius:50%;
                     width:22px;height:22px;text-align:center;line-height:22px;
                     font-size:.72rem;font-weight:700;">3</span>
                <span style="font-size:.78rem;color:#C9A84C;font-weight:500;">Risiko</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        r1a, r1b = st.columns(2)
        with r1a:
            name_i   = st.text_input("Nama Lengkap",
                                     value=prev.name or st.session_state.get("user_name",""),
                                     placeholder="Nama Anda")
        with r1b:
            gender_i = st.selectbox("Jenis Kelamin", ["pria","wanita"],
                                    index=0 if prev.gender=="pria" else 1,
                                    format_func=lambda x:"Pria" if x=="pria" else "Wanita")

        r2a, r2b = st.columns(2)
        with r2a:
            cur_age_i = st.number_input("Usia Saat Ini (tahun)", 18, 75, prev.current_age)
        with r2b:
            ret_age_i = st.number_input("Target Usia Pensiun", int(cur_age_i)+1, 80,
                                        prev.retirement_age)

        st.markdown("<div style='height:1px;background:rgba(255,255,255,.06);margin:.6rem 0 .8rem;'></div>",
                    unsafe_allow_html=True)

        r3a, r3b = st.columns(2)
        with r3a:
            salary_i = st.number_input("Gaji / Penghasilan Bulanan (Rp)",
                                       0, value=int(prev.monthly_salary), step=500_000)
        with r3b:
            savings_i = st.number_input("Total Aset / Tabungan (Rp)",
                                        0, value=int(prev.current_savings), step=1_000_000)

        r4a, r4b = st.columns(2)
        with r4a:
            srate_i = st.slider("% Menabung dari Gaji", 0, 80, int(prev.savings_rate_pct),
                                help="Rekomendasi minimal 15–20% dari gaji bersih")
        with r4b:
            sandwich_i = st.number_input("Tanggungan Keluarga (Rp/bln)",
                                         0, value=int(prev.sandwich_monthly), step=100_000,
                                         help="Biaya menanggung orang tua/keluarga lain di luar rumah tangga inti (sandwich generation)")

        st.markdown("<div style='height:1px;background:rgba(255,255,255,.06);margin:.6rem 0 .8rem;'></div>",
                    unsafe_allow_html=True)

        prof_list = list(PROFESSION_ADJ.keys())
        dom_list  = list(DOMICILE_ADJ.keys())
        r5a, r5b  = st.columns(2)
        with r5a:
            prof_i = st.selectbox("Profesi", prof_list,
                                  index=prof_list.index(prev.profession) if prev.profession in prof_list else 1)
        with r5b:
            dom_i  = st.selectbox("Domisili", dom_list,
                                  index=dom_list.index(prev.domicile) if prev.domicile in dom_list else 0)

        tapera_i = st.checkbox("Terkena potongan Tapera 2.5%", value=prev.tapera_enabled,
                               help="Tapera = Tabungan Perumahan Rakyat, potongan wajib 2.5% dari gaji untuk pekerja formal")

    with summary_col:
        adj        = PROFESSION_ADJ.get(prof_i, 0) + DOMICILE_ADJ.get(dom_i, 0)
        base       = 72.0 if gender_i == "pria" else 76.0
        est_le     = base + adj
        col_le     = "#2DD4BF" if adj >= 0 else "#FFA502"
        tapera_c   = salary_i * 0.025 if tapera_i else 0
        take_home  = max(0, salary_i - tapera_c - sandwich_i)
        net_save   = take_home * (srate_i / 100)
        rate_color = "#2DD4BF" if srate_i >= 15 else ("#FFA502" if srate_i >= 8 else "#FF4757")
        rate_label = "Baik ✓" if srate_i >= 15 else ("Cukup ⚠" if srate_i >= 8 else "Rendah ✗")
        years_left = max(0, int(ret_age_i) - int(cur_age_i))
        bar_w      = min(100, srate_i / 20 * 100)
        st.markdown(f"""
        <div style="margin-top:2.8rem;background:rgba(14,18,32,.9);
             border:1px solid rgba(201,168,76,.2);border-radius:14px;
             padding:1.3rem 1.2rem;display:flex;flex-direction:column;gap:.9rem;">
            <div style="font-size:.6rem;color:#5A5768;letter-spacing:.2em;
                 text-transform:uppercase;">Ringkasan Profil</div>
            <div style="display:flex;flex-direction:column;gap:.5rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;
                     padding:.5rem .7rem;background:rgba(45,212,191,.05);
                     border-radius:8px;border:1px solid rgba(45,212,191,.1);">
                    <span style="font-size:.72rem;color:#5A5768;">Harapan Hidup</span>
                    <span style="font-family:'Cormorant Garamond',serif;font-size:1.1rem;
                         color:{col_le};font-weight:600;">{est_le:.1f} thn</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;
                     padding:.5rem .7rem;background:rgba(201,168,76,.05);
                     border-radius:8px;border:1px solid rgba(201,168,76,.1);">
                    <span style="font-size:.72rem;color:#5A5768;">Waktu tersisa</span>
                    <span style="font-family:'Cormorant Garamond',serif;font-size:1.1rem;
                         color:#C9A84C;font-weight:600;">{years_left} thn</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;
                     padding:.5rem .7rem;background:rgba(22,27,46,.8);
                     border-radius:8px;border:1px solid rgba(255,255,255,.06);">
                    <span style="font-size:.72rem;color:#5A5768;">Tabungan/bln</span>
                    <span style="font-family:'Cormorant Garamond',serif;font-size:1.05rem;
                         color:{rate_color};font-weight:600;">{rp(net_save)}</span>
                </div>
            </div>
            <div style="padding:.7rem;background:rgba(22,27,46,.6);border-radius:8px;
                 border:1px solid rgba(255,255,255,.05);">
                <div style="display:flex;justify-content:space-between;margin-bottom:.4rem;">
                    <span style="font-size:.65rem;color:#5A5768;">% Menabung</span>
                    <span style="font-size:.65rem;color:{rate_color};">{rate_label}</span>
                </div>
                <div style="height:5px;background:rgba(255,255,255,.06);border-radius:3px;overflow:hidden;">
                    <div style="height:100%;width:{bar_w:.0f}%;
                         background:{rate_color};border-radius:3px;"></div>
                </div>
                <div style="font-size:.67rem;color:#5A5768;margin-top:.35rem;">
                    Anda {srate_i}% &nbsp;·&nbsp; Ideal ≥ 15%</div>
            </div>
            <div style="font-size:.68rem;color:#5A5768;line-height:1.6;
                 border-top:1px solid rgba(255,255,255,.05);padding-top:.6rem;">
                Adj harapan hidup:
                <span style="color:{col_le};">{adj:+.1f} thn</span><br>
                Dasar: pria 72 &middot; wanita 76 thn (BPS)
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

    vr = validate_profile_inputs(
        int(cur_age_i), int(ret_age_i), float(salary_i),
        float(savings_i), float(srate_i), float(sandwich_i))
    if not vr.valid:
        for e in vr.errors:
            st.warning(f"⚠ {e}")

    _, bc = st.columns([3, 1])
    with bc:
        go_btn = st.button("Lihat Hasil Proyeksi →",
                           use_container_width=True,
                           disabled=not vr.valid, key="go_proj")

if go_btn and vr.valid:
    p = UserProfile(
        name=name_i, gender=gender_i,
        current_age=int(cur_age_i), retirement_age=int(ret_age_i),
        monthly_salary=float(salary_i), current_savings=float(savings_i),
        savings_rate_pct=float(srate_i), profession=prof_i,
        domicile=dom_i, sandwich_monthly=float(sandwich_i),
        tapera_enabled=tapera_i, scenario_key="Normal",
        inflation_rate=live["cpi"]/100, medical_inf_rate=live["medical"]/100,
    )
    st.session_state["user_profile"] = p
    if email:
        save_profile(email, p.to_dict())
        save_history_entry(email, {"scenario":"Normal","salary":float(salary_i),
            "savings":float(savings_i),"age":int(cur_age_i),"ret_age":int(ret_age_i)})
    st.switch_page("pages/2_dashboard.py")

p_now = st.session_state.get("user_profile")
if p_now:
    with st.expander("🕒 Lihat Data Simulasi Sebelumnya"):
        st.markdown(f"""
        <div style="font-size:.9rem;color:#9B97A0;">
            Gaji: <b>Rp {p_now.monthly_salary:,.0f}</b> &nbsp;|&nbsp;
            Tabungan: <b>{p_now.savings_rate_pct}%</b> &nbsp;|&nbsp;
            Target Pensiun: <b>{p_now.retirement_age} tahun</b>
        </div>""", unsafe_allow_html=True)