/* Offline diagram studio: one geometry model for cards, ports and routes. */
(function () {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const make = (tag, text, cls) => { const n=document.createElement(tag); if(text!=null)n.textContent=text; if(cls)n.className=cls; return n; };
  const svgEl = (tag, attrs) => {const n=document.createElementNS(NS,tag);Object.entries(attrs||{}).forEach(([k,v])=>n.setAttribute(k,v));return n;};
  let serial=0;
  function ordered(nodes, edges, path) {
    if(path && path.length) return [...path.map(id=>nodes.find(n=>n.id===id)).filter(Boolean),...nodes.filter(n=>!path.includes(n.id))];
    const pending=new Set(nodes.map(n=>n.id)), result=[];
    while(pending.size){
      const ready=nodes.filter(n=>pending.has(n.id)&&!edges.some(e=>e.to===n.id&&pending.has(e.from)&&e.kind!=='feedback'&&e.type!=='feedback'));
      // Cycles retain source order and explicit arrows; no invented hierarchy.
      const last=result[result.length-1];
      const degree=id=>edges.filter(e=>e.from===id||e.to===id).length;
      const near=id=>last&&edges.some(e=>(e.from===last.id&&e.to===id)||(e.to===last.id&&e.from===id));
      ready.sort((a,b)=>Number(!!near(b.id))-Number(!!near(a.id))||degree(b.id)-degree(a.id)||nodes.indexOf(a)-nodes.indexOf(b));
      const batch=[ready.length?ready[0]:nodes.find(n=>pending.has(n.id))];
      batch.forEach(n=>{pending.delete(n.id);result.push(n);});
    }
    return result;
  }
  function mount(host, options) {
    const en=options.language==='en', say=(zh,eng)=>en?eng:zh, uid='diagram-'+(++serial);
    const edges=options.edges||[], nodes=options.kind==='methodology'&&!options.mainPath?.length?options.nodes.slice():ordered(options.nodes,edges,options.mainPath), index=new Map(nodes.map((n,i)=>[n.id,i]));
    const root=make('section',null,'diagram-studio'); root.setAttribute('aria-label',options.title);
    const heading=make('div',null,'diagram-heading');
    const headingCopy=make('div');headingCopy.append(make('span',options.kind==='framework'?say('概念之间 · 逻辑相连','CONCEPTS · CONNECTIONS'):say('从理解到应用 · 全文贯通','UNDERSTAND · CONNECT · APPLY'),'diagram-kicker'),make('h3',options.title));
    const count=make('span',`${nodes.length} ${say('节点','nodes')} / ${edges.length} ${say('关系','links')}`,'diagram-count');heading.append(headingCopy,count);root.append(heading);
    const toolbar=make('div',null,'diagram-toolbar'),tools=make('div',null,'diagram-tools');
    const zoomOut=make('button','−'),zoomIn=make('button','+'),fit=make('button',say('适合宽度','Fit width')),overview=make('button',say('查看全图','Overview')),full=make('button',say('全屏查看','Full screen'));
    zoomOut.setAttribute('aria-label',say('缩小关系图','Zoom out'));zoomIn.setAttribute('aria-label',say('放大关系图','Zoom in'));
    const scaleLabel=make('output','100%');[zoomOut,zoomIn,fit,overview,full].forEach(b=>b.type='button');tools.append(zoomOut,scaleLabel,zoomIn,fit,overview,full);
    const legend=make('p',say('实线：材料依据　蓝色：整合推断　金色：反馈 / 回路','Neutral: source evidence · Blue: inference · Gold: feedback'),'diagram-legend');toolbar.append(legend,tools);root.append(toolbar);
    // Safety net: an undeclared relationship set must say so out loud instead of looking like a bare node cloud.
    if(nodes.length>1&&!edges.length){const note=make('p',say('这份页面尚未声明节点之间的关系：下面只列出卡片，没有可展开的连线。这是关系图数据缺失，不是渲染故障。','No relationships were declared for this page: the cards below are listed without any connecting links. This is missing relationship data, not a rendering fault.'),'diagram-empty');note.setAttribute('role','status');root.append(note);}
    const viewport=make('div',null,'diagram-viewport');viewport.tabIndex=0;viewport.setAttribute('aria-label',say('关系图画布，可滚动及放大','Diagram canvas; scroll and zoom'));
    const sizer=make('div',null,'diagram-sizer'),stage=make('div',null,'diagram-stage');sizer.append(stage);viewport.append(sizer);root.append(viewport);host.replaceChildren(root);
    // Components keep their own source-backed topology. Allocate only the columns
    // they actually use: a single chain no longer reserves an empty three-column grid.
    const placement=new Map(),groups=[],unseen=new Set(nodes.map(n=>n.id));let totalRows=0;
    while(unseen.size){const seed=unseen.values().next().value,ids=new Set([seed]),queue=[seed];unseen.delete(seed);
      while(queue.length){const id=queue.shift();edges.filter(e=>e.from===id||e.to===id).forEach(e=>{const other=e.from===id?e.to:e.from;if(unseen.has(other)){unseen.delete(other);ids.add(other);queue.push(other);}});}
      groups.push({ids});
    }
    groups.forEach(g=>{
      const pending=nodes.filter(n=>g.ids.has(n.id)),rows=[];
      while(pending.length){let ready=pending.filter(n=>!edges.some(e=>e.to===n.id&&pending.some(p=>p.id===e.from)&&e.kind!=='feedback'&&e.type!=='feedback'));
        if(!ready.length)ready=[pending[0]]; // A source cycle keeps its recorded order.
        for(let i=0;i<ready.length;i+=3)rows.push(ready.slice(i,i+3));
        ready.forEach(n=>pending.splice(pending.indexOf(n),1));
      }
      g.rows=rows;g.cols=Math.max(1,...rows.map(row=>row.length));
    });
    const bands=[];let band=[],bandCols=0;
    groups.forEach(g=>{
      if(band.length&&bandCols+g.cols>3){bands.push(band);band=[];bandCols=0;}
      band.push(g);bandCols+=g.cols;
    });
    if(band.length)bands.push(band);
    const cols=Math.max(1,...bands.map(band=>band.reduce((sum,g)=>sum+g.cols,0)));
    bands.forEach((band,bandIndex)=>{
      const bandCols=band.reduce((sum,g)=>sum+g.cols,0),bandRows=Math.max(...band.map(g=>g.rows.length));
      let col=(cols-bandCols)/2;
      band.forEach(g=>{
        g.start=totalRows;g.end=totalRows+g.rows.length-1;
        g.rows.forEach((row,r)=>{const offset=(g.cols-row.length)/2;row.forEach((n,j)=>placement.set(n.id,{row:totalRows+r,col:col+offset+j}));});
        col+=g.cols;
      });
      totalRows+=bandRows+(bandIndex<bands.length-1?1:0);
    });
    const cw=286,gap=76,left=32,top=42,positions=new Map(),cards=new Map();
    const surfaceWidth=left*2+cols*cw+(cols-1)*gap;
    nodes.forEach((n,i)=>{
      const {row,col}=placement.get(n.id);
      const card=make('article',null,'diagram-card');card.dataset.nodeId=n.id;card.dataset.tone=String(row%3);card.style.width=cw+'px';
      const button=make('button',null,'diagram-node-button');button.type='button';button.setAttribute('aria-label',n.title);button.setAttribute('aria-pressed','false');
      const meta=make('div',null,'diagram-card-meta');
      const number=options.kind==='framework'&&Number.isInteger(n.sourceOrder)&&n.sourceOrder>0?n.sourceOrder:index.get(n.id)+1;
      if(options.showNumbers!==false)meta.append(make('span',String(number).padStart(2,'0'),'diagram-number'));
      meta.append(make('span',n.tag||say('逻辑节点','Logic node'),'diagram-tag'));
      button.title=n.title;button.append(meta,make('h4',n.title),make('p',n.summary||n.output||'','diagram-summary'));card.append(button);
      const out=edges.filter(e=>e.from===n.id);
      if(out.length){const transitions=make('div',null,'diagram-transitions');out.forEach(e=>{
        const b=make('button',null,'diagram-transition');b.type='button';b.dataset.edgeId=e.id;
        b.append(make('span','→','diagram-destination'),make('span',(e.label||say('关联','Related to'))+' · '+nodes.find(x=>x.id===e.to).title,'diagram-transition-label'));
        b.title=(e.label||say('关联','Related to'))+' · '+nodes.find(x=>x.id===e.to).title+(e.condition?' · '+e.condition:'');b.onclick=()=>select(n.id,e.id);transitions.append(b);
      });card.append(transitions);}
      stage.append(card);cards.set(n.id,card);positions.set(n.id,{row,col,x:left+col*(cw+gap),h:0,y:0});button.onclick=()=>select(n.id);
    });
    const svg=svgEl('svg',{class:'diagram-wires','aria-hidden':'true'});stage.prepend(svg);
    // Surfaces are painted with inline styles read from the themed palette. Stylesheet
    // backgrounds inside this page can be alpha-blended with white by the rendering path
    // (verified 2026-09-18), which turns dark cards light gray; inline button styles do not.
    const readPal=()=>{const cs=getComputedStyle(root);const t=k=>cs.getPropertyValue(k).trim();return{card:t('--dg-card'),dimCard:t('--dg-dim-card'),trans:t('--dg-trans-bg'),transInk:t('--dg-trans-ink')};};
    let pal=readPal();
    const paintSurface=c=>{
      const b=c.querySelector('.diagram-node-button');
      if(b)b.style.background=c.classList.contains('is-dimmed')?pal.dimCard:pal.card;
      c.querySelectorAll('.diagram-transition').forEach(x=>{x.style.background=pal.trans;x.style.color=pal.transInk;});
    };
    cards.forEach(paintSurface);
    new MutationObserver(()=>{pal=readPal();cards.forEach(paintSurface);}).observe(document.body,{attributes:true,attributeFilter:['data-theme','class','style']});
    // Arrowheads read their colour from the themed CSS class, never a hard-coded fill.
    const defs=svgEl('defs');[['normal','dg-arrow-normal',11],['feedback','dg-arrow-feedback',11],['inference','dg-arrow-inference',10]].forEach(([kind,cls,size])=>{const m=svgEl('marker',{id:uid+'-'+kind,viewBox:'0 0 10 10',refX:10,refY:5,markerWidth:size,markerHeight:size,markerUnits:'userSpaceOnUse',orient:'auto'});m.append(svgEl('path',{d:'M 0 0 L 10 5 L 0 10 Z',class:cls}));defs.append(m);});svg.append(defs);
    const help=make('p',say('点击任意卡片，查看与它直接相连的卡片及关系；点击空白处恢复全图。','Click a card to see its connected cards and relationships. Click empty space to reset.'),'diagram-help');root.append(help);
    const connections=make('div',null,'diagram-connections');connections.hidden=true;connections.setAttribute('aria-live','polite');root.append(connections);
    if(options.detail){options.detail.hidden=true;}
    const groupLabels=groups.length>1?groups.map(g=>{const label=make('div',say('独立关系分支 · ','Separate branch · ')+nodes.find(n=>g.ids.has(n.id)).title,'diagram-group-label');stage.append(label);return {g,label};}):[];
    const paths=new Map(),flows=new Map();let width=surfaceWidth,height=0,scale=1,selected=null,manualZoom=false,fitMode='width';
    // One quiet entrance, then a static map. A selected relation gets one
    // directional cue; all other links remain still and readable.
    const RM=matchMedia('(prefers-reduced-motion: reduce)');
    let rebuildFrame=0,visibleNow=false,io=null,hasDrawn=false,flowTimer=null;
    function applyDraw(){svg.classList.add('is-drawn','is-static');}
    function settleWires(){
      cancelAnimationFrame(rebuildFrame);
      flowCancel();
      svg.classList.remove('is-drawn');
      rebuildFrame=requestAnimationFrame(()=>{
        rebuildFrame=0;
        if(RM.matches||hasDrawn){hasDrawn=true;applyDraw();}
        else if(visibleNow)playDraw();
      });
    }
    function armDraw(){
      svg.classList.remove('is-drawn','is-flowing');
    }
    function flowCancel(){clearTimeout(flowTimer);flowTimer=null;svg.classList.remove('is-flowing');}
    function startFlow(){
      if(RM.matches||!selected)return;
      flowCancel();
      void svg.getBoundingClientRect();
      svg.classList.add('is-flowing');
      flowTimer=setTimeout(flowCancel,2300);
    }
    function playDraw(){
      hasDrawn=true;
      svg.classList.remove('is-static');
      svg.classList.add('is-drawn');
    }
    function layout(initial){
      /* A display:none panel reports clientWidth 0 and offsetHeight 0 for every
         descendant. Rebuilding on those numbers wrecks the diagram: cards keep the
         height they had, but the row pitch collapses to the minimum gap, the auto
         scale collapses, and the entry/exit ports stack up. That is
         what happens when a hidden panel is switched back on — the ResizeObserver
         fires during a window where the layout is half-applied.
         Skipping the rebuild leaves the previous geometry intact, and the
         ResizeObserver will call back with real numbers a frame later. */
      if(viewport.clientWidth<=0&&!initial)return;
      const rows=totalRows,heights=Array(rows).fill(0),loads=Array(rows).fill(0);
      nodes.forEach(n=>{const p=positions.get(n.id);p.h=cards.get(n.id).offsetHeight;heights[p.row]=Math.max(heights[p.row],p.h);});
      edges.forEach(e=>{const a=positions.get(e.from),b=positions.get(e.to);if(a&&b){loads[a.row]++;loads[b.row]++;}});
      let y=top;const rowY=[],gaps=[];
      for(let r=0;r<rows;r++){rowY[r]=y;gaps[r]=Math.max(groups.some(g=>g.end===r)?86:66,44+(loads[r]+(loads[r+1]||0))*6);y+=heights[r]+gaps[r];}
      positions.forEach((p,id)=>{p.y=rowY[p.row];const card=cards.get(id);card.style.left=p.x+'px';card.style.top=p.y+'px';});
      paths.forEach(p=>p.remove());paths.clear();flows.forEach(q=>q.remove());flows.clear();
      let lane=0,minY=0;
      const incoming=new Map(),outgoing=new Map();nodes.forEach(n=>{incoming.set(n.id,edges.filter(e=>e.to===n.id));outgoing.set(n.id,edges.filter(e=>e.from===n.id));});
      edges.forEach(e=>{
        const a=positions.get(e.from),b=positions.get(e.to);if(!a||!b)return;
        const feedback=e.kind==='feedback'||e.type==='feedback';
        let d;
        if(a.row===b.row&&Math.abs(a.col-b.col)===1&&!feedback){
          const forward=b.x>a.x,sy=a.y+74,ty=b.y+74;
          const x1=forward?a.x+cw+5:a.x-5,x2=forward?b.x-12:b.x+cw+12;
          d=`M ${x1} ${sy} C ${(x1+x2)/2} ${sy}, ${(x1+x2)/2} ${ty}, ${x2} ${ty}`;
        }else{
          const oi=outgoing.get(e.from).indexOf(e),ii=incoming.get(e.to).indexOf(e);
          const sx=a.x+cw*(oi+1)/(outgoing.get(e.from).length+1),tx=b.x+cw*(ii+1)/(incoming.get(e.to).length+1);
          const sy=a.y+a.h+5,ty=b.y-12;
          if(b.row===a.row+1&&!feedback){
            // A direct next-row link stays in the open gap between both cards.
            const mid=(sy+ty)/2;d=`M ${sx} ${sy} V ${mid} H ${tx} V ${ty}`;
          }else{
            // Only skipping and feedback links need an exterior return lane.
            const exitY=sy+18,entryY=ty-18;minY=Math.min(minY,entryY);
            const rail=surfaceWidth+18+(lane++)*14;
            d=`M ${sx} ${sy} V ${exitY} H ${rail} V ${entryY} H ${tx} V ${ty}`;
          }
        }
      const isInference=e.evidence==='inference';
      const cls='diagram-wire'+(feedback?' is-feedback':'')+(isInference?' is-inference':'');
      const p=svgEl('path',{d,class:cls,'marker-end':`url(#${uid}-${feedback?'feedback':isInference?'inference':'normal'})`});
      svg.append(p);paths.set(e.id,p);
      // The flow head rides a second path with identical geometry, stacked above the
      // solid line so the effect runs ON the line rather than replacing it.
      const q=svgEl('path',{d,class:'diagram-flow'+(feedback?' is-feedback':'')+(isInference?' is-inference':''),'data-edge-id':e.id});
      svg.append(q);flows.set(e.id,q);
      // Geometry is measured AFTER insertion: a detached SVG path reports a bogus
      // getTotalLength() in Chromium, which would freeze the head at its minimum travel.
      let len=0;try{len=p.getTotalLength();}catch(err){len=0;}
      if(len>0){
        p.style.setProperty('--wire-len',len.toFixed(1));
        // A short stagger gives direction without making the reader wait.
        const delay=Math.min(360,(a.row*40)+(outgoing.get(e.from).indexOf(e)*20));
        p.style.setProperty('--draw-delay',delay+'ms');
        p.style.setProperty('--draw-dur',Math.max(360,Math.min(750,len*.45)).toFixed(0)+'ms');
        // The comet travels the visible length minus the arrowhead, so it never
        // collides with the tip; the dash gap is scaled off the same measured length
        // so each wire shows exactly one head in flight however long it is.
        const travel=Math.max(40,len-20);
        q.style.setProperty('--flow-travel',travel.toFixed(1));
        const head=feedback?34:isInference?20:30;
        q.style.setProperty('--flow-dash',head+' '+(travel+head).toFixed(0));
      }
      // Feedback loops and inferred links run slower — weight and pace both carry meaning.
      q.style.setProperty('--flow-dur',(feedback?2.2:isInference?1.9:1.5)+'s');
      });
      width=surfaceWidth+(lane?30+lane*14:0);height=y-gaps[rows-1]+Math.max(54,gaps[rows-1]);
      // Top entry corridors for return arrows are inside the canvas.
      const pad=Math.max(0,16-minY);stage.style.paddingTop='0';
      svg.setAttribute('width',width);svg.setAttribute('height',height+pad);svg.style.top=pad+'px';
      cards.forEach((card,id)=>card.style.top=(positions.get(id).y+pad)+'px');height+=pad;
      groupLabels.forEach(({g,label})=>{label.style.top=(rowY[g.start]+pad-36)+'px';const first=Array.from(g.ids)[0];label.style.left=(positions.get(first)?.x||left)+'px';});
      stage.style.width=width+'px';stage.style.height=height+'px';
      if(!manualZoom){
        const byWidth=(viewport.clientWidth-24)/width;
        const byHeight=(viewport.clientHeight-24)/height;
        scale=Math.max(.18,Math.min(1,fitMode==='all'?Math.min(byWidth,byHeight):byWidth))||1;
      }
      setScale(scale);if(selected)highlight(selected);
      // A path rebuild must leave a complete still map after the first entrance.
      armDraw();
      settleWires();
    }
    function setScale(value){
      scale=Math.max(.18,Math.min(1.8,value));stage.style.transform=`scale(${scale})`;
      sizer.style.width=Math.max(width*scale,viewport.clientWidth)+'px';
      sizer.style.height=Math.max(height*scale,viewport.clientHeight)+'px';
      stage.style.left=Math.max(0,(viewport.clientWidth-width*scale)/2)+'px';
      stage.style.top=Math.max(0,(viewport.clientHeight-height*scale)/2)+'px';
      scaleLabel.textContent=Math.round(scale*100)+'%';
    }
    function zoomBy(delta){
      hideHover();manualZoom=true;
      const old=scale,cx=(viewport.scrollLeft+viewport.clientWidth/2-stage.offsetLeft)/old,cy=(viewport.scrollTop+viewport.clientHeight/2-stage.offsetTop)/old;
      setScale(scale+delta);
      viewport.scrollLeft=stage.offsetLeft+cx*scale-viewport.clientWidth/2;
      viewport.scrollTop=stage.offsetTop+cy*scale-viewport.clientHeight/2;
    }
    function highlight(id,edgeId){const related=new Set([id]);edges.filter(e=>edgeId?e.id===edgeId:e.from===id||e.to===id).forEach(e=>{related.add(e.from);related.add(e.to);});cards.forEach((c,k)=>{c.classList.toggle('is-selected',k===id);c.classList.toggle('is-dimmed',!!id&&!related.has(k));c.querySelector('.diagram-node-button').setAttribute('aria-pressed',String(k===id));paintSurface(c);});edges.forEach(e=>{const p=paths.get(e.id);if(p){const on=!!id&&(edgeId?e.id===edgeId:e.from===id||e.to===id);p.classList.toggle('is-active',on);p.classList.toggle('is-dimmed',!!id&&!on);}const q=flows.get(e.id);if(q){const on=!!id&&(edgeId?e.id===edgeId:e.from===id||e.to===id);q.classList.toggle('is-active',on);q.classList.toggle('is-dimmed',!!id&&!on);}});svg.classList.toggle('is-selecting',!!id);}
    function reset(){hideHover();selected=null;flowCancel();highlight(null);connections.hidden=true;if(options.detail)options.detail.hidden=true;}
    function select(id,edgeId){hideHover();selected=id;highlight(id,edgeId);startFlow();connections.replaceChildren();connections.hidden=false;
      const close=make('button',say('恢复全图','Show all'),'diagram-reset');close.type='button';close.onclick=reset;
      connections.append(close,make('strong',nodes.find(n=>n.id===id).title));
      const nearby=edges.filter(e=>edgeId?e.id===edgeId:e.from===id||e.to===id);
      if(!nearby.length)connections.append(make('p',say('当前材料未提供与其他卡片的明确关系。','No supported connection to another card is recorded.')));
      nearby.forEach(e=>{const row=make('button',null,'diagram-connection');row.type='button';row.append(make('span',nodes.find(n=>n.id===e.from).title+' → '+nodes.find(n=>n.id===e.to).title),make('small',e.label||e.condition||say('关联','Related')));row.onclick=()=>select(e.from===id?e.to:e.from);connections.append(row);});
      if(options.onSelect&&options.detail){options.onSelect(id,edgeId);options.detail.hidden=true;const more=make('button',say('查看详细说明与出处','Details and sources'),'diagram-more');more.type='button';more.onclick=()=>{options.detail.hidden=!options.detail.hidden;more.setAttribute('aria-expanded',String(!options.detail.hidden));};more.setAttribute('aria-expanded','false');connections.append(more);}
    }
    // Hover preview renders the very same card data as the locked detail panel.
    const hover=make('div',null,'diagram-hovercard');hover.setAttribute('aria-hidden','true');hover.tabIndex=0;document.body.append(hover);
    let hoverId=null,hoverAnchor=null,hoverHideTimer=null;
    function cancelHoverHide(){clearTimeout(hoverHideTimer);hoverHideTimer=null;}
    function hideHover(){cancelHoverHide();hover.classList.remove('is-visible');hover.setAttribute('aria-hidden','true');hoverId=null;hoverAnchor=null;}
    function scheduleHoverHide(){if(hoverHideTimer||!hoverId)return;hoverHideTimer=setTimeout(hideHover,300);}
    function inHoverBridge(x,y){
      if(!hoverAnchor||!hover.classList.contains('is-visible'))return false;
      const a=hoverAnchor.getBoundingClientRect(),b=hover.getBoundingClientRect(),pad=8;
      if(x>=a.left-pad&&x<=a.right+pad&&y>=a.top-pad&&y<=a.bottom+pad)return true;
      if(x>=b.left-pad&&x<=b.right+pad&&y>=b.top-pad&&y<=b.bottom+pad)return true;
      if(b.left>=a.right)return x>=a.right-pad&&x<=b.left+pad&&y>=Math.min(a.top,b.top)-pad&&y<=Math.max(a.bottom,b.bottom)+pad;
      if(a.left>=b.right)return x>=b.right-pad&&x<=a.left+pad&&y>=Math.min(a.top,b.top)-pad&&y<=Math.max(a.bottom,b.bottom)+pad;
      return x>=Math.max(a.left,b.left)-pad&&x<=Math.min(a.right,b.right)+pad&&y>=Math.min(a.bottom,b.bottom)-pad&&y<=Math.max(a.top,b.top)+pad;
    }
    function showHover(id,card){
      if(!options.describe)return;
      cancelHoverHide();
      if(hoverId===id&&hoverAnchor===card)return;
      if(hoverId!==id){hover.replaceChildren(options.describe(id));hoverId=id;hover.scrollTop=0;}
      hoverAnchor=card;
      hover.classList.add('is-visible');
      hover.setAttribute('aria-hidden','false');
      // Anchor once to the node. A panel that chases the pointer creates a
      // moving gap and makes a slow pointer transfer fail.
      const box=hover.getBoundingClientRect(),anchor=card.getBoundingClientRect();
      const gap=8,margin=12;
      const fitsRight=anchor.right+gap+box.width<=innerWidth-margin;
      const fitsLeft=anchor.left-gap-box.width>=margin;
      let left=fitsRight?anchor.right+gap:(fitsLeft?anchor.left-gap-box.width:anchor.right+gap);
      let top=anchor.top;
      left=Math.max(margin,Math.min(left,innerWidth-box.width-margin));
      top=Math.max(margin,Math.min(top,innerHeight-box.height-margin));
      hover.style.left=left+'px';
      hover.style.top=top+'px';
    }
    hover.addEventListener('pointerenter',cancelHoverHide);
    hover.addEventListener('pointerleave',e=>{if(!inHoverBridge(e.clientX,e.clientY))scheduleHoverHide();});
    document.addEventListener('pointermove',e=>{
      if(e.pointerType==='touch'||!hoverId)return;
      if(inHoverBridge(e.clientX,e.clientY))cancelHoverHide();
      else scheduleHoverHide();
    });
    // Keep the page and diagram stationary while the pointer is reading the
    // floating explanation, including at the top and bottom of its scrollbar.
    function applyHoverWheel(delta,target){
      let remaining=delta;
      const inner=target?.closest?.('.relation-edge-list');
      if(inner&&hover.contains(inner)&&inner.scrollHeight>inner.clientHeight+1){
        const before=inner.scrollTop;
        inner.scrollTop+=remaining;
        remaining-=inner.scrollTop-before;
      }
      if(remaining)hover.scrollTop+=remaining;
    }
    hover.addEventListener('wheel',e=>{
      applyHoverWheel(e.deltaY*(e.deltaMode===1?40:e.deltaMode===2?hover.clientHeight:1),e.target);
      e.preventDefault();e.stopPropagation();
    },{passive:false});
    viewport.addEventListener('wheel',e=>{
      if(!hover.classList.contains('is-visible')||!hoverAnchor||!inHoverBridge(e.clientX,e.clientY))return;
      applyHoverWheel(e.deltaY*(e.deltaMode===1?40:e.deltaMode===2?hover.clientHeight:1));
      e.preventDefault();
    },{passive:false});
    stage.addEventListener('pointermove',e=>{if(e.pointerType==='touch')return;const card=e.target.closest('.diagram-card');if(card&&selected!==card.dataset.nodeId)showHover(card.dataset.nodeId,card);});
    stage.addEventListener('pointerleave',e=>{if(!inHoverBridge(e.clientX,e.clientY))scheduleHoverHide();});
    viewport.addEventListener('scroll',hideHover);
    viewport.addEventListener('click',e=>{if(!e.target.closest('.diagram-card'))reset();});
    // Escape is layered: in fullscreen the FIRST Escape must collapse the overlay
    // (and put the studio back), and only a subsequent Escape clears a selected node.
    // The fullscreen handler is therefore registered first and marks the event handled
    // via a flag, so the selection handler below does not swallow it with
    // stopImmediatePropagation() before the overlay gets a chance to close.
    let escapeHandledByExpand=false;
    zoomOut.onclick=()=>zoomBy(-.15);zoomIn.onclick=()=>zoomBy(.15);
    fit.onclick=()=>{hideHover();fitMode='width';manualZoom=false;layout();viewport.scrollTop=0;};
    overview.onclick=()=>{hideHover();fitMode='all';manualZoom=false;layout();viewport.scrollLeft=0;viewport.scrollTop=0;};
    let placeholder=null,detailPlaceholder=null;
    function expand(){hideHover();const on=root.classList.toggle('is-expanded');full.textContent=on?say('退出全屏','Exit full screen'):say('全屏查看','Full screen');
      if(on){placeholder=make('span');root.before(placeholder);document.body.append(root);root.setAttribute('aria-modal','true');root.setAttribute('role','dialog');root.dataset.previousOverflow=document.body.style.overflow;document.body.style.overflow='hidden';
        if(options.detail){detailPlaceholder=make('span');options.detail.before(detailPlaceholder);root.append(options.detail);options.detail.classList.add('diagram-expanded-detail');}
        full.focus();
      }else{root.removeAttribute('role');root.removeAttribute('aria-modal');document.body.style.overflow=root.dataset.previousOverflow||'';placeholder.replaceWith(root);if(detailPlaceholder){detailPlaceholder.replaceWith(options.detail);options.detail.classList.remove('diagram-expanded-detail');detailPlaceholder=null;}full.focus();}
      manualZoom=false;requestAnimationFrame(layout);
    }
    full.onclick=expand;root.addEventListener('keydown',e=>{if(!root.classList.contains('is-expanded'))return;if(e.key==='Escape'){escapeHandledByExpand=true;expand();e.stopPropagation();}if(e.key==='Tab'){const focusable=Array.from(root.querySelectorAll('button,[tabindex="0"],summary')).filter(n=>n.getClientRects().length);const first=focusable[0],last=focusable[focusable.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}});
    // Registered AFTER the fullscreen handler so the overlay gets Escape first.
    root.addEventListener('keydown',e=>{if(e.key!=='Escape')return;if(escapeHandledByExpand){escapeHandledByExpand=false;return;}hideHover();if(selected){reset();e.stopImmediatePropagation();}});
    /* IntersectionObserver alone can miss a panel switch at the same scroll
       position. The visibility check presents the entrance once, then restores
       a static map after tab switches and fullscreen changes. */
    const announce=()=>{
      const r=root.getBoundingClientRect();
      const on=r.height>0&&r.width>0&&r.bottom>0&&r.top<innerHeight+240;
      if(on===visibleNow)return;
      visibleNow=on;
      if(on){ if(RM.matches||hasDrawn){hasDrawn=true;applyDraw();return;} playDraw(); }
      else { flowCancel(); }
    };
    const observer=new ResizeObserver(()=>{if(viewport.clientWidth>0){hideHover();layout();announce();}});observer.observe(viewport);
    if('IntersectionObserver' in window){io=new IntersectionObserver(()=>announce(),{threshold:.12});io.observe(root);}
    else{visibleNow=true;playDraw();}
    // A panel switch changes visibility without moving the viewport, so it must be
    // re-announced. The ResizeObserver and the scroll listener cover the remaining
    // paths (expand/collapse, resize, and ordinary scrolling).
    document.addEventListener('visibilitychange',announce);
    window.addEventListener('scroll',announce,{passive:true});
    RM.addEventListener?.('change',()=>{armDraw();
      if(RM.matches){hasDrawn=true;applyDraw();}
      else {applyDraw();if(selected)startFlow();}});
    if(document.fonts)document.fonts.ready.then(()=>layout(true));
    requestAnimationFrame(()=>layout(true));
    /* refresh() is the external hook for a host that switches panels without
       scrolling (a tab click). The host must call it AFTER the panel is laid out —
       a double rAF is the reliable point. */
    function refresh(){ if(viewport.clientWidth<=0)return; layout(); announce(); }
    return {select,layout,root,positions,refresh};
  }
  window.LFMGraphStudio={mount,ordered};
})();
