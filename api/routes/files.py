"""
api/routes/files.py

File browser blueprint — file listing with size/digit-count, preview endpoint.
"""

import os
import logging

from flask import Blueprint, request, jsonify, abort

from config import NUMBERS_DIR, UI_HTTP_FILE_TRANSFER, UI_HTTP_FILE_MAX_DIGITS

logger = logging.getLogger(__name__)

files_bp = Blueprint("files", __name__)


def _file_info(filename: str) -> dict:
    """Return size and digit count for a number file."""
    path = os.path.join(NUMBERS_DIR, filename)
    try:
        size_bytes = os.path.getsize(path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        digits = len(content)
        return {
            "name": filename,
            "size_bytes": size_bytes,
            "size_display": _human_size(size_bytes),
            "digits": digits,
            "digits_display": _human_num(digits),
        }
    except Exception as e:
        logger.warning("Could not stat file %s: %s", filename, e)
        return {"name": filename, "size_bytes": 0, "size_display": "?", "digits": 0, "digits_display": "?"}


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _human_num(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


@files_bp.route("/files/list")
def list_files():
    """JSON list of all number files with size and digit metadata."""
    try:
        files = sorted(
            f for f in os.listdir(NUMBERS_DIR)
            if os.path.isfile(os.path.join(NUMBERS_DIR, f))
        )
        return jsonify([_file_info(f) for f in files])
    except Exception as e:
        logger.error("files/list failed: %s", e)
        return jsonify({"error": str(e)}), 500


@files_bp.route("/files/preview")
def preview_file():
    """
    HTTP transfer mode: return file content to browser.
    Returns 403 if HTTP transfer is disabled in config.
    Returns 413 if the file exceeds UI_HTTP_FILE_MAX_DIGITS.
    """
    if not UI_HTTP_FILE_TRANSFER:
        return "HTTP file transfer is disabled.", 403

    name = request.args.get("name", "").strip()
    if not name or "/" in name or "\\" in name:
        abort(400)
    path = os.path.join(NUMBERS_DIR, name)
    if not os.path.isfile(path):
        abort(404)
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if len(content) > UI_HTTP_FILE_MAX_DIGITS:
            return (
                f"File too large for HTTP transfer ({len(content):,} digits). "
                f"Switch to Disk-Direct mode (limit: {UI_HTTP_FILE_MAX_DIGITS:,} digits).",
                413,
            )
        return content, 200, {"Content-Type": "text/plain; charset=utf-8"}
    except Exception as e:
        logger.error("files/preview failed for %s: %s", name, e)
        abort(500)
