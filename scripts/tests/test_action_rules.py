import copy
import json
import sys
import tempfile
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from action_rules import SCHEMA, RELATION_REVIEW_TYPES, validate
from verify_relations import check_page
from finalize import finalize


class ActionRuleLedgerTests(unittest.TestCase):
    @staticmethod
    def relation_review(page):
        framework_ids = {f['id'] for f in page['frameworks']}
        graph_edges = {
            'framework': [e for e in page['relationships'] if e['from'] in framework_ids and e['to'] in framework_ids],
            'methodology': page['methodology']['edges'],
        }
        return {graph: [dict(type=kind, status='mapped' if matches else 'unsupported',
                             edgeIds=matches, reason='Reviewed source and graph for this relation type')
                        for kind in sorted(types)
                        for matches in [[e['id'] for e in graph_edges[graph]
                                         if e['type' if graph == 'framework' else 'kind'] == kind]]]
                for graph, types in RELATION_REVIEW_TYPES.items()}

    @classmethod
    def setUpClass(cls):
        cls.page = json.loads((ROOT / 'examples/overview-whole-methodology.json').read_text(encoding='utf-8'))
        cls.kb = ROOT / 'examples/rsi-methodology.learnkb'
        cls.audit = json.loads((cls.kb / 'coverage-audit.json').read_text(encoding='utf-8'))
        cls.blocks = {b['source_id']: b for b in json.loads((cls.kb / 'source_map.json').read_text(encoding='utf-8'))}
        cls.raw = (cls.kb / 'full_text.txt').read_text(encoding='utf-8')

    def ledger(self):
        mapped = {u['id']: [] for u in self.page['contentUnits']}
        for b in self.audit['sourceBlocks']:
            if b['status'] == 'covered':
                for uid in b['mappedUnits']:
                    if uid in mapped:
                        mapped[uid].append(b['sourceId'])
        candidates = []
        for rule in self.page['decisionRules']:
            # This synthetic ledger is a structural fixture, not an assertion that
            # the existing demo exhaustively represents the original paper.
            sid, uid = next((sid, uid) for uid, ids in mapped.items() for sid in ids if ids)
            block = self.blocks[sid]
            passage = self.raw[block['start_char']:block['end_char']]
            candidates.append(dict(id='c-' + rule['id'], unitId=uid, sourceIds=[sid],
                                   quote=passage[:20], when=rule['when'], do=rule['do'],
                                   because=rule['because'], prerequisites=[], exceptions=[],
                                   stopCondition='', status='retained', targetRuleId=rule['id'],
                                   reason='Synthetic mapping for structural tests'))
        active = {c['unitId'] for c in candidates}
        units = [dict(unitId=uid, status='reviewed' if uid in active else 'no-rules',
                      reviewedSourceIds=ids, note='Structural test fixture') for uid, ids in mapped.items()]
        in_map = {rid for n in self.page['methodology']['nodes'] for rid in n['methodIds']}
        framework_ids = {f['id'] for f in self.page['frameworks']}
        degree = {fid: 0 for fid in framework_ids}
        for edge in self.page['relationships']:
            if edge['from'] in degree and edge['to'] in degree:
                degree[edge['from']] += 1
                degree[edge['to']] += 1
        return dict(schemaVersion=SCHEMA, pageId=self.page['meta']['pageId'],
                    learningDepth='systematic', units=units, candidates=candidates,
                    independentRules=[dict(ruleId=r['id'], reason='Displayed as an independent card')
                                      for r in self.page['decisionRules'] if r['id'] not in in_map],
                    independentFrameworks=[dict(frameworkId=fid, reason='Independent in source') for fid, d in degree.items() if d == 0],
                    relationStatus='mapped', relationReason='Visible framework links reviewed',
                    relationReview=self.relation_review(self.page))

    def test_complete_structural_mapping(self):
        ledger = self.ledger()
        validate(ledger, self.page, self.kb)
        self.assertFalse(check_page(self.page, ledger=ledger).errors)

    def test_relation_review_requires_every_type_and_exact_visible_edges(self):
        ledger = self.ledger()
        ledger['relationReview']['framework'].pop()
        with self.assertRaisesRegex(ValueError, 'must address every relation type'):
            validate(ledger, self.page, self.kb)
        ledger = self.ledger()
        row = next(r for r in ledger['relationReview']['methodology'] if r['edgeIds'])
        row['edgeIds'] = []
        with self.assertRaisesRegex(ValueError, 'does not match visible graph edges'):
            validate(ledger, self.page, self.kb)

    def test_unit_gap_or_stale_quote_fails(self):
        ledger = self.ledger()
        ledger['units'].pop()
        with self.assertRaisesRegex(ValueError, 'every content unit'):
            validate(ledger, self.page, self.kb)
        ledger = self.ledger()
        ledger['candidates'][0]['quote'] = 'not present in original'
        with self.assertRaisesRegex(ValueError, 'quote absent'):
            validate(ledger, self.page, self.kb)

    def test_card_or_node_mapping_gap_fails(self):
        ledger = self.ledger()
        ledger['candidates'].pop()
        with self.assertRaisesRegex(ValueError, 'mapping incomplete'):
            validate(ledger, self.page, self.kb)
        ledger = self.ledger()
        ledger['independentRules'] = []
        with self.assertRaisesRegex(ValueError, 'every card'):
            validate(ledger, self.page, self.kb)

    def test_framework_rule_edges_do_not_satisfy_visible_graph(self):
        page = copy.deepcopy(self.page)
        page['relationships'] = [dict(id='e1', **{'from': page['frameworks'][0]['id'], 'to': page['decisionRules'][0]['id']},
                                      type='applies', evidence='material', explanation='A sufficiently specific explanation')]
        report = check_page(page)
        self.assertTrue(any('框架关系图为空' in e for e in report.errors))

    def test_documented_absence_does_not_force_invented_rules_or_edges(self):
        page = copy.deepcopy(self.page)
        page['decisionRules'] = []
        page['relationships'] = []
        for node in page['methodology']['nodes']:
            node['methodIds'] = [x for x in node['methodIds'] if not x.startswith('r-')]
        ledger = self.ledger()
        ledger['candidates'] = []
        ledger['independentRules'] = []
        ledger['independentFrameworks'] = []
        ledger['relationStatus'] = 'unsupported'
        ledger['relationReason'] = 'No supported framework-to-framework relation after rereading'
        ledger['relationReview'] = self.relation_review(page)
        for unit in ledger['units']:
            unit['status'] = 'no-rules'
        validate(ledger, page, self.kb)
        self.assertFalse(check_page(page, ledger=ledger).errors)

    def test_new_delivery_includes_checked_ledger_and_linked_rule_details(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            kb = root / 'source.learnkb'
            shutil.copytree(self.kb, kb)
            (kb / 'action-rule-ledger.json').write_text(json.dumps(self.ledger(), ensure_ascii=False), encoding='utf-8')
            result = finalize(ROOT / 'examples/overview-whole-methodology.json', kb, root / 'out', 'new')
            manifest = json.loads(Path(result['manifest']).read_text(encoding='utf-8'))
            self.assertIn('action-rule-ledger', manifest['checks'])
            self.assertTrue((root / 'out' / 'new.learnkb' / 'action-rule-ledger.json').is_file())
            html = Path(result['html']).read_text(encoding='utf-8')
            self.assertIn('method-linked-rules', html)
            self.assertIn('关联行动规则', html)
            checked = subprocess.run([sys.executable, str(ROOT / 'scripts/verify_relations.py'),
                                      str(ROOT / 'examples/overview-whole-methodology.json'),
                                      '--knowledge-base', str(kb)], text=True, capture_output=True)
            self.assertEqual(checked.returncode, 0, checked.stderr + checked.stdout)


if __name__ == '__main__':
    unittest.main()
