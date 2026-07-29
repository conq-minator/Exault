"""
ExcelPlorer — Logging Configuration

Sets up structured logging with console and file handlers.
Each module gets its own logger via logging.getLogger(__name__).
"""

import logging
import sys
from pathlib import Path

import config


def setup_logging() -> logging.Logger:
    """
    Configure application-wide logging.

    Sets up:
        - Console handler (stdout) with colored-style formatting
        - File handler (data/excelplorer.log) for persistence
        - Root logger level from config

    Returns:
        The root application logger.
    """
    # Get the root logger for the application
    root_logger = logging.getLogger("excelplorer")
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.DEBUG))

    # Prevent duplicate handlers on repeated calls
    if root_logger.handlers:
        return root_logger

    # ─── Formatter ───────────────────────────────────────────────────────
    formatter = logging.Formatter(
        fmt=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT
    )

    # ─── Console Handler ─────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # ─── File Handler ────────────────────────────────────────────────────
    try:
        # Ensure log directory exists
        log_dir: Path = config.LOG_FILE.parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            filename=str(config.LOG_FILE),
            encoding="utf-8",
            mode="a"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        root_logger.warning(f"Could not create log file: {e}")

    # ─── Suppress noisy third-party loggers ──────────────────────────────
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    root_logger.debug("Logging configured successfully.")
    return root_logger
