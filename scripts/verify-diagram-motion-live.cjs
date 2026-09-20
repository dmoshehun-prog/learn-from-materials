// Live browser check of the diagram wire motion in a generated learning page.
//
// Covers the failure modes that a static audit cannot see:
//   1. first open        — wires draw in, then the map rests
//   2. tab switch away   — graph removed from view
//   3. tab switch back   — wires MUST still be visible (the reported bug)
//   4. three themes      — every palette recolours wires, heads and arrowheads
//   5. reduced motion    — composed still: lines complete, nothing moving
//
//   node scripts/verify-diagram-motion.cjs --live page.html [--theme warm-paper]
//
// Requires Edge or Chrome and needs no extra packages beyond `ws`.
// Pass --force-prefers-reduced-motion through the browser to test the still state.

const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');

const EDGE_CANDIDATES = [
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
  '/usr/bin/microsoft-edge',
  '/usr/bin/google-chrome',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
];
const browserPath = process.env.BROWSER_PATH || EDGE_CANDIDATES.find(p => { try { return fs.existsSync(p); } catch (e) { return false; } });
if (!browserPath) {
  console.error('No Edge/Chrome found. Set BROWSER_PATH to the executable.');
  process.exit(2);
}

const args = process.argv.slice(2);
const file = args.find(a => !a.startsWith('--'));
const wantReduced = args.includes('--rm');
const shotDir = (() => { const i = args.indexOf('--shots'); return i > -1 ? args[i + 1] : null; })();
if (!file) {
  console.error('usage: node verify-diagram-motion.cjs --live <page.html> [--rm] [--shots <dir>]');
  process.exit(2);
}
if (shotDir) fs.mkdirSync(shotDir, { recursive: true });

const PORT = 9411 + Math.floor(Math.random() * 60);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const getJson = url => new Promise((res, rej) => {
  http.get(url, r => { let d = ''; r.on('data', c => d += c); r.on('end', () => res(JSON.parse(d))); }).on('error', rej);
});

const PROBE = [
  '(function(){',
  '  var out=[];',
  '  [].slice.call(document.querySelectorAll(".diagram-studio")).forEach(function(s,i){',
  '    var svg=s.querySelector(".diagram-wires");',
  '    var wires=[].slice.call(s.querySelectorAll(".diagram-wire"));',
  '    var flows=[].slice.call(s.querySelectorAll(".diagram-flow"));',
  '    var r=s.getBoundingClientRect();',
  '    var mk=[].slice.call(s.querySelectorAll("marker path")).map(function(p){',
  '      return {cls:p.getAttribute("class"),fill:getComputedStyle(p).fill,stroke:getComputedStyle(p).stroke};});',
  '    out.push({i:i,vis:r.height>0&&r.width>0,',
  '      cls:svg?svg.getAttribute("class"):null,wires:wires.length,flows:flows.length,',
  '      dash:wires[0]?getComputedStyle(wires[0]).strokeDasharray:null,',
  '      off:wires[0]?getComputedStyle(wires[0]).strokeDashoffset:null,',
  '      flowOp:flows[0]?getComputedStyle(flows[0]).opacity:null,',
  '      inferStroke:(function(){var w=s.querySelector(".diagram-wire.is-inference");return w?getComputedStyle(w).stroke:null;})(),',
  '      markers:mk});',
  '  });',
  '  return JSON.stringify(out);',
  '})()'
].join('\n');

// Both graphs live in the same document, so a raw index is not stable: the panel
// that is off-screen still exists and reports height 0. Always take the visible one.
const pickVisible = list => (list || []).find(o => o.vis) || (list || [])[0] || {};

let failures = 0;
const check = (label, ok, detail) => {
  if (!ok) failures++;
  console.log((ok ? 'PASS  ' : 'FAIL  ') + label.padEnd(34) + (detail == null ? '' : detail));
};

(async () => {
  const profile = path.join(os.tmpdir(), 'edge-lfm-' + Date.now());
  const launch = ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run',
    '--allow-file-access-from-files', '--remote-debugging-port=' + PORT,
    '--user-data-dir=' + profile, '--window-size=1500,1100'];
  if (wantReduced) launch.push('--force-prefers-reduced-motion');
  launch.push('about:blank');

  const child = spawn(browserPath, launch, { stdio: 'ignore' });
  let target = null;
  for (let i = 0; i < 60; i++) {
    try { const l = await getJson('http://127.0.0.1:' + PORT + '/json/list'); target = l.find(t => t.type === 'page'); if (target) break; } catch (e) {}
    await sleep(250);
  }
  if (!target) { console.error('browser did not expose a debug target'); child.kill(); process.exit(1); }

  const WebSocket = require('ws');
  const ws = new WebSocket(target.webSocketDebuggerUrl, { perMessageDeflate: false, maxPayload: 256 * 1024 * 1024 });
  let id = 0;
  const pending = new Map();
  const send = (m, p) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async e => {
    const r = await send('Runtime.evaluate', { expression: e, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 700));
    return r.result.value;
  };
  const errors = [];
  ws.on('message', m => {
    const x = JSON.parse(m);
    if (x.method === 'Runtime.exceptionThrown') errors.push(JSON.stringify(x.params.exceptionDetails).slice(0, 300));
    if (x.id && pending.has(x.id)) { const p = pending.get(x.id); pending.delete(x.id); x.error ? p.rej(new Error(JSON.stringify(x.error))) : p.res(x.result); }
  });
  await new Promise(r => ws.on('open', r));
  await send('Page.enable'); await send('Runtime.enable');
  await send('Page.navigate', { url: 'file:///' + path.resolve(file).replace(/\\/g, '/') });
  await sleep(3000);

  const dismiss = "(function(){var m=document.querySelector('.guide-overlay,.guide-modal');if(m)m.remove();document.body.classList.remove('is-locked');document.documentElement.style.overflow='';return 1;})()";
  await ev(dismiss);

  // --- open the framework graph ------------------------------------------
  await ev("(function(){var t=document.getElementById('tab-frameworks');if(t)t.click();return 1;})()");
  await sleep(900);
  await ev("(function(){var b=[].slice.call(document.querySelectorAll('button'));for(var i=0;i<b.length;i++){if((b[i].textContent||'').trim()==='框架关系图'){b[i].click();return 1;}}return 0;})()");
  await sleep(1200);
  await ev("(function(){var st=[].slice.call(document.querySelectorAll('.diagram-studio'));var s=null;st.forEach(function(x){var r=x.getBoundingClientRect();if(r.height>100&&(!s||r.height>s.getBoundingClientRect().height))s=x;});if(s){var r=s.getBoundingClientRect();scrollBy(0,r.top-80);}return 1;})()");
  await sleep(4200);

  const first = pickVisible(JSON.parse(await ev(PROBE)));
  console.log('--- framework graph, first open ---');
  console.log('   cls=' + first.cls + ' wires=' + first.wires + ' flows=' + first.flows + ' dash=' + first.dash + ' off=' + first.off + ' flowOp=' + first.flowOp);
  if (wantReduced) {
    check('reduced motion: wires complete', first.dash === 'none' || first.dash === '0px');
    check('reduced motion: no flow head', String(first.flowOp) === '0');
    check('reduced motion: drawn class only', (first.cls || '').indexOf('is-drawn') > -1 && (first.cls || '').indexOf('is-flowing') === -1);
  } else {
    check('first open: wires drawn', first.dash === 'none' || first.dash === '0px', 'dash=' + first.dash);
    check('first open: no perpetual flow', String(first.flowOp) === '0', 'opacity=' + first.flowOp);
    check('first open: flow layer present', first.flows > 0, first.flows + ' flow path(s)');
  }

  // --- switch away and back ----------------------------------------------
  await ev("document.getElementById('tab-content').click();1");
  await sleep(1500);
  const away = pickVisible(JSON.parse(await ev(PROBE)));
  console.log('\n--- switched away ---');
  console.log('   vis=' + away.vis + ' cls=' + away.cls);

  await ev("document.getElementById('tab-frameworks').click();1");
  await sleep(3000);
  const back = pickVisible(JSON.parse(await ev(PROBE)));
  console.log('\n--- switched back ---');
  console.log('   vis=' + back.vis + ' cls=' + back.cls + ' dash=' + back.dash + ' off=' + back.off + ' wires=' + back.wires);
  check('tab return: graph visible', back.vis === true);
  check('tab return: wires still drawn', back.dash === 'none' || back.dash === '0px', 'dash=' + back.dash);
  check('tab return: wire count intact', back.wires > 0, back.wires + ' wire(s)');
  check('tab return: still map restored', (back.cls || '').indexOf('is-drawn') > -1 && (back.cls || '').indexOf('is-static') > -1, 'cls=' + back.cls);

  // --- methodology graph across the three themes -------------------------
  await ev("(function(){var t=document.getElementById('tab-rules');if(t)t.click();return 1;})()");
  await sleep(900);
  await ev("(function(){var b=[].slice.call(document.querySelectorAll('button'));for(var i=0;i<b.length;i++){if((b[i].textContent||'').trim()==='方法论关系图'){b[i].click();return 1;}}return 0;})()");
  await sleep(1600);
  await ev("(function(){var g=document.querySelector('.method-map');if(g){var r=g.getBoundingClientRect();scrollBy(0,r.top-90);}return 1;})()");
  await sleep(3200);

  console.log('\n--- methodology graph, themes ---');
  const seen = {};
  for (const theme of ['warm-paper', 'minimal', 'dark']) {
    await ev('document.body.setAttribute("data-theme","' + theme + '");1');
    await sleep(2800);
    const d = pickVisible(JSON.parse(await ev(PROBE)));
    seen[theme] = d;
    const mk = (d.markers || []).map(m => m.cls + '=' + m.fill + '/' + m.stroke).join(' ');
    console.log('   ' + theme.padEnd(11) + ' vis=' + d.vis + ' wires=' + d.wires + ' dash=' + d.dash + ' flowOp=' + d.flowOp);
    console.log('   ' + ' '.repeat(11) + ' inference=' + d.inferStroke);
    console.log('   ' + ' '.repeat(11) + ' ' + mk);
    check(theme + ': graph visible', d.vis === true);
    check(theme + ': wires drawn', d.dash === 'none' || d.dash === '0px');
    check(theme + ': all arrowheads solid', (d.markers || []).length >= 3 && d.markers.every(m => m.stroke === 'none'));
    if (shotDir) {
      const vh = await ev('innerHeight');
      const sy = await ev('scrollY');
      const shot = await send('Page.captureScreenshot', {
        format: 'png', captureBeyondViewport: true,
        clip: { x: 0, y: sy, width: 1440, height: Math.max(1, Math.min(vh, 900)), scale: 1 }
      });
      if (shot && shot.data) fs.writeFileSync(path.join(shotDir, 'motion-' + theme + (wantReduced ? '-rm' : '') + '.png'), Buffer.from(shot.data, 'base64'));
    }
  }
  const inks = ['warm-paper', 'minimal', 'dark'].map(t => seen[t] && seen[t].inferStroke);
  check('inference colour is themed', new Set(inks).size >= 2, inks.join(' / '));

  check('no JS exceptions', errors.length === 0, errors.length ? errors.join(' | ') : '');

  ws.close(); child.kill(); await sleep(400);
  try { fs.rmSync(profile, { recursive: true, force: true }); } catch (e) {}

  console.log('');
  if (failures) { console.log('RESULT: ' + failures + ' check(s) FAILED'); process.exit(1); }
  console.log('RESULT: all checks passed');
  process.exit(0);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
