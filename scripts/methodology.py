"""Validate, preserve and bind a whole-material reasoning/application structure."""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

SCHEMA = 'learn-from-materials/methodology-v1'
ID = re.compile(r'^[A-Za-z][A-Za-z0-9_-]*$')

def require(ok, message):
    if not ok:
        raise ValueError('methodology: ' + message)

def words(value):
    return isinstance(value, str) and bool(value.strip())

def text_fields(obj, fields):
    require(isinstance(obj, dict), 'object required')
    for key in fields:
        require(words(obj.get(key)), key + ' must be nonempty text')

def strings(value, nonempty=True):
    return isinstance(value, list) and (bool(value) or not nonempty) and all(words(v) for v in value)

def validate(model, page=None, kb=None):
    require(isinstance(model, dict), 'object required')
    fields = {'schemaVersion','id','version','language','status','structure','title','problem','outcome','evidence','note','entryNodes','mainPath','nodes','edges','constraints','coverage'}
    require(set(model) == fields, 'unexpected or missing root fields')
    require(model['schemaVersion'] == SCHEMA, 'unsupported schema')
    text_fields(model, ('id','version','title','problem','outcome','note'))
    require(ID.fullmatch(model['id']), 'invalid id')
    require(re.fullmatch(r'\d+\.\d+\.\d+', model['version']), 'invalid version')
    require(model['language'] in ('en','zh-CN'), 'invalid language')
    require(model['status'] in ('ready','not-applicable'), 'invalid status')
    require(model['structure'] in ('process','decision_tree','causal','hierarchy','none'), 'invalid structure')
    require(model['evidence'] in ('material','synthesis'), 'invalid evidence')
    for field in ('entryNodes','mainPath','nodes','edges','constraints','coverage'):
        require(isinstance(model[field], list), field + ' must be an array')
    if page:
        require(page['meta']['language'] == model['language'], 'page language mismatch')
    if model['status'] == 'not-applicable':
        require(model['structure'] == 'none' and not any(model[k] for k in ('nodes','edges','entryNodes','mainPath','constraints')), 'not-applicable requires no invented structure')
    else:
        require(model['structure'] != 'none' and model['nodes'], 'ready needs a structure and nodes')
    nodes = {}
    all_sources = []
    for n in model['nodes']:
        require(set(n) == {'id','title','role','input','action','output','check','unitIds','methodIds','evidence','sources'}, 'unexpected node fields')
        text_fields(n, ('id','title','input','action','output','check'))
        require(ID.fullmatch(n['id']) and n['id'] not in nodes, 'invalid or duplicate node id')
        require(n['role'] in ('action','decision','concept'), 'invalid node role')
        require(n['evidence'] in ('material','inference'), 'invalid node evidence')
        require(strings(n['unitIds']) and strings(n['methodIds'], False), 'invalid node references')
        require(isinstance(n['sources'], list) and n['sources'], 'node evidence required')
        for s in n['sources']:
            require(set(s) == {'source','sourceIds','quote'}, 'source needs source/sourceIds/quote')
            text_fields(s, ('source','quote'))
            require(strings(s['sourceIds']), 'source IDs required')
            all_sources.append(s)
        nodes[n['id']] = n
    require(strings(model['entryNodes'], False) and strings(model['mainPath'], False), 'invalid path')
    for field in ('entryNodes','mainPath'):
        require(len(set(model[field])) == len(model[field]) and set(model[field]) <= set(nodes), 'invalid ' + field)
    if nodes:
        require(model['entryNodes'], 'entry node required')
    if model['structure'] == 'process' and nodes:
        require(model['mainPath'] and model['mainPath'][0] in model['entryNodes'], 'process needs a main path starting at an entry')
    edge_ids = set()
    for e in model['edges']:
        require(set(e) == {'id','from','to','kind','condition','handoff','why','evidence','source'}, 'unexpected edge fields')
        text_fields(e, ('id','from','to','condition','handoff','why','source'))
        require(ID.fullmatch(e['id']) and e['id'] not in edge_ids, 'invalid or duplicate edge id')
        edge_ids.add(e['id'])
        require(e['from'] in nodes and e['to'] in nodes and e['from'] != e['to'], 'dangling edge')
        require(e['kind'] in ('main','branch','feedback','supports','contains','causes','prerequisite','parallel','contrasts'), 'invalid edge kind')
        require(e['evidence'] in ('material','inference'), 'invalid edge evidence')
    for a,b in zip(model['mainPath'], model['mainPath'][1:]):
        require(any(e['from']==a and e['to']==b and e['kind']=='main' for e in model['edges']), 'main path has a missing handoff')
    reached=set(model['entryNodes'])
    while True:
        next_set=reached | {e['to'] for e in model['edges'] if e['from'] in reached}
        if next_set == reached: break
        reached=next_set
    require(reached == set(nodes), 'unreachable/disconnected nodes')
    for c in model['constraints']:
        require(set(c) == {'text','evidence','source'}, 'invalid constraint fields')
        text_fields(c, ('text','source'))
        require(c['evidence'] in ('material','inference'), 'invalid constraint evidence')
    if model['evidence']=='material':
        require(all(x['evidence']=='material' for x in [*model['nodes'],*model['edges'],*model['constraints']]), 'inferred structure must be labeled synthesis')
    seen=set()
    for c in model['coverage']:
        require(set(c)=={'unitId','nodeIds','role','reason'}, 'invalid coverage fields')
        text_fields(c, ('unitId','reason'))
        require(c['unitId'] not in seen, 'duplicate coverage unit')
        seen.add(c['unitId'])
        require(c['role'] in ('core','evidence','context','out-of-scope'), 'invalid coverage role')
        require(strings(c['nodeIds'], False) and set(c['nodeIds']) <= set(nodes), 'unknown coverage node')
        if c['role'] in ('core','evidence'): require(c['nodeIds'], 'core/evidence unit must map to a node')
    if page:
        unit_ids={u['id'] for u in page['contentUnits']}
        method_ids={n['id'] for key in ('frameworks','decisionRules') for n in page[key]}
        require(seen == unit_ids, 'account for every content unit, including context and exclusions')
        for n in nodes.values():
            require(set(n['unitIds']) <= unit_ids and set(n['methodIds']) <= method_ids, 'unknown unit/method reference')
    if kb:
        kb=Path(kb)
        raw=(kb/'full_text.txt').read_text(encoding='utf-8')
        blocks={b['source_id']:b for b in json.loads((kb/'source_map.json').read_text(encoding='utf-8'))}
        for s in all_sources:
            passages=[]
            for key in s['sourceIds']:
                require(key in blocks, 'unknown evidence block')
                b=blocks[key]; a,z=b['start_char'],b['end_char']
                require(type(a) is int and type(z) is int and 0 <= a <= z <= len(raw), 'invalid evidence range')
                excerpt=raw[a:z]
                require(hashlib.sha256(excerpt.encode()).hexdigest()==b['content_sha256'], 'stale evidence')
                passages.append(excerpt)
            require(any(s['quote'] in p for p in passages), 'quote absent from evidence blocks')
    return model

def markdown(model):
    en=model['language']=='en'
    say=lambda zh,en_text: en_text if en else zh
    lines=['# '+model['title'],'',model['note'],'',say('目标：','Goal: ')+model['outcome'],'']
    for n in model['nodes']:
        lines += ['## '+n['title'],'',say('证据类型：','Evidence: ')+n['evidence'],'']
        for k,zh,eng in [('input','输入','Input'),('action','行动 / 关系含义','Action / meaning'),('output','产出','Output'),('check','检查','Check')]:
            lines += [say(zh,eng)+': '+n[k],'']
        lines += [s['source'] for s in n['sources']]+['']
    names={n['id']:n['title'] for n in model['nodes']}
    for e in model['edges']:
        lines += [f"- {names[e['from']]} → {names[e['to']]} ({e['kind']}; {e['evidence']})",'  '+e['condition'],'  '+e['handoff'],'  '+e['why'],'  '+e['source'],'']
    lines += [say('## 全程约束','## Constraints'),'']+[c['text']+' — '+c['source'] for c in model['constraints']]
    return '\n'.join(lines)+'\n'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('validate','export','bind'))
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--page', type=Path, required=True)
    p.add_argument('--knowledge-base', type=Path, required=True)
    p.add_argument('--output', type=Path)
    p.add_argument('--replace', action='store_true')
    a=p.parse_args()
    try:
        model=json.loads(a.model.read_text(encoding='utf-8')); page=json.loads(a.page.read_text(encoding='utf-8'))
        validate(model,page,a.knowledge_base)
        if a.command=='validate': return
        require(a.output is not None, '--output required')
        if a.command=='bind':
            page=copy.deepcopy(page); page['methodology']=model
            from render_page import validate as validate_page
            validate_page(page)
            value=json.dumps(page,ensure_ascii=False,indent=2)+'\n'
        else: value=markdown(model)
        require(not a.output.exists() or a.replace or a.output.read_text(encoding='utf-8')==value, 'choose a new output or --replace after backup')
        a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(value,encoding='utf-8')
    except (ValueError,OSError,KeyError,TypeError) as exc:
        p.exit(2,str(exc)+'\n')

if __name__=='__main__': main()
