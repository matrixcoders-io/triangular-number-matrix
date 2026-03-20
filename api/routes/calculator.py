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

from flask import Blueprint, request, Response, render_template
from werkzeug.exceptions import RequestEntityTooLarge

from core.calculator import ManualBigNumber, TriangulaNumberMatrix, ShortFormBigNumber
from config import (
    NUMBERS_DIR,
    TN_OUT_FILE,
    WE_FILES_DIR,
    STAT_FILES_DIR,
    WINDOWS_JSON,
)

logger = logging.getLogger(__name__)

calculator_bp = Blueprint("calculator", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_file_content(filepath: str) -> str:
    try:
        with open(filepath, "r") as f:
            return f.read()
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


def list_number_files() -> List[str]:
    """Return sorted list of filenames in the numbers directory."""
    try:
        files = [
            f for f in os.listdir(NUMBERS_DIR)
            if os.path.isfile(os.path.join(NUMBERS_DIR, f))
        ]
        return sorted(files)
    except Exception as e:
        logger.error("Failed to list number files: %s", e)
        return []


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
    file_load_time = 0

    file_names = list_number_files()

    if request.method == "POST":
        num1 = request.form.get("num1", "").strip()
        num2 = request.form.get("num2", "").strip()
        operation = request.form.get("operation", "")

        try:
            start_time = time.perf_counter()

            if file_name:
                num1 = read_file_content(os.path.join(NUMBERS_DIR, file_name))
                file_load_time = str(time.perf_counter() - start_time)
                logger.info("Loading file from: %s/%s", NUMBERS_DIR, file_name)

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

            elif operation == "tri_div_gmpy2_formula":
                a = ManualBigNumber(num1)
                logger.info("loaded file for gmpy2 n(n+1)/2: %s s", file_load_time)
                result = a.triangular_number_gmpy2_division(num1)
                write_to_file(TN_OUT_FILE + "." + operation + ".txt", str(result))
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

            elif operation == "tri_matrix":
                b = TriangulaNumberMatrix("1")
                logger.info("loaded file for tri_matrix: %s s", file_load_time)
                result = b.repDigitTriangularNumber(num1)
                write_to_file(TN_OUT_FILE + "." + operation + "_standard.txt", str(result))
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
                result = b.repDigitTriangularNumberStream(
                    num1,
                    out_path=TN_OUT_FILE + "." + operation + ".txt",
                    extract_ranges=windows,
                    collect_result=False,
                )
                write_to_file(os.path.join(WE_FILES_DIR, "we-file.txt.tri_matrix_stream.txt"), str(result["extracted"]))
                write_to_file(
                    os.path.join(STAT_FILES_DIR, "stat-file.txt.tri_matrix_stream.txt"),
                    "{repdigit: " + str(result["repdigit"]) + ", repdigit_length: " + str(result["repdigit_length"]) +
                    ", generated_chars: " + str(result["generated_chars"]) + ", file_load_time: " + file_load_time +
                    ", elapsed_seconds: " + str(result["elapsed_seconds"]) + ", total_elapsed: " + str(time.perf_counter() - start_time) + "}"
                )
                logger.info("rep digit calculation complete (tri_matrix_stream): %.6f s", time.perf_counter() - start_time)
                result = b.increment_by_gmpy_count(num1, result, num2) if num2 not in (None, "", " ") else result

            elif operation == "tri_matrix_memory":
                b = TriangulaNumberMatrix("1")
                logger.info("loaded file for tri_matrix_memory: %s s", file_load_time)
                windows = [(int(a), int(bv)) for a, bv in load_windows_json(WINDOWS_JSON)]
                result = b.repDigitTriangularNumberMemory(num1, extract_ranges=windows, collect_result=False)
                write_to_file(os.path.join(TN_OUT_FILE + ".tri_matrix_memory.txt"), str(result.get("result", "")))
                write_to_file(os.path.join(WE_FILES_DIR, "we-file.txt.tri_matrix_memory.txt"), str(result["extracted"]))
                write_to_file(
                    os.path.join(STAT_FILES_DIR, "stat-file.txt.tri_matrix_memory.txt"),
                    "{repdigit: " + str(result["repdigit"]) + ", repdigit_length: " + str(result["repdigit_length"]) +
                    ", generated_chars: " + str(result["generated_chars"]) + ", file_load_time: " + file_load_time +
                    ", elapsed_seconds: " + str(result["elapsed_seconds"]) + ", total_elapsed: " + str(time.perf_counter() - start_time) + "}"
                )
                logger.info("rep digit calculation complete (tri_matrix_memory): %.6f s", time.perf_counter() - start_time)
                result = b.increment_by_gmpy_count(num1, result, num2) if num2 not in (None, "", " ") else result

            elif operation == "tri_matrix_random":
                b = TriangulaNumberMatrix("1")
                logger.info("loaded file for tri_matrix_random: %s s", file_load_time)
                windows = [(int(a), int(bv)) for a, bv in load_windows_json(WINDOWS_JSON)]
                sf = ShortFormBigNumber.from_ops(num1)
                result = b.repDigitTriangularNumberRandomAccess(sf, extract_ranges=windows, collect_result=True, compressed_tn_result=False)
                write_to_file(os.path.join(TN_OUT_FILE + ".tri_matrix_random.txt"), str(result.get("result", result.get("compressed"))))
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

        except Exception as e:
            logger.error("Error during operation %s: %s", operation, e, exc_info=True)
            error = str(e)

    if request_type == "API":
        logger.info("API request operation: %s", operation)
        return Response("Elapsed: " + str(elapsed) + " seconds. ", status=200, mimetype="text/plain")

    return render_template(
        "index.html",
        result=result,
        error=error,
        num1=num1,
        num2=num2,
        selected_operation=operation,
        elapsed=elapsed,
        elapsed_display=elapsed,
        percent_change=percent_change,
        file_names=file_names,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@calculator_bp.route("/", methods=["GET", "POST"])
def index():
    return handle_big_number_math("WEB")


@calculator_bp.route("/rep-digit-math", methods=["GET", "POST"])
def rep_digit_math():
    return handle_big_number_math("API")
