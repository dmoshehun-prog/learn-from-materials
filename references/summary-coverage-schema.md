# 内容总结双向覆盖契约

只对 `overview` 页面强制执行。目标是降低“材料已经读完，但关键内容没有进入内容总结”的风险。审计保存在知识库内，不新增 HTML 模块。

## 文件结构

生成 `<主题>.learnkb/summary-ledger.json`：

```json
{
  "schemaVersion": "knowledge-learning-assistant-summary-ledger/v1",
  "claims": [
    {
      "id": "claim-u01-001",
      "unitId": "u01",
      "sourceOrder": 1,
      "kind": "argument",
      "text": "材料中的独立关键主张",
      "source": "材料名 · 精确定位",
      "summaryRefs": [
        "unit:u01:core",
        "unit:u01:conclusion:0:summary",
        "unit:u01:conclusion:0:point:0"
      ]
    }
  ],
  "exclusions": [
    {
      "source": "材料名 · 精确定位",
      "reason": "仅为封面或重复目录，不含独立学习事实"
    }
  ],
  "finalCheck": {
    "sourceToSummaryComplete": true,
    "summaryToSourceComplete": true,
    "secondPassCompleted": true,
    "missingClaimIds": [],
    "orphanSummaryRefs": []
  }
}
```

## 主张提取

第一遍按材料顺序提取全部具有独立学习价值的原子主张，不设数量上限。`sourceOrder` 从 1 开始连续编号；`kind` 只能为：`argument`、`definition`、`mechanism`、`conclusion`、`case`、`evidence`、`data`、`limitation`、`method`、`other`。

必须纳入作者明确结论、框架步骤、概念边界、因果机制、实验或调研结果、关键数据、图表结论、案例教训、适用条件、限制、反例与行动方法。封面、目录、纯版式页、版权声明和完全重复内容可进入 `exclusions`，但必须给出可核验原因。

## 总结引用

`summaryRefs` 只能引用当前 `page.json` 中真实存在的内容总结项：

- `unit:<unitId>:core`
- `unit:<unitId>:framework:<index>`
- `unit:<unitId>:takeaway:<index>`
- `unit:<unitId>:conclusion:<index>:summary`
- `unit:<unitId>:conclusion:<index>:point:<index>`

索引从 0 开始。一个材料主张可映射多个总结项；多个材料主张也可共同支撑一个总结项。不得把只有术语表、行动规则或自检考点中的出现视为已经进入“内容总结”。

## 双向门禁

1. 正向：每条 `claims` 都必须至少映射一个有效 `summaryRef`，否则视为内容总结缺失。
2. 反向：页面中每个 core、关键框架、行动要点、结论摘要和结论分点都必须被至少一条 claim 支撑，否则视为无依据总结。
3. 第二遍必须重新按原材料顺序核对，不得只检查字段数量或沿用第一次提取结论。
4. `missingClaimIds` 与 `orphanSummaryRefs` 必须为空，三个布尔检查必须全部为 `true`。
5. 任一门禁失败时回到知识库或 `page.json` 修正，禁止渲染最终 HTML。

该门禁能显著降低遗漏，但不能把模型判断包装成数学上的百分之百完整保证；未能读取或视觉核验的范围仍须在 coverage audit 中如实标明。
