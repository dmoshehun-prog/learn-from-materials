(function(){
  'use strict';
  const data=JSON.parse(document.getElementById('pageData').textContent);
  const en=data.meta.language==='en',say=(zh,eng)=>en?eng:zh;
  const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
  const view=document.getElementById('chView');
  if(view){
    const tip=el('div',null,'content-source-tooltip');tip.id='contentSourceTooltip';tip.setAttribute('role','tooltip');tip.hidden=true;document.body.append(tip);
    let active=null;
    function hide(){if(active)active.removeAttribute('aria-describedby');active=null;tip.hidden=true;}
    function show(target,x,y){
      if(!target||!view.contains(target)){hide();return;}
      if(active&&active!==target)active.removeAttribute('aria-describedby');active=target;
      tip.textContent=target.dataset.source;tip.hidden=false;target.setAttribute('aria-describedby',tip.id);
      tip.style.left='12px';tip.style.top='12px';
      const box=tip.getBoundingClientRect();
      tip.style.left=Math.max(12,Math.min(x+12,innerWidth-box.width-12))+'px';
      tip.style.top=Math.max(12,Math.min(y+18,innerHeight-box.height-12))+'px';
    }
    view.addEventListener('pointermove',e=>{if(e.pointerType==='touch')return;show(e.target.closest('[data-source]'),e.clientX,e.clientY);});
    view.addEventListener('pointerleave',hide);
    view.addEventListener('focusin',e=>{const t=e.target.closest('.source-target');if(t){const b=t.getBoundingClientRect();show(t,b.left,b.bottom);}else hide();});
    view.addEventListener('focusout',hide);document.addEventListener('keydown',e=>{if(e.key==='Escape')hide();});
    window.addEventListener('scroll',hide,true);window.addEventListener('resize',hide);
    function decorate(){
      const id=document.querySelector('.ch-nav-btn.active')?.getAttribute('data-ch');const u=(data.contentUnits||[]).find(x=>x.id===id);if(!u)return;
      const detail=u.sourceDetails||{};
      const mark=(n,source,scope)=>{if(!n)return;n.classList.add('source-target');n.setAttribute('data-source',(scope?scope+' · ':'')+source);n.setAttribute('tabindex','0');};
      const fallback=say('单元页段','Unit range');
      mark(view.querySelector('.ch-core'),detail.core||u.source,detail.core?'':fallback);
      const lists=view.querySelectorAll('.ch-block ul');
      ['frameworks','takeaways'].forEach((key,k)=>{lists[k]?.querySelectorAll('li').forEach((n,i)=>mark(n,detail[key]?.[i]||u.source,detail[key]?.[i]?'':fallback));});
      view.querySelectorAll('.chapter-conclusion').forEach((group,i)=>{
        const c=u.conclusions[i],s=detail.conclusions?.[i];
        mark(group.querySelector('.conclusion-summary'),s?.summary||c.source,s?.summary?'':say('结论页段','Conclusion range'));
        group.querySelectorAll('.conclusion-body li').forEach((n,j)=>mark(n,s?.points?.[j]||c.source,s?.points?.[j]?'':say('结论页段','Conclusion range')));
      });
      let disclosure=view.querySelector('.unit-source-disclosure');
      if(!disclosure){
        disclosure=el('details',null,'unit-source-disclosure');disclosure.append(el('summary',say('原文出处','Original sources')),el('p',u.source),el('small',say('未提供更细定位的条目显示单元或结论页段。','Items without finer locators show the unit or conclusion range.')));
        const entries=new Set();
        function collect(v){if(typeof v==='string')entries.add(v);else if(Array.isArray(v))v.forEach(collect);else if(v&&typeof v==='object')Object.values(v).forEach(collect);}
        collect(detail);for(const s of entries)disclosure.append(el('p',s));
        view.insertBefore(disclosure,view.querySelector('.ch-send'));
      }
    }
    decorate();
    const observer=new MutationObserver(()=>{observer.disconnect();hide();decorate();observer.observe(view,{childList:true,subtree:true});});observer.observe(view,{childList:true,subtree:true});
  }
  const model=data.methodology,template=document.getElementById('wholeMethodTemplate'),host=document.getElementById('rules');
  if(!model||!template||!host)return;
  const launch=host.querySelector('#applyMethod'),anchor=host.querySelector('.content-stream');
  host.insertBefore(template.content.cloneNode(true),anchor);template.remove();
  const whole=document.getElementById('wholeMethod');
  // 方法论卡片 = 材料原文行动规则（methods.json 的 decisionRules），与方法论关系图双视图切换。
  // 不渲染带序号的节点卡副本：节点详情只经 describe() 出现在悬浮预览与锁定详情里。
  const cardsPanel=el('div',null,'action-view action-cards-view');
  const graphPanel=el('div',null,'action-view action-graph-view');
  const switcher=el('div',null,'action-view-switcher');
  const cardsButton=el('button',say('方法论卡片','Method cards'),'action-view-button');
  const graphButton=el('button',say('方法论关系图','Methodology map'),'action-view-button');
  cardsButton.type=graphButton.type='button';cardsButton.setAttribute('aria-pressed','true');graphButton.setAttribute('aria-pressed','false');
  switcher.append(cardsButton,graphButton);
  if(launch)cardsPanel.append(launch);
  if(anchor)cardsPanel.append(anchor);
  graphPanel.append(whole);
  host.append(switcher,cardsPanel,graphPanel);
  graphPanel.hidden=true;
  function showView(which){const cards=which==='cards';cardsPanel.hidden=!cards;graphPanel.hidden=cards;cardsButton.setAttribute('aria-pressed',String(cards));graphButton.setAttribute('aria-pressed',String(!cards));}
  cardsButton.onclick=()=>showView('cards');graphButton.onclick=()=>showView('graph');
  if(model.status!=='ready')return;
  const map=document.getElementById('methodMap'),detail=document.getElementById('methodNodeDetail'),nodes=new Map(model.nodes.map(n=>[n.id,n]));
  const names=new Map([...data.frameworks.map(n=>[n.id,n.name]),...data.decisionRules.map(n=>[n.id,n.do])]),units=new Map(data.contentUnits.map(u=>[u.id,u]));
  const ruleCards=new Map(data.decisionRules.map(r=>[r.id,r]));
  const edgeKind={main:say('接着做','Next'),branch:say('条件分支','Conditional branch'),feedback:say('返回修正','Return and revise'),supports:say('提供支持','Supports'),contains:say('包含 / 属于','Contains'),causes:say('促成 / 导致','Causes'),prerequisite:say('先要具备','Prerequisite'),parallel:say('并行 / 并列','In parallel'),contrasts:say('对比','Comparison')};
  const processual=model.structure==='process'||model.structure==='decision_tree';
  // describe() is the single source of wording for a node: the locked detail panel and
  // the hover preview both render it, so the two can never drift apart.
  function describe(id,edgeId,interactive){
    const n=nodes.get(id),frag=document.createDocumentFragment();
    frag.append(el('h4',n.title),el('p',n.evidence==='material'?say('材料依据','Material evidence'):say('根据材料作出的推断（不是原文直接结论）','Inference from the material (not a direct source claim)')));
    const dl=el('dl');[['input',processual?'开始前有什么':'已知条件',processual?'What you start with':'Premises'],['action',processual?'具体怎么做':'这一步说明什么',processual?'What to do':'What this means'],['output',processual?'会得到什么':'可以得出什么',processual?'What you get':'What follows'],['check','怎么确认、哪些还不能确定','How to check and what remains uncertain']].forEach(([k,zh,eng])=>dl.append(el('dt',say(zh,eng)),el('dd',n[k])));frag.append(dl);
    const links=el('ul');model.edges.filter(e=>edgeId?e.id===edgeId:e.from===id||e.to===id).forEach(e=>{
      const li=el('li'),step=e.kind==='main'||e.kind==='branch';
      const condition=e.kind==='feedback'?say('什么时候返回：','When to return: '):step?say('什么时候进入下一步：','When to continue: '):say('这条关系何时成立：','When this relationship holds: ');
      const handoff=e.kind==='feedback'?say('带回什么：','What returns: '):step?say('把什么带到下一步：','What carries forward: '):e.kind==='contrasts'?say('比较什么：','What is compared: '):e.kind==='parallel'?say('共同讨论什么：','What they share: '):e.kind==='contains'?say('包含什么：','What is included: '):e.kind==='prerequisite'?say('提供了什么前提：','What prerequisite is provided: '):e.kind==='causes'?say('产生什么影响：','What effect follows: '):say('支持什么判断：','What this supports: ');
      li.append(el('strong',nodes.get(e.from).title+' → '+nodes.get(e.to).title),el('small',edgeKind[e.kind]||say('关联','Relation')),el('p',condition+e.condition),el('p',handoff+e.handoff),el('p',say('为什么这样连接：','Why they connect: ')+e.why),el('small',(e.evidence==='material'?say('原文依据','Source evidence'):say('根据材料作出的推断','Inference from the material'))+' · '+e.source));links.append(li);
    });
    if(!links.childElementCount)links.append(el('li',say('当前材料未提供与其他卡片的明确关系。','No supported connection to another card is recorded.'),'hover-empty'));
    frag.append(links);
    n.sources.forEach(s=>frag.append(el('p',s.source,'relation-source')));
    if(n.methodIds.length)frag.append(el('p',say('关联框架与规则：','Frameworks and rules: ')+n.methodIds.map(x=>names.get(x)).join(' · ')));
    const associated=n.methodIds.map(x=>ruleCards.get(x)).filter(Boolean);
    if(associated.length){
      const disclosure=el('details',null,'method-linked-rules');
      disclosure.append(el('summary',say('关联行动规则（','Related action rules (')+associated.length+')'));
      associated.forEach(r=>{const card=el('div',null,'method-linked-rule');card.append(el('strong',r.do),el('p',say('当 ','When ')+r.when),el('p',say('因为 ','Because ')+r.because),el('small',r.source));disclosure.append(card);});
      frag.append(disclosure);
    }
    if(interactive)n.unitIds.forEach(unitId=>{const u=units.get(unitId),b=el('button',u.label+' · '+u.title);b.type='button';b.onclick=()=>{document.getElementById('tab-content').click();document.querySelector('[data-ch="'+unitId+'"]')?.click();};frag.append(b);});
    else if(n.unitIds.length)frag.append(el('p',n.unitIds.map(x=>{const u=units.get(x);return u?u.label+' · '+u.title:x;}).join(' · '),'hover-source'));
    return frag;
  }
  function select(id,edgeId){detail.replaceChildren(describe(id,edgeId,true));}
  const role={action:say('行动节点','Action'),decision:say('判断与分支','Decision'),concept:say('概念与机制','Concept')};
  const diagram=window.LFMGraphStudio.mount(map,{language:data.meta.language,kind:'methodology',title:model.title,nodes:model.nodes.map(n=>({...n,summary:n.output,tag:role[n.role]})),edges:model.edges.map(e=>({...e,label:edgeKind[e.kind]||say('关联','Relation')})),mainPath:model.mainPath,onSelect:select,detail,describe:(id)=>describe(id,null,false)});
  detail.hidden=true;
  /* A panel switch changes visibility without moving the viewport, and the studio's
     IntersectionObserver has already unobserved the host by then — so the graph must
     be re-announced explicitly. Wait two frames: one for the panel to become visible,
     one for it to have real measurements. */
  if(diagram&&typeof diagram.refresh==='function'){
    const panel=document.getElementById('tab-content')||map.closest('[hidden]')||map;
    const ping=()=>requestAnimationFrame(()=>requestAnimationFrame(diagram.refresh));
    ['click','change','input'].forEach(t=>panel.addEventListener(t,ping,true));
    document.addEventListener('visibilitychange',()=>{if(!document.hidden)ping();});
  }
})();
