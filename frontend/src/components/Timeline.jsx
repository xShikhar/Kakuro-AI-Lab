// Real event replay controls and search-tree view; geometry comes only from emitted branch events.
import React from 'react';
import { Play, Pause, SkipBack, SkipForward, ChevronLeft, ChevronRight } from 'lucide-react';
/** Render a bounded window of a potentially large reasoning trace and its playback controls. */
export default function Timeline({events,index,setIndex,playing,setPlaying,speed,setSpeed,level,setLevel}) {
  const event=events[index],start=Math.max(0,index-3),visible=events.slice(start,start+8);
  /** Produce deterministic audience-specific text from the event's real operation. */
  function reason(e) {
    if(level==='Research') return `${e.reason} Scopes: ${(e.runs||[]).join(', ')}. Δ ${JSON.stringify(e.after)}`;
    if(level==='Beginner') return e.friendly||e.reason.replaceAll('tuple','digit arrangement').replaceAll('domain','candidate set');
    return e.reason;
  }
  return <section className="panel timeline"><div className="panel-top"><div><span className="eyebrow">THE REASONING TRAIL</span><h2>Nothing behind the curtain.</h2></div><span className="count-badge">{events.length} events</span></div>
    <div className="replay-controls"><button aria-label="First event" onClick={()=>setIndex(0)} disabled={!events.length}><SkipBack size={16}/></button><button aria-label="Previous event" onClick={()=>setIndex(Math.max(0,index-1))} disabled={index<=0}><ChevronLeft size={17}/></button><button aria-label={playing?'Pause replay':'Play replay'} className="play-control" onClick={()=>setPlaying(!playing)} disabled={!events.length}>{playing?<Pause size={18}/>:<Play size={18}/>}</button><button aria-label="Next event" onClick={()=>setIndex(Math.min(events.length-1,index+1))} disabled={index>=events.length-1}><ChevronRight size={17}/></button><button aria-label="Last event" onClick={()=>setIndex(events.length-1)} disabled={!events.length}><SkipForward size={16}/></button><select aria-label="Replay speed" value={speed} onChange={e=>setSpeed(Number(e.target.value))}><option value={1000}>1×</option><option value={300}>3×</option><option value={80}>10×</option></select></div>
    <input className="replay-range" type="range" aria-label="Jump to event" min={0} max={Math.max(0,events.length-1)} value={Math.max(0,index)} onChange={e=>{setPlaying(false);setIndex(Number(e.target.value));}}/>
    <div className="timeline-meta"><span>STEP {events.length?index+1:0} / {events.length}</span><select aria-label="Explanation detail" value={level} onChange={e=>setLevel(e.target.value)}>{['Beginner','Technical','Research'].map(v=><option key={v}>{v}</option>)}</select></div>
    {!events.length?<div className="empty-state">Run a solver to watch candidates become conclusions.</div>:<ol className="event-list">{visible.map((e,i)=><li key={e.step} className={start+i===index?'current':''}><button onClick={()=>setIndex(start+i)}><span className={`event-dot ${e.type}`}/><div><div className="event-label"><strong>{e.type.replaceAll('_',' ')}</strong><span>{String(e.step+1).padStart(3,'0')}</span></div><p>{reason(e)}</p></div></button></li>)}</ol>}
    {event?.justification&&<details><summary>Inspect proof premises</summary><pre>{JSON.stringify(event.justification,null,2)}</pre></details>}
  </section>;
}
/** Visualize the actual first 180 search branches, with depth encoded vertically. */
export function SearchTree({events}) {
  const branches=events.filter(e=>e.type==='branch').slice(0,180),depth=Math.max(1,...branches.map(e=>e.depth+1));
  return <section className="panel tree-panel"><div className="eyebrow">SEARCH TOPOLOGY</div><h2>Every branch leaves a trace.</h2>{branches.length?<><svg viewBox="0 0 700 160" role="img" aria-label={`${branches.length} real search branches; depth shown vertically`}>{branches.map((e,i)=> {
    const x=20+i*660/Math.max(1,branches.length-1),y=20+(e.depth+1)*120/depth;
    const parent=branches.slice(0,i).findLastIndex(p=>p.depth===e.depth-1);
    const px=parent<0?350:20+parent*660/Math.max(1,branches.length-1),py=e.depth===0?10:20+e.depth*120/depth;
    return <g key={e.step}><line x1={px} y1={py} x2={x} y2={y} stroke="var(--line)"/><circle cx={x} cy={y} r="3" fill="var(--accent)"><title>{e.reason}</title></circle></g>;
  })}</svg><small>First {branches.length} branch events. Vertical position is actual search depth.</small></>:<p className="muted">No branching yet. A pure deduction solve may need no search tree.</p>}</section>;
}
