"""
repdigit_cache.py

Repdigit cache blocks for fast digit-sum assembly (for scalable reduction workflows).

- build_cache(repdigit, min_cache_block, max_cache_block)
    builds cache blocks at powers of 10 lengths: 10, 100, 1000, ...

Cache key scheme (implicit in methods):
    blockkey = k  <=> block length = 10^k
So for repdigit=2:
    k=1 => length=10  => sum=20
    k=2 => length=100 => sum=200
    ...
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class CacheBlock:
    repdigit: int
    blockkey: int          # number of zeros k where length = 10^k
    block_length: int      # 10^k
    block_sum: int         # digit sum of [repdigit]^(10^k) = repdigit * 10^k


def _is_power_of_ten(n: int) -> bool:
    if n <= 0:
        return False
    while n % 10 == 0:
        n //= 10
    return n == 1


def _zeros_count(power_of_ten: int) -> int:
    """Return k where power_of_ten == 10^k. Assumes input is a power of 10."""
    k = 0
    n = power_of_ten
    while n > 1:
        if n % 10 != 0:
            raise ValueError(f"{power_of_ten} is not a power of 10.")
        n //= 10
        k += 1
    return k


def _digital_root(x: int) -> int:
    """Digital root of a non-negative integer x (returns 0..9)."""
    if x < 0:
        raise ValueError("digital_root input must be non-negative.")
    if x == 0:
        return 0
    r = x % 9
    return 9 if r == 0 else r


class RepdigitCache:
    """
    Stores cache blocks per repdigit:
        self._cache[repdigit][k] = CacheBlock for length 10^k
    """

    def __init__(self) -> None:
        self._cache: Dict[int, Dict[int, CacheBlock]] = {}

    def build_cache(
        self,
        repdigit: int,
        min_cache_block: int = 10,
        max_cache_block: int = 10_000_000_000,
        *,
        overwrite: bool = True,
    ) -> Dict[int, CacheBlock]:
        """
        Build cache blocks for a given repdigit at lengths 10^k from min_cache_block to max_cache_block.

        Example:
            build_cache(repdigit=2, min_cache_block=10, max_cache_block=10_000)
        creates keys k=1..4 (10,100,1000,10000) for repdigit=2.

        Returns:
            Dict mapping blockkey k -> CacheBlock
        """
        if not isinstance(repdigit, int) or not (0 <= repdigit <= 9):
            raise ValueError("repdigit must be an integer digit in [0..9].")

        if not _is_power_of_ten(min_cache_block) or min_cache_block < 10:
            raise ValueError("min_cache_block must be a power of 10 and >= 10 (e.g., 10, 100, 1000).")
        if not _is_power_of_ten(max_cache_block) or max_cache_block < min_cache_block:
            raise ValueError("max_cache_block must be a power of 10 and >= min_cache_block.")

        k_min = _zeros_count(min_cache_block)
        k_max = _zeros_count(max_cache_block)

        if repdigit not in self._cache:
            self._cache[repdigit] = {}
        rep_cache = self._cache[repdigit]

        # Smart build: build smallest, then multiply by 10 each step
        # k=1 => length 10, sum = repdigit * 10
        k = 1
        length = 10
        block_sum = repdigit * length  # e.g., 2*10=20

        while k <= k_max:
            if k >= k_min:
                if overwrite or (k not in rep_cache):
                    rep_cache[k] = CacheBlock(
                        repdigit=repdigit,
                        blockkey=k,
                        block_length=length,
                        block_sum=block_sum,
                    )

            # next block from previous block (your requested method):
            # 10^k -> 10^(k+1): length *= 10, block_sum *= 10
            k += 1
            length *= 10
            block_sum *= 10

        return rep_cache

    def _ensure_cache_up_to(self, repdigit: int, max_blockkey: int) -> None:
        """
        Ensure cache blocks exist up to blockkey=max_blockkey for repdigit.
        Builds missing keys without overwriting existing entries.
        """
        if max_blockkey < 1:
            return
        rep_cache = self._cache.get(repdigit, {})
        current_max = max(rep_cache.keys()) if rep_cache else 0
        if current_max >= max_blockkey:
            return

        # Build from 10 to 10^max_blockkey; do not overwrite existing
        self.build_cache(
            repdigit=repdigit,
            min_cache_block=10,
            max_cache_block=10 ** max_blockkey,
            overwrite=False,
        )

    # ---- Methods you asked for ----

    def getCacheBlock(self, *, repdigit: int, blockkey: int) -> int:
        """
        Return the cached block sum for [repdigit]^(10^blockkey).

        Example:
            getCacheBlock(repdigit=2, blockkey=1) -> 20  (ten 2's sum to 20)
        """
        if blockkey < 1:
            raise ValueError("blockkey must be >= 1 (since 10^1 is the smallest cached block).")
        self._ensure_cache_up_to(repdigit, blockkey)
        try:
            return self._cache[repdigit][blockkey].block_sum
        except KeyError as e:
            raise KeyError(
                f"Cache block not found for repdigit={repdigit}, blockkey={blockkey}. "
                f"Build the cache first (build_cache) or ensure parameters are valid."
            ) from e

    def getValue(self, *, repdigit: int, repdigitlength: int) -> int:
        """
        Return the digit-sum value of the repdigit [repdigit]^repdigitlength by composing cached blocks.

        Example:
            repdigit=2, repdigitlength=132342
            decomposes length into powers of 10:
                132342 = 1*100000 + 3*10000 + 2*1000 + 3*100 + 4*10 + 2
            and computes:
                sum = 1*sum([2]^100000) + 3*sum([2]^10000) + ... + 2*2
        """
        if not isinstance(repdigitlength, int) or repdigitlength < 0:
            raise ValueError("repdigitlength must be a non-negative integer.")
        if not isinstance(repdigit, int) or not (0 <= repdigit <= 9):
            raise ValueError("repdigit must be an integer digit in [0..9].")

        if repdigitlength == 0:
            return 0

        # Determine largest blockkey needed: 10^k <= repdigitlength
        # Example: length=132342 => k=5 (100000)
        max_blockkey = len(str(repdigitlength)) - 1  # because 10^(digits-1) <= n < 10^digits
        if max_blockkey >= 1:
            self._ensure_cache_up_to(repdigit, max_blockkey)

        remaining = repdigitlength
        total_sum = 0

        # Greedy decomposition by powers of 10 (works because blocks are 10^k)
        for k in range(max_blockkey, 0, -1):
            block_len = 10 ** k
            q, remaining = divmod(remaining, block_len)
            if q:
                total_sum += q * self.getCacheBlock(repdigit=repdigit, blockkey=k)

        # remaining is < 10 now; sum directly
        total_sum += remaining * repdigit
        return total_sum

    def getDigitalRoot(self, *, repdigit: int, repdigitlength: int) -> int:
        """
        Compute the digital root of the repdigit [repdigit]^repdigitlength
        by first computing its digit-sum via getValue().
        """
        digit_sum = self.getValue(repdigit=repdigit, repdigitlength=repdigitlength)
        return _digital_root(digit_sum)

    # Optional utility
    def clear(self) -> None:
        self._cache.clear()


if __name__ == "__main__":
    c = RepdigitCache()
    c.build_cache(repdigit=2, min_cache_block=10, max_cache_block=10_000_000_000)
    print("2-1 (10):", c.getCacheBlock(repdigit=2, blockkey=1))  # 20
    print("sum([2]^132342):", c.getValue(repdigit=2, repdigitlength=132_342))  # 264684
    print("digital root:", c.getDigitalRoot(repdigit=2, repdigitlength=132_342))