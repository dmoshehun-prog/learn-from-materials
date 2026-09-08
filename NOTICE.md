# 开源来源与二次开发说明

`learn-from-materials` 在以下 MIT 开源项目基础上进行二次开发与扩展。

## book-to-skill

- 项目：`book-to-skill`
- 原作者：virgiliojr94
- 原仓库：https://github.com/virgiliojr94/book-to-skill
- 原始许可：MIT License，完整文本见 `LICENSE.md`

本项目沿用了其部分材料提取、依赖回退、知识拆解与基础知识库结构。

## book-to-webpage

- 项目：`book-to-webpage`
- 维护者：crayon-ai
- 原仓库：https://github.com/crayon-ai/book-to-webpage
- 原始许可：MIT License

本项目的交互式单文件学习页面、主题切换、出处展示及内容块追问等设计，
参考并改写自 `book-to-webpage`。

## learn-from-materials 的新增与重构

本项目进一步扩展并重构了面向完整学习流程的产品与工程能力，包括：

- “快速了解 / 系统学习”双深度流程及各自质量门禁
- PDF、PPT/PPTM、文档、网页和多材料的细粒度来源映射与视觉复核边界
- 材料依据、材料未覆盖、模型补充与外部核验的分层协议
- 覆盖审计、反向覆盖抽查与总结双向映射
- 固定内容 JSON 契约、确定性渲染器与静态/浏览器验证
- “小巴”渐进讲解、交互术语、动态自检、原题优先和错题变式复测
- 浏览器本地笔记、画像、错题与稳定 `pageId`
- 来源哈希、安全报告、性能报告和语义增量更新
- 面向开放 Agent Skills 规范的跨 Agent 兼容说明

上游项目代码及其派生部分继续遵循各自的 MIT License。新增内容的贡献者可在
不影响原始版权与许可声明的前提下另行声明其修改部分的著作权。上游作者和
维护者不为本项目的扩展、修改或发布背书。

本仓库新增与修改内容按同一 MIT License 发布，具体贡献者以 Git 提交历史为准。
根目录 `assets/icon.svg` 为本仓库原创的简化书本图形，不使用第三方商标。
