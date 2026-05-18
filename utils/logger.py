"""
utils/logger.py
Logging yang berfungsi baik lokal maupun di Streamlit Cloud.
Di cloud: hanya StreamHandler (tidak bisa tulis file).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Sudah dikonfigurasi, skip

    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO"))
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Stream handler — selalu ada
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # File handler — hanya jika bisa tulis (lokal dev)
    # Di Streamlit Cloud, /data tidak writable → skip tanpa error
    try:
        log_dir = Path(os.getenv("DATA_DIR", "data")) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"vantura_{datetime.now().strftime('%Y%m%d')}.log"
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except (PermissionError, OSError):
        pass  # Normal di Streamlit Cloud

    return logger