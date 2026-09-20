"""Version 4.3 contracts and offline relation/application controls."""
from html import escape
import re

RELATION_TYPES = {
    'prerequisite', 'sequence', 'causes', 'supports', 'contrasts',
    'part_of', 'applies', 'feedback', 'parallel',
}
ID = re.compile(r'^[A-Za-z][A-Za-z0-9_-]*$')


def validate_extensions(data, errors):
    meta = data.get('meta') if isinstance(data.get('meta'), dict) else {}
    version = data.get('schemaVersion')
    if version == '4.3' and meta.get('language') not in ('zh-CN', 'en'):
        errors.append('meta.language must be zh-CN or en for schema 4.3')
    elif 'language' in meta and meta['language'] not in ('zh-CN', 'en'):
        errors.append('meta.language must be zh-CN or en')
    if meta.get('mode') != 'overview':
        return
    ids = set()
    for collection in ('frameworks', 'decisionRules'):
        items = data.get(collection)
        for index, item in enumerate(items if isinstance(items, list) else []):
            if not isinstance(item, dict):
                continue
            key = item.get('id')
            if key is None and version == '4.2':
                continue
            if not isinstance(key, str) or not ID.fullmatch(key) or key in ids:
                errors.append(f'{collection}[{index}].id must be valid and unique across frameworks and rules')
            else:
                ids.add(key)
    edges = data.get('relationships', [])
    if not isinstance(edges, list):
        errors.append('relationships must be an array')
        return
    edge_ids = set()
    allowed = {'id', 'from', 'to', 'type', 'explanation', 'evidence', 'source'}
    for i, edge in enumerate(edges):
        prefix = f'relationships[{i}]'
        if not isinstance(edge, dict):
            errors.append(prefix + ' must be an object')
            continue
        if set(edge) != allowed or any(not isinstance(edge.get(k), str) or not edge[k].strip() for k in allowed):
            errors.append(prefix + ' requires exactly id/from/to/type/explanation/evidence/source as nonempty strings')
            continue
        if not ID.fullmatch(edge['id']) or edge['id'] in edge_ids:
            errors.append(prefix + '.id must be valid and unique')
        edge_ids.add(edge['id'])
        if edge['from'] not in ids or edge['to'] not in ids or edge['from'] == edge['to']:
            errors.append(prefix + ' must connect two different existing framework/rule IDs')
        if edge['type'] not in RELATION_TYPES:
            errors.append(prefix + '.type is unsupported')
        if edge['evidence'] not in ('material', 'inference'):
            errors.append(prefix + '.evidence must be material or inference')


def extension_markup(data):
    if data['meta']['mode'] != 'overview':
        return ''
    en = data['meta'].get('language') == 'en'
    def label(zh, english):
        return english if en else zh
    options = [f'<option value="auto">{label("由 AI 判断适用方法", "Ask AI to select suitable methods")}</option>']
    for name in ('frameworks', 'decisionRules'):
        for item in data.get(name, []):
            key = item.get('id')
            if not key:
                continue
            title = item.get('name') or item.get('do')
            options.append(f'<option value="{escape(key, quote=True)}">{escape(title)}</option>')
    return f'''
<dialog id="methodDialog" class="method-dialog" aria-labelledby="methodTitle">
 <form id="methodForm">
  <div class="method-heading"><h2 id="methodTitle">{label('一键使用方法论', 'Apply these methods to my problem')}</h2>
  <button id="methodClose" type="button" aria-label="{label('关闭', 'Close')}">×</button></div>
  <p>{label('填写问题，生成口令，再粘贴到当前材料对话。页面本身不调用 AI。', 'Describe your problem, copy the prompt, and paste it into your material conversation. This page does not call AI.')}</p>
  <label for="methodSelect">{label('选择方法', 'Choose a method')}</label><select id="methodSelect">{''.join(options)}</select>
  <label for="methodProblem">{label('我遇到的问题（必填）', 'My problem (required)')}</label><textarea id="methodProblem" required maxlength="4000" rows="3"></textarea>
  <label for="methodGoal">{label('我希望达到的结果（选填）', 'Desired outcome (optional)')}</label><textarea id="methodGoal" maxlength="2000" rows="2"></textarea>
  <label for="methodLimits">{label('限制条件（选填）', 'Constraints (optional)')}</label><textarea id="methodLimits" maxlength="2000" rows="2"></textarea>
  <button class="method-primary" type="submit">{label('生成并复制口令', 'Generate and copy prompt')}</button>
  <p id="methodStatus" role="status"></p>
  <label for="methodPrompt">{label('口令预览 / 手动复制', 'Prompt preview / manual copy')}</label><textarea id="methodPrompt" readonly rows="7"></textarea>
 </form>
</dialog>'''


def relations_markdown(data):
    en = data['meta'].get('language') == 'en'
    nodes = {item.get('id'): item.get('name') or item.get('do') for name in ('frameworks', 'decisionRules') for item in data.get(name, [])}
    edges = data.get('relationships', [])
    if not edges:
        return ''
    lines = ['\n## ' + ('Relationships' if en else '逻辑关系'), '']
    for edge in edges:
        badge = ('Material evidence' if en else '材料依据') if edge['evidence'] == 'material' else ('Inference for understanding' if en else '辅助理解的推断')
        lines += [f"- {nodes[edge['from']]} → {nodes[edge['to']]} ({edge['type']}; {badge})", f"  {edge['explanation']}", f"  {'Source' if en else '出处'}: {edge['source']}", '']
    return '\n'.join(lines)
