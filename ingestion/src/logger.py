"""
Structured logging setup, shared by every ingestion script.

Logs to both the console (so you see progress while it runs) and a
timestamped file under ingestion/logs/ (so a run over thousands of
PDFs leaves a record you can review afterward — which files failed,
which were flagged as possibly-scanned, etc).
"""

import logging
import sys
from datetime import datetime

from config import LOG_DIR


def get_logger(name: str) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"ingest_{datetime.now():%Y%m%d_%H%M%S}.log"

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()  # avoid duplicate handlers if called twice

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
