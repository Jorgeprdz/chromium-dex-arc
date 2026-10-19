/* Optional observer for the original downloaded HTML; does not replace handlers. */
(() => {
 'use strict';
 if(document.title!=='Archium R5 · Popup & Dialog Diagnostics')throw Error('Original fixture required');
 const ids=['test-alert','test-confirm','test-prompt','test-download','test-favorite','test-chain','test-modal','test-nonmodal','test-overlay','test-window','test-file','test-all-html'];
 if(ids.some(id=>!document.getElementById(id)))throw Error('Original fixture controls missing');
 if(window.__archiumR52)throw Error('Observer already installed');
 const events=[],removers=[];let dropped=0;
 const safeId=element=>element?.id&&['modal','nonmodal','overlay',...ids].includes(element.id)?element.id:'other';
 function observe(event){
  const layers=['modal','nonmodal','overlay'].map(id=>{const e=document.getElementById(id),r=e.getBoundingClientRect(),s=getComputedStyle(e);return {id,open:!!e.open,x:r.x,y:r.y,width:r.width,height:r.height,display:s.display,visibility:s.visibility,opacity:s.opacity,z:s.zIndex}});
  events.push({event,utc:new Date().toISOString(),monotonicMs:performance.now(),scheme:location.protocol,secure:isSecureContext,width:innerWidth,height:innerHeight,dpr:devicePixelRatio,focused:document.hasFocus(),activeId:safeId(document.activeElement),layers});
  if(events.length>250){events.shift();dropped++}
 }
 function listen(target,event,fn,capture=false){target.addEventListener(event,fn,capture);removers.push(()=>target.removeEventListener(event,fn,capture))}
 listen(document,'click',e=>{const id=e.target.closest('button')?.id;if(!ids.includes(id))return;observe(id+'-requested');setTimeout(()=>observe(id+'-returned-no-visual-verdict'),0)},true);
 for(const id of ['modal','nonmodal'])for(const event of ['beforetoggle','toggle','cancel','close'])listen(document.getElementById(id),event,()=>observe(id+'-'+event));
 for(const event of ['focus','blur','resize'])listen(window,event,()=>observe(event));
 const mutation=new MutationObserver(()=>observe('layer-attribute-change'));
 for(const id of ['modal','nonmodal','overlay'])mutation.observe(document.getElementById(id),{attributes:true,attributeFilter:['open','class','style']});
 window.__archiumR52={snapshot:()=>({kind:'DOM_METADATA_NOT_LOGCAT_OR_VISIBILITY_PASS',dropped,events:JSON.parse(JSON.stringify(events))}),stop:()=>{mutation.disconnect();removers.forEach(fn=>fn());delete window.__archiumR52}};
 observe('observer-installed');
})();
