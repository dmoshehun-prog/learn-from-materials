// Regression check for nested framework-hover scrolling.
// Run: node scripts/test-graph-hover-wheel.cjs
const fs = require('fs');
const path = require('path');
const assert = require('assert');

const root = path.resolve(__dirname, '..');
const js = fs.readFileSync(path.join(root, 'templates', 'graph-studio.js'), 'utf8');
const css = fs.readFileSync(path.join(root, 'templates', 'extensions.css'), 'utf8');
const start = js.indexOf('function applyHoverWheel(delta,target){');
const end = js.indexOf("hover.addEventListener('wheel'", start);
assert(start >= 0 && end > start, 'wheel handler is present');
assert(/\.relation-edge-list\s*\{[^}]*max-height:360px;overflow:auto/.test(css),
  'framework relation list retains its own scrollbar');
assert(js.includes("applyHoverWheel(e.deltaY*(e.deltaMode===1?40:e.deltaMode===2?hover.clientHeight:1),e.target)"),
  'hover listener passes its target to the wheel handler');

function scrollBox(scrollHeight, clientHeight, initial = 0) {
  let value = initial;
  return {
    scrollHeight, clientHeight,
    get scrollTop() { return value; },
    set scrollTop(next) { value = Math.max(0, Math.min(scrollHeight - clientHeight, next)); }
  };
}

const inner = scrollBox(720, 360);
const hover = Object.assign(scrollBox(800, 400), {contains: node => node === inner});
const target = {closest: selector => selector === '.relation-edge-list' ? inner : null};
const applyHoverWheel = new Function('hover', js.slice(start, end) + '\nreturn applyHoverWheel;')(hover);

applyHoverWheel(120, target);
assert.strictEqual(inner.scrollTop, 120);
assert.strictEqual(hover.scrollTop, 0);
applyHoverWheel(400, target);
assert.strictEqual(inner.scrollTop, 360);
assert.strictEqual(hover.scrollTop, 160);
applyHoverWheel(-400, target);
assert.strictEqual(inner.scrollTop, 0);
assert.strictEqual(hover.scrollTop, 120);
applyHoverWheel(100, {closest: () => null});
assert.strictEqual(hover.scrollTop, 220);
console.log('PASS nested framework wheel and outer-panel fallback');
