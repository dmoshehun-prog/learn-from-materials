from __future__ import annotations

import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET

from extractor.archive_safety import ArchiveSafetyError, read_member, validate_archive
from extractor.exceptions import ExtractionError

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def _heading_prefix(style_name: str) -> str:
    match = re.search(r"(?:heading|标题)\s*([1-6])", style_name or "", re.IGNORECASE)
    return "#" * int(match.group(1)) + " " if match else ""


def _relationships(zf: zipfile.ZipFile) -> dict[str, str]:
    path = "word/_rels/document.xml.rels"
    if path not in zf.namelist():
        return {}
    root = ET.fromstring(read_member(zf, path))
    output: dict[str, str] = {}
    for node in root.iter(f"{REL}Relationship"):
        rel_id = node.get("Id", "")
        target = node.get("Target", "")
        target_mode = (node.get("TargetMode") or "").casefold()
        normalized_target = target.replace("\\", "/")
        is_external = (
            target_mode == "external"
            or normalized_target.startswith(("/", "//"))
            or re.match(r"^[A-Za-z]:", normalized_target)
            or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", normalized_target)
        )
        if rel_id and normalized_target and not is_external:
            output[rel_id] = posixpath.normpath(posixpath.join("word", normalized_target))
    return output


def _paragraph_text(paragraph: ET.Element) -> str:
    parts: list[str] = []
    for node in paragraph.iter():
        if node.tag == f"{W}t" and node.text:
            parts.append(node.text)
        elif node.tag == f"{W}tab":
            parts.append("\t")
        elif node.tag in {f"{W}br", f"{W}cr"}:
            parts.append("\n")
        elif node.tag == f"{W}footnoteReference":
            footnote_id = node.get(f"{W}id", "")
            if footnote_id and not footnote_id.startswith("-"):
                parts.append(f"[脚注{footnote_id}]")
    return "".join(parts).strip()


def _image_labels(paragraph: ET.Element, relationships: dict[str, str]) -> list[str]:
    labels: list[str] = []
    descriptions: list[str] = []
    for node in paragraph.iter():
        if node.tag.endswith("}docPr"):
            for key in ("descr", "title", "name"):
                value = (node.get(key) or "").strip()
                if value and value.casefold() not in {"picture", "image"}:
                    descriptions.append(value)
        elif node.tag == f"{A}blip":
            rel_id = node.get(f"{R}embed", "") or node.get(f"{R}link", "")
            target = relationships.get(rel_id, "")
            if target:
                descriptions.append(posixpath.basename(target))
    seen: set[str] = set()
    for value in descriptions:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            labels.append(f"[图片：{value}]")
    if not labels and any(node.tag.endswith(("}drawing", "}pict")) for node in paragraph.iter()):
        labels.append("[图片：无可用替代文字，需视觉复核]")
    return labels


def _table_lines(table: ET.Element, table_number: int) -> list[str]:
    lines = [f"[表格 {table_number}]"]
    for row in table.findall(f"./{W}tr"):
        cells: list[str] = []
        for cell in row.findall(f"./{W}tc"):
            values = [_paragraph_text(paragraph) for paragraph in cell.iter(f"{W}p")]
            cells.append(" / ".join(value for value in values if value))
        if any(cells):
            lines.append("\t".join(cells))
    return lines


def _footnote_lines(zf: zipfile.ZipFile) -> list[str]:
    path = "word/footnotes.xml"
    if path not in zf.namelist():
        return []
    root = ET.fromstring(read_member(zf, path))
    lines: list[str] = []
    for footnote in root.findall(f".//{W}footnote"):
        footnote_id = footnote.get(f"{W}id", "")
        if not footnote_id or footnote_id.startswith("-"):
            continue
        text = " ".join(
            value for value in (_paragraph_text(paragraph) for paragraph in footnote.iter(f"{W}p")) if value
        )
        if text:
            lines.append(f"[脚注{footnote_id}] {text}")
    return lines


def extract_docx_with_zipfile(docx_path: str) -> tuple[str | None, int]:
    """Extract paragraphs, tables, footnotes and image placeholders in document order."""
    try:
        with zipfile.ZipFile(docx_path) as zf:
            validate_archive(zf)
            names = set(zf.namelist())
            root = ET.fromstring(read_member(zf, "word/document.xml"))
            relationships = _relationships(zf)
            body = root.find(f".//{W}body")
            if body is None:
                return None, 0
            parts: list[str] = []
            table_number = 0
            for child in list(body):
                if child.tag == f"{W}p":
                    value = _paragraph_text(child)
                    style = child.find(f"./{W}pPr/{W}pStyle")
                    style_name = style.get(f"{W}val", "") if style is not None else ""
                    if value:
                        parts.append(_heading_prefix(style_name) + value)
                    parts.extend(_image_labels(child, relationships))
                elif child.tag == f"{W}tbl":
                    table_number += 1
                    parts.extend(_table_lines(child, table_number))
                    for paragraph in child.iter(f"{W}p"):
                        parts.extend(_image_labels(paragraph, relationships))
            footnotes = _footnote_lines(zf)
            if footnotes:
                parts.extend(["## 脚注", *footnotes])
            visual_assets = sum(1 for name in names if name.startswith("word/media/") and not name.endswith("/"))
            text = "\n".join(part for part in parts if part.strip())
            return (text if text.strip() else None), visual_assets
    except ArchiveSafetyError:
        raise
    except (zipfile.BadZipFile, KeyError, ET.ParseError, OSError):
        return None, 0


def extract_docx_with_python_docx(docx_path: str) -> str | None:
    """Compatibility fallback when a non-standard DOCX defeats the XML reader."""
    try:
        import docx
        from docx.table import Table
        from docx.text.paragraph import Paragraph

        document = docx.Document(docx_path)
        parts: list[str] = []
        table_number = 0
        for child in document.element.body.iterchildren():
            if child.tag.endswith("}p"):
                paragraph = Paragraph(child, document)
                value = paragraph.text.strip()
                if value:
                    style_name = paragraph.style.name if paragraph.style else ""
                    parts.append(_heading_prefix(style_name) + value)
            elif child.tag.endswith("}tbl"):
                table_number += 1
                parts.append(f"[表格 {table_number}]")
                table = Table(child, document)
                for row in table.rows:
                    cells = [cell.text.strip().replace("\n", " / ") for cell in row.cells]
                    if any(cells):
                        parts.append("\t".join(cells))
        return "\n".join(parts) if parts else None
    except ImportError:
        return None
    except Exception:
        return None


def extract_docx(docx_path: str) -> tuple[str, str, int]:
    print("Trying structured stdlib DOCX parser...", end=" ", flush=True)
    text, visual_assets = extract_docx_with_zipfile(docx_path)
    if text and text.strip():
        print("OK")
        return text, "zipfile-docx-structured", visual_assets

    print("FAILED")
    print("Trying python-docx compatibility fallback...", end=" ", flush=True)
    text = extract_docx_with_python_docx(docx_path)
    if text and text.strip():
        print("OK")
        return text, "python-docx-fallback", 0

    print("FAILED")
    raise ExtractionError(
        "Could not extract text from DOCX. The structured ZIP/XML parser and python-docx fallback both failed. "
        "If higher-fidelity extraction is needed, ask the user to approve installing a fixed python-docx version "
        "inside an isolated environment."
    )
