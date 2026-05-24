#!/usr/bin/env python3
"""
Pattern Investigator — Suite 14-H log analysis tool.

CLI usage:
  python3 scripts/pattern_investigator.py latest [--n 5]
  python3 scripts/pattern_investigator.py summary [<log_path>]
  python3 scripts/pattern_investigator.py stats [<log_path>]
  python3 scripts/pattern_investigator.py failures [<log>] [--digit 1] [--mismatch END]
  python3 scripts/pattern_investigator.py compare <log1> <log2>
  python3 scripts/pattern_investigator.py detect-alignment [<log>] [--digit 1]
  python3 scripts/pattern_investigator.py tail [<log>] [--n 30]

Surgical pattern extractors (clean, context-safe):
  python3 scripts/pattern_investigator.py mid-patterns [<log>] [--digit 1] [--compact]
  python3 scripts/pattern_investigator.py start-patterns [<log>] [--digit 1] [--compact]
  python3 scripts/pattern_investigator.py end-patterns [<log>] [--digit 1] [--compact]

  --compact   one line per record: "d=1 I=5 L=407 | <std> | <pyr>"
  no flag     two lines per record labelled std/pyr, grouped by d
"""

import os, re, sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(PROJECT_ROOT, 'tmp', 'tests', 'ui-tests')

_RECORD_RE = re.compile(r'^d=(\d+) I=(\d+) L=(\d+)\s+(PASS|FAIL)\s+banner=(.+)')
_STD_RE    = re.compile(r'^\s+standard: start=(\S+)\s+mid=(\S+)\s+end=(\S+)\s+\(len=(\d+)\)')
_PYR_RE    = re.compile(r'^\s+pyramid:\s+start=(\S+)\s+mid=(\S+)\s+end=(\S+)\s+\(len=(\d+)\)')
_WARN_RE   = re.compile(r'^\s+⚠ (.+)')
_OVERALL_RE= re.compile(r'^OVERALL: PASSED: (\d+), FAILED: (\d+), START-MISMATCH: (\d+), MID-MISMATCH: (\d+), END-MISMATCH: (\d+), LENGTH-MISMATCH: (\d+)')


def list_logs(n=10):
    if not os.path.isdir(LOG_DIR):
        return []
    files = [os.path.join(LOG_DIR, f) for f in os.listdir(LOG_DIR) if f.startswith('s14h-') and f.endswith('.log')]
    files.sort(key=os.path.getmtime, reverse=True)
    return files[:n]


def latest_log():
    logs = list_logs(1)
    if not logs:
        raise FileNotFoundError(f'No s14h-*.log files found in {LOG_DIR}')
    return logs[0]


def summary(log_path=None):
    path = log_path or latest_log()
    # Seek from end to find OVERALL line without loading full file
    with open(path, 'rb') as f:
        f.seek(0, 2)
        size = f.tell()
        chunk = min(2048, size)
        f.seek(max(0, size - chunk))
        tail_bytes = f.read()
    for line in reversed(tail_bytes.decode('utf-8', errors='replace').splitlines()):
        m = _OVERALL_RE.match(line)
        if m:
            return {
                'log': path,
                'passed': int(m.group(1)), 'failed': int(m.group(2)),
                'start_mismatch': int(m.group(3)), 'mid_mismatch': int(m.group(4)),
                'end_mismatch': int(m.group(5)), 'length_mismatch': int(m.group(6)),
            }
    return {'log': path, 'error': 'OVERALL line not found'}


def _parse_records(log_path):
    """Generator: yields one dict per test record, scanning line-by-line."""
    rec = None
    with open(log_path, 'r', errors='replace') as f:
        for line in f:
            m = _RECORD_RE.match(line)
            if m:
                if rec:
                    yield rec
                rec = {
                    'd': int(m.group(1)), 'inc': int(m.group(2)), 'L': int(m.group(3)),
                    'status': m.group(4), 'banner': m.group(5).strip(),
                    'std': {}, 'pyr': {}, 'mismatches': [],
                }
                continue
            if rec is None:
                continue
            ms = _STD_RE.match(line)
            if ms:
                rec['std'] = {'start': ms.group(1), 'mid': ms.group(2), 'end': ms.group(3), 'len': int(ms.group(4))}
                continue
            mp = _PYR_RE.match(line)
            if mp:
                rec['pyr'] = {'start': mp.group(1), 'mid': mp.group(2), 'end': mp.group(3), 'len': int(mp.group(4))}
                continue
            mw = _WARN_RE.match(line)
            if mw:
                rec['mismatches'].append(mw.group(1).strip())
    if rec:
        yield rec


def failures(log_path=None, digit=None, mismatch=None):
    path = log_path or latest_log()
    result = []
    for rec in _parse_records(path):
        if rec['status'] != 'FAIL':
            continue
        if digit is not None and rec['d'] != int(digit):
            continue
        if mismatch is not None:
            mtype = mismatch.upper()
            if not any(mtype in w for w in rec['mismatches']):
                continue
        result.append(rec)
    return result


def stats(log_path=None):
    path = log_path or latest_log()
    digits = {}
    for rec in _parse_records(path):
        d = rec['d']
        if d not in digits:
            digits[d] = {'pass': 0, 'fail': 0, 'start': 0, 'mid': 0, 'end': 0, 'length': 0}
        s = digits[d]
        if rec['status'] == 'PASS':
            s['pass'] += 1
        else:
            s['fail'] += 1
        for w in rec['mismatches']:
            if 'START' in w: s['start'] += 1
            if 'MID'   in w: s['mid']   += 1
            if 'END'   in w: s['end']   += 1
            if 'LENGTH'in w: s['length']+= 1
    return {'log': path, 'digits': digits}


def tail(log_path=None, n=30):
    path = log_path or latest_log()
    with open(path, 'rb') as f:
        f.seek(0, 2)
        size = f.tell()
        # Read backwards in 4KB chunks until we have n lines
        buf = b''
        pos = size
        while pos > 0 and buf.count(b'\n') < n + 1:
            chunk = min(4096, pos)
            pos -= chunk
            f.seek(pos)
            buf = f.read(chunk) + buf
    lines = buf.decode('utf-8', errors='replace').splitlines()
    return '\n'.join(lines[-n:])


def compare(log1, log2):
    def key(r): return (r['d'], r['inc'], r['L'])
    def load(path):
        return {key(r): r['status'] for r in _parse_records(path)}
    s1, s2 = load(log1), load(log2)
    all_keys = set(s1) | set(s2)
    new_passes, new_fails = [], []
    unchanged_pass = unchanged_fail = 0
    for k in sorted(all_keys):
        v1, v2 = s1.get(k), s2.get(k)
        if v1 == 'FAIL' and v2 == 'PASS':
            new_passes.append({'d': k[0], 'inc': k[1], 'L': k[2]})
        elif v1 == 'PASS' and v2 == 'FAIL':
            new_fails.append({'d': k[0], 'inc': k[1], 'L': k[2]})
        elif v2 == 'PASS':
            unchanged_pass += 1
        elif v2 == 'FAIL':
            unchanged_fail += 1
    return {
        'log1': log1, 'log2': log2,
        'new_passes': new_passes, 'new_fails': new_fails,
        'unchanged_pass': unchanged_pass, 'unchanged_fail': unchanged_fail,
    }


def detect_alignment(log_path=None, digit=None, mode='all'):
    """
    Analyse MID alignment for FAIL records using three strategies:

    constant  — std_mid is the ground-truth VPC-centred window from standard mode.
                Find where the first 10 chars of std_mid appear inside pyr_mid (or
                vice versa) to measure the positional shift.  Default for repdigits.

    positional — both windows are centred at the same absolute index from the start
                 of their respective strings (the string midpoint index).  Offset = 0
                 means both strings pick the same digit at position len//2.

    midpoint  — both windows are taken at Math.floor(len/2) of their own string.
                Reports whether the two midpoints coincide in value.  Useful when
                the pyramid reading is shorter/longer than the standard result.

    mode='all' reports all three in one table row.
    """
    path = log_path or latest_log()
    results = []
    for rec in _parse_records(path):
        if rec['status'] != 'FAIL': continue
        if digit is not None and rec['d'] != int(digit): continue
        if 'MID MISMATCH' not in ' '.join(rec['mismatches']): continue

        std_mid = rec['std'].get('mid', '')
        pyr_mid = rec['pyr'].get('mid', '')

        # constant: how far is std_mid shifted inside pyr string?
        const_offset = None
        if std_mid and pyr_mid:
            probe = std_mid[:10]
            idx = pyr_mid.find(probe)
            if idx != -1:
                const_offset = idx - 15      # positive = pyr window starts too early
            else:
                probe2 = pyr_mid[:10]
                idx2 = std_mid.find(probe2)
                if idx2 != -1:
                    const_offset = -(idx2 - 15)

        # positional: compare char at absolute midpoint of each string
        std_start  = rec['std'].get('start', '')
        pyr_start  = rec['pyr'].get('start', '')
        std_end    = rec['std'].get('end', '')
        pyr_end    = rec['pyr'].get('end', '')
        # We don't have full strings — report whether the mid windows share any prefix
        positional_match = std_mid[:5] == pyr_mid[:5] if std_mid and pyr_mid else None

        # midpoint: do the two 30-char windows have the same centre char?
        mid_char_std = std_mid[15] if len(std_mid) > 15 else None
        mid_char_pyr = pyr_mid[15] if len(pyr_mid) > 15 else None
        midpoint_match = mid_char_std == mid_char_pyr if mid_char_std and mid_char_pyr else None

        results.append({
            'd': rec['d'], 'inc': rec['inc'], 'L': rec['L'],
            'std_mid': std_mid, 'pyr_mid': pyr_mid,
            # three mode results
            'const_offset': const_offset,          # chars pyr window is shifted vs VPC anchor
            'positional_match': positional_match,  # True if start of both windows agrees
            'midpoint_match': midpoint_match,       # True if centre char agrees
        })
    return results


def count(log_path=None, segment=None, digit=None):
    """
    Count matching records without loading patterns into memory.

    segment  'mid'|'start'|'end'|None — if None, counts all FAILs
    digit    int or None
    Returns int.
    """
    path = log_path or latest_log()
    mtype = (segment.upper() + ' MISMATCH') if segment else None
    n = 0
    for rec in _parse_records(path):
        if rec['status'] != 'FAIL': continue
        if digit is not None and rec['d'] != int(digit): continue
        if mtype and not any(mtype in w for w in rec['mismatches']): continue
        n += 1
    return n


def sample(log_path=None, segment='mid', digit=None, n=3):
    """
    Return the first n mismatched records for a segment without loading the rest.
    Stops parsing the log as soon as n records are found.

    Returns list of {d, inc, L, std, pyr}.
    """
    seg = segment.lower()
    mtype = seg.upper() + ' MISMATCH'
    path = log_path or latest_log()
    results = []
    for rec in _parse_records(path):
        if len(results) >= n: break
        if rec['status'] != 'FAIL': continue
        if digit is not None and rec['d'] != int(digit): continue
        if not any(mtype in w for w in rec['mismatches']): continue
        results.append({
            'd': rec['d'], 'inc': rec['inc'], 'L': rec['L'],
            'std': rec['std'].get(seg, ''),
            'pyr': rec['pyr'].get(seg, ''),
        })
    return results


def segment_patterns(log_path=None, segment='mid', digit=None):
    """
    Return only the mismatched std/pyr values for one segment (mid/start/end).

    Each result: {d, inc, L, std, pyr}  where std/pyr are the 30-char strings
    for the requested segment. Only records where that segment MISMATCHes are
    returned — matched records are silently skipped.

    segment  one of 'mid', 'start', 'end'
    digit    int or None — filter to one digit family
    """
    seg = segment.lower()
    mtype = seg.upper() + ' MISMATCH'
    path = log_path or latest_log()
    results = []
    for rec in _parse_records(path):
        if rec['status'] != 'FAIL': continue
        if digit is not None and rec['d'] != int(digit): continue
        if not any(mtype in w for w in rec['mismatches']): continue
        results.append({
            'd': rec['d'], 'inc': rec['inc'], 'L': rec['L'],
            'std': rec['std'].get(seg, ''),
            'pyr': rec['pyr'].get(seg, ''),
        })
    return results


# ── CLI ──────────────────────────────────────────────────────────────────────

def _print_summary(s):
    if 'error' in s:
        print(f"ERROR: {s['error']} ({s['log']})")
        return
    total = s['passed'] + s['failed']
    print(f"Log:  {s['log']}")
    print(f"PASS: {s['passed']}/{total}  FAIL: {s['failed']}/{total}")
    print(f"  START-MISMATCH: {s['start_mismatch']}  MID-MISMATCH: {s['mid_mismatch']}  "
          f"END-MISMATCH: {s['end_mismatch']}  LENGTH-MISMATCH: {s['length_mismatch']}")


def _print_stats(st):
    print(f"Log: {st['log']}")
    print(f"{'d':>3}  {'PASS':>5}  {'FAIL':>5}  {'START':>5}  {'MID':>5}  {'END':>5}  {'LEN':>5}")
    print('-' * 46)
    for d in sorted(st['digits']):
        s = st['digits'][d]
        print(f"{d:>3}  {s['pass']:>5}  {s['fail']:>5}  {s['start']:>5}  {s['mid']:>5}  {s['end']:>5}  {s['length']:>5}")


def _print_failures(recs):
    if not recs:
        print('(no failures matching filter)')
        return
    for r in recs:
        print(f"d={r['d']} I={r['inc']} L={r['L']}  {r['status']}  banner={r['banner']}")
        if r['std']:
            print(f"  standard: start={r['std']['start']}  mid={r['std']['mid']}  end={r['std']['end']}")
        if r['pyr']:
            print(f"  pyramid:  start={r['pyr']['start']}  mid={r['pyr']['mid']}  end={r['pyr']['end']}")
        for w in r['mismatches']:
            print(f"  ⚠ {w}")
        print()


def fix_report(log_before, log_after):
    """
    Compare two runs and return a structured diff:
      fixed        — records that went FAIL → PASS (good)
      regressed    — records that went PASS → FAIL (bad)
      net          — fixed - regressed
      by_digit     — per-digit breakdown of both
      new_mismatch_types — mismatch types that appeared in log_after but not log_before
    """
    def load(path):
        records = {}
        mismatches = {}
        for rec in _parse_records(path):
            k = (rec['d'], rec['inc'], rec['L'])
            records[k] = rec['status']
            mismatches[k] = set(rec['mismatches'])
        return records, mismatches

    s1, m1 = load(log_before)
    s2, m2 = load(log_after)
    all_keys = sorted(set(s1) | set(s2))

    fixed, regressed = [], []
    by_digit = {}
    for k in all_keys:
        d = k[0]
        if d not in by_digit:
            by_digit[d] = {'fixed': 0, 'regressed': 0}
        v1, v2 = s1.get(k), s2.get(k)
        if v1 == 'FAIL' and v2 == 'PASS':
            fixed.append({'d': k[0], 'inc': k[1], 'L': k[2]})
            by_digit[d]['fixed'] += 1
        elif v1 == 'PASS' and v2 == 'FAIL':
            regressed.append({'d': k[0], 'inc': k[1], 'L': k[2],
                              'new_mismatches': m2.get(k, set()) - m1.get(k, set())})
            by_digit[d]['regressed'] += 1

    # Mismatch types that increased in frequency
    def mtype_counts(mdict):
        c = {}
        for ms in mdict.values():
            for m in ms:
                c[m] = c.get(m, 0) + 1
        return c
    mc1, mc2 = mtype_counts(m1), mtype_counts(m2)
    introduced = {k: mc2[k] for k in mc2 if mc2[k] > mc1.get(k, 0)}
    eliminated = {k: mc1[k] for k in mc1 if mc1.get(k, 0) > mc2.get(k, 0)}

    return {
        'log_before': log_before, 'log_after': log_after,
        'fixed': fixed, 'regressed': regressed,
        'net': len(fixed) - len(regressed),
        'by_digit': by_digit,
        'introduced': introduced,   # mismatch types that got worse
        'eliminated': eliminated,   # mismatch types that got better
    }


def _print_compare(c):
    print(f"Before: {c['log1']}")
    print(f"After:  {c['log2']}")
    print()
    if c['new_passes']:
        print(f"New PASSes ({len(c['new_passes'])}):")
        for t in c['new_passes']:
            print(f"  d={t['d']} I={t['inc']} L={t['L']}  FAIL→PASS")
    if c['new_fails']:
        print(f"Regressions ({len(c['new_fails'])}) ⚠:")
        for t in c['new_fails']:
            print(f"  d={t['d']} I={t['inc']} L={t['L']}  PASS→FAIL")
    print(f"Unchanged PASS: {c['unchanged_pass']}  Unchanged FAIL: {c['unchanged_fail']}")


def _print_segment_patterns(recs, segment, compact=False):
    if not recs:
        print(f'(no {segment.upper()} mismatches matching filter)')
        return
    if compact:
        for r in recs:
            print(f"d={r['d']} I={r['inc']} L={r['L']} | {r['std']} | {r['pyr']}")
    else:
        cur_d = None
        for r in recs:
            if r['d'] != cur_d:
                cur_d = r['d']
                print(f'\n── digit {cur_d} ──')
            print(f"  I={r['inc']:>4} L={r['L']}  std: {r['std']}")
            print(f"  {'':>10}          pyr: {r['pyr']}")


def _print_alignment(recs):
    if not recs:
        print('(no MID mismatches matching filter)')
        return
    print(f"{'d':>3}  {'I':>6}  {'L':>5}  {'const_off':>10}  {'pos_match':>10}  {'mid_match':>10}")
    print('-' * 60)
    for r in recs:
        off  = f"{r['const_offset']:+d}" if r['const_offset'] is not None else '?'
        pm   = 'yes' if r['positional_match'] else ('no' if r['positional_match'] is False else '?')
        mm   = 'yes' if r['midpoint_match']   else ('no' if r['midpoint_match']   is False else '?')
        print(f"{r['d']:>3}  {r['inc']:>6}  {r['L']:>5}  {off:>10}  {pm:>10}  {mm:>10}")
        print(f"  std: {r['std_mid']}")
        print(f"  pyr: {r['pyr_mid']}")
        print()


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0]
    rest = args[1:]

    def _log_arg(rest):
        skip_next = False
        for a in rest:
            if skip_next:
                skip_next = False
                continue
            if a.startswith('--'):
                if '=' not in a:
                    skip_next = True
                continue
            return a
        return None

    def _flag(rest, name):
        for i, a in enumerate(rest):
            if a == name and i + 1 < len(rest):
                return rest[i + 1]
            if a.startswith(name + '='):
                return a.split('=', 1)[1]
        return None

    if cmd == 'count':
        log = _log_arg(rest)
        seg = _flag(rest, '--segment')
        d   = _flag(rest, '--digit')
        print(count(log, segment=seg, digit=d))

    elif cmd == 'sample':
        log = _log_arg(rest)
        seg = _flag(rest, '--segment') or 'mid'
        d   = _flag(rest, '--digit')
        n   = int(_flag(rest, '--n') or 3)
        recs = sample(log, segment=seg, digit=d, n=n)
        _print_segment_patterns(recs, seg, compact=True)

    elif cmd == 'latest':
        n = int(_flag(rest, '--n') or 5)
        for p in list_logs(n):
            print(p)

    elif cmd == 'summary':
        _print_summary(summary(_log_arg(rest)))

    elif cmd == 'stats':
        _print_stats(stats(_log_arg(rest)))

    elif cmd == 'failures':
        log = _log_arg(rest)
        d = _flag(rest, '--digit')
        m = _flag(rest, '--mismatch')
        _print_failures(failures(log, digit=d, mismatch=m))

    elif cmd == 'fix-report':
        non_flag = [a for a in rest if not a.startswith('--')]
        if len(non_flag) < 2:
            print('Usage: fix-report <log_before> <log_after>')
            sys.exit(1)
        r = fix_report(non_flag[0], non_flag[1])
        print(f"Before: {r['log_before']}")
        print(f"After:  {r['log_after']}")
        print(f"\nFixed (FAIL→PASS): {len(r['fixed'])}   Regressed (PASS→FAIL): {len(r['regressed'])}   Net: {r['net']:+d}")
        print(f"\nPer-digit:")
        print(f"  {'d':>3}  {'fixed':>7}  {'regressed':>10}")
        for d in sorted(r['by_digit']):
            s = r['by_digit'][d]
            if s['fixed'] or s['regressed']:
                reg_flag = ' ⚠' if s['regressed'] else ''
                print(f"  {d:>3}  {s['fixed']:>7}  {s['regressed']:>10}{reg_flag}")
        if r['eliminated']:
            print(f"\nEliminated mismatch types:")
            for k, v in sorted(r['eliminated'].items()):
                print(f"  {k}: -{v}")
        if r['introduced']:
            print(f"\nIntroduced mismatch types ⚠:")
            for k, v in sorted(r['introduced'].items()):
                print(f"  {k}: +{v}")
        if not r['regressed']:
            print('\n✓ No regressions.')

    elif cmd == 'compare':
        non_flag = [a for a in rest if not a.startswith('--')]
        if len(non_flag) < 2:
            print('Usage: compare <log1> <log2>')
            sys.exit(1)
        _print_compare(compare(non_flag[0], non_flag[1]))

    elif cmd in ('mid-patterns', 'start-patterns', 'end-patterns'):
        seg     = cmd.split('-')[0]   # 'mid', 'start', 'end'
        log     = _log_arg(rest)
        d       = _flag(rest, '--digit')
        compact = '--compact' in rest
        _print_segment_patterns(segment_patterns(log, segment=seg, digit=d), seg, compact=compact)

    elif cmd == 'detect-alignment':
        log = _log_arg(rest)
        d   = _flag(rest, '--digit')
        m   = _flag(rest, '--mode') or 'all'
        _print_alignment(detect_alignment(log, digit=d, mode=m))

    elif cmd == 'tail':
        log = _log_arg(rest)
        n = int(_flag(rest, '--n') or 30)
        print(tail(log, n))

    else:
        print(f'Unknown command: {cmd}')
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
