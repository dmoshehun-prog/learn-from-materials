#!/usr/bin/env python3
"""Verify knowledge-base coverage and source locators before page rendering."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

STATUS_VALUES = {"covered", "no-content", "unreadable", "duplicate"}
BLOCK_STATUS_VALUES = STATUS_VALUES | {"quick-omitted"}
REQUIRED_KB_FILES = (
    "INDEX.md",
    "coverage-audit.md",
    "coverage-audit.json",
    "metadata.json",
    "source_manifest.json",
    "source_map.json",
    "glossary.md",
    "patterns.md",
    "cheatsheet.md",
    "practice.md",
    "question-bank.json",
    "summary-ledger.json",
)
QUESTION_BANK_SCHEMA = "knowledge-learning-assistant-question-bank/v1"
QUESTION_BANK_DETECTIONS = {"none", "partial", "complete"}
QUESTION_BANK_CONFIDENCE = {"low", "medium", "high"}
QUESTION_BANK_SOURCE_KINDS = {"question-bank", "chapter-exercises", "sample-exam", "mock-exam", "answer-key"}
QUESTION_TYPES = {"single-choice", "multiple-choice", "true-false", "fill-blank", "short-answer", "case-analysis", "other"}
ANSWER_BASES = {"official", "material-derived", "unavailable"}
SUMMARY_LEDGER_SCHEMA = "knowledge-learning-assistant-summary-ledger/v1"
SUMMARY_CLAIM_KINDS = {"argument", "definition", "mechanism", "conclusion", "case", "evidence", "data", "limitation", "method", "other"}
DEPENDENCY_SCHEMA = "learn-from-materials/unit-dependency-map-v1"
PDF_RANGE = re.compile(r"PDF\s*第\s*(\d+)(?:\s*[–—-]\s*(\d+))?\s*页", re.IGNORECASE)
SLIDE_RANGE = re.compile(r"第\s*(\d+)(?:\s*[–—-]\s*(\d+))?\s*页幻灯片")
EPUB_RANGE = re.compile(r"EPUB\s*第\s*(\d+)(?:\s*[–—-]\s*(\d+))?\s*节", re.IGNORECASE)


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"无法读取 {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 无法解析 {path}: {exc}") from exc


def stable_source_key(item: dict) -> str:
    filename = Path(str(item.get("source_file") or "")).name
    kind = str(item.get("locator_type") or "document")
    field = {"pdf_page": "pdf_page", "slide": "slide", "epub_section": "epub_section"}.get(kind)
    ordinal = item.get(field) if field else 1
    return f"{filename}#{kind}:{ordinal if isinstance(ordinal, int) else 1}"


def collect_sources(value: object) -> list[str]:
    output: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "source" and isinstance(child, str) and child.strip():
                output.append(child.strip())
            else:
                output.extend(collect_sources(child))
    elif isinstance(value, list):
        for child in value:
            output.extend(collect_sources(child))
    return output


def expand_range(start: int, end: int | None) -> set[int]:
    final = end or start
    if final < start:
        return set()
    return set(range(start, final + 1))


def resolve_kb_dir(page_json: Path, data: dict, explicit: Path | None) -> Path:
    if explicit:
        return explicit.resolve()
    raw = str((data.get("meta") or {}).get("knowledgeBase") or "").strip()
    if not raw:
        raise ValueError("meta.knowledgeBase 为空，无法定位知识库")
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = page_json.parent / candidate
    candidate = candidate.resolve()
    return candidate.parent if candidate.suffix else candidate


def source_locators(source_map: list[dict]) -> dict[str, dict[str, set[int]]]:
    result: dict[str, dict[str, set[int]]] = {}
    for item in source_map:
        if not isinstance(item, dict):
            continue
        filename = Path(str(item.get("source_file") or "")).name
        if not filename:
            continue
        bucket = result.setdefault(filename, {"pdf_page": set(), "slide": set(), "epub_section": set(), "unmapped": set()})
        kind = item.get("locator_type")
        if kind == "pdf_page" and isinstance(item.get("pdf_page"), int):
            bucket["pdf_page"].add(item["pdf_page"])
        elif kind == "slide" and isinstance(item.get("slide"), int):
            bucket["slide"].add(item["slide"])
        elif kind == "epub_section" and isinstance(item.get("epub_section"), int):
            bucket["epub_section"].add(item["epub_section"])
        elif kind == "pdf_document_unmapped":
            bucket["unmapped"].add(1)
    return result


def audit_range_values(entry: dict, kind: str) -> set[int]:
    covered: set[int] = set()
    for item in entry.get("ranges", []):
        if not isinstance(item, dict) or item.get("kind") != kind:
            continue
        start = item.get("start")
        end = item.get("end", start)
        if isinstance(start, int) and isinstance(end, int):
            covered.update(expand_range(start, end))
    return covered


def validate_question_bank(bank: object, filenames: set[str], unit_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if not isinstance(bank, dict):
        return ["question-bank.json 根节点必须是对象"]
    if bank.get("schemaVersion") != QUESTION_BANK_SCHEMA:
        errors.append(f'question-bank.json.schemaVersion 必须为 "{QUESTION_BANK_SCHEMA}"')
    detection = bank.get("detection")
    if detection not in QUESTION_BANK_DETECTIONS:
        errors.append("question-bank.json.detection 只能为 none、partial、complete")
    if bank.get("confidence") not in QUESTION_BANK_CONFIDENCE:
        errors.append("question-bank.json.confidence 只能为 low、medium、high")
    sources = bank.get("sources")
    questions = bank.get("questions")
    if not isinstance(sources, list):
        errors.append("question-bank.json.sources 必须是数组")
        sources = []
    if not isinstance(questions, list):
        errors.append("question-bank.json.questions 必须是数组")
        questions = []
    if detection == "none" and (sources or questions):
        errors.append("question-bank.json detection=none 时 sources 和 questions 必须为空")
    if detection in {"partial", "complete"} and not questions:
        errors.append("question-bank.json 检测到题库时 questions 不能为空")
    for index, source in enumerate(sources):
        label = f"question-bank.json.sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label} 必须是对象")
            continue
        filename = str(source.get("filename") or "").strip()
        if not filename or filename not in filenames:
            errors.append(f"{label}.filename 必须指向 source_manifest.json 中的文件")
        if source.get("kind") not in QUESTION_BANK_SOURCE_KINDS:
            errors.append(f"{label}.kind 不合法")
        if not isinstance(source.get("source"), str) or not source["source"].strip():
            errors.append(f"{label}.source 必须填写精确出处")
    seen_ids: set[str] = set()
    for index, question in enumerate(questions):
        label = f"question-bank.json.questions[{index}]"
        if not isinstance(question, dict):
            errors.append(f"{label} 必须是对象")
            continue
        question_id = str(question.get("id") or "").strip()
        if not question_id or question_id in seen_ids:
            errors.append(f"{label}.id 必须非空且唯一")
        seen_ids.add(question_id)
        stem = str(question.get("stem") or "").strip()
        if not stem:
            errors.append(f"{label}.stem 不能为空")
        if question.get("questionType") not in QUESTION_TYPES:
            errors.append(f"{label}.questionType 不合法")
        options = question.get("options")
        if not isinstance(options, list) or any(not isinstance(item, str) for item in options):
            errors.append(f"{label}.options 必须是文本数组")
        basis = question.get("answerBasis")
        if basis not in ANSWER_BASES:
            errors.append(f"{label}.answerBasis 不合法")
        if basis in {"official", "material-derived"} and not str(question.get("answer") or "").strip():
            errors.append(f"{label} 可判分答案不能为空")
        unit_id = str(question.get("unitId") or "").strip()
        if unit_id and unit_ids and unit_id not in unit_ids:
            errors.append(f"{label}.unitId 含未知内容单元")
        points = question.get("knowledgePoints")
        if not isinstance(points, list) or not points or any(not isinstance(item, str) or not item.strip() for item in points):
            errors.append(f"{label}.knowledgePoints 必须是非空文本组成的数组")
        if not isinstance(question.get("source"), str) or not question["source"].strip():
            errors.append(f"{label}.source 必须填写精确出处")
        if not isinstance(question.get("usable"), bool):
            errors.append(f"{label}.usable 必须是布尔值")
        elif question["usable"] and basis == "unavailable":
            errors.append(f"{label} 无可用答案时不得标记 usable=true")
    return errors


def summary_ref_targets(data: dict) -> set[str]:
    targets: set[str] = set()
    for unit in data.get("contentUnits", []):
        if not isinstance(unit, dict):
            continue
        unit_id = str(unit.get("id") or "").strip()
        if not unit_id:
            continue
        targets.add(f"unit:{unit_id}:core")
        for index, _item in enumerate(unit.get("frameworks", [])):
            targets.add(f"unit:{unit_id}:framework:{index}")
        for index, _item in enumerate(unit.get("takeaways", [])):
            targets.add(f"unit:{unit_id}:takeaway:{index}")
        for conclusion_index, conclusion in enumerate(unit.get("conclusions", [])):
            if not isinstance(conclusion, dict):
                continue
            targets.add(f"unit:{unit_id}:conclusion:{conclusion_index}:summary")
            for point_index, _point in enumerate(conclusion.get("points", [])):
                targets.add(f"unit:{unit_id}:conclusion:{conclusion_index}:point:{point_index}")
    return targets


def validate_summary_ledger(ledger: object, data: dict, unit_ids: set[str], enforce_mapping: bool) -> list[str]:
    errors: list[str] = []
    if not isinstance(ledger, dict):
        return ["summary-ledger.json 根节点必须是对象"]
    if ledger.get("schemaVersion") != SUMMARY_LEDGER_SCHEMA:
        errors.append(f'summary-ledger.json.schemaVersion 必须为 "{SUMMARY_LEDGER_SCHEMA}"')
    claims = ledger.get("claims")
    exclusions = ledger.get("exclusions")
    final_check = ledger.get("finalCheck")
    if not isinstance(claims, list):
        errors.append("summary-ledger.json.claims 必须是数组")
        claims = []
    if not isinstance(exclusions, list):
        errors.append("summary-ledger.json.exclusions 必须是数组")
        exclusions = []
    if not isinstance(final_check, dict):
        errors.append("summary-ledger.json.finalCheck 必须是对象")
        final_check = {}
    if not enforce_mapping:
        return errors
    if not claims:
        errors.append("overview 的 summary-ledger.json.claims 不能为空")
    target_refs = summary_ref_targets(data)
    mapped_refs: set[str] = set()
    seen_ids: set[str] = set()
    source_orders: list[int] = []
    for index, claim in enumerate(claims):
        label = f"summary-ledger.json.claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{label} 必须是对象")
            continue
        claim_id = str(claim.get("id") or "").strip()
        if not claim_id or claim_id in seen_ids:
            errors.append(f"{label}.id 必须非空且唯一")
        seen_ids.add(claim_id)
        unit_id = str(claim.get("unitId") or "").strip()
        if unit_id not in unit_ids:
            errors.append(f"{label}.unitId 含未知内容单元")
        source_order = claim.get("sourceOrder")
        if not isinstance(source_order, int) or isinstance(source_order, bool) or source_order < 1:
            errors.append(f"{label}.sourceOrder 必须是从 1 开始的正整数")
        else:
            source_orders.append(source_order)
        if claim.get("kind") not in SUMMARY_CLAIM_KINDS:
            errors.append(f"{label}.kind 不合法")
        for field in ("text", "source"):
            if not isinstance(claim.get(field), str) or not claim[field].strip():
                errors.append(f"{label}.{field} 必须是非空文本")
        refs = claim.get("summaryRefs")
        if not isinstance(refs, list) or not refs or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            errors.append(f"{label}.summaryRefs 必须是非空文本数组")
            continue
        for ref in refs:
            if ref not in target_refs:
                errors.append(f"{label}.summaryRefs 含不存在的总结引用：{ref}")
            elif unit_id and not ref.startswith(f"unit:{unit_id}:"):
                errors.append(f"{label}.summaryRefs 必须映射到同一内容单元：{ref}")
            else:
                mapped_refs.add(ref)
    if len(source_orders) == len(claims) and sorted(source_orders) != list(range(1, len(claims) + 1)):
        errors.append(f"summary-ledger.json.claims.sourceOrder 必须唯一且连续覆盖 1–{len(claims)}")
    for index, item in enumerate(exclusions):
        label = f"summary-ledger.json.exclusions[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} 必须是对象")
            continue
        for field in ("source", "reason"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{label}.{field} 必须是非空文本")
    missing_refs = sorted(target_refs - mapped_refs)
    if missing_refs:
        errors.append("内容总结存在无材料主张支撑的项目：" + "、".join(missing_refs))
    for field in ("sourceToSummaryComplete", "summaryToSourceComplete", "secondPassCompleted"):
        if final_check.get(field) is not True:
            errors.append(f"summary-ledger.json.finalCheck.{field} 必须为 true")
    for field in ("missingClaimIds", "orphanSummaryRefs"):
        value = final_check.get(field)
        if not isinstance(value, list) or value:
            errors.append(f"summary-ledger.json.finalCheck.{field} 必须是空数组")
    return errors


def verify(page_json: Path, kb_dir: Path | None = None) -> list[str]:
    errors: list[str] = []
    data = load_json(page_json)
    if not isinstance(data, dict):
        return ["page.json 根节点必须是对象"]
    resolved_kb = resolve_kb_dir(page_json, data, kb_dir)
    if (data.get("meta") or {}).get("learningDepth") == "quick":
        from verify_quick import verify_quick
        return verify_quick(data, resolved_kb)

    for name in REQUIRED_KB_FILES:
        if not (resolved_kb / name).is_file():
            errors.append(f"知识库缺少必需文件：{name}")
    units_dir = resolved_kb / "units"
    if not units_dir.is_dir() or not any(units_dir.glob("*.md")):
        errors.append("知识库缺少 units/*.md")
    if errors:
        return errors

    manifest = load_json(resolved_kb / "source_manifest.json")
    source_map = load_json(resolved_kb / "source_map.json")
    audit = load_json(resolved_kb / "coverage-audit.json")
    question_bank = load_json(resolved_kb / "question-bank.json")
    summary_ledger = load_json(resolved_kb / "summary-ledger.json")
    audit_md = (resolved_kb / "coverage-audit.md").read_text(encoding="utf-8")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("sources"), list):
        errors.append("source_manifest.json.sources 必须是数组")
        return errors
    if not isinstance(source_map, list):
        errors.append("source_map.json 必须是数组")
        return errors
    if not isinstance(audit, dict) or audit.get("schemaVersion") not in {"1.0", "1.1"}:
        errors.append('coverage-audit.json.schemaVersion 必须为 "1.0" 或 "1.1"')
        return errors
    if not isinstance(audit.get("sources"), list):
        errors.append("coverage-audit.json.sources 必须是数组")
        return errors

    enhanced_manifest = manifest.get("schemaVersion") == "2.0"
    if enhanced_manifest:
        for name in ("material-security-report.json", "performance-report.json", "reverse-coverage-report.json", "unit-dependency-map.json"):
            if not (resolved_kb / name).is_file():
                errors.append(f"增强知识库缺少必需文件：{name}")
        dependency_path = resolved_kb / "unit-dependency-map.json"
        if dependency_path.is_file():
            dependency = load_json(dependency_path)
            if not isinstance(dependency, dict) or dependency.get("schemaVersion") != DEPENDENCY_SCHEMA:
                errors.append(f'unit-dependency-map.json.schemaVersion 必须为 "{DEPENDENCY_SCHEMA}"')
            else:
                page_id = str((data.get("meta") or {}).get("pageId") or "")
                if not page_id or dependency.get("pageId") != page_id:
                    errors.append("unit-dependency-map.json.pageId 必须与 page.json.meta.pageId 一致")
                entries = dependency.get("entries")
                expected_keys = {stable_source_key(item) for item in source_map if isinstance(item, dict)}
                if not isinstance(entries, list):
                    errors.append("unit-dependency-map.json.entries 必须是数组")
                else:
                    actual_keys = {str(item.get("sourceKey") or "") for item in entries if isinstance(item, dict)}
                    if expected_keys != actual_keys:
                        errors.append("unit-dependency-map.json 必须逐项覆盖 source_map 的稳定来源键")
        if audit.get("schemaVersion") != "1.1":
            errors.append('source_manifest 2.0 要求 coverage-audit.json.schemaVersion 为 "1.1"')
        source_ids = {
            str(item.get("source_id") or "").strip()
            for item in source_map if isinstance(item, dict) and str(item.get("source_id") or "").strip()
        }
        if len(source_ids) != len(source_map):
            errors.append("source_manifest 2.0 要求 source_map 每项都有唯一 source_id")
        for index, item in enumerate(source_map):
            if not isinstance(item, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(item.get("content_sha256") or "")):
                errors.append(f"source_map[{index}].content_sha256 必须是 SHA-256")
        blocks = audit.get("sourceBlocks")
        if not isinstance(blocks, list):
            errors.append("coverage-audit 1.1 必须包含 sourceBlocks 数组")
            blocks = []
        block_ids: set[str] = set()
        for index, block in enumerate(blocks):
            label = f"coverage-audit.json.sourceBlocks[{index}]"
            if not isinstance(block, dict):
                errors.append(f"{label} 必须是对象")
                continue
            source_id = str(block.get("sourceId") or "").strip()
            if not source_id or source_id in block_ids:
                errors.append(f"{label}.sourceId 必须非空且唯一")
            block_ids.add(source_id)
            status = block.get("status")
            if status not in BLOCK_STATUS_VALUES:
                errors.append(f"{label}.status 不合法")
            units = block.get("mappedUnits")
            claims = block.get("mappedClaims")
            if not isinstance(units, list) or not isinstance(claims, list):
                errors.append(f"{label} 必须包含 mappedUnits 与 mappedClaims 数组")
            elif status == "covered" and not (units or claims):
                errors.append(f"{label} 标为 covered 时必须映射到单元或主张")
            if status == "quick-omitted" and (data.get("meta") or {}).get("learningDepth") != "quick":
                errors.append(f"{label} 只有快速了解模式可以使用 quick-omitted")
        audit_depth = audit.get("learningDepth", "systematic")
        page_depth = (data.get("meta") or {}).get("learningDepth", "systematic")
        if audit_depth not in {"quick", "systematic"} or audit_depth != page_depth:
            errors.append("coverage-audit.json.learningDepth 必须与 page.json 的学习深度一致")
        missing_blocks = sorted(source_ids - block_ids)
        unknown_blocks = sorted(block_ids - source_ids)
        if missing_blocks:
            errors.append("coverage-audit.sourceBlocks 缺少 source_id：" + "、".join(missing_blocks))
        if unknown_blocks:
            errors.append("coverage-audit.sourceBlocks 含未知 source_id：" + "、".join(unknown_blocks))
        reverse_path = resolved_kb / "reverse-coverage-report.json"
        if reverse_path.is_file():
            reverse = load_json(reverse_path)
            if not isinstance(reverse, dict) or reverse.get("passed") is not True:
                errors.append("reverse-coverage-report.json 未通过反向覆盖抽查")

    final_check = audit.get("finalCheck")
    if not isinstance(final_check, dict):
        errors.append("coverage-audit.json.finalCheck 必须是对象")
    else:
        for field in ("readToEnd", "noEarlyStop", "sourceLocatorsChecked"):
            if final_check.get(field) is not True:
                errors.append(f"coverage-audit.json.finalCheck.{field} 必须为 true")

    manifest_sources = [item for item in manifest["sources"] if isinstance(item, dict)]
    if enhanced_manifest:
        for index, item in enumerate(manifest_sources):
            for field in ("sha256", "text_sha256"):
                if not re.fullmatch(r"[0-9a-f]{64}", str(item.get(field) or "")):
                    errors.append(f"source_manifest.json.sources[{index}].{field} 必须是 SHA-256")
            if not isinstance(item.get("reused_from_cache"), bool):
                errors.append(f"source_manifest.json.sources[{index}].reused_from_cache 必须是布尔值")
    filenames = [str(item.get("filename") or "").strip() for item in manifest_sources]
    filenames = [name for name in filenames if name]
    if not filenames:
        errors.append("source_manifest.json 没有有效 filename")
        return errors
    content_units = data.get("contentUnits") if isinstance(data.get("contentUnits"), list) else []
    unit_ids = {
        str(item.get("id") or "").strip()
        for item in content_units
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }
    errors.extend(validate_question_bank(question_bank, set(filenames), unit_ids))
    errors.extend(validate_summary_ledger(
        summary_ledger,
        data,
        unit_ids,
        str((data.get("meta") or {}).get("mode") or "") == "overview",
    ))
    audit_entries = {
        str(item.get("filename") or "").strip(): item
        for item in audit["sources"]
        if isinstance(item, dict) and str(item.get("filename") or "").strip()
    }
    if len(audit_entries) != len(audit["sources"]):
        errors.append("coverage-audit.json.sources 含无文件名或重复文件名条目")

    locators = source_locators(source_map)
    page_sources = collect_sources(data)
    joined_page_sources = "\n".join(page_sources)
    source_type = str((data.get("meta") or {}).get("sourceType") or "")

    for manifest_item in manifest_sources:
        filename = str(manifest_item.get("filename") or "").strip()
        if not filename:
            continue
        entry = audit_entries.get(filename)
        if not entry:
            errors.append(f"coverage-audit.json 缺少文件：{filename}")
            continue
        if filename not in audit_md:
            errors.append(f"coverage-audit.md 未列出文件：{filename}")
        status = entry.get("status")
        if status not in STATUS_VALUES:
            errors.append(f"{filename} 的 status 必须是：{', '.join(sorted(STATUS_VALUES))}")
            continue
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            errors.append(f"{filename} 必须填写事实性 reason")
        if status == "covered":
            if not isinstance(entry.get("unitIds"), list) or not entry["unitIds"]:
                errors.append(f"{filename} 标为 covered 时必须关联非空 unitIds")
            if source_type == "mixed" and filename not in joined_page_sources:
                errors.append(f"mixed 页面没有任何出处引用已覆盖文件：{filename}")
            mapped = locators.get(filename, {"pdf_page": set(), "slide": set(), "epub_section": set(), "unmapped": set()})
            expected_pdf = mapped["pdf_page"]
            expected_slides = mapped["slide"]
            if expected_pdf:
                audited = audit_range_values(entry, "pdf_page")
                missing = sorted(expected_pdf - audited)
                extra = sorted(audited - expected_pdf)
                if missing:
                    errors.append(f"{filename} coverage audit 缺少 PDF 页：{missing}")
                if extra:
                    errors.append(f"{filename} coverage audit 声称不存在的 PDF 页：{extra}")
            elif mapped["unmapped"] and any(filename in source for source in page_sources):
                claimed = any(PDF_RANGE.search(source) for source in page_sources if filename in source)
                if claimed:
                    errors.append(f"{filename} 没有物理页映射，页面却声称了精确 PDF 页码")
            if expected_slides:
                audited = audit_range_values(entry, "slide")
                missing = sorted(expected_slides - audited)
                extra = sorted(audited - expected_slides)
                if missing:
                    errors.append(f"{filename} coverage audit 缺少幻灯片：{missing}")
                if extra:
                    errors.append(f"{filename} coverage audit 声称不存在的幻灯片：{extra}")
            expected_epub = mapped["epub_section"]
            if expected_epub:
                audited = audit_range_values(entry, "epub_section")
                missing = sorted(expected_epub - audited)
                extra = sorted(audited - expected_epub)
                if missing:
                    errors.append(f"{filename} coverage audit 缺少 EPUB 章节：{missing}")
                if extra:
                    errors.append(f"{filename} coverage audit 声称不存在的 EPUB 章节：{extra}")

    unknown_audit = sorted(set(audit_entries) - set(filenames))
    if unknown_audit:
        errors.append("coverage-audit.json 含 manifest 中不存在的文件：" + "、".join(unknown_audit))

    single_filename = filenames[0] if len(filenames) == 1 else ""
    for index, source in enumerate(page_sources):
        targets = [filename for filename in filenames if filename in source]
        if not targets and single_filename:
            targets = [single_filename]
        if source_type == "mixed" and not targets:
            errors.append(f"页面出处[{index}] 未指向 manifest 中的具体文件：{source}")
            continue
        for filename in targets:
            mapped = locators.get(filename, {"pdf_page": set(), "slide": set(), "epub_section": set(), "unmapped": set()})
            for match in PDF_RANGE.finditer(source):
                claimed = expand_range(int(match.group(1)), int(match.group(2)) if match.group(2) else None)
                if mapped["unmapped"]:
                    errors.append(f"页面出处[{index}] 对无页映射 PDF 声称精确页码：{source}")
                elif mapped["pdf_page"] and not claimed.issubset(mapped["pdf_page"]):
                    errors.append(f"页面出处[{index}] 的 PDF 页码超出 source_map：{source}")
            for match in SLIDE_RANGE.finditer(source):
                claimed = expand_range(int(match.group(1)), int(match.group(2)) if match.group(2) else None)
                if mapped["slide"] and not claimed.issubset(mapped["slide"]):
                    errors.append(f"页面出处[{index}] 的幻灯片页码超出 source_map：{source}")
            for match in EPUB_RANGE.finditer(source):
                claimed = expand_range(int(match.group(1)), int(match.group(2)) if match.group(2) else None)
                if mapped["epub_section"] and not claimed.issubset(mapped["epub_section"]):
                    errors.append(f"页面出处[{index}] 的 EPUB 章节超出 source_map：{source}")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify full-material coverage and source truth")
    parser.add_argument("page_json", type=Path)
    parser.add_argument("--knowledge-base", "-k", type=Path)
    args = parser.parse_args()
    try:
        errors = verify(args.page_json.resolve(), args.knowledge_base)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if errors:
        for error in errors:
            print(f"❌ {error}")
        raise SystemExit(1)
    print("✅ 所选学习深度的覆盖与出处校验通过")


if __name__ == "__main__":
    main()
