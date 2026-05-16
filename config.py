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

# Allowlist for files the calculator will accept. Use ["*"] to allow any file in NUMBERS_DIR.
ALLOWED_FILES = [
    "1-1k.txt", "2-1k.txt", "3-1k.txt", "4-1k.txt", "5-1k.txt",
    "6-1k.txt", "7-1k.txt", "8-1k.txt", "9-1k.txt",
    "1-1m.txt", "1-10m.txt", "1-100m.txt", "1-1b.txt", "1-5b.txt",
]

# --- Calculator defaults ---
DEFAULT_CHUNK_CHARS = 8_388_608  # 8 MiB per chunk for streaming/memory modes
TN_OUT_FILE     = os.path.join(TN_FILES_DIR, "tn-file.txt")
TN_LAST_RESULT  = os.path.join(TN_FILES_DIR, "tn-last-result.txt")

# ---------------------------------------------------------------------------
# Input char limit
# ---------------------------------------------------------------------------
# Max chars accepted from the textarea (num1). Files whose full content fits within
# this limit can be edited in the Input Number panel before calculating.
# Files larger than this are always loaded fresh from disk.
# Set to 0 to disable textarea input entirely (always load from disk).
HTTP_CHAR_LIMIT = int(os.environ.get("HTTP_CHAR_LIMIT", "10000"))

# Minimum input length (digit count) for a run to qualify for the leaderboard.
# Override at startup: LEADERBOARD_MIN_INPUT=1000000000
LEADERBOARD_MIN_INPUT = int(os.environ.get("LEADERBOARD_MIN_INPUT", "4000000000"))

# Set UI_FILE_GENERATE_ENABLED=true at startup to enable the Generate button in File Library.
# When enabled, ALL files in NUMBERS_DIR are accepted by the calculator (ALLOWED_FILES bypassed).
UI_FILE_GENERATE_ENABLED = os.environ.get("UI_FILE_GENERATE_ENABLED", "false").lower() == "true"

# Maximum allowed absolute value for the num2 increment field.
# Override at startup: MAX_INCREMENT=500000
MAX_INCREMENT = int(os.environ.get("MAX_INCREMENT", "100000"))
