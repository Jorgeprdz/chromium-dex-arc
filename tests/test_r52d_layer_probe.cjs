'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {allowedTarget,qualifyPair}=require('../scripts/r52d-layer-probe.cjs');
test('Only the exact authorized homepage is accepted',()=>{
 assert.equal(allowedTarget('https://www.amazon.com.mx/',true),true);
 for(const url of ['https://www.amazon.com.mx/orders','https://www.amazon.com.mx/?token=private','https://www.amazon.com.mx/#account','https://user:pass@www.amazon.com.mx/','https://www.amazon.com.mx.evil/','file:///tmp/a'])assert.equal(allowedTarget(url,true),false);
});
test('Synthetic mode cannot target a personal page',()=>{
 assert.equal(allowedTarget('http://127.0.0.1:8080/r52d-layer-reuse.html',false),true);
 assert.equal(allowedTarget('https://www.amazon.com.mx/',false),false);
 assert.equal(allowedTarget('http://127.0.0.1:8080/other.html',false),false);
});
const meta=()=>({locationAllowed:true,focused:true,visible:'visible',viewport:[1000,700,.96068],scrollY:650,images:[{index:3,x:100,y:100,w:150,h:175,nw:512,nh:512}]});
test('Navigation after target selection invalidates the pair',()=>assert.equal(qualifyPair(meta(),{...meta(),locationAllowed:false}),'PAGE_CHANGED'));
test('Matching metadata is explicitly not visual validation',()=>assert.equal(qualifyPair(meta(),meta()),'STABLE_METADATA_ONLY'));
test('Occlusion or focus changes cannot qualify a screenshot pair',()=>{
 for(const patch of [{focused:false},{visible:'hidden'}])assert.equal(qualifyPair(meta(),{...meta(),...patch}),'FOCUS_OR_VISIBILITY_CHANGED');
});
test('DPR, window and scroll differences invalidate mapping',()=>{
 for(const patch of [{viewport:[1000,700,1]},{viewport:[900,700,.96068]},{scrollY:652}])assert.equal(qualifyPair(meta(),{...meta(),...patch}),'GEOMETRY_CHANGED');
});
test('Dynamic DOM geometry prevents a causal same-image claim',()=>{
 const changed=meta();changed.images[0].y=101;assert.equal(qualifyPair(meta(),changed),'IMAGE_STATE_CHANGED');
});
