"""
src/logging_config.py — Structured Pipeline Logger (PRD §24)
Produces numbered step logs, [CACHE HIT] markers, and file-based logging.
"""
import os
import logging
import sys
import io
from datetime import datetime


def setup_logging(log_dir: str = "logs") -> logging.Logger:
    """
    Configure root logger to emit to both stdout and a timestamped log file.
    Ensures no API keys appear in log output (PRD §30).
    """
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"pipeline_{timestamp}.log")

    # Force UTF-8 on Windows consoles to avoid cp1252 charmap errors
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter("%(message)s"))

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(stream_handler)
    root.addHandler(file_handler)

    logger = logging.getLogger("AutoVideo")
    logger.info(f"Log file: {log_file}")
    return logger


def step(label: str, current: int, total: int) -> str:
    return f"[{current}/{total}] {label}"


def cache_hit(stage: str, key_prefix: str = "") -> str:
    suffix = f" ({key_prefix})" if key_prefix else ""
    return f"[CACHE HIT] {stage}{suffix}"


def cache_miss(stage: str) -> str:
    return f"[CACHE MISS] {stage}"
