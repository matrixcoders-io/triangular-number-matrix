import json
import random
from typing import List, Tuple


def generate_windows(
    total_len: int,
    *,
    count: int = 1000,
    min_size: int = 100,
    max_size: int = 1000,
    seed: int = 1234,
) -> List[Tuple[int, int]]:
    """
    Create `count` windows (start,end) with sizes in [min_size, max_size],
    all within [0, total_len). `end` is exclusive.
    """
    if total_len <= 0:
        raise ValueError("total_len must be > 0")
    if min_size <= 0 or max_size < min_size:
        raise ValueError("Invalid size range")
    if count <= 0:
        return []

    rng = random.Random(seed)
    windows: List[Tuple[int, int]] = []

    # Helper to clamp start so end doesn't exceed total_len
    def pick_start(size: int, lo: int, hi: int) -> int:
        # valid start range is [0, total_len - size]
        max_start = max(0, total_len - size)
        lo = max(0, min(lo, max_start))
        hi = max(0, min(hi, max_start))
        if hi < lo:
            lo, hi = hi, lo
        return rng.randint(lo, hi)

    for i in range(count):
        size = rng.randint(min_size, max_size)

        mode = i % 4
        if mode == 0:
            # early region: first 5%
            start = pick_start(size, 0, int(0.05 * total_len))
        elif mode == 1:
            # middle region: around 50% ± 5%
            mid = int(0.50 * total_len)
            span = int(0.05 * total_len)
            start = pick_start(size, mid - span, mid + span)
        elif mode == 2:
            # late region: last 5%
            start = pick_start(size, int(0.95 * total_len), total_len)
        else:
            # random anywhere
            start = pick_start(size, 0, total_len)

        windows.append((start, start + size))

    return windows


def save_windows_json(path: str, windows: List[Tuple[int, int]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(windows, f)


# Example usage:
if __name__ == "__main__":
    total_len = 50_000_000  # example total output length
    count = 100
    windows = generate_windows(total_len, count=count, min_size=100, max_size=1000, seed=42)
    save_windows_json("static/configs/windows_"+str(count)+".json", windows)
    print("Saved", len(windows), "windows to windows_"+str(count)+".json")