#!/usr/bin/env python3
"""
Triangular Number Calculator using gmpy2

Usage:
    python3 triangular_number_calculator.py <repdigit_file> <increment>

Example:
    python3 triangular_number_calculator.py repdigit.txt 10000003432 > result.txt

Behavior:
    - Reads a very large decimal integer from <repdigit_file>
    - Adds <increment> to it
    - Computes T(n) = n * (n + 1) / 2 for the resulting value
    - Prints the exact result to stdout
"""

import argparse
import sys
from pathlib import Path

import gmpy2


def read_large_integer_from_file(file_path: str) -> gmpy2.mpz:
    """
    Read a large integer from a file.
    All whitespace is removed, so the number may be split across lines.
    Supports an optional leading + or - sign.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    if not path.is_file():
        raise ValueError(f"Not a regular file: {file_path}")

    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ValueError(
            f"Could not read {file_path!r} as UTF-8 text. "
            "The repdigit file must be a text file containing a decimal number."
        )

    cleaned = "".join(raw.split())

    if not cleaned:
        raise ValueError(f"File is empty or contains only whitespace: {file_path}")

    if cleaned[0] in "+-":
        sign = cleaned[0]
        digits = cleaned[1:]
        if not digits or not digits.isdigit():
            raise ValueError(
                f"Invalid integer format in file: {file_path}. "
                "Expected an optional leading sign followed by digits."
            )
        cleaned = sign + digits
    else:
        if not cleaned.isdigit():
            raise ValueError(
                f"Invalid integer format in file: {file_path}. "
                "Expected digits only (whitespace is allowed and ignored)."
            )

    return gmpy2.mpz(cleaned)


def triangular_number(n: gmpy2.mpz) -> gmpy2.mpz:
    """
    Compute T(n) = n(n+1)/2 exactly.
    Uses a parity-aware version to keep the intermediate product a bit smaller.
    """
    if n < 0:
        raise ValueError("Triangular number is only supported here for n >= 0.")

    if gmpy2.is_even(n):
        return (n // 2) * (n + 1)
    return n * ((n + 1) // 2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute triangular number of (large integer from file + increment) using gmpy2."
    )
    parser.add_argument(
        "repdigit_file",
        help="Path to a text file containing the large decimal integer",
    )
    parser.add_argument(
        "increment",
        help="Integer increment to add before computing the triangular number",
    )

    args = parser.parse_args()

    try:
        base_value = read_large_integer_from_file(args.repdigit_file)
        increment = gmpy2.mpz(args.increment)
        n = base_value + increment
        result = triangular_number(n)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())