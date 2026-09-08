# 知识学习助手内容契约 4.2

模型只生成 UTF-8 JSON；不得手写 HTML、CSS 或 JavaScript。渲染器负责固定模块顺序、主题、交互、转义和移动端布局。本契约同时适用于书籍、PPT/PPTX、Word、PDF、网页、Markdown、文本和多材料集合。

## overview 必需字段

深度分支：下文的全量穷举、系统质量档案、预建题库、coverage audit 与双向总结账本仅适用于 `systematic`。`quick` 遵循 `quick-workflow.md`，仍使用同一 JSON 字段、来源格式、六大模块与交互。快速模式只收录必要术语和核心考点，能力不强制凑齐四类；无材料支持的行动规则可用空数组，界面显示说明。主题/单元快速页同样采用快速出处核查。字段类型与其他真实性要求不变。

```json
{
  "schemaVersion": "4.2",
  "meta": {
    "title": "材料名称或学习专题",
    "creator": "作者、讲者、机构或未注明",
    "sourceType": "slides",
    "mode": "overview",
    "pageId": "stable-material-id",
    "learningDepth": "systematic",
    "initialTheme": "warm-paper",
    "knowledgeBase": "专题名.learnkb/INDEX.md"
  },
  "hero": {
    "eyebrow": "材料名称 · 学习页",
    "title": "一句学习者能懂的标题",
    "lede": "这份材料解决什么问题",
    "thesis": "一句话总论"
  },
  "frameworks": [
    {"name":"框架名","oneLine":"准确含义","when":"使用场景","firstUnitId":"u01","sourceOrder":1,"source":"第8页幻灯片"}
  ],
  "contentUnits": [
    {
      "id":"u01","label":"第1–5页","title":"单元标题","core":"核心思想",
      "frameworks":["框架A"],"takeaways":["要点A"],
      "conclusions":[
        {
          "title":"分点结论",
          "summary":"一句话说明整体含义",
          "points":["具体解释一","具体解释二"],
          "source":"第3–5页幻灯片"
        }
      ],
      "source":"第1–5页幻灯片"
    }
  ],
  "glossary": [
    {
      "id":"crm",
      "term":"CRM",
      "fullName":"Customer Relationship Management",
      "zhMeaning":"客户关系管理",
      "category":"英文缩写",
      "definition":"给初学者的准确、简明定义",
      "context":"该词在材料中的具体用法和作用",
      "related":["客户关系管理","销售流程"],
      "units":["u01"],
      "firstUnitId":"u01",
      "sourceOrder":1,
      "source":"第4页幻灯片"
    }
  ],
  "decisionRules": [
    {"when":"出现X","do":"执行Y","because":"原因Z","source":"第12页幻灯片"}
  ],
  "assessment": {
    "focusAreas": [
      {
        "id":"focus-01",
        "title":"可测知识点或判断点",
        "unitId":"u01",
        "abilities":["记忆","解释","应用","迁移"],
        "source":"第8–12页幻灯片"
      }
    ]
  },
  "footer": "可选页面脚注；省略时由渲染器自动生成"
}
```

数量规则：`frameworks`、`glossary`、`decisionRules`、`assessment.focusAreas` 和每个单元的 `conclusions` **均不设置数量上限、配额或“达到下限即可结束”的完成线**。按材料可提炼的独立信息单元完整收录：框架收录所有可改变判断或行动的命名结构及必要的描述性结构；术语收录所有理解材料所必需的术语、角色、流程、指标和英文缩写；行动规则收录全部条件—行动—原因关系；自检考点覆盖全部关键框架、概念区分、判断点、图表解读和案例教训。`focusAreas` 只定义可测范围与能力层级，不预生成题干、提示或答案。仅合并语义完全等价的重复项，不得以条目已经很多为由省略独立内容。所有 overview 数组至少包含一项有效内容，内容单元、术语与自检考点必须覆盖完整材料，不得只处理开头。

上一段数量规则仅适用于 `systematic`；`quick` 以主线、关键条件、必要术语和核心考点为边界，`decisionRules` 可为空，其余核心模块至少有一项。

允许的 `sourceType`：`book`、`slides`、`document`、`web`、`text`、`mixed`。书籍按章节划分；PPT 按连续幻灯片或主题组划分；Word/PDF 按标题层级划分；多材料集合按主题而不是文件数量机械划分。

允许的 overview 顶层字段仅限上述字段。不要添加控制布局、颜色或 JavaScript 的字段。“我的笔记”不是 JSON 字段，模型不得把个人笔记混入静态材料内容。

`meta` 固定包含 `title/creator/sourceType/mode/pageId/learningDepth/initialTheme/knowledgeBase`；`hero` 固定包含 `eyebrow/title/lede/thesis`。`learningDepth` 只能为 `quick` 或 `systematic`，规则见 `learning-depth-modes.md`。`pageId` 是同一学习项目跨重新生成保持不变的稳定标识，用于续用浏览器中的职业、兴趣、笔记和错题；它与所有 `id` 一样，必须以英文字母开头，只能使用英文字母、数字、`-`、`_`。其他所有字段均为非空文本。

学习深度只在解析与内容生成前询问。职业和兴趣不进入 `page.json`，仍由最终 HTML 在首次打开后询问，并仅保存在浏览器本地。

`frameworks` 与 `glossary` 的每项必须包含 `firstUnitId` 和 `sourceOrder`。`firstUnitId` 指向该内容在材料中第一次被实质介绍的内容单元；`sourceOrder` 在各自数组内从 1 开始连续编号。渲染器只按 `sourceOrder` 排列，不按分类、字母或模型输出顺序重排。框架顺序必须与各 `contentUnits[].frameworks` 的首次引入顺序一致；术语顺序必须按首次出现单元递增，同单元内按实际出现位置排列。多材料先按 `source_manifest.json` 文件顺序，再按文件内部定位确定首次出现。

## 内容单元规则

`contentUnits` 是对不同材料结构的统一抽象：

- 书籍：一章或一个有独立论证目标的章节组；
- PPT：一组围绕同一主题的连续幻灯片；
- Word/PDF：一个标题分区或逻辑部分；
- 多材料：跨文件聚合的同一知识主题。

每个单元保留材料原有顺序，写明核心思想、关键框架、行动要点、全部具有独立论证价值的可展开结论和独立出处。结论组与分点不设置数量上限；按材料论证块完整展开，只有材料确实没有更多独立内容时才自然结束。不要把幻灯片页数、文件名或标题层级伪装成知识结论。

## 系统学习的材料类型全量覆盖规则

先根据 `meta.sourceType` 完整读取相应质量档案：`book` 读取 `book-quality-profile.md`；`slides/document/web/text/mixed` 读取 `material-quality-profile.md`。所有类型共同遵守“无数量上限 + 结构账本 + coverage audit”门禁。

### 书籍（`book`）

- `contentUnits` 按作者正文章节或独立论证章节组建立，按论证顺序排列；不得只处理目录、前几章或热门章节；前言、结语、附录含关键方法时也必须纳入；
- 每个章节单元的 `conclusions` 优先展开作者明确命名的框架、阶段、分类或维度；每组包含概括性 `summary`、完整必要的 `points` 和该组独立 `source`；
- 长书必须逐章或逐论证单元切片处理，材料不足时如实说明；禁止用模型常识凑字数，也禁止用重复改写冒充详细；
- 作者原意、页面改写和模型推导必须在正文中可区分；作者命名框架优先保留原名；
- `coverage-audit.md` 逐章记录覆盖范围、已提炼内容与事实性缺口。

### 演示材料（`slides`）

- 覆盖全部幻灯片，包括封面、目录、分隔页、正文、总结页和附录页；无可提炼事实的页面也在 `coverage-audit.md` 标明结构作用或无内容原因；
- 按连续主题和论证推进组织 `contentUnits`，不以每页数量限制或只抽取标题；
- 对影响结论的图表、流程图、图片文字、数据标注逐项视觉核验；不可核验项必须记录边界；
- 术语、框架、规则和自检考点从所有页面（含图表/备注可得内容）完整汇总，不设条数上限。

### 文档（`document`）

- 覆盖全部标题层级、正文论证、表格、图表、公式、代码块、案例框、脚注和附录；
- 按标题路径与论证目标组织单元，保留页码、段落、表图号；
- 文字提取不完整或扫描/OCR不确定处必须在 coverage audit 中说明，不能凭常识补写。

### 网页（`web`）

- 覆盖页面标题、H1–H6、正文、折叠内容、图表、表格、引用、脚注和更新时间；不得只读首屏或搜索摘要；
- 长页面切片读取到末尾；动态/受限/不可见内容在 coverage audit 中标出；
- 来源写页面标题 + 小节 + 段落/图表定位（可得时）。

### 文本（`text`）

- 覆盖 Markdown 标题、纯文本逻辑块、编号结构、代码块、表格、引用块与段落主题；
- 无标题材料按主题连续性分块并记录起止行/字符范围；
- 代码/命令/配置只解释材料已有的作用、前提与边界。

### 多材料（`mixed`）

- 先覆盖每一份文件，再按跨文件主题聚合；不得把文件边界抹成“综合资料”；
- 保留支持、补充、冲突、版本差异和重复关系；不可擅自合并不同材料的立场或数据；
- 每份文件均在 coverage audit 中标为已覆盖、无内容、重复或不可读取，并写明事实性原因。

系统学习中，所有类型的 `frameworks`、`glossary`、`decisionRules` 和 `assessment.focusAreas` 必须按全部可提炼的独立内容完整覆盖；禁止使用“达到若干条”作为停止条件。快速了解按 `quick-workflow.md` 提炼主线内容。

## 术语大全规则

系统学习完整读取 `glossary.md`、各单元 Key Concepts、材料命名框架、英文缩写和专业角色/流程，再去重；快速了解只收录理解核心导读必需的术语。固定分类只能从以下 5 项选择：`英文缩写`、`领域术语`、`方法框架`、`角色与流程`、`指标与工具`。

- 英文缩写必须提供 `fullName` 英文全称；
- 凡 `term` 含英文字母，必须提供 `zhMeaning` 中文含义，并在折叠栏未展开时直接显示；
- `definition` 准确解释“是什么”，不要为了通俗牺牲概念边界；
- `context` 只写材料怎样使用该词；材料外知识不能冒充材料语境；
- `related` 至少 1 项；`units` 至少关联一个有效内容单元；
- 每条术语单独标注真实出处。
- `firstUnitId` 必须是 `units` 中最早的内容单元；`sourceOrder` 按材料首次出现位置连续递增。分类只作为标签，不参与默认排序。

## 学习自检规则

- 静态页面不铺开预生成题目；`assessment.focusAreas` 只记录考点名称、所属单元、需要覆盖的能力层级和真实出处。
- `abilities` 只能使用 `记忆`、`解释`、`应用`、`迁移`，每个考点至少包含一项，并覆盖每个内容单元；系统学习合计覆盖四层能力，快速了解只标记核心考点实际适用的能力。
- 页面由固定渲染器生成“综合全部 / 指定章节或单元 / 自定义要求”三种范围选择，以及题量、难度、能力重点设置。
- AI 出题前按 `question-bank-routing.md` 静默读取知识库内已有的 `question-bank.json`；快速了解没有预建题库时，在用户所选范围内按需检查原题。页面不增加题库识别结果、模式名称、置信度或用户开关。
- 范围内存在可用原题时优先原题；原题不足或不完整时混合生成；没有题库时才依据 `assessment.focusAreas` 动态生成。原题保留题干、选项和官方答案，材料推导答案不得冒充官方答案。
- 复制口令要求 AI 先确认当前对话能访问材料知识库；不可访问时先索要材料，不得凭常识冒充材料出题。
- AI 每次只出一道题，等待用户回答后再判分；不得提前泄露答案。判分、提示、解析和出处均以材料为准，并按回答动态调整难度。
- 测验结束输出总评、薄弱知识点和标准错题 JSON。HTML 只在用户粘贴或导入该记录后写入本地错题本，不声称能自动读取对话。
- 页面固定提示能力要求：基础记忆题和短材料可使用具备文件读取、指令遵循与结构化输出能力的通用模型；长书、多材料、专业论文和复杂开放题建议使用长上下文、高推理能力模型。不得使用特定平台的模型档位作为跨 Agent 前提。

错题 JSON 使用固定结构：

```json
{
  "schemaVersion":"knowledge-learning-assistant-mistakes/v1",
  "materialTitle":"材料名称",
  "knowledgeBase":"专题名.learnkb/INDEX.md",
  "sessionTitle":"本次测验范围",
  "mistakes":[
    {
      "question":"题目",
      "userAnswer":"用户答案",
      "correctAnswer":"材料依据的正确答案",
      "explanation":"错误原因与解析",
      "knowledgePoint":"对应知识点",
      "unit":"对应章节或单元",
      "source":"精确材料出处",
      "status":"未掌握",
      "wrongCount":1
    }
  ]
}
```

AI 在 JSON 前后分别输出 `<<<KLA_MISTAKES_JSON>>>` 与 `<<<END_KLA_MISTAKES_JSON>>>`，方便页面从整段测验总结中提取。`status` 初始为 `未掌握`；无错题时输出空数组。

## 小巴讲解与知识边界

小巴引导由模板固定实现。首次打开说明六类页面交互，再询问职业/主要身份和兴趣爱好；允许跳过。画像仅保存在当前浏览器，并可从工具栏修改。

画像不是首次讲解的默认素材。所有追问必须遵守三级递进：

1. 首次回答先给学术严谨、概念准确、结构清楚的解释，不主动调用画像举例，不主动生成图片；
2. 只有用户明确表示没懂、要求通俗解释或要求举例时，才使用职业或兴趣画像进行类比，同时保留严谨定义；
3. 用户再次表示仍不理解时，才调用可用的图片生成、图片检索或可视化工具，用带标注的示意图、流程图或对比图说明。

材料外问题按“材料依据 → 模型补充 → 外部核验”处理：先查知识库；材料未覆盖时明确说明，再用当前模型知识回答；涉及可能变化的事实或高风险内容时，有联网工具则核验权威来源。禁止伪造材料出处，也禁止把模型补充写回静态材料知识库。完整协议读取 `answer-protocol.md`。

## 我的笔记（运行时模块）

- 每个带出处的内容块提供“☆”一键保存；单击即保存标题、摘录和出处；
- 已保存显示“✓”，重复点击不重复创建；
- 支持编辑、搜索、删除、复制、Markdown 导出、JSON 备份和 JSON 导入；
- 笔记按“材料标题 + knowledgeBase”隔离并保存在当前浏览器；
- 不代表账号记忆、云同步或跨设备自动同步。

## 我的错题（学习自检内的运行时模块）

- 支持粘贴 AI 测验总结中的标准错题记录，也支持 JSON 文件导入与备份；
- 按材料标题与 `knowledgeBase` 隔离并保存在当前浏览器；重复题目按“题目 + 知识点 + 出处”合并并累计错误次数；
- 支持搜索、按掌握状态筛选、修改状态、删除，以及复制单题或筛选结果的变式复测口令；
- 复测口令只提供题目、知识点、单元与出处，不把正确答案提前暴露给用户；
- 不代表账号记忆、云同步或跨设备自动同步。

## topic/unit 模式

保留 `meta`、`hero`，增加 `sections`。`topic` 模式的 `meta` 额外包含非空 `topic`；`unit` 模式额外包含非空 `unit`。

每个分区固定包含 `id/label/title/lead/signature`，可选 `notes`。可用 signature：`causal_chain`、`type_selector`、`matrix`、`timeline`、`decision_tree`、`questions`、`story_card`、`before_after`、`accordion`、`quote_card`。具体字段读取 `templates/components.md`；所有可见内容块必须包含 `source`。

渲染器按固定顺序排序：`quote_card → causal_chain → timeline → before_after → type_selector → matrix → accordion → story_card → decision_tree → questions`。`label` 不要自带序号。

## 出处规则

优先读取 `source_map.json`：

- **书籍 PDF（强制章节+页码）**：`第N章《章节标题》 · 原书第N–M页 · PDF第X–Y页`；若无法确认原书印刷页码，可写 `第N章《章节标题》 · PDF第X–Y页`。不得只写页数、只写章号或省略章节标题。
- **书籍 EPUB / DOCX（强制章节+实际定位）**：`第N章《章节标题》 · EPUB第N节`，或 `第N章《章节标题》 · 标题路径：… · 第N段`；若有页码映射，必须一并写出。
- **书籍前言、序言、结语、后记、附录（强制具体部分+页码/定位）**：`前言《标题》 · 原书第N页 · PDF第X页`、`附录《标题》 · …`。
- **PPT/PPTX/PPTM（强制文件名+页码+标题）**：`文件名 · 第N页幻灯片《页面标题》`；范围：`文件名 · 第N–M页幻灯片《主题/页面标题》`。不得只写“第 N 页”或只写文件名。
- **PDF/Word/RTF 文档（强制文件名+标题路径+定位）**：`文件名 · 标题路径：一级标题 > 二级标题 · PDF第N–M页`；无标题时：`文件名 · 第N段/表N/图N · PDF第N页`。
- **网页（强制页面标题+小节）**：`页面标题 · 小节《……》 · 段落N`；有锚点、图表或更新时间时尽量追加。
- **Markdown/文本（强制文件名+行段）**：`文件名 · 标题《……》 · 第N–M行`；无标题时：`文件名 · 第N–M行`。
- **多材料（强制逐文件定位）**：`文件A · …；文件B · …`。不得用“多份材料”“综合资料”替代逐文件来源。

同一条内容若依据多处，使用分号完整列出每个材料的名称 + 内部定位；只有映射确实不完整时才使用“约”。

材料原话只少量引用并明确标识；页面改写、模型推导、模型补充和外部检索必须彼此区分。

## 系统学习 coverage audit 规则

在 `<主题>.learnkb/coverage-audit.md` 建立可查看的范围审计，并按 `coverage-audit-schema.md` 同步生成 `coverage-audit.json`。Markdown 至少包含：

- 全部文件、页/幻灯片/标题/小节/行段的范围与提取质量；
- 每个范围对应的学习单元、已提炼框架/术语/规则/自检考点/案例/表图结论；
- 无可提炼内容、真实重复、不可读取、OCR/视觉未核验等范围的事实性原因；
- 多材料的支持、补充、冲突与版本差异；
- 最终结论：确认没有因条目数量、篇幅、材料位置或易读性而提前停止。

生成 HTML 前必须运行 `scripts/verify_coverage.py page.json --knowledge-base <主题>.learnkb`。校验器会把 manifest、source map、coverage audit 与 page JSON 交叉核验；不得只凭字段合法性宣称完整覆盖。

## 系统学习内容总结双向覆盖规则

系统学习 overview 生成前必须完整读取 `summary-coverage-schema.md`，在知识库生成 `summary-ledger.json`。快速了解使用 `quick-audit.json` 核对实际展示内容。系统学习第一遍按材料顺序提取所有必须进入总结的独立主张、定义、机制、结论、案例、证据、数据、限制与方法；第二遍把每个原子主张映射到 `contentUnits` 中的核心思想、关键框架、行动要点、结论摘要或结论分点，并反向确认每个页面总结项都至少有一条材料主张支撑。

以下任一情况必须阻止渲染并回到知识库补全：存在未映射主张、存在无材料主张支撑的总结项、第二遍复核未完成、排除项没有事实性原因。该审计只作为内部生成门禁，不在 HTML 增加可见模块。

## 严格字段规则

- 根对象、`meta`、`hero`、section 及所有内容项都拒绝未知字段；
- `contentUnits.id`、`glossary.id`、`sections.id` 及组件内部 ID 各自在所在数组中唯一；
- 所有规定的文本数组必须非空；
- 同一份有效 JSON 无论对象键顺序或 section 输入顺序如何，渲染器都输出稳定结构。
- `frameworks.sourceOrder` 与 `glossary.sourceOrder` 必须各自唯一、连续，并符合材料首次出现顺序。
