# PDF 原文标题索引与出处核验

新系统学习 PDF 在写学习页前建立 `<topic>.learnkb/source-heading-index.json`。目录、正文首页和未编号部分都要核对；自动提取器报告的 `chapters_detected` 只是线索，不能据此补造章号。对长 PDF 可逐章建索引，但交付前必须覆盖页面、方法卡和方法论实际引用的所有标题路径。

```json
{
  "schemaVersion": "learn-from-materials/source-heading-index-v1",
  "entries": [
    {
      "filename": "paper.pdf",
      "path": "第四章 结果",
      "pdfStart": 50,
      "pdfEnd": 70,
      "evidencePage": 50,
      "evidenceText": "第四章 结果",
      "verification": "text"
    },
    {
      "filename": "paper.pdf",
      "path": "第四章 结果 > 4.2 反应",
      "pdfStart": 56,
      "pdfEnd": 64,
      "evidencePage": 56,
      "evidenceText": "4.2 反应",
      "verification": "text"
    },
    {
      "filename": "paper.pdf",
      "path": "第四章 结果 > 4.2 反应 > 4.2.4 金属辅助反应",
      "pdfStart": 61,
      "pdfEnd": 63,
      "evidencePage": 61,
      "evidenceText": "4.2.4 金属辅助反应",
      "verification": "text"
    },
    {
      "filename": "paper.pdf",
      "path": "总结与展望",
      "pdfStart": 72,
      "pdfEnd": 74,
      "evidencePage": 72,
      "evidenceText": "总结与展望",
      "verification": "text"
    }
  ]
}
```

- `path` 必须与页面 `标题路径：` 后展示的文字完全一致，包含原文存在的编号与标题；无编号标题保持无编号。书籍章节引文可直接使用该路径作为章节/部分标签。
- 用 ` > ` 表示原文父子层级，每个父级都必须有自己的索引条目和原文证据；不能只验证末级标题，却在路径前面补一个未证实的“第六章”。
- `pdfStart/pdfEnd` 是该标题覆盖的物理 PDF 页。父级标题可以覆盖子级页段；跨多个同级章节的总结需引用共同父级，或者拆成多个精确出处，不把某一小节扩写成整章出处。
- `evidencePage/evidenceText` 是标题出现在原文的页码与短原文。`verification: text` 会检查该片段确实出现在此页提取文本中，并包含路径末级标题。OCR 文本也应先人工复核。文字提取不到标题时可以用 `verification: visual`，同时填写具体的 `reviewNote`，并在交付说明中标明这是人工视觉核验，不能声称程序验证了原文文字。
- 原标题不确定时先复查目录和正文。仍不能确定则在页面明确写“标题待核”，不得猜测章号、标题或页码；这类未核出处不能通过新系统学习 PDF 的最终门禁。

从核定索引复制出处标签到 `page.json`、`methods.json`、`methodology.json` 和总结账本；不要在每张卡片中重拟一个相似标题。更新旧页面时重核旧出处和派生的 `patterns.md`、`methodology.md`，而不只是检查新内容。

验证：

```bash
python scripts/verify_coverage.py page.json --knowledge-base topic.learnkb --require-heading-index
```

这项机器门禁检查索引证据文字、PDF 物理页、页面展示标题与索引路径的一致性。它不能判断每个科学论断是否由该页支持；完成程序检查后仍须抽查论断对应的原文段落。交付报告分别列出结构/页码检查、标题检查与内容依据复核的结果。
