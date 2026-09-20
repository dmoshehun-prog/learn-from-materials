import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SCRIPTS))
from methods import validate_library,validate_index,accumulate,search,patterns,bind,save,read
from render_page import validate,render
from verify_static import verify as verify_static


class MethodTests(unittest.TestCase):
    def setUp(self):
        self.examples=SCRIPTS.parent/'examples'
        self.kb=self.examples/'methods-demo.learnkb'
        self.lib=read(self.kb/'methods.json')
        self.page=read(self.examples/'overview-en-content.json')

    def test_source_grounded_library(self):
        self.assertEqual(validate_library(self.lib,self.kb),self.lib)

    def test_no_method_is_a_valid_result(self):
        self.lib.update(status='none',note='The material contains descriptions but no supported procedure.',methods=[])
        validate_library(self.lib,self.kb)
        self.assertIn(self.lib['note'],patterns(self.lib))
        self.assertEqual(bind(self.page,self.lib)['frameworks'],self.page['frameworks'])

    def test_bad_cards_are_rejected(self):
        for key,value in [('version','latest'),('steps',[]),('sources',[]),('limitations',[]),('source','made up'),('evidence','proven')]:
            lib=copy.deepcopy(self.lib);lib['methods'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): validate_library(lib)

    def test_duplicate_id_rejected(self):
        self.lib['methods'].append(copy.deepcopy(self.lib['methods'][0]))
        with self.assertRaises(ValueError): validate_library(self.lib)

    def test_fabricated_quote_or_source_id_rejected(self):
        for key,value in [('quote','This quotation was fabricated.'),('sourceIds',['missing'])]:
            lib=copy.deepcopy(self.lib);lib['methods'][0]['sources'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): validate_library(lib,self.kb)

    def test_changed_original_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            kb=Path(tmp)/'kb';shutil.copytree(self.kb,kb)
            raw=kb/'full_text.txt';raw.write_text(raw.read_text(encoding='utf-8').replace('Problem map','Changed map'),encoding='utf-8')
            with self.assertRaises(ValueError): validate_library(self.lib,kb)

    def test_patterns_derived_in_both_languages(self):
        self.assertIn('### Prerequisites',patterns(self.lib))
        self.lib['language']='zh-CN'
        self.assertIn('### 使用前提',patterns(self.lib))
        self.assertIn(self.lib['methods'][0]['sources'][0]['quote'],patterns(self.lib))

    def test_page_binding_and_drift_detection(self):
        page=bind(self.page,self.lib);validate(page)
        self.assertEqual(page['methodLibrary'],self.lib)
        self.assertEqual(page['frameworks'],self.page['frameworks'])
        page['frameworks'][0]['oneLine']='Independently edited and out of sync'
        with self.assertRaises(ValueError): validate(page)

    def test_renamed_framework_updates_unit_references(self):
        self.lib['methods'][0]['name']='Scope map'
        page=bind(self.page,self.lib);validate(page)
        self.assertEqual(page['contentUnits'][0]['frameworks'],['Scope map'])
        self.assertEqual(self.page['frameworks'][0]['name'],'Problem map')

    def test_derived_cards_do_not_become_material_facts(self):
        self.lib['methods'][0]['evidence']='inference'
        with self.assertRaises(ValueError): bind(self.page,self.lib)

    def test_accumulation_is_immutable_and_versioned(self):
        index=accumulate([self.lib]);self.assertEqual(accumulate([self.lib],index),index)
        updated=copy.deepcopy(self.lib);updated['methods'][0]['summary']='Revised summary'
        with self.assertRaises(ValueError): accumulate([updated],index)
        updated['methods'][0]['version']='1.0.1'
        new=accumulate([updated],index)
        self.assertEqual(len(new['entries']),len(index['entries'])+1)
        self.assertEqual(index['entries']['method-lab/f-map@1.0.0']['card']['summary'],self.lib['methods'][0]['summary'])

    def test_library_namespaces_prevent_id_collisions(self):
        other=copy.deepcopy(self.lib);other['libraryId']='another-book'
        index=accumulate([self.lib,other])
        self.assertEqual(len(index['entries']),2*len(self.lib['methods']))

    def test_keyword_retrieval_and_no_match(self):
        self.lib['methods'][0]['tags'].append('问题边界')
        index=accumulate([self.lib])
        self.assertEqual(search(index,'问题边界')[0]['ref'],'method-lab/f-map@1.0.0')
        self.assertTrue(search(index,'counterevidence'))
        self.assertEqual(search(index,'zzunmatchedwordzz'),[])

    def test_synthesis_preserves_and_resolves_parents(self):
        combo=copy.deepcopy(self.lib['methods'][0]);combo.update(id='combined',evidence='synthesis',parents=['method-lab/f-map@1.0.0','method-lab/f-evidence@1.0.0'])
        self.lib['methods'].append(combo)
        index=accumulate([self.lib]);self.assertIn('method-lab/combined@1.0.0',index['entries'])
        self.lib['methods'][-1]['parents'][1]='missing/book@1.0.0'
        with self.assertRaises(ValueError): accumulate([self.lib])

    def test_cycle_and_tampered_index_rejected(self):
        index=accumulate([self.lib]);index['entries']['method-lab/f-map@1.0.0']['card']['name']='Tampered'
        with self.assertRaises(ValueError): validate_index(index)
        self.lib['methods'][0].update(evidence='inference',parents=['method-lab/f-evidence@1.0.0'])
        self.lib['methods'][1].update(evidence='inference',parents=['method-lab/f-map@1.0.0'])
        with self.assertRaises(ValueError): accumulate([self.lib])

    def test_outputs_are_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'patterns.md';save(path,'Original')
            with self.assertRaises(ValueError): save(path,'Different')
            self.assertEqual(path.read_text(),'Original')

    def test_long_lineage_does_not_depend_on_recursion_limit(self):
        seed=copy.deepcopy(self.lib['methods'][0]);self.lib['methods']=[]
        for i in range(1100):
            card=copy.deepcopy(seed);card.update(id=f'm{i}',evidence='inference',parents=[f'method-lab/m{i-1}@1.0.0'] if i else [])
            self.lib['methods'].append(card)
        self.assertEqual(len(accumulate([self.lib])['entries']),1100)

    def test_cli_export_bind_render_index_search_compare(self):
        def run(script,*args):
            result=subprocess.run([sys.executable,str(SCRIPTS/script),*[str(a) for a in args]],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            return result.stdout
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);lib=self.kb/'methods.json'
            run('methods.py','export','--library',lib,'--knowledge-base',self.kb,'--output',tmp/'patterns.md')
            self.assertEqual((tmp/'patterns.md').read_text(encoding='utf-8'),patterns(self.lib))
            run('methods.py','bind','--library',lib,'--knowledge-base',self.kb,'--page',self.examples/'overview-en-content.json','--output',tmp/'page.json')
            # This v0.3 fixture has no whole-material record: explicit legacy path.
            run('render_page.py',tmp/'page.json','-k',self.kb,'-o',tmp/'page.html','--legacy')
            self.assertEqual(verify_static(tmp/'page.html')[0],[])
            run('methods.py','index',lib,'--output',tmp/'index.json')
            result=json.loads(run('methods.py','search','--index',tmp/'index.json','--query','boundary'))
            self.assertTrue(result['results'])
            run('methods.py','compare','--index',tmp/'index.json','method-lab/f-map@1.0.0','method-lab/f-evidence@1.0.0','--output',tmp/'comparison.json')
            self.assertEqual(read(tmp/'comparison.json')['status'],'comparison-only')


if __name__=='__main__':unittest.main()
