"""Lightweight source checks; semantic support still requires reader review."""
from pathlib import Path
import hashlib
from verify_coverage import load_json, collect_sources, PDF_RANGE, SLIDE_RANGE, EPUB_RANGE, expand_range


def verify_quick(data: dict, kb: Path) -> list[str]:
    required = ('full_text.txt', 'metadata.json', 'source_manifest.json', 'source_map.json',
                'material-security-report.json', 'performance-report.json', 'quick-audit.json')
    missing = [f'快速知识库缺少：{name}' for name in required if not (kb / name).is_file()]
    if missing:
        return missing
    audit = load_json(kb / 'quick-audit.json')
    manifest = load_json(kb / 'source_manifest.json')
    source_map = load_json(kb / 'source_map.json')
    if not isinstance(audit, dict) or audit.get('schemaVersion') != 'learn-from-materials/quick-audit-v1' or audit.get('learningDepth') != 'quick':
        return ['quick-audit 格式或深度错误']
    if not isinstance(manifest, dict) or not isinstance(manifest.get('sources'), list) or not manifest['sources']:
        return ['manifest.sources 必须为非空数组']
    if not isinstance(source_map, list) or not source_map or any(not isinstance(x, dict) for x in source_map):
        return ['source_map 必须为非空对象数组']
    text = (kb / 'full_text.txt').read_text(encoding='utf-8')
    errors = []
    blocks = {x.get('source_id'): x for x in source_map}
    filenames = {x.get('filename') for x in manifest['sources'] if isinstance(x, dict)}
    if not all(isinstance(k, str) and k for k in blocks) or len(blocks) != len(source_map):
        return ['来源 ID 必须非空且唯一']
    for block in source_map:
        start, end = block.get('start_char'), block.get('end_char')
        if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start <= end <= len(text):
            errors.append('来源字符范围无效')
            continue
        if hashlib.sha256(text[start:end].encode()).hexdigest() != block.get('content_sha256'):
            errors.append('来源块哈希与原文不一致')
        if Path(str(block.get('source_file', ''))).name not in filenames:
            errors.append('来源块不属于 manifest')
    groups = audit.get('structure')
    if not isinstance(groups, list) or not groups:
        return errors + ['缺少结构扫描记录']
    seen, scanned = [], set()
    for group in groups:
        if not isinstance(group, dict) or group.get('status') not in ('scanned', 'unreadable') or not group.get('title') or not group.get('note'):
            errors.append('结构记录缺少状态、标题或范围说明')
            continue
        ids = group.get('sourceIds')
        if not isinstance(ids, list) or not ids or any(not isinstance(i, str) for i in ids):
            errors.append('结构记录缺少来源 ID')
            continue
        seen.extend(ids)
        if group['status'] == 'scanned':
            scanned.update(ids)
    if len(seen) != len(set(seen)) or set(seen) != set(blocks):
        errors.append('结构扫描必须恰好覆盖全部来源 ID 一次')
    evidence = audit.get('evidence')
    if not isinstance(evidence, list):
        return errors + ['缺少展示出处核查']
    refs = set()
    for item in evidence:
        if not isinstance(item, dict) or not isinstance(item.get('source'), str):
            errors.append('证据格式无效')
            continue
        refs.add(item['source'])
        ids = item.get('sourceIds')
        if not isinstance(ids, list) or not ids or any(not isinstance(i, str) or i not in scanned or i not in blocks for i in ids):
            errors.append('证据引用未知或未核验来源')
            continue
        selected = [blocks[i] for i in ids]
        quote = item.get('quote')
        if item.get('checked') is not True or not isinstance(quote, str) or not quote.strip():
            errors.append('证据必须含已核对的原文摘录')
            continue
        if not any(quote in text[b.get('start_char', 0):b.get('end_char', 0)] for b in selected):
            errors.append('证据摘录不在指定来源块中')
        for part in item['source'].split('；'):
            named = [name for name in filenames if name and name in part]
            if not named and len(filenames) == 1:
                named = list(filenames)
            if not named:
                errors.append('多材料出处必须指明真实文件')
            subset = [b for b in selected if Path(str(b.get('source_file', ''))).name in named]
            if not subset:
                errors.append('出处文件与证据 ID 不一致')
            for regex, field in ((PDF_RANGE, 'pdf_page'), (SLIDE_RANGE, 'slide'), (EPUB_RANGE, 'epub_section')):
                for match in regex.finditer(part):
                    claimed = expand_range(int(match[1]), int(match[2]) if match[2] else None)
                    if not claimed.issubset({b.get(field) for b in subset}):
                        errors.append('出处页码与证据来源范围不一致')
    if refs != set(collect_sources(data)):
        errors.append('展示出处必须全部核对，不能遗漏或引用过时记录')
    limits = audit.get('limitations')
    if not isinstance(limits, list) or not limits or not all(isinstance(s, str) and s.strip() for s in limits):
        errors.append('快速模式必须说明非全量范围和具体限制')
    return errors
