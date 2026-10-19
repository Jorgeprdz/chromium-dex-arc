/* Actual original JavaScript, synthetic DOM/native boundaries. No Android PASS. */
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(process.argv[2],'utf8');
const scripts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n');
function fixture(){
 const elements=new Map(),calls=[],stored=new Map();
 class Element{
  constructor(){this.children=[];this.listeners={};this.checked=false;this.open=false;this.returnValue='';this.classes=new Set();this.classList={add:s=>this.classes.add(s),remove:s=>this.classes.delete(s),contains:s=>this.classes.has(s)}}
  append(...nodes){this.children.push(...nodes)} remove(){} replaceChildren(){this.children=[]}
  addEventListener(name,fn){(this.listeners[name]??=[]).push(fn)}
  focus(){calls.push('focus')} querySelector(){return new Element()}
  showModal(){this.open=true;calls.push('showModal')} show(){this.open=true;calls.push('show')}
  close(value){this.open=false;this.returnValue=value;for(const f of this.listeners.close||[])f({})}
  click(){calls.push(this.id==='file-pick'?'file-picker-request':'anchor-click')}
 }
 for(const match of html.matchAll(/\bid="([^"]+)"/g)){const e=new Element();e.id=match[1];elements.set(e.id,e)}
 const document={body:new Element(),visibilityState:'visible',getElementById:id=>{assert(elements.has(id),'missing original id '+id);return elements.get(id)},createElement:()=>new Element(),createTextNode:text=>({text}),addEventListener(){}};
 const context={document,navigator:{userAgent:'HOST_SIMULATED_NOT_ANDROID',clipboard:{writeText:async()=>{}}},location:{href:'host-fixture://original'},performance:{now:()=>1},Blob,URL,Date,console,innerWidth:1280,innerHeight:720,devicePixelRatio:1,
  alert:()=>{calls.push('alert')},confirm:()=>{calls.push('confirm');return true},prompt:()=>{calls.push('prompt');return 'PRUEBA'},
  localStorage:{setItem:(key,value)=>stored.set(key,value)},setTimeout:fn=>{fn();return 1},setInterval:()=>1,addEventListener(){},
  open:()=>{calls.push('window.open');return {document:{body:new Element()}}}};
 context.window=context;vm.createContext(context);vm.runInContext(scripts,context,{timeout:1000});
 return {calls,stored,elements,click:id=>{const e=elements.get(id);assert(e?.onclick,'original onclick missing '+id);e.onclick()}};
}
let count=0;
for(const [id,expected] of [['test-alert','alert'],['test-confirm','confirm'],['test-prompt','prompt'],['test-download','confirm'],['test-favorite','confirm'],['test-chain','alert'],['test-modal','showModal'],['test-nonmodal','show'],['test-overlay','focus'],['test-window','window.open'],['test-file','file-picker-request'],['test-all-html','showModal']]){
 const f=fixture();f.click(id);assert(f.calls.includes(expected),id+' did not route to '+expected);
 if(id==='test-favorite')assert.equal(f.stored.get('archium-test-favorite'),'true');
 if(id==='test-chain')for(const call of ['alert','confirm','prompt'])assert(f.calls.includes(call));
 if(id==='test-all-html'){assert.equal(f.elements.get('modal').open,true);assert.equal(f.elements.get('nonmodal').open,false)}
 count++;
}
console.log('ORIGINAL_HTML_HOST_ROUTING='+count+' PASS; SYNTHETIC_DOM_NATIVE_BOUNDARIES; DEVICE_RUNTIME=NOT_TESTED');
