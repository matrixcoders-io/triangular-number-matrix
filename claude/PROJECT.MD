# PROJECT.MD — Triangular Number Matrix Calculator

> Last updated: 2026-03-21 (session 2) | Current phase: Phase 2 in progress — pyramid display algorithm unresolved

---

## What This Project Is

A **POC → Production** calculator demonstrating a novel mathematical framework for computing triangular numbers of astronomically large **repdigit numbers** (e.g. 3333…3333 with 10 billion digits) in near-constant time — without using classic `T(n) = n(n+1)/2` arithmetic division, which breaks down at massive scale.

The core insight: triangular numbers of repdigit numbers follow deterministic, repeating **vertical constants** and **horizontal patterns**. The calculator *assembles* the answer from those patterns rather than computing it.

---

## Mathematical Core

### Repdigit Numbers
A number made entirely of one repeated digit: `2`, `22`, `222`, `2222`, etc.

### Pattern Assembly
For any repdigit `d` of length `L`, its triangular number takes the form:
```
[lc prefix?] + [hpl tiled] + [vpc constant] + [hpr tiled]
```

- **vpc1–vpc9** — 3–4 char vertical pattern constant. Which one to use: `vpc{digital_root(d × L)}`
- **hpl** — horizontal pattern left (9-char tile, repeated left of vpc)
- **hpr** — horizontal pattern right (9-char tile, repeated right of vpc)
- **lc** — optional 1-char left prefix (digits 5, 7, 9 only)
- **rpr** — flag for digit 1: right pad is 1 char shorter than left

### Digital Root
`DR(n) = 1 + (n-1) % 9` (or 9 if `n % 9 == 0`). Used to select vpc. Computed by `_REPDIGIT_CACHE.getDigitalRoot(digit, length)`.

### Special Digits
- `3`, `6`, `9` — all 9 vpcs are identical (`561`, `2211`, `950`); simpler assembly
- `1`, `2`, `4`, `5`, `7`, `8` — 9 distinct vpcs + distinct hpl/hpr
- Digit `1` has `rpr=Y` — one fewer character on right side

### Non-repdigit Proximity
`increment_by_gmpy_count(num1, result, offset)` — jump to nearest repdigit T(n), then add/subtract `offset` via gmpy2 counting. Phase 4 item.

---

## Current Project Structure (Phase 1 refactor complete)

```
triangular-number-matrix/
├── app.py                          ← Flask entry point (slim — registers blueprints)
├── config.py                       ← All configuration constants and env vars
├── core/
│   ├── calculator.py               ← TriangulaNumberMatrix, ManualBigNumber, ShortFormBigNumber
│   └── repdigit_cache.py           ← RepdigitCache singleton (_REPDIGIT_CACHE)
├── api/
│   └── routes/
│       ├── calculator.py           ← calculator_bp: GET / and POST /calc (HTMX), POST /rep-digit-math
│       ├── files.py                ← files_bp: GET /files/list, GET /files/preview
│       ├── stats.py                ← stats_bp: GET /stats/history, POST /stats/history/clear
│       └── lab.py                  ← lab_bp: POST /lab/run-tests, GET /lab/run-tests/stream
├── ui/
│   └── templates/
│       ├── base.html               ← Base layout (header, HTMX CDN, CSS/JS links)
│       ├── index.html              ← Main single-page UI (7 panels)
│       └── partials/
│           └── result_panel.html   ← HTMX partial swap target for calculation results
├── static/
│   ├── numbers/                    ← Pregenerated repdigit input files (1k → 5B digits)
│   ├── configs/windows.json        ← Window (start, end) extraction pairs
│   ├── output/
│   │   ├── tn-files/               ← Full triangular number output files
│   │   ├── we-files/               ← Window-extracted output files
│   │   └── stat-files/             ← Timing stats + run_history.json
│   └── ui/
│       ├── css/main.css            ← All UI styles
│       └── js/app.js               ← All UI JavaScript
├── tests/
│   └── test_1k_operations.py       ← Integration tests (42 pass, 3 xfail expected)
├── claude/
│   ├── CLAUDE.MD                   ← Claude behavioral rules
│   ├── PROJECT.MD                  ← This file
│   └── QA_RULES.MD                 ← QA rules, component glossary, phase gate checklist
└── tmp/
    └── triangular_numbers_matrix_new_final.pdf  ← Authoritative math research paper
```

### Legacy root files (not yet deleted — confirm before removing)
`calculator.py`, `repdigit_cache.py`, `base_calc.py`, `templates/` at project root — original POC files superseded by `core/` and `ui/templates/`.

---

## Flask Routes

| Blueprint | Route | Method | Request Type | Returns |
|-----------|-------|--------|--------------|---------|
| `calculator_bp` | `/` | GET | WEB | Full `index.html` |
| `calculator_bp` | `/calc` | POST | HTMX | `partials/result_panel.html` partial |
| `calculator_bp` | `/rep-digit-math` | GET/POST | API | Elapsed time plain text |
| `files_bp` | `/files/list` | GET | JSON | Array of file metadata dicts |
| `files_bp` | `/files/preview` | GET | Text | Raw file content (stripped) |
| `stats_bp` | `/stats/history` | GET | JSON/HTML | Run history |
| `stats_bp` | `/stats/history/clear` | POST | Action | Clears history |
| `lab_bp` | `/lab/run-tests` | POST | HTMX | pytest output HTML |
| `lab_bp` | `/lab/run-tests/stream` | GET | SSE | Streaming pytest output |

---

## Calculator Operations

| Form `operation` value | Core method | Notes |
|------------------------|-------------|-------|
| `tri_matrix` | `repDigitTriangularNumber()` | In-memory string assembly. Returns `str`. |
| `tri_matrix_stream` | `repDigitTriangularNumberStream()` | Chunk-writes to disk. Use `collect_result=True` for web UI. Returns dict. |
| `tri_matrix_memory` | `repDigitTriangularNumberMemory()` | Generator-based chunks. Use `collect_result=True` for web UI. Returns dict. |
| `tri_matrix_random` | `repDigitTriangularNumberRandomAccess()` | Random window access from ShortFormBigNumber. Returns dict. |
| `tri_div_gmpy2_formula` | `triangular_number_gmpy2_division()` | Classic n(n+1)/2 via gmpy2. Ground truth baseline. |
| `tri_div_simpy_formula` | `triangular_number_sympi_division()` | Classic formula via sympy. Slower than gmpy2. |
| `add/subtract/multiply/divide` | `ManualBigNumber.*` | Manual big-number arithmetic helpers. |

**Critical rule**: For web UI, all dict-returning modes (`tri_matrix_stream`, `tri_matrix_memory`, `tri_matrix_random`) must use `collect_result=True`. With `collect_result=False`, the TN string is never built in memory — result stays a stats dict, and `str(dict)` gets displayed instead of the triangular number.

---

## Key Classes

### `TriangulaNumberMatrix` (`core/calculator.py`)
Main calculator. `TriangulaNumberMatrix("1")` — constructor arg is legacy/unused. Holds `self.matrix` dict (all vpc/hpl/hpr/lc/rpr for digits 1–9). All 4 calculation modes live here.

### `ManualBigNumber` (`core/calculator.py`)
String-based big number wrapper. Arithmetic methods + fallback TN methods (gmpy2, sympy).

### `ShortFormBigNumber` (`core/calculator.py`)
Frozen dataclass: `b` (base), `l` (length), `n` (digit). Parsed via `ShortFormBigNumber.from_ops(ops_string)`. Used by `tri_matrix_random`.

### `RepdigitCache` (`core/repdigit_cache.py`)
Precomputed block-sum cache for digits 1–9 up to 10 billion. Powers constant-time digital root lookups. Module-level singleton `_REPDIGIT_CACHE` — **never reinstantiate per request**.

---

## Config Variables (`config.py`)

| Variable | Default | Env var | Purpose |
|----------|---------|---------|---------|
| `NUMBERS_DIR` | `static/numbers` | — | Source repdigit input files |
| `TN_OUT_FILE` | `static/output/tn-files/tn-file.txt` | — | Base path for TN output files |
| `WE_FILES_DIR` | `static/output/we-files` | — | Window extraction output dir |
| `STAT_FILES_DIR` | `static/output/stat-files` | — | Stat files and run history dir |
| `WINDOWS_JSON` | `static/configs/windows.json` | — | Window extraction config |
| `UI_HTTP_FILE_TRANSFER` | `True` | `UI_HTTP_FILE_TRANSFER` | Enable/disable HTTP file preview (`true`/`false`) |
| `UI_HTTP_FILE_MAX_DIGITS` | `10_000_000` | `UI_HTTP_FILE_MAX_DIGITS` | Max digits allowed over HTTP preview |

---

## Data Flow (Typical Calculation)

```
Browser
  → POST /calc (HTMX, hx-target="#result-panel")
  → api/routes/calculator.py: handle_big_number_math("HTMX")
      → file mode check:
          disk mode + file_name → read from NUMBERS_DIR (server side)
          http mode → num1 already in POST body from textarea
      → dispatch to core/calculator.py method (collect_result=True)
      → write output files to static/output/
      → append run to static/output/stat-files/run_history.json
      → compute result_str, result_total_chars, result_preview (cap 10,000)
  → render partials/result_panel.html (partial swap)
  → JS htmx:afterSwap → onResultSwap() → reads #result-full → enables nav
  → JS dispatches calcDone event → history panel auto-refreshes
```

---

## UI Architecture (Phase 2)

### Stack
- **HTMX** — partial swaps, no page reloads
- **Vanilla JS** (`static/ui/js/app.js`) — constants panel, file browser, result nav, event wiring
- **Jinja2** (`ui/templates/`) — server-side rendering

### 7 UI Panels (page order)

| # | Panel | ID / Class | Purpose |
|---|-------|-----------|---------|
| 1 | Calculator | `#calculator-form` | Number input, method select, calculate button |
| 2 | Matrix Constants | `.constants-panel` | VPC grid, hpl/hpr, digit selector (auto-updates on input) |
| 3 | Result | `#result-panel` | HTMX swap target — shows TN output, nav, stats |
| 4 | File Library | `.file-panel` | Scrollable list of `NUMBERS_DIR` files with "Use" buttons |
| 5 | Run History | `#history-panel` | Collapsible; auto-refreshes after each calc via `calcDone` event |
| 6 | Lab — Test Suite | `#lab-panel` | Collapsible; triggers pytest via `POST /lab/run-tests` |
| 7 | File Input Mode | `#file-mode-panel` | Radio: Disk-Direct vs HTTP Transfer (secondary config, bottom of page) |

### Key JS Functions (`static/ui/js/app.js`)

| Function | Purpose |
|----------|---------|
| `digitalRoot(n)` | DR(n) = 1+(n-1)%9 or 9 |
| `repdigitDigitalRoot(digit, length)` | DR of repdigit in JS |
| `detectRepdigit(str)` | Detects if textarea content is a repdigit |
| `updateConstantsPanel(digitStr, activeVpcKey)` | Refreshes VPC grid + patterns |
| `onNumberInput(e)` | Auto-detects repdigit, updates constants panel |
| `getFileMode()` | Reads `input[name="ui_file_mode"]:checked` → `'disk'` or `'http'` |
| `setDiskHiddenField(filename)` | Sets `#file-name-hidden` + `#disk-file-indicator` |
| `initFileBrowser()` | "Use" button handler (always previews in textarea; disk mode also sets hidden field) |
| `initResultNav()` / `navTo(offset)` | 200-char sliding window through `_resultFull` |
| `onResultSwap()` | Reads `#result-full` after HTMX swap, resets nav |
| `colorizeMethodBadges()` | Applies colour map to `.method-badge` elements |

### File Input Mode (important wiring detail)
The File Input Mode radio is **outside the calculator form** (bottom of page). Two hidden fields inside the form sync it:
- `#file-name-hidden` (name=`file_names`) — set by JS on disk selection
- `#file-mode-hidden` (name=`file_mode`) — synced from radio via inline `<script>` on page

Flask reads `file_mode` to decide whether to read from disk or use the `num1` textarea value.

### HTMX Event Flow
1. `POST /calc` → swaps `partials/result_panel.html` into `#result-panel`
2. `htmx:afterSwap` → `onResultSwap()` + dispatches `calcDone` custom event on `document.body`
3. History panel: `hx-trigger="load, calcDone from:body"` → auto-refreshes on each calc

---

## Result Display Rules

- Flask computes `result_str`, `result_total_chars = len(result_str)`, `result_preview = result_str[:10000]`
- Template receives `result` (max 10K chars) and `result_total_chars` (actual full count)
- `<pre id="result-full" style="display:none;">{{ result }}</pre>` — JS reads this for nav
- Shows amber warning when `result_total_chars > 10000`
- Nav window: 200 chars visible, keyboard shortcuts Alt+←/→

---

## Run History

- Stored in `static/output/stat-files/run_history.json` (max 50 entries, newest at end)
- Written by `api/routes/calculator.py` after each successful calculation
- Schema: `{ts, method, repdigit, length, result_chars, elapsed}`
- Read/written via `_load_history()` / `_save_history()` in `api/routes/stats.py`

---

## Critical Rules (learned from bugs)

1. **`.strip()` on file reads** — `read_file_content()` must `.strip()` the result. A trailing newline increases `len(number_str)` by 1, shifts DR by 1, selects wrong vpc. Produces wrong TN silently.

2. **`file_load_time = "0"` not `0`** — used in string concatenation for stat file writes. Must be `str`.

3. **`collect_result=True` for web** — all dict-returning calculator modes must use this flag. Without it, `result` is a stats-only dict — `str(dict)` gets displayed instead of the TN.

4. **`if file_mode == "disk" and file_name`** — guard must check both conditions. `if file_name` alone reads from disk even in HTTP mode if the hidden field has a stale value from a previous disk selection.

5. **`_REPDIGIT_CACHE` is a module-level singleton** — never reinstantiate per request.

6. **File write paths need `os.makedirs(..., exist_ok=True)`** before writing stat/output files.

---

## Known Bugs

### BUG-001 — Digit 8 Wrong Constant (CRITICAL, do not release)

| Field | Detail |
|-------|--------|
| **Affects** | All 3 matrix modes (`tri_matrix`, `tri_matrix_stream`, `tri_matrix_memory`) |
| **Trigger** | Digit 8 repdigit with 999-digit length |
| **Symptom** | Result is 1 character shorter than gmpy2 baseline |
| **Root cause** | DR(8 × 999 = 7992): 7992 % 9 == 0 → returns 9 → selects vpc9=`360`. But gmpy2 implies vpc1=`804` is correct. Math paper review required. |
| **Test status** | Marked `xfail(strict=True)` in `tests/test_1k_operations.py` |
| **Action** | **Do not fix without reviewing the research paper.** Do not remove xfail marker. |

---

## Phase Status

| Phase | Status | Summary |
|-------|--------|---------|
| Phase 0 — Bug Fixes | ✅ Complete | Fixed duplicate Flask init, TypeError, logging, file_load_time string type |
| Phase 1 — Structural Refactor | ✅ Complete | Blueprints, core/, ui/templates/, static/ui/, config.py |
| Phase 2 — UI Enhancements | 🔄 In Progress | HTMX partial swaps, VPC constants panel, file browser, run history, lab panel, file input mode toggle, result nav, 10K display cap — **Pyramid display BROKEN** (delta design shows hollow triangle; need cumulative cap=10 design) |
| Phase 3 — Testing Expansion | 🔲 Next | Expand test coverage, all 4 modes × all 9 digits, edge cases |
| Phase 4 — Non-repdigit / Increment | 🔲 Planned | Polish `increment_by_gmpy_count`, UI support for offset input |

### Pending Cleanup
- Delete legacy root files (`calculator.py`, `repdigit_cache.py`, `base_calc.py`, `templates/` at project root) — confirm with user first, ensure new structure works
- `MAX_CONTENT_LENGTH` in original `app.py` was an astronomically large literal — already resolved in new slim `app.py`

---

## Reference Files

| File | Purpose |
|------|---------|
| `tmp/triangular_numbers_matrix_new_final.pdf` | Research paper — **authoritative source for all math decisions** |
| `claude/CLAUDE.MD` | Claude Code behavioral rules (approval workflow, skill suggestions) |
| `claude/QA_RULES.MD` | Full QA rules, component glossary, phase gate checklist |
| `static/configs/windows.json` | Window extraction pairs used by stream/memory/random modes |
