"""
utils/auth.py
Authentication dengan 2-step: Password → OTP via email.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime
from typing import Optional

import streamlit as st

from utils.db import (get_user, save_user, update_user_field, increment_analytics)
from utils.logger import get_logger

log = get_logger("auth")

_MAX_ATT  = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
_LOCKOUT  = int(os.getenv("LOCKOUT_MINUTES", "15"))
_SESS_TTL = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))


def _secret() -> str:
    try:
        return st.secrets["app"]["secret_key"]
    except Exception:
        return os.getenv("APP_SECRET_KEY", "vantura-dev-secret-change-me")


def hash_password(password: str) -> str:
    salt = _secret()[:16]
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(password), hashed)


def generate_token(email: str) -> str:
    payload = f"{email}:{time.time()}:{secrets.token_hex(8)}"
    sig = hmac.new(_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def verify_token(token: str, email: str) -> bool:
    try:
        parts = token.rsplit(":", 1)
        if len(parts) != 2:
            return False
        payload, sig = parts
        expected = hmac.new(_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False
        ts = float(payload.split(":")[1])
        return (time.time() - ts) < (_SESS_TTL * 60)
    except Exception:
        return False


_ATTEMPTS: dict[str, list] = {}


def is_locked(email: str) -> tuple[bool, int]:
    attempts = _ATTEMPTS.get(email, [])
    now = time.time()
    recent = [t for t in attempts if now - t < _LOCKOUT * 60]
    _ATTEMPTS[email] = recent
    if len(recent) >= _MAX_ATT:
        wait = int(_LOCKOUT * 60 - (now - recent[0]))
        return True, max(0, wait)
    return False, 0


def record_failed_attempt(email: str):
    _ATTEMPTS.setdefault(email, []).append(time.time())
    log.warning(f"Failed login: {email[:3]}***")


def clear_attempts(email: str):
    _ATTEMPTS.pop(email, None)


def register_user(email: str, password: str, name: str) -> tuple[bool, str]:
    if get_user(email):
        return False, "Email sudah terdaftar."
    if len(password) < 8:
        return False, "Password minimal 8 karakter."
    if len(name.strip()) < 2:
        return False, "Nama minimal 2 karakter."
    if "@" not in email or "." not in email:
        return False, "Format email tidak valid."
    save_user(email, {
        "name":          name.strip(),
        "password_hash": hash_password(password),
        "created_at":    datetime.now().isoformat(),
        "last_login":    None,
        "login_count":   0,
    })
    increment_analytics("total_registrations")
    log.info(f"Registered: {email[:3]}***")
    return True, "Akun berhasil dibuat."


def login_step1(email: str, password: str) -> tuple[bool, str]:
    """Step 1: Verifikasi password → kirim OTP ke email."""
    locked, wait = is_locked(email)
    if locked:
        return False, f"Akun terkunci. Coba lagi dalam {wait//60}m {wait%60}s."
    user = get_user(email)
    if not user:
        record_failed_attempt(email)
        return False, "Email tidak ditemukan."
    if not verify_password(password, user["password_hash"]):
        record_failed_attempt(email)
        remaining = _MAX_ATT - len(_ATTEMPTS.get(email, []))
        return False, f"Password salah. {max(0,remaining)} percobaan tersisa."
    from utils.otp import send_and_store_otp
    ok, msg = send_and_store_otp(email, user.get("name", ""))
    if not ok:
        return False, msg
    st.session_state["_otp_pending_email"] = email
    clear_attempts(email)
    return True, msg


def login_step2(email: str, otp_code: str) -> tuple[bool, str, Optional[dict]]:
    """Step 2: Verifikasi OTP → buat session."""
    from utils.otp import verify_otp
    ok, msg = verify_otp(email, otp_code.strip())
    if not ok:
        return False, msg, None
    user = get_user(email)
    if not user:
        return False, "User tidak ditemukan.", None
    token = generate_token(email)
    update_user_field(email, "last_login",    datetime.now().isoformat())
    update_user_field(email, "login_count",   (user.get("login_count", 0) or 0) + 1)
    update_user_field(email, "session_token", token)
    increment_analytics("total_logins")
    st.session_state.pop("_otp_pending_email", None)
    log.info(f"Login OTP success: {email[:3]}***")
    return True, "Login berhasil.", {**user, "email": email, "token": token}


def login_user(email: str, password: str) -> tuple[bool, str, Optional[dict]]:
    """Legacy login tanpa OTP — kompatibilitas."""
    locked, wait = is_locked(email)
    if locked:
        return False, f"Akun terkunci. Coba lagi dalam {wait//60}m {wait%60}s.", None
    user = get_user(email)
    if not user:
        record_failed_attempt(email)
        return False, "Email tidak ditemukan.", None
    if not verify_password(password, user["password_hash"]):
        record_failed_attempt(email)
        remaining = _MAX_ATT - len(_ATTEMPTS.get(email, []))
        return False, f"Password salah. {max(0,remaining)} percobaan tersisa.", None
    clear_attempts(email)
    token = generate_token(email)
    update_user_field(email, "last_login",    datetime.now().isoformat())
    update_user_field(email, "login_count",   (user.get("login_count", 0) or 0) + 1)
    update_user_field(email, "session_token", token)
    increment_analytics("total_logins")
    return True, "Login berhasil.", {**user, "email": email, "token": token}


def change_password(email: str, old_pw: str, new_pw: str) -> tuple[bool, str]:
    user = get_user(email)
    if not user:
        return False, "User tidak ditemukan."
    if not verify_password(old_pw, user["password_hash"]):
        return False, "Password lama salah."
    if len(new_pw) < 8:
        return False, "Password baru minimal 8 karakter."
    if old_pw == new_pw:
        return False, "Password baru tidak boleh sama dengan lama."
    update_user_field(email, "password_hash", hash_password(new_pw))
    log.info(f"Password changed: {email[:3]}***")
    return True, "Password berhasil diubah."