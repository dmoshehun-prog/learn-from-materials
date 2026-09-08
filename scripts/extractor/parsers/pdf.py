from __future__ import annotations
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _macos_pdfkit_available() -> bool:
    """Return whether macOS PDFKit can be invoked through the system Swift runtime."""
    return sys.platform == "darwin" and bool(shutil.which("swift"))


def extract_with_pdfkit(pdf_path: str) -> str | None:
    """Extract a text-layer PDF with macOS PDFKit without installing Python packages."""
    if not _macos_pdfkit_available():
        return None
    swift = shutil.which("swift")
    if not swift:
        return None
    script = r'''
import Foundation
import PDFKit
let path = CommandLine.arguments.last!
let url = URL(fileURLWithPath: path)
guard let doc = PDFDocument(url: url) else { fatalError("Unable to open PDF") }
for index in 0..<doc.pageCount {
    print(doc.page(at: index)?.string ?? "")
    if index + 1 < doc.pageCount { print("\u{000C}") }
}
'''
    try:
        result = subprocess.run(
            [swift, "-e", script, pdf_path], capture_output=True, text=True, timeout=240
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except Exception:
        pass
    return None


def extract_with_pdftotext(pdf_path: str) -> str | None:
    if not shutil.which("pdftotext"):
        return None
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", pdf_path, "-"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except Exception:
        pass
    return None


def extract_with_pypdf2(pdf_path: str) -> str | None:
    try:
        import PyPDF2
        text_parts = []
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                try:
                    text_parts.append(page.extract_text() or "")
                except Exception:
                    text_parts.append("")
        # Preserve one form-feed boundary per physical page so source_map.json
        # can map every extracted span back to the correct PDF page.
        return "\f".join(text_parts)
    except ImportError:
        return None
    except Exception:
        return None


def extract_with_pdfminer(pdf_path: str) -> str | None:
    try:
        from pdfminer.high_level import extract_text
        return extract_text(pdf_path)
    except ImportError:
        return None
    except Exception:
        return None


def extract_with_ocrmypdf(pdf_path: str, force: bool = False) -> str | None:
    """OCR a scanned or low-text PDF, then return layout-preserving text."""
    if not shutil.which("ocrmypdf") or not shutil.which("pdftotext"):
        return None
    try:
        with tempfile.TemporaryDirectory(prefix="material-to-learning-ocr-") as temp_dir:
            output_pdf = Path(temp_dir) / "ocr.pdf"
            mode_flag = "--force-ocr" if force else "--skip-text"
            result = subprocess.run(
                [
                    "ocrmypdf", mode_flag, "--deskew", "--rotate-pages",
                    "--output-type", "pdf", pdf_path, str(output_pdf),
                ],
                capture_output=True,
                text=True,
                timeout=1800,
            )
            if result.returncode != 0 or not output_pdf.exists():
                return None
            return extract_with_pdftotext(str(output_pdf))
    except Exception:
        return None


def extract_with_docling(pdf_path: str) -> str | None:
    """Layout-aware extraction using Docling. Best for technical books with tables and code."""
    try:
        from docling.document_converter import DocumentConverter
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import PdfFormatOption

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        pipeline_options.do_table_structure = True

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        result = converter.convert(pdf_path)
        return result.document.export_to_markdown()
    except ImportError:
        return None
    except Exception:
        return None


def count_pages_pdfkit(pdf_path: str) -> int:
    """Return the PDF physical page count through macOS PDFKit when available."""
    if not _macos_pdfkit_available():
        return 0
    swift = shutil.which("swift")
    if not swift:
        return 0
    script = r'''
import Foundation
import PDFKit
let path = CommandLine.arguments.last!
guard let doc = PDFDocument(url: URL(fileURLWithPath: path)) else { fatalError("Unable to open PDF") }
print(doc.pageCount)
'''
    try:
        result = subprocess.run(
            [swift, "-e", script, pdf_path], capture_output=True, text=True, timeout=90
        )
        return int(result.stdout.strip()) if result.returncode == 0 else 0
    except Exception:
        return 0


def count_pages(pdf_path: str) -> int:
    # Try pdfinfo first
    if shutil.which("pdfinfo"):
        try:
            result = subprocess.run(
                ["pdfinfo", pdf_path], capture_output=True, text=True, timeout=15
            )
            for line in result.stdout.splitlines():
                if line.startswith("Pages:"):
                    return int(line.split(":")[1].strip())
        except Exception:
            pass
    # macOS fallback: PDFKit is available without adding Python packages.
    pdfkit_pages = count_pages_pdfkit(pdf_path)
    if pdfkit_pages:
        return pdfkit_pages
    # Fallback: count form-feed chars (pdftotext -layout uses \f between pages)
    try:
        import PyPDF2
        with open(pdf_path, "rb") as f:
            return len(PyPDF2.PdfReader(f).pages)
    except Exception:
        return 0
