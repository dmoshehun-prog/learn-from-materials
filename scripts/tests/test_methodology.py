import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from methodology import validate
from render_page import validate as validate_page, render_frameworks

class WholeMethodologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page=json.loads((ROOT/'examples/overview-whole-methodology.json').read_text(encoding='utf-8'))
        cls.kb=ROOT/'examples/rsi-methodology.learnkb'

    def test_real_evidence_and_complete_structure(self):
        validate(self.page['methodology'],self.page,self.kb)
        validate_page(self.page)

    def test_nonsequential_relation_kinds_are_valid(self):
        for kind in ('prerequisite', 'parallel', 'contrasts'):
            model=copy.deepcopy(self.page['methodology'])
            extra=copy.deepcopy(model['edges'][0]);extra['id']='extra-'+kind;extra['kind']=kind
            model['edges'].append(extra)
            validate(model,self.page,self.kb)

    def test_framework_card_numbers_use_source_order(self):
        items=[dict(name='Item '+str(i),oneLine='Meaning',when='When needed',source='Source',sourceOrder=i)
               for i in range(1,13)]
        html=render_frameworks(items)
        self.assertIn('data-framework-number="01"',html)
        self.assertIn('data-framework-number="10"',html)
        self.assertNotIn('data-framework-number="010"',html)

    def test_disconnected_node_rejected(self):
        m=copy.deepcopy(self.page['methodology'])
        n=copy.deepcopy(m['nodes'][0]);n['id']='unreachable';m['nodes'].append(n)
        with self.assertRaisesRegex(ValueError,'unreachable'):validate(m,self.page)

    def test_missing_handoff_rejected(self):
        m=copy.deepcopy(self.page['methodology']);m['edges'].pop(0)
        with self.assertRaisesRegex(ValueError,'handoff'):validate(m,self.page)

    def test_unaccounted_unit_rejected(self):
        m=copy.deepcopy(self.page['methodology']);m['coverage'].pop()
        with self.assertRaisesRegex(ValueError,'every content unit'):validate(m,self.page)

    def test_false_author_attribution_rejected(self):
        m=copy.deepcopy(self.page['methodology']);m['evidence']='material'
        with self.assertRaisesRegex(ValueError,'synthesis'):validate(m,self.page)

    def test_fabricated_quote_rejected(self):
        m=copy.deepcopy(self.page['methodology']);m['nodes'][0]['sources'][0]['quote']='this exact sentence is absent from the original PDF'
        with self.assertRaisesRegex(ValueError,'quote absent'):validate(m,self.page,self.kb)

    def test_source_detail_alignment(self):
        p=copy.deepcopy(self.page);p['contentUnits'][0]['sourceDetails']={'takeaways':['only one']}
        with self.assertRaisesRegex(ValueError,'count mismatch'):validate_page(p)

    def test_nonprocedural_and_not_applicable(self):
        m=copy.deepcopy(self.page['methodology']);m['structure']='causal';m['mainPath']=[]
        validate(m,self.page,self.kb)
        m['status']='not-applicable';m['structure']='none'
        for k in ('entryNodes','nodes','edges','constraints'):m[k]=[]
        for c in m['coverage']:c.update(nodeIds=[],role='context')
        validate(m,self.page,self.kb)

    def test_language_mismatch_rejected(self):
        m=copy.deepcopy(self.page['methodology']);m['language']='en'
        with self.assertRaisesRegex(ValueError,'language'):validate(m,self.page)

if __name__=='__main__':unittest.main()
