/** Presentation-only adapter. No planner or simulator is imported. */
export const AGENTS = ['human_1','human_2','rover_1','rover_2','drone_1','drone_2'];
export function validateRun(d) {
  if(d.schema_version!==1 || d.execution_type!=='simulation_2_5d' || !d.trajectory?.length || !d.frames?.length || !d.events?.length) throw new Error('Registro ausente o incompatible (contrato v1).');
  if(!AGENTS.every(id=>d.trajectory.every(p=>p.positions[id]?.length>=3))) throw new Error('El registro no contiene los seis agentes.');
  for(const rows of [d.frames,d.trajectory,d.events]) if(rows.some((p,i)=>!Number.isFinite(p.time_s)||(i&&p.time_s<rows[i-1].time_s))) throw new Error('Tiempo de misión incompatible.');
  if(d.frames.length!==d.mean.length || d.sigma.length!==d.frames.length) throw new Error('Capas temporales incompletas.');
  return d;
}
export function lastIndexAt(rows,t) { let lo=0, hi=rows.length-1; while(lo<hi){const mid=Math.ceil((lo+hi)/2);if(rows[mid].time_s<=t)lo=mid;else hi=mid-1;}return lo; }
export function snapshot(d,t) {
  t=Math.max(0,Math.min(Number(t)||0,d.summary.duration_s));
  const frameIndex=lastIndexAt(d.frames,t), positionIndex=lastIndexAt(d.trajectory,t), events=d.events.filter(e=>e.time_s<=t);
  const detected=new Set(events.filter(e=>e.event==='site_detected').map(e=>e.site));
  const tasks={};
  for(const e of events){if(!e.task)continue;if(e.event==='task_created')tasks[e.task]={id:e.task,state:'pendiente',agent:null};if(e.event==='assigned')tasks[e.task]={id:e.task,state:'asignada',agent:e.agent,score_s:e.score_s};if(e.event==='completed')tasks[e.task]={...(tasks[e.task]||{}),id:e.task,state:'completada',agent:e.agent};}
  return {time:t,frameIndex,positionIndex,frame:d.frames[frameIndex],position:d.trajectory[positionIndex],events,tasks,sites:d.sites.filter(s=>detected.has(s.id)),samples:events.filter(e=>e.event==='completed'&&e.kind==='sample').length,returns:events.filter(e=>e.event==='completed'&&e.kind==='return').length};
}
export function decodeGrid(encoded,bytes=2){const raw=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));if(bytes===1)return raw;const view=new DataView(raw.buffer);return Uint16Array.from({length:raw.length/2},(_,i)=>view.getUint16(i*2,true));}
export function makePlayback(duration){return {time:0,playing:false,selection:null,policy:'information_hungarian',seek(t){this.time=Math.max(0,Math.min(Number(t)||0,duration));if(this.time>=duration)this.playing=false;},reset(){this.time=0;this.playing=false;this.selection=null;},selectRun(policy){this.reset();this.policy=policy;},tick(seconds){if(this.playing&&this.policy==='information_hungarian')this.seek(this.time+seconds);},toggle(){if(this.policy!=='information_hungarian')return;if(this.time>=duration)this.time=0;this.playing=!this.playing;}};}
export const futureEngineAdapter = Object.freeze({available:false, async calculate(){throw new Error('Motor no conectado. Esta interfaz solo reproduce registros.');}});
