"""
utils/otp.py
Email OTP — generate, send, verify.
Pakai Gmail SMTP + Supabase untuk simpan token.
"""
from __future__ import annotations

import random
import smtplib
import string
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st

from utils.logger import get_logger

log = get_logger("otp")

OTP_EXPIRY_MINUTES = 5


# ── Supabase client ────────────────────────────────────────────────────────────

def _db():
    from utils.db import _get_client
    return _get_client()


# ── Generate & Store OTP ──────────────────────────────────────────────────────

def generate_otp() -> str:
    """Generate 6-digit numeric OTP."""
    return "".join(random.choices(string.digits, k=6))


def store_otp(email: str, token: str):
    """Simpan OTP ke Supabase, hapus OTP lama milik email ini dulu."""
    try:
        now     = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=OTP_EXPIRY_MINUTES)

        # Hapus OTP lama
        _db().table("otp_tokens").delete().eq("email", email).execute()

        # Simpan yang baru
        _db().table("otp_tokens").insert({
            "email":      email,
            "token":      token,
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "used":       False,
        }).execute()
        log.info(f"OTP stored for {email[:3]}***")
    except Exception as e:
        log.error(f"store_otp error: {e}")
        raise


def verify_otp(email: str, token: str) -> tuple[bool, str]:
    """
    Verifikasi OTP.
    Returns (success, message)
    """
    try:
        res = (_db().table("otp_tokens")
               .select("*")
               .eq("email", email)
               .eq("token", token)
               .eq("used", False)
               .execute())

        if not res.data:
            return False, "Kode OTP salah atau sudah digunakan."

        row     = res.data[0]
        expires = datetime.fromisoformat(row["expires_at"])

        # Pastikan expires_at timezone-aware
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) > expires:
            # Hapus OTP expired
            _db().table("otp_tokens").delete().eq("email", email).execute()
            return False, f"Kode OTP sudah kedaluwarsa. Berlaku {OTP_EXPIRY_MINUTES} menit."

        # Tandai sebagai sudah dipakai
        _db().table("otp_tokens").update({"used": True}).eq("email", email).execute()
        log.info(f"OTP verified for {email[:3]}***")
        return True, "OTP valid."

    except Exception as e:
        log.error(f"verify_otp error: {e}")
        return False, "Terjadi kesalahan saat verifikasi OTP."


# ── Send Email ─────────────────────────────────────────────────────────────────

def send_otp_email(email: str, otp: str, user_name: str = "") -> bool:
    """Kirim OTP via Gmail SMTP. Returns True jika berhasil."""
    try:
        smtp_user = st.secrets["email"]["smtp_user"]
        smtp_pass = st.secrets["email"]["smtp_password"]
        sender    = st.secrets["email"].get("sender_name", "Vantura")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Kode Verifikasi Vantura: {otp}"
        msg["From"]    = f"{sender} <{smtp_user}>"
        msg["To"]      = email

        name_display = user_name or email.split("@")[0]

        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:#0A0D14;font-family:'DM Sans',sans-serif;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td align="center" style="padding:40px 20px;">
              <table width="480" style="background:#111520;border-radius:16px;
                     border:1px solid rgba(201,168,76,.2);overflow:hidden;">

                <!-- Header -->
                <tr><td style="background:#0A0D14;padding:28px 36px;
                         border-bottom:1px solid rgba(201,168,76,.15);">
                  <div style="font-size:1.4rem;font-weight:700;letter-spacing:.12em;
                       background:linear-gradient(135deg,#C9A84C,#E8C97A);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                       background-clip:text;">VANTURA</div>
                  <div style="font-size:.6rem;letter-spacing:.2em;color:#5A5768;
                       margin-top:2px;">WEALTH INTELLIGENCE v2.0</div>
                </td></tr>

                <!-- Body -->
                <tr><td style="padding:36px;">
                  <p style="color:#9B97A0;font-size:.9rem;margin:0 0 8px;">
                    Halo, <b style="color:#F0EDE8;">{name_display}</b></p>
                  <p style="color:#9B97A0;font-size:.85rem;margin:0 0 28px;line-height:1.6;">
                    Gunakan kode berikut untuk masuk ke akun Vantura Anda.</p>

                  <!-- OTP Box -->
                  <div style="background:#0A0D14;border:2px solid rgba(201,168,76,.3);
                       border-radius:12px;padding:24px;text-align:center;margin-bottom:28px;">
                    <div style="font-size:2.8rem;font-weight:700;letter-spacing:.5em;
                         color:#C9A84C;font-family:monospace;">{otp}</div>
                    <div style="font-size:.75rem;color:#5A5768;margin-top:8px;">
                      Berlaku selama <b style="color:#FFA502;">{OTP_EXPIRY_MINUTES} menit</b>
                    </div>
                  </div>

                  <p style="color:#5A5768;font-size:.78rem;margin:0;line-height:1.6;">
                    Jika Anda tidak merasa melakukan permintaan ini, abaikan email ini.
                    Akun Anda tetap aman.</p>
                </td></tr>

                <!-- Footer -->
                <tr><td style="padding:20px 36px;border-top:1px solid rgba(255,255,255,.05);
                         text-align:center;">
                  <p style="color:#2A2A3E;font-size:.7rem;margin:0;">
                    VANTURA v2.0 · Bukan saran investasi resmi</p>
                </td></tr>

              </table>
            </td></tr>
          </table>
        </body>
        </html>
        """

        text = f"Kode OTP Vantura Anda: {otp}\nBerlaku {OTP_EXPIRY_MINUTES} menit."

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html,  "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, email, msg.as_string())

        log.info(f"OTP email sent to {email[:3]}***")
        return True

    except Exception as e:
        log.error(f"send_otp_email error: {e}")
        return False


# ── High-level helper ─────────────────────────────────────────────────────────

def send_and_store_otp(email: str, user_name: str = "") -> tuple[bool, str]:
    """
    Generate OTP, simpan ke DB, kirim ke email.
    Returns (success, message)
    """
    otp = generate_otp()
    try:
        store_otp(email, otp)
    except Exception:
        return False, "Gagal menyimpan OTP. Coba lagi."

    sent = send_otp_email(email, otp, user_name)
    if not sent:
        return False, "Gagal mengirim email. Periksa koneksi atau konfigurasi SMTP."

    return True, f"Kode OTP telah dikirim ke {email}. Berlaku {OTP_EXPIRY_MINUTES} menit."