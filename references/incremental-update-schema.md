# 增量知识库更新契约

增量更新只在用户提供已有 `.learnkb` 与新增、修改或删除后的材料集合时启用。它复用未变化的来源块和知识单元，但不允许用缓存掩盖失效出处。

## 初次构建必须生成的依赖表

知识库根目录生成 `unit-dependency-map.json`：

```json
{
  "schemaVersion": "learn-from-materials/unit-dependency-map-v1",
  "pageId": "material-project-01",
  "entries": [
    {
      "sourceKey": "教材.pdf#pdf_page:18",
      "contentHash": "64位SHA-256",
      "unitIds": ["u04"],
      "claimIds": ["claim-021"],
      "derivedRefs": ["framework:f03", "term:t17", "assessment:a09"]
    }
  ]
}
```

`sourceKey` 由文件名、定位类型和页/幻灯片/章节序号组成，在文件内容变化但定位未变化时保持稳定。每个 `source_map.json` 来源块恰好对应一个依赖条目；系统学习模式不得遗漏。快速模式允许没有知识映射的块，但仍需条目并将三个映射数组留空。

## 更新步骤

1. 将新材料提取到独立 staging 目录，不覆盖旧知识库。
2. 运行 `scripts/plan_incremental_update.py` 比较旧 manifest、旧/新 source map 和依赖表，生成 `incremental-update-plan.json`。
3. 如果计划中 `requiresFullRebuild=true`，如实说明缺少可靠依赖证据并执行全量重建；不得假装进行了语义增量更新。
4. 否则只读取新增/变化来源块、受影响旧单元及其直接依赖。未影响的 `units/*.md` 必须逐字节复用。
5. 删除来源时，清除或重新支撑依赖该来源的主张、术语、框架、规则和自检考点。
6. 从全部新旧单元重新汇总全局索引；汇总可由脚本完成的部分不得重新交给模型改写。
7. 保持 `pageId` 和未受影响单元 ID 不变。生成新的知识库目录与新的完整 HTML，不直接覆盖旧成果。
8. 依次执行覆盖校验、反向覆盖、静态页面验证和 `scripts/validate_incremental_update.py`；全部通过后才交付更新版。

## 计划语义

- `unchangedSources`：文件文字哈希未变，提取及内容可复用。
- `addedSources`：新出现文件；其来源块进入新增分析范围。
- `modifiedSources`：同名文件的文字哈希变化；按 `sourceKey + contentHash` 继续缩小到变化块。
- `deletedSources`：旧 manifest 存在但新集合不存在；反向依赖全部进入失效检查。
- `impactedUnitIds`：变化或删除块在旧依赖表中指向的单元。
- `newSourceKeys`、`changedSourceKeys`、`deletedSourceKeys`：模型允许读取和处理的来源范围。

模型不得重新改写 `impactedUnitIds` 之外的旧单元。新增材料确实改变全局核心框架时，可把额外单元加入计划，但必须在 `manualExpansions` 中记录具体原因。
