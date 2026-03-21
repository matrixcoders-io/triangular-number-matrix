"""
api/routes/stats.py

Stats blueprint — run history (append/read from JSON), stat file reading.
History is stored in static/output/stat-files/run_history.json.
"""

import os
import json
import time
import logging

from flask import Blueprint, request, jsonify

from config import STAT_FILES_DIR

logger = logging.getLogger(__name__)

stats_bp = Blueprint("stats", __name__)

HISTORY_FILE = os.path.join(STAT_FILES_DIR, "run_history.json")
MAX_HISTORY  = 50  # keep most recent N entries


def _load_history() -> list:
    if not os.path.isfile(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_history(history: list) -> None:
    os.makedirs(STAT_FILES_DIR, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-MAX_HISTORY:], f, indent=2)


@stats_bp.route("/stats/history")
def get_history():
    """Return the run history as JSON."""
    return jsonify(_load_history())


@stats_bp.route("/stats/history/append", methods=["POST"])
def append_history():
    """
    Append one run record to history.
    Expected JSON body:
      { "method": "tri_matrix", "repdigit": "2", "length": 1000,
        "result_chars": 1998, "elapsed": 0.0023 }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "no JSON body"}), 400
    record = {
        "ts":           time.strftime("%Y-%m-%dT%H:%M:%S"),
        "method":       str(data.get("method", "")),
        "repdigit":     str(data.get("repdigit", "")),
        "length":       int(data.get("length", 0)),
        "result_chars": int(data.get("result_chars", 0)),
        "elapsed":      float(data.get("elapsed", 0.0)),
    }
    history = _load_history()
    history.append(record)
    _save_history(history)
    return jsonify({"ok": True, "count": len(history)})


@stats_bp.route("/stats/history/clear", methods=["POST"])
def clear_history():
    """Wipe all run history."""
    _save_history([])
    return jsonify({"ok": True})
