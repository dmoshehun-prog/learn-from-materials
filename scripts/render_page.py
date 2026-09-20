#!/usr/bin/env python3
"""Deterministically render knowledge-learning-assistant JSON into one HTML + Markdown pair."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

from verify_coverage import verify as verify_coverage
from localization import LOCALE, CATEGORY_EN, ABILITY_EN, localized, localized_enum, t, translate_static
from page_extensions import validate_extensions, extension_markup, relations_markdown
from methods import validate_binding, validate_library, read as read_methods


THEMES = (
    "warm-paper",
    "minimal",
    "dark",
)
GLOSSARY_CATEGORIES = (
    "英文缩写",
    "领域术语",
    "方法框架",
    "角色与流程",
    "指标与工具",
)
MODES = {"overview", "topic", "unit"}
SOURCE_TYPES = {"book", "slides", "document", "web", "text", "mixed"}
ASSESSMENT_ABILITIES = {"记忆", "解释", "应用", "迁移"}
SIGNATURES = {
    "causal_chain", "type_selector", "matrix", "timeline", "decision_tree",
    "questions", "story_card", "before_after", "accordion", "quote_card",
}
SIGNATURE_ORDER = (
    "quote_card",
    "causal_chain",
    "timeline",
    "before_after",
    "type_selector",
    "matrix",
    "accordion",
    "story_card",
    "decision_tree",
    "questions",
)
ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
ACRONYM_PATTERN = re.compile(r"^[A-Z][A-Z0-9+./-]{1,15}$")
ENGLISH_TERM_PATTERN = re.compile(r"[A-Za-z]")
NUMBERED_LABEL_PATTERN = re.compile(r"^\s*(?:[0-9]+|[一二三四五六七八九十]+)\s*[、.．:：)）-]")
# 书籍模式必须让读者看到“具体章节名 + 页码”的可追溯出处。
# 接受中文章节、英文 Chapter/Part、以及前言/序言/结语/附录等书籍部分；
# 标题可使用《》/“”/「」或冒号写法。
BOOK_SECTION_SOURCE_PATTERN = re.compile(
    r"(?:第\s*(?:[0-9]+|[一二三四五六七八九十百千]+)\s*[章节回卷篇]|Chapter\s+\d+|Part\s+[IVXLC0-9]+|前言|序言|引言|结语|后记|附录)"
    r"\s*(?:《[^》]+》|「[^」]+」|“[^”]+”|[:：]\s*[^·；;]+)",
    re.IGNORECASE,
)
BOOK_PAGE_SOURCE_PATTERN = re.compile(
    r"(?:原书\s*第\s*\d+(?:\s*[–—-]\s*\d+)?\s*页|PDF\s*第\s*\d+(?:\s*[–—-]\s*\d+)?\s*页|EPUB\s*第\s*\d+(?:\s*[–—-]\s*\d+)?\s*节|第\s*\d+(?:\s*[–—-]\s*\d+)?\s*页)",
    re.IGNORECASE,
)
SLIDES_SOURCE_PATTERN = re.compile(
    r".+\s·\s第\s*\d+(?:\s*[–—-]\s*\d+)?\s*页幻灯片(?:《[^》]+》|「[^」]+」|“[^”]+”|[:：]\s*.+)",
)
DOCUMENT_SOURCE_PATTERN = re.compile(
    r".+\s·\s(?:标题路径[:：].+|第\s*\d+\s*(?:段|表|图)).*(?:PDF\s*第\s*\d+(?:\s*[–—-]\s*\d+)?\s*页|第\s*\d+\s*(?:段|表|图))",
    re.IGNORECASE,
)
WEB_SOURCE_PATTERN = re.compile(r".+\s·\s小节(?:《[^》]+》|「[^」]+」|“[^”]+”|[:：]\s*.+)")
TEXT_SOURCE_PATTERN = re.compile(
    r".+\s·\s(?:标题(?:《[^》]+》|「[^」]+」|“[^”]+”|[:：]\s*.+)\s·\s)?第\s*\d+(?:\s*[–—-]\s*\d+)?\s*行",
)


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def source_attr(item: dict) -> str:
    return f' data-source="{esc(item.get("source", ""))}"'


def deep_button(concept: str, source: str) -> str:
    return f'''<button class="deep-dive-btn" data-deep-dive data-concept="{esc(concept)}" data-source-ref="{esc(source)}{t('" aria-label="追问：')}{esc(concept)}{t('" title="追问这个概念">?</button>')}'''


def require_text(errors: list[str], obj: dict, field: str, path: str) -> None:
    if not isinstance(obj.get(field), str) or not obj[field].strip():
        errors.append(f"{path}.{field} 必须是非空文本")


def reject_unknown(errors: list[str], obj: dict, allowed: set[str], path: str) -> None:
    unknown = set(obj) - allowed
    if unknown:
        errors.append(f"{path} 含未定义字段：" + "、".join(sorted(unknown)))


def require_text_list(errors: list[str], obj: dict, field: str, path: str) -> list[str]:
    values = obj.get(field)
    if not isinstance(values, list) or not values or not all(isinstance(value, str) and value.strip() for value in values):
        errors.append(f"{path}.{field} 必须是非空文本数组")
        return []
    return values


def validate_book_source(errors: list[str], source: object, path: str) -> None:
    """Require a concrete chapter/part title plus a page locator for book sources."""
    if not isinstance(source, str) or not source.strip():
        return
    if not BOOK_SECTION_SOURCE_PATTERN.search(source):
        errors.append(
            f"{path}.source 是书籍出处，必须包含具体章节/部分名称，例如：第3章《章节标题》"
        )
    if not BOOK_PAGE_SOURCE_PATTERN.search(source) and not re.search(r"(?:PDF\s+(?:pp?\.|pages?)|EPUB\s+sections?|(?:Original\s+)?(?:pp?\.|pages?))\s*\d+(?:\s*[–—-]\s*\d+)?", source, re.I):
        errors.append(
            f"{path}.source 是书籍出处，必须包含页码定位，例如：原书第041–046页 · PDF第049–054页"
        )


def validate_book_sources_recursively(errors: list[str], value: object, path: str = "") -> None:
    """Validate every source field in topic/unit book JSON, including component items."""
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if key == "source":
                validate_book_source(errors, child, path or "root")
            else:
                validate_book_sources_recursively(errors, child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_book_sources_recursively(errors, child, f"{path}[{index}]")


def validate_source_for_type(errors: list[str], source: object, path: str, source_type: object) -> None:
    """Validate non-book source locators so every material type remains traceable."""
    if not isinstance(source, str) or not source.strip():
        return
    patterns = {
        "slides": (SLIDES_SOURCE_PATTERN, "文件名 · 第N页幻灯片《页面标题》"),
        "document": (DOCUMENT_SOURCE_PATTERN, "文件名 · 标题路径：… · PDF第N页（或文件名 · 第N段/表N/图N）"),
        "web": (WEB_SOURCE_PATTERN, "页面标题 · 小节《标题》 · 段落N"),
        "text": (TEXT_SOURCE_PATTERN, "文件名 · 标题《标题》 · 第N–M行（或文件名 · 第N–M行）"),
    }
    rule = patterns.get(source_type)
    english_patterns = {
        "slides": r".+\s·\sSlides?\s+\d+(?:\s*[–—-]\s*\d+)?\s*:\s*\S.+",
        "document": r".+\s·\s(?:Heading:\s*.+\s·\s(?:PDF\s+(?:pp?\.|pages?)\s*\d+(?:\s*[–—-]\s*\d+)?|Paragraph\s+\d+)|(?:Paragraph|Table|Figure)\s+\d+)",
        "web": r".+\s·\sSection:\s*\S.+",
        "text": r".+\s·\s(?:Heading:\s*.+\s·\s)?Lines?\s+\d+(?:\s*[–—-]\s*\d+)?",
    }
    english_match = source_type in english_patterns and re.search(english_patterns[source_type], source, re.I)
    if rule and not rule[0].search(source) and not english_match:
        errors.append(f"{path}.source 是 {source_type} 出处，必须包含可追溯定位，例如：{rule[1]}")
    if source_type == "mixed" and " · " not in source:
        errors.append(f"{path}.source 是多材料出处，必须至少包含文件名和内部定位；多处依据时用分号逐项列出")


def validate_sources_recursively(errors: list[str], value: object, source_type: object, path: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if key == "source":
                validate_source_for_type(errors, child, path or "root", source_type)
            else:
                validate_sources_recursively(errors, child, source_type, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_sources_recursively(errors, child, source_type, f"{path}[{index}]")


def validate_items(
    errors: list[str],
    items: object,
    path: str,
    fields: tuple[str, ...],
    allowed: tuple[str, ...] | None = None,
) -> list[dict]:
    if not isinstance(items, list):
        errors.append(f"{path} 必须是数组")
        return []
    clean = []
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path} 必须是对象")
            continue
        for field in fields:
            require_text(errors, item, field, item_path)
        reject_unknown(errors, item, set(allowed or fields), item_path)
        clean.append(item)
    return clean


def validate_ids(errors: list[str], items: list[dict], path: str) -> list[str]:
    ids: list[str] = []
    for index, item in enumerate(items):
        value = item.get("id")
        if isinstance(value, str) and value.strip():
            ids.append(value)
            if not ID_PATTERN.fullmatch(value):
                errors.append(f"{path}[{index}].id 只能使用英文字母开头的字母、数字、-、_")
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        errors.append(f"{path}.id 不得重复：" + "、".join(duplicates))
    return ids


def ordered_sections(sections: list[dict]) -> list[dict]:
    """Return the canonical pedagogical order, independent of model array order."""
    ranks = {signature: index for index, signature in enumerate(SIGNATURE_ORDER)}
    return sorted(sections, key=lambda item: (ranks.get(item.get("signature"), len(ranks)), item.get("id", "")))


def ordered_source_items(items: list[dict]) -> list[dict]:
    """Keep learning items in first-appearance order from the source material."""
    return sorted(
        items,
        key=lambda item: (
            item.get("sourceOrder", sys.maxsize),
            item.get("id", ""),
            str(item.get("name") or item.get("term") or "").casefold(),
        ),
    )


def ordered_frameworks(items: list[dict]) -> list[dict]:
    return ordered_source_items(items)


def ordered_glossary(items: list[dict]) -> list[dict]:
    return ordered_source_items(items)


def validate_source_order(errors: list[str], items: list[dict], path: str) -> None:
    values: list[int] = []
    for index, item in enumerate(items):
        value = item.get("sourceOrder")
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"{path}[{index}].sourceOrder 必须是从 1 开始的正整数")
        else:
            values.append(value)
    if len(values) == len(items) and sorted(values) != list(range(1, len(items) + 1)):
        errors.append(f"{path}.sourceOrder 必须唯一且连续覆盖 1–{len(items)}")


def validate(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError("内容契约校验失败：根节点必须是对象")
    errors: list[str] = []
    allowed_common = {"schemaVersion", "meta", "hero", "footer"}
    if data.get("schemaVersion") not in {"4.2", "4.3"}:
        errors.append('schemaVersion must be "4.2" or "4.3"')
    meta = data.get("meta")
    hero = data.get("hero")
    if not isinstance(meta, dict):
        errors.append("meta 必须是对象")
        meta = {}
    if not isinstance(hero, dict):
        errors.append("hero 必须是对象")
        hero = {}
    for field in ("title", "creator", "sourceType", "initialTheme", "knowledgeBase", "pageId", "learningDepth"):
        require_text(errors, meta, field, "meta")
    mode = meta.get("mode")
    if mode not in MODES:
        errors.append("meta.mode 必须是 overview/topic/unit")
    if meta.get("sourceType") not in SOURCE_TYPES:
        errors.append("meta.sourceType 必须是 book/slides/document/web/text/mixed")
    theme = meta.get("initialTheme", "warm-paper")
    if theme not in THEMES:
        errors.append("meta.initialTheme 不是受支持主题")
    if meta.get("learningDepth") not in {"quick", "systematic"}:
        errors.append("meta.learningDepth 必须是 quick/systematic")
    if isinstance(meta.get("pageId"), str) and not ID_PATTERN.fullmatch(meta["pageId"]):
        errors.append("meta.pageId 必须以英文字母开头且只含英文字母、数字、-、_")
    allowed_meta = {"title", "creator", "sourceType", "mode", "initialTheme", "knowledgeBase", "pageId", "learningDepth", "language"}
    if mode == "topic":
        allowed_meta.add("topic")
        require_text(errors, meta, "topic", "meta")
    elif mode == "unit":
        allowed_meta.add("unit")
        require_text(errors, meta, "unit", "meta")
    reject_unknown(errors, meta, allowed_meta, "meta")
    reject_unknown(errors, hero, {"eyebrow", "title", "lede", "thesis"}, "hero")
    for field in ("eyebrow", "title", "lede", "thesis"):
        require_text(errors, hero, field, "hero")
    if "footer" in data and (not isinstance(data["footer"], str) or not data["footer"].strip()):
        errors.append("footer 出现时必须是非空文本")

    if mode == "overview":
        unknown = set(data) - (allowed_common | {"frameworks", "contentUnits", "glossary", "decisionRules", "assessment", "relationships", "methodLibrary", "methodology"})
        if unknown:
            errors.append("overview 含未定义顶层字段：" + "、".join(sorted(unknown)))
        frameworks = validate_items(
            errors,
            data.get("frameworks"),
            "frameworks",
            ("name", "oneLine", "when", "firstUnitId", "source"),
            ("id", "name", "oneLine", "when", "firstUnitId", "sourceOrder", "source"),
        )
        content_units = validate_items(
            errors,
            data.get("contentUnits"),
            "contentUnits",
            ("id", "label", "title", "core", "source"),
            ("id", "label", "title", "core", "frameworks", "takeaways", "conclusions", "source", "sourceDetails"),
        )
        glossary = validate_items(
            errors,
            data.get("glossary"),
            "glossary",
            ("id", "term", "category", "definition", "context", "firstUnitId", "source"),
            ("id", "term", "fullName", "zhMeaning", "category", "definition", "context", "related", "units", "firstUnitId", "sourceOrder", "source"),
        )
        rules = validate_items(errors, data.get("decisionRules"), "decisionRules", ("when", "do", "because", "source"), ("id", "when", "do", "because", "source"))
        assessment = data.get("assessment")
        if not isinstance(assessment, dict):
            errors.append("assessment 必须是对象")
            assessment = {}
        reject_unknown(errors, assessment, {"focusAreas"}, "assessment")
        focus_areas = validate_items(
            errors,
            assessment.get("focusAreas"),
            "assessment.focusAreas",
            ("id", "title", "unitId", "source"),
            ("id", "title", "unitId", "abilities", "source"),
        )
        # 不以固定数量或预设上限判断书籍/材料是否完整。数组只要非空即可通过
        # 结构校验；覆盖完整性由知识库、coverage-audit.md 与生成流程逐项保证。
        if not frameworks:
            errors.append("overview 至少需要 1 个来自材料的核心框架")
        if not content_units:
            errors.append("overview 至少需要 1 个内容单元")
        if not glossary:
            errors.append("overview 至少需要 1 个术语")
        if not rules and meta.get("learningDepth") != "quick":
            errors.append("overview 至少需要 1 条行动规则")
        if not focus_areas:
            errors.append("overview 至少需要 1 个学习自检考点")

        unit_ids = validate_ids(errors, content_units, "contentUnits")
        validate_ids(errors, glossary, "glossary")
        validate_ids(errors, focus_areas, "assessment.focusAreas")
        validate_source_order(errors, frameworks, "frameworks")
        validate_source_order(errors, glossary, "glossary")
        for index, unit in enumerate(content_units):
            require_text_list(errors, unit, "frameworks", f"contentUnits[{index}]")
            require_text_list(errors, unit, "takeaways", f"contentUnits[{index}]")
            conclusions = validate_items(
                errors,
                unit.get("conclusions"),
                f"contentUnits[{index}].conclusions",
                ("title", "summary", "source"),
                ("title", "summary", "points", "source"),
            )
            if not conclusions:
                errors.append(f"contentUnits[{index}].conclusions 至少需要 1 组可展开结论")
            for conclusion_index, conclusion in enumerate(conclusions):
                require_text_list(
                    errors,
                    conclusion,
                    "points",
                    f"contentUnits[{index}].conclusions[{conclusion_index}]",
                )
        seen_terms: set[str] = set()
        covered_units: set[str] = set()
        unit_ranks = {unit_id: index for index, unit_id in enumerate(unit_ids)}
        for index, term in enumerate(glossary):
            term_value = str(term.get("term", "")).strip()
            term_key = term_value.casefold()
            if term_key in seen_terms:
                errors.append(f"glossary[{index}].term 与其他术语重复：{term_value}")
            seen_terms.add(term_key)
            if term.get("category") not in (*GLOSSARY_CATEGORIES, *CATEGORY_EN.values()):
                errors.append(
                    f"glossary[{index}].category 必须是：" + "、".join(GLOSSARY_CATEGORIES)
                )
            if "fullName" in term:
                require_text(errors, term, "fullName", f"glossary[{index}]")
            if (
                term.get("category") in {"英文缩写", "Abbreviations"} or ACRONYM_PATTERN.fullmatch(term_value)
            ) and not str(term.get("fullName", "")).strip():
                errors.append(f"glossary[{index}] 是英文缩写，必须提供 fullName 英文全称")
            if "zhMeaning" in term:
                require_text(errors, term, "zhMeaning", f"glossary[{index}]")
            if meta.get("language", "zh-CN") == "zh-CN" and ENGLISH_TERM_PATTERN.search(term_value) and not str(term.get("zhMeaning", "")).strip():
                errors.append(f"glossary[{index}] 是英文缩写或英文术语，必须提供 zhMeaning 中文含义")
            require_text_list(errors, term, "related", f"glossary[{index}]")
            refs = term.get("units")
            if not isinstance(refs, list) or not refs:
                errors.append(f"glossary[{index}].units 至少关联一个内容单元")
            elif not all(isinstance(ref, str) and ref.strip() for ref in refs):
                errors.append(f"glossary[{index}].units 必须是非空文本数组")
            elif any(ref not in unit_ids for ref in refs):
                errors.append(f"glossary[{index}].units 含未知内容单元")
            else:
                covered_units.update(refs)
            first_unit_id = term.get("firstUnitId")
            if first_unit_id not in unit_ids:
                errors.append(f"glossary[{index}].firstUnitId 含未知内容单元")
            elif isinstance(refs, list) and refs and first_unit_id not in refs:
                errors.append(f"glossary[{index}].firstUnitId 必须同时出现在 units 中")
            elif isinstance(refs, list) and refs and all(ref in unit_ranks for ref in refs):
                earliest = min(refs, key=lambda ref: unit_ranks[ref])
                if first_unit_id != earliest:
                    errors.append(f"glossary[{index}].firstUnitId 必须是该术语最早出现的内容单元")
        uncovered = [unit_id for unit_id in unit_ids if unit_id not in covered_units]
        if uncovered:
            errors.append("glossary 必须覆盖每个内容单元，尚未覆盖：" + "、".join(uncovered))
        ordered_term_unit_ranks = [
            unit_ranks.get(item.get("firstUnitId"), sys.maxsize)
            for item in ordered_glossary(glossary)
        ]
        if ordered_term_unit_ranks != sorted(ordered_term_unit_ranks):
            errors.append("glossary.sourceOrder 必须按术语在材料中的首次出现单元递增")

        framework_names = [str(item.get("name") or "").strip() for item in frameworks]
        if len(set(framework_names)) != len(framework_names):
            errors.append("frameworks.name 不得重复")
        expected_frameworks: list[str] = []
        framework_first_units: dict[str, str] = {}
        for unit in content_units:
            for name in unit.get("frameworks", []):
                if name not in framework_first_units:
                    framework_first_units[name] = unit.get("id", "")
                    expected_frameworks.append(name)
        if set(framework_names) != set(expected_frameworks):
            missing = [name for name in expected_frameworks if name not in framework_names]
            extra = [name for name in framework_names if name not in expected_frameworks]
            detail = []
            if missing:
                detail.append("缺少：" + "、".join(missing))
            if extra:
                detail.append("未进入内容单元：" + "、".join(extra))
            errors.append("frameworks 必须与各内容单元首次引入的框架一致（" + "；".join(detail) + "）")
        else:
            ordered_framework_names = [item.get("name") for item in ordered_frameworks(frameworks)]
            if ordered_framework_names != expected_frameworks:
                errors.append("frameworks.sourceOrder 必须按框架在内容单元中的首次出现顺序排列")
        for index, item in enumerate(frameworks):
            name = str(item.get("name") or "").strip()
            first_unit_id = item.get("firstUnitId")
            if first_unit_id not in unit_ids:
                errors.append(f"frameworks[{index}].firstUnitId 含未知内容单元")
            elif name in framework_first_units and first_unit_id != framework_first_units[name]:
                errors.append(f"frameworks[{index}].firstUnitId 不是该框架首次出现的内容单元")

        assessment_units: set[str] = set()
        assessment_abilities: set[str] = set()
        for index, item in enumerate(focus_areas):
            unit_id = item.get("unitId")
            if unit_id not in unit_ids:
                errors.append(f"assessment.focusAreas[{index}].unitId 含未知内容单元")
            else:
                assessment_units.add(unit_id)
            abilities = item.get("abilities")
            if not isinstance(abilities, list) or not abilities or not all(
                isinstance(value, str) and value.strip() for value in abilities
            ):
                errors.append(f"assessment.focusAreas[{index}].abilities 必须是非空文本数组")
            elif any(value not in ASSESSMENT_ABILITIES and value not in ABILITY_EN.values() for value in abilities):
                errors.append(
                    f"assessment.focusAreas[{index}].abilities 只能使用："
                    + "、".join(sorted(ASSESSMENT_ABILITIES))
                )
            else:
                reverse_abilities = {value: key for key, value in ABILITY_EN.items()}
                assessment_abilities.update(reverse_abilities.get(value, value) for value in abilities)
        missing_assessment_units = [unit_id for unit_id in unit_ids if unit_id not in assessment_units]
        if missing_assessment_units:
            errors.append("assessment.focusAreas 必须覆盖每个内容单元，尚未覆盖：" + "、".join(missing_assessment_units))
        missing_abilities = sorted(ASSESSMENT_ABILITIES - assessment_abilities)
        if missing_abilities and meta.get("learningDepth") != "quick":
            errors.append("assessment.focusAreas 合计必须覆盖四层能力，尚未覆盖：" + "、".join(missing_abilities))

        # 书籍阅读必须让每一个可见内容块回溯到“具体章节/部分名称 + 页码”。
        if meta.get("sourceType") == "book":
            for index, item in enumerate(frameworks):
                validate_book_source(errors, item.get("source"), f"frameworks[{index}]")
            for index, unit in enumerate(content_units):
                validate_book_source(errors, unit.get("source"), f"contentUnits[{index}]")
                for conclusion_index, conclusion in enumerate(unit.get("conclusions", [])):
                    if isinstance(conclusion, dict):
                        validate_book_source(
                            errors,
                            conclusion.get("source"),
                            f"contentUnits[{index}].conclusions[{conclusion_index}]",
                        )
            for index, term in enumerate(glossary):
                validate_book_source(errors, term.get("source"), f"glossary[{index}]")
            for index, item in enumerate(rules):
                validate_book_source(errors, item.get("source"), f"decisionRules[{index}]")
            for index, item in enumerate(focus_areas):
                validate_book_source(errors, item.get("source"), f"assessment.focusAreas[{index}]")
        elif meta.get("sourceType") in {"slides", "document", "web", "text", "mixed"}:
            validate_sources_recursively(
                errors,
                {
                    "frameworks": frameworks,
                    "contentUnits": content_units,
                    "glossary": glossary,
                    "decisionRules": rules,
                    "assessment": assessment,
                },
                meta.get("sourceType"),
                "overview",
            )
    elif mode in {"topic", "unit"}:
        unknown = set(data) - (allowed_common | {"sections"})
        if unknown:
            errors.append(f"{mode} 含未定义顶层字段：" + "、".join(sorted(unknown)))
        sections = data.get("sections")
        if not isinstance(sections, list) or not sections:
            errors.append(f"{mode} 模式至少需要一个 sections 分区")
        else:
            validate_ids(errors, [section for section in sections if isinstance(section, dict)], "sections")
            for index, section in enumerate(sections):
                if not isinstance(section, dict):
                    errors.append(f"sections[{index}] 必须是对象")
                    continue
                for field in ("id", "label", "title", "lead", "signature"):
                    require_text(errors, section, field, f"sections[{index}]")
                section_path = f"sections[{index}]"
                if isinstance(section.get("label"), str) and NUMBERED_LABEL_PATTERN.match(section["label"]):
                    errors.append(f"{section_path}.label 不要自带序号；渲染器会固定分区顺序")
                signature = section.get("signature")
                if signature not in SIGNATURES:
                    errors.append(f"{section_path}.signature 不受支持")
                    continue
                signature_field = {
                    "causal_chain": "chain",
                    "type_selector": "options",
                    "matrix": "rows",
                    "timeline": "events",
                    "decision_tree": "branches",
                    "questions": "questions",
                    "story_card": "stories",
                    "before_after": "before",
                    "accordion": "items",
                    "quote_card": "quote",
                }[signature]
                allowed_section = {"id", "label", "title", "lead", "signature", "notes", signature_field}
                if signature == "matrix":
                    allowed_section.add("dimensions")
                elif signature == "before_after":
                    allowed_section.add("after")
                reject_unknown(errors, section, allowed_section, section_path)
                if "notes" in section:
                    validate_items(errors, section.get("notes"), f"{section_path}.notes", ("title", "body", "source"))
                if signature == "causal_chain":
                    items = validate_items(errors, section.get("chain"), f"{section_path}.chain", ("id", "label", "body", "source"))
                    validate_ids(errors, items, f"{section_path}.chain")
                    if len(items) < 3:
                        errors.append(f"{section_path}.chain 至少需要 3 项")
                elif signature == "type_selector":
                    items = validate_items(errors, section.get("options"), f"{section_path}.options", ("id", "label", "title", "body", "watch", "source"))
                    validate_ids(errors, items, f"{section_path}.options")
                    if len(items) < 2:
                        errors.append(f"{section_path}.options 至少需要 2 项")
                elif signature == "matrix":
                    dimensions = section.get("dimensions")
                    if not isinstance(dimensions, list) or not dimensions or not all(isinstance(item, str) and item.strip() for item in dimensions):
                        errors.append(f"{section_path}.dimensions 必须是非空文本数组")
                        dimensions = []
                    rows = validate_items(
                        errors,
                        section.get("rows"),
                        f"{section_path}.rows",
                        ("option", "source"),
                        ("option", "scores", "source"),
                    )
                    if not rows:
                        errors.append(f"{section_path}.rows 至少需要 1 项")
                    for row_index, row in enumerate(rows):
                        scores = row.get("scores")
                        if not isinstance(scores, list) or len(scores) != len(dimensions):
                            errors.append(f"{section_path}.rows[{row_index}].scores 数量必须等于 dimensions")
                        elif not all(isinstance(score, str) and score.strip() for score in scores):
                            errors.append(f"{section_path}.rows[{row_index}].scores 必须是非空文本数组")
                elif signature == "timeline":
                    items = validate_items(errors, section.get("events"), f"{section_path}.events", ("time", "title", "body", "source"))
                    if len(items) < 2:
                        errors.append(f"{section_path}.events 至少需要 2 项")
                elif signature == "decision_tree":
                    items = validate_items(errors, section.get("branches"), f"{section_path}.branches", ("question", "reasoning", "source"))
                    if len(items) < 2:
                        errors.append(f"{section_path}.branches 至少需要 2 项")
                elif signature == "questions":
                    items = validate_items(errors, section.get("questions"), f"{section_path}.questions", ("title", "hint", "source"))
                    if len(items) < 2:
                        errors.append(f"{section_path}.questions 至少需要 2 项")
                elif signature == "story_card":
                    items = validate_items(errors, section.get("stories"), f"{section_path}.stories", ("label", "title", "body", "insight", "source"))
                    if not items:
                        errors.append(f"{section_path}.stories 至少需要 1 项")
                elif signature == "before_after":
                    for side in ("before", "after"):
                        item = section.get(side)
                        if not isinstance(item, dict):
                            errors.append(f"{section_path}.{side} 必须是对象")
                        else:
                            reject_unknown(errors, item, {"label", "title", "body", "source"}, f"{section_path}.{side}")
                            for field in ("label", "title", "body", "source"):
                                require_text(errors, item, field, f"{section_path}.{side}")
                elif signature == "accordion":
                    items = validate_items(errors, section.get("items"), f"{section_path}.items", ("title", "body", "source"))
                    if len(items) < 2:
                        errors.append(f"{section_path}.items 至少需要 2 项")
                elif signature == "quote_card":
                    item = section.get("quote")
                    if not isinstance(item, dict):
                        errors.append(f"{section_path}.quote 必须是对象")
                    else:
                        reject_unknown(errors, item, {"text", "attribution", "source"}, f"{section_path}.quote")
                        for field in ("text", "attribution", "source"):
                            require_text(errors, item, field, f"{section_path}.quote")
            if meta.get("sourceType") == "book":
                validate_book_sources_recursively(errors, sections, "sections")
            elif meta.get("sourceType") in {"slides", "document", "web", "text", "mixed"}:
                validate_sources_recursively(errors, sections, meta.get("sourceType"), "sections")

    validate_extensions(data, errors)
    if 'methodology' in data:
        from methodology import validate as validate_methodology
        try:
            validate_methodology(data['methodology'], data)
            if meta.get('sourceType') == 'book':
                validate_book_sources_recursively(errors, data['methodology'], 'methodology')
            else:
                validate_sources_recursively(errors, data['methodology'], meta.get('sourceType'), 'methodology')
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(str(exc))
    for unit in data.get('contentUnits', []):
        if 'sourceDetails' in unit:
            details = unit['sourceDetails']
            if not isinstance(details, dict):
                errors.append('sourceDetails must be an object')
                continue
            reject_unknown(errors, details, {'core','frameworks','takeaways','conclusions'}, 'sourceDetails')
            if 'core' in details:
                require_text(errors, details, 'core', 'sourceDetails')
            for key in ('frameworks','takeaways'):
                if key in details:
                    require_text_list(errors, details, key, 'sourceDetails')
                    if len(details[key]) != len(unit[key]): errors.append('sourceDetails.' + key + ' count mismatch')
            if 'conclusions' in details:
                if not isinstance(details['conclusions'], list) or len(details['conclusions']) != len(unit['conclusions']):
                    errors.append('sourceDetails.conclusions count mismatch')
                else:
                    for detail, conclusion in zip(details['conclusions'], unit['conclusions']):
                        if not isinstance(detail, dict):
                            errors.append('sourceDetails conclusion must be an object'); continue
                        reject_unknown(errors, detail, {'summary','points'}, 'sourceDetails conclusion')
                        require_text(errors, detail, 'summary', 'sourceDetails conclusion')
                        require_text_list(errors, detail, 'points', 'sourceDetails conclusion')
                        if len(detail.get('points', [])) != len(conclusion['points']): errors.append('sourceDetails conclusion point count mismatch')
            def check_detail(v):
                if isinstance(v, str):
                    if meta.get('sourceType') == 'book':
                        validate_book_source(errors, v, 'sourceDetails')
                    else:
                        validate_source_for_type(errors, v, 'sourceDetails', meta.get('sourceType'))
                elif isinstance(v, list):
                    for x in v: check_detail(x)
                elif isinstance(v, dict):
                    for x in v.values(): check_detail(x)
            check_detail(details)
    if isinstance(data.get("relationships"), list):
        if meta.get("sourceType") == "book":
            validate_book_sources_recursively(errors, data["relationships"], "relationships")
        else:
            validate_sources_recursively(errors, data["relationships"], meta.get("sourceType"), "relationships")
    if errors:
        raise ValueError("内容契约校验失败：\n- " + "\n- ".join(errors))
    validate_binding(data)


def render_hero(hero: dict) -> str:
    return f"""<section class="hero" aria-labelledby="pageTitle"><div class="hero-stamp" aria-hidden="true"><span>LEARNING</span><strong>01</strong><span>STUDIO</span></div><div class="hero-copy"><p class="eyebrow">{esc(hero['eyebrow'])}</p><h1 id="pageTitle">{esc(hero['title'])}</h1><p class="lede">{esc(hero['lede'])}{t('</p></div><aside class="thesis"><span class="thesis-index">CORE / 01</span><strong>一句话总论</strong><span>')}{esc(hero['thesis'])}</span></aside></section>"""


def render_learning_depth_banner(meta: dict) -> str:
    if meta['learningDepth'] == 'quick':
        return t('<section class="depth-banner depth-quick" aria-label="学习深度"><div><strong>快速了解模式</strong><span>核心导读，非全量知识整理。聚焦各章主线、必要术语与关键限制；细节可通过“让 AI 详解本单元”继续学习。未核验范围见配套覆盖说明。</span></div><button id="upgradeDepthCopy" type="button">改为系统学习</button></section>')
    return t('<section class="depth-banner depth-systematic" aria-label="学习深度"><div><strong>系统学习模式</strong><span>尽可能全面保留材料中的框架、术语、论证、案例、规则与可测知识点。</span></div></section>')


def render_frameworks(items: list[dict]) -> str:
    cards = []
    for index, item in enumerate(ordered_frameworks(items), 1):
        number = item.get('sourceOrder')
        if type(number) is not int or number < 1:  # Legacy 4.2 pages may omit sourceOrder.
            number = index
        cards.append(f'''<article class="note" data-framework-number="{number:02d}"{source_attr(item)}><h3>{esc(item['name'])}</h3><p>{esc(item['oneLine'])}{t('</p><p class="when">适用：')}{esc(item['when'])}</p>{deep_button(item['name'], item['source'])}</article>''')
    return t('<h2 class="section-title">先抓住材料的知识骨架</h2><p class="section-lead">这些框架来自材料中的关键判断，也是后续内容单元、术语和行动规则的共同底座。</p><div class="grid">') + ''.join(cards) + '</div>'


def render_unit_contents(unit: dict) -> str:
    frameworks = ''.join((f'<li>{esc(item)}</li>' for item in unit.get('frameworks', [])))
    takeaways = ''.join((f'<li>{esc(item)}</li>' for item in unit.get('takeaways', [])))
    conclusions = []
    for item in unit.get('conclusions', []):
        points = ''.join((f'<li>{esc(point)}</li>' for point in item.get('points', [])))
        conclusions.append(f'''<details class="chapter-conclusion"{source_attr(item)}><summary><span class="conclusion-title">{esc(item['title'])}</span><span class="conclusion-summary">{esc(item['summary'])}</span></summary><div class="conclusion-body"><ul>{points}</ul>{deep_button(item['title'], item['source'])}</div></details>''')
    return f"""<div class="ch-view-label">{esc(unit['label'])} · {esc(unit['title'])}{t('</div><p class="ch-core"><strong>核心思想：</strong>')}{esc(unit['core'])}{t('</p><div class="ch-block"><h4>关键框架</h4><ul>')}{frameworks}{t('</ul></div><div class="ch-block"><h4>行动要点</h4><ul>')}{takeaways}{t('</ul></div><div class="ch-conclusions"><h4>点开结论，继续往下理解</h4>')}""" + ''.join(conclusions) + f'''</div><button class="ch-send" type="button" data-ch-send="{esc(unit['id'])}{t('" data-tooltip="复制本单元的核心内容、关键框架和材料出处。粘贴到当前材料对话后，AI 将基于原材料进行深入讲解。" aria-label="让 AI 详解本单元：复制详解口令到当前材料对话">让 AI 详解本单元</button>')}'''


def render_units(units: list[dict]) -> str:
    nav = ''.join((f'''<button class="ch-nav-btn{(' active' if index == 0 else '')}" data-ch="{esc(item['id'])}">{esc(item['label'])}</button>''' for index, item in enumerate(units)))
    first = units[0]
    return f'''{t('<h2 class="section-title">按材料结构逐个学懂</h2><p class="section-lead">内容单元保留原材料顺序；书籍对应章节，PPT对应连续幻灯片组，文档对应标题分区。每个单元先给核心思想，再展开关键结论；第一单元已直接写入页面。</p><div class="ch-explorer"><div class="ch-nav" aria-label="内容单元导航">')}{nav}</div><article class="ch-view" id="chView"{source_attr(first)}>{render_unit_contents(first)}</article></div>'''


def render_glossary(items: list[dict], units: list[dict]) -> str:
    unit_labels = {item['id']: f"{item['label']}·{item['title']}" for item in units}
    cards = []
    for item in ordered_glossary(items):
        full_name = item.get('fullName', '')
        full_name_html = f'<span class="term-full-name">{esc(full_name)}</span>' if full_name else ''
        zh_meaning = item.get('zhMeaning', '') if LOCALE.get() == 'zh-CN' else ''
        zh_meaning_html = f"""{t('<span class="term-zh-meaning">中文：')}{esc(zh_meaning)}</span>""" if zh_meaning else ''
        related = '、'.join(item.get('related', []))
        unit_text = '、'.join((unit_labels.get(unit_id, unit_id) for unit_id in item.get('units', [])))
        cards.append(f"""<details class="term-item" data-term-entry{source_attr(item)}><summary><span class="term-heading"><span class="term-name">{esc(item['term'])}</span>{zh_meaning_html}{full_name_html}</span><span class="term-category">{esc(localized_enum(item['category']))}{t('</span></summary><div class="term-body"><p><strong>通俗定义：</strong>')}{esc(item['definition'])}{t('</p><p><strong>材料语境：</strong>')}{esc(item['context'])}{t('</p><p><strong>相关术语：</strong>')}{esc(related)}{t('</p><p><strong>涉及单元：</strong>')}{esc(unit_text)}</p>{deep_button(item['term'], item['source'])}</div></details>""")
    return f"""{t('<h2 class="section-title">把材料中的专业词汇一次查清</h2><p class="section-lead">共 ')}{len(items)}{t(' 个术语，覆盖英文缩写、领域术语、方法框架、角色流程与指标工具。英文缩写和单词会直接显示中文含义；可搜索，也可逐条展开查看解释和材料语境。</p><div class="glossary-toolbar"><label class="sr-only" for="glossarySearch">搜索术语</label><input id="glossarySearch" class="glossary-search" type="search" placeholder="搜索术语、英文缩写或解释…" autocomplete="off"><span class="glossary-count" id="glossaryCount" aria-live="polite">显示 ')}{len(items)} / {len(items)}</span></div><div class="glossary-list" id="glossaryList">""" + ''.join(cards) + t('</div><p class="glossary-empty" id="glossaryEmpty" hidden>没有找到匹配术语，请换一个关键词。</p><button class="term-ask-fab" id="termAskFab" type="button" data-deep-dive data-concept="术语大全" data-source-ref="材料术语汇总" aria-label="粘贴不理解的术语并向 AI 提问" title="粘贴术语问 AI">?</button>')


def render_rules(items: list[dict]) -> str:
    if not items:
        return t('<h2 class="section-title">行动规则</h2><p class="section-lead">本次核心导读未提炼出材料明确支持的行动规则，不额外编造建议。</p>')
    rules = []
    for item in items:
        title = f"{t('当 ')}{item['when']}"
        rules.append(f'''<li class="rule-item"{source_attr(item)}><strong>{esc(title)}</strong> → {esc(item['do'])} <em>（{esc(item['because'])}）</em>{deep_button(title, item['source'])}</li>''')
    return f"""{t('<h2 class="section-title">把方法论压缩成下一步动作</h2><p class="section-lead">共 ')}{len(items)}{t(' 条规则，覆盖材料中的主要判断与行动场景。统一采用“当 X，做 Y，因为 Z”，按页面向下滚动即可连续阅读。</p><div class="content-stream"><ul class="rules">')}""" + ''.join(rules) + '</ul></div>'


def render_assessment(assessment: dict, units: list[dict]) -> str:
    options = ''.join((f'''<option value="{esc(item['id'])}">{esc(item['label'])} · {esc(item['title'])}</option>''' for item in units))
    focus_count = len(assessment.get('focusAreas', []))
    return f"""{t('<h2 class="section-title">按你的目标生成一场动态测验</h2><p class="section-lead">页面已整理 ')}{focus_count}{t(' 个可测考点，但不会把固定题目全部铺开。选择范围和要求后复制口令，粘贴到当前材料对话中，AI 会基于知识库逐题测试、判分并动态调整难度。</p><div class="assessment-shell"><div class="assessment-steps" aria-label="动态测验步骤"><div><strong>1</strong><span>选择范围与难度</span></div><div><strong>2</strong><span>复制口令到对话框</span></div><div><strong>3</strong><span>结束后导回错题</span></div></div><fieldset class="assessment-scope"><legend>出题范围</legend><label><input type="radio" name="assessmentScope" value="all" checked><span>综合全部</span><small>覆盖整份材料</small></label><label><input type="radio" name="assessmentScope" value="unit"><span>指定章节</span><small>选择一个内容单元</small></label><label><input type="radio" name="assessmentScope" value="custom"><span>自定义要求</span><small>按你的目标出题</small></label></fieldset><div class="assessment-field" id="assessmentUnitWrap" hidden><label for="assessmentUnit">选择章节或单元</label><select id="assessmentUnit">')}{options}{t('</select></div><div class="assessment-field" id="assessmentCustomWrap" hidden><label for="assessmentCustom">告诉 AI 你想重点练什么</label><textarea id="assessmentCustom" placeholder="例如：重点测试第三章，多出应用题，少出记忆题；或者只练容易混淆的概念。"></textarea></div><div class="assessment-settings"><label for="assessmentCount">题量<select id="assessmentCount"><option value="5">5 题</option><option value="8" selected>8 题</option><option value="10">10 题</option><option value="15">15 题</option></select></label><label for="assessmentDifficulty">难度<select id="assessmentDifficulty"><option value="基础">基础</option><option value="进阶">进阶</option><option value="挑战">挑战</option><option value="自适应" selected>自适应</option></select></label><label for="assessmentAbility">能力重点<select id="assessmentAbility"><option value="综合：记忆、解释、应用与迁移" selected>综合能力</option><option value="记忆与概念辨析">记忆与辨析</option><option value="解释机制与因果关系">理解与解释</option><option value="应用与案例判断">应用判断</option><option value="新情境迁移">迁移能力</option></select></label></div><button class="assessment-copy" id="assessmentCopy" type="button">生成并复制自检口令</button><details class="assessment-preview"><summary>查看或手动复制口令</summary><textarea id="assessmentPromptPreview" readonly aria-label="生成的自检口令"></textarea></details><p class="assessment-boundary">如果当前对话没有加载对应材料或知识库，口令会要求 AI 先请你上传，避免脱离材料出题。基础题可使用具备文件读取和结构化输出能力的通用模型；专业材料与复杂开放题建议使用长上下文、高推理能力模型。</p></div><section class="mistake-book" aria-labelledby="mistakeBookTitle"><div class="mistake-book-heading"><div><p class="section-kicker">测验后的复习闭环</p><h2 id="mistakeBookTitle">我的错题本</h2></div><span id="mistakeCount">0 道错题</span></div><p class="mistake-book-lead">测验结束后，复制 AI 生成的错题记录，粘贴到下方即可导入。错题保存在当前浏览器；换设备前请备份 JSON。</p><div class="mistake-import-box"><label for="mistakeImportText">粘贴 AI 的测验总结或错题 JSON</label><textarea id="mistakeImportText" placeholder="可直接粘贴整段测验总结，页面会自动寻找 KLA_MISTAKES_JSON 标记。"></textarea><button id="mistakeImportPaste" type="button">导入粘贴内容</button></div><div class="mistake-toolbar"><input id="mistakeSearch" type="search" placeholder="搜索题目、知识点或章节…" aria-label="搜索错题"><select id="mistakeStatusFilter" aria-label="按掌握状态筛选"><option value="全部">全部状态</option><option value="未掌握">未掌握</option><option value="复习中">复习中</option><option value="已掌握">已掌握</option></select><button id="mistakeRetryVisible" type="button">复制筛选结果复测口令</button><button id="mistakeExportJson" type="button">备份 JSON</button><label class="mistake-file-import">导入 JSON<input id="mistakeImportFile" type="file" accept="application/json,.json" hidden></label></div><p class="mistake-storage" id="mistakeStorageStatus">保存在当前浏览器；换设备前请备份 JSON。</p><div class="mistake-list" id="mistakeList"><div class="mistake-empty"><strong>还没有错题</strong><span>完成一次 AI 测验后，把错题记录粘贴到上方。</span></div></div></section>')}"""


def render_personal_notes() -> str:
    return t('<h2 class="section-title">把感兴趣的内容变成自己的知识</h2><p class="section-lead">在任意内容卡片右下角点击“☆”，原内容和出处会立即保存，无需复制粘贴。之后可在这里搜索、展开、编辑或删除；笔记只保存在当前浏览器，可用 JSON 备份或迁移。</p><div class="notes-guide" aria-label="笔记使用步骤"><div><strong>1</strong><span>点击内容旁的 ☆</span></div><div><strong>2</strong><span>原内容立即保存</span></div><div><strong>3</strong><span>回来编辑与回顾</span></div></div><div class="notes-toolbar"><label class="sr-only" for="noteSearch">搜索笔记</label><input id="noteSearch" class="note-search" type="search" placeholder="搜索标题、标签、理解或行动…" autocomplete="off"><button id="freeNoteBtn" class="note-tool primary" type="button">新增自由笔记</button><button id="exportNotesMd" class="note-tool" type="button">导出 Markdown</button><button id="exportNotesJson" class="note-tool" type="button">备份 JSON</button><label class="note-tool note-import">导入 JSON<input id="noteImportInput" type="file" accept="application/json,.json" hidden></label></div><div class="notes-meta"><span id="noteCount" aria-live="polite">0 条笔记</span><span id="notesStorageStatus">保存在当前浏览器；换设备前请备份 JSON。</span></div><div class="notes-list" id="notesList" aria-live="polite"><div class="notes-empty" id="notesEmpty"><strong>还没有笔记</strong><span>点击任意内容卡片右下角的“☆”即可保存。</span></div></div>')


def render_notes(items: list[dict]) -> str:
    cards = []
    for item in items:
        title = item.get('title', t('要点'))
        cards.append(f'''<article class="note"{source_attr(item)}><h3>{esc(title)}</h3><p>{esc(item.get('body'))}</p>{deep_button(title, item.get('source', ''))}</article>''')
    return '<div class="grid">' + ''.join(cards) + '</div>' if cards else ''


def render_signature(section: dict) -> str:
    signature = section.get('signature')
    if signature == 'causal_chain':
        chain = section.get('chain', [])
        buttons = ''.join((f'''<button class="chain-step{(' active' if index == 0 else '')}" data-section-id="{esc(section['id'])}" data-step-id="{esc(item.get('id'))}">{esc(item.get('label'))}</button>''' for index, item in enumerate(chain)))
        first = chain[0] if chain else {'body': '', 'source': ''}
        return f'''<div class="chain">{buttons}</div><div class="explain section-explain" data-section-explain="{esc(section['id'])}"{source_attr(first)}>{esc(first.get('body'))}{deep_button(first.get('label', t('因果链')), first.get('source', ''))}</div>'''
    if signature == 'type_selector':
        options = section.get('options', [])
        buttons = ''.join((f'''<button class="city-btn{(' active' if index == 0 else '')}" data-section-id="{esc(section['id'])}" data-option-id="{esc(item.get('id'))}">{esc(item.get('label'))}</button>''' for index, item in enumerate(options)))
        first = options[0] if options else {}
        return f'''<div class="split"><div class="city-buttons">{buttons}</div><article class="result" data-section-result="{esc(section['id'])}"{source_attr(first)}><h3>{esc(first.get('title'))}</h3><p>{esc(first.get('body'))}{t('</p><p><strong>看点：</strong>')}{esc(first.get('watch'))}</p>{deep_button(first.get('title', t('类型分析')), first.get('source', ''))}</article></div>'''
    if signature == 'matrix':
        dimensions = section.get('dimensions', [])
        rows = section.get('rows', [])
        head = ''.join((f'<th>{esc(item)}</th>' for item in dimensions))
        body = ''.join((f'''<tr><td class="matrix-option"{source_attr(row)}>{esc(row.get('option'))}{deep_button(row.get('option', t('矩阵选项')), row.get('source', ''))}</td>''' + ''.join((f'<td>{esc(score)}</td>' for score in row.get('scores', []))) + '</tr>' for row in rows))
        return f"""{t('<div class="table-wrap"><table class="matrix"><thead><tr><th>选项</th>')}{head}</tr></thead><tbody>{body}</tbody></table></div>"""
    if signature == 'timeline':
        return '<div class="timeline">' + ''.join((f'''<article class="timeline-item"{source_attr(item)}><div class="time">{esc(item.get('time'))}</div><h3>{esc(item.get('title'))}</h3><p>{esc(item.get('body'))}</p>{deep_button(item.get('title', t('时间节点')), item.get('source', ''))}</article>''' for item in section.get('events', []))) + '</div>'
    if signature in {'decision_tree', 'accordion'}:
        items = section.get('branches', section.get('items', []))
        return '<div class="accordion">' + ''.join((f'''<details class="acc-item"{source_attr(item)}><summary>{esc(item.get('question', item.get('title')))}</summary><div class="acc-body">{esc(item.get('reasoning', item.get('body')))}{deep_button(item.get('question', item.get('title', t('分层论述'))), item.get('source', ''))}</div></details>''' for item in items)) + '</div>'
    if signature == 'questions':
        return '<div class="questions">' + ''.join((f'''<article class="question"{source_attr(item)}><div><h3>{esc(item.get('title'))}</h3><p>{esc(item.get('hint'))}</p></div>{deep_button(item.get('title', t('自检问题')), item.get('source', ''))}</article>''' for item in section.get('questions', []))) + '</div>'
    if signature == 'story_card':
        return ''.join((f'''<article class="story"{source_attr(item)}><div class="story-label">{esc(item.get('label'))}</div><h3>{esc(item.get('title'))}</h3><p>{esc(item.get('body'))}</p><div class="story-insight">{esc(item.get('insight'))}</div>{deep_button(item.get('title', t('案例')), item.get('source', ''))}</article>''' for item in section.get('stories', [])))
    if signature == 'before_after':
        before = section.get('before', {})
        after = section.get('after', {})
        return f'''<div class="before-after"><article class="ba-col before"{source_attr(before)}><div class="ba-label">{esc(before.get('label', t('之前')))}</div><h3>{esc(before.get('title'))}</h3><p>{esc(before.get('body'))}</p>{deep_button(before.get('title', t('之前')), before.get('source', ''))}</article><article class="ba-col after"{source_attr(after)}><div class="ba-label">{esc(after.get('label', t('之后')))}</div><h3>{esc(after.get('title'))}</h3><p>{esc(after.get('body'))}</p>{deep_button(after.get('title', t('之后')), after.get('source', ''))}</article></div>'''
    if signature == 'quote_card':
        quote = section.get('quote', {})
        return f'''<figure class="quote"{source_attr(quote)}><blockquote>{esc(quote.get('text'))}</blockquote><figcaption class="q-source">{esc(quote.get('attribution'))}</figcaption>{deep_button(t('材料原话'), quote.get('source', ''))}</figure>'''
    return ''


def render_sections(sections: list[dict]) -> list[tuple[str, str, str]]:
    output = []
    for section in ordered_sections(sections):
        body = f"""<h2 class="section-title">{esc(section['title'])}</h2><p class="section-lead">{esc(section['lead'])}</p>""" + render_notes(section.get('notes', [])) + render_signature(section)
        output.append((section['id'], section['label'], body))
    return output


def overview_modules(data: dict) -> list[tuple[str, str, str]]:
    return [('frameworks', t('核心框架'), render_frameworks(data['frameworks'])), ('content', t('内容导学'), render_units(data['contentUnits'])), ('glossary', t('术语大全'), render_glossary(data['glossary'], data['contentUnits'])), ('rules', t('行动规则'), render_rules(data['decisionRules'])), ('practice', t('学习自检'), render_assessment(data['assessment'], data['contentUnits']))]


def md_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", "<br>")


def markdown_signature(section: dict) -> list[str]:
    signature = section['signature']
    lines: list[str] = []
    if signature == 'causal_chain':
        for index, item in enumerate(section['chain'], start=1):
            lines.extend([f"### {index}. {item['label']}", '', item['body'], f"{t('出处：')}{item['source']}", ''])
    elif signature == 'type_selector':
        for item in section['options']:
            lines.extend([f"### {item['label']}｜{item['title']}", '', item['body'], '', f"{t('判断重点：')}{item['watch']}", f"{t('出处：')}{item['source']}", ''])
    elif signature == 'matrix':
        headers = [t('选项'), *section['dimensions'], t('出处')]
        lines.extend(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'])
        for item in section['rows']:
            cells = [item['option'], *item['scores'], item['source']]
            lines.append('| ' + ' | '.join((md_cell(value) for value in cells)) + ' |')
        lines.append('')
    elif signature == 'timeline':
        for item in section['events']:
            lines.extend([f"### {item['time']}｜{item['title']}", '', item['body'], f"{t('出处：')}{item['source']}", ''])
    elif signature == 'decision_tree':
        for item in section['branches']:
            lines.extend([f"### {item['question']}", '', item['reasoning'], f"{t('出处：')}{item['source']}", ''])
    elif signature == 'questions':
        for item in section['questions']:
            lines.extend([f"### {item['title']}", '', item['hint'], f"{t('出处：')}{item['source']}", ''])
    elif signature == 'story_card':
        for item in section['stories']:
            lines.extend([f"### {item['label']}｜{item['title']}", '', item['body'], '', f"{t('案例启示：')}{item['insight']}", f"{t('出处：')}{item['source']}", ''])
    elif signature == 'before_after':
        for item in (section['before'], section['after']):
            lines.extend([f"### {item['label']}｜{item['title']}", '', item['body'], f"{t('出处：')}{item['source']}", ''])
    elif signature == 'accordion':
        for item in section['items']:
            lines.extend([f"### {item['title']}", '', item['body'], f"{t('出处：')}{item['source']}", ''])
    elif signature == 'quote_card':
        item = section['quote']
        quoted = '\n> '.join(item['text'].splitlines())
        lines.extend([f'> {quoted}', '', f"— {item['attribution']}", f"{t('出处：')}{item['source']}", ''])
    return lines


def component_styles(tab_count: int) -> str:
    return f"""
    .tabs {{ grid-template-columns: repeat({max(1, min(tab_count, 6))}, minmax(0, 1fr)); }}
    .ch-explorer {{ display:grid; grid-template-columns:190px minmax(0,1fr); gap:18px; margin:20px 0; align-items:start; }}
    .ch-nav {{ display:grid; gap:8px; align-content:start; position:sticky; top:92px; }}
    .ch-nav-btn {{ min-height:48px; padding:12px 14px; border:1px solid var(--line); border-radius:12px; background:var(--surface); color:var(--ink); cursor:pointer; font:800 14px/1.3 var(--font-display); text-align:left; transition:transform .18s ease,background .18s ease,border-color .18s ease; }}
    .ch-nav-btn:hover {{ transform:translateX(3px); border-color:var(--blue); }}
    .ch-nav-btn.active {{ color:var(--white); background:var(--ink); border-color:var(--ink); }}
    .ch-view {{ position:relative; min-height:320px; padding:26px; border:1px solid var(--line); border-radius:20px; background:var(--surface-strong); box-shadow:var(--card-shadow); }}
    .ch-view-label {{ margin-bottom:10px; color:var(--gold); font:700 14px/1.3 var(--font-display); }}
    .ch-view h4 {{ margin:16px 0 8px; color:var(--blue); }}
    .ch-view ul {{ padding-left:20px; line-height:1.75; }}
    .ch-conclusions {{ margin-top:22px; }}
    .chapter-conclusion {{ position:relative; margin:10px 0; border:1px solid var(--line); border-radius:14px; background:var(--surface); overflow:visible; }}
    .chapter-conclusion summary {{ display:grid; gap:5px; min-height:58px; padding:15px 48px 15px 17px; cursor:pointer; list-style:none; }}
    .chapter-conclusion summary::-webkit-details-marker {{ display:none; }}
    .chapter-conclusion summary::after {{ content:"+"; position:absolute; top:18px; right:18px; color:var(--gold); font:900 22px/1 var(--font-display); }}
    .chapter-conclusion[open] summary::after {{ content:"−"; }}
    .conclusion-title {{ color:var(--ink); font:850 17px/1.3 var(--font-display); }}
    .conclusion-summary {{ color:var(--muted); font:14px/1.55 var(--font-display); }}
    .conclusion-body {{ position:relative; padding:0 20px 18px; border-top:1px solid var(--line); }}
    .conclusion-body ul {{ margin:14px 0 0; }}
    .ch-send {{ min-height:46px; margin-top:18px; padding:11px 18px; border:0; border-radius:12px; background:var(--blue); color:var(--white); cursor:pointer; font:700 14px/1.3 var(--font-display); }}
    .ch-send[data-tooltip] {{ position:relative; }}
    .ch-send[data-tooltip]::after {{ content:attr(data-tooltip); position:absolute; left:0; bottom:calc(100% + 10px); z-index:80; width:min(320px,calc(100vw - 48px)); padding:10px 12px; border:1px solid var(--line); border-radius:10px; background:var(--ink); color:var(--white); box-shadow:var(--card-shadow); opacity:0; visibility:hidden; transform:translateY(5px); pointer-events:none; text-align:left; white-space:normal; font:600 12px/1.55 var(--font-display); transition:opacity .16s ease,transform .16s ease,visibility .16s ease; }}
    .ch-send[data-tooltip]:hover::after,.ch-send[data-tooltip]:focus-visible::after {{ opacity:1; visibility:visible; transform:translateY(0); }}
    .glossary-toolbar {{ display:flex; gap:12px; align-items:center; margin:18px 0 14px; }}
    .glossary-search {{ flex:1; min-width:0; min-height:48px; padding:12px 16px; border:1px solid var(--line); border-radius:14px; background:var(--surface-strong); color:var(--ink); box-shadow:var(--card-shadow); font:600 15px/1.4 var(--font-display); }}
    .glossary-search:focus {{ outline:3px solid var(--tint-blue); outline:3px solid color-mix(in srgb,var(--blue) 24%,transparent); border-color:var(--blue); }}
    .glossary-count {{ flex:none; color:var(--muted); font:700 13px/1.3 var(--font-display); }}
    .glossary-list {{ display:grid; gap:10px; }}
    #glossary.panel.active {{ padding-bottom:94px; }}
    .term-item {{ position:relative; border:1px solid var(--line); border-radius:16px; background:var(--surface); box-shadow:var(--card-shadow); overflow:visible; }}
    .term-item[hidden] {{ display:none; }}
    .term-item summary {{ display:flex; gap:14px; align-items:center; justify-content:space-between; min-height:62px; padding:14px 48px 14px 18px; cursor:pointer; list-style:none; }}
    .term-item summary::-webkit-details-marker {{ display:none; }}
    .term-item summary::after {{ content:"+"; position:absolute; top:20px; right:18px; color:var(--gold); font:900 22px/1 var(--font-display); }}
    .term-item[open] summary::after {{ content:"−"; }}
    .term-heading {{ display:grid; gap:3px; min-width:0; }}
    .term-name {{ color:var(--ink); font:850 17px/1.3 var(--font-display); overflow-wrap:anywhere; }}
    .term-zh-meaning {{ color:var(--blue); font:800 13px/1.4 var(--font-display); overflow-wrap:anywhere; }}
    .term-full-name {{ color:var(--muted); font:600 13px/1.4 var(--font-display); overflow-wrap:anywhere; }}
    .term-category {{ flex:none; padding:5px 9px; border-radius:999px; color:var(--blue); background:var(--tint-blue); font:800 11px/1.2 var(--font-display); }}
    .term-body {{ position:relative; padding:14px 50px 18px 20px; border-top:1px solid var(--line); }}
    .term-body p {{ margin:7px 0; color:var(--ink-soft-2); line-height:1.72; }}
    .glossary-empty {{ padding:28px 16px; border:1px dashed var(--line); border-radius:16px; color:var(--muted); text-align:center; }}
    .term-ask-fab {{ position:fixed; right:20px; bottom:20px; right:max(20px,env(safe-area-inset-right)); bottom:max(20px,env(safe-area-inset-bottom)); z-index:120; display:grid; place-items:center; width:58px; height:58px; border:1px solid var(--line); border:1px solid color-mix(in srgb,var(--white) 36%,transparent); border-radius:50%; background:linear-gradient(145deg,var(--blue),var(--ink)); color:var(--white); box-shadow:0 16px 38px rgba(20,28,45,.28); box-shadow:0 16px 38px color-mix(in srgb,var(--ink) 28%,transparent); cursor:pointer; font:900 24px/1 var(--font-display); transition:transform .2s ease,box-shadow .2s ease; }}
    .term-ask-fab:hover {{ transform:translateY(-3px) scale(1.03); box-shadow:0 20px 44px color-mix(in srgb,var(--ink) 34%,transparent); }}
    .notes-guide {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:18px 0; }}
    .notes-guide div {{ display:flex; gap:10px; align-items:center; min-height:56px; padding:12px 14px; border:1px solid var(--line); border-radius:14px; background:var(--surface); }}
    .notes-guide strong {{ display:grid; place-items:center; flex:none; width:28px; height:28px; border-radius:50%; background:var(--ink); color:var(--white); font:800 13px/1 var(--font-display); }}
    .notes-guide span {{ color:var(--ink-soft-2); font:700 13px/1.4 var(--font-display); }}
    .notes-toolbar {{ display:flex; flex-wrap:wrap; gap:9px; align-items:center; margin:18px 0 10px; }}
    .note-search {{ flex:1 1 260px; min-width:0; min-height:46px; padding:11px 15px; border:1px solid var(--line); border-radius:13px; background:var(--surface-strong); color:var(--ink); font:600 14px/1.4 var(--font-display); }}
    .note-search:focus {{ outline:3px solid var(--tint-blue); border-color:var(--blue); }}
    .note-tool {{ display:inline-flex; align-items:center; justify-content:center; min-height:44px; padding:10px 13px; border:1px solid var(--line); border-radius:12px; background:var(--surface); color:var(--ink); cursor:pointer; font:750 12px/1.25 var(--font-display); }}
    .note-tool.primary {{ border-color:var(--blue); background:var(--blue); color:var(--white); }}
    .note-import {{ position:relative; }}
    .notes-meta {{ display:flex; gap:12px; justify-content:space-between; margin:10px 0 16px; color:var(--muted); font:650 12px/1.5 var(--font-display); }}
    .notes-list {{ display:grid; gap:11px; min-height:120px; }}
    .notes-empty {{ display:grid; gap:7px; place-items:center; padding:36px 20px; border:1px dashed var(--line); border-radius:18px; color:var(--muted); text-align:center; }}
    .notes-empty strong {{ color:var(--ink); font:850 18px/1.3 var(--font-display); }}
    .personal-note-card {{ border:1px solid var(--line); border-radius:16px; background:var(--surface); box-shadow:var(--card-shadow); overflow:hidden; }}
    .personal-note-card[hidden] {{ display:none; }}
    .personal-note-card summary {{ display:grid; gap:7px; min-height:64px; padding:15px 48px 15px 18px; cursor:pointer; list-style:none; position:relative; }}
    .personal-note-card summary::-webkit-details-marker {{ display:none; }}
    .personal-note-card summary::after {{ content:"+"; position:absolute; top:21px; right:18px; color:var(--gold); font:900 22px/1 var(--font-display); }}
    .personal-note-card[open] summary::after {{ content:"−"; }}
    .personal-note-title {{ color:var(--ink); font:850 17px/1.35 var(--font-display); }}
    .personal-note-meta {{ display:flex; flex-wrap:wrap; gap:7px; align-items:center; color:var(--muted); font:650 11px/1.35 var(--font-display); }}
    .personal-note-tag {{ padding:4px 8px; border-radius:999px; background:var(--tint-blue); color:var(--blue); }}
    .personal-note-body {{ display:grid; gap:10px; padding:16px 18px 18px; border-top:1px solid var(--line); }}
    .personal-note-section {{ margin:0; color:var(--ink-soft-2); line-height:1.72; white-space:pre-wrap; overflow-wrap:anywhere; }}
    .personal-note-source {{ color:var(--muted); font:650 11px/1.45 var(--font-display); }}
    .personal-note-actions {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:4px; }}
    .personal-note-actions button {{ min-height:38px; padding:8px 11px; border:1px solid var(--line); border-radius:10px; background:var(--surface-strong); color:var(--ink); cursor:pointer; font:700 12px/1.2 var(--font-display); }}
    .personal-note-actions .note-delete {{ color:var(--red); }}
    .note-capture-btn {{ position:absolute; right:42px; bottom:8px; z-index:4; display:grid; place-items:center; width:28px; height:28px; padding:0; border:1px solid var(--line); border-radius:50%; background:var(--white); color:var(--muted); cursor:pointer; font:800 15px/1 var(--font-display); opacity:0; transition:opacity .2s,transform .2s,background .2s; }}
    [data-note-ready]:hover > .note-capture-btn {{ opacity:.72; }}
    .note-capture-btn:hover {{ opacity:1 !important; transform:translateY(-1px); background:var(--gold); color:var(--white); border-color:var(--gold); }}
    .note-capture-btn.saved {{ opacity:.92; background:var(--green); color:var(--white); border-color:var(--green); }}
    .note-overlay {{ display:none; position:fixed; inset:0; z-index:220; padding:18px; background:rgba(17,24,39,.48); backdrop-filter:blur(4px); align-items:center; justify-content:center; }}
    .note-overlay.active {{ display:flex; }}
    .note-popover {{ width:min(680px,100%); max-height:min(90vh,820px); overflow-y:auto; padding:24px; border:1px solid var(--line); border-radius:22px; background:var(--surface-strong); color:var(--ink); box-shadow:0 28px 90px rgba(12,20,34,.32); }}
    .note-dialog-title {{ margin:0 0 7px; font:900 24px/1.25 var(--font-display); }}
    .note-dialog-context {{ margin:0 0 14px; color:var(--muted); line-height:1.6; }}
    .note-source-preview {{ max-height:112px; overflow:auto; margin:12px 0; padding:12px 14px; border:1px solid var(--line); border-radius:12px; background:var(--surface); color:var(--ink-soft-2); font:13px/1.58 var(--font-display); white-space:pre-wrap; }}
    .note-popover label {{ display:block; margin:13px 0 6px; color:var(--ink); font:800 13px/1.3 var(--font-display); }}
    .note-popover input,.note-popover textarea {{ width:100%; padding:12px 14px; border:1px solid var(--line); border-radius:12px; background:var(--surface); color:var(--ink); font:14px/1.6 var(--font-body); }}
    .note-popover textarea {{ min-height:92px; resize:vertical; }}
    #noteInsightInput,#noteActionInput,#notePersonalInput {{ min-height:72px; }}
    .note-dialog-actions {{ display:flex; flex-wrap:wrap; gap:9px; margin-top:16px; }}
    .note-dialog-actions button {{ min-height:44px; padding:10px 14px; border:1px solid var(--line); border-radius:11px; background:var(--surface); color:var(--ink); cursor:pointer; font:750 13px/1.25 var(--font-display); }}
    .note-dialog-actions .note-save {{ border-color:var(--blue); background:var(--blue); color:var(--white); }}
    .rules li {{ position:relative; }}
    .content-stream {{ height:auto; max-height:none; overflow:visible; touch-action:pan-y; }}
    .assessment-shell {{ margin-top:20px; padding:24px; border:1px solid var(--line); border-radius:22px; background:var(--surface-strong); box-shadow:var(--card-shadow); }}
    .assessment-steps {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-bottom:22px; }}
    .assessment-steps div {{ display:flex; gap:10px; align-items:center; padding:12px 14px; border:1px solid var(--line); border-radius:14px; background:var(--surface); }}
    .assessment-steps strong {{ display:grid; place-items:center; flex:none; width:28px; height:28px; border-radius:50%; color:var(--white); background:var(--ink); font:800 13px/1 var(--font-display); }}
    .assessment-steps span {{ color:var(--ink-soft-2); font:750 13px/1.45 var(--font-display); }}
    .assessment-scope {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:0 0 16px; padding:0; border:0; }}
    .assessment-scope legend {{ width:100%; margin-bottom:10px; color:var(--ink); font:850 14px/1.4 var(--font-display); }}
    .assessment-scope label {{ position:relative; display:grid; gap:4px; min-height:86px; padding:15px 15px 15px 44px; border:1px solid var(--line); border-radius:15px; background:var(--surface); cursor:pointer; }}
    .assessment-scope input {{ position:absolute; top:18px; left:16px; width:17px; height:17px; accent-color:var(--blue); }}
    .assessment-scope span {{ font:850 15px/1.35 var(--font-display); }}
    .assessment-scope small {{ color:var(--muted); font:12px/1.45 var(--font-display); }}
    .assessment-field {{ display:grid; gap:7px; margin:14px 0; }}
    .assessment-field label,.assessment-settings label,.mistake-import-box label {{ color:var(--ink); font:800 13px/1.4 var(--font-display); }}
    .assessment-field select,.assessment-field textarea,.assessment-settings select,.assessment-preview textarea,.mistake-import-box textarea,.mistake-toolbar input,.mistake-toolbar select {{ width:100%; min-height:46px; padding:10px 12px; border:1px solid var(--line); border-radius:12px; color:var(--ink); background:var(--surface); font:14px/1.55 var(--font-display); }}
    .assessment-field textarea {{ min-height:100px; resize:vertical; }}
    .assessment-settings {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:15px 0; }}
    .assessment-settings label {{ display:grid; gap:7px; }}
    .assessment-copy {{ width:100%; min-height:50px; margin-top:4px; border:0; border-radius:14px; color:var(--white); background:var(--blue); cursor:pointer; font:850 15px/1.4 var(--font-display); }}
    .assessment-preview {{ margin-top:12px; border:1px solid var(--line); border-radius:13px; background:var(--surface); }}
    .assessment-preview summary {{ padding:12px 14px; cursor:pointer; font:800 13px/1.4 var(--font-display); }}
    .assessment-preview textarea {{ min-height:220px; margin:0 12px 12px; width:calc(100% - 24px); resize:vertical; }}
    .assessment-boundary {{ margin:12px 0 0; color:var(--muted); font:12px/1.6 var(--font-display); }}
    .mistake-book {{ margin-top:30px; padding-top:28px; border-top:1px solid var(--line); }}
    .mistake-book-heading {{ display:flex; align-items:flex-end; justify-content:space-between; gap:16px; }}
    .mistake-book-heading h2 {{ margin:2px 0 0; font:900 28px/1.2 var(--font-display); }}
    .section-kicker {{ margin:0; color:var(--gold); font:800 12px/1.3 var(--font-display); letter-spacing:.06em; }}
    .mistake-book-heading > span {{ padding:7px 11px; border-radius:999px; color:var(--blue); background:var(--tint-accent); font:800 12px/1 var(--font-display); }}
    .mistake-book-lead {{ color:var(--ink-soft-2); line-height:1.7; }}
    .mistake-import-box {{ display:grid; gap:8px; margin:18px 0; padding:18px; border:1px solid var(--line); border-radius:16px; background:var(--surface); }}
    .mistake-import-box textarea {{ min-height:120px; resize:vertical; }}
    .mistake-import-box button,.mistake-toolbar button,.mistake-file-import,.mistake-action {{ min-height:42px; padding:9px 13px; border:1px solid var(--line); border-radius:11px; color:var(--ink); background:var(--surface); cursor:pointer; font:780 12px/1.35 var(--font-display); }}
    .mistake-import-box button {{ border-color:var(--blue); color:var(--white); background:var(--blue); }}
    .mistake-toolbar {{ display:grid; grid-template-columns:minmax(180px,1.3fr) minmax(130px,.7fr) auto auto auto; gap:8px; align-items:center; }}
    .mistake-file-import {{ display:grid; place-items:center; }}
    .mistake-storage {{ margin:10px 0 14px; color:var(--muted); font:12px/1.5 var(--font-display); }}
    .mistake-list {{ display:grid; gap:10px; min-height:110px; }}
    .mistake-empty {{ display:grid; gap:6px; place-items:center; padding:30px 18px; border:1px dashed var(--line); border-radius:16px; color:var(--muted); text-align:center; }}
    .mistake-empty strong {{ color:var(--ink); font:850 17px/1.3 var(--font-display); }}
    .mistake-card {{ border:1px solid var(--line); border-radius:15px; background:var(--surface); overflow:hidden; }}
    .mistake-card summary {{ display:grid; gap:6px; padding:15px 16px; cursor:pointer; }}
    .mistake-question {{ color:var(--ink); font:850 15px/1.5 var(--font-display); }}
    .mistake-meta {{ display:flex; flex-wrap:wrap; gap:7px; color:var(--muted); font:12px/1.4 var(--font-display); }}
    .mistake-status {{ padding:3px 8px; border-radius:999px; color:var(--blue); background:var(--tint-accent); }}
    .mistake-body {{ display:grid; gap:10px; padding:0 16px 16px; color:var(--ink-soft-2); line-height:1.65; }}
    .mistake-body p {{ margin:0; }}
    .mistake-actions {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:4px; }}
    .mistake-action.delete {{ color:var(--red); }}
    .table-wrap {{ overflow-x:auto; }}
    @media (max-width:880px) {{ .tabs {{ grid-template-columns:repeat(2,1fr); }} .ch-explorer {{ grid-template-columns:1fr; }} .ch-nav {{ position:static; grid-template-columns:repeat(3,1fr); }} .assessment-scope,.assessment-settings {{ grid-template-columns:1fr; }} .mistake-toolbar {{ grid-template-columns:1fr 1fr; }} }}
    @media (hover:none) {{ .note-capture-btn {{ right:58px; width:44px; height:44px; opacity:.78; }} }}
    @media (max-width:520px) {{ .tabs {{ grid-template-columns:1fr; }} .ch-nav {{ grid-template-columns:repeat(2,1fr); }} .ch-view {{ padding:20px 16px; }} .chapter-conclusion summary {{ padding-left:14px; }} .glossary-toolbar {{ align-items:stretch; flex-direction:column; }} .glossary-count {{ align-self:flex-end; }} .term-item summary {{ align-items:flex-start; flex-direction:column; }} .term-category {{ margin-top:2px; }} .term-ask-fab {{ width:54px; height:54px; right:max(16px,env(safe-area-inset-right)); bottom:max(16px,env(safe-area-inset-bottom)); }} .assessment-shell {{ padding:18px 14px; }} .assessment-steps,.mistake-toolbar {{ grid-template-columns:1fr; }} .mistake-book-heading {{ align-items:flex-start; flex-direction:column; }} .notes-guide {{ grid-template-columns:1fr; }} .notes-toolbar {{ align-items:stretch; flex-direction:column; }} .note-search,.note-tool {{ width:100%; }} .notes-meta {{ align-items:flex-start; flex-direction:column; }} .note-overlay {{ align-items:flex-end; padding:0; }} .note-popover {{ max-height:92vh; padding:20px 16px calc(18px + env(safe-area-inset-bottom)); border-radius:22px 22px 0 0; }} }}
    """


@localized
def markdown_output(data: dict, modules: list[tuple[str, str, str]]) -> str:
    hero = data['hero']
    depth_label = t('快速了解') if data['meta']['learningDepth'] == 'quick' else t('系统学习')
    lines = [f"# {hero['title']}", '', f"{t('**学习深度：** ')}{depth_label}", '', hero['lede'], '', f"{t('**一句话总论：** ')}{hero['thesis']}", '']
    if data['meta']['mode'] == 'overview':
        lines.extend([t('## 核心框架'), ''])
        for item in ordered_frameworks(data['frameworks']):
            lines.extend([f"### {item['name']}", '', item['oneLine'], '', f"{t('适用：')}{item['when']}", f"{t('出处：')}{item['source']}", ''])
        lines.extend([t('## 内容导学'), ''])
        for item in data['contentUnits']:
            lines.extend([f"### {item['label']} {item['title']}", '', item['core'], '', t('关键框架：') + '、'.join(item.get('frameworks', [])), '', *[f'- {x}' for x in item.get('takeaways', [])], f"{t('出处：')}{item['source']}", ''])
            for conclusion in item.get('conclusions', []):
                lines.extend([f"#### {conclusion['title']}", '', conclusion['summary'], '', *[f'- {point}' for point in conclusion.get('points', [])], f"{t('出处：')}{conclusion['source']}", ''])
        lines.extend([t('## 术语大全'), ''])
        glossary_unit_labels = {item['id']: f"{item['label']}·{item['title']}" for item in data['contentUnits']}
        for item in ordered_glossary(data['glossary']):
            full_name = f"｜{item['fullName']}" if item.get('fullName') else ''
            meaning_lines = [f"{t('中文含义：')}{item['zhMeaning']}"] if item.get('zhMeaning') and LOCALE.get() == 'zh-CN' else []
            unit_text = '、'.join((glossary_unit_labels.get(unit_id, unit_id) for unit_id in item.get('units', [])))
            lines.extend([f"### {item['term']}{full_name}", '', f"{t('分类：')}{localized_enum(item['category'])}", *meaning_lines, f"{t('通俗定义：')}{item['definition']}", f"{t('材料语境：')}{item['context']}", f"{t('相关术语：')}{'、'.join(item.get('related', []))}", f"{t('涉及单元：')}{unit_text}", f"{t('出处：')}{item['source']}", ''])
        lines.extend([t('## 行动规则'), ''])
        for item in data['decisionRules']:
            lines.append(f"{t('- 当 ')}{item['when']} → {item['do']}{t('；因为 ')}{item['because']}。（{item['source']}）")
        lines.extend(['', t('## 学习自检'), '', t('HTML 页面不会平铺固定题目。请选择综合全部、指定章节或自定义要求，复制口令到材料对话中，由 AI 基于知识库逐题测验。测验结束后可将标准错题记录导回 HTML 的本地错题本。'), '', t('### 自检考点'), ''])
        unit_labels = {item['id']: f"{item['label']}·{item['title']}" for item in data['contentUnits']}
        for item in data['assessment']['focusAreas']:
            lines.extend([f"- **{item['title']}**｜{unit_labels.get(item['unitId'], item['unitId'])}{t('｜能力：')}{', '.join((localized_enum(x) for x in item['abilities']))}{t('｜出处：')}{item['source']}"])
        lines.extend(['', t('错题只保存在 HTML 所在浏览器的本地存储中；请定期导出 JSON 备份。'), ''])
    else:
        for section in ordered_sections(data['sections']):
            lines.extend([f"## {section['title']}", '', section['lead'], ''])
            for item in section.get('notes', []):
                lines.extend([f"### {item.get('title', t('要点'))}", '', item.get('body', ''), f"{t('出处：')}{item.get('source', '')}", ''])
            lines.extend(markdown_signature(section))
    lines.extend([t('## 我的笔记'), '', t('个人笔记保存在 HTML 所在浏览器的本地存储中，不写入这份静态 Markdown。可在网页中导出 Markdown，或用 JSON 备份和迁移。'), ''])
    footer = data.get('footer')
    if footer:
        lines.extend([t('## 页面说明'), '', footer, ''])
    return '\n'.join(lines).rstrip() + '\n' + relations_markdown(data)


@localized
def render(data: dict, output: Path, markdown: Path | None) -> None:
    validate(data)
    skill_root = Path(__file__).resolve().parent.parent
    base = (skill_root / 'templates' / 'base.html').read_text(encoding='utf-8')
    base = translate_static(base, LOCALE.get())
    base = base.replace('<script id="pageData"', '{{extensions_markup}}\n<script id="pageData"')
    themes = '\n\n'.join(((skill_root / 'templates' / 'themes' / f'{name}.css').read_text(encoding='utf-8') for name in THEMES))
    mode = data['meta']['mode']
    if mode in {'topic', 'unit'}:
        data = {**data, 'sections': ordered_sections(data['sections'])}
    elif mode == 'overview':
        data = {**data, 'frameworks': ordered_frameworks(data['frameworks']), 'glossary': ordered_glossary(data['glossary'])}
    modules = overview_modules(data) if mode == 'overview' else render_sections(data['sections'])
    modules.append(('notes', t('我的笔记'), render_personal_notes()))
    tabs = ''.join((f'''<button class="tab" id="tab-{esc(module_id)}" type="button" role="tab" data-panel="{esc(module_id)}" aria-controls="{esc(module_id)}" aria-selected="{('true' if index == 0 else 'false')}" tabindex="{(0 if index == 0 else -1)}">{esc(label)}</button>''' for index, (module_id, label, _) in enumerate(modules)))
    panels = ''.join((f'''<section class="panel{(' active' if index == 0 else '')}" id="{esc(module_id)}" role="tabpanel" aria-labelledby="tab-{esc(module_id)}" tabindex="0">{body}</section>''' for index, (module_id, _, body) in enumerate(modules)))
    page_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'), sort_keys=True).replace('<', '\\u003c')
    meta = data['meta']
    mode_title = {'overview': t('材料概览'), 'topic': meta.get('topic', t('主题学习')), 'unit': meta.get('unit', t('单元深读'))}[mode]
    replacements = {'{{lang}}': LOCALE.get(), '{{title}}': esc(f"{meta['title']}｜{mode_title}"), '{{theme_style}}': themes, '{{theme_name}}': meta.get('initialTheme', 'warm-paper'), '{{body_mode}}': mode, '{{hero}}': render_hero(data['hero']), '{{learning_depth_banner}}': render_learning_depth_banner(meta), '{{tabs}}': tabs, '{{panels}}': panels, '{{footer_note}}': esc(data.get('footer', f"{t('依据“')}{meta['title']}{t('”材料知识库整理；材料原意与页面改写均保留出处。')}")), '{{component_styles}}': component_styles(len(modules)) + (skill_root / 'templates/extensions.css').read_text(encoding='utf-8'), '{{component_scripts}}': (skill_root / 'templates/extensions.js').read_text(encoding='utf-8'), '{{page_data}}': page_json}
    replacements['{{extensions_markup}}'] = extension_markup(data)
    replacements['{{component_scripts}}'] = (skill_root / 'templates/graph-studio.js').read_text(encoding='utf-8') + '\n' + replacements['{{component_scripts}}']
    from methodology_ui import overview_markup, content_sources
    if mode == 'overview':
        source_markup = content_sources(data['contentUnits'][0], meta.get('language', 'zh-CN'))
        replacements['{{panels}}'] = replacements['{{panels}}'].replace('<button class="ch-send"', source_markup + '<button class="ch-send"', 1)
        replacements['{{extensions_markup}}'] += overview_markup(data)
        replacements['{{component_styles}}'] += (skill_root / 'templates/methodology.css').read_text(encoding='utf-8')
        replacements['{{component_scripts}}'] += '\n' + (skill_root / 'templates/methodology.js').read_text(encoding='utf-8')
    replacements['{{component_styles}}'] += (skill_root / 'templates/graph-studio.css').read_text(encoding='utf-8')
    leftovers = sorted(set(re.findall('\\{\\{[^{}]+\\}\\}', base)))
    unknown = set(leftovers) - set(replacements)
    if unknown:
        raise ValueError(t('模板仍有未替换占位符：') + ', '.join(sorted(unknown)))
    # Only substitute the original template. Material may legitimately contain {{...}}.
    base = re.sub(r'\{\{[^{}]+\}\}', lambda match: replacements[match.group()], base)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(base, encoding='utf-8')
    if markdown:
        markdown.parent.mkdir(parents=True, exist_ok=True)
        markdown.write_text(markdown_output(data, modules), encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a deterministic knowledge learning page")
    parser.add_argument("content_json", type=Path)
    parser.add_argument("--output", "-o", type=Path, required=True)
    parser.add_argument("--markdown", "-m", type=Path)
    parser.add_argument("--knowledge-base", "-k", type=Path)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--legacy", action="store_true", help="Explicitly re-render an old page without v0.5 delivery requirements; never use for new overviews")
    args = parser.parse_args()
    try:
        content_json = args.content_json.resolve()
        data = json.loads(content_json.read_text(encoding="utf-8"))
        validate(data)
        exports = {}
        if data['meta']['mode'] == 'overview' and not args.legacy:
            from verify_coverage import resolve_kb_dir
            from delivery import check_canonical
            kb = resolve_kb_dir(content_json, data, args.knowledge_base)
            exports = check_canonical(data, kb)
        if 'methodology' in data:
            from verify_coverage import resolve_kb_dir
            from methodology import validate as validate_methodology
            kb = resolve_kb_dir(content_json, data, args.knowledge_base)
            validate_methodology(data['methodology'], data, kb)
            if json.loads((kb / 'methodology.json').read_text(encoding='utf-8')) != data['methodology']:
                raise ValueError('Embedded methodology differs from methodology.json; bind again')
        if 'methodLibrary' in data:
            from verify_coverage import resolve_kb_dir
            kb = resolve_kb_dir(content_json, data, args.knowledge_base)
            validate_library(data['methodLibrary'], kb)
            if read_methods(kb / 'methods.json') != data['methodLibrary']:
                raise ValueError('Embedded methods differ from knowledge-base methods.json; bind again')
        coverage_errors = verify_coverage(content_json, args.knowledge_base)
        if coverage_errors:
            raise ValueError("全量覆盖与出处真实性校验失败：\n- " + "\n- ".join(coverage_errors))
        if not args.check_only:
            if exports:
                from delivery import export_readable, verify_readable
                export_readable(kb, exports)
                verify_readable(kb, exports)
            render(data, args.output, args.markdown)
            if args.markdown and 'methodology' in data:
                from methodology import markdown as methodology_markdown
                with args.markdown.open('a', encoding='utf-8') as stream:
                    stream.write('\n' + methodology_markdown(data['methodology']))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if args.check_only:
        print("✅ 内容契约校验通过")
    else:
        print(f"✅ HTML -> {args.output}")
        if args.markdown:
            print(f"✅ Markdown -> {args.markdown}")


if __name__ == "__main__":
    main()
