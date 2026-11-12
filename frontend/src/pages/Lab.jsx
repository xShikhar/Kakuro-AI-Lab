// Streaming solver lab and live demonstration share real trace playback and engine controls.
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { FlaskConical, Play, Square, RotateCcw, ArrowRight } from 'lucide-react';
import Board from '../components/Board';
import Timeline, { SearchTree } from '../components/Timeline';
import { Button, PageHead, Metric, Notice, ProofStatus } from '../components/UI';
import { streamSolve } from '../services/api';
import { reconstruct } from '../store';
export const strategyNames={baseline:'Basic Backtracking',mrv:'+ MRV',degree:'+ MRV + Degree',lcv:'+ MRV + Degree + LCV',propagation:'Propagation only',full:'Full CSP',human:'Human Logic + Proofs'};
/** Keep a complete replay session above page navigation, including real streamed events. */
export function useSolver(item) {
  const [events,setEvents]=useState([]),[result,setResult]=useState(null),[index,setIndex]=useState(0),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [strategy,setStrategy]=useState('full'),[playing,setPlaying]=useState(false),[speed,setSpeed]=useState(300),[level,setLevel]=useState('Technical');
  const controller=useRef(),id=useRef(item?.id);
  /** Cancel a live search and discard its trace when a different puzzle is selected. */
  function reset(){controller.current?.abort();setEvents([]);setResult(null);setIndex(0);setPlaying(false);setBusy(false);setError('');}
  useEffect(()=>{if(item?.id!==id.current){id.current=item?.id;reset();}},[item?.id]);
  useEffect(()=>()=>controller.current?.abort(),[]);
  useEffect(()=> {if(!playing) return;const timer=setInterval(()=>setIndex(i=>{if(i>=events.length-1){setPlaying(false);return i;}return i+1;}),speed);return()=>clearInterval(timer);},[playing,speed,events.length]);
  /** Start a worker-backed solve, batching event delivery so heavy searches cannot flood React renders. */
  async function run(override) {
    if(!item) return;
    reset();setBusy(true);const abort=new AbortController();controller.current=abort;
    let received=[],flush;
    try {
      flush=setInterval(()=>setEvents([...received]),80);
      await streamSolve({puzzle:item.puzzle,strategy:override||strategy,node_limit:100000,timeout:15},e=>received.push(e),setResult,abort.signal);
      setEvents([...received]);
    } catch(e){if(e.name!=='AbortError')setError(e.message);} finally {clearInterval(flush);setBusy(false);}
  }
  return {events,result,index,setIndex,busy,error,strategy,setStrategy,playing,setPlaying,speed,setSpeed,level,setLevel,run,reset,stop:()=>controller.current?.abort()};
}
/** Present the engine's actual domains, heuristic decisions, proofs and reversible search. */
export default function Lab({item,selected,setSelected,solver,demo=false,onArena,onDemoPuzzle}) {
  const s=solver,event=s.events[s.index];
  const domains=useMemo(()=>s.events.length?reconstruct(s.events,s.index):Object.fromEntries(item?.puzzle.cells.flatMap((row,r)=>row.flatMap((c,col)=>c.type==='white'?[[`${r},${col}`,[1,2,3,4,5,6,7,8,9]]]:[]))||[]),[s.events,s.index,item]);
  return <>
    <PageHead eyebrow={demo?'05 / PRESENTATION STUDIO':'02 / AI SOLVER LAB'} title={demo?'Let the reasoning do the talking.':'Watch a solution take shape.'} description={demo?'A repeatable demonstration, powered entirely by the live engine.':'Inspect every elimination, follow every decision, and rewind any assumption.'} action={demo?<Button secondary onClick={()=>{s.reset();onDemoPuzzle();}}>Reset demonstration <RotateCcw size={16}/></Button>:<span className="pill"><span className="status-dot"/> CUSTOM PYTHON ENGINE</span>}/>
    {demo&&<div className="demo-stages">{[['Initial domains',()=>s.setIndex(0)],['Propagation',()=>s.setIndex(Math.max(0,s.events.findIndex(e=>e.type==='eliminate_candidate')))],['Decision',()=>s.setIndex(Math.max(0,s.events.findIndex(e=>e.type==='heuristic_select')))],['Backtrack',()=>s.setIndex(Math.max(0,s.events.findIndex(e=>e.type==='backtrack')))],['Solution',()=>s.setIndex(s.events.length-1)],['Compare strategies',onArena]].map(([name,fn],i)=><button key={name} onClick={fn} disabled={i<5&&!s.events.length}><span>0{i+1}</span>{name}</button>)}</div>}
    <div className="solver-config"><label>Solver configuration<select value={s.strategy} onChange={e=>s.setStrategy(e.target.value)} disabled={s.busy}>{Object.entries(strategyNames).map(([key,name])=><option key={key} value={key}>{name}</option>)}</select></label><span className="config-note">100,000 nodes · 15s cap · real-time trace</span>{s.busy?<Button secondary onClick={s.stop}><Square size={15}/> Stop search</Button>:<Button onClick={()=>s.run()} disabled={!item}><Play size={16}/> Run solver</Button>}</div>
    <Notice error>{s.error}</Notice>
    <div className="workspace-grid lab-grid"><section className="panel board-panel"><div className="panel-top"><div><div className="eyebrow">{item?.difficulty?.label} / {item?.name}</div><h2>The constraint canvas</h2></div><span className="count-badge">{s.result?.status|| (s.busy?'computing':'ready')}</span></div><Board item={item} domains={domains} selected={selected} onSelect={setSelected} focusCells={event?.cells} focusRuns={event?.runs}/><div className="legend"><span><i className="legend-orange"/> Active deduction</span><span><i className="legend-green"/> Selected run</span><span>Small digits = candidates</span></div><div className="metrics four"><Metric label="Nodes" value={s.result?.metrics.nodes}/><Metric label="Backtracks" value={s.result?.metrics.backtracks}/><Metric label="Eliminations" value={s.result?.metrics.candidate_eliminations}/><Metric label="Solve time" value={s.result?.metrics.wall_time_ms?.toFixed(1)} unit="ms"/></div><ProofStatus report={s.result?.verification}/>{s.result?.status==='limit'&&<Notice>Search stopped at its budget. Uniqueness and unsatisfiability remain unproved.</Notice>}</section><Timeline {...s}/></div>
    <SearchTree events={s.events}/>
  </>;
}
