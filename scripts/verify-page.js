// Playwright 自动验证脚本
// 用法: node scripts/verify-page.js <path-to-html>
// 前置：仅在本地已有 Playwright 时运行；本 Skill 不会安装依赖。
let chromium;
try {
  ({ chromium } = require('playwright'));
} catch (error) {
  console.log('⚠️  未安装 Playwright，已跳过增强验证；请以 verify_static.py 结果为准。');
  process.exit(2);
}

(async () => {
  const htmlPath = process.argv[2];
  if (!htmlPath) {
    console.error('用法: node scripts/verify-page.js <path-to-html>');
    process.exit(1);
  }

  const fs = require('fs');
  const path = require('path');
  const { pathToFileURL } = require('url');
  const resolvedHtmlPath = path.resolve(htmlPath);
  if (!['.html', '.htm'].includes(path.extname(resolvedHtmlPath).toLowerCase())) {
    console.error('仅允许验证本地 HTML 文件。');
    process.exit(1);
  }
  try {
    if (!fs.statSync(resolvedHtmlPath).isFile()) throw new Error('not a file');
  } catch (error) {
    console.error('找不到可读取的 HTML 文件：' + resolvedHtmlPath);
    process.exit(1);
  }

  let browser;
  try {
    browser = await chromium.launch();
  } catch (error) {
    console.log('⚠️  浏览器运行时不可用，已跳过增强验证；请以 verify_static.py 结果为准。');
    console.log('   ' + String(error.message || error).split('\n')[0]);
    process.exit(2);
  }
  const context = await browser.newContext({ serviceWorkers: 'block' });
  const errors = [];
  const targetUrl = pathToFileURL(resolvedHtmlPath).href;

  await context.route('**/*', async route => {
    const url = route.request().url();
    if (url === targetUrl || url.startsWith('data:') || url.startsWith('blob:')) {
      await route.continue();
    } else {
      errors.push('❌ 已阻止页面访问非目标资源: ' + url);
      await route.abort('blockedbyclient');
    }
  });
  await context.addInitScript(() => {
    window.WebSocket = class BlockedWebSocket {
      constructor() { throw new Error('WebSocket is disabled during offline verification'); }
    };
    window.EventSource = class BlockedEventSource {
      constructor() { throw new Error('EventSource is disabled during offline verification'); }
    };
  });

  const page = await context.newPage();
  context.on('page', openedPage => {
    if (openedPage !== page) openedPage.close().catch(() => {});
  });
  page.on('pageerror', err => errors.push('❌ JS Error: ' + err.message));

  try {
    await page.goto(targetUrl, { waitUntil: 'domcontentloaded' });
    try {
      await page.evaluate(() => localStorage.clear());
      await page.evaluate(() => {
        localStorage.setItem('knowledge-learning-assistant-reader-profile:v1', JSON.stringify({ profession: '厨师', interests: '烹饪' }));
        localStorage.setItem('knowledge-learning-assistant-guide-seen:v1', '1');
      });
      await page.reload({ waitUntil: 'domcontentloaded' });
    } catch (error) {
      errors.push('❌ 无法准备浏览器本地存储测试: ' + String(error.message || error));
    }

    // 0. 小巴新手引导与读者画像
    const guideOverlay = page.locator('#guideOverlay');
    if (await guideOverlay.count() !== 1) {
      errors.push('❌ 缺少小巴新手引导');
    } else {
      if (!(await guideOverlay.evaluate(el => el.classList.contains('active')))) {
        errors.push('❌ 新生成页面被旧页面的画像或导读状态跳过，首次打开没有显示小巴新手引导');
      } else {
        const initialProfile = await page.evaluate(() => ({
          profession: document.querySelector('#profileProfession').value,
          interests: document.querySelector('#profileInterests').value,
        }));
        if (initialProfile.profession || initialProfile.interests) {
          errors.push('❌ 新生成页面错误带入了其他页面保存的读者画像');
        }
        await page.locator('#profileProfession').fill('销售');
        await page.locator('#profileInterests').fill('汽车和股票');
        await page.locator('#guideSave').click();
        if (await guideOverlay.evaluate(el => el.classList.contains('active'))) errors.push('❌ 保存画像后引导没有关闭');
        const profile = await page.evaluate(() => {
          try {
            const key = Object.keys(localStorage).find(item => item.indexOf('knowledge-learning-assistant-reader-profile:v2:') === 0);
            return key ? JSON.parse(localStorage.getItem(key) || '{}') : {};
          } catch (error) { return {}; }
        });
        if (profile.profession !== '销售' || profile.interests !== '汽车和股票') errors.push('❌ 职业或兴趣画像没有正确保存');
        await page.locator('#guideBtn').click();
        if (!(await guideOverlay.evaluate(el => el.classList.contains('active')))) errors.push('❌ 工具栏无法重新打开小巴引导');
        await page.locator('#guideSkip').click();
        console.log('✅ 小巴引导 — 可讲解交互、采集并重新编辑读者画像');
      }
    }

    // 1. 检查占位符残留
    const html = await page.content();
    if (html.includes('{{') && html.includes('}}')) {
      errors.push('❌ 残留占位符 {{...}}（可能含 {{theme_style}}/{{theme_name}} 未填）');
    } else {
      console.log('✅ 无占位符残留');
    }

    // 1b. 检查主题（body data-theme）
    const theme = await page.getAttribute('body', 'data-theme');
    const bodyMode = await page.getAttribute('body', 'data-mode');
    const knownThemes = ['warm-paper', 'minimal', 'dark', 'ink-wash', 'vintage-editorial', 'paper-ink'];
    if (!theme) {
      errors.push('❌ <body> 缺少 data-theme 属性（{{theme_name}} 未填）');
    } else if (!knownThemes.includes(theme)) {
      errors.push('❌ 未知主题 data-theme="' + theme + '"，已知: ' + knownThemes.join('/'));
    } else {
      console.log('🎨 当前主题: ' + theme);
    }

    // 1c. 框架与术语必须按材料首次出现顺序嵌入页面。
    if (bodyMode === 'overview') {
      const orderedData = await page.evaluate(() => JSON.parse(document.querySelector('#pageData').textContent || '{}'));
      for (const [field, label] of [['frameworks', '核心框架'], ['glossary', '术语大全']]) {
        const values = Array.isArray(orderedData[field]) ? orderedData[field].map(item => item && item.sourceOrder) : [];
        const sorted = values.slice().sort((a, b) => a - b);
        if (!values.length || values.some(value => !Number.isInteger(value)) || JSON.stringify(values) !== JSON.stringify(sorted)) {
          errors.push('❌ ' + label + '未按材料首次出现顺序嵌入页面');
        }
      }
      console.log('✅ 核心框架与术语大全 — 按材料首次出现顺序排列');
    }

    // 2. 验证 Tab
    const tabs = await page.locator('.tab').all();
    console.log(`📑 Tab 数量: ${tabs.length}`);
    if (tabs.length === 0) {
      errors.push('❌ 没有找到 Tab 按钮');
    } else {
      for (let i = 0; i < tabs.length; i++) {
        await tabs[i].click();
        await page.waitForTimeout(100);
        const selected = await tabs[i].getAttribute('aria-selected');
        if (selected !== 'true') {
          errors.push(`❌ Tab ${i} 点击后 aria-selected 不是 true`);
        }
      }
      console.log(`✅ ${tabs.length} 个 Tab 全部可切换`);
    }

    // 2b. 验证六主题实时切换
    const picker = page.locator('#themePicker');
    if (await picker.count() !== 1) {
      errors.push('❌ 缺少主题选择器');
    } else {
      for (const themeName of knownThemes) {
        await picker.selectOption(themeName);
        const activeTheme = await page.getAttribute('body', 'data-theme');
        if (activeTheme !== themeName) errors.push('❌ 主题切换失败: ' + themeName);
      }
      console.log('✅ 六主题切换 — 正常');
    }

    // 3. 验证 Causal Chain
    const chainBtns = await page.locator('.chain-step').all();
    if (chainBtns.length > 0) {
      // 确保 chain 所在 panel 是可见的
      for (const btn of chainBtns) {
        const visible = await btn.isVisible();
        if (visible) {
          await btn.click();
          await page.waitForTimeout(100);
          const active = await btn.evaluate(el => el.classList.contains('active'));
          if (!active) errors.push('❌ Chain 按钮点击后未激活');
          break;
        }
      }
      // 验证 chainText 有内容
      const ct = await page.locator('#chainText');
      if (await ct.count() > 0) {
        const text = await ct.textContent();
        if (text.length < 10) errors.push('❌ chainText 内容过短');
        else console.log(`✅ Causal Chain (${chainBtns.length} 节点) — 正常`);
      }
    }

    // 4. 验证 Type Selector
    const cityBtns = await page.locator('.city-btn').all();
    if (cityBtns.length > 0) {
      for (const btn of cityBtns) {
        const visible = await btn.isVisible();
        if (visible) {
          await btn.click();
          await page.waitForTimeout(100);
          break;
        }
      }
      const result = await page.locator('.result h3');
      if (await result.count() > 0) console.log('✅ Type Selector — 正常');
    }

    // 5. 验证 Accordion
    const details = await page.locator('.accordion details').all();
    if (details.length > 0) {
      for (const d of details) {
        const visible = await d.isVisible();
        if (visible) {
          const wasOpen = await d.evaluate(el => el.hasAttribute('open'));
          await d.locator('summary').click();
          await page.waitForTimeout(200);
          const isOpen = await d.evaluate(el => el.hasAttribute('open'));
          if (wasOpen === isOpen) errors.push('❌ Accordion 点击后状态未变化');
          break;
        }
      }
      console.log(`✅ Accordion (${details.length} 项) — 可折叠`);
    }

    // 6. 验证 Timeline
    const tlItems = await page.locator('.timeline-item').all();
    if (tlItems.length > 0) console.log(`✅ Timeline (${tlItems.length} 个节点) — 正常渲染`);

    // 7. 验证 Before/After
    const baCols = await page.locator('.before-after .ba-col').all();
    if (baCols.length > 0) console.log(`✅ Before/After (${baCols.length} 列) — 正常渲染`);

    // 8. 验证 Story Card
    const stories = await page.locator('.story').all();
    if (stories.length > 0) console.log(`✅ Story Card (${stories.length} 个) — 正常渲染`);

    // 9. 验证 Quote Card
    const quotes = await page.locator('.quote').all();
    if (quotes.length > 0) console.log(`✅ Quote Card (${quotes.length} 个) — 正常渲染`);

    // 10. 验证 Question list
    const questions = await page.locator('.questions .question').all();
    if (questions.length > 0) console.log(`✅ Questions (${questions.length} 个) — 正常渲染`);

    // 11. 验证 Source Toggle
    const toggle = page.locator('#srcToggle');
    if (await toggle.count() > 0) {
      await toggle.click();
      await page.waitForTimeout(100);
      const hasSources = await page.evaluate(() => document.body.classList.contains('show-sources'));
      if (!hasSources) errors.push('❌ Source Toggle 点击后 body.show-sources 未添加');
      await toggle.click();
      console.log('✅ Source Toggle — 正常');
    }

    // 11b. 内容导学、术语大全、追问弹窗
    // Tab 遍历结束时可能停留在“我的笔记”，先恢复内容面板再读取导航按钮。
    const contentTab = page.locator('.tab[data-panel="content"]');
    if (await contentTab.count() === 1) await contentTab.click();
    const unitButtons = await page.locator('.ch-nav-btn').all();
    if (unitButtons.length > 0) {
      const initialUnitText = await page.locator('#chView').textContent();
      if (!initialUnitText || initialUnitText.length < 80) errors.push('❌ 内容单元首屏没有预渲染正文');
      // 内容导航在桌面端可能处于 sticky 侧栏中，强制点击避免 Playwright 对
      // 视口外 sticky 项目的自动滚动超时；真实用户可正常滚动与点击。
      await unitButtons[unitButtons.length - 1].click({ force: true });
      const unitText = await page.locator('#chView').textContent();
      if (!unitText || unitText.length < 30) errors.push('❌ 内容导学没有切换到目标单元');
      const unitConclusions = await page.locator('#chView .chapter-conclusion').count();
      if (unitConclusions < 1) errors.push('❌ 内容单元缺少可展开结论');
      else console.log(`✅ 内容导学器 (${unitButtons.length} 个单元，${unitConclusions} 组展开结论) — 正常`);
    }
    // 恢复内容导学面板，确保后续深挖与笔记测试从可见的带出处内容启动。
    const restoreContentTab = page.locator('.tab[data-panel="content"]');
    if (await restoreContentTab.count() === 1) await restoreContentTab.click();

    const glossaryTab = page.locator('.tab[data-panel="glossary"]');
    const termItems = page.locator('.term-item');
    if (await glossaryTab.count() === 1) {
      await glossaryTab.click();
      const termCount = await termItems.count();
      if (termCount < 1) errors.push('❌ 术语大全没有可用术语');
      if (termCount > 0) {
        const firstTerm = termItems.first();
        const wasOpen = await firstTerm.evaluate(el => el.hasAttribute('open'));
        await firstTerm.locator('summary').click();
        const isOpen = await firstTerm.evaluate(el => el.hasAttribute('open'));
        if (wasOpen === isOpen) errors.push('❌ 术语展开栏点击后状态未变化');
        const query = (await firstTerm.locator('.term-name').textContent() || '').trim();
        await page.locator('#glossarySearch').fill(query);
        const visibleTerms = await page.locator('.term-item:visible').count();
        if (visibleTerms < 1 || visibleTerms > termCount) errors.push('❌ 术语搜索筛选异常');
        await page.locator('#glossarySearch').fill('');
        const englishTerms = await page.evaluate(() => {
          const data = JSON.parse(document.querySelector('#pageData').textContent || '{}');
          return (data.glossary || []).filter(item => /[A-Za-z]/.test(String(item.term || ''))).length;
        });
        const chineseMeaningCount = await page.locator('.term-zh-meaning').count();
        if (englishTerms > 0 && chineseMeaningCount < englishTerms) errors.push('❌ 英文术语没有同时显示中文含义');
      }
      const askButton = page.locator('#termAskFab');
      await askButton.click();
      if (!(await page.locator('#ddOverlay').evaluate(el => el.classList.contains('active')))) {
        errors.push('❌ 术语大全右下角问号未打开提问框');
      } else {
        const title = await page.locator('#ddTitle').textContent();
        if (!title || !title.includes('术语')) errors.push('❌ 术语提问框标题不正确');
        await page.evaluate(() => {
          window.__learningTestCopied = '';
          Object.defineProperty(navigator, 'clipboard', {
            configurable: true,
            value: { writeText: text => { window.__learningTestCopied = String(text); return Promise.resolve(); } }
          });
        });
        await page.locator('#ddInput').fill('KPI 是什么意思？');
        await page.locator('#ddSubmit').click();
        const copied = await page.evaluate(() => window.__learningTestCopied || '');
        if (!copied.includes('小巴') || !copied.includes('销售') || !copied.includes('汽车和股票')) {
          errors.push('❌ 术语追问没有带入小巴身份和读者画像');
        }
        const requiredProtocol = ['[材料依据]', '[材料未覆盖]', '[模型补充]', '[外部核验]', '首次回答', '不要使用画像举例', '第三层', '图片生成'];
        for (const marker of requiredProtocol) {
          if (!copied.includes(marker)) errors.push('❌ 追问缺少协议标记：' + marker);
        }
        // 复制成功时页面会自动关闭弹窗；仅在仍处于打开状态时再点取消。
        if (await page.locator('#ddOverlay').evaluate(el => el.classList.contains('active'))) {
          await page.locator('#ddCancel').click({ force: true });
        }
      }
      console.log(`✅ 术语大全 (${termCount} 条) — 可搜索、显示中文含义并执行三级讲解`);
    } else if (bodyMode === 'overview') {
      errors.push('❌ 缺少术语大全模块');
    }
    // 术语模块结束后恢复内容导学，避免首个深挖按钮属于隐藏单元导航项。
    if (await restoreContentTab.count() === 1) await restoreContentTab.click();
    const diveButton = page.locator('.panel.active [data-deep-dive]').first();
    if (await diveButton.count() > 0) {
      // 由页面的事件委托处理深挖按钮；直接触发 DOM click 可规避 sticky/折叠容器的可见性差异。
      await diveButton.evaluate(el => el.click());
      if (!(await page.locator('#ddOverlay').evaluate(el => el.classList.contains('active')))) {
        errors.push('❌ 深挖追问弹窗未打开');
      } else {
        await page.locator('#ddCancel').click();
        console.log('✅ 深挖追问 — 正常');
      }
    }

    // 11c. 动态学习自检与本地错题本
    const assessmentTab = page.locator('.tab[data-panel="practice"]');
    if (bodyMode === 'overview' && await assessmentTab.count() !== 1) {
      errors.push('❌ 缺少动态学习自检模块');
    } else if (await assessmentTab.count() === 1) {
      await assessmentTab.click();
      if (await page.locator('.practice-card').count() > 0) errors.push('❌ 学习自检仍平铺预生成题目');
      await page.locator('input[name="assessmentScope"][value="unit"]').check();
      const unitOptions = await page.locator('#assessmentUnit option').count();
      if (unitOptions < 1) errors.push('❌ 指定章节没有可选内容单元');
      else await page.locator('#assessmentUnit').selectOption({ index: unitOptions - 1 });
      await page.evaluate(() => { window.__learningTestCopied = ''; });
      await page.locator('#assessmentCopy').click();
      const assessmentPrompt = await page.evaluate(() => window.__learningTestCopied || '');
      const assessmentMarkers = ['每次只出一道题', 'KLA_MISTAKES_JSON', '当前对话能够访问', '知识库', '动态调整难度', 'question-bank.json', '不要向我报告检测过程', '优先使用原题', '原题不足时'];
      for (const marker of assessmentMarkers) {
        if (!assessmentPrompt.includes(marker)) errors.push('❌ 动态自检口令缺少：' + marker);
      }
      const previewValue = await page.locator('#assessmentPromptPreview').inputValue();
      if (!previewValue || previewValue !== assessmentPrompt) errors.push('❌ 自检口令预览与复制内容不一致');

      const materialMeta = await page.evaluate(() => JSON.parse(document.querySelector('#pageData').textContent || '{}').meta || {});
      const mistakePayload = {
        schemaVersion: 'knowledge-learning-assistant-mistakes/v1',
        materialTitle: materialMeta.title || '',
        knowledgeBase: materialMeta.knowledgeBase || '',
        sessionTitle: '浏览器验证',
        mistakes: [{
          question: '验证错题：问题地图包含什么？',
          userAnswer: '错误答案',
          correctAnswer: '正确答案示例',
          explanation: '遗漏关键要素',
          knowledgePoint: '问题地图',
          unit: '第一章',
          source: '第1章《建立问题地图》 · PDF第10-20页',
          status: '未掌握',
          wrongCount: 1,
        }],
      };
      await page.locator('#mistakeImportText').fill('测验总结\n<<<KLA_MISTAKES_JSON>>>\n' + JSON.stringify(mistakePayload) + '\n<<<END_KLA_MISTAKES_JSON>>>');
      await page.locator('#mistakeImportPaste').click();
      const mistakeCards = page.locator('#mistakeList .mistake-card');
      if (await mistakeCards.count() !== 1) {
        errors.push('❌ AI 错题记录没有导入本地错题本');
      } else {
        await mistakeCards.first().locator('summary').click();
        await page.evaluate(() => { window.__learningTestCopied = ''; });
        await mistakeCards.first().locator('[data-mistake-action="retry"]').click();
        const retryPrompt = await page.evaluate(() => window.__learningTestCopied || '');
        if (!retryPrompt.includes('变式复测') || retryPrompt.includes('正确答案示例')) errors.push('❌ 错题复测口令异常或提前泄露答案');
        await mistakeCards.first().locator('summary').click();
        await mistakeCards.first().locator('[data-mistake-action="status"]').click();
        const statusText = await page.locator('#mistakeList .mistake-status').textContent();
        if (statusText !== '复习中') errors.push('❌ 错题掌握状态没有更新');
      }
      const storedMistakes = await page.evaluate(() => {
        try {
          const key = Object.keys(localStorage).find(item => item.indexOf('knowledge-learning-assistant-mistakes:v1:') === 0);
          return key ? JSON.parse(localStorage.getItem(key) || '[]').length : -1;
        } catch (error) { return -2; }
      });
      if (storedMistakes !== 1) errors.push('❌ 错题没有写入浏览器本地存储');
      console.log('✅ 动态学习自检 — 可按范围生成口令、导入错题并进行变式复测');
    }

    // 11d. 我的笔记：一键保存、去重、编辑、搜索与本地持久化
    const notesTab = page.locator('.tab[data-panel="notes"]');
    if (await notesTab.count() !== 1) {
      errors.push('❌ 缺少我的笔记模块');
    } else {
      const sourceTab = page.locator('.tab:not([data-panel="notes"])').first();
      if (await sourceTab.count() > 0) await sourceTab.click();
      const capture = page.locator('.panel.active .note-capture-btn').first();
      if (await capture.count() < 1) {
        errors.push('❌ 带出处内容没有笔记摘记入口');
      } else {
        await capture.click({ force: true });
        const noteDialogOpen = await page.locator('#noteOverlay').evaluate(el => el.classList.contains('active'));
        if (noteDialogOpen) {
          errors.push('❌ 一键保存仍然打开了复制粘贴弹窗');
        } else {
          if (!(await capture.evaluate(el => el.classList.contains('saved')))) errors.push('❌ 一键保存后按钮未显示已保存状态');
          await capture.click({ force: true });
          await notesTab.click();
          const cards = page.locator('#notesList .personal-note-card');
          if (await cards.count() !== 1) {
            errors.push('❌ 一键保存未写入列表或重复创建了笔记');
          } else {
            await cards.first().locator('summary').click();
            await cards.first().locator('[data-note-action="edit"]').click();
            if (!(await page.locator('#noteOverlay').evaluate(el => el.classList.contains('active')))) errors.push('❌ 笔记编辑弹窗未打开');
            await page.locator('#noteTitleInput').fill('验证笔记标题');
            await page.locator('#noteInsightInput').fill('验证个人理解');
            await page.locator('#noteActionInput').fill('验证下一步行动');
            await page.locator('#notePersonalInput').fill('验证个人补充');
            await page.locator('#noteSave').click();
            const title = await cards.first().locator('.personal-note-title').textContent();
            if (title !== '验证笔记标题') errors.push('❌ 笔记编辑保存异常');
            await page.locator('#noteSearch').fill('下一步行动');
            if (await page.locator('#notesList .personal-note-card:visible').count() !== 1) errors.push('❌ 笔记搜索异常');
            await page.locator('#noteSearch').fill('不存在的验证关键词');
            if (await page.locator('#notesList .personal-note-card:visible').count() !== 0) errors.push('❌ 笔记搜索未隐藏不匹配内容');
            await page.locator('#noteSearch').fill('');
          }
          const storedCount = await page.evaluate(() => {
            try {
              const key = Object.keys(localStorage).find(item => item.indexOf('knowledge-learning-assistant-notes:v1:') === 0);
              return key ? JSON.parse(localStorage.getItem(key) || '[]').length : -1;
            } catch (error) { return -2; }
          });
          if (storedCount === 0 || storedCount === -1) errors.push('❌ 笔记没有写入浏览器本地存储');
          console.log('✅ 我的笔记 — 可一键保存、去重、编辑、搜索并本地持久化');
        }
      }
    }

    // 12. 验证移动端断点（检查 viewport 变化时页面不崩溃）
    await page.setViewportSize({ width: 500, height: 800 });
    await page.waitForTimeout(200);
    const overflows = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
    if (overflows) errors.push('❌ 500px 移动端出现横向溢出');
    await page.setViewportSize({ width: 1280, height: 900 });
    console.log('✅ 移动端响应式断点 — 无崩溃');

    // 13. 检查 data-source 属性
    const srcElements = await page.locator('[data-source]').count();
    if (srcElements > 0) {
      console.log(`📎 出处标注: ${srcElements} 个元素有 data-source 属性`);
    } else {
      console.log('⚠️  无 data-source 属性 — 如非 overview 模式，需检查');
    }

  } catch (e) {
    errors.push('❌ 测试异常: ' + e.message);
  }

  // 结果汇总
  console.log('\n' + '='.repeat(40));
  if (errors.length === 0) {
    console.log('✅ 全部验证通过');
  } else {
    console.log(`❌ ${errors.length} 个错误:`);
    errors.forEach(e => console.log('  ' + e));
  }
  console.log('='.repeat(40));

  await context.close();
  await browser.close();
  process.exit(errors.length > 0 ? 1 : 0);
})();
