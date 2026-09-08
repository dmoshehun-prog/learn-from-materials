#!/usr/bin/env python3
"""Dependency-free structural verification for generated learning pages."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from render_page import ordered_sections, validate


THEMES = (
    "warm-paper",
    "minimal",
    "dark",
    "ink-wash",
    "vintage-editorial",
    "paper-ink",
)
SOURCE_CLASSES = {
    "note", "story", "question", "timeline-item", "ba-col", "quote",
    "explain", "term-item", "ch-view",
    "matrix-option", "result", "acc-item", "rule-item", "chapter-conclusion",
}


class Inspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.tabs: list[str] = []
        self.panel_ids: list[str] = []
        self.themes: list[str] = []
        self.source_targets = 0
        self.source_marked = 0
        self.scripts: list[str] = []
        self._script_type = ""
        self._script_buffer: list[str] | None = None
        self.page_data_text = ""
        self.body_mode = ""

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = {key: value or "" for key, value in attrs_list}
        classes = set(attrs.get("class", "").split())
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "body":
            self.body_mode = attrs.get("data-mode", "")
        if tag == "button" and "tab" in classes:
            self.tabs.append(attrs.get("data-panel", ""))
        if tag == "section" and "panel" in classes:
            self.panel_ids.append(attrs.get("id", ""))
        if tag == "option" and attrs.get("value"):
            self.themes.append(attrs["value"])
        if classes & SOURCE_CLASSES:
            self.source_targets += 1
            if attrs.get("data-source"):
                self.source_marked += 1
        if tag == "script":
            self._script_type = attrs.get("type", "")
            self._script_buffer = []

    def handle_data(self, data: str) -> None:
        if self._script_buffer is not None:
            self._script_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._script_buffer is not None:
            content = "".join(self._script_buffer)
            if self._script_type == "application/json":
                self.page_data_text += content
            else:
                self.scripts.append(content)
            self._script_buffer = None
            self._script_type = ""


def check_javascript(scripts: list[str], errors: list[str], warnings: list[str]) -> None:
    node = shutil.which("node")
    if not node:
        warnings.append("未找到 Node.js，跳过 JavaScript 语法检查")
        return
    code = "\n".join(scripts)
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as temp:
        temp.write(code)
        temp.flush()
        result = subprocess.run([node, "--check", temp.name], capture_output=True, text=True)
    if result.returncode:
        errors.append("JavaScript 语法错误：" + (result.stderr.strip().splitlines()[-1] if result.stderr else "未知错误"))


def verify(path: Path) -> tuple[list[str], list[str], dict]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []
    if re.search(r"\{\{[^{}]+\}\}", text):
        errors.append("存在未替换模板占位符")
    if re.search(r"\b(?:TODO|FIXME|XXX)\b", text):
        errors.append("存在 TODO/FIXME/XXX 残留")

    inspector = Inspector()
    inspector.feed(text)
    duplicate_ids = [item for item, count in Counter(inspector.ids).items() if count > 1]
    if duplicate_ids:
        errors.append("HTML id 重复：" + "、".join(duplicate_ids))
    if not inspector.tabs:
        errors.append("没有学习模块 Tab")
    if any(not panel for panel in inspector.tabs):
        errors.append("Tab 缺少 data-panel")
    if set(inspector.tabs) != set(inspector.panel_ids):
        errors.append("Tab 与 Panel 不能一一对应")
    if set(THEMES) - set(inspector.themes):
        errors.append("主题菜单未包含全部六套主题")
    for theme in THEMES:
        if f'body[data-theme="{theme}"]' not in text:
            errors.append(f"主题 CSS 缺少作用域：{theme}")
    if inspector.source_targets and inspector.source_marked != inspector.source_targets:
        errors.append(f"出处覆盖不足：{inspector.source_marked}/{inspector.source_targets} 个内容块已标注")
    if "@media (hover: none)" not in text:
        errors.append("缺少触屏设备的追问按钮可见性规则")
    if "overflow-y: auto" not in text or "-webkit-overflow-scrolling: touch" not in text:
        errors.append("缺少移动端持续向下滚动规则")
    if inspector.body_mode == "overview":
        if not re.search(r'<article class="ch-view"[^>]*>\s*<div class="ch-view-label">', text):
            errors.append("内容单元首屏正文未预渲染，脚本受限时可能出现空白")
        if 'id="glossarySearch"' not in text or "filterGlossary" not in text:
            errors.append("术语大全缺少搜索功能")
        if 'id="termAskFab"' not in text or "term-ask-fab" not in text:
            errors.append("术语大全缺少右下角 AI 提问入口")
        if ".term-ask-fab" not in text or "position:fixed" not in text.replace(" ", ""):
            errors.append("术语提问按钮没有固定在视口右下角")
        assessment_markers = (
            'id="assessmentCopy"', 'name="assessmentScope"', 'id="assessmentUnit"',
            'id="assessmentCustom"', "buildAssessmentPrompt", "assessmentPromptPreview",
            "每次只出一道题", "KLA_MISTAKES_JSON", "question-bank.json",
            "不要向我报告检测过程", "优先使用原题", "原题不足时",
        )
        missing_assessment_markers = [marker for marker in assessment_markers if marker not in text]
        if missing_assessment_markers:
            errors.append("动态学习自检功能不完整：" + "、".join(missing_assessment_markers))
        mistake_markers = (
            'id="mistakeList"', 'id="mistakeImportText"', "mistakesStorageKey",
            "parseMistakePayload", "mergeMistakes", "renderMistakes", "mistakeRetryPrompt",
            "exportMistakesJson", "importMistakeFile",
        )
        missing_mistake_markers = [marker for marker in mistake_markers if marker not in text]
        if missing_mistake_markers:
            errors.append("本地错题本功能不完整：" + "、".join(missing_mistake_markers))
        if 'class="practice-card"' in text:
            errors.append("学习自检仍把预生成题目平铺在页面上")
    if 'id="notesList"' not in text or 'id="noteOverlay"' not in text:
        errors.append("缺少我的笔记列表或编辑弹窗")
    note_markers = (
        "notesStorageKey", "localStorage", "renderPersonalNotes", "quickSaveNote",
        "captureKey", "exportNotesMarkdown", "exportNotesJson", "importNotesJson", "note-capture-btn",
    )
    missing_note_markers = [marker for marker in note_markers if marker not in text]
    if missing_note_markers:
        errors.append("我的笔记功能不完整：" + "、".join(missing_note_markers))
    if "copyNotePrompt" in text or 'id="noteCopyAi"' in text:
        errors.append("一键笔记仍残留复制粘贴整理流程")
    if 'id="guideOverlay"' not in text or 'id="guideBtn"' not in text:
        errors.append("缺少小巴新手引导或重新打开入口")
    if text.count('class="guide-step"') != 6:
        errors.append("小巴新手引导必须完整说明六类页面交互")
    guide_markers = (
        "makeReaderStorageScope", "readerStorageScope", "readerProfileStorageKey", "readerGuideSeenKey", "readerProfileContext",
        "profileProfession", "profileInterests", "saveReaderProfile",
        "knowledgeSourceProtocol", "progressiveExplanationProtocol", "xiaobaPromptHeader",
    )
    missing_guide_markers = [marker for marker in guide_markers if marker not in text]
    if missing_guide_markers:
        errors.append("小巴画像功能不完整：" + "、".join(missing_guide_markers))
    if 'knowledge-learning-assistant-reader-profile:v1' in text or 'knowledge-learning-assistant-guide-seen:v1' in text:
        errors.append("小巴画像仍使用跨页面共享的 v1 本地存储键")
    if 'knowledge-learning-assistant-reader-profile:v2:" + readerStorageScope' not in text:
        errors.append("小巴画像没有按当前生成页面隔离本地存储")
    if 'knowledge-learning-assistant-guide-seen:v2:" + readerStorageScope' not in text:
        errors.append("小巴首次导读没有按当前生成页面隔离本地存储")
    if "stablePageIdentity" not in text:
        errors.append("页面本地数据没有绑定稳定 pageId，增量更新后可能丢失关联")
    protocol_markers = (
        "[材料依据]", "[材料未覆盖]", "[模型补充]", "[外部核验]",
        "第一层（本次首次回答）", "第二层", "第三层", "不要使用画像举例", "图片生成",
    )
    missing_protocol_markers = [marker for marker in protocol_markers if marker not in text]
    if missing_protocol_markers:
        errors.append("材料知识边界或三级讲解协议不完整：" + "、".join(missing_protocol_markers))

    data: dict = {}
    try:
        data = json.loads(inspector.page_data_text)
    except json.JSONDecodeError as exc:
        errors.append(f"pageData JSON 无法解析：{exc}")
    if data:
        try:
            validate(data)
        except ValueError as exc:
            errors.append(str(exc))
        depth = (data.get("meta") or {}).get("learningDepth")
        if depth == "quick" and ('快速了解模式' not in text or 'id="upgradeDepthCopy"' not in text):
            errors.append("快速了解页面缺少范围提示或系统学习升级入口")
        if depth == "systematic" and "系统学习模式" not in text:
            errors.append("系统学习页面缺少学习深度提示")
        mode = (data.get("meta") or {}).get("mode")
        if mode != inspector.body_mode:
            errors.append("body data-mode 与 pageData.meta.mode 不一致")
        if mode == "overview":
            expected = ["frameworks", "content", "glossary", "rules", "practice", "notes"]
            if inspector.tabs != expected:
                errors.append("overview 模块顺序不符合固定规范")
            if "processPath" in data or "concepts" in data or "conceptRelations" in data:
                errors.append("overview 仍包含已删除的方法路径或概念关系数据")
            if "practice" in data:
                errors.append("overview 仍包含旧版静态 practice 题库")
            if not isinstance(data.get("assessment"), dict) or not data["assessment"].get("focusAreas"):
                errors.append("overview 缺少动态自检考点蓝图")
            framework_orders = [item.get("sourceOrder") for item in data.get("frameworks", [])]
            glossary_orders = [item.get("sourceOrder") for item in data.get("glossary", [])]
            if all(isinstance(item, int) and not isinstance(item, bool) for item in framework_orders) and framework_orders != sorted(framework_orders):
                errors.append("核心框架未按材料首次出现顺序写入页面")
            if all(isinstance(item, int) and not isinstance(item, bool) for item in glossary_orders) and glossary_orders != sorted(glossary_orders):
                errors.append("术语大全未按材料首次出现顺序写入页面")
            if not re.search(r'<details class="term-item"[^>]*data-term-entry', text):
                errors.append("术语大全没有预渲染可展开术语")
            english_terms = [item for item in data.get("glossary", []) if re.search(r"[A-Za-z]", str(item.get("term", "")))]
            if english_terms and text.count('class="term-zh-meaning"') < len(english_terms):
                errors.append("英文术语没有在折叠栏中同时显示中文含义")
        elif mode in {"topic", "unit"}:
            expected = [section.get("id", "") for section in ordered_sections(data.get("sections", []))] + ["notes"]
            if inspector.tabs != expected:
                errors.append(f"{mode} 模块顺序不符合 signature 固定规范")
        if inspector.tabs and inspector.tabs[-1] != "notes":
            errors.append("我的笔记必须是最后一个模块")
    check_javascript(inspector.scripts, errors, warnings)
    return errors, warnings, data


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify generated knowledge learning HTML")
    parser.add_argument("html", type=Path)
    args = parser.parse_args()
    try:
        errors, warnings, data = verify(args.html)
    except OSError as exc:
        print(f"❌ 无法读取页面：{exc}")
        raise SystemExit(2)
    print(f"页面模式：{(data.get('meta') or {}).get('mode', 'unknown')}")
    for warning in warnings:
        print(f"⚠️  {warning}")
    if errors:
        for error in errors:
            print(f"❌ {error}")
        raise SystemExit(1)
    print("✅ 静态验证全部通过")


if __name__ == "__main__":
    main()
