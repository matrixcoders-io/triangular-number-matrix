/**
 * app.js — Triangular Number Matrix UI
 *
 * Responsibilities:
 *  - MATRIX constants data (all 9 digits with vpc1–vpc9, hpl, hpr, lc, rpr)
 *  - Digital root computation in JS (mirrors Python digit_reducer logic)
 *  - Constants panel: digit selector, vpc grid, pattern/badge updates
 *  - Auto-detect repdigit from textarea and update constants panel
 *  - File browser "Use" button → loads file content into number textarea
 *  - Collapsible section toggles
 *  - Result panel: window navigation (prev/next/goto)
 *  - HTMX lifecycle hooks (loading states, result fade-in)
 */

'use strict';

/* ============================================================
   MATRIX CONSTANTS DATA
   Source: core/calculator.py TriangulaNumberMatrix.matrix
   ============================================================ */
const MATRIX = {
  '1': {
    vpc1: '104', vpc2: '660', vpc3: '216', vpc4: '771',
    vpc5: '327', vpc6: '882', vpc7: '438', vpc8: '993', vpc9: '549',
    hpr: '049382716', hpl: '617283950', rpr: 'Y'
  },
  '2': {
    vpc1: '919', vpc2: '030', vpc3: '141', vpc4: '253',
    vpc5: '364', vpc6: '475', vpc7: '586', vpc8: '697', vpc9: '808',
    hpr: '086419753', hpl: '246913580'
  },
  '3': {
    vpc1: '561', vpc2: '561', vpc3: '561', vpc4: '561',
    vpc5: '561', vpc6: '561', vpc7: '561', vpc8: '561', vpc9: '561',
    hpr: '1', hpl: '5'
  },
  '4': {
    vpc1: '434', vpc2: '656', vpc3: '879', vpc4: '101',
    vpc5: '323', vpc6: '545', vpc7: '767', vpc8: '990', vpc9: '212',
    hpr: '123456790', hpl: '987654320'
  },
  '5': {
    vpc1: '540', vpc2: '317', vpc3: '095', vpc4: '873',
    vpc5: '651', vpc6: '429', vpc7: '206', vpc8: '984', vpc9: '762',
    hpr: '123456790', hpl: '543209876', lc: '1'
  },
  '6': {
    vpc1: '2211', vpc2: '2211', vpc3: '2211', vpc4: '2211',
    vpc5: '2211', vpc6: '2211', vpc7: '2211', vpc8: '2211', vpc9: '2211',
    hpr: '1', hpl: '2'
  },
  '7': {
    vpc1: '447', vpc2: '336', vpc3: '225', vpc4: '114',
    vpc5: '003', vpc6: '891', vpc7: '780', vpc8: '669', vpc9: '558',
    hpr: '086419753', hpl: '024691358', lc: '3'
  },
  '8': {
    vpc1: '804', vpc2: '249', vpc3: '693', vpc4: '138',
    vpc5: '582', vpc6: '027', vpc7: '471', vpc8: '916', vpc9: '360',
    hpr: '049382716', hpl: '395061728'
  },
  '9': {
    vpc1: '950', vpc2: '950', vpc3: '950', vpc4: '950',
    vpc5: '950', vpc6: '950', vpc7: '950', vpc8: '950', vpc9: '950',
    hpr: '0', hpl: '9', lc: '4'
  }
};

/* ============================================================
   DIGITAL ROOT (mirrors Python: digit_reducer / reduce_to_single_digit)
   digital_root(n) = 0 if n==0, else 1 + (n-1)%9
   ============================================================ */
function digitalRoot(n) {
  if (n === 0) return 0;
  const r = n % 9;
  return r === 0 ? 9 : r;
}

/**
 * Given a repdigit string "2222...2", return its digital root.
 * digit_sum = digit * length
 * digital_root = digitalRoot(digit_sum)
 */
function repdigitDigitalRoot(digit, length) {
  const digitSum = digit * length;
  return digitalRoot(digitSum);
}

/* ============================================================
   DETECT REPDIGIT from a raw number string
   Returns { isRepdigit, digit } or { isRepdigit: false }
   ============================================================ */
function detectRepdigit(str) {
  const s = str.trim().replace(/\s+/g, '');
  if (!s || !/^\d+$/.test(s)) return { isRepdigit: false };
  const first = s[0];
  if (s.split('').every(c => c === first)) {
    return { isRepdigit: true, digit: first, length: s.length };
  }
  return { isRepdigit: false };
}

/* ============================================================
   DETECT CONSTANTS from a computed result string
   Scans the result for a known hpl (identifies digit family), then
   finds the active vpc key via tile-alignment check (same logic as
   findBestVpcIdx). Falls back to first-occurrence if tile check misses
   (e.g. after increment where surrounding tiles changed).
   Returns { digit, vpcKey } or null.
   ============================================================ */
function detectConstantsFromResult(text, hintDigit = null) {
  // Fast path: digit family already known — skip hpl scan, just find the vpc key.
  // Prevents misidentification when increment shifts tiles near single-char hpl patterns.
  if (hintDigit && MATRIX[hintDigit]) {
    const data   = MATRIX[hintDigit];
    const hplLen = data.hpl.length;
    for (const key of vpcKeys) {
      const vpc = data[key];
      if (!vpc || vpc === '—') continue;
      let searchFrom = 0;
      while (searchFrom < text.length) {
        const idx = text.indexOf(vpc, searchFrom);
        if (idx === -1) break;
        for (let lr = 0; lr < hplLen; lr++) {
          if (idx >= hplLen + lr && text.slice(idx - hplLen - lr, idx - lr) === data.hpl) {
            return { digit: hintDigit, vpcKey: key };
          }
        }
        searchFrom = idx + 1;
      }
    }
    for (const key of vpcKeys) {
      const vpc = data[key];
      if (vpc && vpc !== '—' && text.includes(vpc)) return { digit: hintDigit, vpcKey: key };
    }
    // Fuzzy fallback: exact vpc not found (increment changed the constant).
    // Try 2-of-3 fuzzy match from center outward for each vpc key.
    for (const key of vpcKeys) {
      const vpc = data[key];
      if (!vpc || vpc === '—') continue;
      if (findFuzzyVpcIdx(text, vpc, data.hpl)) return { digit: hintDigit, vpcKey: key };
    }
    return { digit: hintDigit, vpcKey: null };
  }

  for (const [digit, data] of Object.entries(MATRIX)) {
    if (!text.includes(data.hpl)) continue;
    const hplLen = data.hpl.length;

    // Strict tile-alignment check: find the vpc whose occurrence sits
    // immediately after a complete hpl tile (verifies it's the real center).
    for (const key of vpcKeys) {
      const vpc = data[key];
      if (!vpc || vpc === '—') continue;
      let searchFrom = 0;
      let found = false;
      while (searchFrom < text.length) {
        const idx = text.indexOf(vpc, searchFrom);
        if (idx === -1) break;
        for (let lr = 0; lr < hplLen; lr++) {
          if (idx >= hplLen + lr && text.slice(idx - hplLen - lr, idx - lr) === data.hpl) {
            found = true; break;
          }
        }
        if (found) break;
        searchFrom = idx + 1;
      }
      if (found) return { digit, vpcKey: key };
    }

    // Fallback: tile-alignment missed (increment shifted surrounding tiles).
    // Pick the first vpc that appears anywhere in the text.
    for (const key of vpcKeys) {
      const vpc = data[key];
      if (vpc && vpc !== '—' && text.includes(vpc)) return { digit, vpcKey: key };
    }
    return { digit, vpcKey: null };
  }
  return null;
}

/* ============================================================
   CONSTANTS PANEL
   ============================================================ */
const vpcKeys = ['vpc1','vpc2','vpc3','vpc4','vpc5','vpc6','vpc7','vpc8','vpc9'];

// Persist the last calculated active constant so digit-family browsing doesn't clear it.
let _calcDigit     = null;  // digit family of the last calculation (e.g. '1')
let _calcActiveKey = null;  // vpc key of the last active constant (e.g. 'vpc3')

function updateConstantsPanel(digitStr, activeVpcKey) {
  const data = MATRIX[digitStr];
  if (!data) return;

  // Persist the active key so digit-family browsing can restore it.
  if (activeVpcKey) {
    _calcDigit     = digitStr;
    _calcActiveKey = activeVpcKey;
  }

  // Update digit selector active state
  document.querySelectorAll('.digit-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.digit === digitStr);
  });

  // Update VPC grid
  vpcKeys.forEach(key => {
    const item = document.querySelector(`.vpc-item[data-key="${key}"]`);
    if (!item) return;
    const valEl = item.querySelector('.vpc-value');
    if (valEl) valEl.textContent = data[key] ?? '—';
    item.classList.toggle('active', key === activeVpcKey);
  });

  // Patterns
  const hprEl = document.getElementById('const-hpr');
  const hplEl = document.getElementById('const-hpl');
  if (hprEl) hprEl.textContent = data.hpr ?? '—';
  if (hplEl) hplEl.textContent = data.hpl ?? '—';

  // Optional badges: lc, rpr
  const lcBadge  = document.getElementById('badge-lc');
  const rprBadge = document.getElementById('badge-rpr');
  if (lcBadge)  lcBadge.textContent  = data.lc  ? `— Left Pattern Padding Digit = ${data.lc}` : '';
  if (rprBadge) rprBadge.textContent = data.rpr ? `— Right Pattern Cutoff = r - 1`             : '';

  // Active indicator — Active Constant (violet) and Digital Root (green) displayed separately
  const constVal = document.getElementById('active-const-value');
  const drVal    = document.getElementById('active-dr-value');
  if (activeVpcKey) {
    const drNumber = activeVpcKey.replace('vpc', '');
    if (constVal) constVal.textContent = data[activeVpcKey] ?? '—';
    if (drVal)    drVal.textContent    = drNumber;
  }
}

/* ============================================================
   AUTO-DETECT: update panel when user types in number textarea
   ============================================================ */
function onNumberInput(e) {
  const { isRepdigit, digit, length } = detectRepdigit(e.target.value);
  const metaEl = document.getElementById('input-char-count');
  if (metaEl) {
    if (isRepdigit) {
      metaEl.innerHTML = `<strong style="color:var(--green)">${length.toLocaleString()}</strong><span style="color:var(--text-secondary)"> digits · repdigit </span><strong style="color:var(--gold)">${digit}</strong>`;
    } else if (e.target.value.trim()) {
      metaEl.textContent = `${e.target.value.trim().length.toLocaleString()} digits`;
    } else {
      metaEl.textContent = '';
    }
  }
  if (!isRepdigit) return;

  const dr = repdigitDigitalRoot(parseInt(digit), length);
  const activeKey = `vpc${dr}`;
  updateConstantsPanel(digit, activeKey);
}

/* ============================================================
   DIGIT SELECTOR BUTTONS — manual override
   ============================================================ */
function initDigitSelector() {
  document.querySelectorAll('.digit-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const d = btn.dataset.digit;
      const key = (d === _calcDigit) ? _calcActiveKey : null;
      updateConstantsPanel(d, key);
      // Load the minimum file for this digit family, then auto-calculate.
      await loadFile(`${d}-1k.txt`);
      document.querySelector('.btn-calculate')?.click();
    });
  });
  // Default: show digit 1 on load
  updateConstantsPanel('1', null);
}

/* ============================================================
   FILE MODE — disk-direct vs http transfer
   ============================================================ */
function getFileMode() {
  const checked = document.querySelector('input[name="ui_file_mode"]:checked');
  return checked ? checked.value : 'disk';
}

function setDiskHiddenField(filename) {
  const hidden = document.getElementById('file-name-hidden');
  if (hidden) hidden.value = filename;
  const label = document.getElementById('disk-file-name');
  if (label) label.textContent = filename;
  const indicator = document.getElementById('disk-file-indicator');
  if (indicator) indicator.style.display = filename ? 'block' : 'none';
}

function clearDiskHiddenField() {
  setDiskHiddenField('');
  const badge = document.getElementById('input-file-badge');
  if (badge) badge.textContent = '';
}

/* ============================================================
   FILE LOADER — shared by file browser Use buttons and digit selector
   ============================================================ */

/**
 * Load a number file: mark it selected in the UI, update Number Family,
 * set the disk hidden field (disk mode) or fetch content into textarea.
 * Returns a Promise that resolves when the textarea is populated.
 */
async function loadFile(filename) {
  if (!filename) return;

  // Mark row + button selected
  document.querySelectorAll('.file-table tr.selected').forEach(r => r.classList.remove('selected'));
  document.querySelectorAll('.btn-use.active').forEach(b => b.classList.remove('active'));
  const btn = document.querySelector(`.btn-use[data-filename="${CSS.escape(filename)}"]`);
  btn?.closest('tr')?.classList.add('selected');
  btn?.classList.add('active');

  // Update selected-file badge
  const badge = document.getElementById('input-file-badge');
  if (badge) badge.innerHTML = `<span style="color:var(--text-secondary)"> · filename </span><span style="color:var(--green)">◫</span> <strong style="color:var(--text-primary);font-weight:600">${filename}</strong>`;

  // Update Number Family from filename immediately (before async fetch).
  const fileDigit = filename.match(/^(\d)/)?.[1];
  if (fileDigit && MATRIX[fileDigit]) {
    _calcDigit     = null;
    _calcActiveKey = null;
    const sizeMatch = filename.match(/-(\d+)k\b/i);
    if (sizeMatch) {
      const length = parseInt(sizeMatch[1], 10) * 1000;
      const dr     = repdigitDigitalRoot(parseInt(fileDigit, 10), length);
      updateConstantsPanel(fileDigit, `vpc${dr}`);
    } else {
      updateConstantsPanel(fileDigit, null);
    }
  }

  const mode = getFileMode();
  if (mode === 'disk') {
    setDiskHiddenField(filename);
  } else {
    clearDiskHiddenField();
  }

  const ta = document.getElementById('number-input');
  if (ta) ta.value = mode === 'disk' ? 'Loading preview…' : 'Loading…';

  try {
    const resp = await fetch(`/files/preview?name=${encodeURIComponent(filename)}`);
    if (resp.ok) {
      const text         = await resp.text();
      const truncated    = resp.headers.get('X-Preview-Truncated') === 'true';
      const totalDigits  = parseInt(resp.headers.get('X-File-Digits') || '0', 10);
      if (ta) {
        ta.value = text;
        ta.dispatchEvent(new Event('input'));
        if (truncated) {
          const metaEl = document.getElementById('input-char-count');
          if (metaEl) metaEl.textContent =
            `${totalDigits.toLocaleString()} digits · showing first ${INPUT_DISPLAY_CAP.toLocaleString()}`;
        }
      }
    } else {
      if (mode === 'disk' && ta) {
        ta.value = '';
        ta.placeholder = `[Disk-Direct] ${filename} — content will be read from server on Calculate`;
      } else if (ta) {
        const msg = await resp.text();
        ta.value = '';
        alert(`Could not load file over HTTP:\n${msg}`);
      }
    }
  } catch (_) {
    if (ta) { ta.value = ''; ta.placeholder = `[Disk-Direct] ${filename}`; }
  }
}

/* ============================================================
   FILE BROWSER — "Use" button, mode-aware
   ============================================================ */
function initFileBrowser() {
  document.querySelectorAll('.btn-use').forEach(btn => {
    btn.addEventListener('click', () => loadFile(btn.dataset.filename));
  });

  // When user switches modes, clear disk hidden field (keep textarea content)
  document.querySelectorAll('input[name="ui_file_mode"]').forEach(radio => {
    radio.addEventListener('change', () => {
      clearDiskHiddenField();
      document.querySelectorAll('.file-table tr.selected').forEach(r => r.classList.remove('selected'));
      document.querySelectorAll('.btn-use.active').forEach(b => b.classList.remove('active'));
    });
  });
}

/* ============================================================
   FILE GENERATE
   ============================================================ */
function initFileGenerate() {
  document.querySelectorAll('.btn-gen:not(.btn-gen-disabled)').forEach(btn => {
    btn.addEventListener('click', () => openGenPanel(btn));
  });
}

function openGenPanel(btn) {
  document.querySelectorAll('.gen-panel-row').forEach(r => r.remove());

  const name = btn.dataset.filename;
  if (!/^\d-\d+(k|m|b)\.txt$/.test(name)) {
    alert('Cannot generate: filename does not match expected pattern.');
    return;
  }

  const row = btn.closest('tr');
  const panel = document.createElement('tr');
  panel.className = 'gen-panel-row';
  panel.innerHTML = `
    <td colspan="4" style="padding:6px 10px;background:var(--bg-input,#1a1a2e);">
      <span style="font-size:0.78rem;color:var(--text-secondary);margin-right:6px;">Expand <strong style="color:var(--cyan)">${name}</strong> by</span>
      <select class="gen-factor-select" style="font-size:0.78rem;padding:2px 4px;background:var(--bg-card);color:var(--text-primary);border:1px solid var(--border);border-radius:3px;">
        ${[2,3,4,5,6,7,8,9,10].map(n=>`<option value="${n}">${n}x</option>`).join('')}
      </select>
      <button class="btn-gen-confirm" style="margin-left:6px;font-size:0.78rem;padding:2px 8px;background:var(--cyan);color:#000;border:none;border-radius:3px;cursor:pointer;">Generate</button>
      <button class="btn-gen-cancel" style="margin-left:4px;font-size:0.78rem;padding:2px 8px;background:transparent;color:var(--text-muted);border:1px solid var(--border);border-radius:3px;cursor:pointer;">Cancel</button>
      <span class="gen-status" style="margin-left:8px;font-size:0.76rem;color:var(--text-muted);"></span>
    </td>`;

  row.after(panel);

  panel.querySelector('.btn-gen-cancel').addEventListener('click', () => panel.remove());
  panel.querySelector('.btn-gen-confirm').addEventListener('click', async () => {
    const factor = parseInt(panel.querySelector('.gen-factor-select').value);
    const status = panel.querySelector('.gen-status');
    status.textContent = 'Generating…';
    try {
      const resp = await fetch('/files/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name, factor}),
      });
      const result = await resp.json();
      if (!resp.ok) {
        status.style.color = 'var(--red)';
        status.textContent = result.error || 'Error';
        return;
      }
      panel.remove();
      await refreshFileTable(result.name);
    } catch (e) {
      status.style.color = 'var(--red)';
      status.textContent = 'Network error';
    }
  });
}

async function refreshFileTable(autoSelectName) {
  try {
    const resp = await fetch('/files/list');
    const files = await resp.json();
    const tbody = document.querySelector('.file-table tbody');
    if (!tbody) return;
    tbody.innerHTML = files.map(f => {
      const canGen = /^\d-\d+(k|m|b)\.txt$/.test(f.name);
      const genDisabled = !FILE_GENERATE_ENABLED || !canGen;
      return `<tr data-filename="${f.name}">
        <td><span class="file-name">${f.name}</span></td>
        <td><span class="file-size">${f.size_display}</span></td>
        <td><button class="btn-use" type="button" data-filename="${f.name}">Use</button></td>
        <td><button class="btn-gen${genDisabled ? ' btn-gen-disabled' : ''}"
                    type="button" data-filename="${f.name}"
                    ${genDisabled ? 'disabled' : ''}>Generate</button></td>
      </tr>`;
    }).join('');
    initFileBrowser();
    initFileGenerate();
    if (autoSelectName) loadFile(autoSelectName);
  } catch (e) {
    console.error('refreshFileTable failed:', e);
  }
}

/* ============================================================
   COLLAPSIBLE SECTIONS
   ============================================================ */
function initCollapsibles() {
  document.querySelectorAll('.collapsible-toggle').forEach(toggle => {
    toggle.addEventListener('click', () => {
      const target = document.getElementById(toggle.dataset.target);
      if (!target) return;
      const isOpen = !target.classList.contains('collapsed');
      target.classList.toggle('collapsed', isOpen);
      toggle.setAttribute('aria-expanded', String(!isOpen));
      const icon = toggle.querySelector('.collapse-icon');
      if (icon) icon.style.transform = isOpen ? 'rotate(-90deg)' : 'rotate(0deg)';
    });
  });
}

/* ============================================================
   RESULT WINDOW NAVIGATION
   Manages a client-side view into the full result string.
   The full result is stored in a hidden element after calculation.
   ============================================================ */
const INPUT_DISPLAY_CAP = 10_000; // max chars shown in the number textarea (disk mode)
const RESULT_WINDOW     = 10_000; // chars per Prev/Next navigation window

let _resultFull        = '';  // content of the currently-displayed result window
let _resultLength      = 0;   // chars in the current window
let _resultTotalChars  = 0;   // true total chars in the full result (from server)
let _windowOffset      = 0;   // absolute start position of current window in full result
let _navOffset         = 0;   // legacy alias — equals _windowOffset
let _currentPage       = 1;   // 1-based page number of current window
let _totalPages        = 0;   // total pages = ceil(_resultTotalChars / RESULT_WINDOW)
let _displayMode       = 'pyramid';  // 'standard' | 'pyramid'
let _lastResultOperation = '';  // operation used for the last calculation — passed to /calc/window

let _highlightHpl = true;  // HPL pattern highlight toggle
let _highlightHpr = true;  // HPR pattern highlight toggle

/** Convert 1-based page number to byte/char offset. */
function pageToOffset(page) { return Math.max(0, page - 1) * RESULT_WINDOW; }

/** Convert byte/char offset to 1-based page number. */
function offsetToPage(offset) { return Math.floor(offset / RESULT_WINDOW) + 1; }

function initResultNav() {
  // Event delegation on document — nav elements (#nav-prev, #nav-next, #nav-goto,
  // #nav-index) live inside #result-panel which is fully replaced on every HTMX
  // result swap.  Attaching listeners directly to those elements means they die on
  // every swap.  Delegating to document means this runs exactly once and always works.
  document.addEventListener('click', (e) => {
    switch (e.target.id) {
      case 'nav-prev':
        if (_currentPage > 1) loadWindow(pageToOffset(_currentPage - 1));
        break;
      case 'nav-next':
        if (_totalPages === 0 || _currentPage < _totalPages)
          loadWindow(pageToOffset(_currentPage + 1));
        break;
      case 'nav-goto': {
        const navInput = document.getElementById('nav-index');
        const page = parseInt(navInput?.value ?? '1', 10);
        if (!isNaN(page) && page >= 1) loadWindow(pageToOffset(page));
        break;
      }
      default:
        if (e.target.classList.contains('display-mode-btn'))
          setDisplayMode(e.target.dataset.mode);
    }
  });
}

function navTo(offset) {
  // Backward-compat wrapper — redirect to window-based navigation.
  loadWindow(offset);
}

/**
 * Render `text` into #number-display, applying the VPC gold highlight if the
 * active constant appears anywhere in this window.  Called both on initial
 * result swap and after every Prev/Next window load.
 */
function renderWindowContent(text) {
  const display = document.getElementById('number-display');
  if (!display) return;

  const vpcEl  = document.getElementById('active-const-value');
  const vpcVal = vpcEl ? vpcEl.textContent.trim() : '';

  if (vpcVal && vpcVal !== '—' && text.includes(vpcVal)) {
    const idx    = text.indexOf(vpcVal);
    const before = text.slice(0, idx);
    const after  = text.slice(idx + vpcVal.length);
    display.innerHTML =
      before +
      `<span class="vpc-highlight">${vpcVal}</span>` +
      after;
  } else {
    display.textContent = text;
  }
  display.scrollTop = 0;
}

/**
 * Build a text pyramid of the triangular number.
 *
 * Design: inner-accumulation with centered apex.
 *   - Apex (row 0, top): leftRem + VPC + rightRem, centered over the gap column.
 *   - Row k (k=1..cap): innermost k left-patterns right-aligned + gap + innermost k right-patterns left-aligned.
 *   - Cap = min(N, M, MAX_PYRAMID_ROWS) — show the patterns closest to the VPC.
 *   - The gap column is fixed at cap × hplLen for all rows → apex sits centered above the pyramid.
 *   - Trailing spaces are trimmed per line for clean output.
 *
 * Visual result (narrow at top, wide at bottom — proper pyramid shape):
 *
 *              [leftRem VPC rightRem]
 *       [pN]  ···gap···  [q1]
 *    [pN-1 pN] ···gap··· [q1 q2]
 *  [pN-2..pN]  ···gap···  [q1..q3]
 */
const MAX_PYRAMID_ROWS = 10;

/**
 * Char-by-char comparison: wraps matching chars in a colored span, leaves non-matching as plain text.
 * @param {string} str      The actual string to colorize (e.g. a hpl/hpr chunk or remainder).
 * @param {string} expected The reference pattern to compare against (aligned to str[0]).
 * @param {string} cssClass CSS class to apply to matching chars ('hpl-match' or 'hpr-match').
 * @returns {string} HTML string — matching chars in spans, non-matching as plain text.
 */
function colorizeStr(str, expected, cssClass) {
  let html = '';
  for (let i = 0; i < str.length; i++) {
    if (i < expected.length && str[i] === expected[i]) {
      html += `<span class="${cssClass}">${str[i]}</span>`;
    } else {
      html += str[i];
    }
  }
  return html;
}

/**
 * Render the VPC apex span.
 * Exact match (wildPos null): entire value in vpc-highlight.
 * Fuzzy match: matched chars in vpc-highlight, changed char as plain text (renders green).
 */
function vpcApexHtml(matchedVpc, wildPos) {
  if (wildPos === null || wildPos === undefined) {
    return '<span class="vpc-highlight">' + matchedVpc + '</span>';
  }
  let html = '';
  for (let i = 0; i < matchedVpc.length; i++) {
    if (i === wildPos) {
      html += matchedVpc[i]; // plain — inherits green (this digit was changed by increment)
    } else {
      html += '<span class="vpc-highlight">' + matchedVpc[i] + '</span>';
    }
  }
  return html;
}

/**
 * Find the VPC index using tile-alignment verification.
 * Rejects coincidental VPC occurrences (e.g. in a +1 incremented TN) by checking
 * that the tile immediately to the left of the candidate position matches hpl.
 * Tries all possible leftRemLens (0..hplLen-1) to handle partial leading tiles.
 * Returns -1 if no well-aligned occurrence is found.
 */
function findBestVpcIdx(text, vpcVal, hpl) {
  const hplLen = hpl.length;
  let searchFrom = 0;
  while (searchFrom < text.length) {
    const idx = text.indexOf(vpcVal, searchFrom);
    if (idx === -1) break;
    // Check for each possible leftRemLen: is the full hpl tile just before leftRem == hpl?
    for (let lr = 0; lr < hplLen; lr++) {
      if (idx >= hplLen + lr && text.slice(idx - hplLen - lr, idx - lr) === hpl) return idx;
    }
    searchFrom = idx + 1;
  }
  // Tile-alignment failed for all occurrences (e.g. increment changed surrounding tiles).
  // Fall back to the first occurrence — still correct when vpcVal is unique in the text.
  const fallback = text.indexOf(vpcVal);
  console.log('[findBestVpcIdx] tile-alignment miss for', JSON.stringify(vpcVal),
    '— fallback pos', fallback, '(text len', text.length + ')');
  return fallback;
}

/**
 * Fuzzy VPC search when exact match fails.
 * Expands outward from the text midpoint (VPC is always near the center).
 * Tries all vpcLen wildcard positions: any single char may differ from vpcVal.
 * Returns { idx, matchedVpc, wildPos } for the first tile-aligned fuzzy match,
 * or the first fuzzy match closest to center if no tile-aligned one is found.
 */
function findFuzzyVpcIdx(text, vpcVal, hpl) {
  const vpcLen = vpcVal.length;
  const hplLen = hpl.length;
  const mid    = Math.floor(text.length / 2);

  let firstFuzzy = null; // closest-to-center fuzzy match (fallback if no tile-aligned)

  for (let offset = 0; offset <= mid + vpcLen; offset++) {
    const positions = offset === 0 ? [mid] : [mid - offset, mid + offset];
    for (const pos of positions) {
      if (pos < 0 || pos + vpcLen > text.length) continue;
      const candidate = text.slice(pos, pos + vpcLen);

      for (let wildPos = 0; wildPos < vpcLen; wildPos++) {
        let ok = true;
        for (let i = 0; i < vpcLen; i++) {
          if (i === wildPos) {
            if (!/\d/.test(candidate[i])) { ok = false; break; }
          } else {
            if (candidate[i] !== vpcVal[i]) { ok = false; break; }
          }
        }
        if (!ok) continue;

        // Fuzzy match found — save as fallback (first = closest to center)
        if (!firstFuzzy) firstFuzzy = { idx: pos, matchedVpc: candidate, wildPos };

        // Prefer a tile-aligned occurrence
        for (let lr = 0; lr < hplLen; lr++) {
          if (pos >= hplLen + lr && text.slice(pos - hplLen - lr, pos - lr) === hpl) {
            return { idx: pos, matchedVpc: candidate, wildPos };
          }
        }
      }
    }
  }

  return firstFuzzy; // null if nothing matched at all
}

function buildPyramid(text, vpcVal, hpl, hpr, highlightHpl, highlightHpr) {
  if (!vpcVal || vpcVal === '—') return null;
  if (!hpl || hpl === '—' || !hpr || hpr === '—') return null;

  const hplLen = hpl.length;
  const hprLen = hpr.length;

  // Look up lc prefix length for this digit family (digits 5, 7, 9 have a 1-char lc prefix).
  // leftFull tiles start after the lc prefix.
  let lcLen = 0;
  for (const data of Object.values(MATRIX)) {
    if (data.hpl === hpl) { lcLen = data.lc ? data.lc.length : 0; break; }
  }

  // Find vpcIdx with tile-alignment verification (rejects coincidental matches in changed zones).
  let vpcIdx      = findBestVpcIdx(text, vpcVal, hpl);
  let activeVpc   = vpcVal;  // may be overridden by fuzzy match
  let vpcWildPos  = null;    // null = exact match; 0/1/2 = which char was changed

  if (vpcIdx === -1) {
    // Exact match failed — try 2-of-3 fuzzy match expanding from center outward.
    const fuzzy = findFuzzyVpcIdx(text, vpcVal, hpl);
    if (fuzzy) {
      vpcIdx     = fuzzy.idx;
      activeVpc  = fuzzy.matchedVpc;
      vpcWildPos = fuzzy.wildPos;
      console.log('[buildPyramid] fuzzy VPC:', JSON.stringify(activeVpc),
        '(expected', JSON.stringify(vpcVal) + ') at idx', vpcIdx, 'wildPos=', vpcWildPos);
    }
  }
  if (vpcIdx === -1) return null;

  const leftPart  = text.slice(0, vpcIdx);
  const rightPart = text.slice(vpcIdx + activeVpc.length);

  // Left: skip lc prefix, then split into full hpl tiles + leftRem (partial, closest to VPC).
  // Python build_left tiles L→R: full tiles then hpl[0:rem] at the end.
  // So leftRemStr = head of hpl (first leftRemLen chars).
  const leftTilesPart = leftPart.slice(lcLen);
  const leftRemLen    = leftTilesPart.length % hplLen;
  const leftRemStr    = leftRemLen > 0 ? leftTilesPart.slice(-leftRemLen) : '';
  const leftFullStr   = leftRemLen > 0 ? leftTilesPart.slice(0, -leftRemLen) : leftTilesPart;
  const leftFull      = [];
  for (let i = 0; i < leftFullStr.length; i += hplLen)
    leftFull.push(leftFullStr.slice(i, i + hplLen));

  // Right: use natural tile boundaries (modular rem).
  // For pure repdigit: rem = tail-of-hpr prefix length; full tiles = hpr exactly.
  // For increment: rem = same formula; full tiles = a fixed rotation of hpr (all equal).
  // Natural boundaries ensure Pyramid content matches Standard mode char-for-char.
  const rightRemLen  = rightPart.length % hprLen;
  const rightRemStr  = rightRemLen > 0 ? rightPart.slice(0, rightRemLen) : '';
  const rightFullStr = rightRemLen > 0 ? rightPart.slice(rightRemLen) : rightPart;
  const rightFull    = [];
  for (let i = 0; i + hprLen <= rightFullStr.length; i += hprLen)
    rightFull.push(rightFullStr.slice(i, i + hprLen));
  // Always override last tile with the true last hprLen chars of the result.
  // Inner tiles repeat the same rotation; the last tile carries the actual final digit
  // which may differ after any increment.
  if (rightFull.length > 0)
    rightFull[rightFull.length - 1] = rightPart.slice(-hprLen);

  const N      = leftFull.length;
  const M      = rightFull.length;
  const vpcLen = activeVpc.length;

  console.log('[buildPyramid] vpcIdx=' + vpcIdx + ' vpcVal=' + JSON.stringify(vpcVal) +
    ' leftRemLen=' + leftRemLen + ' rightRemLen=' + rightRemLen + ' N=' + N + ' M=' + M +
    ' | resultTail=' + JSON.stringify(text.slice(-9)) +
    ' rightPartTail=' + JSON.stringify(rightPart.slice(-9)) +
    ' rightFull[M-1]=' + JSON.stringify(rightFull[M - 1]));

  // cap = max rows to show. gapCol = column where VPC starts in every row.
  // Row k text widths: left = k*hplLen + leftRemLen, right = rightRemLen + k*hprLen.
  // leftPad = gapCol - (k*hplLen + leftRemLen) = (cap-k)*hplLen  (purely arithmetic).
  const cap    = Math.min(N, M, MAX_PYRAMID_ROWS);
  if (cap === 0) return null;
  const gapCol = cap * hplLen + leftRemLen;  // column where VPC starts

  // Colorize helpers for the partial rem slots:
  //   leftRem aligns to hpl HEAD  (hpl[0:leftRemLen])
  //   rightRem aligns to the TAIL of the first full right tile (rightFull[0][-rightRemLen:]).
  //     For pure repdigit: rightFull[0] = hpr, so this equals hpr[-rightRemLen:] (same as before).
  //     For increment: rightFull[0] is a rotation of hpr; using its tail gives the correct
  //     expected value for the partial slot, so only genuinely changed chars show as green.
  const colorLeftRem  = () => colorizeStr(leftRemStr,  hpl.slice(0, leftRemLen), 'hpl-match');
  const colorRightRem = () => colorizeStr(
    rightRemStr,
    (rightFull.length > 1 ? rightFull[0] : hpr).slice(hprLen - rightRemLen),
    'hpr-match'
  );

  const lines = [];

  // Apex row: leftRem + VPC (red) + rightRem — the partial patterns adjacent to the constant.
  {
    const apexLeft  = (leftRemLen  > 0 && highlightHpl) ? colorLeftRem()  : leftRemStr;
    const apexRight = (rightRemLen > 0 && highlightHpr) ? colorRightRem() : rightRemStr;
    lines.push(
      ' '.repeat(cap * hplLen) +
      apexLeft +
      vpcApexHtml(activeVpc, vpcWildPos) +
      apexRight
    );
  }

  // Body rows k=1..cap: k tiles on each side, growing wider per row.
  // Left:  outermost k tiles → leftFull[0..k-1]          (start of TN, farthest from VPC)
  // Right (k < cap): VPC-adjacent → rightFull[0..k-1]    (inner tiles, no mirroring between rows)
  // Right (k = cap): end-window  → rightFull[M-cap..M-1] (actual tail of TN, shows changed digits)
  //
  // Two-region design:
  //   Upper rows (k<cap) use VPC-adjacent tiles — all inner rotation, all amber for pure repdigit.
  //   Bottom row (k=cap) uses the true end-window — changed digits from any increment show green.
  //   No mirroring: k<cap rows and k=cap row draw from independent positions, so a changed tile
  //   never appears at the same column in adjacent rows.
  //   For pure repdigit all tiles are equal so both windows produce identical amber output.
  //
  // rightBaseline: inner repeating tile (rightFull[M-cap]) used by colorizeStr for all rows.
  //   Upper rows: tiles match baseline → all amber.
  //   Bottom row: inner tiles match → amber; changed end tiles differ → green.
  const rightBaseline = rightFull[M - cap];

  for (let k = 1; k <= cap; k++) {
    let leftContent = '';
    if (highlightHpl) {
      for (let i = 0; i < k; i++)
        leftContent += colorizeStr(leftFull[i], hpl, 'hpl-match');
    } else {
      for (let i = 0; i < k; i++) leftContent += leftFull[i];
    }

    const rStart = (k < cap) ? 0 : (M - cap);
    let rightContent = '';
    if (highlightHpr) {
      for (let i = rStart; i < rStart + k; i++)
        rightContent += colorizeStr(rightFull[i], rightBaseline, 'hpr-match');
    } else {
      for (let i = rStart; i < rStart + k; i++) rightContent += rightFull[i];
    }

    // leftPad: text length of leftContent = k*hplLen (no partial).
    // gapCol = cap*hplLen + leftRemLen → leftPad = (cap-k)*hplLen + leftRemLen.
    const leftPad = ' '.repeat((cap - k) * hplLen + leftRemLen);
    lines.push(leftPad + leftContent + ' '.repeat(vpcLen) + rightContent);
  }

  return { html: lines.join('\n'), gapCol };
}

/** Render the current result window as a pyramid into #number-display. */
function renderPyramid() {
  const display = document.getElementById('number-display');
  if (!display) return;

  if (_resultTotalChars > RESULT_WINDOW) {
    display.classList.remove('pyramid-mode');
    display.style.overflowX = '';
    display.style.overflowY = '';
    display.textContent =
      'Pyramid view is only available for results ≤ 10,000 digits.\n' +
      'This result has ' + _resultTotalChars.toLocaleString() + ' digits — use Standard view.';
    return;
  }

  let vpcVal = document.getElementById('active-const-value')?.textContent.trim() ?? '';
  const hpl  = document.getElementById('const-hpl')?.textContent.trim() ?? '';
  const hpr  = document.getElementById('const-hpr')?.textContent.trim() ?? '';

  // If the stored VPC is stale (wrong digit's constant) or missing, auto-detect from MATRIX.
  // hpl uniquely identifies the digit family; scan that family's VPCs for one present in the result.
  if (!vpcVal || vpcVal === '—' || !_resultFull.includes(vpcVal)) {
    for (const data of Object.values(MATRIX)) {
      if (data.hpl !== hpl) continue;
      for (const key of vpcKeys) {
        const candidate = data[key];
        if (candidate && candidate !== '—' && _resultFull.includes(candidate)) {
          vpcVal = candidate;
          break;
        }
      }
      break;
    }
  }

  if (!vpcVal || vpcVal === '—') {
    display.classList.remove('pyramid-mode');
    display.style.overflowX = '';
    display.style.overflowY = '';
    display.textContent = 'No active constant — calculate a result first, then select Pyramid view.';
    return;
  }

  console.log('[renderPyramid] vpcVal=' + JSON.stringify(vpcVal) +
    ' hpl=' + JSON.stringify(hpl) + ' hpr=' + JSON.stringify(hpr) +
    ' highlightHpl=' + _highlightHpl + ' highlightHpr=' + _highlightHpr +
    ' textLen=' + _resultFull.length);
  const result = buildPyramid(_resultFull, vpcVal, hpl, hpr, _highlightHpl, _highlightHpr);
  if (!result) {
    display.classList.remove('pyramid-mode');
    display.style.overflowX = '';
    display.style.overflowY = '';
    display.textContent = _resultFull; // fall back to raw digits
    return;
  }

  const { html: pyramid, gapCol } = result;
  display.classList.add('pyramid-mode');
  // Set overflow on the container div; whitespace preservation is handled by the
  // inner <pre class="pyramid-inner"> which uses the browser UA stylesheet's
  // white-space:pre — no CSS cascade fight needed.
  display.style.whiteSpace = '';
  display.style.wordBreak = '';
  display.style.overflowWrap = '';
  display.style.overflowX = 'auto';
  display.style.overflowY = 'auto';
  display.innerHTML = '<pre class="pyramid-inner">' + pyramid + '</pre>';
  display.scrollTop = 0;

  // Auto-scroll horizontally to center the VPC column in the viewport
  requestAnimationFrame(() => {
    const probe = document.createElement('span');
    probe.style.cssText = 'visibility:hidden;position:absolute;white-space:pre;font:inherit;';
    probe.textContent = '0'.repeat(100);
    display.appendChild(probe);
    const charWidth = probe.getBoundingClientRect().width / 100;
    display.removeChild(probe);
    display.scrollLeft = Math.max(0, gapCol * charWidth - display.clientWidth / 2);
  });
}

/** Sync display-mode toggle buttons then render in the current mode. */
function renderCurrentMode() {
  document.querySelectorAll('.display-mode-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.mode === _displayMode);
  });
  if (_displayMode === 'pyramid') {
    renderPyramid();
  } else {
    const display = document.getElementById('number-display');
    if (display) {
      display.classList.remove('pyramid-mode');
      display.style.overflowX = '';
      display.style.overflowY = '';
    }
    renderWindowContent(_resultFull);
  }
}

/** Switch display mode and re-render. */
function setDisplayMode(mode) {
  _displayMode = mode;
  renderCurrentMode();
}

/**
 * Fetch a RESULT_WINDOW-sized chunk of the full result from the server,
 * update state, and re-render the display.
 * @param {number} offset  Absolute character position in the full result.
 */
async function loadWindow(offset) {
  offset = Math.max(0, offset);
  // If total is known, don't fetch past the end
  if (_resultTotalChars > 0 && offset >= _resultTotalChars) return;

  try {
    const resp = await fetch(`/calc/window?offset=${offset}&length=${RESULT_WINDOW}&operation=${encodeURIComponent(_lastResultOperation)}`);
    if (!resp.ok) return;
    const data = await resp.json();

    _windowOffset     = data.offset;
    _resultTotalChars = data.total;
    _totalPages       = Math.ceil(_resultTotalChars / RESULT_WINDOW);
    _currentPage      = offsetToPage(_windowOffset);
    _resultFull       = data.chunk;
    _resultLength     = data.chunk.length;
    _navOffset        = _windowOffset;

    const navIndex = document.getElementById('nav-index');
    if (navIndex) navIndex.value = _currentPage;
    const navTotal = document.getElementById('nav-total');
    if (navTotal) navTotal.textContent = `/ ${_totalPages.toLocaleString()} pages`;
    const navChars = document.getElementById('nav-chars');
    if (navChars) {
      const start = (_windowOffset + 1).toLocaleString();
      const end   = Math.min(_windowOffset + _resultLength, _resultTotalChars).toLocaleString();
      navChars.textContent = `chars ${start}–${end} of ${_resultTotalChars.toLocaleString()}`;
    }

    renderCurrentMode();
  } catch (e) {
    console.error('loadWindow failed:', e);
  }
}

/**
 * Called after HTMX swaps in a new result (from the result partial).
 * Reads the full result from the hidden #result-full element.
 */
function onResultSwap() {
  const fullEl = document.getElementById('result-full');
  if (!fullEl) return;

  _lastResultOperation = document.getElementById('operation')?.value || '';

  // Seed state from the server-rendered first window (up to 10 000 chars).
  _resultFull   = fullEl.textContent;
  _resultLength = _resultFull.length;
  _windowOffset = 0;
  _navOffset    = 0;
  _currentPage  = 1;

  // Update Matrix Constants panel to reflect the active constant in this result.
  // Detects digit family (via hpl) and active vpc (via tile-alignment check).
  const detected = detectConstantsFromResult(_resultFull, _calcDigit || null);
  if (detected) updateConstantsPanel(detected.digit, detected.vpcKey);

  // True total result length (may be larger than the 10 000-char preview).
  const totalEl = document.getElementById('result-total-chars');
  _resultTotalChars = totalEl ? parseInt(totalEl.textContent, 10) : _resultLength;
  _totalPages       = _resultTotalChars > 0 ? Math.ceil(_resultTotalChars / RESULT_WINDOW) : 0;

  // Pyramid mode is only valid for results that fit in a single window.
  // Auto-switch to standard so large results are immediately navigable.
  if (_resultTotalChars > RESULT_WINDOW) {
    _displayMode = 'standard';
  }

  const navIndex = document.getElementById('nav-index');
  if (navIndex) navIndex.value = 1;
  const navTotal = document.getElementById('nav-total');
  if (navTotal) navTotal.textContent = `/ ${_totalPages.toLocaleString()} pages`;
  const navChars = document.getElementById('nav-chars');
  if (navChars) {
    const end = Math.min(_resultLength, _resultTotalChars).toLocaleString();
    navChars.textContent = `chars 1–${end} of ${_resultTotalChars.toLocaleString()}`;
  }

  // Render in the current display mode (standard or pyramid).
  renderCurrentMode();
}

/* ============================================================
   HTMX EVENT HOOKS
   ============================================================ */
function colorizeResultPatterns() {
  document.querySelectorAll('.pattern-colorize').forEach(el => {
    const pattern = el.dataset.pattern;
    const digit = el.dataset.digit;
    if (pattern && digit && typeof colorizePattern === 'function') {
      el.innerHTML = colorizePattern(pattern, digit, el.dataset.end === 'true');
    }
  });
}

document.addEventListener('htmx:afterSwap', (e) => {
  // After result partial is swapped in, init nav and animate
  if (e.detail.target?.id === 'result-panel') {
    onResultSwap();
    colorizeResultPatterns();
    const display = document.getElementById('number-display');
    if (display) {
      display.classList.add('htmx-added');
      setTimeout(() => display.classList.remove('htmx-added'), 600);
    }
  }
});

document.addEventListener('htmx:beforeRequest', () => {
  const calcBtn = document.querySelector('.btn-calculate');
  if (calcBtn) calcBtn.textContent = '⏳ Computing…';
});

document.addEventListener('htmx:afterRequest', () => {
  const calcBtn = document.querySelector('.btn-calculate');
  if (calcBtn) calcBtn.innerHTML = '<span class="btn-triangle">▲</span> Calculate Triangular Number';
});

/* ============================================================
   HISTORY TABLE — method badges colour map
   Applied to any .method-badge element added dynamically.
   ============================================================ */
const METHOD_COLORS = {
  'tri_matrix':        'cyan',
  'tri_matrix_memory': 'violet',
  'tri_matrix_stream': 'green',
  'tri_matrix_random': 'amber',
  'tri_div_gmpy2':     'amber',
  'tri_div_sympy':     'red',
};

function colorizeMethodBadges() {
  document.querySelectorAll('.method-badge').forEach(el => {
    const method = el.dataset.method;
    const color  = METHOD_COLORS[method] ?? 'secondary';
    el.dataset.color = color;
  });
}

/* ============================================================
   COPY TO CLIPBOARD — result display
   ============================================================ */
function initCopyButton() {
  const copyBtn = document.getElementById('btn-copy-result');
  if (!copyBtn) return;
  copyBtn.addEventListener('click', () => {
    if (!_resultFull) return;
    navigator.clipboard.writeText(_resultFull).then(() => {
      const orig = copyBtn.textContent;
      copyBtn.textContent = 'Copied!';
      setTimeout(() => { copyBtn.textContent = orig; }, 1500);
    });
  });
}

/* ============================================================
   PATTERN HIGHLIGHT TOGGLES — HPL / HPR
   ============================================================ */
function initPatternToggles() {
  document.getElementById('toggle-hpl')?.addEventListener('click', () => {
    _highlightHpl = !_highlightHpl;
    const btn = document.getElementById('toggle-hpl');
    btn.classList.toggle('active', _highlightHpl);
    btn.textContent = _highlightHpl ? 'ON' : 'OFF';
    if (_displayMode === 'pyramid') renderCurrentMode();
  });
  document.getElementById('toggle-hpr')?.addEventListener('click', () => {
    _highlightHpr = !_highlightHpr;
    const btn = document.getElementById('toggle-hpr');
    btn.classList.toggle('active', _highlightHpr);
    btn.textContent = _highlightHpr ? 'ON' : 'OFF';
    if (_displayMode === 'pyramid') renderCurrentMode();
  });
}

/* ============================================================
   KEYBOARD SHORTCUTS
   ============================================================ */
document.addEventListener('keydown', (e) => {
  // Enter in the page-number input — same as clicking Go
  if (e.target.id === 'nav-index' && e.key === 'Enter') {
    const page = parseInt(e.target.value, 10);
    if (!isNaN(page) && page >= 1) loadWindow(pageToOffset(page));
  }
  // Alt+← / Alt+→ for result page navigation
  if (e.altKey && e.key === 'ArrowLeft'  && _currentPage > 1)
    loadWindow(pageToOffset(_currentPage - 1));
  if (e.altKey && e.key === 'ArrowRight' && (_totalPages === 0 || _currentPage < _totalPages))
    loadWindow(pageToOffset(_currentPage + 1));
});

/* ============================================================
   INCREMENT STEPPERS  (− / + buttons next to the Increment field)
   ============================================================ */
function initIncrementSteppers() {
  function getStep() {
    const s = parseInt(document.getElementById('increment-step-l')?.value, 10);
    return (isNaN(s) || s < 1) ? 1 : s;
  }
  // Keep both step inputs in sync
  ['increment-step-l', 'increment-step-r'].forEach(id => {
    document.getElementById(id)?.addEventListener('input', e => {
      const otherId = id === 'increment-step-l' ? 'increment-step-r' : 'increment-step-l';
      const other = document.getElementById(otherId);
      if (other) other.value = e.target.value;
    });
  });
  function step(sign) {
    const inp = document.getElementById('num2');
    if (!inp) return;
    const current = parseInt(inp.value, 10);
    inp.value = (isNaN(current) ? 0 : current) + sign * getStep();
    document.querySelector('.btn-calculate')?.click();
  }
  document.getElementById('btn-increment-dec')?.addEventListener('click', () => step(-1));
  document.getElementById('btn-increment-inc')?.addEventListener('click', () => step(1));
}

/* ============================================================
   INIT
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  initDigitSelector();
  initFileBrowser();
  initFileGenerate();
  initCollapsibles();
  initResultNav();
  initCopyButton();
  initPatternToggles();
  initIncrementSteppers();
  colorizeMethodBadges();

  // Wire up number textarea
  const ta = document.getElementById('number-input');
  if (ta) ta.addEventListener('input', onNumberInput);

  // On page load, if textarea already has a value (e.g. Jinja pre-fill), run detection
  if (ta && ta.value.trim()) {
    ta.dispatchEvent(new Event('input'));
  }

  // If result was pre-loaded server-side (GET /), HTMX never fires afterSwap,
  // so we must initialize nav state here.  Without this, _resultTotalChars stays 0
  // and Prev/Next load out-of-range chunks, blanking the display.
  if (document.getElementById('result-full')) {
    onResultSwap();
    colorizeResultPatterns();
  }
});
