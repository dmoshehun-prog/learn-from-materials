"""Server-rendered fallbacks for the whole-material view and content sources."""
from html import escape

def content_sources(unit, language):
    heading='原文出处' if language=='zh-CN' else 'Original sources'
    note='单元页段；未提供更细定位的条目沿用此范围。' if language=='zh-CN' else 'Unit range; items without a finer locator inherit this range.'
    return '<details class="unit-source-disclosure"><summary>'+heading+'</summary><p>'+escape(unit['source'])+'</p><small>'+note+'</small></details>'

def overview_markup(data):
    model=data.get('methodology')
    if not model: return ''
    en=data['meta']['language']=='en'
    title='Whole-material methodology' if en else '整份材料的方法论'
    # Template is moved into the action-rules module by the fixed renderer script.
    body='<section class="whole-method" id="wholeMethod">'
    if model['status']=='not-applicable':
        body+='<p>'+escape(model['problem'])+'</p></section>'
        return '<template id="wholeMethodTemplate">'+body+'</template>'
    body+='<div class="method-map" id="methodMap"></div><div id="methodNodeDetail" class="method-node-detail" aria-live="polite" hidden></div>'
    body+='<details class="whole-text"><summary>'+('Complete structure and sources' if en else '完整步骤、逻辑关系与出处')+'</summary>'
    body+='<p>'+escape(model['note'])+'</p><p>'+escape(model['outcome'])+'</p>'
    for n in model['nodes']:
        body+='<h4>'+escape(n['title'])+'</h4><p>'+escape(n['action'])+'</p><p>'+escape(n['output'])+'</p>'
        for s in n['sources']: body+='<p class="relation-source">'+escape(s['source'])+'</p>'
        linked=[r for r in data.get('decisionRules',[]) if r.get('id') in n['methodIds']]
        if linked:
            body+='<h5>'+('Related action rules' if en else '关联行动规则')+'</h5>'
            for r in linked:
                body+='<p>'+escape(r['when']+' → '+r['do']+' · '+r['because'])+'</p><p class="relation-source">'+escape(r['source'])+'</p>'
    names={n['id']:n['title'] for n in model['nodes']}
    for e in model['edges']:
        body+='<p>'+escape(names[e['from']]+' → '+names[e['to']]+' · '+e['condition']+' · '+e['handoff']+' · '+e['why'])+'</p><p class="relation-source">'+escape(e['source'])+'</p>'
    body+='<div class="method-constraints">'
    for c in model['constraints']: body+='<p title="'+escape(c['source'],quote=True)+'">'+escape(c['text'])+'</p>'
    body+='</div></details></section>'
    return '<template id="wholeMethodTemplate">'+body+'</template>'
