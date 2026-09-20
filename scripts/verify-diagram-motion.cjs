// Static structural audit of a generated single-file learning page.
//
// Checks the invariants that a text-only edit can silently break: tag balance,
// the embedded pageData JSON, theme-token discipline, and — most importantly —
// the presence of the restrained wire-motion contract (one entrance, one
// selected-edge direction cue, rebuild still state,
// hidden-panel guard, reduced-motion gate).
//
//   node scripts/verify-diagram-motion.cjs page.html
//
// Exit code 0 = all invariants hold, 1 = at least one failed.

const fs = require('fs');

const file = process.argv[2];
if (!file) {
  console.error('usage: node verify-diagram-motion.cjs <page.html>');
  process.exit(2);
}
const s = fs.readFileSync(file, 'utf8');

let failures = 0;
const check = (label, ok, detail) => {
  if (!ok) failures++;
  console.log((ok ? 'PASS  ' : 'FAIL  ') + label.padEnd(30) + (detail == null ? '' : detail));
};

// ---- structure ------------------------------------------------------------
const stripped = s
  .replace(/<script[\s\S]*?<\/script>/gi, '')
  .replace(/<style[\s\S]*?<\/style>/gi, '')
  .replace(/<!--[\s\S]*?-->/g, '');
const VOID = /^<(br|hr|img|input|meta|link|source|area|base|col|embed|param|track|wbr)\b/i;
const census = {};
let opens = 0;
for (const m of stripped.matchAll(/<(\w[\w-]*)(?:\s[^>]*)?>/g)) {
  if (/\/>$/.test(m[0]) || VOID.test(m[0])) continue;
  opens++;
  const t = m[1].toLowerCase();
  census[t] = (census[t] || 0) + 1;
}
let closes = 0;
for (const m of stripped.matchAll(/<\/(\w[\w-]*)>/g)) {
  closes++;
  const t = m[1].toLowerCase();
  census[t] = (census[t] || 0) - 1;
}
console.log('bytes          ', Buffer.byteLength(s));
console.log('lines          ', s.split('\n').length);
check('tag balance', opens === closes, opens + ' / ' + closes);
const unbalanced = Object.entries(census).filter(([, v]) => v !== 0);
check('no unbalanced tags', unbalanced.length === 0, JSON.stringify(unbalanced));

const pd = s.match(/<script id="pageData"[^>]*>([\s\S]*?)<\/script>/);
if (pd) {
  try { check('pageData JSON parses', true, 'keys=' + Object.keys(JSON.parse(pd[1])).length); }
  catch (e) { check('pageData JSON parses', false, e.message); }
} else check('pageData JSON parses', false, 'block missing');

// ---- theming discipline ---------------------------------------------------
const hardcoded = (s.match(/\.diagram-[^{]*\{[^}]*#[0-9a-fA-F]{3,6}/g) || []);
check('no hard-coded diagram colours', hardcoded.length === 0, hardcoded.length + ' rule(s)');

// ---- arrowheads: solid fill, never a stroked wedge ------------------------
check('three arrowhead markers',
  (s.match(/dg-arrow-normal/g) || []).length > 0 &&
  (s.match(/dg-arrow-feedback/g) || []).length > 0 &&
  (s.match(/dg-arrow-inference/g) || []).length > 0);
// The three marker paths are built in one loop, so the triangle literal appears
// once in the script while the marker *ids* appear once each. Assert the solid
// triangle exists and that all three markers are constructed from it.
const solidTriangle = /d:'M 0 0 L 10 5 L 0 10 Z'/.test(s);
const markerLoop = /\[\[['"]normal['"],['"]dg-arrow-normal['"],\d+\],\s*\[['"]feedback['"],['"]dg-arrow-feedback['"],\d+\],\s*\[['"]inference['"],['"]dg-arrow-inference['"],\d+\]\]/.test(s);
check('arrowheads are solid triangles', solidTriangle && markerLoop,
  solidTriangle ? (markerLoop ? '' : 'loop does not build all three') : 'triangle literal missing');
check('no stroked marker wedge', !/marker[\s\S]{0,400}stroke-width:\s*1/.test(s) || !solidTriangle);
check('inference arrowheads not stroked', /dg-arrow-inference\{fill:var\(--dg-arrow-inference\);opacity/.test(s.replace(/\s+/g, '')));
check('no legacy dashed inference',
  !/stroke-dasharray:\s*6\s+5/.test(s) && !/dashed inference/i.test(s));

// ---- motion contract ------------------------------------------------------
console.log('--- wire motion ---');
check('draw-in keyframes', /@keyframes\s+dg-draw/.test(s));
check('flow keyframes', /@keyframes\s+dg-flow/.test(s));
check('no perpetual feedback pulse', !/@keyframes\s+dg-breath/.test(s));
check('selected cue runs once', /\.diagram-wires\.is-flowing \.diagram-flow\.is-active\{[^}]*linear 1/.test(s));
check('width and overview modes', /fitMode==='all'/.test(s) && /查看全图/.test(s));
check('is-drawn state', /is-drawn/.test(s));
check('is-flowing state', /is-flowing/.test(s));
check('flow layer is a separate path', /diagram-flow/.test(s));
check('geometry measured after insert', /getTotalLength/.test(s));
check('rebuild re-arms the draw', /function\s+settleWires/.test(s) && /function\s+armDraw/.test(s));
check('hidden-panel layout guard', /clientWidth<=0/.test(s));
check('visibility re-announce', /const\s+announce\s*=/.test(s));
check('refresh exported from mount', /refresh\(\)\{|refresh\s*:\s*function/.test(s) && /\{select,layout,root,positions,refresh\}/.test(s));
check('host calls refresh', /diagram\.refresh/.test(s) || /\.refresh\(\)/.test(s));
check('reduced-motion still composed', (s.match(/prefers-reduced-motion/g) || []).length >= 2);
check('reduced-motion gated in JS', /RM\.matches/.test(s));

// ---- relationship chip layout --------------------------------------------
console.log('--- card layout ---');
const chipRule = s.match(/\.diagram-transition-label\s*\{([^}]*)\}/);
check('relation chips wrap', !!chipRule && /white-space\s*:\s*normal/.test(chipRule[1]) && /overflow-wrap\s*:\s*anywhere/.test(chipRule[1]));
check('relation chips not ellipsized', !!chipRule && !/text-overflow\s*:\s*ellipsis/.test(chipRule[1]) && !/overflow\s*:\s*hidden/.test(chipRule[1]));
check('card heights measured for rows', /cards\.get\(n\.id\)\.offsetHeight/.test(s) && /heights\[p\.row\]\s*=\s*Math\.max/.test(s));

// ---- registry -------------------------------------------------------------
console.log('--- wiring ---');
console.log('mount calls    ', (s.match(/LFMGraphStudio\.mount\(/g) || []).length);

console.log('');
if (failures) {
  console.log('RESULT: ' + failures + ' check(s) FAILED');
  process.exit(1);
}
console.log('RESULT: all checks passed');
process.exit(0);
