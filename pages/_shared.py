"""Shared sidebar component."""
import streamlit as st
from utils.session import logout

NAV = [
    ("📋", "Profil & Input",    "pages/1_profil.py"),
    ("📊", "Dashboard & Skor", "pages/2_dashboard.py"),
    ("⚡", "Stress Test",       "pages/3_stress_test.py"),
    ("👥", "Peer Benchmark",   "pages/4_benchmark.py"),
    ("📄", "Unduh Laporan",    "pages/5_report.py"),
    ("⚙️", "Pengaturan",       "pages/6_settings.py"),
    ("🎯", "Simulasi Cepat",   "pages/7_simulator.py"),
]

def sidebar(live_data: dict | None = None):
    # Sembunyikan default Streamlit page navigation — cukup inject di sini sekali
    st.markdown("""
    <style>
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavItems"],
    [data-testid="stSidebarNavSeparator"],
    [data-testid="collapsedControl"] { display:none!important; }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
        <div style="padding:1.4rem 0 1rem;">
            <div style="font-family:'Cormorant Garamond',serif;font-size:1.6rem;
                 font-weight:600;letter-spacing:.13em;
                 background:linear-gradient(135deg,#C9A84C,#E8C97A);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                 background-clip:text;">VANTURA</div>
            <div style="font-size:.6rem;letter-spacing:.22em;color:#5A5768;margin-top:3px;">
                WEALTH INTELLIGENCE v2.0</div>
        </div>
        <hr style="border:none;border-top:1px solid rgba(201,168,76,.15);margin-bottom:1.2rem;">
        """, unsafe_allow_html=True)

        nm = st.session_state.get("user_name","Pengguna")
        email = st.session_state.get("user_email","")
        st.markdown(f"""
        <div style="font-size:.78rem;color:#9B97A0;margin-bottom:.2rem;">Selamat datang,</div>
        <div style="font-size:.95rem;color:#F0EDE8;font-weight:500;margin-bottom:.2rem;">{nm}</div>
        <div style="font-size:.7rem;color:#5A5768;margin-bottom:1.4rem;">{email[:20]}{'...' if len(email)>20 else ''}</div>
        """, unsafe_allow_html=True)

        for icon, label, page in NAV:
            if st.button(f"{icon}  {label}", key=f"nav_{page}",
                         use_container_width=True):
                st.switch_page(page)

        if live_data:
            st.markdown(f"""
            <div style="background:rgba(22,27,46,.8);border:1px solid rgba(201,168,76,.13);
                 border-radius:10px;padding:.9rem;margin-top:1rem;margin-bottom:.8rem;">
                <div style="font-size:.62rem;letter-spacing:.18em;text-transform:uppercase;
                     color:#5A5768;margin-bottom:.7rem;">LIVE DATA INDONESIA</div>
                <div style="display:flex;justify-content:space-between;margin-bottom:.4rem;">
                    <span style="color:#9B97A0;font-size:.76rem;">CPI ({live_data.get('year','?')})</span>
                    <span style="color:#C9A84C;font-weight:500;font-size:.82rem;">{live_data.get('cpi',5):.1f}%</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:.4rem;">
                    <span style="color:#9B97A0;font-size:.76rem;">Inflasi Medis</span>
                    <span style="color:#FF4757;font-weight:500;font-size:.82rem;">{live_data.get('medical',10):.1f}%</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:.4rem;">
                    <span style="color:#9B97A0;font-size:.76rem;">GDP Growth</span>
                    <span style="color:#2DD4BF;font-weight:500;font-size:.82rem;">{live_data.get('gdp',5):.1f}%</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:.4rem;">
                    <span style="color:#9B97A0;font-size:.76rem;">BI Rate</span>
                    <span style="color:#C9A84C;font-weight:500;font-size:.82rem;">{live_data.get('bi_rate',6.25):.2f}%</span>
                </div>
                <div style="display:flex;justify-content:space-between;">
                    <span style="color:#9B97A0;font-size:.76rem;">Emas/gram</span>
                    <span style="color:#E8C97A;font-weight:500;font-size:.82rem;">Rp {live_data.get('gold_idr',1100000):,.0f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,.05);margin:.8rem 0;'>",
                    unsafe_allow_html=True)
        if st.button("⎋  Keluar", key="sidebar_logout", use_container_width=True):
            logout()