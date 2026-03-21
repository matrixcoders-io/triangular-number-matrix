/**
 * verify_pyramid.js
 *
 * Verifies that the NEW delta-design buildPyramid algorithm:
 *   1. Produces exactly 1998 digit characters across all rows.
 *   2. Every digit appears at the EXACT position it occupies in the standard string.
 *   3. No position is covered twice (no overlap).
 *   4. No position is missing (complete coverage of 0..1997).
 */

'use strict';

// ─── Standard reference string (1998 digits) ────────────────────────────────
const STANDARD =
  '617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283950617283951049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716049382716';

const VPC = '104';
const HPL = '617283950';
const HPR = '049382716';

console.log('=== Pyramid Algorithm Verification ===\n');
console.log(`Standard string length : ${STANDARD.length} chars`);
console.log(`VPC="${VPC}"  hpl="${HPL}"  hpr="${HPR}"\n`);

// ─── Replicate buildPyramid (pure-text version, no HTML) ────────────────────
function buildPyramidRows(text, vpcVal, hpl, hpr) {
  const vpcIdx = text.indexOf(vpcVal);
  if (vpcIdx === -1) throw new Error('VPC not found in text');

  const leftPart  = text.slice(0, vpcIdx);
  const rightPart = text.slice(vpcIdx + vpcVal.length);
  const hplLen    = hpl.length;
  const hprLen    = hpr.length;
  const vpcLen    = vpcVal.length;

  // Left side
  const leftRemLen  = leftPart.length % hplLen;
  const leftRemStr  = leftRemLen > 0 ? leftPart.slice(-leftRemLen) : '';
  const leftFullStr = leftRemLen > 0 ? leftPart.slice(0, -leftRemLen) : leftPart;
  const leftFull    = [];
  for (let i = 0; i < leftFullStr.length; i += hplLen)
    leftFull.push(leftFullStr.slice(i, i + hplLen));

  // Right side
  const rightRemLen  = rightPart.length % hprLen;
  const rightRemStr  = rightRemLen > 0 ? rightPart.slice(0, rightRemLen) : '';
  const rightFullStr = rightRemLen > 0 ? rightPart.slice(rightRemLen) : rightPart;
  const rightFull    = [];
  for (let i = 0; i < rightFullStr.length; i += hprLen)
    rightFull.push(rightFullStr.slice(i, i + hprLen));

  const N   = leftFull.length;
  const M   = rightFull.length;
  const gapCol = vpcIdx;  // column where VPC starts

  // Collect rows as { col, content } objects so we can verify positions
  const rows = [];

  // Apex
  rows.push({ col: gapCol, content: vpcVal, label: 'apex' });

  // Partial row
  if (leftRemLen > 0 || rightRemLen > 0) {
    const parts = [];
    if (leftRemLen > 0)
      parts.push({ col: gapCol - leftRemLen, content: leftRemStr });
    if (rightRemLen > 0)
      parts.push({ col: gapCol + vpcLen, content: rightRemStr });
    rows.push({ parts, label: 'partial' });
  }

  // Body rows
  const rightPartStart = gapCol + vpcLen + rightRemLen;
  const cap = Math.max(N, M);
  for (let k = 1; k <= cap; k++) {
    const leftCol  = gapCol - leftRemLen - k * hplLen;
    const rightCol = rightPartStart + (k - 1) * hprLen;
    const hasLeft  = k <= N;
    const hasRight = k <= M;

    const parts = [];
    if (hasLeft)  parts.push({ col: leftCol,  content: leftFull[N - k] });
    if (hasRight) parts.push({ col: rightCol, content: rightFull[k - 1] });
    rows.push({ parts, label: `body-k${k}` });
  }

  return { rows, meta: { vpcIdx, vpcLen, hplLen, hprLen, leftRemLen, rightRemLen, N, M, leftFull, rightFull, leftRemStr, rightRemStr } };
}

// ─── Flatten all placed digits into a position→char map ─────────────────────
function flattenRows(rows) {
  const posMap = new Map(); // position -> char
  const overlaps = [];
  let totalDigits = 0;

  for (const row of rows) {
    // Normalise: apex row has col+content directly, body/partial have parts array
    const parts = row.parts ? row.parts : [{ col: row.col, content: row.content }];
    for (const { col, content } of parts) {
      for (let i = 0; i < content.length; i++) {
        const ch = content[i];
        if (!/\d/.test(ch)) continue; // skip spaces (shouldn't occur in content)
        const pos = col + i;
        totalDigits++;
        if (posMap.has(pos)) {
          overlaps.push({ pos, existing: posMap.get(pos), incoming: ch, row: row.label });
        } else {
          posMap.set(pos, ch);
        }
      }
    }
  }
  return { posMap, overlaps, totalDigits };
}

// ─── Run ─────────────────────────────────────────────────────────────────────
const { rows, meta } = buildPyramidRows(STANDARD, VPC, HPL, HPR);

console.log('--- Decomposition summary ---');
console.log(`vpcIdx       = ${meta.vpcIdx}`);
console.log(`leftRemLen   = ${meta.leftRemLen}  leftRemStr  = "${meta.leftRemStr}"`);
console.log(`rightRemLen  = ${meta.rightRemLen}  rightRemStr = "${meta.rightRemStr}"`);
console.log(`N (leftFull) = ${meta.N}`);
console.log(`M (rightFull)= ${meta.M}`);
console.log(`Total rows generated: ${rows.length}\n`);

const { posMap, overlaps, totalDigits } = flattenRows(rows);

// Check 1: total digits
console.log('--- Check 1: Total digit count ---');
console.log(`Digits placed by pyramid : ${totalDigits}`);
console.log(`Expected (standard len)  : ${STANDARD.length}`);
const check1 = totalDigits === STANDARD.length;
console.log(`RESULT: ${check1 ? 'PASS' : 'FAIL'}\n`);

// Check 2 & 3: position correctness and overlaps
console.log('--- Check 2: Correct positions (digit matches standard at same index) ---');
let mismatches = 0;
for (const [pos, ch] of posMap) {
  if (STANDARD[pos] !== ch) {
    mismatches++;
    if (mismatches <= 10)
      console.log(`  MISMATCH at pos ${pos}: pyramid="${ch}" standard="${STANDARD[pos]}"`);
  }
}
if (mismatches > 10) console.log(`  ... and ${mismatches - 10} more mismatches`);
const check2 = mismatches === 0;
console.log(`RESULT: ${check2 ? 'PASS' : 'FAIL'} (${mismatches} mismatches)\n`);

console.log('--- Check 3: No overlaps ---');
if (overlaps.length > 0) {
  overlaps.slice(0, 10).forEach(o =>
    console.log(`  OVERLAP at pos ${o.pos}: existing="${o.existing}" incoming="${o.incoming}" row=${o.row}`)
  );
  if (overlaps.length > 10) console.log(`  ... and ${overlaps.length - 10} more`);
}
const check3 = overlaps.length === 0;
console.log(`RESULT: ${check3 ? 'PASS' : 'FAIL'} (${overlaps.length} overlaps)\n`);

// Check 4: complete coverage of 0..1997
console.log('--- Check 4: Complete coverage of positions 0..1997 ---');
const missing = [];
for (let i = 0; i < STANDARD.length; i++) {
  if (!posMap.has(i)) missing.push(i);
}
if (missing.length > 0) {
  console.log(`  Missing positions (first 20): ${missing.slice(0, 20).join(', ')}`);
}
const check4 = missing.length === 0;
console.log(`RESULT: ${check4 ? 'PASS' : 'FAIL'} (${missing.length} missing positions)\n`);

// ─── Summary ─────────────────────────────────────────────────────────────────
console.log('=== SUMMARY ===');
console.log(`Check 1 — Total digit count matches 1998     : ${check1 ? 'PASS' : 'FAIL'}`);
console.log(`Check 2 — Every digit at correct position     : ${check2 ? 'PASS' : 'FAIL'}`);
console.log(`Check 3 — No position covered twice           : ${check3 ? 'PASS' : 'FAIL'}`);
console.log(`Check 4 — No position missing (0..1997)       : ${check4 ? 'PASS' : 'FAIL'}`);

const allPass = check1 && check2 && check3 && check4;
console.log(`\nOverall: ${allPass ? '✓ ALL CHECKS PASSED' : '✗ ONE OR MORE CHECKS FAILED'}`);
process.exit(allPass ? 0 : 1);
