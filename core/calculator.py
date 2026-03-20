# --- imports (REMOVE ThreadPoolExecutor; ADD RepdigitCache import) ---
from typing import List
from typing import Optional, TextIO
import sys
import sympy
import time
import gmpy2
import logging

logger = logging.getLogger(__name__)

from .repdigit_cache import RepdigitCache  # <-- NEW

sys.set_int_max_str_digits(100000000)
# Allow huge numbers
sys.set_int_max_str_digits(1000000000)

# --- build a module-level cache once (Flask-friendly singleton) ---
_REPDIGIT_CACHE = RepdigitCache()
for _d in range(1, 10):  # digits 1..9
    _REPDIGIT_CACHE.build_cache(
        repdigit=_d,
        min_cache_block=10,
        max_cache_block=10_000_000_000,
        overwrite=True,
    )

from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional

import re
from dataclasses import dataclass

@dataclass(frozen=True)
class ShortFormBigNumber:
    b: int
    l: int
    n: int

    @classmethod
    def from_ops(cls, ops: str) -> "ShortFormBigNumber":
        """
        Parse an op string like:
          "(b=10,l=1233,n=2)"
          "b=10,l=1233,n=2"
          "b:10 l:1233 n:2"
        Returns ShortFormBigNumber(b=10, l=1233, n=2)
        """
        if not isinstance(ops, str):
            raise TypeError("ops must be a string")
        s = ops.strip()
        # remove surrounding parentheses if present
        if s.startswith("(") and s.endswith(")"):
            s = s[1:-1].strip()
        # Find key/value pairs for b,l,n with separators = or :
        pairs = dict(re.findall(r"\b([bln])\s*[:=]\s*(\d+)\b", s))
        if not all(k in pairs for k in ("b", "l", "n")):
            raise ValueError(f"Invalid ops string (need b,l,n): {ops}")
        b = int(pairs["b"])
        l = int(pairs["l"])
        n = int(pairs["n"])
        return cls(b=b, l=l, n=n)

# bigint.py
class ManualBigNumber:
    def __init__(self, value: str):
        if not value.isdigit():
            raise ValueError("Invalid number")
        self.value = value.lstrip('0') or '0'

    @staticmethod
    def _pad_zeros(a: str, b: str):
        max_len = max(len(a), len(b))
        return a.zfill(max_len), b.zfill(max_len)

    def triangular_number_sympi_division(self, n: str):
        n = sympy.Integer(n)
        triangular = (n * (n + 1)) / 2
        return triangular

    def triangular_number_gmpy2_division(self, n: str):
        start_time_gmpy2 = time.perf_counter()
        n = gmpy2.mpz(n)
        f_convert_time = str(time.perf_counter() - start_time_gmpy2)
        logger.debug("Finished converting string to gmpy2 format: %.6f s", float(f_convert_time))
        
        triangular = (n * (n + 1)) // 2
        gmpy2_calc_time = str(time.perf_counter() - start_time_gmpy2)
        logger.debug("Finished calculating triangular number: %.6f s", float(gmpy2_calc_time))
        return triangular

    @staticmethod
    def _multiply_single_digit(a: str, digit: int) -> str:
        if digit == 0:
            return '0'
        if digit == 1:
            return a
        carry = 0
        result = ''
        for i in range(len(a) - 1, -1, -1):
            mul = (ord(a[i]) - ord('0')) * digit + carry
            carry = mul // 10
            result = chr((mul % 10) + ord('0')) + result
        if carry:
            result = chr(carry + ord('0')) + result
        return result

    @staticmethod
    def _str_increment(num: str) -> str:
        result = ''
        carry = 1
        for i in range(len(num) - 1, -1, -1):
            n = ord(num[i]) - ord('0') + carry
            carry = n // 10
            result = chr((n % 10) + ord('0')) + result
        if carry:
            result = '1' + result
        return result

    @staticmethod
    def _compare(a: str, b: str) -> int:
        a = a.lstrip('0') or '0'
        b = b.lstrip('0') or '0'
        if len(a) > len(b):
            return 1
        if len(a) < len(b):
            return -1
        return (a > b) - (a < b)

    def __str__(self):
        return self.value


class TriangulaNumberMatrix:
    def __init__(self, value: str):
        if not value.isdigit():
            raise ValueError("Invalid number")
        self.value = value.lstrip('0') or '0'

        # Attach the shared repdigit cache
        self.repdigit_cache = _REPDIGIT_CACHE  # <-- NEW

        # vpc{lane} stands for Vertical Pattern Constant.
        # hpr and hpl for Horizontal Pattern Right and Horizontal Pattern Left respectively.
        # lc and rc stand for left constant and right constant respectively.
        self.matrix = {
            # ... (UNCHANGED: your existing matrix dict)
            '1': {
                "vpc2": '660',
                "vpc3": '216',
                "vpc4": '771',
                "vpc5": '327',
                "vpc6": '882',
                "vpc7": '438',
                "vpc8": '993',
                "vpc9": '549',
                "vpc1": '104',
                "hpr": '049382716',
                "hpl": '617283950',
                "rpr": 'Y'
            },
            '2': {
                "vpc4": '253',
                "vpc6": '475',
                "vpc8": '697',
                "vpc1": '919',
                "vpc3": '141',
                "vpc5": '364',
                "vpc7": '586',
                "vpc9": '808',
                "vpc2": '030',
                "hpr": '086419753',
                "hpl": '246913580'
            },
            '3': {
                "vpc1": '561',
                "vpc2": '561',
                "vpc3": '561',
                "vpc4": '561',
                "vpc5": '561',
                "vpc6": '561',
                "vpc7": '561',
                "vpc8": '561',
                "vpc9": '561',
                "hpr": '1',
                "hpl": '5'
            },
            '4': {
                "vpc8": '990',
                "vpc3": '879',
                "vpc7": '767',
                "vpc2": '656',
                "vpc6": '545',
                "vpc1": '434',
                "vpc5": '323',
                "vpc9": '212',
                "vpc4": '101',
                "hpr": '123456790',
                "hpl": '987654320'
            },
            '5': {
                "vpc1": '540',
                "vpc6": '429',
                "vpc2": '317',
                "vpc7": '206',
                "vpc3": '095',
                "vpc8": '984',
                "vpc4": '873',
                "vpc9": '762',
                "vpc5": '651',
                "hpr": '123456790',
                "hpl": '543209876',
                "lc": '1'
            },
            '6': {
                "vpc1": '2211',
                "vpc2": '2211',
                "vpc3": '2211',
                "vpc4": '2211',
                "vpc5": '2211',
                "vpc6": '2211',
                "vpc7": '2211',
                "vpc8": '2211',
                "vpc9": '2211',
                "hpr": '1',
                "hpl": '2'
            },
            '7': {
                "vpc5": '003',
                "vpc3": '225',
                "vpc1": '447',
                "vpc8": '669',
                "vpc6": '891',
                "vpc4": '114',
                "vpc2": '336',
                "vpc9": '558',
                "vpc7": '780',
                "hpr": '086419753',
                "hpl": '024691358',
                "lc": '3'
            },
            '8': {
                "vpc8": '916',
                "vpc7": '471',
                "vpc6": '027',
                "vpc5": '582',
                "vpc4": '138',
                "vpc3": '693',
                "vpc2": '249',
                "vpc1": '804',
                "vpc9": '360',
                "hpr": '049382716',
                "hpl": '395061728'
            },
            '9': {
                "vpc1": '950',
                "vpc2": '950',
                "vpc3": '950',
                "vpc4": '950',
                "vpc5": '950',
                "vpc6": '950',
                "vpc7": '950',
                "vpc8": '950',
                "vpc9": '950',
                "hpr": '0',
                "hpl": '9',
                "lc": '4'
            }
        }

    def sum_digits(self, s: str) -> int:
        """Sum the digits of a string."""
        return sum(int(ch) for ch in s if ch.isdigit())

    def reduce_to_single_digit(self, n: int) -> int:
        """Reduce a number to a single digit by repeatedly summing digits."""
        while n >= 10:
            n = self.sum_digits(str(n))
        return n

    def split_number(self, number_str: str, num_parts: int) -> List[str]:
        """Split the string into roughly equal parts for threading (kept for compatibility)."""
        length = len(number_str)
        part_size = length // num_parts
        parts = []
        for i in range(num_parts):
            start = i * part_size
            end = (i + 1) * part_size if i < num_parts - 1 else length
            parts.append(number_str[start:end])
        return parts

    # --- UPDATED: digit_reducer now uses RepdigitCache (no threading) ---
    def digit_reducer(self, number_str: str, num_threads: int) -> int:
        """
        Reduce a repdigit string to its digital root using the prebuilt repdigit cache.

        Assumptions: `number_str` is always a non-empty repdigit string of decimal digits.
        """
        rep_digit_char = number_str[0]   # e.g., '2'
        d = int(rep_digit_char)          # '2' -> 2
        L = len(number_str)              # full repdigit length
        return self.repdigit_cache.getDigitalRoot(repdigit=d, repdigitlength=L)

    def pad_with_patterns(self, length: int, leftPattern: str, rightPattern: str, constant: str, rep_digit: str) -> str:
        start_time_pad = time.perf_counter()

        def build_left(pattern: str, target_len: int) -> str:
            if not pattern or target_len <= 0:
                return ""
            full_repeats = target_len // len(pattern)
            remaining = target_len % len(pattern)
            return (pattern * full_repeats) + pattern[:remaining]

        def build_right(pattern: str, target_len: int) -> str:
            if not pattern or target_len <= 0:
                return ""
            full_repeats = target_len // len(pattern)
            remaining = target_len % len(pattern)
            return (pattern[-remaining:] + (pattern * full_repeats)) if remaining > 0 else (pattern * full_repeats)

        # If rpr is present, the old code did: right_pad = right_pad[1:]
        # Avoid that extra copy by building one fewer char from the start.
        has_rpr = "rpr" in self.matrix.get(rep_digit, {})
        right_len = length - 1 if has_rpr else length

        right_pad = build_right(rightPattern, right_len)
        logger.debug("building right pattern complete: %.6f s", time.perf_counter() - start_time_pad)

        left_pad = build_left(leftPattern, length)
        logger.debug("building left pattern complete: %.6f s", time.perf_counter() - start_time_pad)

        logger.debug("pad_with_patterns complete: %.6f s", time.perf_counter() - start_time_pad)
        #return left_pad + constant + right_pad
        return ''.join((left_pad, constant, right_pad))

    def increment_by_gmpy_count(self, k: ManualBigNumber, n: ManualBigNumber, count: int):
        count_int = int(count)
        if count_int > 0:
            total = gmpy2.mpz(n)
            k_int = gmpy2.mpz(k)
            for i in range(1, count_int + 1):
                total += k_int + i
            return total
        return n

    def increment_by_count(self, k: ManualBigNumber, n: ManualBigNumber, count: int):
        count_int = int(count)
        if count_int > 0:
            total = int(n)
            k_int = int(k.value)
            for i in range(1, count_int + 1):
                total += k_int + i
            return total
        return n

    def repDigitTriangularNumber(self, rep_digit: 'ManualBigNumber') -> 'ManualBigNumber':
        # Reduce digit using cache-based digital root (constant time)
        start_time = time.perf_counter()
        reduced = self.digit_reducer(rep_digit, 4)  # num_threads ignored now, kept for compatibility
        logger.debug("rep digit reducer complete: %.6f s", time.perf_counter() - start_time)

        # "Formula length - 2"
        rep_str = rep_digit.value if isinstance(rep_digit, ManualBigNumber) else str(rep_digit)
        length = len(rep_str) - 2
        logger.debug("length operation complete: %.6f s", time.perf_counter() - start_time)
        # Get Right Horizontal Pattern for rep digit
        leftPattern = self.matrix.get(rep_str[0], {}).get("hpl")
        logger.debug("got leftPattern complete: %.6f s", time.perf_counter() - start_time)
        # Get Left Horizontal Pattern for rep digit
        rightPattern = self.matrix.get(rep_str[0], {}).get("hpr")
        logger.debug("got rightPattern complete: %.6f s", time.perf_counter() - start_time)
        # Find constant with reduced number
        constant = self.matrix.get(rep_str[0], {}).get("vpc" + str(reduced), 0)

        result = self.pad_with_patterns(length, leftPattern, rightPattern, constant, rep_str[0])
        logger.debug("padding complete: %.6f s", time.perf_counter() - start_time)
        if "lc" in self.matrix.get(rep_str[0], {}):
            #result = self.matrix.get(rep_str[0], {}).get("lc") + result
            result = ''.join((self.matrix.get(rep_str[0], {}).get("lc", ""), result))
        return result
    



    def build_left_stream(
        self,
        pattern: str,
        target_len: int,
        out_f: TextIO,
        chunk_chars: int = 8_388_608,
        on_chunk=None,
        offset_base: int = 0,
    ) -> int:
        """
        Stream-write the left pad (left-aligned repetition) to an open text file handle.
        Optionally calls on_chunk(chunk_str, offset) for window extraction / collection.
        Returns number of characters written.
        """
        if not pattern or target_len <= 0:
            return 0

        plen = len(pattern)
        full_repeats, remaining = divmod(target_len, plen)

        reps_per_chunk = max(1, chunk_chars // plen)
        chunk = pattern * reps_per_chunk

        written = 0

        while full_repeats >= reps_per_chunk:
            if on_chunk:
                on_chunk(chunk, offset_base + written)
            out_f.write(chunk)
            written += len(chunk)
            full_repeats -= reps_per_chunk

        if full_repeats:
            tail = pattern * full_repeats
            if on_chunk:
                on_chunk(tail, offset_base + written)
            out_f.write(tail)
            written += len(tail)

        if remaining:
            rem_str = pattern[:remaining]
            if on_chunk:
                on_chunk(rem_str, offset_base + written)
            out_f.write(rem_str)
            written += len(rem_str)

        return written


    def build_right_stream(
        self,
        pattern: str,
        target_len: int,
        out_f: TextIO,
        chunk_chars: int = 8_388_608,
        on_chunk=None,
        offset_base: int = 0,
    ) -> int:
        """
        Stream-write the right pad (right-aligned repetition) to an open text file handle.
        Optionally calls on_chunk(chunk_str, offset) for window extraction / collection.
        Returns number of characters written.
        """
        if not pattern or target_len <= 0:
            return 0

        plen = len(pattern)
        full_repeats, remaining = divmod(target_len, plen)

        written = 0

        # Right-aligned leading suffix
        if remaining:
            lead = pattern[-remaining:]
            if on_chunk:
                on_chunk(lead, offset_base + written)
            out_f.write(lead)
            written += len(lead)

        reps_per_chunk = max(1, chunk_chars // plen)
        chunk = pattern * reps_per_chunk

        while full_repeats >= reps_per_chunk:
            if on_chunk:
                on_chunk(chunk, offset_base + written)
            out_f.write(chunk)
            written += len(chunk)
            full_repeats -= reps_per_chunk

        if full_repeats:
            tail = pattern * full_repeats
            if on_chunk:
                on_chunk(tail, offset_base + written)
            out_f.write(tail)
            written += len(tail)

        return written


    def pad_with_patterns_stream(
        self,
        length: int,
        leftPattern: str,
        rightPattern: str,
        constant: str,
        rep_digit: str,
        out_f: TextIO,
        chunk_chars: int = 8_388_608,
        on_chunk=None,
        offset_base: int = 0,
    ) -> int:
        """
        Stream-write:
            left_pad(length) + constant + right_pad(adjusted_length_if_rpr)
        to an open file handle.

        Optionally calls on_chunk(chunk_str, offset) for extraction/collection.
        Returns number of characters written (excluding any lc prefix handled by caller).
        """
        start_time_pad = time.perf_counter()

        has_rpr = "rpr" in self.matrix.get(rep_digit, {})
        right_len = (length - 1) if has_rpr else length
        if right_len < 0:
            right_len = 0

        written = 0

        # Left pad
        t0 = time.perf_counter()
        w_left = self.build_left_stream(
            leftPattern, length, out_f,
            chunk_chars=chunk_chars,
            on_chunk=on_chunk,
            offset_base=offset_base + written
        )
        written += w_left
        logger.debug("building left pattern complete (stream): %.6f s", time.perf_counter() - t0)

        # Constant (small)
        const_str = str(constant)
        if const_str:
            if on_chunk:
                on_chunk(const_str, offset_base + written)
            out_f.write(const_str)
            written += len(const_str)

        # Right pad
        t1 = time.perf_counter()
        w_right = self.build_right_stream(
            rightPattern, right_len, out_f,
            chunk_chars=chunk_chars,
            on_chunk=on_chunk,
            offset_base=offset_base + written
        )
        written += w_right
        logger.debug("building right pattern complete (stream): %.6f s", time.perf_counter() - t1)

        logger.debug("pad_with_patterns_stream complete: %.6f s", time.perf_counter() - start_time_pad)
        return written


    def repDigitTriangularNumberStream(
        self,
        rep_digit: 'ManualBigNumber',
        out_path: Optional[str] = None,
        chunk_chars: int = 8_388_608,
        *,
        extract_ranges=None,
        collect_result: bool = False,
    ):
        """
        Stream-based alternative to repDigitTriangularNumber() with optional window extraction.

        - Always writes the full output to disk in chunks.
        - Optionally extracts specified ranges without loading the full output into memory.
        - Optionally collects the entire output in memory (collect_result=True) for validation.

        Backward compatibility:
        - If extract_ranges is None and collect_result is False -> returns out_path (str) like before.
        - Otherwise -> returns dict with out_path, extracted windows, timing, etc.
        """
        start_time = time.perf_counter()

        rep_str = rep_digit.value if isinstance(rep_digit, ManualBigNumber) else str(rep_digit)

        reduced = self.digit_reducer(rep_str, 4)
        logger.debug("rep digit reducer complete (stream): %.6f s", time.perf_counter() - start_time)

        length = len(rep_str) - 2
        logger.debug("length operation complete (stream): %.6f s", time.perf_counter() - start_time)

        rep_char = rep_str[0]

        leftPattern = self.matrix.get(rep_char, {}).get("hpl", "")
        logger.debug("got leftPattern complete (stream): %.6f s", time.perf_counter() - start_time)

        rightPattern = self.matrix.get(rep_char, {}).get("hpr", "")
        logger.debug("got rightPattern complete (stream): %.6f s", time.perf_counter() - start_time)

        constant = self.matrix.get(rep_char, {}).get("vpc" + str(reduced), "0")
        logger.debug("got constant complete (stream): %.6f s", time.perf_counter() - start_time)

        if out_path is None:
            out_path = f"tri_matrix_{rep_char}_{len(rep_str)}.txt"

        # ---- Optional extraction setup ----
        # Normalize extract_ranges to list of (int,int) tuples (accept list-of-lists from JSON).
        extracted = {}
        if extract_ranges:
            norm = []
            for a, b in extract_ranges:
                a = int(a); b = int(b)
                if a < 0 or b < a:
                    raise ValueError(f"Invalid extract range {(a, b)}")
                norm.append((a, b))
                extracted[(a, b)] = []
            extract_ranges = norm

        collected_parts = [] if collect_result else None

        def on_chunk(chunk: str, offset: int):
            # Optional full collection (WARNING: massive memory if output is huge)
            if collect_result:
                collected_parts.append(chunk)

            # Optional window extraction
            if extracted:
                chunk_start = offset
                chunk_end = offset + len(chunk)
                for (a, b), pieces in extracted.items():
                    if chunk_end <= a or chunk_start >= b:
                        continue
                    s = max(a, chunk_start) - chunk_start
                    e = min(b, chunk_end) - chunk_start
                    pieces.append(chunk[s:e])

        # Stream write to disk
        t_write = time.perf_counter()
        total_written = 0

        with open(out_path, "w", encoding="utf-8", buffering=1024 * 1024) as out_f:
            # Optional lc prefix
            if "lc" in self.matrix.get(rep_char, {}):
                lc = self.matrix.get(rep_char, {}).get("lc", "")
                if lc:
                    if extract_ranges or collect_result:
                        on_chunk(lc, 0)
                    out_f.write(lc)
                    total_written += len(lc)

            # Main pads + constant + right
            total_written += self.pad_with_patterns_stream(
                length=length,
                leftPattern=leftPattern,
                rightPattern=rightPattern,
                constant=constant,
                rep_digit=rep_char,
                out_f=out_f,
                chunk_chars=chunk_chars,
                on_chunk=(on_chunk if (extract_ranges or collect_result) else None),
                offset_base=total_written,
            )

        logger.debug("stream write complete: %.6f s", time.perf_counter() - t_write)
        elapsed = time.perf_counter() - start_time
        logger.info("repDigitTriangularNumberStream complete: %.6f s", elapsed)

        # Backward compatible return
        if not extract_ranges and not collect_result:
            return out_path

        extracted_str = {rng: "".join(pieces) for rng, pieces in extracted.items()}

        out = {
            "out_path": out_path,
            "repdigit": rep_char,
            "repdigit_length": len(rep_str),
            "generated_chars": total_written,
            "elapsed_seconds": elapsed,
            "extracted": extracted_str,
        }

        if collect_result:
            out["result"] = "".join(collected_parts)

        return out
        




    def build_left_memory(self, pattern: str, target_len: int, chunk_chars: int = 8_388_608):
        """
        Yield left pad chunks (left-aligned repetition) without building the full string.
        """
        if not pattern or target_len <= 0:
            return
            yield  # makes this a generator even on early return

        plen = len(pattern)
        full_repeats, rem = divmod(target_len, plen)

        reps_per_chunk = max(1, chunk_chars // plen)
        chunk = pattern * reps_per_chunk  # reusable chunk string

        while full_repeats >= reps_per_chunk:
            yield chunk
            full_repeats -= reps_per_chunk

        if full_repeats:
            yield pattern * full_repeats

        if rem:
            yield pattern[:rem]


    def build_right_memory(self, pattern: str, target_len: int, chunk_chars: int = 8_388_608):
        """
        Yield right pad chunks (right-aligned repetition) without building the full string.

        Matches build_right():
            (pattern[-rem:] + pattern*full_repeats) if rem>0 else (pattern*full_repeats)
        """
        if not pattern or target_len <= 0:
            return
            yield

        plen = len(pattern)
        full_repeats, rem = divmod(target_len, plen)

        if rem:
            yield pattern[-rem:]  # leading suffix for right-aligned padding

        reps_per_chunk = max(1, chunk_chars // plen)
        chunk = pattern * reps_per_chunk  # reusable chunk string

        while full_repeats >= reps_per_chunk:
            yield chunk
            full_repeats -= reps_per_chunk

        if full_repeats:
            yield pattern * full_repeats


    def pad_with_patterns_memory(
        self,
        length: int,
        leftPattern: str,
        rightPattern: str,
        constant: str,
        rep_digit: str,
        *,
        chunk_chars: int = 8_388_608,
        on_chunk=None,
    ):
        """
        Generate (left_pad + constant + right_pad) in chunks and call on_chunk(chunk, offset).

        - Does NOT return the full string.
        - offset is the starting character index of the chunk in the full output.
        """
        t0 = time.perf_counter()

        has_rpr = "rpr" in self.matrix.get(rep_digit, {})
        right_len = (length - 1) if has_rpr else length
        if right_len < 0:
            right_len = 0

        offset = 0

        # Left pad
        t_left = time.perf_counter()
        for ch in self.build_left_memory(leftPattern, length, chunk_chars=chunk_chars):
            if on_chunk:
                on_chunk(ch, offset)
            offset += len(ch)
        logger.debug("building left pattern complete (memory-chunks): %.6f s", time.perf_counter() - t_left)

        # Constant (small)
        const_str = str(constant)
        if const_str:
            if on_chunk:
                on_chunk(const_str, offset)
            offset += len(const_str)

        # Right pad
        t_right = time.perf_counter()
        for ch in self.build_right_memory(rightPattern, right_len, chunk_chars=chunk_chars):
            if on_chunk:
                on_chunk(ch, offset)
            offset += len(ch)
        logger.debug("building right pattern complete (memory-chunks): %.6f s", time.perf_counter() - t_right)

        logger.debug("pad_with_patterns_memory complete: %.6f s", time.perf_counter() - t0)
        return offset  # total chars generated


    def repDigitTriangularNumberMemory(
        self,
        rep_digit: "ManualBigNumber",
        *,
        chunk_chars: int = 8_388_608,
        extract_ranges=None,
        collect_result: bool = False,
    ):
        """
        Memory-optimized alternative that generates output in chunks and optionally:
        - extracts one or more ranges (start,end) without materializing full output, and/or
        - collects the full output (collect_result=True) for correctness comparison.

        Returns dict with timing + extracted slices; if collect_result=True also returns 'result'.
        """
        start_time = time.perf_counter()

        rep_str = rep_digit.value if isinstance(rep_digit, ManualBigNumber) else str(rep_digit)
        rep_char = rep_str[0]

        # Digital root reduction (cache-based)
        reduced = self.digit_reducer(rep_str, 4)
        logger.debug("rep digit reducer complete (memory-chunks): %.6f s", time.perf_counter() - start_time)

        length = len(rep_str) - 2
        leftPattern = self.matrix.get(rep_char, {}).get("hpl", "")
        rightPattern = self.matrix.get(rep_char, {}).get("hpr", "")
        constant = self.matrix.get(rep_char, {}).get("vpc" + str(reduced), "0")

        # Optional leading constant prefix
        lc_prefix = self.matrix.get(rep_char, {}).get("lc", "") if "lc" in self.matrix.get(rep_char, {}) else ""

        # Prepare extraction
        # extract_ranges: list of (start,end) with 0-based indexing; end is exclusive.
        extracted = {}
        if extract_ranges:
            for i, (a, b) in enumerate(extract_ranges):
                if a < 0 or b < a:
                    raise ValueError(f"Invalid extract range {(a, b)}")
                extracted[(a, b)] = []  # list of pieces

        collected_parts = [] if collect_result else None

        def on_chunk(chunk: str, offset: int):
            # Collect full output if requested (WARNING: can be huge)
            if collect_result:
                collected_parts.append(chunk)

            # Extract ranges if requested (without storing whole output)
            if extracted:
                chunk_start = offset
                chunk_end = offset + len(chunk)
                for (a, b), pieces in extracted.items():
                    if chunk_end <= a or chunk_start >= b:
                        continue  # no overlap
                    s = max(a, chunk_start) - chunk_start
                    e = min(b, chunk_end) - chunk_start
                    pieces.append(chunk[s:e])

        # Emit lc prefix first (so offsets match true full output)
        offset = 0
        if lc_prefix:
            on_chunk(lc_prefix, offset)
            offset += len(lc_prefix)

        # Emit pads + constant + right in chunks
        total_chars = self.pad_with_patterns_memory(
            length=length,
            leftPattern=leftPattern,
            rightPattern=rightPattern,
            constant=constant,
            rep_digit=rep_char,
            chunk_chars=chunk_chars,
            on_chunk=lambda ch, off: on_chunk(ch, off + offset),
        )
        total_chars += offset

        # Finalize extracted strings
        extracted_str = {rng: "".join(pieces) for rng, pieces in extracted.items()}

        out = {
            "repdigit": rep_char,
            "repdigit_length": len(rep_str),
            "generated_chars": total_chars,
            "elapsed_seconds": time.perf_counter() - start_time,
            "extracted": extracted_str,
        }

        if collect_result:
            out["result"] = "".join(collected_parts)

        logger.info("repDigitTriangularNumberMemory complete: %.6f s", out["elapsed_seconds"])
        return out
    


    def _repeat_slice_left(self, pattern: str, start: int, end: int) -> str:
        """
        Slice [start:end) from infinite left repetition of `pattern`: patternpatternpattern...
        Efficient for window sizes ~100..1000.
        """
        if not pattern or end <= start:
            return ""
        p = len(pattern)
        length = end - start
        phase = start % p

        # First partial
        first = pattern[phase:]
        if len(first) >= length:
            return first[:length]

        parts = [first]
        remaining = length - len(first)

        # Full repeats
        q, r = divmod(remaining, p)
        if q:
            parts.append(pattern * q)
        if r:
            parts.append(pattern[:r])
        return "".join(parts)


    def _repeat_slice_right(self, pattern: str, total_len: int, start: int, end: int) -> str:
        """
        Slice [start:end) from RIGHT-aligned repetition of pattern with total length = total_len.

        This matches your build_right() semantics:
        right_pad = pattern[-rem:] + pattern*full_repeats   if rem>0 else pattern*full_repeats
        where rem = total_len % len(pattern)

        We avoid constructing right_pad, by using a phase shift:
        base_phase = (p - rem) % p
        char at right_pad[i] = pattern[(base_phase + i) % p]
        """
        if not pattern or end <= start or total_len <= 0:
            return ""
        p = len(pattern)
        if p == 0:
            return ""

        # Clamp to [0, total_len]
        start = max(0, min(start, total_len))
        end = max(0, min(end, total_len))
        if end <= start:
            return ""

        rem = total_len % p
        base_phase = (p - rem) % p  # aligns the right edge

        # Convert to a slice of infinite left repetition starting at phase (base_phase + start) % p
        phase0 = (base_phase + start) % p
        length = end - start

        first = pattern[phase0:]
        if len(first) >= length:
            return first[:length]

        parts = [first]
        remaining = length - len(first)

        q, r = divmod(remaining, p)
        if q:
            parts.append(pattern * q)
        if r:
            parts.append(pattern[:r])
        return "".join(parts)


    def _extract_window_from_descriptor(
        self,
        *,
        start: int,
        end: int,
        lc: str,
        left_len: int,
        Lconst: str,
        Vconst: str,
        right_len: int,
        Rconst: str,
    ) -> str:
        """
        Extract substring [start:end) from the final TN output:
        lc + left_pad + Vconst + right_pad
        without building left/right pads fully.
        """
        if end <= start:
            return ""

        lc_len = len(lc)
        v_len = len(Vconst)

        # Segment boundaries (absolute, includes lc)
        s0 = 0
        e0 = lc_len
        s1 = e0
        e1 = s1 + max(0, left_len)
        s2 = e1
        e2 = s2 + v_len
        s3 = e2
        e3 = s3 + max(0, right_len)

        parts: List[str] = []

        # 1) lc
        if start < e0 and end > s0 and lc_len > 0:
            a = max(start, s0)
            b = min(end, e0)
            parts.append(lc[a:b])

        # 2) left pad
        if start < e1 and end > s1 and left_len > 0:
            a = max(start, s1) - s1
            b = min(end, e1) - s1
            parts.append(self._repeat_slice_left(Lconst, a, b))

        # 3) Vconst
        if start < e2 and end > s2 and v_len > 0:
            a = max(start, s2) - s2
            b = min(end, e2) - s2
            parts.append(Vconst[a:b])

        # 4) right pad
        if start < e3 and end > s3 and right_len > 0:
            a = max(start, s3) - s3
            b = min(end, e3) - s3
            parts.append(self._repeat_slice_right(Rconst, right_len, a, b))

        return "".join(parts)


    def _merge_ranges(self, ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Sort and merge overlapping/adjacent [start,end) ranges.
        This reduces repeated work for 1000 windows.
        """
        if not ranges:
            return []
        ranges = sorted(ranges, key=lambda x: (x[0], x[1]))
        merged = [ranges[0]]
        for a, b in ranges[1:]:
            pa, pb = merged[-1]
            if a <= pb:  # overlap or adjacent
                merged[-1] = (pa, max(pb, b))
            else:
                merged.append((a, b))
        return merged


    def repDigitTriangularNumberRandomAccess(
        self,
        rep_digit: "ShortFormBigNumber",
        *,
        extract_ranges=None,
        collect_result: bool = False,
        compressed_tn_result: bool = True,
    ):
        """
        Random-access window extractor for the TN output generated by TNM rules.

        - Base 10 only.
        - Never expands the full TN unless collect_result=True and compressed_tn_result=False.
        - Uses repdigit family rules (lc/rpr) internally for correct indexing and reconstruction,
        but does NOT include lc/rpr in the compressed output.

        Returns:
        dict with:
            - compressed (if compressed_tn_result=True)
            - extracted windows (if extract_ranges provided)
            - metadata (lengths, elapsed time)
            - result (only if collect_result=True and compressed_tn_result=False)
        """
        t0 = time.perf_counter()

        # ---- Validate short form ----
        if rep_digit.b != 10:
            raise ValueError("repDigitTriangularNumberRandomAccess currently supports base b=10 only.")
        if rep_digit.n not in range(1, 10):
            raise ValueError("repdigit n must be in {1..9}.")
        if rep_digit.l <= 0:
            raise ValueError("repdigit length l must be positive.")

        rep_char = str(rep_digit.n)
        l = int(rep_digit.l)

        # ---- Compute reduced lane and constants (without expanding repdigit) ----
        reduced = self.repdigit_cache.getDigitalRoot(repdigit=rep_digit.n, repdigitlength=l)

        # Patterns / constants from matrix
        Lconst = self.matrix.get(rep_char, {}).get("hpl", "")
        Rconst = self.matrix.get(rep_char, {}).get("hpr", "")
        Vconst = self.matrix.get(rep_char, {}).get("vpc" + str(reduced), "")

        # Family-dependent flags (used internally only)
        lc = self.matrix.get(rep_char, {}).get("lc", "")  # optional prefix
        has_rpr = "rpr" in self.matrix.get(rep_char, {})

        left_len = l - 2
        if left_len < 0:
            left_len = 0

        right_len = (left_len - 1) if has_rpr else left_len
        if right_len < 0:
            right_len = 0

        # Cutoffs as lengths (your naming)
        Lcutoff = (left_len % len(Lconst)) if Lconst else 0
        Rcutoff = (right_len % len(Rconst)) if Rconst else 0

        total_len = len(lc) + left_len + len(Vconst) + right_len

        # ---- Build compressed descriptor (Option A) ----
        compressed = None
        if compressed_tn_result:
            compressed = {
                "b": 10,
                "repdigit": rep_digit.n,
                "l": l,
                "Lconst": Lconst,
                "Lcutoff": Lcutoff,
                "Vconst": Vconst,
                "Rconst": Rconst,
                "Rcutoff": Rcutoff,
            }

        # ---- Extract windows (random access) ----
        extracted: Dict[Tuple[int, int], str] = {}

        if extract_ranges:
            # normalize to list of (int,int) tuples
            norm: List[Tuple[int, int]] = []
            for a, b in extract_ranges:
                a = int(a); b = int(b)
                if a < 0 or b < a:
                    raise ValueError(f"Invalid extract range {(a, b)}")
                # allow b > total_len (will just clamp by segment intersections)
                norm.append((a, b))

            # merge ranges for speed
            merged = self._merge_ranges(norm)

            # compute merged window strings
            merged_map: Dict[Tuple[int, int], str] = {}
            for (a, b) in merged:
                merged_map[(a, b)] = self._extract_window_from_descriptor(
                    start=a,
                    end=b,
                    lc=lc,
                    left_len=left_len,
                    Lconst=Lconst,
                    Vconst=Vconst,
                    right_len=right_len,
                    Rconst=Rconst,
                )

            # map each original window by slicing its merged parent
            # (single pass with pointer because both lists are sorted)
            merged_sorted = sorted(merged)
            m_idx = 0
            for (a, b) in norm:
                while m_idx < len(merged_sorted) and merged_sorted[m_idx][1] < a:
                    m_idx += 1
                # find the merged range that contains (a,b)
                # because merged ranges were created from norm, each (a,b) must be within some merged range
                # but if b > merged_end due to out-of-range, we still slice safely
                # (use the first merged that overlaps)
                if m_idx >= len(merged_sorted):
                    extracted[(a, b)] = ""
                    continue

                ma, mb = merged_sorted[m_idx]
                # If the current merged doesn't cover a (due to pointer drift), search forward
                j = m_idx
                while j < len(merged_sorted) and not (merged_sorted[j][0] <= a <= merged_sorted[j][1]):
                    j += 1
                if j >= len(merged_sorted):
                    extracted[(a, b)] = ""
                    continue
                ma, mb = merged_sorted[j]

                big = merged_map[(ma, mb)]
                s = max(0, a - ma)
                e = max(0, b - ma)
                extracted[(a, b)] = big[s:e]

        # ---- Collect full result (ONLY if requested and compression disabled) ----
        full_result = None
        if collect_result and (not compressed_tn_result):
            # Expand strictly from descriptor + family rules (lc/rpr), for validation.
            # WARNING: this may be huge; intended for small l / correctness tests.
            left_full = ""
            if Lconst and left_len > 0:
                p = len(Lconst)
                q, r = divmod(left_len, p)
                left_full = (Lconst * q) + Lconst[:r]

            right_full = ""
            if Rconst and right_len > 0:
                p = len(Rconst)
                q, r = divmod(right_len, p)
                right_full = (Rconst[-r:] + (Rconst * q)) if r > 0 else (Rconst * q)

            # lc derived from repdigit family
            full_result = "".join((lc, left_full, Vconst, right_full))

        elapsed = time.perf_counter() - t0

        out = {
            "repdigit": rep_digit.n,
            "l": l,
            "reduced": reduced,
            "total_len": total_len,
            "left_len": left_len,
            "right_len": right_len,
            "Vlen": len(Vconst),
            "elapsed_seconds": elapsed,
            "extracted": extracted,
        }
        if compressed_tn_result:
            out["compressed"] = compressed
        if full_result is not None:
            out["result"] = full_result

        return out