import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from html.parser import HTMLParser

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from render_page import render, validate, validate_source_for_type, validate_book_source
from verify_static import verify as verify_static
from verify_coverage import verify as verify_coverage, PDF_RANGE, SLIDE_RANGE, EPUB_RANGE
from localization import LOCALE


class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.root = SCRIPTS.parent
        self.data = json.loads((self.root / 'examples/overview-en-content.json').read_text(encoding='utf-8'))

    def test_english_content_and_ui_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'page.html'
            md = Path(directory) / 'page.md'
            render(self.data, path, md)
            errors, _, data = verify_static(path)
            self.assertEqual(errors, [])
            self.assertEqual(data['meta']['language'], 'en')
            self.assertEqual(data['relationships'], self.data['relationships'])
            self.assertIn('<html lang="en"', path.read_text(encoding='utf-8'))
            self.assertNotRegex(md.read_text(encoding='utf-8'), r'[\u3400-\u9fff]')

    def test_original_quotes_are_not_translated(self):
        self.data['hero']['thesis'] = 'Original quotation: 材料依据。'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'page.html'
            render(self.data, path, None)
            _, _, data = verify_static(path)
            self.assertEqual(data['hero']['thesis'], self.data['hero']['thesis'])
            self.assertIn('Original quotation: 材料依据。', path.read_text(encoding='utf-8'))

    def test_all_static_english_ui_labels_are_english(self):
        class TextInspector(HTMLParser):
            def __init__(self):
                super().__init__(); self.ignore = False; self.labels = []
            def handle_starttag(self, tag, attrs):
                if tag in ('script','style'): self.ignore = True
                self.labels.extend(value for key, value in attrs if key in ('title','placeholder','aria-label','alt') and value)
            def handle_endtag(self, tag):
                if tag in ('script','style'): self.ignore = False
            def handle_data(self, value):
                if not self.ignore: self.labels.append(value)
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / 'en.html'
            render(self.data, page, None)
            parser = TextInspector(); parser.feed(page.read_text(encoding='utf-8'))
            self.assertNotRegex('\n'.join(parser.labels), r'[\u3400-\u9fff]')

    def test_material_template_notation_is_never_executed(self):
        self.data['hero']['thesis'] = 'Example syntax: {{component_scripts}} and {{page_data}}'
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / 'page.html'
            render(self.data, page, None)
            errors, _, data = verify_static(page)
            self.assertEqual(errors, [])
            self.assertEqual(data['hero']['thesis'], self.data['hero']['thesis'])
            self.assertIn(self.data['hero']['thesis'], page.read_text(encoding='utf-8'))

    def test_english_topic_and_unit_pages(self):
        for mode in ('topic','unit'):
            data = {key:copy.deepcopy(self.data[key]) for key in ('schemaVersion','meta','hero')}
            data['meta'].update(mode=mode)
            data['meta'][mode] = 'Problem framing'
            data['sections'] = [{'id':'quote','label':'Original passage','title':'Frame the problem','lead':'A synthetic excerpt.','signature':'quote_card','quote':{'text':'Before choosing an action, record the problem boundary.','attribution':'Method Lab','source':'methods-demo.txt · Lines 3-4'}}]
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                page = Path(directory) / 'page.html'
                render(data, page, Path(directory) / 'page.md')
                errors, _, embedded = verify_static(page)
                self.assertEqual(errors, [])
                self.assertEqual(embedded['meta']['mode'], mode)
                self.assertNotIn('id="methodDialog"',page.read_text(encoding='utf-8'))

    def test_untrusted_html_cannot_create_scripts(self):
        payload = '</script><script id="injected">alert(1)</script>'
        self.data['hero']['thesis'] = payload
        self.data['relationships'][0]['explanation'] = payload
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'page.html'
            render(self.data, path, None)
            text = path.read_text(encoding='utf-8')
            self.assertNotIn(payload, text)
            _, _, data = verify_static(path)
            self.assertEqual(data['relationships'][0]['explanation'], payload)

    def test_language_context_restored_after_render(self):
        with tempfile.TemporaryDirectory() as directory:
            render(self.data, Path(directory) / 'en.html', None)
            self.assertEqual(LOCALE.get(), 'zh-CN')
            old = json.loads((self.root / 'examples/overview-content.json').read_text(encoding='utf-8'))
            render(old, Path(directory) / 'zh.html', None)
            self.assertIn('<html lang="zh-CN"', (Path(directory) / 'zh.html').read_text(encoding='utf-8'))

    def test_schema_43_requires_language_and_method_ids(self):
        for missing in ('language', 'id'):
            data = copy.deepcopy(self.data)
            del (data['meta'] if missing == 'language' else data['frameworks'][0])[missing]
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                validate(data)

    def test_invalid_language_rejected(self):
        self.data['meta']['language'] = 'fr'
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_duplicate_method_id_rejected(self):
        self.data['decisionRules'][0]['id'] = self.data['frameworks'][0]['id']
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_relationship_validation(self):
        for change in ({'from':'missing'}, {'to':'f-map'}, {'type':'pretty-line'}, {'evidence':'certain'}, {'source':''}, {'explanation':''}, {'extra':True}):
            data = copy.deepcopy(self.data)
            data['relationships'][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(data)
        self.data['relationships'].append(copy.deepcopy(self.data['relationships'][0]))
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_empty_relationships_allowed_no_invention(self):
        self.data['relationships'] = []
        validate(self.data)

    def test_english_glossary_does_not_require_chinese_meaning(self):
        validate(self.data)
        self.data['meta']['language'] = 'zh-CN'
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_english_ability_enums_cover_systematic(self):
        self.data['meta']['learningDepth'] = 'systematic'
        validate(self.data)

    def test_english_source_locators(self):
        samples = {'slides':'deck.pptx · Slides 2-3: Evidence', 'document':'report.pdf · Heading: Findings · PDF pp. 2-3', 'web':'Article · Section: Findings · Paragraph 2', 'text':'notes.txt · Lines 2-3'}
        for source_type, source in samples.items():
            errors = []
            validate_source_for_type(errors, source, 'test', source_type)
            self.assertEqual(errors, [], source)
        errors = []
        validate_book_source(errors, 'Chapter 2: Evidence · PDF pp. 12-14', 'test')
        self.assertEqual(errors, [])

    def test_english_ranges_still_checked(self):
        for regex, source in [(PDF_RANGE, 'PDF pp. 12-14'), (SLIDE_RANGE, 'Slides 12-14'), (EPUB_RANGE, 'EPUB sections 12-14')]:
            self.assertEqual(regex.search(source).groups(), ('12', '14'))
        old = json.loads((self.root / 'examples/overview-content.json').read_text(encoding='utf-8'))
        old['frameworks'][0]['source'] = 'Chapter 1: Example · PDF pp. 999-1000'
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / 'page.json'
            page.write_text(json.dumps(old), encoding='utf-8')
            errors = verify_coverage(page, self.root / 'examples/示例方法材料.learnkb')
            self.assertTrue(any('source_map' in error for error in errors))


if __name__ == '__main__':
    unittest.main()
