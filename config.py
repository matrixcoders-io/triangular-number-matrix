"""Application configuration — paths and tunable constants."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Static file paths ---
NUMBERS_DIR    = os.path.join(BASE_DIR, "static", "numbers")
OUTPUT_DIR     = os.path.join(BASE_DIR, "static", "output")
TN_FILES_DIR   = os.path.join(OUTPUT_DIR, "tn-files")
WE_FILES_DIR   = os.path.join(OUTPUT_DIR, "we-files")
STAT_FILES_DIR = os.path.join(OUTPUT_DIR, "stat-files")
CONFIGS_DIR    = os.path.join(BASE_DIR, "static", "configs")
WINDOWS_JSON   = os.path.join(CONFIGS_DIR, "windows.json")

# --- Calculator defaults ---
DEFAULT_CHUNK_CHARS = 8_388_608  # 8 MiB per chunk for streaming/memory modes
TN_OUT_FILE     = os.path.join(TN_FILES_DIR, "tn-file.txt")
TN_LAST_RESULT  = os.path.join(TN_FILES_DIR, "tn-last-result.txt")

# ---------------------------------------------------------------------------
# UI file transfer options
# ---------------------------------------------------------------------------
# Set UI_HTTP_FILE_TRANSFER=false at startup to disable HTTP mode entirely.
# The radio toggle will be hidden and all files are read server-side (disk-direct).
UI_HTTP_FILE_TRANSFER = os.environ.get("UI_HTTP_FILE_TRANSFER", "true").lower() == "true"

# Maximum number of digits allowed for HTTP transfer to the browser.
# Files with more digits than this will force disk-direct mode automatically.
# Override at startup: UI_HTTP_FILE_MAX_DIGITS=5000000
UI_HTTP_FILE_MAX_DIGITS = int(os.environ.get("UI_HTTP_FILE_MAX_DIGITS", "10000000"))
