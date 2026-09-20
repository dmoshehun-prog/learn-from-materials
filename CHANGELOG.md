# 更新日志 / Changelog

## v0.2.0 · 2026-09-20

相对于上一公开版本 `v0.1.0-beta`，本次更新包括：

### 新增能力

- 学习页、讲解、Markdown 和可复制的提问口令可跟随当前请求使用中文或英文；仓库提供独立的英文和中文 README。
- 新增可积累的方法论库：从材料中保存带版本和出处的方法卡，并可在用户指定的材料之间检索、比较。
- 新增整份材料的方法论视图，展示框架、行动规则、前提、分支、对比和反馈；可复制口令，让 AI 结合自己的问题应用整套方法论。学习页本身不会联网调用 AI。
- 核心框架和方法论增加关系图，与原有卡片视图配合使用；连线解释保留出处，支持缩放、查看全图、键盘操作、窄屏阅读和较长文字。

### 出处核验与交付

- 系统学习增加逐单元行动规则账本，并复核两张关系图中实际展示的关系，以便追查规则与连线的来源。
- 系统学习 PDF 增加原文标题索引核验，检查学习页展示的章节路径和页码范围。
- 交付前先在暂存目录验证完整文件包，再发布结果；新增方法论、关系图、出处核验和页面交互的示例与回归检查。

### 兼容性与边界

- 已生成的旧学习页仍可阅读。重新交付使用 v1 账本的旧系统学习知识库时，需使用文档说明的兼容选项，或按新版要求重新复核。
- `v0.2.0` 仍是预稳定版本。结构和出处检查不能代替人工对原文及其解读的复核。

---

Compared with the previous public version, `v0.1.0-beta`:

### Added

- English and Chinese learning pages, explanations, Markdown output, and copyable prompts that follow the language of the current request, plus separate English and Chinese READMEs.
- A reusable method library with versioned, source-linked method cards that users can search and compare across selected materials.
- A whole-material methodology view for frameworks, action rules, prerequisites, branches, comparisons, and feedback. Readers can copy a prompt to apply the methodology to their own problem; the page does not call an AI service.
- Framework and methodology relationship maps alongside the existing cards, with source-linked explanations, zoom and overview controls, keyboard support, and layouts for narrow screens and long labels.

### Verification and delivery

- Per-unit action-rule ledgers and reviews of the relationships actually shown in both maps for systematic-study deliveries.
- A reviewed index of original headings and page ranges for systematic PDF deliveries.
- Staged validation of the complete delivery bundle before publication, with new examples and regression checks for methods, maps, sources, and page interactions.

### Compatibility

- Existing learning pages remain readable. Re-delivering an older systematic knowledge base with a v1 ledger requires the documented legacy option or a new review under the current rules.
- This remains a pre-stable release. Structural and source checks do not replace human review of the material and its interpretation.
