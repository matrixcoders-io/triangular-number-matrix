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
   CONSTANTS PANEL
   ============================================================ */
const vpcKeys = ['vpc1','vpc2','vpc3','vpc4','vpc5','vpc6','vpc7','vpc8','vpc9'];

function updateConstantsPanel(digitStr, activeVpcKey) {
  const data = MATRIX[digitStr];
  if (!data) return;

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
      metaEl.textContent = `${length.toLocaleString()} digits · repdigit ${digit}`;
    } else if (e.target.value.trim()) {
      metaEl.textContent = `${e.target.value.trim().length.toLocaleString()} chars`;
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
    btn.addEventListener('click', () => {
      const d = btn.dataset.digit;
      updateConstantsPanel(d, null);
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
   FILE BROWSER — "Use" button, mode-aware
   Always fetches and shows content in textarea.
   Disk mode additionally sets the hidden filename field.
   ============================================================ */
function initFileBrowser() {
  document.querySelectorAll('.btn-use').forEach(btn => {
    btn.addEventListener('click', async () => {
      const filename = btn.dataset.filename;
      if (!filename) return;

      // Mark row selected
      document.querySelectorAll('.file-table tr.selected').forEach(r => r.classList.remove('selected'));
      btn.closest('tr')?.classList.add('selected');
      document.querySelectorAll('.btn-use.active').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Update selected-file badge next to Input Number label
      const badge = document.getElementById('input-file-badge');
      if (badge) badge.textContent = `◫ ${filename}`;

      // Immediately update Number Family from filename (e.g. "6-1k.txt" → digit 6).
      // Fires before the async preview fetch so the panel updates instantly on click.
      const fileDigit = filename.match(/^(\d)/)?.[1];
      if (fileDigit && MATRIX[fileDigit]) updateConstantsPanel(fileDigit, null);

      const mode = getFileMode();

      if (mode === 'disk') {
        // Record filename so Flask reads from disk on Calculate
        setDiskHiddenField(filename);
        // Still fetch and show content so user can see what they're calculating
        const ta = document.getElementById('number-input');
        if (ta) ta.value = 'Loading preview…';
        try {
          const resp = await fetch(`/files/preview?name=${encodeURIComponent(filename)}`);
          if (resp.ok) {
            const text = await resp.text();
            if (ta) {
              const trimmed = text.trim();
              ta.value = trimmed.length > INPUT_DISPLAY_CAP
                ? trimmed.slice(0, INPUT_DISPLAY_CAP)
                : trimmed;
              ta.dispatchEvent(new Event('input'));
              // If content was truncated, override the meta label with real digit count
              if (trimmed.length > INPUT_DISPLAY_CAP) {
                const metaEl = document.getElementById('input-char-count');
                if (metaEl) metaEl.textContent =
                  `${trimmed.length.toLocaleString()} digits · showing first ${INPUT_DISPLAY_CAP.toLocaleString()}`;
              }
            }
          } else {
            // HTTP transfer may be disabled or file too large — show a note instead
            if (ta) {
              ta.value = '';
              ta.placeholder = `[Disk-Direct] ${filename} — content will be read from server on Calculate`;
            }
          }
        } catch (_) {
          if (ta) { ta.value = ''; ta.placeholder = `[Disk-Direct] ${filename}`; }
        }
        return;
      }

      // HTTP mode: fetch content into textarea, no hidden file field
      clearDiskHiddenField();
      const ta = document.getElementById('number-input');
      if (ta) ta.value = 'Loading…';
      try {
        const resp = await fetch(`/files/preview?name=${encodeURIComponent(filename)}`);
        if (!resp.ok) {
          const msg = await resp.text();
          if (ta) ta.value = '';
          alert(`Could not load file over HTTP:\n${msg}`);
          return;
        }
        const text = await resp.text();
        if (ta) { ta.value = text.trim(); ta.dispatchEvent(new Event('input')); }
      } catch (err) {
        if (ta) ta.value = '';
        console.error('File preview failed:', err);
      }
    });
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

let _resultFull       = '';  // content of the currently-displayed result window
let _resultLength     = 0;   // chars in the current window
let _resultTotalChars = 0;   // true total chars in the full result (from server)
let _windowOffset     = 0;   // absolute start position of current window in full result
let _navOffset        = 0;   // legacy alias — equals _windowOffset
let _currentPage      = 1;   // 1-based page number of current window
let _totalPages       = 0;   // total pages = ceil(_resultTotalChars / RESULT_WINDOW)

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
 * Fetch a RESULT_WINDOW-sized chunk of the full result from the server,
 * update state, and re-render the display.
 * @param {number} offset  Absolute character position in the full result.
 */
async function loadWindow(offset) {
  offset = Math.max(0, offset);
  // If total is known, don't fetch past the end
  if (_resultTotalChars > 0 && offset >= _resultTotalChars) return;

  try {
    const resp = await fetch(`/calc/window?offset=${offset}&length=${RESULT_WINDOW}`);
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

    renderWindowContent(_resultFull);
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

  // Seed state from the server-rendered first window (up to 10 000 chars).
  _resultFull   = fullEl.textContent;
  _resultLength = _resultFull.length;
  _windowOffset = 0;
  _navOffset    = 0;
  _currentPage  = 1;

  // True total result length (may be larger than the 10 000-char preview).
  const totalEl = document.getElementById('result-total-chars');
  _resultTotalChars = totalEl ? parseInt(totalEl.textContent, 10) : _resultLength;
  _totalPages       = _resultTotalChars > 0 ? Math.ceil(_resultTotalChars / RESULT_WINDOW) : 0;

  const navIndex = document.getElementById('nav-index');
  if (navIndex) navIndex.value = 1;
  const navTotal = document.getElementById('nav-total');
  if (navTotal) navTotal.textContent = `/ ${_totalPages.toLocaleString()} pages`;

  // Render first window with VPC gold highlight if the constant appears here.
  renderWindowContent(_resultFull);
}

/* ============================================================
   HTMX EVENT HOOKS
   ============================================================ */
document.addEventListener('htmx:afterSwap', (e) => {
  // After result partial is swapped in, init nav and animate
  if (e.detail.target?.id === 'result-panel') {
    onResultSwap();
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
   INIT
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  initDigitSelector();
  initFileBrowser();
  initCollapsibles();
  initResultNav();
  initCopyButton();
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
  }
});
