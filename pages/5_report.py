import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv; load_dotenv()

from datetime import datetime
import streamlit as st

from utils.session        import auth_guard
from engine.actuarial     import ActuarialEngine, UserProfile
from engine.data_fetcher  import fetch_all_live_data
from engine.pdf_generator import generate_pdf
from pages._shared        import sidebar

st.set_page_config(page_title="Vantura — Laporan", page_icon="⚜️",
                   layout="wide", initial_sidebar_state="expanded")
auth_guard()
if "user_profile" not in st.session_state:
    st.switch_page("pages/1_profil.py")

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
[data-testid="stMetricValue"]{color:var(--gold)!important;
    font-family:'Cormorant Garamond',serif!important;font-size:1.9rem!important;}
[data-testid="stMetricLabel"]{color:var(--ts)!important;font-size:.74rem!important;
    letter-spacing:.08em!important;text-transform:uppercase!important;}
.stMetric{background:var(--card)!important;border:1px solid var(--bdrs)!important;
    border-radius:10px!important;padding:1rem 1.2rem!important;}
::-webkit-scrollbar{width:5px;}::-webkit-scrollbar-track{background:var(--bg2);}
::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:3px;}
</style>""", unsafe_allow_html=True)

def rp(v):
    if abs(v)>=1e9: return f"Rp {v/1e9:.2f} M"
    if abs(v)>=1e6: return f"Rp {v/1e6:.1f} Jt"
    return f"Rp {v:,.0f}"

live = fetch_all_live_data()
sidebar(live)

profile: UserProfile = st.session_state["user_profile"]
with st.spinner("Menghitung proyeksi final…"):
    res = ActuarialEngine(profile).run()

st.markdown("""
<div style="margin-bottom:2rem;">
    <h1 style="font-family:'Cormorant Garamond',serif;font-size:2.2rem;font-weight:300;
         color:#F0EDE8;letter-spacing:.04em;line-height:1.2;margin-bottom:.3rem;">
        Laporan <span style="color:#C9A84C;">Eksekutif PDF</span></h1>
    <p style="color:#5A5768;font-size:.83rem;">
        Dokumen A4 lengkap · Skor · Proyeksi · Glide Path · 6 Rekomendasi Konkrit</p>
</div>
""", unsafe_allow_html=True)

m1,m2,m3,m4 = st.columns(4)
with m1: st.metric("Readiness Score", f"{res.readiness_score:.0f}/100",
                   help="Skor 0–100 kesiapan pensiun Anda. ≥85 = sangat siap")
with m2: st.metric("Proyeksi Dana", rp(res.nest_egg_at_retirement),
                   help="Total dana saat pensiun. Bandingkan dengan target di sebelah kanan")
with m3:
    bs = f"{res.broke_age:.0f} thn" if res.broke_age else "Tidak habis ✓"
    st.metric("Broke Age", bs,
              help="Usia saat dana habis. Idealnya kosong (tidak ada) — berarti dana cukup hingga akhir hayat")
with m4: st.metric("Monte Carlo", f"{res.mc_success_rate:.0f}% sukses",
                   help="Dari 1.000 simulasi pasar acak, berapa % yang dana Anda tidak habis. ≥70% = aman")

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

dl_c, info_c = st.columns([2, 3])

with dl_c:
    sc_color = res.readiness_color
    mc_color = "#2DD4BF" if res.mc_success_rate >= 70 else "#FF4757"
    st.markdown(f"""
    <div style="background:#161B2E;border:1px solid rgba(201,168,76,.25);
         border-radius:12px;padding:1.4rem 1.5rem 1rem;">
        <div style="font-size:.62rem;color:#5A5768;letter-spacing:.18em;
             text-transform:uppercase;margin-bottom:.5rem;">Dokumen Aktuaria</div>
        <div style="font-family:'Cormorant Garamond',serif;font-size:1.35rem;
             color:#F0EDE8;margin-bottom:.25rem;">Generate & Unduh PDF</div>
        <div style="font-size:.76rem;color:#5A5768;margin-bottom:.8rem;">
            Dibuat di memori &middot; Tidak tersimpan di server &middot; Format A4</div>
        <div style="display:flex;gap:1.2rem;flex-wrap:wrap;">
            <div style="font-size:.76rem;color:#9B97A0;">
                <span style="color:{sc_color};">●</span> Skor {res.readiness_score:.0f}/100</div>
            <div style="font-size:.76rem;color:#9B97A0;">
                <span style="color:{mc_color};">●</span> MC {res.mc_success_rate:.0f}%</div>
            <div style="font-size:.76rem;color:#9B97A0;">
                <span style="color:#9B97A0;">●</span> {profile.scenario_key}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    try:
        with st.spinner("Membuat PDF…"):
            pdf_bytes = generate_pdf(profile, res)
        fname = (f"Vantura_{profile.name.replace(' ','_') or 'Report'}_"
                 f"{datetime.now().strftime('%Y%m%d_%H%M')}.pdf")
        st.download_button(label="⬇  Unduh Laporan PDF", data=pdf_bytes,
                           file_name=fname, mime="application/pdf",
                           use_container_width=True)
        st.markdown(
            "<div style='background:rgba(45,212,191,.08);border:1px solid rgba(45,212,191,.25);"
            "border-radius:8px;padding:.65rem 1rem;font-size:.82rem;color:#2DD4BF;"
            "text-align:center;margin-top:.4rem;'>✓ Laporan siap diunduh</div>",
            unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Gagal membuat PDF: {e}")

with info_c:
    broke_txt = f"{res.broke_age:.0f} tahun" if res.broke_age else "Tidak terdeteksi ✓"
    st.markdown(f"""
    <div style="background:#161B2E;border:1px solid rgba(255,255,255,.06);
         border-radius:12px;padding:1.4rem 1.5rem;">
        <div style="font-size:.62rem;color:#5A5768;letter-spacing:.18em;
             text-transform:uppercase;margin-bottom:.5rem;">Konten Laporan</div>
        <div style="font-family:'Cormorant Garamond',serif;font-size:1.35rem;
             color:#F0EDE8;margin-bottom:.8rem;">Isi Laporan v2.0</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:.55rem .8rem;margin-bottom:1rem;">
            <div style="display:flex;align-items:center;gap:.5rem;">
                <span style="color:#C9A84C;font-size:.7rem;">✦</span>
                <span style="font-size:.8rem;color:#9B97A0;">Skor kesiapan {res.readiness_score:.0f}/100 — {res.readiness_label}</span>
            </div>
            <div style="display:flex;align-items:center;gap:.5rem;">
                <span style="color:#C9A84C;font-size:.7rem;">✦</span>
                <span style="font-size:.8rem;color:#9B97A0;">Profil aktuaria lengkap</span>
            </div>
            <div style="display:flex;align-items:center;gap:.5rem;">
                <span style="color:#C9A84C;font-size:.7rem;">✦</span>
                <span style="font-size:.8rem;color:#9B97A0;">Proyeksi dana & Broke Age ({broke_txt})</span>
            </div>
            <div style="display:flex;align-items:center;gap:.5rem;">
                <span style="color:#C9A84C;font-size:.7rem;">✦</span>
                <span style="font-size:.8rem;color:#9B97A0;">Monte Carlo {res.mc_success_rate:.0f}% dari 1.000 simulasi</span>
            </div>
            <div style="display:flex;align-items:center;gap:.5rem;">
                <span style="color:#C9A84C;font-size:.7rem;">✦</span>
                <span style="font-size:.8rem;color:#9B97A0;">Glide path alokasi aset ideal</span>
            </div>
            <div style="display:flex;align-items:center;gap:.5rem;">
                <span style="color:#C9A84C;font-size:.7rem;">✦</span>
                <span style="font-size:.8rem;color:#9B97A0;">Peer benchmarking vs sebaya</span>
            </div>
            <div style="display:flex;align-items:center;gap:.5rem;">
                <span style="color:#C9A84C;font-size:.7rem;">✦</span>
                <span style="font-size:.8rem;color:#9B97A0;">6 rekomendasi tindakan konkrit</span>
            </div>
            <div style="display:flex;align-items:center;gap:.5rem;">
                <span style="color:#C9A84C;font-size:.7rem;">✦</span>
                <span style="font-size:.8rem;color:#9B97A0;">Skenario: {profile.scenario_key}</span>
            </div>
        </div>
        <div style="padding-top:.8rem;border-top:1px solid rgba(255,255,255,.05);
             font-size:.73rem;color:#5A5768;">
            Format A4 · ReportLab PDF · Dicetak {datetime.now().strftime("%d %b %Y")} ·
            Bukan saran investasi resmi</div>
    </div>
    """, unsafe_allow_html=True)