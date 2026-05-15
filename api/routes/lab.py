"""
api/routes/lab.py

Lab blueprint — pytest runner, returns streaming/collected test output.
"""

import os
import sys
import subprocess
import logging

from flask import Blueprint, jsonify, Response, stream_with_context

logger = logging.getLogger(__name__)

lab_bp = Blueprint("lab", __name__)

# Project root is two levels above this file
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_venv_python = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")
VENV_PYTHON  = _venv_python if os.path.isfile(_venv_python) else sys.executable


def _pytest_cmd(test_file: str | None = None) -> list:
    target = os.path.join(PROJECT_ROOT, "tests", test_file) if test_file else os.path.join(PROJECT_ROOT, "tests")
    return [VENV_PYTHON, "-m", "pytest", target, "-v", "--tb=short", "--no-header"]


@lab_bp.route("/lab/run-tests", methods=["POST"])
def run_tests():
    """
    Run the full test suite and return collected output as JSON.
    { "returncode": 0, "output": "...", "passed": N, "failed": N }
    Small test files only — stream mode not used here for simplicity.
    """
    try:
        proc = subprocess.run(
            _pytest_cmd(),
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=120,
        )
        output = proc.stdout + proc.stderr
        passed = output.count(" PASSED")
        failed = output.count(" FAILED")
        xfailed = output.count(" XFAIL")
        return jsonify({
            "returncode": proc.returncode,
            "output": output,
            "passed": passed,
            "failed": failed,
            "xfailed": xfailed,
        })
    except subprocess.TimeoutExpired:
        return jsonify({"returncode": -1, "output": "Tests timed out after 120s.", "passed": 0, "failed": 0, "xfailed": 0})
    except Exception as e:
        logger.error("lab/run-tests error: %s", e)
        # Return 200 so HTMX swaps the output — HTMX 1.9 silently ignores non-2xx responses
        return jsonify({"returncode": -1, "output": str(e), "passed": 0, "failed": 0, "xfailed": 0})


@lab_bp.route("/lab/run-tests/stream")
def run_tests_stream():
    """
    Run tests and stream output line-by-line as text/event-stream (SSE).
    The browser Lab panel can consume this to show live output.
    """
    def generate():
        try:
            proc = subprocess.Popen(
                _pytest_cmd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=PROJECT_ROOT,
            )
            for line in proc.stdout:
                yield f"data: {line.rstrip()}\n\n"
            proc.wait()
            yield f"data: [EXIT:{proc.returncode}]\n\n"
        except Exception as e:
            yield f"data: [ERROR:{e}]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
