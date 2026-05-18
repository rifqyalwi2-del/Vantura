"""
engine/data_fetcher.py
Live macro data: CPI, GDP, BI Rate, Gold price.
"""
from __future__ import annotations
from typing import Tuple
import requests
import streamlit as st
from utils.logger import get_logger

log = get_logger("data_fetcher")

_FALLBACK = {"cpi": 5.0, "medical": 10.0, "gdp": 5.0,
             "bi_rate": 6.25, "gold_idr": 1_100_000}


@st.cache_data(ttl=21_600)
def fetch_indonesia_inflation() -> Tuple[float, float, str]:
    url = ("https://api.worldbank.org/v2/country/ID/indicator/FP.CPI.TOTL.ZG"
           "?format=json&mrv=3&per_page=3")
    try:
        r = requests.get(url, timeout=8); r.raise_for_status()
        for rec in (r.json()[1] or []):
            if rec.get("value") is not None:
                cpi = round(float(rec["value"]), 2)
                return cpi, round(cpi * 2.0, 2), str(rec.get("date","?"))
    except Exception as e:
        log.warning(f"Inflation API failed: {e}")
    return _FALLBACK["cpi"], _FALLBACK["medical"], "Fallback"


@st.cache_data(ttl=21_600)
def fetch_gdp_growth() -> float:
    url = ("https://api.worldbank.org/v2/country/ID/indicator/NY.GDP.MKTP.KD.ZG"
           "?format=json&mrv=2&per_page=2")
    try:
        r = requests.get(url, timeout=8); r.raise_for_status()
        for rec in (r.json()[1] or []):
            if rec.get("value") is not None:
                return round(float(rec["value"]), 2)
    except Exception as e:
        log.warning(f"GDP API failed: {e}")
    return _FALLBACK["gdp"]


@st.cache_data(ttl=3_600)
def fetch_bi_rate() -> float:
    """BI Rate from World Bank lending rate proxy."""
    url = ("https://api.worldbank.org/v2/country/ID/indicator/FR.INR.LEND"
           "?format=json&mrv=2&per_page=2")
    try:
        r = requests.get(url, timeout=8); r.raise_for_status()
        for rec in (r.json()[1] or []):
            if rec.get("value") is not None:
                return round(float(rec["value"]), 2)
    except Exception as e:
        log.warning(f"BI Rate API failed: {e}")
    return _FALLBACK["bi_rate"]


@st.cache_data(ttl=3_600)
def fetch_gold_price_idr() -> float:
    """Gold price in IDR/gram via frankfurter.app (XAU/USD) × USD/IDR."""
    try:
        r1 = requests.get("https://api.frankfurter.app/latest?from=XAU&to=USD",
                          timeout=6)
        r2 = requests.get("https://api.frankfurter.app/latest?from=USD&to=IDR",
                          timeout=6)
        r1.raise_for_status(); r2.raise_for_status()
        xau_usd = r1.json()["rates"]["USD"]    # 1 troy oz in USD
        usd_idr = r2.json()["rates"]["IDR"]
        per_gram = (xau_usd * usd_idr) / 31.1035
        return round(per_gram, 0)
    except Exception as e:
        log.warning(f"Gold API failed: {e}")
    return _FALLBACK["gold_idr"]


def fetch_all_live_data() -> dict:
    cpi, med, yr = fetch_indonesia_inflation()
    return {
        "cpi":          cpi,
        "medical":      med,
        "year":         yr,
        "gdp":          fetch_gdp_growth(),
        "bi_rate":      fetch_bi_rate(),
        "gold_idr":     fetch_gold_price_idr(),
    }