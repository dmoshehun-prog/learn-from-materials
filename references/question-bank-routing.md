# 静默题库识别与出题路由

## 一、目标

在不增加页面模块、模式开关或识别提示的前提下，判断用户材料是否包含可用于测验的原题。优先利用用户提供的题库；题库不足时补充生成题；没有题库时完全依据自检考点动态出题。

## 二、内部索引

每次建立知识库都生成 `<主题>.learnkb/question-bank.json`。未检测到题库时使用：

```json
{
  "schemaVersion": "knowledge-learning-assistant-question-bank/v1",
  "detection": "none",
  "confidence": "high",
  "sources": [],
  "questions": []
}
```

检测到题目时使用：

```json
{
  "schemaVersion": "knowledge-learning-assistant-question-bank/v1",
  "detection": "complete",
  "confidence": "high",
  "sources": [
    {
      "filename": "模拟题.pdf",
      "kind": "mock-exam",
      "source": "模拟题.pdf · PDF第1–20页"
    }
  ],
  "questions": [
    {
      "id": "q001",
      "stem": "原题题干",
      "questionType": "single-choice",
      "options": ["A. 选项一", "B. 选项二"],
      "answer": "A",
      "explanation": "材料中的原解析；没有时留空",
      "answerBasis": "official",
      "unitId": "u01",
      "knowledgePoints": ["知识点"],
      "source": "模拟题.pdf · PDF第3页 · 第1题",
      "usable": true
    }
  ]
}
```

字段规则：

- `detection` 只能为 `none`、`partial`、`complete`；完整题库或成套练习使用 `complete`，零散题目、缺答案题目或仅部分可解析内容使用 `partial`。
- `confidence` 只能为 `low`、`medium`、`high`，表示题库识别置信度，不表示答案正确率。
- `sources[].kind` 只能为 `question-bank`、`chapter-exercises`、`sample-exam`、`mock-exam`、`answer-key`。
- `questionType` 只能为 `single-choice`、`multiple-choice`、`true-false`、`fill-blank`、`short-answer`、`case-analysis`、`other`。
- `answerBasis` 只能为 `official`、`material-derived`、`unavailable`。只有材料明确给出答案时使用 `official`；依据正文推导时使用 `material-derived`；无法可靠判定时使用 `unavailable`。
- `unitId` 必须指向现有内容单元；无法可靠映射时留空字符串，不得猜测。
- `source` 必须精确定位原题。保留原题、选项、答案和解析，不改写为“类似题”。
- `usable` 仅在题干完整、作答要求明确且能够可靠判分时为 `true`。
- 不设置题目数量上限；读取到题库末尾并去除完全重复题，不得抽样代替全量索引。

## 三、识别规则

只在出现可验证的题目结构时判定为题库或练习：题干与选项、题干与作答要求、连续试题编号、答案表、解析区或明确的“练习/测试/模拟题/真题”标题。正文编号列表、案例步骤、目录、检查清单和普通思考提示不能单独作为题库证据。

- 完整题干 + 明确作答形式 + 可定位答案/解析：`usable: true`。
- 完整题干 + 明确作答形式，但无官方答案：只有正文能可靠支持判分时才可标记 `answerBasis: material-derived` 和 `usable: true`。
- 题干残缺、选项缺失、答案无法核验：保留索引但标记 `usable: false`。
- 无可靠题库证据：输出 `detection: "none"`、`confidence: "high"`、空数组，不强行识别。

## 四、静默出题路由

收到学习自检口令后，先确认材料知识库可访问，再在内部执行以下路由，不向用户展示检测过程、识别结果、置信度或“原题/混合/生成”模式名称：

1. 按用户选择的章节、全部内容或自定义要求过滤 `questions`，只使用 `usable: true` 的范围内题目。
2. 有足够原题时优先原题；保持题干、选项和评分依据，不提前泄露答案。可打乱题目顺序和选择题选项顺序，但必须同步答案映射。
3. 原题不足时先用完不重复的原题，再依据同一知识点与能力要求补充生成题。
4. 只有零散题目或低置信度条目时采用混合路由；不得为了“优先题库”使用残缺或不可判分题目。
5. 没有题库或范围内无可用原题时，依据 `assessment.focusAreas` 动态生成。
6. 同一轮不得重复同一道原题。错题复测默认生成变式题，不直接重复原题；用户明确要求重做原题时除外。
7. 原题使用官方答案判分；`material-derived` 答案按正文事实判分并在解析中如实写“依据正文推导”，不得冒充题库官方答案。
8. 无论走哪条路，都一次只出一题、等待回答、按材料解释和给出处，并输出统一错题 JSON。

页面文案和控件保持不变。复制出的口令可包含执行协议，但预览默认折叠；AI 开始时直接出第 1 题，不报告内部路由。
