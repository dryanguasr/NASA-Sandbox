import {AGENTS,validateRun,snapshot,decodeGrid,makePlayback} from './replay.js';
import {copy} from './copy.js';
const $=id=>document.getElementById(id), fmt=(n,d=0)=>Number(n).toLocaleString('es-CO',{maximumFractionDigits:d,minimumFractionDigits:d});
const colors={human_1:'#e7bf8f',human_2:'#e8ddba',rover_1:'#e99675',rover_2:'#e9c06e',drone_1:'#78e1e5',drone_2:'#a7c8f4'};
const shape=id=>id.startsWith('human')?'○':id.startsWith('rover')?'□':'△';
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
let data,comparison,playback,view,guideIndex=null,decoded={},lastFrame=-1,lastLayer='',lastRender=-1;
const safePath=p=>typeof p==='string'&&!p.startsWith('/')&&!p.includes('..')&&!/^[a-z]+:/i.test(p);
async function json(path){const res=await fetch(path);if(!res.ok)throw new Error(`${path}: HTTP ${res.status}`);return res.json();}
function decodeCached(key,encoded,bytes=2){return decoded[key]??=decodeGrid(encoded,bytes);}
function paintTerrain(canvas,values,n,{sigma=false,hero=false}={}){
 const ctx=canvas.getContext('2d'), scratch=document.createElement('canvas');scratch.width=n;scratch.height=n;
 const sc=scratch.getContext('2d'), pixels=sc.createImageData(n,n);
 for(let y=0;y<n;y++)for(let x=0;x<n;x++){
  const i=y*n+x,v=values[i]/(sigma?255:65535),dx=(values[y*n+Math.min(n-1,x+1)]-values[y*n+Math.max(0,x-1)])/65535,dy=(values[Math.min(n-1,y+1)*n+x]-values[Math.max(0,y-1)*n+x])/65535;
  const shade=sigma?1:Math.max(.48,Math.min(1.5,1-dx*4+dy*3));
  const rgb=sigma?[18+v*91,37+v*176,47+v*172]:[52+v*156,44+v*128,38+v*91];
  for(let c=0;c<3;c++)pixels.data[i*4+c]=Math.min(255,rgb[c]*shade);pixels.data[i*4+3]=255;
 }
 sc.putImageData(pixels,0,0);ctx.imageSmoothingEnabled=true;ctx.drawImage(scratch,0,0,canvas.width,canvas.height);
 // Contours come only from the selected normalized height field; sigma is not relief.
 if(!sigma){ctx.strokeStyle=hero?'#ead4b744':'#e9cfaa38';ctx.lineWidth=hero?1.1:.8;ctx.beginPath();for(let y=0;y<n-1;y++)for(let x=0;x<n-1;x++){let v=Math.floor(values[y*n+x]/3500);if(v!==Math.floor(values[y*n+x+1]/3500)){const xx=(x+1)*canvas.width/n;ctx.moveTo(xx,y*canvas.height/n);ctx.lineTo(xx,(y+1)*canvas.height/n);}if(v!==Math.floor(values[(y+1)*n+x]/3500)){const yy=(y+1)*canvas.height/n;ctx.moveTo(x*canvas.width/n,yy);ctx.lineTo((x+1)*canvas.width/n,yy);}}ctx.stroke();}
 ctx.strokeStyle='#f2e3c81c';ctx.lineWidth=1;for(let i=1;i<8;i++){ctx.beginPath();ctx.moveTo(i*canvas.width/8,0);ctx.lineTo(i*canvas.width/8,canvas.height);ctx.moveTo(0,i*canvas.height/8);ctx.lineTo(canvas.width,i*canvas.height/8);ctx.stroke();}
}
const xy=(p,size=800)=>[(p[0]/data.side+.5)*size,(.5-p[1]/data.side)*size];
function renderMap(){
 const layer=$('layer').value,fi=view.frameIndex,canvas=$('mission-map');
 let key=layer==='mean'||layer==='sigma'?`${layer}-${fi}`:layer;
 const raw=(layer==='mean'||layer==='sigma')?data[layer][fi]:data[layer];
 paintTerrain(canvas,decodeCached(key,raw,layer==='sigma'?1:2),data.n,{sigma:layer==='sigma'});
 const ctx=canvas.getContext('2d');
 const selectedAgent=AGENTS.includes(playback.selection)?playback.selection:[...view.events].reverse().find(e=>e.event==='assigned'&&e.task?.endsWith(':'+playback.selection))?.agent;
 if($('trails').checked){for(const id of AGENTS){ctx.strokeStyle=colors[id];ctx.lineWidth=selectedAgent===id?4:2;ctx.globalAlpha=selectedAgent&&selectedAgent!==id?.35:.85;ctx.beginPath();for(let i=0;i<=view.positionIndex;i++){const p=xy(data.trajectory[i].positions[id]);if(i===0)ctx.moveTo(...p);else ctx.lineTo(...p);}ctx.stroke();}ctx.globalAlpha=1;}
 const base=xy([-178,-178]);ctx.fillStyle='#fff';ctx.font='22px sans-serif';ctx.fillText('⌂',base[0]-8,base[1]+25);
 const overlay=$('map-overlay');overlay.replaceChildren();
 for(const site of view.sites){const marker=el('button','◇ '+site.id,'map-marker target'+(playback.selection===site.id?' selected':''));marker.id=`map-${site.id}`;marker.style.left=`${xy(site.xy_m,100)[0]}%`;marker.style.top=`${xy(site.xy_m,100)[1]}%`;marker.setAttribute('aria-label',`Objetivo ficticio ${site.id}`);marker.onclick=()=>select(site.id);overlay.append(marker);}
 for(const id of AGENTS){const marker=el('button',shape(id)+id.slice(-1),'map-marker'+(playback.selection===id?' selected':''));marker.id=`map-${id}`;const pos=xy(view.position.positions[id],100);marker.style.left=pos[0]+'%';marker.style.top=pos[1]+'%';marker.style.setProperty('--agent',colors[id]);marker.setAttribute('aria-label',`${copy.agents[id]} en el mapa`);marker.onclick=()=>select(id);overlay.append(marker);}
 $('layer-note').textContent=copy.layers[layer];lastFrame=fi;lastLayer=layer;
}
function taskText(task){if(!task)return 'En espera';const [kind,target]=task.split(':');return `${copy.kinds[kind]||kind}${target&&kind!=='survey'?' · '+target:''}`;}
function eventText(e){if(e.event==='site_detected')return `${copy.agents[e.agent]} descubre ${e.site}`;return `${copy.events[e.event]||e.event}${e.task?' · '+taskText(e.task):''}${e.agent?' · '+copy.agents[e.agent]:''}`;}
function select(id){playback.selection=id;render();}
function renderContext(){
 const root=$('context-detail');root.replaceChildren();
 const id=playback.selection;
 if(id&&AGENTS.includes(id)){
   root.append(el('h4',`${shape(id)} ${copy.agents[id]}`));const pos=view.position.positions[id];
   root.append(el('p',`${id} · X ${fmt(pos[0],1)} m / Y ${fmt(pos[1],1)} m`));
   const current=view.position.tasks[id];root.append(el('p',taskText(current),'chain'));
   const taskEvent=[...view.events].reverse().find(e=>e.agent===id&&e.event==='assigned'&&e.task===current);
   if(taskEvent?.score_s!=null)root.append(el('p',`Puntuación registrada: ${fmt(taskEvent.score_s,2)} s. No equivale a duración real; puede incluir bonificación informativa.`));
   root.append(el('p','Criterio detallado no registrado: no se conserva la tabla completa de candidatos.'));
   root.append(el('p',`Tareas completadas hasta este instante: ${view.events.filter(e=>e.agent===id&&e.event==='completed').length}.`));
 }else if(id&&view.sites.some(s=>s.id===id)){
   root.append(el('h4',`◇ Objetivo ${id} · ficticio`));
   const detection=view.events.find(e=>e.event==='site_detected'&&e.site===id);
   root.append(el('p',`Observación → ${copy.agents[detection.agent]} descubre ${id} a T+${detection.time_s} s.`,'chain'));
   for(const kind of ['inspect','sample']){const task=view.tasks[`${kind}:${id}`];root.append(el('p',task?`${copy.kinds[kind]} → ${task.state}${task.agent?' · '+copy.agents[task.agent]:''}.`:`${copy.kinds[kind]} → todavía no habilitada.`));}
   root.append(el('p','La detección habilita la inspección. Completar la inspección habilita el muestreo. Criterio detallado de candidatos no registrado.'));
 }else{
   root.append(el('h4','Una observación abre el camino.'));
   root.append(el('p','Selecciona un agente o un objetivo descubierto para seguir su actividad registrada.'));
   const latest=[...view.events].reverse().find(e=>e.event==='site_detected'||(e.event==='completed'&&['inspect','sample','return'].includes(e.kind)));
   root.append(el('p',latest?`T+${latest.time_s} s · ${eventText(latest)}`:'CTX → observación ideal → nueva información → tarea → agente','chain'));
   root.append(el('p',view.time===data.summary.duration_s?`${view.returns}/6 regresos registrados. Misión finalizada.`:'Solo aparecen objetivos detectados hasta el tiempo seleccionado.'));
 }
 const events=$('events');events.replaceChildren(...view.events.slice(-12).reverse().map(e=>el('li',`T+${e.time_s} s · ${eventText(e)}`)));
}
function render(){
 if(!data)return;
 const focusedId=document.activeElement?.id;
 view=snapshot(data,playback.time);
 if(playback.selection?.startsWith('S')&&!view.sites.some(s=>s.id===playback.selection))playback.selection=null;
 $('time').textContent=`T+${Math.floor(view.time).toString().padStart(4,'0')} s`;
 $('seek').value=view.time;$('play-state').textContent=playback.playing?'Reproduciendo registro':view.time===data.summary.duration_s?'Finalizado':view.time===0?'Listo':'Pausado';
 $('play').textContent=playback.playing?'Ⅱ Pausar':'▶ Reproducir';
 $('coverage').textContent=`${fmt(view.frame.coverage*100,1)} %`;$('discovered').textContent=`${view.sites.length} / 4`;$('samples').textContent=`${view.samples} / 4`;
 $('snapshot-time').textContent=`Posición ${view.position.time_s} s · Mapa ${view.frame.time_s} s`;
 for(const id of AGENTS){const b=$(`agent-${id}`);b.setAttribute('aria-pressed',String(playback.selection===id));b.querySelector('small').textContent=taskText(view.position.tasks[id]);}
 const targets=$('targets');targets.replaceChildren();if(!view.sites.length)targets.append(el('small','Aún no hay objetivos descubiertos.'));
 for(const site of view.sites){const b=el('button',`◇ ${site.id}`);b.id=`target-${site.id}`;b.setAttribute('aria-pressed',String(playback.selection===site.id));b.onclick=()=>select(site.id);targets.append(b);}
 renderMap();renderContext();lastRender=Math.floor(playback.time/5);
 if(focusedId?.startsWith('map-')||focusedId?.startsWith('target-'))$(focusedId)?.focus({preventScroll:true});
}
function seek(time){playback.playing=false;playback.seek(time);render();}
function guideStep(i){
 guideIndex=Math.max(0,Math.min(i,data.milestones.length-1));const m=data.milestones[guideIndex];
 playback.selectRun('information_hungarian');$('run-select').value='information_hungarian';$('replay-ui').hidden=false;$('unavailable').hidden=true;
 $('guide').hidden=false;$('guide-step').textContent=`DEMO GUIADA · ${guideIndex+1}/${data.milestones.length} · RECORRIDO ~90 S A TU RITMO`;
 $('guide-title').textContent=m.label;$('guide-text').textContent=m.explanation;$('guide-back').disabled=guideIndex===0;$('guide-next').textContent=guideIndex===data.milestones.length-1?'Comparar estrategias ↗':'Siguiente →';
 $('layer').value=guideIndex===0?'prior':'mean';playback.seek(m.time_s);if(['discovery','inspection','sample'].includes(m.id))playback.selection='S2';render();
}
function buildAgents(){for(const id of AGENTS){const b=el('button',undefined,'agent-button');b.id=`agent-${id}`;b.setAttribute('aria-pressed','false');b.setAttribute('aria-label',`Seleccionar ${copy.agents[id]}`);b.style.setProperty('--agent',colors[id]);b.append(el('span',shape(id),'agent-icon'));const label=el('span');label.append(el('b',copy.agents[id]),el('small','En espera'));b.append(label);b.onclick=()=>select(id);$('agents').append(b);}}
function renderComparison(c){
 const policies=c.policies;if(!policies?.information_hungarian||!policies?.nearest_greedy)throw new Error('Resultados de comparación incompatibles.');
 const a=policies.information_hungarian,b=policies.nearest_greedy;
 for(const [key,title,unit]of[['t80_s','Tiempo hasta el 80 %','s'],['duration_s','Duración de la misión','s'],['drone_distance_m','Recorrido de los drones','m']]){
   const group=el('article',undefined,'bar-group');group.append(el('h3',title),el('p','Media de 3 ejecuciones · Menor es mejor'));
   const max=Math.max(a[key].mean,b[key].mean);
   for(const [policy,alt]of[[a,false],[b,true]]){const row=el('div',undefined,'bar-row'+(alt?' alt':''));row.dataset.metric=key;row.dataset.policy=alt?'nearest_greedy':'information_hungarian';row.append(el('span',`${fmt(policy[key].mean,key==='drone_distance_m'?1:0)} ${unit}`,'bar-label'));const bar=el('i');bar.style.width=(policy[key].mean/max*100)+'%';row.append(bar);group.append(row);}
   $('comparison-bars').append(group);
 }
 $('tradeoff').textContent=`La política informativa alcanza el 80 % ${fmt(b.t80_s.mean-a.t80_s.mean)} s antes, pero tarda ${fmt(a.duration_s.mean-b.duration_s.mean)} s más y recorre ${fmt(a.drone_distance_m.mean-b.drone_distance_m.mean,1)} m adicionales con sus drones.`;
 for(const [key,label,unit]of[['t50_s','Tiempo al 50 %','s'],['t80_s','Tiempo al 80 %','s'],['t95_s','Tiempo al 95 %','s'],['duration_s','Duración','s'],['drone_distance_m','Distancia de drones','m'],['final_rmse_m','RMSE final','m']]){const tr=el('tr');tr.append(el('th',label),el('td',`${fmt(a[key].mean,3)} ${unit}`),el('td',`${fmt(b[key].mean,3)} ${unit}`));$('comparison-table').querySelector('tbody').append(tr);}
}
function renderVideos(m){
 for(const v of m.videos||[]){const card=el('article',undefined,'video-card'),body=el('div',undefined,'video-body');
 if(v.status==='available'&&safePath(v.src)){
   const video=el('video');video.controls=true;video.playsInline=true;video.preload='none';video.src=v.src;if(safePath(v.poster))video.poster=v.poster;video.setAttribute('aria-label',v.title);video.setAttribute('aria-describedby',`video-summary-${v.id}`);
   const fallback=el('p','Tu navegador no puede reproducir este video. Usa el enlace de descarga.');video.append(fallback);
   video.addEventListener('error',()=>{video.hidden=true;card.prepend(el('p','Recurso no disponible. Consulta el informe o restaura el MP4 del respaldo.','notice error'));},{once:true});
   video.addEventListener('play',()=>document.querySelectorAll('video').forEach(other=>{if(other!==video)other.pause();}));card.append(video);
 }else card.append(el('p','Video no disponible en este paquete. El informe conserva los resultados.','notice'));
 body.append(el('span',v.fidelity_label,'badge'),el('h3',v.title));const desc=el('p',v.summary);desc.id=`video-summary-${v.id}`;body.append(desc);
 body.append(el('p',`${fmt(v.duration_s,1)} s · H.264 · ${fmt(v.bytes/1e6,2)} MB · Sin audio`,'video-meta'));
 for(const [text,path]of[['Abrir informe ↗',v.report],['Descargar MP4 ↓',v.src]])if(safePath(path)){const a=el('a',text);a.href=path;if(text.startsWith('Descargar'))a.download='';body.append(a);}
 const details=el('details'),summary=el('summary','Resumen accesible y trazabilidad');details.append(summary,el('p',v.transcript),el('p',`${v.run_id} · semilla ${v.seed??'no aplica'} · ${v.origin_commit.slice(0,12)}`));body.append(details);card.append(body);$('videos').append(card);
 }
}
function setupControls(){
 $('play').onclick=()=>{playback.toggle();render();};$('seek').oninput=e=>seek(Number(e.target.value));
 $('reset').onclick=()=>{playback.reset();$('guide').hidden=true;guideIndex=null;$('layer').value='mean';render();};
 $('overview').onclick=()=>{playback.selection=null;render();};$('layer').onchange=render;$('trails').onchange=render;
 for(const [id,dir]of[['prev-event',-1],['next-event',1]])$(id).onclick=()=>{const times=data.milestones.map(m=>m.time_s);seek(dir===1?(times.find(t=>t>playback.time)??data.summary.duration_s):([...times].reverse().find(t=>t<playback.time)??0));};
 $('run-select').onchange=e=>{playback.selectRun(e.target.value);$('guide').hidden=true;guideIndex=null;const available=e.target.value==='information_hungarian';$('replay-ui').hidden=!available;$('unavailable').hidden=available;render();};
 $('start-demo').onclick=()=>{guideStep(0);location.hash='explorador';};$('guide-next').onclick=()=>{if(guideIndex===data.milestones.length-1){playback.playing=false;location.hash='comparador';}else guideStep(guideIndex+1);};$('guide-back').onclick=()=>guideStep(guideIndex-1);$('guide-close').onclick=()=>{$('guide').hidden=true;guideIndex=null;};
 $('presentation').onclick=()=>{const active=document.body.classList.toggle('presentation');$('presentation').setAttribute('aria-pressed',String(active));$('presentation').textContent=active?'Salir de presentación':'Modo presentación';};
 document.addEventListener('visibilitychange',()=>{if(document.hidden&&playback){playback.playing=false;render();}});
 let previous=performance.now();function tick(now){const elapsed=Math.min((now-previous)/1000,.25);previous=now;if(playback.playing){playback.tick(elapsed*Number($('speed').value));if(Math.floor(playback.time/5)!==lastRender||!playback.playing)render();}requestAnimationFrame(tick);}requestAnimationFrame(tick);
}
async function init(){
 $('start-demo').disabled=true;$('run-select').disabled=true;
 const [mission,comp,belva,media]=await Promise.allSettled([json('data/mission.json'),json('data/comparison.json'),json('data/belva.json'),json('media-manifest.json')]);
 if(comp.status==='fulfilled'){try{comparison=comp.value;renderComparison(comparison);}catch(e){$('comparison-bars').append(el('p',e.message,'notice error'));}}else $('comparison-bars').append(el('p','Comparación no disponible. Revisa el paquete de datos.','notice error'));
 if(media.status==='fulfilled')renderVideos(media.value);else $('videos').append(el('p','Inventario de videos no disponible. Consulta el respaldo local.','notice error'));
 if(belva.status==='fulfilled'){const {result,seedComparison}=belva.value;const b=$('belva-metrics');b.append(el('span',`${result.returns} / 6`,'belva-number'),el('p',`Regresos · ensayo filmado de ${fmt(result.duration_s,2)} s`),el('p',`${seedComparison.complete_missions}/${seedComparison.runs.length} misiones completas en repeticiones posteriores; ${seedComparison.runs.reduce((n,r)=>n+r.verified_count,0)}/${seedComparison.runs.length*6} regresos. Estas repeticiones no están filmadas.`));}
 if(mission.status==='rejected')throw mission.reason;
 data=validateRun(mission.value);playback=makePlayback(data.summary.duration_s);$('seek').max=data.summary.duration_s;
 buildAgents();setupControls();paintTerrain($('hero-map'),decodeCached('prior',data.prior),data.n,{hero:true});render();
 $('run-provenance').textContent=`${data.run_id} · Fuente ${data.source_commit.slice(0,12)} · Semilla ${data.seed??data.summary.seed}`;
 $('start-demo').disabled=false;$('run-select').disabled=false;$('load-status').hidden=true;
 performance.mark('mission-ready');document.documentElement.dataset.ready='true';
}
init().catch(e=>{$('load-status').hidden=false;$('load-status').classList.add('error');$('load-status').textContent=`Registro no disponible: ${e.message}. Recarga la página o restaura el build local completo.`;$('replay-ui').hidden=true;document.documentElement.dataset.ready='error';});
