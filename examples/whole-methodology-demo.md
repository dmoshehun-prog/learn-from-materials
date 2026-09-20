# AI 如何真正学会改进自己？

**学习深度：** 系统学习

从闭环部件、五级自主性，到行业反馈制度与可信演化，顺序读懂这篇 RSI 论文的论证与边界。

**一句话总论：** RSI 的关键不是‘AI 会改自己’，而是改进机制能否被验证地继承。

## 核心框架

### 改进闭环审计

用循环部件判断一项改进是否能被验证地继承。

适用：分析任何声称会自我改进的系统时。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：2.2.1 Anatomy of an Improvement Loop · PDF第10页

### 五级自主性阶梯

按改进责任由谁承担，将系统定位在 L1–L5。

适用：需要比较提示、训练、经验、部署或元改进系统时。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：1 Introduction · PDF第5页

### HCI 能力余量闭合指数

把知识、推理、工具与代理协作的差距看作闭环尚未关闭的证据。

适用：解释为何基准高分仍不等于 RSI 时。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：2 Headroom-Closed Index · PDF第7–9页

### L1/L2 的任务与策略优化

区分执行预定改进与在外部目标下选择改进策略。

适用：定位提示、训练或代理搜索属于哪一层时。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.2 L1 / 3.3 L2 · PDF第12–21页

### 学习议程自主

检查系统是否根据学习者状态选择下一步经验。

适用：分析课程生成、自博弈、任务生成或自主练习时。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.4 L3: Autonomy over Future Learning Experience · PDF第22页

### 轨迹蒸馏与部署适应

将部署轨迹转化为可验证、可保留、可退役的记忆、技能或工具。

适用：设计持久经验库与上线闭环时。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5 L4 · PDF第27–31页

### 元改进评估

区分改进机制被修改的结构性 L5 与被独立证据支持的有效 L5。

适用：评估自动研究、改优化器、改评估器或后继生成机制时。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.6 L5: From Environmental Adaptation to Meta-Improvement · PDF第32页

### 领域反馈制度

按反馈成本、延迟、可验证性和风险决定可安全关闭的循环。

适用：在科学、具身、软件、医疗间迁移 RSI 方案时。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：4 Domain-Specific RSI · PDF第36–37页

### 产业闭环实践

把行业实践还原为环境、数据、模型、评估与部署接口，而非营销标签。

适用：阅读或设计企业级 RSI 项目时。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：5 Industry Practices · PDF第37–46页

### RSI 长期议程

以诊断、持久状态、可信演化、长期评估和基础设施组织未来工作。

适用：制定研究或产品路线图时。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：6 Future Directions · PDF第46–49页

### 文献与场景分类

以层级、改进对象和证据标签组织文献与行业条目。

适用：做系统综述或避免过度归类时。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：Appendix A–C · PDF第63–79页

## 内容导学

### 01 RSI 的问题、定义与边界

递归自我改进不是一次性能变强，而是把经验与反馈转成可持续的系统状态变化，使后续改进的能力或机制也随之提升。

关键框架：改进闭环审计、五级自主性阶梯

- 先区分任务输出与可继承系统状态；没有后者通常只是单次优化。
- 判断一个系统是否接近 RSI，要同时问：闭环在哪里、更新什么、什么仍由外部承担。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：Abstract / 1 Introduction · PDF第1–6页

#### 定义比拟人化叙事更重要

论文把 RSI 放进‘自主、继承、验证’的闭环，而非把任何自动调参都叫自我改进。

- 系统要从经验中识别局限、提出并验证改进。
- 被采纳的变化必须影响后续学习或改进过程。
- 安全继承、归因与验证可靠性是早期风险。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：Abstract / 1 Introduction · PDF第1–6页

### 02 现有能力到 RSI 的距离

HCI 用多个能力与工具维度的观察说明：模型在知识题上可强，在持续工具使用、软件任务和代理协作上仍存在明显闭环缺口。

关键框架：改进闭环审计、HCI 能力余量闭合指数

- 不要用单项基准分数替代改进闭环能力的判断。
- 把‘能答对’与‘能可靠地产生、验证并保留改进’分开衡量。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：2 Headroom-Closed Index / 2.2.1 Anatomy of an Improvement Loop · PDF第7–12页

#### 能力不均衡决定闭环短板

研究的要点不是一个总分，而是能力、工具与环境接口并不同步成熟。

- 知识与推理表现并不自动推出长期工具自主。
- 缺少可靠环境、反馈和状态管理时，高分也难形成 RSI。
- 后文的闭环部件可用来定位缺口而非笼统称为‘能力不足’。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：2 Headroom-Closed Index / 2.2.1 Anatomy of an Improvement Loop · PDF第7–12页

### 03 从 B0 到 L2：执行与策略

B0 只改当次输出；L1 执行外部指定的改进；L2 开始由系统诊断问题并选择干预策略，但目标和验证仍主要外置。

关键框架：五级自主性阶梯、L1/L2 的任务与策略优化

- 先给系统定位层级，避免把提示词搜索或训练搜索直接夸大为完全自改。
- L2 的关键不是自动运行，而是能在外部目标下选择改进策略。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.2 L1 / 3.3 L2 · PDF第12–21页

#### 层级上升改变的是责任边界

L1 到 L2 的变化是从‘执行已规定方案’到‘在给定目标下选择方案’，不是简单增加更多工具。

- L1 的主要风险是执行可靠性与持久化安全。
- L2 容易出现基准过拟合、评估盲区和搜索成本膨胀。
- 外部评估仍决定系统是否真的变好。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.2 L1 / 3.3 L2 · PDF第12–21页

### 04 L3：学习议程自主

L3 的定义性变化是：系统基于当前学习者状态决定下一步需要什么经验，而不是只在固定数据或任务上换策略。

关键框架：五级自主性阶梯、学习议程自主

- 分别评估经验的正确性、难度和学习收益，三者不能互相替代。
- 把课程、环境、对手或任务生成纳入闭环时，要防经验污染与目标漂移。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.4 L3 · PDF第22–26页

#### 经验选择是新的自主性门槛

自适应课程、对抗生成、自博弈和自主练习都说明‘下一条经验由谁决定’会改变改进边界。

- 系统需要条件化地选择未来经验。
- 经验不仅要可得，还要对当前系统有学习价值。
- 错误或偏置经验会被持久闭环放大。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.4 L3 · PDF第22–26页

### 05 L4：部署适应与轨迹蒸馏

L4 把部署后的观察转化为可选择、可回滚、可复验的持久状态；轨迹蒸馏是把过程经验压缩为记忆、技能或可执行工具的一类机制。

关键框架：五级自主性阶梯、轨迹蒸馏与部署适应

- 把采纳门槛、证据日志、版本上限、重验证和淘汰规则写进状态库。
- 部署数据不是天然经验；要区分可保留的因果证据与短期噪声。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5 L4 · PDF第27–31页

#### 持久化让改进变成治理问题

当系统会保留并复用经验，关键问题从‘能否更新’转为‘什么证据允许进入、何时重验、如何退出’。

- 状态可表现为文本记忆、结构化记忆、程序化技能或工具。
- 论文以配对对照说明部署变化必须比较更新前后。
- Library Drift 要求证据日志、容量控制、再验证和退役。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5 L4 · PDF第27–31页

### 06 L5：改进改进机制

L5 不只改任务能力，还修改改进器、评估器或搜索策略；论文区分结构性 L5 与有效性 L5，后者还必须证明元层更新确实带来收益。

关键框架：五级自主性阶梯、元改进评估

- 先审计更新的是任务对象还是改进机制，再谈 L5。
- 对元改进同时检查适应性、留存、迁移、效率、稳定性和元递归证据。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.6 L5 / 3.7 Cross-Level Synthesis · PDF第31–35页

#### ‘会改优化器’不等于已经证明元递归

结构存在只能说明可能性；有效 L5 需要跨轮、可比较的实证证据。

- 自指或自动代码修改本身不足以证明长期收益。
- 评估器也在闭环内时，要防 Goodhart 式钻空子。
- 层级更高不保证质量更高。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.6 L5 / 3.7 Cross-Level Synthesis · PDF第31–35页

### 07 四类应用场景的反馈制度

科学发现、具身智能、软件工程和医疗健康的差异，首先来自反馈是否便宜、可重复、可验证和可安全部署，而不是来自统一的‘智能程度’。

关键框架：领域反馈制度

- 先选择与场景匹配的 RSI 层级，而不是追求最高层级。
- 真实世界成本、监督要求和评估延迟会决定哪些闭环可以安全关闭。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：4 Domain-Specific RSI · PDF第36–37页

#### 场景决定可达层级

论文将不同领域放在反馈制度下比较：软件反馈较快，科学与具身场景更昂贵，医疗还受高风险治理约束。

- 科学的强项在可验证发现与早期经验选择。
- 具身系统受物理试验代价和安全限制。
- 医疗适合成熟 L2 与受限 L3，真实 L4/L5仍需谨慎。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：4 Domain-Specific RSI · PDF第36–37页

### 08 行业案例：闭环而非宣传语

产业案例展示环境、数据、模型、评估与部署的不同组合；它们是实践线索，不能自动当作通用或独立复现的 RSI 证据。

关键框架：产业闭环实践

- 阅读公司报告时标注是作者报告、行业案例还是可重复研究，不混为一谈。
- 用闭环部件表核查：状态、经验、改进器、验证器和后继系统是否明确。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：5 Industry Practices · PDF第37–46页

#### 案例价值在于暴露工程接口

这些案例把环境重建、企业数据、人类评审、记忆管理与部署闭环等工程问题具体化。

- Theseus 强调环境—数据—模型协同。
- Lark、IMA、Humanlaya等案例将企业数据、评估或质量系统纳入循环。
- 论文列出的业务指标应按其报告性质理解，不应外推为普适因果结论。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：5 Industry Practices · PDF第37–46页

### 09 走向可信 RSI 的研究议程

论文提出八类后续能力：跨组件诊断、学习者条件化信号、持久状态管理、领域反馈治理、可信演化机制、长期评估、资源与人类协同、可复现实验基础设施。

关键框架：RSI 长期议程

- 把长期收益、迁移和稳定性纳入实验设计，别只比较单次开发集结果。
- 把人类参与视为可设计的监督接口，而非‘没有自主性’的反例。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：6 Future Directions / 7 Conclusion · PDF第46–49页

#### 可信演化需要基础设施

研究挑战不止模型结构，还包括可重现实验环境、长期可观测性与资源受限条件下的治理。

- 跨组件诊断帮助定位闭环瓶颈。
- 长期评估用于区别短期适配与可继承改进。
- 人类协作可在高风险领域提供边界与校验。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：6 Future Directions / 7 Conclusion · PDF第46–49页

### 10 附录：文献与行业分类法

附录的 491 篇论文与行业表是分类基础：它记录目前不同层级、改进对象和实践标签的分布，不是对每个条目的能力背书。

关键框架：文献与场景分类

- 把 taxonomy 当作检索和比较工具，保留条目的层级、对象与证据标签。
- 对‘adjacent’、‘candidate’等标签保留不确定性，而不是强行归入 RSI。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：Appendix A / Appendix B · PDF第63–71页

#### 分类法服务于可审计比较

层级分布和产业清单为后续复核提供索引；它们同时显示高层级证据仍相对稀少。

- 论文给出 L1–L5 的文献分布。
- 改进对象横跨模型、提示、环境、工具、记忆与系统结构。
- 行业表使用谨慎标签区分相邻、候选与目标实践。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：Appendix A / Appendix B · PDF第63–71页

### 11 附录：按场景回看完整闭环

科学、具身、软件和医疗的补充案例把系统对象、经验、改进器、验证器和持久状态逐项展开，强调真实世界闭环仍受验证与安全约束。

关键框架：文献与场景分类

- 将同一闭环审计表应用到不同领域，观察缺失部件而非只比较模型名称。
- 当真实世界验证不可逆或成本高时，明确保留外部监督与模拟边界。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：Appendix C · PDF第72–79页

#### 完整闭环在现实中通常仍不完整

附录说明许多系统在模拟、软件或局部子环中有效，但安全的端到端真实世界自改仍未被充分证明。

- 科学系统依赖可验证的假设与实验接口。
- 具身系统的真实试验受到安全和成本限制。
- 软件可执行反馈较强，医疗则需要更严格监督。
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：Appendix C · PDF第72–79页

## 术语大全

### RSI｜Recursive Self-Improvement

分类：英文缩写
中文含义：递归自我改进
通俗定义：把经验与反馈转成可持续状态变化，并使后续改进能力或机制提升的闭环。
材料语境：论文的总定义，强调自主、继承与验证。
相关术语：改进闭环、L5
涉及单元：01·RSI 的问题、定义与边界、06·L5：改进改进机制
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：Abstract / 1 Introduction · PDF第1–6页

### 改进闭环

分类：角色与流程
通俗定义：由系统状态、经验、目标、改进器、验证器、改进和后继系统组成的分析框架。
材料语境：用于拆解一个系统到底在哪里关闭改进回路。
相关术语：RSI、验证器
涉及单元：01·RSI 的问题、定义与边界、02·现有能力到 RSI 的距离、08·行业案例：闭环而非宣传语、11·附录：按场景回看完整闭环
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：1 Introduction / 2.2.1 Anatomy · PDF第3–12页

### HCI｜Headroom-Closed Index

分类：英文缩写
中文含义：余量闭合指数
通俗定义：比较系统距人类可闭合能力的观察性指数，用于呈现不同能力维度的剩余缺口。
材料语境：论文用它展示知识、工具与代理能力的不均衡。
相关术语：改进闭环
涉及单元：02·现有能力到 RSI 的距离
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：2 Headroom-Closed Index · PDF第7–9页

### L1｜Improvement Execution Autonomy

分类：英文缩写
中文含义：改进执行自主性
通俗定义：人类或外部方规定改什么、怎么改和何时成功，系统执行候选更新。
材料语境：自主性主要在执行，不在选择目标或策略。
相关术语：L2、五级自主性阶梯
涉及单元：03·从 B0 到 L2：执行与策略
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.2 L1 · PDF第12–18页

### L2｜Improvement Strategy Autonomy

分类：英文缩写
中文含义：改进策略自主性
通俗定义：外部目标与评估保留，但系统诊断问题并选择干预策略。
材料语境：提示搜索、训练搜索和代理/评测 harness 是主要例子。
相关术语：L1、L3
涉及单元：03·从 B0 到 L2：执行与策略
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.3 L2 · PDF第18–21页

### L3｜Experience Acquisition Autonomy

分类：英文缩写
中文含义：经验获取自主性
通俗定义：系统根据当前学习状态选择下一步该获得什么经验。
材料语境：课程、自博弈与自主练习的层级关键。
相关术语：L2、L4
涉及单元：04·L3：学习议程自主
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.4 L3 · PDF第22–26页

### Trajectory Distillation｜Trajectory Distillation

分类：方法框架
中文含义：轨迹蒸馏
通俗定义：把交互或任务轨迹提炼为可复用的记忆、技能、程序或工具。
材料语境：L4 中将部署经验转为持久状态的代表机制。
相关术语：L4、部署适应
涉及单元：05·L4：部署适应与轨迹蒸馏
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5 L4 · PDF第27–31页

### L4｜Deployment and Environment-Adaptation Autonomy

分类：英文缩写
中文含义：部署与环境适应自主性
通俗定义：系统在部署中获取反馈，选择性保留、更新或退役状态。
材料语境：使改进跨出离线训练并进入持续运行。
相关术语：Trajectory Distillation、L5
涉及单元：05·L4：部署适应与轨迹蒸馏
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5 L4 · PDF第27–31页

### L5｜Meta-Improvement Autonomy

分类：英文缩写
中文含义：元改进自主性
通俗定义：系统改变产生、选择或验证未来改进的机制本身。
材料语境：论文区分结构性与有效性 L5。
相关术语：RSI、元改进评估
涉及单元：06·L5：改进改进机制
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.6 L5 · PDF第31–35页

### 反馈制度

分类：领域术语
通俗定义：由反馈成本、延迟、保真度、可验证性与治理约束共同决定的场景条件。
材料语境：解释同一层级在不同领域可不可行。
相关术语：领域反馈制度
涉及单元：07·四类应用场景的反馈制度、11·附录：按场景回看完整闭环
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：4 Domain-Specific RSI · PDF第36–37页

### Theseus｜Theseus

分类：指标与工具
中文含义：行业案例中的环境—数据—模型协同实践
通俗定义：论文列举的产业案例，用来说明环境与数据质量会影响闭环效果。
材料语境：属于论文中的行业实践线索。
相关术语：产业闭环实践
涉及单元：08·行业案例：闭环而非宣传语
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：5.1 Theseus · PDF第37–40页

### 长期评估

分类：指标与工具
通俗定义：跨轮次检查适应、留存、迁移、效率与稳定性的评估，而非只看单次分数。
材料语境：用于区分短期调优和可继承改进。
相关术语：L5、可信演化
涉及单元：09·走向可信 RSI 的研究议程
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：6 Future Directions · PDF第46–49页

### 自主性分类法

分类：方法框架
通俗定义：以层级与改进对象整理研究和行业案例的分类框架。
材料语境：附录用它展示文献与场景分布。
相关术语：五级自主性阶梯
涉及单元：10·附录：文献与行业分类法
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：Appendix A / B · PDF第63–71页

### 具身闭环

分类：领域术语
通俗定义：涉及物理环境、感知—行动反馈与安全约束的持续改进循环。
材料语境：附录比较具身系统与软件系统的验证边界。
相关术语：反馈制度
涉及单元：11·附录：按场景回看完整闭环
出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：Appendix C · PDF第72–79页

## 行动规则

- 当 看到任何‘自我改进’系统时。 → 先用闭环部件和 L1–L5 标出它实际承担的责任边界。；因为 自动执行、策略选择、经验获取、部署适应和元改进是不同主张。。（The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：1 Introduction / 2.2.1 Anatomy · PDF第5–12页）
- 当 系统能反复选择策略、查询开发集或调用自动评估器时。 → 隔离并保护评估接口；因为 论文指出重复访问开发集会诱发基准过拟合，评估器还可能与提议者共享盲区。。（The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.3.4 Evaluating L2 Strategy Autonomy · PDF第21页）
- 当 系统开始自动选数据、任务、对手或环境时。 → 分别记录经验正确性、难度与学习收益，并保留来源。；因为 经验选择是 L3 的定义性能力，也会传播污染。。（The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.4 L3 · PDF第22–26页）
- 当 准备把记忆、技能、工具、代码或规则纳入长期库时。 → 证据门控的持久化；因为 论文在 L4 的选择性保留部分明确提出：候选更新要先产生证据才可进入持久状态。。（The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5.3 Selective retention and deployment of updates · PDF第30页）
- 当 有人宣称系统达到了 L5 或元递归时。 → 同时报告改了什么机制，以及跨轮适应、留存、迁移、效率和稳定性证据。；因为 有自指结构不等于元层更新有效。。（The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.6 L5 · PDF第31–35页）
- 当 要把方法迁移到新的行业或物理场景时。 → 先评估反馈成本、延迟、可验证性、安全性与人工监督需要，再定层级。；因为 场景反馈制度限制了能安全关闭的循环。。（The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：4 Domain-Specific RSI · PDF第36–37页）
- 当 设计 RSI 研究或产品路线图时。 → 把长期评估、可复现实验环境、资源约束和人类协作纳入同一计划。；因为 可信演化需要的不只是更强模型。。（The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：6 Future Directions · PDF第46–49页）

## 学习自检

HTML 页面不会平铺固定题目。请选择综合全部、指定章节或自定义要求，复制口令到材料对话中，由 AI 基于知识库逐题测验。测验结束后可将标准错题记录导回 HTML 的本地错题本。

### 自检考点

- **RSI 的问题、定义与边界：概念、边界与迁移**｜01·RSI 的问题、定义与边界｜能力：记忆, 解释｜出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：Abstract / 1 Introduction · PDF第1–6页
- **现有能力到 RSI 的距离：概念、边界与迁移**｜02·现有能力到 RSI 的距离｜能力：解释, 应用｜出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：2 Headroom-Closed Index / 2.2.1 Anatomy of an Improvement Loop · PDF第7–12页
- **从 B0 到 L2：执行与策略：概念、边界与迁移**｜03·从 B0 到 L2：执行与策略｜能力：记忆, 应用｜出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.2 L1 / 3.3 L2 · PDF第12–21页
- **L3：学习议程自主：概念、边界与迁移**｜04·L3：学习议程自主｜能力：解释, 迁移｜出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.4 L3 · PDF第22–26页
- **L4：部署适应与轨迹蒸馏：概念、边界与迁移**｜05·L4：部署适应与轨迹蒸馏｜能力：应用, 迁移｜出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5 L4 · PDF第27–31页
- **L5：改进改进机制：概念、边界与迁移**｜06·L5：改进改进机制｜能力：解释, 迁移｜出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.6 L5 / 3.7 Cross-Level Synthesis · PDF第31–35页
- **四类应用场景的反馈制度：概念、边界与迁移**｜07·四类应用场景的反馈制度｜能力：记忆, 应用｜出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：4 Domain-Specific RSI · PDF第36–37页
- **行业案例：闭环而非宣传语：概念、边界与迁移**｜08·行业案例：闭环而非宣传语｜能力：解释, 应用｜出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：5 Industry Practices · PDF第37–46页
- **走向可信 RSI 的研究议程：概念、边界与迁移**｜09·走向可信 RSI 的研究议程｜能力：解释, 迁移｜出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：6 Future Directions / 7 Conclusion · PDF第46–49页
- **附录：文献与行业分类法：概念、边界与迁移**｜10·附录：文献与行业分类法｜能力：记忆, 解释｜出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：Appendix A / Appendix B · PDF第63–71页
- **附录：按场景回看完整闭环：概念、边界与迁移**｜11·附录：按场景回看完整闭环｜能力：应用, 迁移｜出处：The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：Appendix C · PDF第72–79页

错题只保存在 HTML 所在浏览器的本地存储中；请定期导出 JSON 备份。

## 我的笔记

个人笔记保存在 HTML 所在浏览器的本地存储中，不写入这份静态 Markdown。可在网页中导出 Markdown，或用 JSON 备份和迁移。

## 页面说明

基于论文文本层系统整理；行业案例与数值按论文报告性质呈现，页面不把它们外推为独立复现结论。

## 逻辑关系

- 改进闭环审计 → 五级自主性阶梯 (prerequisite; 材料依据)
  先识别闭环部件，才能判断哪些责任由系统承担并定位层级。
  出处: The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：1 Introduction / 2.2.1 Anatomy · PDF第5–12页

- 五级自主性阶梯 → 学习议程自主 (sequence; 材料依据)
  L3 在阶梯上接在 L1/L2之后，把自主性推进到未来经验选择。
  出处: The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.4 L3 · PDF第22–26页

- 学习议程自主 → 轨迹蒸馏与部署适应 (sequence; 材料依据)
  经验获取之后，L4 关注部署反馈如何沉淀为持久状态。
  出处: The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5 L4 · PDF第27–31页

- 轨迹蒸馏与部署适应 → 元改进评估 (sequence; 材料依据)
  L5 在 L4 之后进一步修改产生或验证改进的机制。
  出处: The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.6 L5 · PDF第31–35页

- HCI 能力余量闭合指数 → 先用闭环部件和 L1–L5 标出它实际承担的责任边界。 (supports; 辅助理解的推断)
  能力余量观察为给系统定位闭环短板提供证据。
  出处: The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：2 Headroom-Closed Index / 2.2.1 Anatomy · PDF第7–12页

- L1/L2 的任务与策略优化 → 隔离并保护评估接口 (causes; 材料依据)
  一旦系统能搜索策略，反复访问评估接口就带来过拟合与盲区风险。
  出处: The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.3 L2 · PDF第18–21页

- 元改进评估 → 隔离并保护评估接口 (supports; 材料依据)
  元改进需要更强的评估完整性，防止评估器也被优化目标劫持。
  出处: The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.6 L5 · PDF第31–35页

- 领域反馈制度 → 先用闭环部件和 L1–L5 标出它实际承担的责任边界。 (applies; 材料依据)
  同一系统在不同领域的层级判断需结合该领域反馈制度。
  出处: The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：4 Domain-Specific RSI · PDF第36–37页

- 产业闭环实践 → 证据门控的持久化 (supports; 辅助理解的推断)
  产业实践让数据、记忆、质量系统和部署状态的保留问题具象化。
  出处: The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：5 Industry Practices · PDF第37–46页

- RSI 长期议程 → 把长期评估、可复现实验环境、资源约束和人类协作纳入同一计划。 (part_of; 材料依据)
  长期评估、基础设施、资源与协作正是论文未来议程中的组成部分。
  出处: The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：6 Future Directions · PDF第46–49页

- 文献与场景分类 → 先用闭环部件和 L1–L5 标出它实际承担的责任边界。 (supports; 材料依据)
  附录分类法为审计系统属于相邻、候选或目标实践提供共同语言。
  出处: The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：Appendix A / B · PDF第63–71页

# 从问题诊断到可继承改进

依据论文全文整合的应用方法论；流程及其连接属于分析性整合，并非作者原文提出的固定步骤。虚线表示整合推断，点击节点查看条件、证据与来源。

目标：形成有验收证据、可继承、可复查的改进闭环。

## 明确目标与边界

证据类型：inference

输入: 待改进的问题与使用场景

行动 / 关系含义: 明确结果、预算、允许修改的对象和验收权限。

产出: 目标、资源与验收标准

检查: 目标可评估，改动不越过既定权限。

The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：1.4 Autonomy Levels · PDF第5页

## 拆解改进闭环

证据类型：inference

输入: 目标与现有系统

行动 / 关系含义: 列出状态、经验、改进器、验证器与下一轮继承的内容。

产出: 系统闭环与责任分工

检查: 区分一次输出和跨轮保留的状态。

The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：2.2.1 Anatomy of an Improvement Loop · PDF第10页

## 定位瓶颈与层级

证据类型：inference

输入: 闭环记录与失败证据

行动 / 关系含义: 判断短板在执行、策略、经验、部署还是改进机制；结合领域反馈条件。

产出: 当前短板与自主性边界

检查: 判断针对具体机制，并记录不确定性。

The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：1.4 Autonomy Levels · PDF第5页

## 选择改进方式

证据类型：inference

输入: 瓶颈、证据与资源约束

行动 / 关系含义: 选择与瓶颈相符的干预；不要把更高层级自动当作更优方案。

产出: 干预方案与可检查假设

检查: 说明为什么该干预可能改善已识别短板。

The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：1.4 Autonomy Levels · PDF第5页

## 获取经验并提出更新

证据类型：inference

输入: 干预方案与学习者状态

行动 / 关系含义: 获取适用经验，提出候选更新并记录来源；需要 L3 时由学习者状态决定下一批经验。

产出: 候选方案与来源证据

检查: 经验有适用性；候选仍可撤回。

The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.4 L3: Autonomy over Future Learning Experience · PDF第22页

## 验证真实收益

证据类型：inference

输入: 候选更新与受保护的评估条件

行动 / 关系含义: 检查独立表现、预算、迁移与稳定性；区分增加搜索成本与机制进步。

产出: 通过或未通过的验证证据

检查: 未达到验收要求不入库；成本或风险超限则停止。

The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.3.4 Evaluating L2 Strategy Autonomy · PDF第21页

## 保留并复用改进

证据类型：inference

输入: 通过验证的候选与支持证据

行动 / 关系含义: 连同版本、证据、适用条件保存；安排重验证与退役。

产出: 可追溯且可退役的持久状态

检查: 只有验证支持的更新被保留。

The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5.3 Selective retention and deployment of updates · PDF第30页

## 观察后续表现

证据类型：inference

输入: 后续任务中的实际调用与效果

行动 / 关系含义: 检查更新能否被调用、正确执行和持续受益，记录新失败与漂移。

产出: 实际收益、失效信号与新瓶颈

检查: 达到目标且收益稳定可停止；新问题回到诊断。

The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5 L4 · PDF第31页

## 改进“改进机制”本身

证据类型：inference

输入: 反复失败且指向改进机制的证据

行动 / 关系含义: 检查搜索策略、验证方式或经验获取流程，提出机制修订并验证后继效果。

产出: 待验证、可继承的机制修订

检查: 机制确实被后继复用；结构性变化与有效性分别验证。

The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.6 L5: From Environmental Adaptation to Meta-Improvement · PDF第32页

- 明确目标与边界 → 拆解改进闭环 (main; inference)
  目标与边界已明确
  目标、资源与验收标准
  先明确验收边界，才能界定要审计的系统。
  The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：2.2.1 Anatomy of an Improvement Loop · PDF第10页

- 拆解改进闭环 → 定位瓶颈与层级 (main; inference)
  闭环部件可识别
  系统闭环与责任分工
  借助闭环部件定位失效位置。
  The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：1.4 Autonomy Levels · PDF第5页

- 定位瓶颈与层级 → 选择改进方式 (main; inference)
  瓶颈有初步证据
  当前短板与自主性边界
  干预方式应对应已识别的短板。
  The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：1.4 Autonomy Levels · PDF第5页

- 选择改进方式 → 获取经验并提出更新 (main; inference)
  方案具备可验证假设
  干预方案与可检查假设
  用方案决定获取什么经验以及提出什么更新。
  The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.4 L3: Autonomy over Future Learning Experience · PDF第22页

- 获取经验并提出更新 → 验证真实收益 (main; inference)
  候选准备就绪
  候选方案与来源证据
  候选必须接受验证才能判断收益。
  The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.3.4 Evaluating L2 Strategy Autonomy · PDF第21页

- 验证真实收益 → 保留并复用改进 (main; inference)
  验证通过
  通过或未通过的验证证据
  证据决定候选是否可进入持久状态。
  The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5.3 Selective retention and deployment of updates · PDF第30页

- 保留并复用改进 → 观察后续表现 (main; inference)
  更新已部署或可复用
  可追溯且可退役的持久状态
  入库并不保证后续任务真正获益。
  The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5 L4 · PDF第31页

- 验证真实收益 → 选择改进方式 (feedback; inference)
  未通过：修正方案
  失败记录、成本与验证结果
  失败证据用于改变干预；不要重复同一无效候选。
  The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5 L4 / 3.6 L5 · PDF第30–35页

- 观察后续表现 → 定位瓶颈与层级 (feedback; inference)
  新问题：重新诊断
  后续失败、遗忘或调用失效证据
  部署改变状态，新短板需要重新定位。
  The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5 L4 / 3.6 L5 · PDF第30–35页

- 观察后续表现 → 改进“改进机制”本身 (branch; inference)
  持续停滞且指向改进机制
  跨轮停滞与机制失效证据
  只有证据指向改进过程时，才考虑修改该过程；并非所有问题都需要 L5。
  The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5 L4 / 3.6 L5 · PDF第30–35页

- 改进“改进机制”本身 → 选择改进方式 (feedback; inference)
  机制修订：重新设计与验证
  修订后的搜索或验证机制
  修订机制需进入后续候选生成与验证，而非凭自修改直接宣布有效。
  The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.5 L4 / 3.6 L5 · PDF第30–35页

## 全程约束

受保护的评估 — The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.6 L5 · PDF第31–35页
证据与版本记录 — The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.6 L5 · PDF第31–35页
资源预算 — The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.6 L5 · PDF第31–35页
人工权限与场景风险 — The-Last-AI-Built-by-Humans-arXiv-2609.11873v2.pdf · 标题路径：3.6 L5 · PDF第31–35页
