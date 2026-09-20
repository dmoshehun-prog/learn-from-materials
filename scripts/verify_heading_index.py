"""Check displayed PDF heading paths against a reviewed index and source text.

This is a structural gate. It verifies literal headings, physical page ranges and
the evidence snippets used to build the index; it cannot judge whether a claim's
interpretation is supported by the cited passage.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMA = "learn-from-materials/source-heading-index-v1"
PAGE_RANGE = re.compile(r"PDF\s*(?:第\s*(\d+)(?:\s*[–—-]\s*(\d+))?\s*页|pp?\.\s*(\d+)(?:\s*[–—-]\s*(\d+))?)", re.I)
HEADING_PATH = re.compile(r"(?:标题路径：|Heading:\s*)(.+?)(?=\s*[·•]\s*(?:原书|PDF)|$)", re.I)


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def displayed_path(citation: str) -> str | None:
    match = HEADING_PATH.search(citation)
    if match:
        return match.group(1).strip()
    # Book citations may put the exact chapter/part before the page locator.
    before_page = PAGE_RANGE.split(citation, maxsplit=1)[0]
    parts = re.split(r"\s*[·•]\s*", before_page)
    for part in reversed(parts):
        value = part.strip()
        if value and not value.lower().endswith(".pdf") and "原书第" not in value:
            return value
    return None


def validate(page: dict, kb: Path, manifest: dict, source_map: list[dict], citations: list[str], *, required: bool) -> list[str]:
    errors: list[str] = []
    pdf_names = {str(s.get("filename") or "") for s in manifest.get("sources", [])
                 if isinstance(s, dict) and str(s.get("format") or "").lower() == "pdf"}
    if not pdf_names:
        return errors
    path = kb / "source-heading-index.json"
    if not path.is_file():
        return ["缺少 source-heading-index.json：PDF 的章节标题尚未核对"] if required else []
    try:
        index = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"source-heading-index.json 无法读取：{exc}"]
    if not isinstance(index, dict) or index.get("schemaVersion") != SCHEMA or not isinstance(index.get("entries"), list):
        return [f"source-heading-index.json 必须含 schemaVersion={SCHEMA} 和 entries 数组"]
    entries: dict[tuple[str, str], dict] = {}
    pages: dict[tuple[str, int], str] = {}
    raw = (kb / "full_text.txt").read_text(encoding="utf-8") if (kb / "full_text.txt").is_file() else ""
    for block in source_map:
        if not isinstance(block, dict) or block.get("locator_type") != "pdf_page":
            continue
        name, number = Path(str(block.get("source_file") or "")).name, block.get("pdf_page")
        start, end = block.get("start_char"), block.get("end_char")
        if isinstance(number, int) and isinstance(start, int) and isinstance(end, int) and 0 <= start <= end <= len(raw):
            pages[(name, number)] = raw[start:end]
    for i, entry in enumerate(index["entries"]):
        label = f"source-heading-index.json.entries[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} 必须是对象")
            continue
        name, heading = str(entry.get("filename") or ""), str(entry.get("path") or "").strip()
        first, last, evidence_page = entry.get("pdfStart"), entry.get("pdfEnd"), entry.get("evidencePage")
        snippet, verification = str(entry.get("evidenceText") or "").strip(), entry.get("verification")
        if name not in pdf_names or not heading or (name, heading) in entries:
            errors.append(f"{label} 的 filename/path 必须有效且唯一")
            continue
        entries[(name, heading)] = entry
        known = {p for (source, p) in pages if source == name}
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in (first, last, evidence_page)) or first > last or evidence_page not in known or not set(range(first, last + 1)).issubset(known):
            errors.append(f"{label} 的 PDF 页范围或标题证据页不在 source_map 中")
            continue
        if verification == "text":
            if not snippet or compact(snippet) not in compact(pages[(name, evidence_page)]):
                errors.append(f"{label}.evidenceText 未出现在标明的 PDF 页原文中")
            leaf = re.split(r"\s*[>/]\s*", heading)[-1].strip()
            if compact(leaf) not in compact(snippet):
                errors.append(f"{label}.evidenceText 未包含标题路径的末级原文标题")
        elif verification == "visual":
            if not str(entry.get("reviewNote") or "").strip():
                errors.append(f"{label} 视觉核验必须记录 reviewNote")
        else:
            errors.append(f"{label}.verification 必须为 text 或 visual")
    for name, heading in entries:
        segments = [segment.strip() for segment in heading.split(">")]
        for depth in range(1, len(segments)):
            parent = " > ".join(segments[:depth])
            if (name, parent) not in entries:
                errors.append(f"原文标题路径缺少已核父级标题：{name} · {parent}")
            elif (all(isinstance(item.get(key), int) for item in (entries[(name, parent)], entries[(name, heading)]) for key in ("pdfStart", "pdfEnd"))
                  and (entries[(name, parent)]["pdfStart"] > entries[(name, heading)]["pdfStart"]
                       or entries[(name, parent)]["pdfEnd"] < entries[(name, heading)]["pdfEnd"])):
                errors.append(f"子标题页段超出父级标题：{name} · {heading}")
    for i, citation in enumerate(sorted(set(citations))):
        names = [name for name in pdf_names if name and name in citation]
        if len(pdf_names) == 1 and not names:
            names = list(pdf_names)
        match = PAGE_RANGE.search(citation)
        if not names:
            continue
        if not match:
            errors.append(f"页面出处[{i}] 缺少精确 PDF 页码：{citation}")
            continue
        title = displayed_path(citation)
        for name in names:
            entry = entries.get((name, title or ""))
            if entry is None:
                errors.append(f"页面出处[{i}] 的标题路径不在已核原文目录中：{citation}")
                continue
            start = int(match.group(1) or match.group(3))
            end = int(match.group(2) or match.group(4) or start)
            if (not isinstance(entry.get("pdfStart"), int) or not isinstance(entry.get("pdfEnd"), int)
                    or start > end or start < entry["pdfStart"] or end > entry["pdfEnd"]):
                errors.append(f"页面出处[{i}] 的 PDF 页码不属于该原文标题：{citation}")
    return errors
