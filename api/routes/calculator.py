"""
api/routes/calculator.py

Calculator blueprint — handles all calculation routes (web UI + API).
Extracted from the original app.py.
"""

import os
import time
import json
import logging
from typing import List, Tuple

from flask import Blueprint, request, Response, render_template, jsonify
from werkzeug.exceptions import RequestEntityTooLarge

from core.calculator import ManualBigNumber, TriangulaNumberMatrix, ShortFormBigNumber
from config import (
    NUMBERS_DIR,
    TN_OUT_FILE,
    TN_LAST_RESULT,
    WE_FILES_DIR,
    STAT_FILES_DIR,
    WINDOWS_JSON,
    HTTP_CHAR_LIMIT,
    ALLOWED_FILES,
    UI_FILE_GENERATE_ENABLED,
    MAX_INCREMENT,
)
from api.routes.stats import _load_history, _save_history, _update_leaderboard

logger = logging.getLogger(__name__)

calculator_bp = Blueprint("calculator", __name__)

VALID_OPERATIONS = frozenset({
    "tri_matrix", "tri_matrix_stream", "tri_matrix_memory",
    "tri_matrix_random", "tri_div_gmpy2_formula", "tri_div_simpy_formula",
})


def _tn_file_path(operation: str, file_stem: str) -> str:
    """TN output path keyed by (operation, input-file-stem).

    tri_matrix writes with suffix 'tri_matrix_standard' to match its legacy pattern.
    All other operations use the operation name directly.
    """
    suffix = "tri_matrix_standard" if operation == "tri_matrix" else operation
    return f"{TN_OUT_FILE}.{suffix}.{file_stem}.txt"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_file_content(filepath: str) -> str:
    try:
        with open(filepath, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return f"Error: The file {filepath} was not found."
    except Exception as e:
        return f"An error occurred: {e}"


def write_to_file(output_file: str, content: str) -> None:
    """Write content to output_file, overwriting if it already exists."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)


def load_windows_json(path: str) -> List[Tuple[int, int]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [tuple(pair) for pair in data]


def calc_change(old, new) -> float:
    if old == 0:
        raise ValueError("Cannot calculate percent change from zero.")
    return ((float(new) - float(old)) / float(old)) * 100


def list_number_files() -> List[dict]:
    """Return sorted list of file metadata dicts for the numbers directory."""
    try:
        names = sorted(
            f for f in os.listdir(NUMBERS_DIR)
            if os.path.isfile(os.path.join(NUMBERS_DIR, f)) and not f.startswith('.')
        )
        result = []
        for name in names:
            path = os.path.join(NUMBERS_DIR, name)
            size_bytes = os.path.getsize(path)
            result.append({
                "name": name,
                "size_bytes": size_bytes,
                "size_display": _human_size(size_bytes),
            })
        return result
    except Exception as e:
        logger.error("Failed to list number files: %s", e)
        return []


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ---------------------------------------------------------------------------
# Core dispatch
# ---------------------------------------------------------------------------

def handle_big_number_math(request_type: str):
    result = None
    error = None
    num1 = ""
    num2 = ""
    operation = ""
    file_name = request.form.get("file_names", "")
    elapsed = None
    percent_change = float("0.0")
    file_load_time = "0"

    file_names = list_number_files()

    if request.method == "POST":
        num1 = request.form.get("num1", "").strip()
        num2 = request.form.get("num2", "").strip()
        operation = request.form.get("operation", "")
        # file_stem always comes from the selected filename when one exists.
        # This ensures TN files are keyed correctly and /calc/window works,
        # regardless of whether we use textarea or disk for num1.
        file_stem = os.path.splitext(file_name)[0] if file_name else ""
        try:
            start_time = time.perf_counter()

            # Use textarea content when it's within the char limit; otherwise load from disk.
            # Strict less-than ensures truncated previews (= HTTP_CHAR_LIMIT chars) go to disk.
            use_textarea = HTTP_CHAR_LIMIT > 0 and len(num1) < HTTP_CHAR_LIMIT

            # SEC-12: reject oversized increment before any computation
            if num2 and num2.lstrip('-').isdigit() and abs(int(num2)) > MAX_INCREMENT:
                return render_template(
                    "partials/result_panel.html",
                    error=f"Increment must be between -{MAX_INCREMENT:,} and {MAX_INCREMENT:,}.",
                )

            if not use_textarea:
                if not file_name:
                    return render_template("partials/result_panel.html",
                                           error="No input provided. Select a file or enter a number.")
                if ".." in file_name or "/" in file_name or "\\" in file_name:
                    return render_template("partials/result_panel.html", error="Invalid file name.")
                if ALLOWED_FILES != ["*"] and file_name not in ALLOWED_FILES:
                    allowed = ", ".join(ALLOWED_FILES)
                    return render_template(
                        "partials/result_panel.html",
                        error=f"File '{file_name}' is not permitted. Allowed files: {allowed}",
                    )
                num1 = read_file_content(os.path.join(NUMBERS_DIR, file_name))
                file_load_time = str(time.perf_counter() - start_time)
                logger.info("Loading file from disk: %s/%s", NUMBERS_DIR, file_name)

            if operation == "add":
                result = ManualBigNumber(num1).add(ManualBigNumber(num2))

            elif operation == "subtract":
                result = ManualBigNumber(num1).subtract(ManualBigNumber(num2))

            elif operation == "multiply":
                result = ManualBigNumber(num1).multiply(ManualBigNumber(num2))

            elif operation == "divide":
                result = ManualBigNumber(num1).divide(ManualBigNumber(num2))

            elif operation == "tri_add":
                result = ManualBigNumber(num1).triangular_number_addition()

            elif operation == "tri_formula":
                result = ManualBigNumber(num1).triangular_number_formula()

            elif operation == "tri_div_simpy_formula":
                result = ManualBigNumber(num1).triangular_number_sympi_division(num1)
                logger.info("rep digit calculation complete (sympy n(n+1)/2): %.6f s", time.perf_counter() - start_time)
                b = TriangulaNumberMatrix("1")
                result = b.increment_by_gmpy_count(num1, result, num2) if num2 not in (None, "", " ") else result
                result = str(result)  # convert sympy Integer to str once — later str() calls are no-ops
                if file_stem:
                    write_to_file(_tn_file_path(operation, file_stem), result)
                write_to_file(
                    os.path.join(STAT_FILES_DIR, "stat-file.txt.tri_div_simpy_formula.txt"),
                    "{repdigit: " + str(num1[0]) +
                    ", repdigit_length: " + str(len(num1)) +
                    ", generated_chars: " + str(len(result)) +
                    ", file_load_time: " + str(file_load_time) +
                    ", total_elapsed: " + str(time.perf_counter() - start_time) + "}"
                )

            elif operation == "tri_div_gmpy2_formula":
                a = ManualBigNumber(num1)
                logger.info("loaded file for gmpy2 n(n+1)/2: %s s", file_load_time)
                result = a.triangular_number_gmpy2_division(num1)
                result = str(result)  # convert gmpy2 mpz → str once; later str() calls are no-ops
                if file_stem:
                    write_to_file(_tn_file_path(operation, file_stem), result)
                write_to_file(
                    os.path.join(STAT_FILES_DIR, "stat-file.txt.tri_div_pmpy2_formula.txt"),
                    "{repdigit: " + str(num1[0]) +
                    ", repdigit_length: " + str(len(num1)) +
                    ", generated_chars: " + str(len(result)) +
                    ", file_load_time: " + str(file_load_time) +
                    ", total_elapsed: " + str(time.perf_counter() - start_time) + "}"
                )
                logger.info("rep digit calculation complete (gmpy2 n(n+1)/2): %.6f s", time.perf_counter() - start_time)
                b = TriangulaNumberMatrix("1")
                result = b.increment_by_gmpy_count(num1, result, num2) if num2 not in (None, "", " ") else result
                result = str(result)  # no-op if no increment (already str); converts mpz if increment applied

            elif operation == "tri_matrix":
                b = TriangulaNumberMatrix("1")
                logger.info("loaded file for tri_matrix: %s s", file_load_time)
                result = b.repDigitTriangularNumber(num1)
                if file_stem:
                    write_to_file(_tn_file_path(operation, file_stem), str(result))
                write_to_file(
                    os.path.join(STAT_FILES_DIR, "stat-file.txt.tri_matrix_standard.txt"),
                    "{repdigit: " + str(num1[0]) + ", repdigit_length: " + str(len(num1)) +
                    ", generated_chars: " + str(len(result)) + ", file_load_time: " + str(file_load_time) +
                    ", total_elapsed: " + str(time.perf_counter() - start_time) + "}"
                )
                logger.info("rep digit calculation complete (tri_matrix): %.6f s", time.perf_counter() - start_time)
                result = b.increment_by_gmpy_count(num1, result, num2) if num2 not in (None, "", " ") else result

            elif operation == "tri_matrix_stream":
                b = TriangulaNumberMatrix("1")
                logger.info("loaded file for tri_matrix_stream: %s s", file_load_time)
                windows = [(int(a), int(bv)) for a, bv in load_windows_json(WINDOWS_JSON)]
                _stream_res = b.repDigitTriangularNumberStream(
                    num1,
                    out_path=_tn_file_path(operation, file_stem) if file_stem else TN_OUT_FILE + ".tri_matrix_stream.raw.txt",
                    extract_ranges=windows,
                    collect_result=True,
                )
                write_to_file(os.path.join(WE_FILES_DIR, "we-file.txt.tri_matrix_stream.txt"), str(_stream_res["extracted"]))
                write_to_file(
                    os.path.join(STAT_FILES_DIR, "stat-file.txt.tri_matrix_stream.txt"),
                    "{repdigit: " + str(_stream_res["repdigit"]) + ", repdigit_length: " + str(_stream_res["repdigit_length"]) +
                    ", generated_chars: " + str(_stream_res["generated_chars"]) + ", file_load_time: " + file_load_time +
                    ", elapsed_seconds: " + str(_stream_res["elapsed_seconds"]) + ", total_elapsed: " + str(time.perf_counter() - start_time) + "}"
                )
                result = _stream_res.get("result", "")
                logger.info("rep digit calculation complete (tri_matrix_stream): %.6f s", time.perf_counter() - start_time)
                result = b.increment_by_gmpy_count(num1, result, num2) if num2 not in (None, "", " ") else result

            elif operation == "tri_matrix_memory":
                b = TriangulaNumberMatrix("1")
                logger.info("loaded file for tri_matrix_memory: %s s", file_load_time)
                windows = [(int(a), int(bv)) for a, bv in load_windows_json(WINDOWS_JSON)]
                _mem_res = b.repDigitTriangularNumberMemory(num1, extract_ranges=windows, collect_result=True)
                if file_stem:
                    write_to_file(_tn_file_path(operation, file_stem), str(_mem_res.get("result", "")))
                write_to_file(os.path.join(WE_FILES_DIR, "we-file.txt.tri_matrix_memory.txt"), str(_mem_res["extracted"]))
                write_to_file(
                    os.path.join(STAT_FILES_DIR, "stat-file.txt.tri_matrix_memory.txt"),
                    "{repdigit: " + str(_mem_res["repdigit"]) + ", repdigit_length: " + str(_mem_res["repdigit_length"]) +
                    ", generated_chars: " + str(_mem_res["generated_chars"]) + ", file_load_time: " + file_load_time +
                    ", elapsed_seconds: " + str(_mem_res["elapsed_seconds"]) + ", total_elapsed: " + str(time.perf_counter() - start_time) + "}"
                )
                result = _mem_res.get("result", "")
                logger.info("rep digit calculation complete (tri_matrix_memory): %.6f s", time.perf_counter() - start_time)
                result = b.increment_by_gmpy_count(num1, result, num2) if num2 not in (None, "", " ") else result

            elif operation == "tri_matrix_random":
                b = TriangulaNumberMatrix("1")
                logger.info("loaded file for tri_matrix_random: %s s", file_load_time)
                windows = [(int(a), int(bv)) for a, bv in load_windows_json(WINDOWS_JSON)]
                sf = ShortFormBigNumber.from_ops(num1)
                result = b.repDigitTriangularNumberRandomAccess(sf, extract_ranges=windows, collect_result=True, compressed_tn_result=False)
                if file_stem:
                    write_to_file(_tn_file_path(operation, file_stem), str(result.get("result", result.get("compressed"))))
                write_to_file(os.path.join(WE_FILES_DIR, "we-file.txt.tri_matrix_random.txt"), str(result["extracted"]))
                write_to_file(
                    os.path.join(STAT_FILES_DIR, "stat-file.txt.tri_matrix_random.txt"),
                    "{repdigit: " + str(result["repdigit"]) + ", repdigit_length: " + str(result["l"]) +
                    ", file_load_time: " + file_load_time +
                    ", elapsed_seconds: " + str(result["elapsed_seconds"]) + ", total_elapsed: " + str(time.perf_counter() - start_time) + "}"
                )
                result = result.get("result", result.get("compressed"))
                logger.info("rep digit calculation complete (tri_matrix_random): %.6f s", time.perf_counter() - start_time)
                result = b.increment_by_gmpy_count(num1, result, num2) if num2 not in (None, "", " ") else result

            else:
                error = "Unsupported operation."

            old_elapsed = request.form.get("elapsed")
            elapsed = time.perf_counter() - start_time
            logger.info("Operation complete, elapsed time: %.6f s", elapsed)
            try:
                percent_change = calc_change(old_elapsed, elapsed)
            except Exception:
                percent_change = 0.0

            # Append to run history
            if result is not None and error is None:
                repdigit = num1[0] if num1 else ""
                result_str = str(result)
                history = _load_history()
                _mid = len(result_str) // 2
                history.append({
                    "ts":           time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "method":       operation,
                    "repdigit":     repdigit,
                    "length":       len(num1),
                    "result_chars": len(result_str),
                    "elapsed":      round(elapsed, 6),
                    "increment":    int(num2) if num2 and num2.lstrip('-').isdigit() else 0,
                    "mid_pattern":  result_str[max(0, _mid - 15): _mid + 15],
                    "end_pattern":  result_str[-30:],
                })
                try:
                    _save_history(history)
                    _update_leaderboard(history[-1])
                except Exception as he:
                    logger.warning("Could not save run history: %s", he)

        except Exception as e:
            logger.error("Error during operation %s: %s", operation, e, exc_info=True)
            error = "Calculation failed. Check your input and try again."  # SEC-07: don't leak internals

    if request_type == "API":
        logger.info("API request operation: %s", operation)
        return Response("Elapsed: " + str(elapsed) + " seconds. ", status=200, mimetype="text/plain")

    # Always ensure result is a string (never a dict) and cap display at 10 000 chars
    DISPLAY_CAP = 10_000
    result_str = str(result) if result is not None else None

    result_total_chars = len(result_str) if result_str else 0
    result_preview = result_str[:DISPLAY_CAP] if result_str else None

    _mid = len(result_str) // 2 if result_str else 0
    tpl_mid_pattern = result_str[max(0, _mid - 15): _mid + 15] if result_str else ""
    tpl_end_pattern = result_str[-30:] if result_str else ""
    tpl_repdigit = num1[0] if (result_str and num1) else ""

    template_vars = dict(
        result=result_preview,
        result_total_chars=result_total_chars,
        error=error,
        num1=num1,
        num2=num2,
        selected_operation=operation,
        elapsed=elapsed,
        elapsed_display=elapsed,
        percent_change=percent_change,
        mid_pattern=tpl_mid_pattern,
        end_pattern=tpl_end_pattern,
        repdigit=tpl_repdigit,
        file_names=file_names,
        ui_file_generate_enabled=UI_FILE_GENERATE_ENABLED,
        http_char_limit=HTTP_CHAR_LIMIT,
        default_file=None,
    )

    # HTMX partial swap — return only the result panel fragment
    if request_type == "HTMX":
        return render_template("partials/result_panel.html", **template_vars)

    return render_template("index.html", **template_vars)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@calculator_bp.route("/", methods=["GET"])
def index():
    # Pre-load 1-1k.txt with a tri_matrix result so the page opens ready to use.
    default_filename = "1-1k.txt"
    default_path = os.path.join(NUMBERS_DIR, default_filename)
    if os.path.isfile(default_path):
        try:
            num1 = read_file_content(default_path)
            start = time.perf_counter()
            b = TriangulaNumberMatrix("1")
            result_str = str(b.repDigitTriangularNumber(num1))
            elapsed = time.perf_counter() - start
            try:
                write_to_file(TN_LAST_RESULT, result_str)
            except Exception:
                pass
            DISPLAY_CAP = 10_000
            result_total_chars = len(result_str)
            result_preview = result_str[:DISPLAY_CAP]
            _mid = result_total_chars // 2
            file_names = list_number_files()
            return render_template("index.html",
                result=result_preview,
                result_total_chars=result_total_chars,
                num1=num1,
                num2="",
                selected_operation="tri_matrix",
                elapsed=elapsed,
                elapsed_display=elapsed,
                percent_change=0.0,
                error=None,
                mid_pattern=result_str[max(0, _mid - 15): _mid + 15],
                end_pattern=result_str[-30:],
                repdigit=num1[0] if num1 else "",
                file_names=file_names,
                ui_file_generate_enabled=UI_FILE_GENERATE_ENABLED,
        http_char_limit=HTTP_CHAR_LIMIT,
                default_file=default_filename,
            )
        except Exception as e:
            logger.warning("Default pre-load of %s failed: %s", default_filename, e)
    return handle_big_number_math("WEB")


@calculator_bp.route("/calc", methods=["POST"])
def calc():
    """HTMX endpoint — returns the result panel partial only."""
    return handle_big_number_math("HTMX")


@calculator_bp.route("/rep-digit-math", methods=["GET", "POST"])
def rep_digit_math():
    return handle_big_number_math("API")


@calculator_bp.route("/calc/window")
def result_window():
    """
    Return a 10 000-char window of the last calculated result.
    Used by the UI Prev/Next navigation to page through large results.
    Query params:
      offset    — start character position (default 0)
      length    — window size, capped at 50 000 (default 10 000)
      operation — which operation's result file to read
      file_stem — input file stem (e.g. '1-1k') that keys the result file
    Response JSON: { chunk, total, offset, length }
    """
    try:
        offset = max(0, int(request.args.get("offset", 0)))
        length = min(max(1, int(request.args.get("length", 10_000))), 50_000)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid offset or length"}), 400

    operation = request.args.get("operation", "").strip()
    file_stem = request.args.get("file_stem", "").strip()

    if operation not in VALID_OPERATIONS:
        return jsonify({"error": f"Unknown operation '{operation}'"}), 404
    if not file_stem:
        return jsonify({"error": "Windowed reading requires a file-based calculation — run a file calculation first"}), 400
    if ".." in file_stem or "/" in file_stem or "\\" in file_stem:
        return jsonify({"error": "Invalid file_stem"}), 400

    result_file = _tn_file_path(operation, file_stem)

    try:
        # Use seek/read so only the requested chunk is loaded — safe for files of any size.
        # The result file contains pure ASCII digits (0–9), so bytes == chars.
        with open(result_file, "rb") as f:
            f.seek(0, 2)          # seek to end
            total = f.tell()      # file size in bytes == total chars
            if offset >= total:
                return jsonify({"error": "offset past end of file", "total": total}), 416
            f.seek(offset)
            chunk = f.read(length).decode("ascii", errors="replace")
        return jsonify({"chunk": chunk, "total": total, "offset": offset, "length": len(chunk)})
    except FileNotFoundError:
        return jsonify({"error": "No result available — run a calculation first"}), 404
    except Exception as e:
        logger.error("result_window failed: %s", e)
        return jsonify({"error": str(e)}), 500
