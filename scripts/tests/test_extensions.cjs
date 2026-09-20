// Dependency-free unit tests using an in-memory DOM double, NOT a browser/layout test.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname,'../..');

function fixture(data, clipboardMode='ok') {
  const roots=[];
  let document;
  class Element {
    constructor(tag){this.tagName=tag;this.children=[];this.attrs={};this.events={};this.hidden=false;this.value='';this._text='';this.className='';this.namespaceURI='http://www.w3.org/2000/svg';this.classList={add:name=>{this.className+=' '+name;}};}
    set textContent(value){this._text=String(value);this.children=[];}
    get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
    get options(){return this.children.filter(x=>x.tagName==='option');}
    append(...nodes){for(const value of nodes){const n=typeof value==='string'?Object.assign(new Element('#text'),{textContent:value}):value;n.parent=this;this.children.push(n);}}
    insertBefore(node,before){if(!before){this.append(node);return;}const i=this.children.indexOf(before);assert(i>=0);node.parent=this;this.children.splice(i,0,node);}
    replaceChildren(...nodes){this.children=[];this.append(...nodes);}
    setAttribute(key,value){this.attrs[key]=String(value);if(key==='id')this.id=String(value);if(key==='class')this.className=String(value);}
    getAttribute(key){return this.attrs[key];}
    all(){return this.children.flatMap(x=>[x,...x.all()]);}
    querySelector(selector){return this.all().find(x=>selector[0]==='.'?x.className.split(' ').includes(selector.slice(1)):x.tagName===selector)||null;}
    addEventListener(name,fn){(this.events[name]||=[]).push(fn);}
    async dispatch(name,event={}){for(const fn of this.events[name]||[]) await fn({preventDefault(){},...event});}
    focus(){document.activeElement=this;}
    select(){this.selected=true;}
    showModal(){this.open=true;}
    close(){this.open=false;this.dispatch('close');}
    setCustomValidity(value){this.validityMessage=value;}
    reportValidity(){return !this.validityMessage;}
  }
  document={activeElement:null,getElementById:id=>roots.flatMap(x=>[x,...x.all()]).find(x=>x.id===id)||null,createElement:tag=>new Element(tag),createElementNS:(_ns,tag)=>new Element(tag),execCommand:()=>true};
  const add=(tag,id,parent)=>{const n=new Element(tag);n.id=id;(parent?parent.children:roots).push(n);return n;};
  add('script','pageData').textContent=JSON.stringify(data);
  const frameworkHost=add('section','frameworks');add('div','',frameworkHost).className='grid';
  const ruleHost=add('section','rules');if(data.decisionRules.length)add('div','',ruleHost).className='content-stream';
  const dialog=add('dialog','methodDialog'),form=add('form','methodForm',dialog);
  ['methodClose','methodSelect','methodProblem','methodGoal','methodLimits','methodPrompt','methodStatus'].forEach(id=>add(id==='methodSelect'?'select':'textarea',id,form));
  const select=document.getElementById('methodSelect');
  ['auto',...data.frameworks.map(x=>x.id),...data.decisionRules.map(x=>x.id)].filter(Boolean).forEach(id=>{const opt=new Element('option');opt.value=id;select.append(opt);});
  let copied='';
  const navigator=clipboardMode==='missing'?{}:{clipboard:{writeText:async text=>{if(clipboardMode==='denied')throw Error('denied');copied=text;}}};
  const graphs=[];
  const window={LFMGraphStudio:{mount:(host,options)=>{const graph={...options,layout:()=>{},select:id=>options.onSelect(id)};graphs.push(graph);return graph;}}};
  const context=vm.createContext({document,navigator,window,requestAnimationFrame:fn=>fn(),Option:function(text,value){const opt=new Element('option');opt.textContent=text;opt.value=value;return opt;}});
  vm.runInContext(fs.readFileSync(path.join(root,'templates/extensions.js'),'utf8'),context);
  return {document,form,dialog,frameworkHost,ruleHost,graphs,copied:()=>copied};
}

(async()=>{
  let cases=0;
  {
    const data=JSON.parse(fs.readFileSync(path.join(root,'examples/overview-whole-methodology.json'),'utf8'));
    const f=fixture(data),get=id=>f.document.getElementById(id);
    assert(f.frameworkHost.querySelector('.relation-tools'));assert.equal(f.frameworkHost.querySelector('.grid').hidden,false);
    get('applyMethod').onclick();assert.equal(get('methodSelect').value,'whole');
    get('methodProblem').value='The experience library grows without useful transfer.';
    await f.form.dispatch('submit');
    const prompt=get('methodPrompt').value,body=JSON.parse(prompt.slice(prompt.indexOf('{\n')));
    assert.equal(body.selection,'whole-material');assert.deepEqual(body.methodology,data.methodology);
    assert.deepEqual(body.methodCards,data.methodLibrary.methods);
    assert(body.methodology.edges.some(e=>e.kind==='feedback'));
    get('methodSelect').value=data.frameworks[0].id;await f.form.dispatch('submit');
    const selected=JSON.parse(get('methodPrompt').value.slice(get('methodPrompt').value.indexOf('{\n')));
    assert.equal(selected.selection,'selected');assert.equal(selected.method.id,data.frameworks[0].id);
    cases++;
  }
  for(const filename of ['overview-en-content.json','overview-zh-content.json','overview-methods-content.json']){
    const data=JSON.parse(fs.readFileSync(path.join(root,'examples',filename),'utf8'));
    for(const mode of ['ok','denied','missing']){
      const f=fixture(data,mode),get=id=>f.document.getElementById(id);
      f.frameworkHost.querySelector('.relation-tools').children[1].onclick();
      assert.equal(get('frameworks-relations').hidden,false);
      assert.equal(f.frameworkHost.querySelector('.grid').hidden,true);
      f.graphs[0].select(data.frameworks[0].id);
      const details=get('frameworks-relations').querySelector('.relation-detail');
      assert(details.textContent.includes(data.frameworks[0].source));
      details.querySelector('button').onclick();
      get('applyMethod').onclick();get('methodSelect').value=data.frameworks[0].id;
      assert.equal(f.dialog.open,true);assert.equal(get('methodSelect').value,data.frameworks[0].id);
      get('methodProblem').value='   ';await f.form.dispatch('submit');assert(get('methodProblem').validityMessage);
      get('methodProblem').value='<script>not executable</script> A real question';await get('methodProblem').dispatch('input');
      get('methodGoal').value='Measurable outcome';get('methodLimits').value='No uploads';
      await f.form.dispatch('submit');const prompt=get('methodPrompt').value;
      const body=JSON.parse(prompt.slice(prompt.indexOf('{\n')));
      assert.equal(body.method.id,data.frameworks[0].id);assert.equal(body.problem,get('methodProblem').value);assert.equal(body.constraints,'No uploads');
      if(data.methodLibrary){assert.deepEqual(body.methodCard,data.methodLibrary.methods[0]);assert.equal(body.methodLibraryId,data.methodLibrary.libraryId);}
      assert.equal(body.relationships.length,data.relationships.filter(e=>e.from===body.method.id||e.to===body.method.id).length);
      if(data.meta.language==='en')assert(!/[\u3400-\u9fff]/.test(prompt));
      if(mode==='ok')assert.equal(f.copied(),prompt);
      if(mode==='denied'){assert.equal(f.copied(),'');assert(get('methodPrompt').selected);assert(get('methodStatus').textContent.includes(data.meta.language==='en'?'manually':'手动'));}
      await get('methodProblem').dispatch('input');assert.equal(get('methodPrompt').value,'');
      get('methodClose').onclick();assert.equal(f.dialog.open,false);
      get('applyMethod').onclick();assert.equal(get('methodSelect').value,'auto');await f.form.dispatch('submit');
      const auto=JSON.parse(get('methodPrompt').value.slice(get('methodPrompt').value.indexOf('{\n')));
      assert.equal(auto.methodIndex.length,data.frameworks.length+data.decisionRules.length);
      if(data.methodLibrary)assert.equal(auto.savedMethodIndex.length,data.methodLibrary.methods.length);
      assert.equal(f.ruleHost.querySelector('.relation-tools'),null);
      assert(f.graphs[0].edges.every(e=>data.frameworks.some(n=>n.id===e.from)&&data.frameworks.some(n=>n.id===e.to)));
      cases++;
    }
  }
  const base=JSON.parse(fs.readFileSync(path.join(root,'examples/overview-en-content.json'),'utf8'));
  const large=JSON.parse(JSON.stringify(base));
  for(let i=0;i<20;i++)large.frameworks.push({...base.frameworks[0],id:'extra-'+i,name:'Independent '+i});
  const f=fixture(large),get=id=>f.document.getElementById(id);
  f.frameworkHost.querySelector('.relation-tools').children[1].onclick();
  const panel=get('frameworks-relations');
  assert.equal(f.graphs[0].nodes.length,large.frameworks.length,'All nodes supplied, without pagination');
  f.graphs[0].select('extra-19');assert(panel.querySelector('.relation-detail').textContent.includes('Independent 19'));cases++;
  const empty=JSON.parse(JSON.stringify(base));empty.relationships=[];empty.decisionRules=[];
  const noRules=fixture(empty);assert(noRules.document.getElementById('applyMethod'));cases++;
  const flow=JSON.parse(JSON.stringify(base));flow.relationships=[{...base.relationships[0],from:'f-map',to:'f-evidence',type:'sequence'},{...base.relationships[0],from:'f-evidence',to:'f-action',type:'prerequisite'}];
  const layered=fixture(flow);layered.frameworkHost.querySelector('.relation-tools').children[1].onclick();
  assert.equal(layered.graphs[0].edges.length,2);cases++;
  console.log('PASS '+cases+' in-memory interaction scenarios; no browser or visual verification claimed.');
})().catch(error=>{console.error(error);process.exit(1);});
