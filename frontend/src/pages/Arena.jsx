// Measured ablation comparison, stored runs and experiment scatter plots without simulated values.
import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ScatterChart, Scatter } from 'recharts';
import { ArrowRight, Download } from 'lucide-react';
import { Button, PageHead, Notice, Metric } from '../components/UI';
import { strategyNames } from './Lab';
import { api } from '../services/api';
import { readLocal,writeLocal } from '../store';
/** Compare selected puzzles with identical time and node caps and show persisted measured outputs. */
export default function Arena({item,puzzles,active=true}) {
  const [selection,setSelection]=useState('current'),[strategies,setStrategies]=useState(Object.keys(strategyNames)),[result,setResult]=useState(()=>readLocal('kakuro:arena',null));
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[metric,setMetric]=useState('nodes'),[experiments,setExperiments]=useState(null);
  useEffect(()=>{api('experiments').then(setExperiments).catch(e=>setError(e.message));},[]);
  /** Run every selected configuration against the exact same requested puzzle set. */
  async function run() {
    setBusy(true);setError('');
    try {
      const payload={strategies,timeout:3,node_limit:100000};
      if(selection==='current')payload.puzzles=[item];
      else payload.ids=puzzles.filter(p=>selection==='all'||p.difficulty.label===selection||p.id===selection).map(p=>p.id);
      const data=await api('arena',payload);setResult(data);writeLocal('kakuro:arena',data);
    } catch(e){setError(e.message);}finally{setBusy(false);}
  }
  const chart=Object.keys(strategyNames).filter(s=>result?.results.some(r=>r.strategy===s)).map(s=>({strategy:s,value:result.results.filter(r=>r.strategy===s).reduce((a,r)=>a+r[metric],0)}));
  return <>
    <PageHead eyebrow="03 / STRATEGY ARENA" title="Good ideas deserve a fair test." description="An ablation study you can run. Identical puzzles and limits, with visualization excluded from the clock."/>
    <section className="panel arena-controls"><label>Benchmark set<select value={selection} onChange={e=>setSelection(e.target.value)}><option value="current">Current puzzle</option><option value="all">All benchmark puzzles</option>{['Beginner','Easy','Medium','Hard','Expert'].map(v=><option key={v}>{v}</option>)}<optgroup label="Individual puzzles">{puzzles.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</optgroup></select></label><div className="strategy-toggles">{Object.entries(strategyNames).map(([key,name])=><label key={key}><input type="checkbox" checked={strategies.includes(key)} onChange={()=>setStrategies(strategies.includes(key)?strategies.filter(s=>s!==key):[...strategies,key])}/>{name}</label>)}</div><Button onClick={run} busy={busy} disabled={!item||!strategies.length}>Run comparison <ArrowRight size={16}/></Button></section>
    <Notice error>{error}</Notice>
    {!result?<section className="panel empty-state large"><h2>The evidence starts here.</h2><p>Select your strategies and run an identical-input comparison.</p></section>:active&&<>
      <div className="arena-summary"><Metric label="Recorded runs" value={result.results.length}/><Metric label="Fastest / current set" value={result.fastest?strategyNames[result.fastest]:'See paired results'}/><Metric label="Timing" value="Trace disabled"/></div>
      <section className="panel chart-panel"><div className="panel-top"><div><span className="eyebrow">MEASURED SEARCH EFFORT</span><h2>Let the results speak.</h2></div><select aria-label="Comparison metric" value={metric} onChange={e=>setMetric(e.target.value)}>{[['nodes','Nodes'],['wall_time_ms','Time (ms)'],['backtracks','Backtracks'],['constraint_checks','Constraint checks']].map(([key,name])=><option value={key} key={key}>{name}</option>)}</select></div><ResponsiveContainer width="100%" height={270}><BarChart data={chart} margin={{top:20,right:20,left:0,bottom:10}}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="strategy" tick={{fontSize:11}}/><YAxis width={65}/><Tooltip/><Bar dataKey="value" fill="#d96a3a" radius={[3,3,0,0]}/></BarChart></ResponsiveContainer><p className="muted">Totals include limited runs; consult status before interpreting aggregate bars.</p></section>
      <section className="panel results-table"><div className="panel-top"><h2>The complete record</h2><button className="text-button" onClick={()=>{const blob=new Blob([JSON.stringify(result,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='kakuro-benchmark.json';a.click();URL.revokeObjectURL(url);}}><Download size={15}/> Export JSON</button></div><div className="table-scroll"><table><thead><tr><th>Puzzle / strategy</th><th>Time ms</th><th>Nodes</th><th>Backtracks</th><th>Checks</th><th>Human steps / guess</th><th>Status</th></tr></thead><tbody>{result.results.map((r,i)=><tr key={i}><td><small>{r.puzzle_id} · {r.difficulty}</small>{strategyNames[r.strategy]}</td><td>{r.wall_time_ms.toFixed(2)}</td><td>{r.nodes}</td><td>{r.backtracks}</td><td>{r.constraint_checks}</td><td>{r.technique_steps} / {r.guess_levels}</td><td><span className={`result-status ${r.status==='limit'?'limited':''}`}>{r.status}</span></td></tr>)}</tbody></table></div><p className="analysis">{result.analysis}</p></section>
    </>}
    {active&&experiments?.generation&&<section className="panel experiment-panel"><div className="eyebrow">PAIRED GENERATOR STUDY / RECORDED DATA</div><h2>Repair the doubt. Measure the difference.</h2><p className="muted">{experiments.n_paired_seeds} paired seeds per size · {experiments.budget_seconds}s cap per method · 20 attempts. Failures remain in the data.</p><div className="table-scroll"><table><thead><tr><th>Size / method</th><th>Runs</th><th>Unique success</th><th>Mean time ms</th></tr></thead><tbody>{experiments.generation.map(r=><tr key={`${r.size}-${r.mode}`}><td>{r.size} × {r.size} / {r.mode}</td><td>{r.n}</td><td>{(r.success_rate*100).toFixed(1)}%</td><td>{r.mean_time_ms.toFixed(2)}</td></tr>)}</tbody></table></div><img className="experiment-chart" src="/api/results/repair-vs-random.png" alt="Measured paired success rates and mean generation times for repair and random regeneration"/><p className="muted">Paired seeds share their initial random stream. Method-specific operations diverge afterward; this comparison applies to the recorded budgets and generator distribution.</p></section>}
    {active&&experiments?.correlation&&<section className="panel"><div className="eyebrow">RECORDED GENERATOR EXPERIMENT</div><h2>Does difficulty predict effort?</h2><p>Spearman ρ = {experiments.correlation.rho?.toFixed(3)} · n = {experiments.correlation.n} · timed-out baseline runs excluded.</p><ResponsiveContainer width="100%" height={280}><ScatterChart><CartesianGrid strokeDasharray="3 3"/><XAxis type="number" dataKey="score" name="Difficulty score"/><YAxis type="number" dataKey="nodes" name="Backtracking nodes"/><Tooltip cursor={{strokeDasharray:'3 3'}}/><Scatter data={experiments.scatter} fill="#527c65"/></ScatterChart></ResponsiveContainer><a href="/api/results/generation.csv" download>Download raw generation CSV</a></section>}
  </>;
}
