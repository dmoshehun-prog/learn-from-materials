// Usage: node scripts/verify-features.js examples/features-en.html examples/features-zh.html
// Uses existing Playwright only. Optional: LFM_BROWSER_EXECUTABLE and LFM_SCREENSHOT_DIR.
'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const {pathToFileURL} = require('node:url');
let chromium;
try { ({chromium} = require('playwright')); }
catch { console.error('Playwright is unavailable; no dependencies were installed.'); process.exit(2); }

(async () => {
  if (process.argv.length < 3) throw new Error('Supply one or more local feature-demo HTML paths.');
  const browser = await chromium.launch({headless:true, ...(process.env.LFM_BROWSER_EXECUTABLE ? {executablePath:process.env.LFM_BROWSER_EXECUTABLE} : {})});
  try {
    for (const file of process.argv.slice(2)) {
      const target = pathToFileURL(path.resolve(file)).href;
      const context = await browser.newContext({serviceWorkers:'block', viewport:{width:1440,height:1050}});
      const errors = [], requests = [];
      await context.route('**/*', async route => {
        const url = route.request().url();
        if (url === target || url.startsWith('data:') || url.startsWith('blob:')) await route.continue();
        else {requests.push(url); await route.abort();}
      });
      await context.addInitScript(() => {
        window.__copied = '';
        Object.defineProperty(navigator, 'clipboard', {configurable:true,value:{writeText:async text => {if(window.__copyDenied) throw new Error('denied');window.__copied=text;}}});
      });
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(target);
      const data = await page.locator('#pageData').evaluate(el=>JSON.parse(el.textContent));
      const en = data.meta.language === 'en';
      assert.equal(await page.locator('html').getAttribute('lang'), en?'en':'zh-CN');
      await page.locator('#guideSkip').click();
      for(const id of ['frameworks','content','glossary','rules','practice','notes']){
        await page.locator('#tab-'+id).click();
        if(en) assert(!/[\u3400-\u9fff]/.test(await page.locator('#'+id).innerText()), 'Untranslated UI in '+id);
      }
      await page.locator('#tab-frameworks').click();
      await page.locator('#frameworks > .relation-tools button').nth(1).click();
      const total = data.frameworks.length;
      assert.equal(await page.locator('#frameworks-relations .node').count(), Math.min(12,total));
      if(total>12){await page.locator('#frameworks-relations .relation-tools button').click();assert(await page.locator('#frameworks-relations .node').count()>0);}
      await page.locator('#frameworks-relation-focus').selectOption(data.frameworks[0].id);
      assert((await page.locator('#frameworks-relations .relation-detail').innerText()).includes(data.frameworks[0].source));
      await page.locator('#frameworks-relations .relation-detail button').click();
      assert.equal(await page.locator('#methodSelect').inputValue(), data.frameworks[0].id);
      const problem = 'My team <script>window.__pwned=true</script> cannot agree on the scope.';
      await page.locator('#methodProblem').fill(problem);
      await page.locator('#methodGoal').fill('Agree on a small test this week.');
      await page.locator('#methodLimits').fill('Two people; no external data uploads.');
      await page.locator('#methodForm button[type=submit]').click();
      await page.waitForFunction(()=>document.getElementById('methodStatus').textContent.length>0);
      const prompt = await page.locator('#methodPrompt').inputValue();
      assert.equal(await page.evaluate(()=>window.__copied), prompt);
      const payload = JSON.parse(prompt.slice(prompt.indexOf('{\n')));
      assert.equal(payload.problem,problem); assert.equal(payload.method.id,data.frameworks[0].id);
      assert.equal(payload.method.source,data.frameworks[0].source);
      assert.equal(await page.evaluate(()=>!!window.__pwned),false);
      if(en) assert(!/[\u3400-\u9fff]/.test(prompt));
      await page.locator('#methodProblem').fill('Changed problem');
      assert.equal(await page.locator('#methodPrompt').inputValue(),'');
      await page.evaluate(()=>{window.__copyDenied=true;window.__copied='';});
      await page.locator('#methodForm button[type=submit]').click();
      await page.waitForFunction(()=>document.getElementById('methodStatus').textContent.length>0);
      assert.equal(await page.evaluate(()=>window.__copied),'');
      assert((await page.locator('#methodPrompt').inputValue()).includes('Changed problem'));
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#methodDialog').evaluate(el=>el.open),false);
      await page.evaluate(()=>window.__copyDenied=false);
      await page.locator('#tab-rules').click();
      await page.locator('#applyMethod').click();
      assert.equal(await page.locator('#methodSelect').inputValue(),'auto');
      await page.locator('#methodProblem').fill('Which method fits this situation?');
      await page.locator('#methodForm button[type=submit]').click();
      const auto = await page.locator('#methodPrompt').inputValue();
      const autoData = JSON.parse(auto.slice(auto.indexOf('{\n')));
      assert.equal(autoData.methodIndex.length,data.frameworks.length+data.decisionRules.length);
      await page.locator('#methodClose').click();
      if(data.decisionRules.length){
        await page.locator('#rules > .relation-tools button').nth(1).click();
        assert.equal(await page.locator('#rules-relations .relation-edge-list').last().locator('li').count(),Math.max(1,data.relationships.length));
        if(data.relationships.some(x=>x.evidence==='inference')) assert(await page.locator('#rules-relations .edge.inference').count()>0);
      }
      if(process.env.LFM_SCREENSHOT_DIR){
        fs.mkdirSync(process.env.LFM_SCREENSHOT_DIR,{recursive:true});
        await page.screenshot({path:path.join(process.env.LFM_SCREENSHOT_DIR,path.basename(file,'.html')+'-desktop.png'),fullPage:true});
      }
      await page.locator('#tab-practice').click();
      await page.locator('#assessmentCopy').click();
      if(en) assert(!/[\u3400-\u9fff]/.test(await page.locator('#assessmentPromptPreview').inputValue()),'Untranslated quiz prompt');
      await page.locator('#mistakeImportText').fill(JSON.stringify({schemaVersion:'knowledge-learning-assistant-mistakes/v1',materialTitle:data.meta.title,mistakes:[{question:'Question',userAnswer:'A',correctAnswer:'B',explanation:'Reason',knowledgePoint:'Topic',unit:'Unit',source:data.frameworks[0].source,status:'已掌握'}]}));
      await page.locator('#mistakeImportPaste').click();
      assert.equal(await page.locator('.mistake-card .mistake-status').innerText(),en?'Mastered':'已掌握');
      await page.locator('#tab-frameworks').click();
      await page.locator('#frameworks > .relation-tools button').first().click();
      await page.locator('#frameworks .note').first().hover();
      await page.locator('#frameworks .note-capture-btn').first().click();
      await page.locator('#tab-notes').click();
      assert(await page.locator('.personal-note-card').count()>0);
      await page.reload();
      await page.locator('#tab-notes').click();
      assert(await page.locator('.personal-note-card').count()>0,'Saved notes lost after reload');
      await page.setViewportSize({width:390,height:844});
      await page.locator('#tab-rules').click();
      if(data.decisionRules.length) await page.locator('#rules > .relation-tools button').nth(1).click();
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+2),'Mobile document overflows');
      await page.locator('#applyMethod').click();
      const box = await page.locator('#methodDialog').boundingBox();
      assert(box.x>=0 && box.x+box.width<=392,'Mobile dialog clipped');
      if(process.env.LFM_SCREENSHOT_DIR) await page.screenshot({path:path.join(process.env.LFM_SCREENSHOT_DIR,path.basename(file,'.html')+'-mobile.png'),fullPage:true});
      assert.deepEqual(errors,[]); assert.deepEqual(requests,[],'Unexpected external requests');
      console.log('PASS '+file+' ('+(en?'English':'Chinese')+', desktop/mobile, graph, prompts, clipboard fallback, persistence, offline)');
      await context.close();
    }
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exit(1);});
