// Complete game controls, escalating help and completion summary around the shared board.
import React, { useEffect, useRef, useState } from 'react';
import { Pause, Play as PlayIcon, Undo2, Redo2, Pencil, RotateCcw, Lightbulb, Eye, Check, HelpCircle } from 'lucide-react';
import Board, { scopes } from '../components/Board';
import { Button, PageHead, Metric, Notice, clock } from '../components/UI';
import { api } from '../services/api';
/** Provide keyboard/digit input and genuine engine-backed check, hints and reveals. */
export default function Play({item,selected,setSelected,session,loadNext}) {
  const {game,dispatch,feedback,error}=session;
  const [pencil,setPencil]=useState(false),[help,setHelp]=useState(null),[busy,setBusy]=useState(false),[localError,setError]=useState(''),[hintLevel,setHintLevel]=useState(1);
  const activePuzzle=useRef(item?.id),request=useRef(null);
  activePuzzle.current=item?.id;
  useEffect(()=>{request.current?.abort();setHelp(null);setBusy(false);setHintLevel(1);setError('');return()=>request.current?.abort();},[item?.id]);
  /** Perform one help request and highlight its actual scope. */
  async function assist(kind) {
    if(!item) return;
    const puzzleId=item.id,controller=new AbortController();request.current=controller;
    /** Ignore responses that belong to a previous puzzle or a cancelled help action. */
    const current=()=>activePuzzle.current===puzzleId&&!controller.signal.aborted;
    setBusy(true);setError('');
    try {
      if(kind==='hint') {
        const data=await api('hint',{puzzle:item.puzzle,entries:game.entries,level:hintLevel},controller.signal);
        if(!current())return;setHelp(data);
        if(data.cell&&data.value)dispatch({type:'entry',key:data.cell,value:data.value});
        setHintLevel(hintLevel%3+1);dispatch({type:'meta',changes:{hints:game.hints+1}});
      } else if(kind==='check') {
        const data=await api('check',{puzzle:item.puzzle,entries:game.entries},controller.signal);
        if(!current())return;
        setHelp({message:data.complete?'Every constraint is satisfied. Puzzle complete!':data.classification==='compatible'?'Your entries are compatible with a solution.':data.classification==='unknown'?'The checking budget was exhausted.':data.classification==='rule_violation'?'A run repeats a digit or cannot reach its sum.':'Your move is locally legal, but no complete solution extends these entries.',cells:data.violations.flatMap(v=>v.cells)});
      } else if(kind==='diagnose') {const data=await api('diagnose',{puzzle:item.puzzle,entries:game.entries},controller.signal);if(current())setHelp(data);}
      else {
        if(kind==='solution'&&!window.confirm('Reveal the complete solution? This counts as help.')) return;
        const result=await api('solve',{puzzle:item.puzzle,strategy:'full'},controller.signal);
        if(!current())return;
        if(!result.solution) throw new Error('No solution found within the search budget.');
        const keys=kind==='solution'?Object.keys(result.solution):kind==='run'?(scopes(item.puzzle).find(r=>r.id.startsWith('across:')&&r.cells.includes(selected))?.cells||[]):[selected];
        for(const key of keys) dispatch({type:'entry',key,value:result.solution[key]});
        dispatch({type:'meta',changes:{hints:game.hints+1}});setHelp({message:`Revealed ${kind}.`});
      }
    } catch(e) {if(current()&&e.name!=='AbortError')setError(e.message);} finally {if(current())setBusy(false);}
  }
  const errors=feedback?.violations?.flatMap(v=>v.cells)||[];
  return <>
    <PageHead eyebrow="01 / THE PUZZLE ROOM" title="A little focus. A lot of possibility." description="Follow the sums. Trust your reasoning. Every cell belongs to two conversations." action={<Button secondary onClick={loadNext}>New puzzle <RotateCcw size={15}/></Button>}/>
    <div className="workspace-grid"><section className="panel board-panel">
      <div className="panel-top"><div><span className="eyebrow">{item?.difficulty?.label||'Loading'} / {item?.puzzle.rows} × {item?.puzzle.cols}</span><h2>{item?.name||'Your next puzzle'}</h2></div><button className="timer" onClick={()=>dispatch({type:'pause'})} aria-label={game.paused?'Resume timer':'Pause timer'}>{game.paused?<PlayIcon size={15}/>:<Pause size={15}/>} {clock(game.seconds)}</button></div>
      <Board item={item} entries={game.entries} notes={game.notes} selected={selected} onSelect={setSelected} onEntry={(key,value)=>dispatch({type:'entry',key,value,pencil})} errors={errors} focusCells={help?.cells} focusRuns={help?.runs} paused={game.paused}/>
      <div className="board-toolbar"><button onClick={()=>dispatch({type:'undo'})} disabled={!game.past.length} aria-label="Undo"><Undo2 size={19}/></button><button onClick={()=>dispatch({type:'redo'})} disabled={!game.future.length} aria-label="Redo"><Redo2 size={19}/></button><span/><button className={pencil?'active':''} onClick={()=>setPencil(!pencil)} aria-pressed={pencil}><Pencil size={17}/> Pencil</button><button onClick={()=>{if(window.confirm('Reset this puzzle and its timer?')){dispatch({type:'reset'});setHelp(null);setHintLevel(1);}}} aria-label="Reset puzzle"><RotateCcw size={18}/></button></div>
      <div className="digit-pad">{Array.from({length:9},(_,i)=><button key={i} onClick={()=>dispatch({type:'entry',key:selected,value:i+1,pencil})} disabled={!selected||game.paused||game.completed}>{i+1}</button>)}<button onClick={()=>dispatch({type:'entry',key:selected,value:0})} aria-label="Erase cell">⌫</button></div>
      <p className="board-caption">Click a cell · type 1–9 · arrow keys to move · delete to clear</p>
    </section><aside className="side-stack">
      <section className="panel"><div className="eyebrow">YOUR SESSION</div><div className="metrics trio"><Metric label="Mistakes" value={game.mistakes}/><Metric label="Hints" value={game.hints}/><Metric label="Filled" value={Object.keys(game.entries).length}/></div><div className={`feedback ${feedback?.classification==='solution_incompatible'?'warning':''}`}>{feedback?.classification==='rule_violation'?'! Rule violation — highlighted run':feedback?.classification==='solution_incompatible'?'! Locally legal, globally incompatible':feedback?.classification==='unknown'?'Check budget exhausted':game.completed?'✓ Every constraint satisfied':'✓ Keep following the constraints'}</div></section>
      <section className="panel help-panel"><h2>A second pair of eyes.</h2><p>Ask for a direction before asking for an answer.</p><Button onClick={()=>assist('hint')} busy={busy}><Lightbulb size={17}/> Hint · level {hintLevel}</Button><div className="help-actions"><button onClick={()=>assist('check')} disabled={busy}><Check size={16}/> Check board</button><button onClick={()=>assist('diagnose')} disabled={busy}><HelpCircle size={16}/> Why is this wrong?</button><button onClick={()=>assist('cell')} disabled={busy}><Eye size={16}/> Reveal cell</button><button onClick={()=>assist('run')} disabled={busy}><Eye size={16}/> Reveal across run</button><button onClick={()=>assist('solution')} disabled={busy}><Eye size={16}/> Reveal solution</button></div></section>
      {help&&<section className="panel explanation"><div className="eyebrow">REASONING, NOT MAGIC</div><p>{help.message||help.steps?.at(-1)?.message}</p>{help.technique&&<strong>{help.technique}</strong>}{help.changes&&<pre>{JSON.stringify(help.changes,null,2)}</pre>}{help.steps?.map((s,i)=><p key={i}>{i+1}. {s.message}</p>)}{help.shortest&&<small>Shortest deduction chain certified. {help.scope_note}</small>}</section>}
      <Notice error>{localError||error}</Notice>
      {game.completed&&<section className="panel completion"><span className="eyebrow">ALL CONSTRAINTS SATISFIED</span><h2>Beautifully reasoned.</h2><p>{item?.difficulty?.label} completed in {clock(game.seconds)}, with {game.mistakes} mistakes and {game.hints} help actions. Saved to your local history.</p><Button onClick={loadNext}>Keep the momentum →</Button></section>}
    </aside></div>
  </>;
}
