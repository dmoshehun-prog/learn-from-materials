from __future__ import annotations

import re
import posixpath
import zipfile
import xml.etree.ElementTree as ET

from extractor.archive_safety import read_member, validate_archive
from extractor.exceptions import ExtractionError


_SLIDE_PATH = re.compile(r"^ppt/slides/slide(\d+)\.xml$")
_PLACEHOLDER_NOTES = {
    "click to add notes",
    "单击此处添加备注",
    "单击添加备注",
}


def _xml_text(xml_bytes: bytes) -> list[str]:
    root = ET.fromstring(xml_bytes)
    texts: list[str] = []
    for node in root.iter():
        if node.tag.endswith("}t") and node.text and node.text.strip():
            value = node.text.strip()
            if value.casefold() not in _PLACEHOLDER_NOTES:
                texts.append(value)
    return texts


def _relationships(xml_bytes: bytes, base_dir: str) -> dict[str, str]:
    root = ET.fromstring(xml_bytes)
    output: dict[str, str] = {}
    for node in root.iter():
        if not node.tag.endswith("}Relationship"):
            continue
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
            output[rel_id] = posixpath.normpath(posixpath.join(base_dir, normalized_target))
    return output


def _ordered_slides(archive: zipfile.ZipFile, names: set[str]) -> list[str]:
    presentation = "ppt/presentation.xml"
    rels = "ppt/_rels/presentation.xml.rels"
    if presentation in names and rels in names:
        targets = _relationships(read_member(archive, rels), "ppt")
        root = ET.fromstring(read_member(archive, presentation))
        ordered: list[str] = []
        relationship_namespace = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        for node in root.iter():
            if node.tag.endswith("}sldId"):
                target = targets.get(node.get(relationship_namespace, ""), "")
                if target in names:
                    ordered.append(target)
        if ordered:
            return ordered
    return sorted(
        (name for name in names if _SLIDE_PATH.match(name)),
        key=lambda name: int(_SLIDE_PATH.match(name).group(1)),
    )


def _notes_for_slide(archive: zipfile.ZipFile, names: set[str], slide_name: str) -> str | None:
    rel_name = posixpath.join(
        posixpath.dirname(slide_name),
        "_rels",
        posixpath.basename(slide_name) + ".rels",
    )
    if rel_name in names:
        targets = _relationships(read_member(archive, rel_name), posixpath.dirname(slide_name))
        for target in targets.values():
            if target.startswith("ppt/notesSlides/") and target in names:
                return target
    match = _SLIDE_PATH.match(slide_name)
    fallback = f"ppt/notesSlides/notesSlide{match.group(1)}.xml" if match else ""
    return fallback if fallback in names else None


def extract_pptx(pptx_path: str) -> tuple[str, str, int, int]:
    """Return slide-delimited text, method, slide count and visual asset count.

    The stdlib parser preserves slide numbers and speaker notes without requiring
    PowerPoint or python-pptx. Images and charts are counted so the caller can
    flag visually dense decks for selective multimodal review.
    """
    try:
        with zipfile.ZipFile(pptx_path) as archive:
            validate_archive(archive)
            names = set(archive.namelist())
            slide_names = _ordered_slides(archive, names)
            if not slide_names:
                raise ExtractionError("演示文稿中没有可读取的幻灯片")

            parts: list[str] = []
            for slide_number, slide_name in enumerate(slide_names, start=1):
                slide_text = _xml_text(read_member(archive, slide_name))
                note_name = _notes_for_slide(archive, names, slide_name)
                note_text: list[str] = []
                if note_name:
                    note_text = _xml_text(read_member(archive, note_name))

                lines = [f"【幻灯片 {slide_number}】", *slide_text]
                if note_text:
                    lines.extend(["【演讲者备注】", *note_text])
                parts.append("\n".join(lines))

            visual_assets = sum(
                1
                for name in names
                if name.startswith("ppt/media/") or name.startswith("ppt/charts/chart")
            )
            return "\f".join(parts), "zipfile-pptx", len(slide_names), visual_assets
    except ExtractionError:
        raise
    except (zipfile.BadZipFile, KeyError, ET.ParseError, OSError) as exc:
        raise ExtractionError(f"无法读取 PPTX/PPTM：{exc}") from exc
