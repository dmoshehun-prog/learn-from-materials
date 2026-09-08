from __future__ import annotations

import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET
from urllib.parse import unquote

from extractor.archive_safety import ArchiveSafetyError, read_member, validate_archive
from extractor.parsers.html import _HTMLTextExtractor


def _ebooklib_spine_item(spine_item: object) -> tuple[str, bool]:
    """Return the item id and whether ebooklib marks it as linear reading content."""
    if isinstance(spine_item, (tuple, list)):
        item_id = str(spine_item[0]) if spine_item else ""
        linear = not (len(spine_item) > 1 and str(spine_item[1]).casefold() == "no")
        return item_id, linear
    return str(spine_item), True


def extract_with_ebooklib(epub_path: str) -> str | None:
    """Extract EPUB content in the package spine order."""
    try:
        from ebooklib import epub
        from bs4 import BeautifulSoup

        with zipfile.ZipFile(epub_path) as archive:
            validate_archive(archive)
        book = epub.read_epub(epub_path)
        parts: list[str] = []
        seen: set[str] = set()
        section_number = 0
        for spine_item in book.spine:
            item_id, is_linear = _ebooklib_spine_item(spine_item)
            if not is_linear:
                continue
            section_number += 1
            item = book.get_item_with_id(item_id)
            if item is None or item_id in seen:
                continue
            seen.add(item_id)
            soup = BeautifulSoup(item.get_content(), "html.parser")
            text = soup.get_text(separator="\n").strip()
            if text:
                parts.append(f"【EPUB 章节 {section_number}】\n{text}")
        return "\f".join(parts) if parts else None
    except ImportError:
        return None
    except ArchiveSafetyError:
        raise
    except Exception:
        return None


def _find_opf_path(zf: zipfile.ZipFile) -> str | None:
    """Locate the OPF package document from container.xml or a safe fallback."""
    try:
        root = ET.fromstring(read_member(zf, "META-INF/container.xml"))
        for node in root.iter():
            if node.tag.endswith("}rootfile") or node.tag == "rootfile":
                path = (node.get("full-path") or "").strip()
                if path:
                    return path
    except (KeyError, ET.ParseError, OSError):
        pass
    opf_files = sorted(name for name in zf.namelist() if name.lower().endswith(".opf"))
    return opf_files[0] if opf_files else None


def _spine_paths(zf: zipfile.ZipFile, opf_path: str) -> list[str] | None:
    """Resolve linear manifest IDs through spine itemrefs; return None when no spine exists."""
    root = ET.fromstring(read_member(zf, opf_path))
    opf_dir = posixpath.dirname(opf_path)
    manifest: dict[str, str] = {}
    for node in root.iter():
        if not (node.tag.endswith("}item") or node.tag == "item"):
            continue
        item_id = (node.get("id") or "").strip()
        href = unquote((node.get("href") or "").split("#", 1)[0]).strip()
        media_type = (node.get("media-type") or "").lower()
        if item_id and href and ("html" in media_type or href.lower().endswith((".xhtml", ".html", ".htm"))):
            manifest[item_id] = posixpath.normpath(posixpath.join(opf_dir, href))

    ordered: list[str] = []
    seen: set[str] = set()
    saw_spine_item = False
    for node in root.iter():
        if not (node.tag.endswith("}itemref") or node.tag == "itemref"):
            continue
        saw_spine_item = True
        if (node.get("linear") or "yes").casefold() == "no":
            continue
        item_id = (node.get("idref") or "").strip()
        target = manifest.get(item_id)
        if target and target not in seen:
            seen.add(target)
            ordered.append(target)
    return ordered if saw_spine_item else None


def extract_with_zipfile(epub_path: str) -> str | None:
    """Dependency-free EPUB extraction that follows the OPF spine reading order."""
    try:
        with zipfile.ZipFile(epub_path) as zf:
            validate_archive(zf)
            names = set(zf.namelist())
            opf_path = _find_opf_path(zf)
            spine_order = _spine_paths(zf, opf_path) if opf_path else None
            if spine_order is None:
                html_files = sorted(name for name in names if name.lower().endswith((".html", ".htm", ".xhtml")))
            else:
                html_files = [name for name in spine_order if name in names]
            if not html_files:
                return None

            parts: list[str] = []
            for section_number, name in enumerate(html_files, start=1):
                try:
                    raw = read_member(zf, name).decode("utf-8", errors="replace")
                    parser = _HTMLTextExtractor()
                    parser.feed(raw)
                    text = parser.get_text().strip()
                    if text:
                        parts.append(f"【EPUB 章节 {section_number}】\n{text}")
                except (KeyError, UnicodeError, ET.ParseError):
                    continue
            return "\f".join(parts) if parts else None
    except (zipfile.BadZipFile, OSError, ET.ParseError, KeyError):
        return None


def count_epub_chapters(epub_path: str) -> int:
    """Count actual linear reading-order entries from the EPUB spine."""
    try:
        with zipfile.ZipFile(epub_path) as zf:
            validate_archive(zf)
            opf_path = _find_opf_path(zf)
            spine_paths = _spine_paths(zf, opf_path) if opf_path else None
            return len(spine_paths) if spine_paths is not None else 0
    except (zipfile.BadZipFile, OSError, ET.ParseError, KeyError):
        return 0
