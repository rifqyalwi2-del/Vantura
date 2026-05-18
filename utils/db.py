"""
utils/db.py
Supabase-backed database — drop-in replacement untuk JSON file db.
Semua fungsi signature sama persis dengan versi lama.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Optional

import streamlit as st
from supabase import create_client, Client

from utils.logger import get_logger

log = get_logger("db")


# ── Supabase client (singleton via st.cache_resource) ─────────────────────────

@st.cache_resource
def _get_client() -> Client:
    """Buat Supabase client sekali, reuse untuk semua request."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


def _db() -> Client:
    return _get_client()


# ── Users ─────────────────────────────────────────────────────────────────────

def load_users() -> dict:
    """Ambil semua users sebagai dict {email: data} — kompatibel dengan versi lama."""
    try:
        rows = _db().table("users").select("*").execute().data
        return {r["email"]: r for r in rows}
    except Exception as e:
        log.error(f"load_users error: {e}")
        return {}


def save_user(email: str, data: dict):
    """Simpan user baru ke tabel users."""
    try:
        row = {
            "email":         email,
            "name":          data.get("name", ""),
            "password_hash": data["password_hash"],
            "created_at":    data.get("created_at", datetime.now().isoformat()),
            "last_login":    data.get("last_login"),
            "login_count":   data.get("login_count", 0),
        }
        _db().table("users").upsert(row).execute()
        log.info(f"User saved: {email[:3]}***")
    except Exception as e:
        log.error(f"save_user error: {e}")
        raise


def get_user(email: str) -> Optional[dict]:
    """Ambil satu user berdasarkan email."""
    try:
        res = _db().table("users").select("*").eq("email", email).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        log.error(f"get_user error: {e}")
        return None


def update_user_field(email: str, field: str, value: Any):
    """Update satu field di tabel users."""
    try:
        _db().table("users").update({field: value}).eq("email", email).execute()
    except Exception as e:
        log.error(f"update_user_field error ({field}): {e}")


def delete_user(email: str):
    """Hapus user dan semua data terkait (cascade via FK)."""
    try:
        _db().table("users").delete().eq("email", email).execute()
        log.info(f"User deleted: {email[:3]}***")
    except Exception as e:
        log.error(f"delete_user error: {e}")
        raise


# ── Profiles ──────────────────────────────────────────────────────────────────

def save_profile(email: str, profile_data: dict):
    """Simpan atau update profil finansial user."""
    try:
        row = {
            "email":      email,
            "data":       profile_data,
            "updated_at": datetime.now().isoformat(),
        }
        _db().table("profiles").upsert(row).execute()
        log.info(f"Profile saved: {email[:3]}***")
    except Exception as e:
        log.error(f"save_profile error: {e}")
        raise


def load_profile(email: str) -> Optional[dict]:
    """Ambil profil finansial user."""
    try:
        res = _db().table("profiles").select("data").eq("email", email).execute()
        return res.data[0]["data"] if res.data else None
    except Exception as e:
        log.error(f"load_profile error: {e}")
        return None


# ── Simulation History ─────────────────────────────────────────────────────────

def save_history_entry(email: str, entry: dict):
    """Tambah satu entri riwayat simulasi."""
    try:
        entry["timestamp"] = datetime.now().isoformat()
        _db().table("history").insert({
            "email": email,
            "data":  entry,
        }).execute()

        # Bersihkan history lama — simpan max 20 terakhir
        all_rows = (_db().table("history")
                    .select("id")
                    .eq("email", email)
                    .order("created_at", desc=True)
                    .execute().data)
        if len(all_rows) > 20:
            old_ids = [r["id"] for r in all_rows[20:]]
            _db().table("history").delete().in_("id", old_ids).execute()

    except Exception as e:
        log.error(f"save_history_entry error: {e}")


def load_history(email: str) -> list:
    """Ambil riwayat simulasi user, terbaru duluan."""
    try:
        res = (_db().table("history")
               .select("data, created_at")
               .eq("email", email)
               .order("created_at", desc=True)
               .limit(20)
               .execute())
        return [r["data"] for r in res.data]
    except Exception as e:
        log.error(f"load_history error: {e}")
        return []


# ── Analytics ─────────────────────────────────────────────────────────────────

def increment_analytics(key: str):
    """Increment counter analytics (upsert)."""
    try:
        # Coba update dulu
        existing = (_db().table("analytics")
                    .select("value")
                    .eq("key", key)
                    .execute().data)
        if existing:
            new_val = existing[0]["value"] + 1
            _db().table("analytics").update({
                "value":      new_val,
                "updated_at": datetime.now().isoformat(),
            }).eq("key", key).execute()
        else:
            _db().table("analytics").insert({
                "key":        key,
                "value":      1,
                "updated_at": datetime.now().isoformat(),
            }).execute()
    except Exception as e:
        log.error(f"increment_analytics error: {e}")


def get_analytics() -> dict:
    """Ambil semua analytics sebagai dict."""
    try:
        rows = _db().table("analytics").select("key, value").execute().data
        return {r["key"]: r["value"] for r in rows}
    except Exception as e:
        log.error(f"get_analytics error: {e}")
        return {}