"""Audit systematic-study action rules from source blocks to visible cards and map nodes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

SCHEMA = 'learn-from-materials/action-rule-ledger-v2'
RELATION_REVIEW_TYPES = {
    'framework': {'prerequisite', 'sequence', 'causes', 'supports', 'contrasts', 'part_of', 'applies', 'feedback', 'parallel'},
    'methodology': {'main', 'branch', 'feedback', 'supports', 'contains', 'causes', 'prerequisite', 'parallel', 'contrasts'},
}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _ids(value):
    return isinstance(value, list) and all(_text(x) for x in value) and len(value) == len(set(value))


def validate(ledger, page, kb):
    """Return a complete ledger or raise with a concrete, repairable error.

    This proves that recorded candidates survive into cards and map details. It cannot
    prove that an agent noticed every rule in the original material; the recorded
    per-unit source inventory and a final source reread remain required.
    """
    def need(ok, message):
        if not ok:
            raise ValueError('action-rule-ledger: ' + message)

    kb = Path(kb)
    need(isinstance(ledger, dict) and set(ledger) == {
        'schemaVersion', 'pageId', 'learningDepth', 'units', 'candidates',
        'independentRules', 'independentFrameworks', 'relationStatus', 'relationReason', 'relationReview'
    }, 'missing or unexpected root fields')
    need(ledger['schemaVersion'] == SCHEMA, 'unsupported schema')
    need(page['meta']['mode'] == 'overview' and page['meta']['learningDepth'] == 'systematic', 'systematic overview required')
    need(ledger['pageId'] == page['meta']['pageId'] and ledger['learningDepth'] == 'systematic', 'page identity/depth mismatch')
    need(isinstance(ledger['units'], list) and isinstance(ledger['candidates'], list), 'units/candidates must be arrays')
    need(isinstance(ledger['independentRules'], list) and isinstance(ledger['independentFrameworks'], list), 'independent mappings must be arrays')
    need(ledger['relationStatus'] in ('mapped', 'unsupported') and _text(ledger['relationReason']), 'relation status needs a reason')
    need(isinstance(ledger['relationReview'], dict) and set(ledger['relationReview']) == set(RELATION_REVIEW_TYPES),
         'relationReview must cover framework and methodology graphs')
    framework_ids = {f['id'] for f in page['frameworks']}
    visible_edges = [e for e in page.get('relationships', []) if e.get('from') in framework_ids and e.get('to') in framework_ids]
    model_edges = (page.get('methodology') or {}).get('edges') or []
    for graph, types in RELATION_REVIEW_TYPES.items():
        rows = ledger['relationReview'][graph]
        need(isinstance(rows, list), 'relationReview.' + graph + ' must be an array')
        seen_types = set()
        actual = visible_edges if graph == 'framework' else model_edges
        for row in rows:
            need(isinstance(row, dict) and set(row) == {'type', 'status', 'edgeIds', 'reason'},
                 'relationReview.' + graph + ' entry fields invalid')
            kind = row['type']
            need(kind in types and kind not in seen_types, 'unknown or duplicate reviewed relation type: ' + str(kind))
            seen_types.add(kind)
            need(row['status'] in ('mapped', 'unsupported') and _ids(row['edgeIds']) and _text(row['reason']),
                 'relationReview.' + graph + '.' + kind + ' needs status, edge IDs and reason')
            matching = {e['id'] for e in actual if e.get('type' if graph == 'framework' else 'kind') == kind}
            need(set(row['edgeIds']) == matching,
                 'relationReview.' + graph + '.' + kind + ' does not match visible graph edges')
            need((row['status'] == 'mapped') == bool(matching),
                 'relationReview.' + graph + '.' + kind + ' status disagrees with visible graph')
        need(seen_types == types, 'relationReview.' + graph + ' must address every relation type')

    raw = (kb / 'full_text.txt').read_text(encoding='utf-8')
    source_map = json.loads((kb / 'source_map.json').read_text(encoding='utf-8'))
    audit = json.loads((kb / 'coverage-audit.json').read_text(encoding='utf-8'))
    need(isinstance(audit.get('sourceBlocks'), list) and audit['sourceBlocks'], 'source-block coverage audit required')
    source_by_id = {b['source_id']: b for b in source_map}
    need(len(source_by_id) == len(source_map), 'duplicate source block ID')
    unit_ids = {u['id'] for u in page['contentUnits']}
    mapped = {uid: set() for uid in unit_ids}
    for block in audit.get('sourceBlocks', []):
        if block.get('status') == 'covered':
            for uid in block.get('mappedUnits', []):
                if uid in mapped:
                    mapped[uid].add(block['sourceId'])
    reviewed = {}
    for item in ledger['units']:
        need(isinstance(item, dict) and set(item) == {'unitId', 'status', 'reviewedSourceIds', 'note'}, 'unit entry fields invalid')
        uid = item['unitId']
        need(uid in unit_ids and uid not in reviewed, 'unknown or duplicate unit: ' + str(uid))
        need(item['status'] in ('reviewed', 'no-rules') and _text(item['note']), 'unit must be reviewed or explicitly no-rules')
        need(_ids(item['reviewedSourceIds']), 'invalid reviewedSourceIds for ' + uid)
        need(set(item['reviewedSourceIds']) == mapped[uid], 'unit source blocks not fully reviewed: ' + uid)
        reviewed[uid] = item
    need(set(reviewed) == unit_ids, 'every content unit must have a review entry')

    rule_by_id = {r['id']: r for r in page['decisionRules']}
    need(len(rule_by_id) == len(page['decisionRules']), 'page rule IDs must be unique')
    candidate_ids = set()
    targets = set()
    primary_targets = set()
    unit_candidates = {uid: 0 for uid in unit_ids}
    for item in ledger['candidates']:
        fields = {'id', 'unitId', 'sourceIds', 'quote', 'when', 'do', 'because',
                  'prerequisites', 'exceptions', 'stopCondition', 'status', 'targetRuleId', 'reason'}
        need(isinstance(item, dict) and set(item) == fields, 'candidate entry fields invalid')
        cid, uid = item['id'], item['unitId']
        need(_text(cid) and cid not in candidate_ids, 'duplicate/invalid candidate ID')
        candidate_ids.add(cid)
        need(uid in reviewed and reviewed[uid]['status'] == 'reviewed', 'candidate belongs to unreviewed/no-rules unit: ' + str(uid))
        unit_candidates[uid] += 1
        need(_ids(item['sourceIds']) and item['sourceIds'], 'candidate needs source block IDs: ' + cid)
        need(set(item['sourceIds']) <= set(reviewed[uid]['reviewedSourceIds']), 'candidate source not reviewed in its unit: ' + cid)
        need(all(_text(item[k]) for k in ('quote', 'when', 'do', 'because', 'reason')), 'candidate wording/reason missing: ' + cid)
        need(all(isinstance(item[k], list) and all(_text(x) for x in item[k]) for k in ('prerequisites', 'exceptions')), 'candidate prerequisites/exceptions invalid: ' + cid)
        need(isinstance(item['stopCondition'], str), 'candidate stopCondition must be text: ' + cid)
        need(item['status'] in ('retained', 'merged', 'excluded'), 'candidate disposition invalid: ' + cid)
        passages = []
        for sid in item['sourceIds']:
            need(sid in source_by_id, 'unknown source block: ' + sid)
            block = source_by_id[sid]
            start, end = block.get('start_char'), block.get('end_char')
            need(type(start) is int and type(end) is int and 0 <= start <= end <= len(raw), 'source range invalid: ' + sid)
            passage = raw[start:end]
            need(hashlib.sha256(passage.encode()).hexdigest() == block.get('content_sha256'), 'source block changed: ' + sid)
            passages.append(passage)
        need(any(item['quote'] in p for p in passages), 'quote absent from original: ' + cid)
        target = item['targetRuleId']
        if item['status'] == 'excluded':
            need(target is None, 'excluded candidate cannot target a card: ' + cid)
        else:
            need(_text(target) and target in rule_by_id, 'retained/merged candidate needs a visible card: ' + cid)
            targets.add(target)
            if item['status'] == 'retained':
                need(target not in primary_targets, 'duplicate primary candidate for card: ' + target)
                primary_targets.add(target)
                rule = rule_by_id[target]
                need(all(item[k] == rule[k] for k in ('when', 'do', 'because')), 'card wording drifted from retained candidate: ' + target)
    need(all(item['status'] != 'reviewed' or unit_candidates[uid] for uid, item in reviewed.items()), 'reviewed unit has no candidates; use no-rules with a reason')
    need(targets == set(rule_by_id) and primary_targets == set(rule_by_id), 'candidate-to-card mapping incomplete or card has no primary evidence')

    model = page.get('methodology') or {}
    nodes = model.get('nodes') or []
    mapped_rules = {rid for n in nodes for rid in n.get('methodIds', []) if rid in rule_by_id}
    independent = {}
    for item in ledger['independentRules']:
        need(isinstance(item, dict) and set(item) == {'ruleId', 'reason'}, 'independent rule entry invalid')
        rid = item['ruleId']
        need(rid in rule_by_id and rid not in independent and _text(item['reason']), 'independent rule ID/reason invalid')
        independent[rid] = item['reason']
    need(not (set(independent) & mapped_rules), 'rule cannot be both mapped and independent')
    need(mapped_rules | set(independent) == set(rule_by_id), 'every card must map to a methodology node or documented independent list')
    independent_frameworks = {}
    for item in ledger['independentFrameworks']:
        need(isinstance(item, dict) and set(item) == {'frameworkId', 'reason'}, 'independent framework entry invalid')
        fid = item['frameworkId']
        need(fid in framework_ids and fid not in independent_frameworks and _text(item['reason']), 'independent framework ID/reason invalid')
        independent_frameworks[fid] = item['reason']
    if ledger['relationStatus'] == 'mapped':
        degree = {fid: 0 for fid in framework_ids}
        for edge in page.get('relationships', []):
            if edge.get('from') in degree and edge.get('to') in degree:
                degree[edge['from']] += 1
                degree[edge['to']] += 1
        need(set(independent_frameworks) == {fid for fid, count in degree.items() if count == 0},
             'independentFrameworks must match isolated nodes in the visible graph')
    if ledger['relationStatus'] == 'unsupported':
        need(not any(e.get('from') in framework_ids and e.get('to') in framework_ids for e in page.get('relationships', [])), 'unsupported framework graph contains visible links')
    return ledger


def load_and_validate(page, kb):
    path = Path(kb) / 'action-rule-ledger.json'
    if not path.is_file():
        raise ValueError('Missing action-rule-ledger.json for a new systematic overview; finish per-unit review before delivery')
    return validate(json.loads(path.read_text(encoding='utf-8')), page, kb)
