"""
Unit tests for repdigit_cache.py.

Tests the cache building, getValue (digit sum), and getDigitalRoot directly.
These are foundational — calculator.py depends on this for all constant selection.

Usage:
    .venv/bin/python -m pytest tests/test_repdigit_cache.py -v
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.repdigit_cache import RepdigitCache


@pytest.fixture(scope="module")
def cache():
    c = RepdigitCache()
    c.build_cache(repdigit=1, min_cache_block=10, max_cache_block=10_000_000_000)
    c.build_cache(repdigit=2, min_cache_block=10, max_cache_block=10_000_000_000)
    c.build_cache(repdigit=9, min_cache_block=10, max_cache_block=10_000_000_000)
    return c


def test_getValue_single_digit(cache):
    assert cache.getValue(repdigit=2, repdigitlength=1) == 2
    assert cache.getValue(repdigit=9, repdigitlength=1) == 9
    assert cache.getValue(repdigit=1, repdigitlength=1) == 1


def test_getValue_small(cache):
    # Ten 2s: digit sum = 20
    assert cache.getValue(repdigit=2, repdigitlength=10) == 20
    # 100 nines: digit sum = 900
    assert cache.getValue(repdigit=9, repdigitlength=100) == 900


def test_getValue_decomposition(cache):
    # repdigit=2, length=132342 → sum = 2*132342 = 264684
    assert cache.getValue(repdigit=2, repdigitlength=132_342) == 264_684


def test_getValue_zero_length(cache):
    assert cache.getValue(repdigit=2, repdigitlength=0) == 0


def test_getDigitalRoot_known_values(cache):
    # digital root of 20 (ten 2s): 2+0 = 2
    assert cache.getDigitalRoot(repdigit=2, repdigitlength=10) == 2
    # digital root of 9 (one 9): 9
    assert cache.getDigitalRoot(repdigit=9, repdigitlength=1) == 9
    # digital root of 900 (100 nines): 9+0+0 = 9
    assert cache.getDigitalRoot(repdigit=9, repdigitlength=100) == 9


def test_getDigitalRoot_divisible_by_9(cache):
    # digit sum = 9 * N → digital root should be 9, not 0
    # repdigit=9, length=1: sum=9 → digital root=9
    assert cache.getDigitalRoot(repdigit=9, repdigitlength=1) == 9
    # repdigit=9, length=9: sum=81 → 8+1=9 → digital root=9
    assert cache.getDigitalRoot(repdigit=9, repdigitlength=9) == 9


def test_getCacheBlock_basic(cache):
    # blockkey=1 → length 10, sum = repdigit * 10
    assert cache.getCacheBlock(repdigit=2, blockkey=1) == 20
    assert cache.getCacheBlock(repdigit=9, blockkey=1) == 90


def test_invalid_repdigit_raises():
    c = RepdigitCache()
    with pytest.raises(ValueError):
        c.build_cache(repdigit=10, min_cache_block=10, max_cache_block=100)


def test_invalid_length_raises(cache):
    with pytest.raises(ValueError):
        cache.getValue(repdigit=2, repdigitlength=-1)
