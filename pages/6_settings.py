import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv; load_dotenv()

import streamlit as st
from datetime import datetime

from utils.session import auth_guard, logout
from utils.auth    import change_password
from utils.db      import get_user, update_user_field, delete_user, load_history, get_analytics
from engine.data_fetcher import fetch_all_live_data
from pages._shared import sidebar

st.set_page_config(page_title="Vantura — Pengaturan", page_icon="⚜️",
                   layout="wide", initial_sidebar_state="expanded")
auth_guard()

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
.stTextInput>div>div>input{background:var(--card)!important;color:var(--tp)!important;
    border:1px solid var(--bdrs)!important;border-radius:6px!important;}
.stTextInput>div>div>input:focus{border-color:var(--gold)!important;}
label,[data-baseweb="label"]{color:var(--ts)!important;font-size:.78rem!important;
    letter-spacing:.07em!important;text-transform:uppercase!important;}
::-webkit-scrollbar{width:5px;}::-webkit-scrollbar-track{background:var(--bg2);}
::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:3px;}
</style>""", unsafe_allow_html=True)

live = fetch_all_live_data()
sidebar(live)

email   = st.session_state.get("user_email","")
user    = get_user(email) if email else {}
history = load_history(email) if email else []

st.markdown("""
<div style="margin-bottom:2rem;">
    <h1 style="font-family:'Cormorant Garamond',serif;font-size:2.2rem;font-weight:300;
         color:#F0EDE8;letter-spacing:.04em;line-height:1.2;margin-bottom:.3rem;">
        Pengaturan <span style="color:#C9A84C;">Akun</span></h1>
</div>
""", unsafe_allow_html=True)

tab1,tab2,tab3,tab4 = st.tabs(["👤 Profil","🔑 Password","📋 Riwayat Simulasi","⚠️ Danger Zone"])

# ── Tab 1: Profil ──────────────────────────────────────────────────────────────
with tab1:
    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("""
        <div style="font-size:.62rem;color:#5A5768;letter-spacing:.18em;
             text-transform:uppercase;margin-bottom:.9rem;">✦ Data Diri</div>
        """, unsafe_allow_html=True)
        new_name = st.text_input("Nama Lengkap", value=user.get("name",""))
        st.text_input("Email (tidak dapat diubah)", value=email, disabled=True)
        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
        if st.button("Simpan Perubahan", key="save_name"):
            if len(new_name.strip()) >= 2:
                update_user_field(email, "name", new_name.strip())
                st.session_state.user_name = new_name.strip()
                st.success("✓ Nama berhasil diperbarui.")
            else:
                st.error("Nama minimal 2 karakter.")
    with col2:
        created   = user.get("created_at","")[:10] if user.get("created_at") else "—"
        last_log  = user.get("last_login","")[:10] if user.get("last_login") else "—"
        log_count = user.get("login_count",0)
        st.markdown(f"""
        <div style="margin-top:1.8rem;background:rgba(201,168,76,.05);
             border:1px solid rgba(201,168,76,.18);border-radius:12px;padding:1.3rem 1.4rem;">
            <div style="font-size:.62rem;color:#5A5768;letter-spacing:.18em;
                 text-transform:uppercase;margin-bottom:.9rem;">✦ Info Akun</div>
            <div style="display:flex;flex-direction:column;gap:.6rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:.78rem;color:#5A5768;">Dibuat</span>
                    <span style="font-size:.82rem;color:#F0EDE8;">{created}</span>
                </div>
                <div style="height:1px;background:rgba(255,255,255,.04);"></div>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:.78rem;color:#5A5768;">Login terakhir</span>
                    <span style="font-size:.82rem;color:#F0EDE8;">{last_log}</span>
                </div>
                <div style="height:1px;background:rgba(255,255,255,.04);"></div>
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:.78rem;color:#5A5768;">Total login</span>
                    <span style="font-size:.82rem;color:#C9A84C;font-weight:600;">{log_count}×</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Tab 2: Password ────────────────────────────────────────────────────────────
with tab2:
    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    col_pw, col_tip = st.columns([3, 2])
    with col_pw:
        st.markdown("""
        <div style="font-size:.62rem;color:#5A5768;letter-spacing:.18em;
             text-transform:uppercase;margin-bottom:.9rem;">✦ Ganti Password</div>
        """, unsafe_allow_html=True)
        old_pw  = st.text_input("Password Lama", type="password", key="old_pw")
        new_pw  = st.text_input("Password Baru", type="password", key="new_pw",
                                help="Minimal 8 karakter, kombinasi huruf dan angka")
        new_pw2 = st.text_input("Konfirmasi Baru", type="password", key="new_pw2")
        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
        if st.button("Ganti Password", key="chg_pw"):
            if not all([old_pw, new_pw, new_pw2]):
                st.error("Semua field wajib diisi.")
            elif new_pw != new_pw2:
                st.error("Password baru tidak cocok.")
            else:
                ok, msg = change_password(email, old_pw, new_pw)
                st.success(f"✓ {msg}") if ok else st.error(f"✗ {msg}")
    with col_tip:
        st.markdown("""
        <div style="margin-top:1.8rem;background:rgba(45,212,191,.05);
             border:1px solid rgba(45,212,191,.15);border-radius:12px;padding:1.3rem 1.4rem;">
            <div style="font-size:.62rem;color:#5A5768;letter-spacing:.18em;
                 text-transform:uppercase;margin-bottom:.9rem;">✦ Tips Keamanan</div>
            <div style="display:flex;flex-direction:column;gap:.65rem;">
                <div style="display:flex;gap:.6rem;align-items:flex-start;">
                    <span style="color:#2DD4BF;font-size:.7rem;margin-top:.1rem;">◈</span>
                    <span style="font-size:.79rem;color:#9B97A0;line-height:1.5;">
                        Minimal <b style="color:#F0EDE8;">8 karakter</b></span></div>
                <div style="display:flex;gap:.6rem;align-items:flex-start;">
                    <span style="color:#2DD4BF;font-size:.7rem;margin-top:.1rem;">◈</span>
                    <span style="font-size:.79rem;color:#9B97A0;line-height:1.5;">
                        Kombinasi huruf besar, kecil &amp; angka</span></div>
                <div style="display:flex;gap:.6rem;align-items:flex-start;">
                    <span style="color:#2DD4BF;font-size:.7rem;margin-top:.1rem;">◈</span>
                    <span style="font-size:.79rem;color:#9B97A0;line-height:1.5;">
                        Jangan pakai tanggal lahir atau nama</span></div>
                <div style="display:flex;gap:.6rem;align-items:flex-start;">
                    <span style="color:#2DD4BF;font-size:.7rem;margin-top:.1rem;">◈</span>
                    <span style="font-size:.79rem;color:#9B97A0;line-height:1.5;">
                        Password unik untuk setiap akun</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Tab 3: Riwayat ─────────────────────────────────────────────────────────────
with tab3:
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    if not history:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#5A5768;">
            <div style="font-size:2rem;margin-bottom:.8rem;">📋</div>
            <div style="font-size:.9rem;">Belum ada riwayat simulasi.</div>
            <div style="font-size:.8rem;margin-top:.4rem;">
                Isi profil dan lihat proyeksi untuk mulai menyimpan riwayat.</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='font-size:.75rem;color:#5A5768;margin-bottom:.6rem;'>"
                    f"Menampilkan {min(10,len(history))} simulasi terakhir</div>",
                    unsafe_allow_html=True)
        for run in history[:10]:
            ts = run.get("timestamp","")[:16].replace("T"," ")
            st.markdown(f"""
            <div style="background:#161B2E;border:1px solid rgba(255,255,255,.06);
                 border-radius:10px;padding:1rem 1.3rem;margin-bottom:.6rem;
                 display:flex;gap:2rem;flex-wrap:wrap;align-items:center;">
                <div style="font-size:.75rem;color:#5A5768;">{ts}</div>
                <div style="font-size:.82rem;color:#9B97A0;">
                    Usia: <span style="color:#F0EDE8;">{run.get('age','?')}</span></div>
                <div style="font-size:.82rem;color:#9B97A0;">
                    Skenario: <span style="color:#C9A84C;">{run.get('scenario','Normal')}</span></div>
                <div style="font-size:.82rem;color:#9B97A0;">
                    Pensiun: <span style="color:#F0EDE8;">{run.get('ret_age','?')} thn</span></div>
            </div>""", unsafe_allow_html=True)

# ── Tab 4: Danger Zone ─────────────────────────────────────────────────────────
with tab4:
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:rgba(255,71,87,.06);border:1px solid rgba(255,71,87,.25);
         border-radius:12px;padding:1.4rem 1.6rem;margin-bottom:1rem;">
        <div style="color:#FF4757;font-weight:600;margin-bottom:.5rem;">⚠️ Hapus Akun Permanen</div>
        <div style="color:#9B97A0;font-size:.83rem;line-height:1.6;">
            Tindakan ini <b style="color:#FF4757;">tidak dapat dibatalkan</b>.
            Seluruh data, profil, dan riwayat simulasi Anda akan dihapus selamanya dari server.
        </div>
    </div>
    """, unsafe_allow_html=True)
    confirm_del = st.text_input("Ketik DELETE (huruf kapital) untuk konfirmasi",
                                placeholder="DELETE", key="confirm_del")
    if st.button("🗑  Hapus Akun Saya Permanen", key="del_acct"):
        if confirm_del == "DELETE":
            delete_user(email)
            logout()
        else:
            st.error("Ketik DELETE (huruf kapital semua) untuk konfirmasi.")