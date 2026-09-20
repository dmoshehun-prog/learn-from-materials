"""Local, source-grounded method cards, derived Markdown and cumulative indexes."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

SCHEMA = 'learn-from-materials/methods-v1'
INDEX_SCHEMA = 'learn-from-materials/method-index-v1'
ID = re.compile(r'^[A-Za-z][A-Za-z0-9_-]*$')
VERSION = re.compile(r'^\d+\.\d+\.\d+$')
REF = re.compile(r'^[A-Za-z][A-Za-z0-9_-]*/[A-Za-z][A-Za-z0-9_-]*@\d+\.\d+\.\d+$')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def text(value):
    return isinstance(value, str) and bool(value.strip())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_library(lib, kb=None):
    require(isinstance(lib, dict), 'Method library must be an object')
    require(set(lib) == {'schemaVersion','libraryId','title','language','status','note','methods'}, 'Unexpected/missing method-library fields')
    require(lib['schemaVersion'] == SCHEMA, 'Unsupported method-library schema')
    require(text(lib['libraryId']) and ID.fullmatch(lib['libraryId']), 'Invalid libraryId')
    require(lib['language'] in ('en','zh-CN'), 'Unsupported library language')
    require(text(lib['title']) and text(lib['note']), 'Library title/note required')
    require(lib['status'] in ('extracted','none') and isinstance(lib['methods'],list), 'Invalid library status/methods')
    require(bool(lib['methods']) == (lib['status']=='extracted'), 'Empty methods require status=none and an explanatory note')
    seen=set()
    fields={'id','version','kind','name','summary','problem','when','prerequisites','limitations','rationale','steps','successChecks','tags','evidence','source','sources','parents'}
    for m in lib['methods']:
        require(isinstance(m,dict) and set(m)==fields, 'Unexpected/missing method-card fields')
        for key in ('id','version','name','summary','problem','when','rationale','source'):
            require(text(m[key]), f'Method {key} must be nonempty text')
        require(ID.fullmatch(m['id']) and m['id'] not in seen, 'Invalid/duplicate method ID')
        seen.add(m['id'])
        require(VERSION.fullmatch(m['version']), 'Method version must be MAJOR.MINOR.PATCH')
        require(m['kind'] in ('framework','rule'), 'Method kind must be framework/rule')
        require(m['evidence'] in ('material','inference','synthesis'), 'Invalid evidence kind')
        for key in ('prerequisites','limitations','successChecks','tags'):
            require(isinstance(m[key],list) and bool(m[key]) and all(text(x) for x in m[key]), f'Method {key} must be a nonempty text list; state unknown limits explicitly')
        require(isinstance(m['steps'],list) and bool(m['steps']), 'Method requires executable steps')
        for step in m['steps']:
            require(isinstance(step,dict) and set(step)=={'action','input','output','check'} and all(text(x) for x in step.values()), 'Steps require action/input/output/check')
        require(isinstance(m['sources'],list) and bool(m['sources']), 'Method sources required')
        locators=[]
        for source in m['sources']:
            require(isinstance(source,dict) and set(source)=={'locator','sourceIds','quote'}, 'Source requires locator/sourceIds/quote')
            require(text(source['locator']) and text(source['quote']), 'Source locator and short evidence quote required')
            require(isinstance(source['sourceIds'],list) and bool(source['sourceIds']) and all(text(x) for x in source['sourceIds']), 'Source IDs required')
            locators.append(source['locator'])
        require(m['source'] in locators, 'Primary source must match one evidence locator')
        require(isinstance(m['parents'],list) and all(text(x) and REF.fullmatch(x) for x in m['parents']), 'Invalid parent references')
        require(len(set(m['parents']))==len(m['parents']), 'Duplicate parent references')
        ref=f"{lib['libraryId']}/{m['id']}@{m['version']}"
        require(ref not in m['parents'], 'A method cannot derive from itself')
        if m['evidence']=='material': require(not m['parents'], 'Material cards must not claim synthesized ancestry')
        if m['evidence']=='synthesis': require(len(m['parents'])>=2, 'Synthesis requires at least two versioned parents')
    if kb is not None:
        kb=Path(kb)
        raw=(kb/'full_text.txt').read_text(encoding='utf-8')
        blocks=read(kb/'source_map.json')
        require(isinstance(blocks,list) and all(isinstance(b,dict) and text(b.get('source_id')) for b in blocks), 'Invalid source map')
        by_id={b['source_id']:b for b in blocks}
        require(len(by_id)==len(blocks), 'Duplicate source IDs')
        for m in lib['methods']:
            for source in m['sources']:
                passages=[]
                for key in source['sourceIds']:
                    require(key in by_id, f'Unknown source ID: {key}')
                    b=by_id[key]; a,z=b.get('start_char'),b.get('end_char')
                    require(type(a) is int and type(z) is int and 0<=a<=z<=len(raw), 'Invalid source range')
                    excerpt=raw[a:z]
                    require(hashlib.sha256(excerpt.encode()).hexdigest()==b.get('content_sha256'), 'Source changed: rebuild/review affected cards')
                    passages.append(excerpt)
                require(any(source['quote'] in s for s in passages), 'Evidence quote absent from declared source blocks')
    return lib


def project(card, original):
    result=copy.deepcopy(original)
    result.update(id=card['id'],when=card['when'],source=card['source'])
    if card['kind']=='framework': result.update(name=card['name'],oneLine=card['summary'])
    else: result.update(do=card['name'],because=card['rationale'])
    return result


def bind(page, lib):
    validate_library(lib)
    require(page.get('schemaVersion')=='4.3' and page['meta']['mode']=='overview', 'Method binding requires a 4.3 overview page')
    require(page['meta']['language']==lib['language'], 'Page/library languages differ')
    result=copy.deepcopy(page)
    for card in lib['methods']:
        require(card['evidence']=='material', 'Derived cards stay in the separate method library, not in material-fact page modules')
        collection='frameworks' if card['kind']=='framework' else 'decisionRules'
        candidates=[(i,n) for i,n in enumerate(result[collection]) if n.get('id')==card['id']]
        require(len(candidates)==1, f"Missing page node: {card['id']}")
        i,original=candidates[0]
        if card['kind']=='framework':
            for unit in result['contentUnits']:
                unit['frameworks']=[card['name'] if n==original['name'] else n for n in unit['frameworks']]
        result[collection][i]=project(card,original)
    result['methodLibrary']=copy.deepcopy(lib)
    return result


def validate_binding(page):
    if 'methodLibrary' not in page: return
    lib=validate_library(page['methodLibrary'])
    expected=bind(page,lib)
    require(expected['frameworks']==page['frameworks'] and expected['decisionRules']==page['decisionRules'], 'Page cards drifted from methods.json; run methods.py bind again')


def patterns(lib):
    validate_library(lib)
    en=lib['language']=='en'
    say=lambda zh,eng:eng if en else zh
    lines=['# '+lib['title'], '',say('由 methods.json 生成；修改主数据后重新生成。','Generated from methods.json; edit the source data and regenerate.'),'',lib['note'],'']
    for m in lib['methods']:
        lines += ['## '+m['name'],'',f"`{lib['libraryId']}/{m['id']}@{m['version']}` · {m['evidence']}",'',m['summary'],'']
        for key,zh,eng in [('problem','解决的问题','Problem'),('when','适用场景','When to use'),('prerequisites','使用前提','Prerequisites'),('limitations','限制与不适用情况','Limitations'),('rationale','原理与依据','Rationale'),('successChecks','效果检查','Success checks')]:
            value=m[key]; lines += ['### '+say(zh,eng),'']+(['- '+x for x in value] if isinstance(value,list) else [value])+['']
        lines += ['### '+say('执行步骤','Steps'),'']
        for i,s in enumerate(m['steps'],1):
            lines += [f"{i}. {s['action']}",f"   - {say('输入','Input')}: {s['input']}",f"   - {say('产出','Output')}: {s['output']}",f"   - {say('检查','Check')}: {s['check']}"]
        lines += ['', '### '+say('出处与短引文','Sources and short evidence quotes'),'']
        for s in m['sources']: lines += ['- '+s['locator']+' ['+', '.join(s['sourceIds'])+']', '  '+s['quote']]
        if m['parents']: lines += ['',say('派生自：','Derived from: ')+', '.join(m['parents'])]
        lines += ['']
    return '\n'.join(lines).rstrip()+'\n'


def validate_index(index):
    require(isinstance(index,dict) and set(index)=={'schemaVersion','entries'} and index['schemaVersion']==INDEX_SCHEMA and isinstance(index['entries'],dict), 'Invalid method index')
    for ref,entry in index['entries'].items():
        require(isinstance(entry,dict) and set(entry)=={'libraryId','title','language','card','sha256'}, 'Invalid index entry')
        m=entry['card']
        lib=dict(schemaVersion=SCHEMA,libraryId=entry['libraryId'],title=entry['title'],language=entry['language'],status='extracted',note='Indexed snapshot',methods=[m])
        validate_library(lib)
        require(ref==f"{entry['libraryId']}/{m['id']}@{m['version']}" and entry['sha256']==digest(m), 'Index identity/hash mismatch')
    colors={}
    for start in index['entries']:
        if colors.get(start)==2: continue
        stack=[(start,False)]
        while stack:
            ref,leaving=stack.pop()
            require(ref in index['entries'], f'Unresolved parent: {ref}')
            if leaving: colors[ref]=2;continue
            if colors.get(ref)==2: continue
            require(colors.get(ref)!=1,'Cyclic method ancestry')
            colors[ref]=1;stack.append((ref,True))
            stack.extend((parent,False) for parent in index['entries'][ref]['card']['parents'])
    return index


def accumulate(libraries, previous=None):
    result=copy.deepcopy(validate_index(previous)) if previous is not None else {'schemaVersion':INDEX_SCHEMA,'entries':{}}
    for lib in libraries:
        validate_library(lib)
        for card in lib['methods']:
            ref=f"{lib['libraryId']}/{card['id']}@{card['version']}"
            entry={k:lib[k] for k in ('libraryId','title','language')}
            entry.update(card=copy.deepcopy(card),sha256=digest(card))
            old=result['entries'].get(ref)
            require(old is None or old==entry, f'Conflicting immutable version: {ref}; increment version, do not overwrite')
            result['entries'][ref]=entry
    return validate_index(result)


def tokens(value):
    value=value.casefold()
    return set(re.findall(r'[a-z0-9]{2,}',value)) | {s[i:i+2] for s in re.findall(r'[\u3400-\u9fff]+',value) for i in range(max(1,len(s)-1))}


def search(index, query, limit=10):
    validate_index(index); q=tokens(query)
    ranked=[]
    for ref,e in index['entries'].items():
        m=e['card']; corpus=' '.join([m['name'],m['summary'],m['problem'],m['when'],*m['tags']])
        score=len(q & tokens(corpus))
        if score: ranked.append({'ref':ref,'keywordMatches':score,'card':copy.deepcopy(m),'language':e['language'],'materialTitle':e['title']})
    return sorted(ranked,key=lambda x:(-x['keywordMatches'],x['ref']))[:limit]


def save(path, value, replace=False):
    path=Path(path)
    content=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    if path.exists():
        if path.read_text(encoding='utf-8')==content: return
        require(replace, f'Output exists: {path}; choose a new path or explicitly use --replace after backup')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(content,encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ('validate','export','bind'):
        p=sub.add_parser(name); p.add_argument('--library',type=Path,required=True); p.add_argument('--knowledge-base',type=Path,required=True)
        if name!='validate': p.add_argument('--output',type=Path,required=True); p.add_argument('--replace',action='store_true')
        if name=='bind': p.add_argument('--page',type=Path,required=True)
    p=sub.add_parser('index');p.add_argument('libraries',type=Path,nargs='+');p.add_argument('--previous',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--replace',action='store_true')
    p=sub.add_parser('search');p.add_argument('--index',type=Path,required=True);p.add_argument('--query',required=True);p.add_argument('--limit',type=int,default=10)
    p=sub.add_parser('compare');p.add_argument('--index',type=Path,required=True);p.add_argument('refs',nargs='+');p.add_argument('--output',type=Path,required=True);p.add_argument('--replace',action='store_true')
    args=parser.parse_args()
    try:
        if args.command in ('validate','export','bind'):
            lib=validate_library(read(args.library),args.knowledge_base)
            if args.command=='export': save(args.output,patterns(lib),args.replace)
            if args.command=='bind':
                from render_page import validate
                page=bind(read(args.page),lib);validate(page);save(args.output,page,args.replace)
        elif args.command=='index':
            result=accumulate([read(p) for p in args.libraries],read(args.previous) if args.previous else None)
            save(args.output,result,args.replace)
        elif args.command=='search':
            require(1<=args.limit<=100,'limit must be 1..100')
            print(json.dumps({'notice':'Keyword candidates only; assess applicability and verify current sources before use.','results':search(read(args.index),args.query,args.limit)},ensure_ascii=False,indent=2))
        else:
            index=validate_index(read(args.index));require(len(set(args.refs))>=2,'Select at least two different method references')
            require(all(ref in index['entries'] for ref in args.refs),'Unknown method reference')
            result={'status':'comparison-only','notice':'Not a merged method. Compare prerequisites, limitations, steps and evidence; record conflicts. Synthesis requires a new ID and explicit parent references.','candidates':[{ 'ref':ref,**index['entries'][ref]} for ref in args.refs]}
            save(args.output,result,args.replace)
    except (ValueError,OSError,KeyError,TypeError) as exc: parser.exit(2,str(exc)+'\n')


if __name__=='__main__': main()
