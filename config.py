"""
ExcelPlorer — Application Configuration

All application-wide settings are defined here.
No hardcoded paths — all paths are relative to the project root.
"""

import os
from pathlib import Path


# ─── Project Paths ──────────────────────────────────────────────────────────

# Project root directory (where this file lives)
PROJECT_ROOT: Path = Path(__file__).parent.resolve()

# Data directory for sessions, exports, and database
DATA_DIR: Path = PROJECT_ROOT / "data"

# Session file storage
SESSIONS_DIR: Path = DATA_DIR / "sessions"

# Export output directory
EXPORTS_DIR: Path = DATA_DIR / "exports"

# Product library storage
PRODUCTS_DIR: Path = DATA_DIR / "products"

# Notes library storage
NOTES_DIR: Path = DATA_DIR / "notes"

# SQLite database path
DATABASE_PATH: Path = DATA_DIR / "excelplorer.db"

# Log file path
LOG_FILE: Path = DATA_DIR / "excelplorer.log"

# Frontend directory (served as static files)
FRONTEND_DIR: Path = PROJECT_ROOT / "frontend"


# ─── Server Settings ────────────────────────────────────────────────────────

# Flask server host and port
HOST: str = "127.0.0.1"
PORT: int = 5000
DEBUG: bool = True

# Auto-open browser on startup
AUTO_OPEN_BROWSER: bool = True


# ─── Upload Settings ────────────────────────────────────────────────────────

# Maximum upload file size in bytes (50 MB)
MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024

# Allowed file extensions for upload
ALLOWED_EXTENSIONS: set[str] = {".xlsx", ".xls"}


# ─── Logging Settings ───────────────────────────────────────────────────────

# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL: str = os.environ.get("EXCELPLORER_LOG_LEVEL", "DEBUG")

# Log format
LOG_FORMAT: str = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"

# Log date format
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


# ─── Analysis Settings ──────────────────────────────────────────────────────

# Maximum number of sample values to collect per column during analysis
MAX_SAMPLE_VALUES: int = 5

# Minimum confidence score for marketplace plugin detection (0.0 — 1.0)
PLUGIN_DETECTION_THRESHOLD: float = 0.5


# ─── Prompt Settings ────────────────────────────────────────────────────────

# Estimated tokens per word (rough GPT tokenizer approximation)
TOKENS_PER_WORD: float = 1.33


# ─── Auto-Correction Settings ───────────────────────────────────────────────

# Fuzzy match threshold for dropdown value correction (0.0 — 1.0)
# Higher = stricter matching (fewer false corrections)
FUZZY_MATCH_THRESHOLD: float = 0.8


# ─── Performance Settings ───────────────────────────────────────────────────

# Maximum number of products to process in a single batch
MAX_PRODUCTS_PER_BATCH: int = 500


# ─── Ensure directories exist ───────────────────────────────────────────────

def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    for _d in [DATA_DIR, SESSIONS_DIR, EXPORTS_DIR, PRODUCTS_DIR, NOTES_DIR]:
        _d.mkdir(parents=True, exist_ok=True)
