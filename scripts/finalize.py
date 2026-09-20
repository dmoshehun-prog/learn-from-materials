"""Publish a complete offline learning bundle from reviewed canonical data.

Usage: python scripts/finalize.py page.json --knowledge-base topic.learnkb
       --output-dir delivery --name learning
New output names are required; source knowledge bases are never overwritten.
"""
import argparse
import hashlib
import json
import shutil
import uuid
import zipfile
from pathlib import Path

from delivery import check_canonical, export_readable, verify_readable
from methods import bind, read, validate_library
from methodology import validate as validate_model, markdown
from render_page import render, validate as validate_page
from verify_coverage import verify
from verify_static import verify as verify_static
from verify_relations import check_page as check_relations
from action_rules import load_and_validate


def finalize(page_file, kb, output_dir, name, legacy_rule_ledger=False):
    kb, out = Path(kb).resolve(), Path(output_dir).resolve()
    if not name or Path(name).name != name or any(c in name for c in '/\\:') or name in ('.', '..'):
        raise ValueError('name must be a filename stem, not a path')
    page = read(Path(page_file))
    if page['meta']['mode'] != 'overview':
        raise ValueError('finalize.py currently accepts overview pages; topic/unit pages use render_page.py')
    # Fail before publishing anything if either canonical file is missing.
    library = validate_library(read(kb / 'methods.json'), kb)
    model = read(kb / 'methodology.json')
    page = bind(page, library)
    validate_model(model, page, kb)
    page['methodology'] = model
    validate_page(page)
    exports = check_canonical(page, kb)
    ledger = None
    if page['meta']['learningDepth'] == 'systematic' and not legacy_rule_ledger:
        ledger = load_and_validate(page, kb)
    target_kb = out / (name + '.learnkb')
    if target_kb == kb or target_kb.is_relative_to(kb):
        raise ValueError('Choose an output directory outside the source knowledge base')
    targets = {k: out / (name + suffix) for k, suffix in [('page','.page.json'),('html','.html'),('markdown','.md'),('manifest','.delivery.json'),('archive','.zip')]}
    if any(p.exists() for p in [target_kb, *targets.values()]):
        raise ValueError('A delivery target already exists. Choose a new name/directory to preserve the prior output.')
    relation_report = check_relations(page, ledger=ledger, allow_empty=legacy_rule_ledger)
    if relation_report.errors:
        raise ValueError('Relationship graph validation failed: ' + '; '.join(relation_report.errors))
    out.mkdir(parents=True, exist_ok=True)
    stage = out / ('.' + name + '-staging-' + uuid.uuid4().hex)
    stage.mkdir()
    staged_kb = stage / target_kb.name
    staged = {key: stage / path.name for key, path in targets.items()}
    published = []
    try:
        shutil.copytree(kb, staged_kb, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        export_readable(staged_kb, exports)
        page['meta']['knowledgeBase'] = target_kb.name + '/INDEX.md'
        staged['page'].write_text(json.dumps(page,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        errors = verify(staged['page'], staged_kb,
                        require_heading_index=page['meta']['learningDepth'] == 'systematic' and not legacy_rule_ledger)
        if errors:
            raise ValueError('Coverage validation failed: ' + '; '.join(errors))
        render(page, staged['html'], staged['markdown'])
        with staged['markdown'].open('a',encoding='utf-8') as f:
            f.write('\n' + markdown(model))
        errors, warnings, _ = verify_static(staged['html'])
        if errors:
            raise ValueError('Static validation failed: ' + '; '.join(errors))
        verify_readable(staged_kb, exports)
        files = [staged['page'],staged['html'],staged['markdown'],*sorted(p for p in staged_kb.rglob('*') if p.is_file())]
        heading_file = staged_kb / 'source-heading-index.json'
        heading_entries = json.loads(heading_file.read_text(encoding='utf-8')).get('entries', []) if heading_file.is_file() else []
        visual_heading_count = sum(item.get('verification') == 'visual' for item in heading_entries if isinstance(item, dict))
        manifest = {'skillVersion':'0.2.0','status':'complete','pageId':page['meta']['pageId'],
            'checks':['canonical-evidence','coverage','snapshot-equality','derived-files','static-html','relations'] + (['action-rule-ledger'] if ledger else []) + (['pdf-heading-index'] if (staged_kb/'source-heading-index.json').is_file() else []),
            'relations':relation_report.as_dict(),
            'headingIndex':{'textEntries':len(heading_entries)-visual_heading_count,'visualEntries':visual_heading_count},
            'visualReview':'not-performed-by-this-command','warnings':[*warnings,*relation_report.warnings] + (['PDF 标题索引含人工视觉核验条目，程序未验证其文字'] if visual_heading_count else []),
            'files':[{'path':p.relative_to(stage).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
        staged['manifest'].write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        with zipfile.ZipFile(staged['archive'],'x',compression=zipfile.ZIP_DEFLATED) as archive:
            for p in [*files,staged['manifest']]:archive.write(p,p.relative_to(stage))
        with zipfile.ZipFile(staged['archive']) as archive:
            if archive.testzip() is not None:raise ValueError('Archive integrity check failed')
        if any(p.exists() for p in [target_kb, *targets.values()]):
            raise ValueError('A delivery target appeared during validation; choose another name.')
        for source, destination in [(staged_kb, target_kb), *[(staged[key], path) for key, path in targets.items()]]:
            source.rename(destination)
            published.append(destination)
    except Exception:
        for path in reversed(published):
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        raise
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    result={k:str(v) for k,v in targets.items()}
    result['methodology']=str(target_kb/'methodology.md')
    result['methodologyData']=str(target_kb/'methodology.json')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('page',type=Path);p.add_argument('--knowledge-base',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--name',required=True)
    p.add_argument('--legacy-rule-ledger',action='store_true',help='Only for re-delivering an existing overview created before the rule ledger')
    a=p.parse_args()
    try:print(json.dumps(finalize(a.page,a.knowledge_base,a.output_dir,a.name,a.legacy_rule_ledger),ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError,TypeError) as exc:p.exit(2,str(exc)+'\n')


if __name__=='__main__':main()
