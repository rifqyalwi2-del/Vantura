"""
utils/session.py
Session management, auth guard, auto-logout.
"""
from __future__ import annotations

import time
import os
import streamlit as st
from typing import Optional

from utils.auth import verify_token
from utils.logger import get_logger

log = get_logger("session")

_SESS_TTL = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60")) * 60


def init_session():
    defaults = {
        "authenticated":  False,
        "user_email":     None,
        "user_name":      None,
        "session_token":  None,
        "session_start":  None,
        "user_profile":   None,
        "login_tab":      "masuk",
        "stress_scenario":"Normal",
        "theme":          "dark",
        "onboarded":      False,
        "alert_shown":    False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def is_session_valid() -> bool:
    if not st.session_state.get("authenticated"):
        return False
    token = st.session_state.get("session_token")
    email = st.session_state.get("user_email")
    if not token or not email:
        return False
    if not verify_token(token, email):
        return False
    start = st.session_state.get("session_start", 0)
    if time.time() - start > _SESS_TTL:
        return False
    return True


def auth_guard(redirect_to: str = "pages/0_login.py"):
    """Call at top of every protected page."""
    init_session()
    if not is_session_valid():
        _clear_session()
        st.switch_page(redirect_to)


def profile_guard(redirect_to: str = "pages/1_profil.py"):
    """Ensure user has filled in their profile."""
    if st.session_state.get("user_profile") is None:
        st.switch_page(redirect_to)


def set_authenticated(user_data: dict):
    st.session_state.authenticated  = True
    st.session_state.user_email     = user_data["email"]
    st.session_state.user_name      = user_data.get("name", "")
    st.session_state.session_token  = user_data["token"]
    st.session_state.session_start  = time.time()


def _clear_session():
    for k in ["authenticated","user_email","user_name","session_token",
              "session_start","user_profile"]:
        st.session_state[k] = None
    st.session_state.authenticated = False


def logout():
    _clear_session()
    st.switch_page("pages/0_login.py")