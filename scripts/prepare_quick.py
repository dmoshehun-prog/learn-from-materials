"""Validate quick content, then derive compact indexes without model rewrites."""
import argparse
from pathlib import Path
from render_page import validate
from verify_coverage import load_json
from verify_quick import verify_quick


def prepare(page: Path, kb: Path) -> None:
    data = load_json(page)
    validate(data)
    if data['meta']['learningDepth'] != 'quick':
        raise ValueError('prepare_quick 仅用于 quick 模式')
    errors = verify_quick(data, kb)
    if errors:
        raise ValueError('\n'.join(errors))
    audit = load_json(kb / 'quick-audit.json')
    index = ['# ' + data['meta']['title'], '', '核心导读，非全量知识整理。',
             '原文：full_text.txt；出处：source_map.json；限制：coverage-audit.md',
             '题库未在此步骤预建；启动测验时检查所选范围原题。', '']
    for unit in data.get('contentUnits', []):
        index.extend(['## ' + unit['id'] + ' · ' + unit['title'], unit['core'], unit['source'], ''])
    (kb / 'INDEX.md').write_text('\n'.join(index), encoding='utf-8')
    lines = ['# 快速导读范围说明', '', *audit['limitations'], '']
    for group in audit['structure']:
        lines.extend(['## ' + group['title'], group['status'] + '：' + group['note'], ''])
    (kb / 'coverage-audit.md').write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('page', type=Path)
    parser.add_argument('--knowledge-base', '-k', type=Path, required=True)
    args = parser.parse_args()
    try:
        prepare(args.page, args.knowledge_base)
    except (ValueError, OSError) as exc:
        parser.exit(2, str(exc) + '\n')
    print('快速导读校验与索引生成完成')
