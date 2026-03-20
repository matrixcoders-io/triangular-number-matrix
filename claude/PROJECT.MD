# PROJECT.MD — Triangular Number Matrix Calculator

> Last updated: 2026-03-20

---

## What This Project Is

A **POC → Production** calculator that demonstrates a novel mathematical framework for computing triangular numbers of astronomically large **repdigit numbers** (e.g. 3333…3333 with 10 billion digits) in near-constant time — without using the classic `Tn = n(n+1)/2` division formula, which breaks down at massive scale.

The core insight: triangular numbers of repdigit numbers follow deterministic, repeating **vertical constants** and **horizontal patterns**. The calculator *assembles* the answer from those patterns rather than computing it arithmetically.

---

## Mathematical Core

### Repdigit Numbers
A number made entirely of one repeated digit: `2`, `22`, `222`, `2222`, etc.

### Key Discovery
For any repdigit `d` of length `L`, its triangular number `T(ddd…d)` always takes the form:

```
[Left Horizontal Pattern] + [Vertical Constant] + [Right Horizontal Pattern]
```

- **Vertical Pattern Constants (vpc)**: 9 repeating 3-digit constants per digit (e.g. for `d=2`: `253, 475, 697, 919, 141, 364, 586, 808, 030`)
- **Horizontal Patterns**: Left (hpl) and Right (hpr) — 9-digit patterns appended outward from the constant
- **Length Formula**: `pad_length = L - 2`
- **Constant selection**: determined by the **digital root** of the repdigit number (`reduce_to_single_digit`)

### Special digits
- `3`, `6`, `9`: simpler patterns — all vpcs are identical (`561`, `2211`, `950`)
- `1`, `2`, `4`, `5`, `7`, `8`: 9 distinct vpcs + 9-digit hpl/hpr; some have a Left Constant (`lc`) prefix
- Digit `1` has `rpr=Y` flag (right pad is 1 char shorter)

### Non-repdigit proximity
The system can also compute triangular numbers **close to** a repdigit by using `increment_by_gmpy_count`: jump to the nearest repdigit Tn, then increment/decrement by counting up from that anchor.

---

## Codebase Overview

### Core Logic
| File | Role |
|------|------|
| `calculator.py` | Main math engine — **do not modify without care** |
| `repdigit_cache.py` | Precomputes repdigit digit sums & digital roots at powers-of-10 block sizes |

### Web Layer
| File | Role |
|------|------|
| `app.py` | Flask app — routes, operation dispatch, stats logging |
| `templates/index.html` | Browser UI |

### Support Scripts
| File | Role |
|------|------|
| `post_numbers.py` | HTTP POST to Flask `/rep-digit-math` endpoint with a file and operation |
| `generate_numbers.py` | Generates repdigit number files |
| `integration_test.sh` | Runs a series of operations via `post_numbers.py` |
| `check_diff.sh` | Compares two output files for validity |
| `benchmark_catalog_read.py` | Benchmarks random-access reads on large output files |
| `window_extraction_count.py` | Utilities for counting extracted window characters |
| `window_collection_generator.py` | Generates `windows.json` configs for window extraction |
| `file_extractor_generator.sh` | Generates shortform big number files (`-sf.txt`) |
| `base_calc.py` | Baseline/reference calculator (likely for comparison) |

### Static Assets
| Path | Contents |
|------|----------|
| `static/numbers/` | Pregenerated repdigit input files (1k → 5B digits) |
| `static/configs/windows.json` | Window (start,end) pairs for extraction |
| `static/output/tn-files/` | Full triangular number output files |
| `static/output/we-files/` | Window-extracted output files |
| `static/output/stat-files/` | Timing stats per operation |

---

## Calculator Operations (app.py dispatch)

| Operation key | Method | Description |
|---|---|---|
| `tri_matrix` | `repDigitTriangularNumber()` | In-memory string assembly (standard) |
| `tri_matrix_stream` | `repDigitTriangularNumberStream()` | Chunk-writes to disk, optional window extraction |
| `tri_matrix_memory` | `repDigitTriangularNumberMemory()` | Generator-based chunked, no disk write |
| `tri_matrix_random` | `repDigitTriangularNumberRandomAccess()` | Random window access from ShortFormBigNumber |
| `tri_div_gmpy2_formula` | `triangular_number_gmpy2_division()` | Classic `n(n+1)/2` via gmpy2 (baseline comparison) |
| `tri_div_simpy_formula` | `triangular_number_sympi_division()` | Classic formula via sympy (slower baseline) |
| `add/subtract/multiply/divide` | `ManualBigNumber.*` | Manual big-number arithmetic (helper ops) |

---

## Key Classes

### `ManualBigNumber`
- Manual big-number arithmetic (add, subtract, multiply, divide)
- Triangular number via classic division (sympy, gmpy2)
- Input is always a **decimal digit string**

### `TriangulaNumberMatrix`
- The pattern-based matrix engine
- Holds the `matrix` dict with vpc/hpl/hpr/lc/rpr constants for digits 1–9
- All 4 calculation modes (standard, stream, memory, random access)
- Uses `RepdigitCache` for digital root computation

### `ShortFormBigNumber`
- Compact notation for huge repdigit numbers: `b=10, l=1233, n=2` = ten 2s of length 1233
- Used by `tri_matrix_random` for window access without materializing the full number

### `RepdigitCache`
- Precomputes block sums at powers of 10 for digits 1–9
- `getValue(repdigit, length)` → digit sum via block decomposition
- `getDigitalRoot(repdigit, length)` → digital root (1–9)
- Singleton built at module load, used across all requests

---

## Data Flow (Typical Request)

```
Browser / post_numbers.py
    → POST /rep-digit-math (or /)
    → app.py: handle_big_number_math()
        → loads num1 from form or file (static/numbers/)
        → dispatches to calculator.py method
        → writes output to static/output/
        → writes stats to static/output/stat-files/
    → returns elapsed time (API) or renders index.html (WEB)
```

---

## Critical Bugs — Must Fix Before Production

| ID | Severity | File | Description | Status |
|----|----------|------|-------------|--------|
| BUG-001 | **CRITICAL** | `calculator.py` | Digit 8 triangular number is 1 character shorter than gmpy2 baseline for 999-digit inputs. `digit_reducer` returns `reduced=9` (→ vpc9=`360`) but correct constant is `vpc1=804`. Digital root of (8×999=7992): 7992%9==0 → returns 9, but math expects a different mapping. All 3 matrix modes affected. Test marked `xfail` in `tests/test_1k_operations.py`. **Do not release to production until resolved.** | Open — needs research paper review |

---

## Known Issues / Tech Debt (Observed, Not Yet Addressed)

- `app.py` has duplicate `Flask()` instantiation (`app = Flask(...)` appears twice — line 9 and line 18)
- `app.config['MAX_CONTENT_LENGTH']` is set to an astronomically large literal integer (cosmetic/risky)
- `calculator.py` has leftover `print()` debug statements throughout (not structured logging)
- `sys.set_int_max_str_digits(...)` is called twice with different values (line 11 then 13) — second wins
- `tri_matrix_memory` operation has `print(...) - start_time` without `str()` wrap — will raise `TypeError` at line 187
- No input validation beyond `isdigit()` checks
- No structured error logging in Flask — exceptions caught and returned as plain strings

---

## Refactoring / Enhancement Goals (POC → Production)

### Phase 0 — Bug Fixes (remind user before starting)
- Fix duplicate `Flask()` instantiation in `app.py`
- Fix `TypeError` on `app.py:187` (missing `str()` around `time.perf_counter()`)
- Fix duplicate `sys.set_int_max_str_digits()` call in `calculator.py`
- Replace `print()` debug statements with structured logging throughout `calculator.py`
- Clean up absurdly large `MAX_CONTENT_LENGTH` literal in `app.py`

### Tech Stack Decision
- **Backend**: Flask (Python)
- **Frontend**: Jinja2 templates + HTMX + Vanilla JS (no React/Vue)
- **UI Layout**: Single-page — all panels (calculator, stats, lab, file browser) as sections/tabs on one page. May move Lab to `/lab` later if complexity demands it.

### Phase 1 — Structural Refactor (folder/component reorganization)
Reorganize from flat POC structure into a proper production app layout. Exact structure TBD, but guided by:
- Separate UI component folder (stats panel, file browser, run controls, number viewer) — expected to get complex
- Clean separation: core math engine / Flask routes / UI templates / test infrastructure
- All script logic (`integration_test.sh`, `post_numbers.py`, `check_diff.sh`, etc.) must be triggerable from UI

### Phase 2 — UI Enhancements
All of the following should be operable through the web UI (no manual scripts needed):

**Number Input & Display**
- Support 1B+ digit inputs without crashing the browser
- Partial display of output: user specifies `[start_index : end_index]` window to view
- Page-scroll / index navigation through huge triangular number outputs
- File browser for `static/numbers/` — show file size on disk, **character/digit count** (read from file metadata or calculate if cheap), select file to feed calculator
- Preview portion of selected input file in a text area

**Calculator Enhancements**
- Display Vertical Pattern Constants and Horizontal Patterns in UI when applicable (dynamically update as user changes input digit)
- Show which constant (`vpc*`) was selected and why (based on digital root)

**Stats & Runs**
- Display run statistics in UI (repdigit, length, generated chars, elapsed time, file load time)
- History of runs visible in UI
- Download triangular number output files from UI

**Lab / Experiment Panel** (separate section/folder in UI)
- Trigger integration tests from UI
- Trigger unit tests from UI and show pass/fail results
- Show file sizes of all output files
- Compare output files (diff check) from UI

### Phase 3 — Testing
- Unit tests (pytest) verifying correctness of all 4 matrix modes against each other and against gmpy2 baseline
- Integration tests verify output files in `static/output/tn-files/` match expected results
- ShortForm validation: reconstruct/expand a shortform number from stats output and compare to full output (automated)
- Tests runnable from UI (Phase 2 lab panel) and from CLI

### Phase 4 — Non-repdigit / increment support
- `increment_by_gmpy_count` polish and testing (secondary priority)
- UI support for specifying count offset from nearest repdigit anchor

---

## Reference Files

| File | Purpose |
|------|---------|
| `tmp/triangular_numbers_matrix_new_final.pdf` | Research paper — **authoritative source** for math |
| `CALC-NOTES.md` | Older notes with visual explanations (partially outdated vs PDF) |
| `images/` | Diagrams referenced in CALC-NOTES.md |
| `claude/CLAUDE.MD` | Claude Code behavioral rules for this project |
| `claude/PROJECT.MD` | This file — project context and architecture |
