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
