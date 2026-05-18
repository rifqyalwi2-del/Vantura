"""
pages/0_login.py
Login page — clean premium design, zero orphaned divs.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv; load_dotenv()

import streamlit as st
from utils.session import init_session, set_authenticated
from utils.auth    import register_user, login_step1, login_step2
from utils.logger  import get_logger

log = get_logger("login")

st.set_page_config(page_title="Vantura — Login", page_icon="⚜️",
                   layout="centered", initial_sidebar_state="collapsed")
init_session()

if st.session_state.get("authenticated"):
    st.switch_page("pages/2_dashboard.py")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=DM+Sans:wght@300;400;500&display=swap');
:root{--gold:#C9A84C;--gold-l:#E8C97A;--teal:#2DD4BF;--bg:#0A0D14;--bg2:#111520;
      --card:#161B2E;--tp:#F0EDE8;--ts:#9B97A0;--tm:#5A5768;
      --bdr:rgba(201,168,76,.18);--bdrs:rgba(255,255,255,.06);}
*,*::before,*::after{box-sizing:border-box;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"]{
    background:var(--bg)!important;color:var(--tp)!important;
    font-family:'DM Sans',sans-serif!important;}
[data-testid="stSidebarNav"],[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavSeparator"],[data-testid="collapsedControl"],
[data-testid="stSidebar"]{display:none!important;}
[data-testid="stHeader"]{background:transparent!important;}
#MainMenu,footer,[data-testid="stToolbar"]{visibility:hidden!important;}
.stTextInput>div>div>input{
    background:#0E1220!important;color:#F0EDE8!important;
    border:1px solid rgba(255,255,255,.08)!important;border-radius:10px!important;
    font-size:.92rem!important;padding:.7rem 1rem!important;
    transition:border-color .2s,box-shadow .2s!important;}
.stTextInput>div>div>input:focus{
    border-color:rgba(201,168,76,.5)!important;
    box-shadow:0 0 0 3px rgba(201,168,76,.08)!important;}
.stTextInput>div>div>input::placeholder{color:#3A3A4E!important;}
label,[data-baseweb="label"]{
    color:#5A5768!important;font-size:.7rem!important;
    letter-spacing:.14em!important;text-transform:uppercase!important;}
.stButton>button{
    background:linear-gradient(135deg,#C9A84C,#A8862E)!important;
    color:#0A0D14!important;border:none!important;border-radius:10px!important;
    font-weight:600!important;font-size:.88rem!important;
    padding:.75rem 1.4rem!important;width:100%!important;
    letter-spacing:.04em!important;transition:all .25s!important;}
.stButton>button:hover{
    background:linear-gradient(135deg,#E8C97A,#C9A84C)!important;
    transform:translateY(-2px)!important;
    box-shadow:0 6px 24px rgba(201,168,76,.35)!important;}
.stTabs [data-baseweb="tab-list"]{
    background:#0E1220!important;
    border:1px solid rgba(255,255,255,.06)!important;
    border-radius:12px!important;padding:5px!important;gap:3px!important;
    margin-bottom:0!important;justify-content:center!important;
    width:fit-content!important;margin-left:auto!important;margin-right:auto!important;}
.stTabs [data-baseweb="tab"]{
    background:transparent!important;color:#5A5768!important;
    border-radius:8px!important;padding:.5rem 2.5rem!important;
    font-size:.86rem!important;border:none!important;flex:0 0 auto!important;}
.stTabs [aria-selected="true"]{
    background:rgba(201,168,76,.14)!important;
    color:#C9A84C!important;font-weight:500!important;}
.stTabs [data-baseweb="tab-highlight"]{display:none!important;}
.stTabs [data-baseweb="tab-border"]{display:none!important;}
::-webkit-scrollbar{width:4px;}
::-webkit-scrollbar-track{background:var(--bg2);}
::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:2px;}
</style>""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:3.5rem'></div>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;margin-bottom:2.8rem;">
    <div style="font-family:'Cormorant Garamond',serif;font-size:3rem;font-weight:600;
         letter-spacing:.2em;line-height:1;
         background:linear-gradient(135deg,#C9A84C 0%,#E8C97A 50%,#C9A84C 100%);
         -webkit-background-clip:text;-webkit-text-fill-color:transparent;
         background-clip:text;">VANTURA</div>
    <div style="font-size:.58rem;letter-spacing:.35em;color:#3A3A50;margin-top:8px;">
        WEALTH INTELLIGENCE v2.0</div>
    <div style="width:40px;height:1px;margin:14px auto 0;
         background:linear-gradient(90deg,transparent,#C9A84C,transparent);"></div>
</div>
""", unsafe_allow_html=True)

# ── Content ────────────────────────────────────────────────────────────────────
_, card, _ = st.columns([1, 2.2, 1])

with card:
    pending_email = st.session_state.get("_otp_pending_email")

    # ── OTP Step ───────────────────────────────────────────────────────────────
    if pending_email:
        st.markdown(f"""
        <div style="background:#161B2E;border:1px solid rgba(201,168,76,.2);
             border-radius:16px;padding:2rem 1.8rem;text-align:center;margin-bottom:1.2rem;">
            <div style="font-size:2.2rem;margin-bottom:.8rem;">📬</div>
            <div style="font-family:'Cormorant Garamond',serif;font-size:1.5rem;
                 color:#F0EDE8;margin-bottom:.5rem;">Cek Email Anda</div>
            <div style="font-size:.82rem;color:#5A5768;line-height:1.7;">
                Kode OTP dikirim ke<br>
                <span style="color:#C9A84C;font-weight:500;">{pending_email}</span>
            </div>
            <div style="display:inline-block;margin-top:.8rem;padding:.3rem .9rem;
                 background:rgba(255,165,2,.08);border:1px solid rgba(255,165,2,.2);
                 border-radius:20px;font-size:.72rem;color:#FFA502;">
                ⏱ Berlaku 5 menit
            </div>
        </div>
        """, unsafe_allow_html=True)

        otp_input = st.text_input("Masukkan Kode OTP", placeholder="6 digit kode",
                                  max_chars=6, key="otp_input")
        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

        if st.button("✓  Verifikasi & Masuk", key="verify_otp"):
            if not otp_input or len(otp_input.strip()) != 6:
                st.error("Masukkan kode OTP 6 digit.")
            else:
                with st.spinner("Memverifikasi…"):
                    ok, msg, user_data = login_step2(pending_email, otp_input)
                if ok:
                    set_authenticated(user_data)
                    st.success("✓ Berhasil! Mengalihkan…")
                    st.switch_page("pages/1_profil.py")
                else:
                    st.error(f"✗ {msg}")

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        col_l, col_r = st.columns(2)
        with col_l:
            if st.button("🔄 Kirim ulang", key="resend_otp"):
                with st.spinner("Mengirim…"):
                    from utils.otp import send_and_store_otp
                    from utils.db  import get_user
                    u = get_user(pending_email)
                    ok, msg = send_and_store_otp(
                        pending_email, u.get("name","") if u else "")
                st.success("✓ Terkirim.") if ok else st.error(f"✗ {msg}")
        with col_r:
            if st.button("← Kembali", key="back_to_login"):
                st.session_state.pop("_otp_pending_email", None)
                st.rerun()

    # ── Login / Register ───────────────────────────────────────────────────────
    else:
        tab_masuk, tab_daftar = st.tabs(["  Masuk  ", "  Daftar  "])

        with tab_masuk:
            st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
            email_in = st.text_input("Email", placeholder="nama@email.com",
                                     key="login_email")
            pw_in    = st.text_input("Password", type="password",
                                     placeholder="Password Anda", key="login_pw")
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

            if st.button("Masuk  →", key="btn_login", use_container_width=True):
                if not email_in or not pw_in:
                    st.error("Email dan password wajib diisi.")
                else:
                    with st.spinner("Memverifikasi…"):
                        ok, msg = login_step1(email_in.strip().lower(), pw_in)
                    if ok:
                        st.success(f"✓ {msg}")
                        st.rerun()
                    else:
                        st.error(f"✗ {msg}")

            st.markdown("""
            <div style="text-align:center;margin-top:.9rem;padding:.55rem;
                 background:rgba(45,212,191,.04);border-radius:8px;
                 border:1px solid rgba(45,212,191,.1);">
                <span style="font-size:.73rem;color:#5A5768;">
                    🔐 Kode OTP dikirim ke email setelah password benar
                </span>
            </div>
            """, unsafe_allow_html=True)

        with tab_daftar:
            st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
            reg_name  = st.text_input("Nama Lengkap", placeholder="Nama Anda",
                                      key="reg_name")
            reg_email = st.text_input("Email", placeholder="nama@email.com",
                                      key="reg_email")
            reg_pw    = st.text_input("Password", type="password",
                                      placeholder="Min. 8 karakter", key="reg_pw")
            reg_pw2   = st.text_input("Konfirmasi Password", type="password",
                                      placeholder="Ulangi password", key="reg_pw2")
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

            if st.button("Buat Akun  →", key="btn_register", use_container_width=True):
                if not all([reg_name, reg_email, reg_pw, reg_pw2]):
                    st.error("Semua field wajib diisi.")
                elif reg_pw != reg_pw2:
                    st.error("Password tidak cocok.")
                elif len(reg_pw) < 8:
                    st.error("Password minimal 8 karakter.")
                else:
                    with st.spinner("Membuat akun…"):
                        ok, msg = register_user(
                            reg_email.strip().lower(), reg_pw, reg_name.strip())
                    if ok:
                        st.success(f"✓ {msg} Silakan masuk.")
                    else:
                        st.error(f"✗ {msg}")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;margin-top:2.5rem;padding-bottom:2rem;">
    <div style="font-size:.65rem;color:#2A2A3E;letter-spacing:.1em;">
        VANTURA v2.0 © 2025 &nbsp;·&nbsp; Bukan saran investasi resmi
    </div>
</div>
""", unsafe_allow_html=True)