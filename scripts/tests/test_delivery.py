import copy
import json
from pathlib import Path
import shutil
import sys
import subprocess
import tempfile
import unittest
import zipfile

SCRIPTS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SCRIPTS))
from delivery import check_canonical, export_readable, verify_readable
from finalize import finalize


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.page_file=SCRIPTS.parent/'examples/overview-whole-methodology.json'
        self.page=json.loads(self.page_file.read_text(encoding='utf-8'))
        self.kb=SCRIPTS.parent/'examples/rsi-methodology.learnkb'

    def test_missing_snapshot_cannot_pass(self):
        page=copy.deepcopy(self.page);page.pop('methodology')
        with self.assertRaisesRegex(ValueError,'snapshot'):
            check_canonical(page,self.kb)

    def test_cli_blocks_missing_model_before_html(self):
        with tempfile.TemporaryDirectory() as t:
            t=Path(t);page=copy.deepcopy(self.page);page.pop('methodology')
            (t/'input.json').write_text(json.dumps(page),encoding='utf-8')
            result=subprocess.run([sys.executable,str(SCRIPTS/'render_page.py'),str(t/'input.json'),'-k',str(self.kb),'-o',str(t/'out.html')],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('snapshot',result.stderr)
            self.assertFalse((t/'out.html').exists())

    def test_missing_canonical_cannot_publish(self):
        with tempfile.TemporaryDirectory() as t:
            kb=Path(t)/'kb';kb.mkdir()
            shutil.copy2(self.kb/'methods.json',kb/'methods.json')
            with self.assertRaisesRegex(ValueError,'methodology.json'):
                check_canonical(self.page,kb)

    def test_derived_export_is_rebuilt_and_prior_prose_preserved(self):
        exports=check_canonical(self.page,self.kb)
        with tempfile.TemporaryDirectory() as t:
            kb=Path(t);(kb/'methodology.md').write_text('prior human notes',encoding='utf-8')
            export_readable(kb,exports);verify_readable(kb,exports)
            self.assertEqual(next((kb/'history').glob('*.md')).read_text(encoding='utf-8'),'prior human notes')

    def test_package_contains_readable_canonical_and_bound_snapshot(self):
        with tempfile.TemporaryDirectory() as t:
            result=finalize(self.page_file,self.kb,Path(t)/'out','review',legacy_rule_ledger=True)
            page=json.loads(Path(result['page']).read_text(encoding='utf-8'))
            self.assertEqual(page['meta']['pageId'],self.page['meta']['pageId'])
            with zipfile.ZipFile(result['archive']) as z:
                for name in ['methodology.md','methodology.json','methods.json','patterns.md']:
                    self.assertGreater(len(z.read('review.learnkb/'+name)),10)
                self.assertEqual(json.loads(z.read('review.learnkb/methodology.json')),page['methodology'])
                self.assertIsNone(z.testzip())

    def test_existing_delivery_is_preserved(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t)/'review.html').write_text('keep',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'exists'):
                finalize(self.page_file,self.kb,t,'review',legacy_rule_ledger=True)
            self.assertEqual((Path(t)/'review.html').read_text(encoding='utf-8'),'keep')

    def test_new_systematic_delivery_requires_ledger(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError,'action-rule-ledger.json'):
                finalize(self.page_file,self.kb,t,'review')

    def test_validation_failure_leaves_no_delivery_and_allows_retry(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'out'
            with patch('finalize.verify',return_value=['injected coverage failure']):
                with self.assertRaisesRegex(ValueError,'injected coverage failure'):
                    finalize(self.page_file,self.kb,out,'review',legacy_rule_ledger=True)
            self.assertFalse(any(out.iterdir()))
            result=finalize(self.page_file,self.kb,out,'review',legacy_rule_ledger=True)
            self.assertTrue(Path(result['archive']).is_file())

if __name__=='__main__':unittest.main()
