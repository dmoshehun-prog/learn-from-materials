# 主题页组件字段

本文件只说明 `page.json` 的内容字段。不要复制 HTML、CSS 或 JavaScript；`scripts/render_page.py` 统一渲染交互和样式。

每个 `topic` 或 `unit` 页面都包含：`meta`、`hero`、`sections`。每个 section 固定包含：

```json
{
  "id": "stable-id",
  "label": "Tab短名",
  "title": "分区标题",
  "lead": "段首引导",
  "signature": "组件名",
  "notes": [
    {"title":"要点标题","body":"解释","source":"第三章 · PDF第40-43页"}
  ]
}
```

`notes` 可省略。`id` 以英文字母开头，只能含英文字母、数字、`-`、`_`，并在 `sections` 中唯一。`label` 不写数字序号。以下字段按照 `signature` 添加；不要添加未列出的字段。

## causal_chain

用于因果或步骤推进，至少 3 项。

```json
"chain": [
  {"id":"cause","label":"起点","body":"解释","source":"第一章 · PDF第10-12页"}
]
```

## type_selector

用于并列类型，至少 2 项。

```json
"options": [
  {"id":"type-a","label":"类型A","title":"标题","body":"解释","watch":"判断重点","source":"第二章 · PDF第20-24页"}
]
```

## matrix

用于多维权衡。每行 `scores` 数量必须等于 `dimensions` 数量。

```json
"dimensions": ["成本", "速度"],
"rows": [
  {"option":"方案A","scores":["低","快"],"source":"第三章 · PDF第30-34页"}
]
```

## timeline

用于历史或阶段演进。

```json
"events": [
  {"time":"阶段一","title":"事件","body":"变化及意义","source":"第四章 · PDF第40-44页"}
]
```

## decision_tree

用于条件分叉。

```json
"branches": [
  {"question":"如果出现X？","reasoning":"选择与原因","source":"第五章 · PDF第50-53页"}
]
```

## questions

用于行动检查或读者自检。

```json
"questions": [
  {"title":"自检问题","hint":"回答方向","source":"第六章 · PDF第60-62页"}
]
```

## story_card

用于材料中的具体案例，不自行编造。

```json
"stories": [
  {"label":"材料案例","title":"案例标题","body":"经过","insight":"案例揭示的规律","source":"第七章 · PDF第70-75页"}
]
```

## before_after

用于同一事物前后对比。

```json
"before": {"label":"之前","title":"旧状态","body":"解释","source":"第八章 · PDF第80-82页"},
"after": {"label":"之后","title":"新状态","body":"解释","source":"第八章 · PDF第83-86页"}
```

## accordion

用于先给结论、再展开论证。

```json
"items": [
  {"title":"结论","body":"详细论证","source":"第九章 · PDF第90-95页"}
]
```

## quote_card

用于少量材料原话，必须准确且注明归属。

```json
"quote": {
  "text":"短引用",
  "attribution":"材料原话",
  "source":"第十章 · PDF第100页"
}
```

## 选择规则

| 内容结构 | signature |
|---|---|
| 因果或步骤 | `causal_chain` |
| 并列类别 | `type_selector` |
| 多维比较 | `matrix` |
| 时间演进 | `timeline` |
| 条件分叉 | `decision_tree` |
| 行动检查 | `questions` |
| 具体案例 | `story_card` |
| 前后变化 | `before_after` |
| 分层论证 | `accordion` |
| 精确原话 | `quote_card` |

每个主题页按材料实际论证结构使用 section，不设置预设数量上限。根据内容主要结构选择组件，不为展示组件而拆散叙事。所有可见内容块必须有 `source`；当 `sourceType=book` 时，每个出处必须写成“具体章节名称 · 原书页码（如可得） · PDF/EPUB 实际定位”。

## 固定渲染顺序

输入数组顺序不会决定页面顺序。渲染器固定按以下次序排列：`quote_card` → `causal_chain` → `timeline` → `before_after` → `type_selector` → `matrix` → `accordion` → `story_card` → `decision_tree` → `questions`。同一种 signature 重复时按 section `id` 排序。

`causal_chain.chain[].id` 与 `type_selector.options[].id` 必须在各自 section 内唯一，并遵循相同的 ID 字符规则。HTML 与同步 Markdown 使用完全相同的 section 顺序；Markdown 会保留每个 signature 的全部内容和出处。
