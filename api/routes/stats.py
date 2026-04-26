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

from config import STAT_FILES_DIR, LEADERBOARD_MIN_INPUT

logger = logging.getLogger(__name__)

stats_bp = Blueprint("stats", __name__)

HISTORY_FILE     = os.path.join(STAT_FILES_DIR, "run_history.json")
LEADERBOARD_FILE = os.path.join(STAT_FILES_DIR, "leaderboard.json")
MAX_HISTORY      = 100  # keep most recent N entries


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


def _load_leaderboard() -> list:
    if not os.path.isfile(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # Migrate from old dict-keyed-by-method format to list
            entries = list(data.values())
            for e in entries:
                e.setdefault("increment", 0)
            _save_leaderboard(entries)  # persist immediately so migration only runs once
            return entries
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_leaderboard(lb: list) -> None:
    os.makedirs(STAT_FILES_DIR, exist_ok=True)
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(lb, f, indent=2)


def _update_leaderboard(record: dict) -> None:
    """Add/update leaderboard for qualifying runs (length >= threshold, not random method)."""
    method = record.get("method", "")
    if not method or method == "tri_matrix_random":
        return
    length = record.get("length", 0)
    if length < LEADERBOARD_MIN_INPUT:
        return

    lb = _load_leaderboard()
    for i, entry in enumerate(lb):
        if entry.get("method") == method and entry.get("length") == length:
            if record["elapsed"] < entry["elapsed"]:  # keep fastest
                lb[i] = record
                _save_leaderboard(lb)
            return  # same key exists regardless of time

    lb.append(record)
    _save_leaderboard(lb)


@stats_bp.route("/stats/history")
def get_history():
    """Return the run history as JSON."""
    return jsonify(_load_history())


@stats_bp.route("/stats/leaderboard")
def get_leaderboard():
    """Return the leaderboard as a JSON array sorted by length desc, method asc."""
    lb = _load_leaderboard()
    lb_sorted = sorted(lb, key=lambda e: (-e.get("length", 0), e.get("method", "")))
    return jsonify(lb_sorted)


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
