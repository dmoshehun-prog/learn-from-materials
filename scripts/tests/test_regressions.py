from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
import zipfile
from contextlib import contextmanager
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from extractor.archive_safety import ArchiveSafetyError, validate_archive
from extractor.parsers.docx import extract_docx
from extractor.parsers.epub import _ebooklib_spine_item, count_epub_chapters, extract_with_zipfile
from extractor.parsers.pdf import extract_with_pypdf2
from extractor.utils import epub_section_number, render_traceable_markdown
from render_page import render
from verify_coverage import REQUIRED_KB_FILES, validate_summary_ledger, verify
from verify_static import verify as verify_static_page


@contextmanager
def closed_temporary_file(suffix):
    """A reopenable test file on Windows as well as POSIX."""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / ('fixture' + suffix)
        path.touch()
        yield types.SimpleNamespace(name=str(path))


class RegressionTests(unittest.TestCase):
    def test_overview_renders_dynamic_assessment_and_local_mistakes(self) -> None:
        skill_root = Path(__file__).resolve().parents[2]
        data = json.loads((skill_root / "examples" / "overview-content.json").read_text(encoding="utf-8"))
        data["frameworks"].reverse()
        data["glossary"].reverse()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "learning.html"
            markdown = Path(temp) / "learning.md"
            render(data, output, markdown)
            text = output.read_text(encoding="utf-8")
            errors, _warnings, page_data = verify_static_page(output)
        self.assertEqual(errors, [])
        self.assertEqual(page_data["schemaVersion"], "4.2")
        self.assertEqual([item["name"] for item in page_data["frameworks"]], ["问题地图", "证据链", "行动循环"])
        self.assertEqual([item["term"] for item in page_data["glossary"][:6]], ["问题地图", "问题边界", "关键角色", "成功标准", "KPI", "证据链"])
        self.assertIn('id="assessmentCopy"', text)
        self.assertIn('id="mistakeList"', text)
        self.assertIn("KLA_MISTAKES_JSON", text)
        self.assertIn("mistakesStorageKey", text)
        self.assertIn("系统学习模式", text)
        self.assertIn("stablePageIdentity", text)
        self.assertIn("question-bank.json", text)
        self.assertIn("不要向我报告检测过程", text)
        self.assertIn("优先使用原题", text)
        self.assertIn("让 AI 详解本单元", text)
        self.assertIn("详解口令已复制，请粘贴到当前材料对话中", text)
        self.assertIn("data-tooltip=\"复制本单元的核心内容、关键框架和材料出处。", text)
        self.assertNotIn("复制本单元到对话", text)
        self.assertNotIn('class="practice-card"', text)

    def test_quick_mode_renders_visible_scope_and_upgrade_action(self) -> None:
        skill_root = Path(__file__).resolve().parents[2]
        data = json.loads((skill_root / "examples" / "overview-content.json").read_text(encoding="utf-8"))
        data["meta"]["learningDepth"] = "quick"
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "quick.html"
            markdown = Path(temp) / "quick.md"
            render(data, output, markdown)
            text = output.read_text(encoding="utf-8")
            md_text = markdown.read_text(encoding="utf-8")
            errors, _warnings, _page_data = verify_static_page(output)
        self.assertEqual(errors, [])
        self.assertIn("快速了解模式", text)
        self.assertIn('id="upgradeDepthCopy"', text)
        self.assertIn("**学习深度：** 快速了解", md_text)

    def test_reader_layout_preserves_semantic_tabs_and_design_tokens(self) -> None:
        skill_root = Path(__file__).resolve().parents[2]
        data = json.loads((skill_root / "examples" / "overview-content.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "reader.html"
            render(data, output, None)
            text = output.read_text(encoding="utf-8")
            errors, _warnings, page_data = verify_static_page(output)
        self.assertEqual(errors, [])
        self.assertEqual(page_data["schemaVersion"], "4.2")
        self.assertIn("Knowledge Reader UI v2", text)
        self.assertIn("Knowledge Studio UI v3", text)
        self.assertIn("Knowledge Studio UI v4", text)
        self.assertIn('class="hero-stamp"', text)
        self.assertIn("雾蓝书房", text)
        self.assertIn('role="tab"', text)
        self.assertIn('role="tabpanel"', text)
        self.assertIn("prefers-reduced-motion", text)
        self.assertIn("--accent: var(--blue)", text)
        self.assertIn("--card: var(--surface)", text)

    def test_pypdf2_preserves_page_boundaries(self) -> None:
        class Page:
            def __init__(self, text: str) -> None:
                self.text = text

            def extract_text(self) -> str:
                return self.text

        class Reader:
            def __init__(self, _stream: object) -> None:
                self.pages = [Page("第一页"), Page("第二页")]

        old_module = sys.modules.get("PyPDF2")
        sys.modules["PyPDF2"] = types.SimpleNamespace(PdfReader=Reader)
        try:
            with closed_temporary_file(suffix=".pdf") as handle:
                self.assertEqual(extract_with_pypdf2(handle.name), "第一页\f第二页")
        finally:
            if old_module is None:
                sys.modules.pop("PyPDF2", None)
            else:
                sys.modules["PyPDF2"] = old_module

    def test_traceable_markdown_has_pdf_markers(self) -> None:
        text = render_traceable_markdown([
            {
                "filename": "two-pages.pdf",
                "source_file": "/tmp/two-pages.pdf",
                "format": "pdf",
                "pages": 2,
                "page_mapping_complete": True,
                "text": "A\fB",
            }
        ])
        self.assertIn("<!-- PDF 页 1 -->", text)
        self.assertIn("<!-- PDF 页 2 -->", text)

    def test_archive_safety_rejects_oversized_member(self) -> None:
        with closed_temporary_file(suffix=".zip") as handle:
            with zipfile.ZipFile(handle.name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("payload.xml", b"x" * 128)
            with zipfile.ZipFile(handle.name) as archive:
                with self.assertRaises(ArchiveSafetyError):
                    validate_archive(archive, max_member_size=64)

    def test_archive_safety_rejects_windows_absolute_path(self) -> None:
        with closed_temporary_file(suffix=".zip") as handle:
            with zipfile.ZipFile(handle.name, "w") as archive:
                archive.writestr("C:payload.xml", b"x")
            with zipfile.ZipFile(handle.name) as archive:
                with self.assertRaises(ArchiveSafetyError):
                    validate_archive(archive)

    def test_epub_section_number_preserves_original_spine_position(self) -> None:
        self.assertEqual(epub_section_number("【EPUB 章节 4】\n正文", 1), 4)
        self.assertEqual(epub_section_number("无章节标记", 2), 2)

    def test_ebooklib_spine_skips_non_linear_items(self) -> None:
        self.assertEqual(_ebooklib_spine_item(("chapter-1", "yes")), ("chapter-1", True))
        self.assertEqual(_ebooklib_spine_item(("nav", "no")), ("nav", False))

    def test_docx_keeps_table_footnote_and_image_placeholder(self) -> None:
        document = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
<w:body>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>标题</w:t></w:r><w:r><w:footnoteReference w:id="1"/></w:r></w:p>
<w:tbl><w:tr><w:tc><w:p><w:r><w:t>A1</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>B1</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
<w:p><w:r><w:drawing><wp:docPr id="1" name="Picture 1" descr="销售流程图"/><a:blip r:embed="rId1"/></w:drawing></w:r></w:p>
<w:p><w:r><w:drawing><a:blip r:embed="rId2"/></w:drawing></w:r></w:p>
</w:body></w:document>'''
        footnotes = '''<?xml version="1.0" encoding="UTF-8"?>
<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:footnote w:id="1"><w:p><w:r><w:t>脚注正文</w:t></w:r></w:p></w:footnote>
</w:footnotes>'''
        rels = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Target="media/image1.png" Type="image"/>
<Relationship Id="rId2" Target="C:\\Users\\Alice\\secret.png" TargetMode="External" Type="image"/>
</Relationships>'''
        with closed_temporary_file(suffix=".docx") as handle:
            with zipfile.ZipFile(handle.name, "w") as archive:
                archive.writestr("word/document.xml", document)
                archive.writestr("word/footnotes.xml", footnotes)
                archive.writestr("word/_rels/document.xml.rels", rels)
                archive.writestr("word/media/image1.png", b"png")
            text, method, visual_assets = extract_docx(handle.name)
        self.assertEqual(method, "zipfile-docx-structured")
        self.assertEqual(visual_assets, 1)
        self.assertIn("# 标题[脚注1]", text)
        self.assertIn("[表格 1]", text)
        self.assertIn("A1\tB1", text)
        self.assertIn("[图片：销售流程图]", text)
        self.assertNotIn("Alice", text)
        self.assertNotIn("secret.png", text)
        self.assertIn("[脚注1] 脚注正文", text)

    def test_epub_uses_spine_not_manifest_order(self) -> None:
        container = '''<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OPS/book.opf"/></rootfiles></container>'''
        opf = '''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf"><manifest>
<item id="two" href="two.xhtml" media-type="application/xhtml+xml"/>
<item id="one" href="one.xhtml" media-type="application/xhtml+xml"/>
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml"/>
</manifest><spine><itemref idref="nav" linear="no"/><itemref idref="one"/><itemref idref="two"/></spine></package>'''
        with closed_temporary_file(suffix=".epub") as handle:
            with zipfile.ZipFile(handle.name, "w") as archive:
                archive.writestr("META-INF/container.xml", container)
                archive.writestr("OPS/book.opf", opf)
                archive.writestr("OPS/nav.xhtml", "<html><body>不应读取的导航页</body></html>")
                archive.writestr("OPS/one.xhtml", "<html><body>第一章</body></html>")
                archive.writestr("OPS/two.xhtml", "<html><body>第二章</body></html>")
            text = extract_with_zipfile(handle.name)
            count = count_epub_chapters(handle.name)
        self.assertIsNotNone(text)
        self.assertLess(text.index("第一章"), text.index("第二章"))
        self.assertIn("\f", text)
        self.assertNotIn("不应读取的导航页", text)
        self.assertEqual(count, 2)

    def test_coverage_verifier_rejects_missing_page(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            kb = root / "demo.learnkb"
            kb.mkdir()
            (kb / "units").mkdir()
            (kb / "units" / "u01.md").write_text("unit", encoding="utf-8")
            for name in REQUIRED_KB_FILES:
                path = kb / name
                if not path.exists():
                    path.write_text("x", encoding="utf-8")
            manifest = {"sources": [{"filename": "demo.pdf"}]}
            source_map = [
                {"source_file": "/tmp/demo.pdf", "locator_type": "pdf_page", "pdf_page": 1},
                {"source_file": "/tmp/demo.pdf", "locator_type": "pdf_page", "pdf_page": 2},
            ]
            audit = {
                "schemaVersion": "1.0",
                "sources": [{
                    "filename": "demo.pdf",
                    "status": "covered",
                    "reason": "逐页读取",
                    "unitIds": ["u01"],
                    "ranges": [{"kind": "pdf_page", "start": 1, "end": 2}],
                }],
                "finalCheck": {"readToEnd": True, "noEarlyStop": True, "sourceLocatorsChecked": True},
            }
            (kb / "source_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (kb / "source_map.json").write_text(json.dumps(source_map), encoding="utf-8")
            (kb / "metadata.json").write_text("{}", encoding="utf-8")
            (kb / "question-bank.json").write_text(json.dumps({
                "schemaVersion": "knowledge-learning-assistant-question-bank/v1",
                "detection": "none",
                "confidence": "high",
                "sources": [],
                "questions": [],
            }), encoding="utf-8")
            (kb / "summary-ledger.json").write_text(json.dumps({
                "schemaVersion": "knowledge-learning-assistant-summary-ledger/v1",
                "claims": [], "exclusions": [], "finalCheck": {},
            }), encoding="utf-8")
            (kb / "coverage-audit.md").write_text("demo.pdf 已覆盖", encoding="utf-8")
            (kb / "coverage-audit.json").write_text(json.dumps(audit), encoding="utf-8")
            page = {
                "meta": {"knowledgeBase": str(kb / "INDEX.md"), "sourceType": "book"},
                "frameworks": [{"source": "第1章《示例》 · demo.pdf · PDF第1–2页"}],
            }
            page_path = root / "page.json"
            page_path.write_text(json.dumps(page), encoding="utf-8")
            self.assertEqual(verify(page_path), [])
            audit["sources"][0]["ranges"][0]["end"] = 1
            (kb / "coverage-audit.json").write_text(json.dumps(audit), encoding="utf-8")
            self.assertTrue(any("缺少 PDF 页" in error for error in verify(page_path)))

    def test_coverage_verifier_rejects_unusable_question_bank_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            kb = root / "demo.learnkb"
            kb.mkdir()
            (kb / "units").mkdir()
            (kb / "units" / "u01.md").write_text("unit", encoding="utf-8")
            for name in REQUIRED_KB_FILES:
                (kb / name).write_text("x", encoding="utf-8")
            (kb / "source_manifest.json").write_text(json.dumps({"sources": [{"filename": "题库.pdf"}]}), encoding="utf-8")
            (kb / "source_map.json").write_text("[]", encoding="utf-8")
            (kb / "coverage-audit.md").write_text("题库.pdf 已覆盖", encoding="utf-8")
            (kb / "coverage-audit.json").write_text(json.dumps({
                "schemaVersion": "1.0",
                "sources": [{"filename": "题库.pdf", "status": "covered", "reason": "逐页读取", "unitIds": ["u01"], "ranges": []}],
                "finalCheck": {"readToEnd": True, "noEarlyStop": True, "sourceLocatorsChecked": True},
            }), encoding="utf-8")
            (kb / "question-bank.json").write_text(json.dumps({
                "schemaVersion": "knowledge-learning-assistant-question-bank/v1",
                "detection": "partial",
                "confidence": "high",
                "sources": [{"filename": "题库.pdf", "kind": "question-bank", "source": "题库.pdf · 第1题"}],
                "questions": [{
                    "id": "q001", "stem": "题目", "questionType": "single-choice", "options": ["A. 一"],
                    "answer": "", "explanation": "", "answerBasis": "unavailable", "unitId": "u01",
                    "knowledgePoints": ["知识点"], "source": "题库.pdf · 第1题", "usable": True,
                }],
            }), encoding="utf-8")
            (kb / "summary-ledger.json").write_text(json.dumps({
                "schemaVersion": "knowledge-learning-assistant-summary-ledger/v1",
                "claims": [], "exclusions": [], "finalCheck": {},
            }), encoding="utf-8")
            page_path = root / "page.json"
            page_path.write_text(json.dumps({
                "meta": {"knowledgeBase": str(kb / "INDEX.md"), "sourceType": "book"},
                "contentUnits": [{"id": "u01"}],
                "frameworks": [{"source": "题库.pdf · 第1题"}],
            }), encoding="utf-8")
            self.assertTrue(any("不得标记 usable=true" in error for error in verify(page_path)))

    def test_summary_ledger_rejects_missing_content_summary_mapping(self) -> None:
        skill_root = Path(__file__).resolve().parents[2]
        data = json.loads((skill_root / "examples" / "overview-content.json").read_text(encoding="utf-8"))
        ledger = json.loads((skill_root / "examples" / "示例方法材料.learnkb" / "summary-ledger.json").read_text(encoding="utf-8"))
        ledger["claims"][0]["summaryRefs"].remove("unit:ch01:core")
        unit_ids = {item["id"] for item in data["contentUnits"]}
        errors = validate_summary_ledger(ledger, data, unit_ids, True)
        self.assertTrue(any("unit:ch01:core" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
