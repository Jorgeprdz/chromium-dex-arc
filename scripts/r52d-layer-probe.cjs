#!/usr/bin/env node
'use strict';
// Read-only CDP probe. Node >=22; no dependencies, Android input, navigation or ADB.
const fs=require('node:fs'),path=require('node:path');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function allowedTarget(raw,amazon){try{const u=new URL(raw);if(u.username||u.password)return false;return amazon?
 u.protocol==='https:'&&u.hostname==='www.amazon.com.mx'&&u.pathname==='/'&&!u.search&&!u.hash:
 u.protocol==='http:'&&u.hostname==='127.0.0.1'&&u.pathname==='/r52d-layer-reuse.html'&&!u.search&&!u.hash;
 }catch{return false}}
function qualifyPair(a,b){
 if(!a?.locationAllowed||!b?.locationAllowed)return 'PAGE_CHANGED';
 if(!a||!b||!a.focused||!b.focused||a.visible!=='visible'||b.visible!=='visible')return 'FOCUS_OR_VISIBILITY_CHANGED';
 if(JSON.stringify(a.viewport)!==JSON.stringify(b.viewport)||Math.abs(a.scrollY-b.scrollY)>.5)return 'GEOMETRY_CHANGED';
 if(JSON.stringify(a.images)!==JSON.stringify(b.images))return 'IMAGE_STATE_CHANGED';
 return 'STABLE_METADATA_ONLY'; // Never a visual PASS or proof of identical GPU resources.
}
async function main(args){
 const port=Number(args[0]),output=args[1],amazon=args[2]==='--amazon-homepage';
 if(!Number.isInteger(port)||port<1024||port>65535||!output||args.length>(amazon?3:2))throw Error('Usage: node r52d-layer-probe.cjs PORT NEW_PRIVATE_DIR [--amazon-homepage]');
 // The operator owns an existing localhost forward. This program never removes it.
 fs.mkdirSync(output,{mode:0o700});const save=(n,v)=>fs.writeFileSync(path.join(output,n),Buffer.isBuffer(v)?v:JSON.stringify(v,null,2),{mode:0o600});
 const targets=await(await fetch(`http://127.0.0.1:${port}/json/list`,{signal:AbortSignal.timeout(5000)})).json();
 const target=targets.find(t=>t.type==='page'&&allowedTarget(t.url,amazon));if(!target)throw Error('Exact allowed page unavailable');
 const endpoint=new URL(target.webSocketDebuggerUrl);
 if(!['127.0.0.1','localhost'].includes(endpoint.hostname)||Number(endpoint.port)!==port||endpoint.protocol!=='ws:')throw Error('Nonlocal WebSocket rejected');
 const ws=new WebSocket(endpoint);let id=0,layers=[],events=0;const pending=new Map();
 const budget=setTimeout(()=>ws.close(),25000);let receipt={status:'BLOCKED',start:new Date().toISOString(),scope:amazon?'AMAZON_HOMEPAGE':'SYNTHETIC_ONLY',snapshots:[]};
 ws.onmessage=({data})=>{const x=JSON.parse(data);if(x.id){const p=pending.get(x.id);if(!p)return;pending.delete(x.id);clearTimeout(p.timer);x.error?p.reject(Error(x.error.message)):p.resolve(x.result)}
 else if(x.method==='LayerTree.layerTreeDidChange'){events++;layers=(x.params.layers||[]).slice(0,512)}};
 ws.onclose=()=>{for(const p of pending.values()){clearTimeout(p.timer);p.reject(Error('CDP closed'))}pending.clear()};
 const call=(method,params={})=>new Promise((resolve,reject)=>{const n=++id,timer=setTimeout(()=>{pending.delete(n);reject(Error(method+' timed out'))},4000);
 pending.set(n,{resolve,reject,timer});ws.send(JSON.stringify({id:n,method,params}))});
 const evaluate=async expression=>(await call('Runtime.evaluate',{expression,returnByValue:true})).result.value;
 const metadata=()=>evaluate(`(()=>({locationAllowed:(${allowedTarget.toString()})(location.href,${amazon}),focused:document.hasFocus(),visible:document.visibilityState,viewport:[innerWidth,innerHeight,devicePixelRatio],scrollY,
 images:[...document.images].map((i,index)=>{const r=i.getBoundingClientRect();return {index,complete:i.complete,nw:i.naturalWidth,nh:i.naturalHeight,x:r.x,y:r.y,w:r.width,h:r.height}}).slice(0,512)}))()`);
 try{
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=()=>reject(Error('CDP connection failed'));ws.addEventListener('close',()=>reject(Error('CDP closed before open')),{once:true})});await call('LayerTree.enable');await sleep(300);
  const before=await metadata();if(qualifyPair(before,before)!=='STABLE_METADATA_ONLY')throw Error('Page must already be visible and focused');save('before.json',before);
  const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false,fromSurface:true});save('before.PRIVATE.png',Buffer.from(shot.data,'base64'));
  const selected=before.images.filter(i=>i.complete&&i.nw>0&&i.w>100&&i.h>100&&i.x>=0&&i.y>=0&&i.x+i.w<before.viewport[0]&&i.y+i.h<before.viewport[1]).slice(0,3);
  const mapping=[];for(const image of selected){for(let depth=0;depth<5;depth++){
   const {result}=await call('Runtime.evaluate',{expression:`(()=>{let n=document.images[${image.index}];for(let d=0;n&&d<${depth};d++)n=n.parentElement;return n})()`});
   if(!result.objectId)continue;try{const {node}=await call('DOM.describeNode',{objectId:result.objectId});mapping.push({imageIndex:image.index,depth,backendNodeId:node.backendNodeId})}
   finally{await call('Runtime.releaseObject',{objectId:result.objectId})}}}
  const ids=new Set(mapping.map(m=>m.backendNodeId));save('mapping.json',mapping);save('layers.json',layers);
  for(const layer of layers.filter(l=>l.drawsContent&&ids.has(l.backendNodeId)).slice(0,3)){
   let snapshotId;try{({snapshotId}=await call('LayerTree.makeSnapshot',{layerId:layer.layerId}));const replay=await call('LayerTree.replaySnapshot',{snapshotId});
    save(`layer-${layer.layerId}.PRIVATE.png`,Buffer.from(replay.dataURL.split(',')[1],'base64'));receipt.snapshots.push({layerId:layer.layerId,status:'CAPTURED'})}
   catch{receipt.snapshots.push({layerId:layer.layerId,status:'UNAVAILABLE'})}finally{if(snapshotId)await call('LayerTree.releaseSnapshot',{snapshotId})}}
  const after=await metadata();save('after.json',after);receipt.pair=qualifyPair(before,after);
  if(receipt.pair==='STABLE_METADATA_ONLY'){const shot=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false,fromSurface:true});save('after.PRIVATE.png',Buffer.from(shot.data,'base64'))}
  receipt.status='CAPTURED_NOT_VALIDATED';
 }finally{receipt.end=new Date().toISOString();receipt.layerEvents=events;save('receipt.json',receipt);clearTimeout(budget);
  for(const p of pending.values()){clearTimeout(p.timer);p.reject(Error('Probe closed'))}pending.clear();ws.close()}
 console.log(JSON.stringify(receipt));
}
module.exports={allowedTarget,qualifyPair};
if(require.main===module)main(process.argv.slice(2)).catch(()=>{console.error('Probe blocked; preserve private receipt if created.');process.exitCode=1});
