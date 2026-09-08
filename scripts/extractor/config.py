from __future__ import annotations
import os
from pathlib import Path

OUTPUT_DIR = Path(
    os.environ.get(
        "LEARNING_SKILL_WORKDIR",
        os.environ.get("BOOK_SKILL_WORKDIR", str(Path.cwd() / "material_learning_work")),
    )
)
OUTPUT_TEXT = OUTPUT_DIR / "full_text.txt"
OUTPUT_MARKDOWN = OUTPUT_DIR / "full_text.md"
OUTPUT_META = OUTPUT_DIR / "metadata.json"
OUTPUT_PAGE_MAP = OUTPUT_DIR / "page_map.json"
OUTPUT_SOURCE_MAP = OUTPUT_DIR / "source_map.json"
OUTPUT_SOURCE_MANIFEST = OUTPUT_DIR / "source_manifest.json"
OUTPUT_SECURITY_REPORT = OUTPUT_DIR / "material-security-report.json"
OUTPUT_PERFORMANCE_REPORT = OUTPUT_DIR / "performance-report.json"
EXTRACTION_CACHE_DIR = OUTPUT_DIR / ".extraction-cache"

EXTRACTOR_SCHEMA_VERSION = "learn-from-materials/extractor-v2"

WORDS_PER_TOKEN = 0.75  # Latin-language approximation
CJK_TOKENS_PER_CHAR = 0.90  # midpoint estimate across common modern tokenizers

TEXT_EXTENSIONS = {".txt", ".text", ".md", ".markdown", ".rst", ".adoc", ".asciidoc"}
HTML_EXTENSIONS = {".html", ".htm", ".xhtml"}
CALIBRE_EBOOK_EXTENSIONS = {".mobi", ".azw", ".azw3"}
PRESENTATION_EXTENSIONS = {".pptx", ".pptm"}
SUPPORTED_EXTENSIONS = {
    ".pdf", ".epub", ".docx", ".rtf",
    *TEXT_EXTENSIONS,
    *HTML_EXTENSIONS,
    *CALIBRE_EBOOK_EXTENSIONS,
    *PRESENTATION_EXTENSIONS,
}

PYTHON_DEPENDENCIES = {
    "docling": "docling",
    "PyPDF2": "PyPDF2",
    "pdfminer": "pdfminer.six",
    "ebooklib": "ebooklib",
    "bs4": "beautifulsoup4",
    "docx": "python-docx",
    "striprtf": "striprtf",
}


def supported_formats_message() -> str:
    return ", ".join(sorted(SUPPORTED_EXTENSIONS))
