from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from verify_heading_index import validate


class HeadingIndexTests(unittest.TestCase):
    def setUp(self):
        test_root = SCRIPTS.parent.parent / "skill-test-temp"
        test_root.mkdir(exist_ok=True)
        self.kb = test_root / ("heading-" + uuid.uuid4().hex)
        self.kb.mkdir()
        self.addCleanup(lambda: shutil.rmtree(self.kb) if self.kb.resolve().is_relative_to(test_root.resolve()) else None)
        lines = ["4.2.4 Ni 增原子辅助脱氧反应", "总结与展望"]
        raw = "\n".join(lines)
        (self.kb / "full_text.txt").write_text(raw, encoding="utf-8")
        self.manifest = {"sources": [{"filename": "paper.pdf", "format": "pdf"}]}
        self.source_map = [
            {"source_file": "paper.pdf", "locator_type": "pdf_page", "pdf_page": 61,
             "start_char": 0, "end_char": len(lines[0])},
            {"source_file": "paper.pdf", "locator_type": "pdf_page", "pdf_page": 72,
             "start_char": len(lines[0]) + 1, "end_char": len(raw)},
        ]
        self.index = {"schemaVersion": "learn-from-materials/source-heading-index-v1", "entries": [
            {"filename": "paper.pdf", "path": "第四章", "pdfStart": 61, "pdfEnd": 61,
             "evidencePage": 61, "evidenceText": "4.2.4 Ni 增原子辅助脱氧反应", "verification": "visual",
             "reviewNote": "测试夹具模拟已对照原 PDF 的章标题"},
            {"filename": "paper.pdf", "path": "第四章 > 4.2.4 Ni 增原子辅助脱氧反应",
             "pdfStart": 61, "pdfEnd": 61, "evidencePage": 61,
             "evidenceText": lines[0], "verification": "text"},
            {"filename": "paper.pdf", "path": "总结与展望",
             "pdfStart": 72, "pdfEnd": 72, "evidencePage": 72,
             "evidenceText": lines[1], "verification": "text"},
        ]}
        self.save()

    def save(self):
        (self.kb / "source-heading-index.json").write_text(
            json.dumps(self.index, ensure_ascii=False), encoding="utf-8")

    def check(self, *citations):
        return validate({}, self.kb, self.manifest, self.source_map, list(citations), required=True)

    def test_correct_numbered_and_unnumbered_sources(self):
        self.assertEqual(self.check(
            "paper.pdf · 标题路径：第四章 > 4.2.4 Ni 增原子辅助脱氧反应 · PDF第61页",
            "paper.pdf · 标题路径：总结与展望 · PDF第72页"), [])

    def test_wrong_number_and_invented_chapter_fail(self):
        errors = self.check(
            "paper.pdf · 标题路径：第四章 > 4.3 Ni 增原子辅助脱氧反应 · PDF第61页",
            "paper.pdf · 标题路径：第六章 总结与展望 · PDF第72页")
        self.assertEqual(sum("标题路径不在" in error for error in errors), 2)

    def test_page_outside_heading_fails(self):
        errors = self.check("paper.pdf · 标题路径：总结与展望 · PDF第61页")
        self.assertTrue(any("PDF 页码不属于" in error for error in errors))

    def test_missing_pdf_page_fails(self):
        errors = self.check("paper.pdf · 标题路径：总结与展望")
        self.assertTrue(any("缺少精确 PDF 页码" in error for error in errors))

    def test_index_must_cite_original_heading_text(self):
        self.index["entries"][1]["evidenceText"] = "4.3 Ni 增原子辅助脱氧反应"
        self.save()
        self.assertTrue(any("evidenceText 未出现在" in error for error in self.check()))

    def test_missing_index_blocks_required_delivery(self):
        (self.kb / "source-heading-index.json").unlink()
        self.assertTrue(any("缺少 source-heading-index.json" in error for error in self.check()))


if __name__ == "__main__":
    unittest.main()
