"""
api/routes/files.py

File browser blueprint — file listing with size/digit-count, preview endpoint.
"""

import os
import re
import logging

from flask import Blueprint, request, jsonify, abort

from config import NUMBERS_DIR, UI_FILE_GENERATE_ENABLED

logger = logging.getLogger(__name__)

files_bp = Blueprint("files", __name__)

PREVIEW_CAP = 10_000  # max digits returned to browser for textarea preview

_GEN_PATTERN = re.compile(r'^(\d)-(\d+)(k|m|b)\.txt$')
_UNIT_MAP = {'k': 1_000, 'm': 1_000_000, 'b': 1_000_000_000}


def _count_digits(path: str) -> int:
    """Count digits in a number file without loading it into memory.

    Works by using file size (1 byte per ASCII digit) and checking whether
    the last byte is a newline so we can subtract it if needed.
    """
    size = os.path.getsize(path)
    if size == 0:
        return 0
    with open(path, "rb") as f:
        f.seek(-1, 2)
        last = f.read(1)
    return size - 1 if last in (b"\n", b"\r") else size


def _file_info(filename: str) -> dict:
    """Return size and digit count for a number file."""
    path = os.path.join(NUMBERS_DIR, filename)
    try:
        size_bytes = os.path.getsize(path)
        digits = _count_digits(path)
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
            if os.path.isfile(os.path.join(NUMBERS_DIR, f)) and not f.startswith('.')
        )
        return jsonify([_file_info(f) for f in files])
    except Exception as e:
        logger.error("files/list failed: %s", e)
        return jsonify({"error": str(e)}), 500


@files_bp.route("/files/preview")
def preview_file():
    """
    Return the first PREVIEW_CAP digits of a number file for textarea display.
    Adds X-File-Digits and X-Preview-Truncated headers so the browser can show
    a truncation note without loading the full file into memory.
    """
    name = request.args.get("name", "").strip()
    if not name or "/" in name or "\\" in name:
        abort(400)
    path = os.path.join(NUMBERS_DIR, name)
    if not os.path.isfile(path):
        abort(404)
    try:
        total_digits = _count_digits(path)
        with open(path, "r", encoding="utf-8") as f:
            chunk = f.read(PREVIEW_CAP + 1)
        # Strip trailing newline from the read chunk before checking truncation
        content = chunk.rstrip("\n\r ")
        truncated = len(content) > PREVIEW_CAP
        content = content[:PREVIEW_CAP]
        headers = {
            "Content-Type": "text/plain; charset=utf-8",
            "X-File-Digits": str(total_digits),
            "X-Preview-Truncated": "true" if truncated else "false",
        }
        return content, 200, headers
    except Exception as e:
        logger.error("files/preview failed for %s: %s", name, e)
        abort(500)


@files_bp.route("/files/generate", methods=["POST"])
def generate_file():
    """Generate a new repdigit file by expanding a source file N times."""
    if not UI_FILE_GENERATE_ENABLED:
        return jsonify({"error": "File generation is disabled"}), 403

    data = request.get_json(silent=True) or {}
    name = data.get("name", "")
    try:
        factor = int(data.get("factor", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid factor"}), 400

    if not name or "/" in name or "\\" in name or ".." in name:
        return jsonify({"error": "Invalid filename"}), 400
    if factor < 1 or factor > 10:
        return jsonify({"error": "Factor must be 1-10"}), 400

    m = _GEN_PATTERN.match(name)
    if not m:
        return jsonify({"error": "Filename must match pattern: digit-Nunit.txt"}), 400

    digit, num, unit = m.group(1), int(m.group(2)), m.group(3)
    src_path = os.path.join(NUMBERS_DIR, name)
    if not os.path.isfile(src_path):
        return jsonify({"error": "Source file not found"}), 404

    new_num = num * factor
    new_name = f"{digit}-{new_num}{unit}.txt"
    dest_path = os.path.join(NUMBERS_DIR, new_name)
    total_digits = new_num * _UNIT_MAP[unit]

    try:
        CHUNK = 1024 * 1024  # 1 MB per write
        with open(dest_path, "w", encoding="ascii") as f:
            remaining = total_digits
            while remaining > 0:
                chunk = min(remaining, CHUNK)
                f.write(digit * chunk)
                remaining -= chunk
        return jsonify({
            "name": new_name,
            "digits": total_digits,
            "size_display": _human_size(total_digits),
        })
    except Exception as e:
        logger.error("generate_file failed: %s", e)
        return jsonify({"error": str(e)}), 500
