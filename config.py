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
TN_OUT_FILE = os.path.join(TN_FILES_DIR, "tn-file.txt")
