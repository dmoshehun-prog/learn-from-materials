# 快速了解执行路线

目标：核心导读，非全量知识整理。保留六大模块、主题、笔记、错题和详解按钮，不用缩减事实准确性换速度。

## 处理

1. 使用 `extract.py` 的正常提取、安全检查和来源映射。在同一项目复用原提取目录与指纹缓存；原文未变不重复 OCR。缓存只复用文字提取，不代表模型已完成阅读。扫描件及关键图表仍可能耗时，未核验内容不得写成事实。
2. 扫描完整文件/章节结构，按章节或连续主题组记录 `structure`，覆盖全部来源块。每组阅读足够正文以确认主线、适用条件和重要反例；不能仅凭目录写结论。无法读取的组明确标注 `unreadable`，不编造章节导读。长材料分组读，不逐条穷举主张。
3. 直接生成一次 `page.json`，不先重复写十几个知识索引。每个可读主要章节在内容导学中保留讲什么、核心结论与意义，核心条件与限制写入结论分点。术语仅保留理解页面必需的项；行动规则无依据则留空；自检只列核心考点，不预写题目、不预建 `question-bank.json`。现有有效题库可复用，不写 detection=none 冒充已检查。
4. 同步完成 `quick-audit.json`。对每个展示出处，核对该出处所支撑的全部内容（包含结论条件、数据、单位和限制），记录少量原文证据及来源 ID。证据摘录只用于后台核查，不大段转载到页面。脚本检查结构和摘录存在性，不能替代模型的语义核查。
5. 运行以下命令（提取目录即知识库，保留原文、manifest、map、metadata、安全和性能报告）：

```bash
python3 scripts/prepare_quick.py page.json --knowledge-base <主题>.learnkb
python3 scripts/render_page.py page.json -k <主题>.learnkb -o <材料>-quick.html -m <材料>-quick.md
python3 scripts/verify_static.py <材料>-quick.html
```

`prepare_quick.py` 校验后从同一份 page 数据派生 INDEX 和简要覆盖说明，不生成系统账本。不要为迎合系统检查创建空账本、伪造全量阅读标志。记录实际总耗时与提取耗时，不能把提取性能报告当全流程测速结果。

## quick-audit.json

```json
{
  "schemaVersion": "learn-from-materials/quick-audit-v1",
  "learningDepth": "quick",
  "structure": [
    {"title":"第1章：主题", "sourceIds":["原source_map中的ID"], "status":"scanned", "note":"核心正文已核对，次要案例未展开"}
  ],
  "evidence": [
    {"source":"与page.json中的source完全一致", "sourceIds":["原source_map中的ID"], "quote":"对应来源块原文中的短摘录", "checked":true}
  ],
  "limitations": ["核心导读，非全量知识整理；次要论证和案例未逐项展开"]
}
```

structure 按源顺序分组，所有 source_id 恰好出现一次，状态为 scanned/unreadable。扫描记录不声称精读每块。evidence 覆盖 page 中每个不同的 source 字符串，ID 必须来自已扫描范围，短摘录需存在于所指来源原文；checked 只有人工/模型核对支撑关系后才能写 true。共享 source 的多个结论必须全部核对，不只检查摘录。limitations 写具体缺口。改动页面内容后必须重新核查对应 evidence。

## 按需深入与升级

- 详解：按材料名、单元 ID 与出处定位回原文；当前页面只是摘要，不用摘要冒充完整原文。找不到材料则索要，不凭常识补齐。
- 测验：读取 question-bank-routing.md 与回答协议。已有题库未覆盖所选范围时，先查该范围原文中的练习、答案，再遵循原题优先；不为一次章节测验先索引整本书。后续可复用已核对题目，未检查范围不能标为无题库。
- 升级：沿用 pageId 和可复用单元 ID，验证文件指纹后复用原文、页码映射与已核实核心内容；补全详细单元、全量题库和系统审计。首次从快速升级需要补齐依赖表，不能声称已完成语义增量验证。系统模式须通过原有完整门禁。
- 输出文件保留来源材料标识；不把用户画像、笔记、错题写入共享内容数据。
