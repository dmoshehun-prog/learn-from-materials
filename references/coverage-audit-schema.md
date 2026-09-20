# 全量覆盖审计机器契约 1.1

同时生成面向读者的 `coverage-audit.md` 和供程序校验的 `coverage-audit.json`。两者必须记录同一批文件与覆盖结论；不得只写 Markdown 后跳过机器校验。

## 必需结构

```json
{
  "schemaVersion": "1.1",
  "learningDepth": "systematic",
  "sources": [
    {
      "filename": "课程.pdf",
      "status": "covered",
      "reason": "逐页读取并进入 u01-u05",
      "unitIds": ["u01", "u02", "u03", "u04", "u05"],
      "ranges": [
        {"kind": "pdf_page", "start": 1, "end": 42}
      ]
    },
    {
      "filename": "封面说明.txt",
      "status": "no-content",
      "reason": "仅含版权声明，无可提炼学习事实",
      "unitIds": [],
      "ranges": []
    }
  ],
  "sourceBlocks": [
    {
      "sourceId": "src-a1b2c3d4e5f6-pdf_page-00001",
      "status": "covered",
      "mappedUnits": ["u01"],
      "mappedClaims": ["claim-001", "claim-002"]
    }
  ],
  "finalCheck": {
    "readToEnd": true,
    "noEarlyStop": true,
    "sourceLocatorsChecked": true
  }
}
```

## 字段规则

- `filename`：必须与 `source_manifest.json.sources[].filename` 完全一致，且每个文件恰好出现一次。
- 文件级 `status`：只能是 `covered`、`no-content`、`unreadable`、`duplicate`。
- `learningDepth`：必须与 `page.json.meta.learningDepth` 一致。`systematic` 表示系统学习，`quick` 表示快速了解。
- `reason`：必须填写事实性原因，不能只写“已处理”。
- `unitIds`：`covered` 文件必须关联至少一个知识单元；其他状态可为空。
- `ranges`：
  - PDF 使用 `{"kind":"pdf_page","start":1,"end":N}`；
  - PPT/PPTX/PPTM 使用 `{"kind":"slide","start":1,"end":N}`；
  - EPUB 使用 `{"kind":"epub_section","start":1,"end":N}`，顺序必须来自 OPF spine；
  - 多个不连续范围拆成多项；
  - 文本、网页、DOCX 等没有稳定物理页映射时，可使用 `{"kind":"document","start":1,"end":1}`，并在 Markdown 审计中列出标题/段落边界。
- `finalCheck` 三项必须全部为 `true`，分别确认顺序读到末尾、未因篇幅或条目数提前停止、页面出处已经对照 `source_map.json`。
- `sourceBlocks`：必须逐项覆盖 `source_map.json[].source_id`。标记为 `covered` 时，`mappedUnits` 或 `mappedClaims` 至少一项非空；无学习内容的块使用 `no-content` 并保留事实性理由。快速了解模式可以把已扫描但未进入核心学习页的次要来源块标为 `quick-omitted`；系统学习模式禁止使用该状态。禁止用一个笼统文件级条目代替逐来源块映射。

完成 `coverage-audit.json` 后生成反向抽查报告：

```bash
python3 scripts/audit_reverse_coverage.py \
  --source-map <主题>.learnkb/source_map.json \
  --coverage-audit <主题>.learnkb/coverage-audit.json \
  --output <主题>.learnkb/reverse-coverage-report.json
```

脚本会从原材料定位块反向寻找内容单元与主张映射，并分别报告未映射比例和快速模式下的主动省略比例。未映射块不为零时必须修复或以 `no-content`/`duplicate` 给出事实性处理结论；`quick-omitted` 必须在页面上明确告知读者，不能伪装成全量覆盖。

## 强制校验

生成 `page.json` 后、渲染 HTML 前运行：

```bash
python3 scripts/verify_coverage.py page.json \
  --knowledge-base <主题>.learnkb
```

校验器会检查：

1. 知识库必需文件及 `units/*.md` 是否存在；
2. manifest 中每个文件是否同时出现在 Markdown/JSON 审计中；
3. PDF 页或幻灯片范围是否覆盖 `source_map.json` 中的全部真实定位；
4. mixed 页面是否实际引用每个标为 `covered` 的文件；
5. 页面中的 PDF/幻灯片页码是否超出真实映射；
6. 没有物理页边界的 PDF 是否被错误标成精确页码。
7. `question-bank.json` 是否存在、结构有效，检测到的题目是否有唯一 ID、可靠判分依据、内容单元映射和精确出处。
8. `summary-ledger.json` 是否完成“材料关键主张 → 页面总结”和“页面总结 → 材料关键主张”的双向映射；任何遗漏主张、孤立总结、跨单元错配或未完成二次复核都会阻止渲染。
9. 增强 manifest 的文件哈希、文本哈希、逐来源块哈希、反向覆盖报告、安全扫描报告和性能报告是否齐全。
10. 对新系统学习 PDF，使用 `--require-heading-index` 检查 `source-heading-index.json` 中核对过的原文标题路径、标题证据页及展示出处的页码归属。章节编号与标题必须一致；未编号部分不得补造章号。详见 `source-heading-index.md`。

任何错误都必须回到提取、结构账本或知识库修复，不得跳过校验或手改 HTML。
