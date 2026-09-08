from pathlib import Path
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from render_page import render, validate
from verify_coverage import verify
from prepare_quick import prepare
from verify_static import verify as verify_static


class QuickTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.kb = self.root / 'demo.learnkb'
        self.kb.mkdir()
        self.page = self.root / 'page.json'
        self.data = json.loads((SCRIPTS.parent / 'examples/overview-content.json').read_text())
        self.data['meta'].update(learningDepth='quick', sourceType='text', knowledgeBase='demo.learnkb/INDEX.md')
        self.data['decisionRules'] = []
        for area in self.data['assessment']['focusAreas']:
            area['abilities'] = ['解释']
        def rewrite(value):
            if isinstance(value, dict):
                for key in value:
                    if key == 'source':
                        value[key] = 'demo.txt · 第1行'
                    else:
                        rewrite(value[key])
            elif isinstance(value, list):
                for item in value:
                    rewrite(item)
        rewrite(self.data)
        self.raw = '合成测试原文：问题地图、证据链和行动循环。'
        source = self.root / 'demo.txt'
        source.write_text(self.raw, encoding='utf-8')
        result = subprocess.run([sys.executable, str(SCRIPTS / 'extract.py'), str(source),
                                 '--output-dir', str(self.kb), '--ocr', 'off'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.blocks = json.loads((self.kb / 'source_map.json').read_text())
        ids = [b['source_id'] for b in self.blocks]
        self.audit = {'schemaVersion':'learn-from-materials/quick-audit-v1', 'learningDepth':'quick',
                      'structure':[{'title':'合成测试章节', 'sourceIds':ids, 'status':'scanned', 'note':'用于结构测试，不代表语义评测'}],
                      'evidence':[{'source':'demo.txt · 第1行', 'sourceIds':ids, 'quote':self.raw, 'checked':True}],
                      'limitations':['合成结构测试；非全量知识整理']}
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        self.page.write_text(json.dumps(self.data, ensure_ascii=False), encoding='utf-8')
        (self.kb / 'quick-audit.json').write_text(json.dumps(self.audit, ensure_ascii=False), encoding='utf-8')

    def test_quick_extract_prepare_render(self):
        self.assertEqual(verify(self.page, self.kb), [])
        prepare(self.page, self.kb)
        self.assertTrue((self.kb / 'INDEX.md').exists())
        for name in ('summary-ledger.json', 'question-bank.json', 'unit-dependency-map.json'):
            self.assertFalse((self.kb / name).exists())
        output = self.root / 'quick.html'
        render(self.data, output, self.root / 'quick.md')
        errors, _, _ = verify_static(output)
        self.assertEqual(errors, [])
        self.assertIn('不额外编造建议', output.read_text())
        result = subprocess.run([sys.executable, str(SCRIPTS / 'render_page.py'), str(self.page),
                                 '-k', str(self.kb), '-o', str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_systematic_cannot_use_quick_gate(self):
        self.data['meta']['learningDepth'] = 'systematic'
        self.save()
        self.assertTrue(verify(self.page, self.kb))
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_invalid_evidence_fails(self):
        original = copy.deepcopy(self.audit)
        for change in ({'sourceIds':['unknown']}, {'quote':'虚构引文'}, {'checked':False},
                       {'source':'demo.txt · PDF第999页'}):
            with self.subTest(change=change):
                self.audit = copy.deepcopy(original)
                self.audit['evidence'][0].update(change)
                self.save()
                self.assertTrue(verify(self.page, self.kb))

    def test_missing_or_unreadable_structure_fails(self):
        self.audit['structure'][0]['status'] = 'unreadable'
        self.save()
        self.assertTrue(verify(self.page, self.kb))
        self.audit['structure'] = []
        self.save()
        self.assertTrue(verify(self.page, self.kb))

    def test_changed_source_hash_fails(self):
        (self.kb / 'full_text.txt').write_text('已变更', encoding='utf-8')
        self.assertTrue(verify(self.page, self.kb))


if __name__ == '__main__':
    unittest.main()
