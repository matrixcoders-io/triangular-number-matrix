import os
import re
import sys
import time

# Match tuple-key dict entries: (digits, digits): '  OR  (digits,digits): "
ENTRY_RE = re.compile(rb"\(\s*\d+\s*,\s*\d+\s*\)\s*:\s*['\"]")

def count_windows(path: str, chunk_size: int = 16 * 1024 * 1024, overlap: int = 512, progress: bool = False) -> int:
    """
    Counts how many extracted windows exist in a file that looks like:
      {(466956, 467710): '....', (24807113, 24807238): '....', ...}

    Streaming: does NOT load the full file.
    """
    total = 0
    carry = b""
    processed = 0
    size = os.path.getsize(path)

    t0 = time.perf_counter()
    next_report = 0

    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            data = carry + chunk

            # Keep a small overlap so matches crossing boundary aren't missed
            if len(data) > overlap:
                process = data[:-overlap]
                carry = data[-overlap:]
            else:
                carry = data
                continue

            total += len(ENTRY_RE.findall(process))
            processed += len(chunk)

            if progress:
                pct = int((processed / size) * 100) if size else 0
                now = time.perf_counter()
                if now >= next_report:
                    print(f"[{pct:3d}%] scanned {processed:,} / {size:,} bytes | windows={total:,}", flush=True)
                    next_report = now + 0.5  # report twice per second (no spam)

    # final tail
    total += len(ENTRY_RE.findall(carry))

    if progress:
        dt = time.perf_counter() - t0
        print(f"[100%] done | windows={total:,} | elapsed={dt:.2f}s", flush=True)

    return total

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 window_extraction_count.py <path> [--progress]")
        sys.exit(1)

    path = sys.argv[1]
    progress = ("--progress" in sys.argv)

    n = count_windows(path, progress=progress)
    print("Windows extracted:", n)

if __name__ == "__main__":
    main()