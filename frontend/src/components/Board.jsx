// Accessible Kakuro grid with true run highlights, clue geometry and domain change animations.
import React, { useMemo } from 'react';
import { moveSelection } from '../store';
/** Derive across/down scopes directly from clue cells for user interaction. */
export function scopes(puzzle) {
  const runs=[];
  puzzle.cells.forEach((row,r)=>row.forEach((cell,c)=> {
    if(cell.type!=='black') return;
    for(const [direction,dr,dc] of [['across',0,1],['down',1,0]]) if(cell[direction]) {
      const cells=[];let rr=r+dr,cc=c+dc;
      while(puzzle.cells[rr]?.[cc]?.type==='white'){cells.push(`${rr},${cc}`);rr+=dr;cc+=dc;}
      runs.push({id:`${direction}:${r},${c}`,cells,clue:`${r},${c}`,target:cell[direction]});
    }
  }));return runs;
}
/** Render player values or reconstructed solver domains with complete keyboard controls. */
export default function Board({item,entries={},notes={},domains,selected,onSelect,onEntry,focusCells=[],focusRuns=[],errors=[],paused=false,compact=false}) {
  const runs=useMemo(()=>item?scopes(item.puzzle):[],[item]);
  if(!item) return <div className="board-empty" aria-busy="true">Preparing the puzzle library…</div>;
  const p=item.puzzle,variables=p.cells.flatMap((row,r)=>row.flatMap((cell,c)=>cell.type==='white'?[`${r},${c}`]:[]));
  const related=new Set(runs.filter(r=>r.cells.includes(selected)).flatMap(r=>r.cells));
  const clueFocus=new Set(runs.filter(r=>focusRuns.includes(r.id)).map(r=>r.clue));
  /** Handle navigation and digit entry on the focused cell without capturing global shortcuts. */
  function keyboard(e,key) {
    if(e.key.startsWith('Arrow')) {e.preventDefault();const next=moveSelection(key,e.key,variables);onSelect?.(next);document.getElementById(`cell-${next}`)?.focus();}
    else if(/^[1-9]$/.test(e.key)) {e.preventDefault();onEntry?.(key,Number(e.key));}
    else if(['Backspace','Delete','0'].includes(e.key)) {e.preventDefault();onEntry?.(key,0);}
  }
  return <div className={`board-wrap ${compact?'compact':''} ${paused?'is-paused':''}`}>
    <div className="kakuro-board" role="grid" aria-label="Kakuro puzzle" style={{'--cols':p.cols}}>
      {p.cells.map((row,r)=><div role="row" className="board-row" key={r}>{row.map((cell,c)=> {
        const key=`${r},${c}`;
        if(cell.type==='black') return <div role="gridcell" key={key} className={`black-cell ${cell.across||cell.down?'clue-cell':''} ${clueFocus.has(key)?'clue-focus':''}`} aria-label={`Clue row ${r+1} column ${c+1}${cell.across?`, across ${cell.across}`:''}${cell.down?`, down ${cell.down}`:''}`}>
          {cell.across&&<span className="across-clue">{cell.across}</span>}{cell.down&&<span className="down-clue">{cell.down}</span>}
        </div>;
        const domain=domains?.[key],value=domain?.length===1?domain[0]:domains?null:entries[key];
        const candidates=domains?domain:notes[key];
        return <button role="gridcell" id={`cell-${key}`} key={key} aria-selected={key===selected} aria-label={`Row ${r+1}, column ${c+1}${value?`, digit ${value}`:`, candidates ${(candidates||[]).join(' ')||'empty'}`}`} tabIndex={selected===key?0:-1}
          className={`white-cell ${related.has(key)?'related':''} ${selected===key?'selected':''} ${focusCells.includes(key)?'ai-focus':''} ${errors.includes(key)?'invalid':''}`}
          onClick={()=>onSelect?.(key)} onKeyDown={e=>keyboard(e,key)} disabled={paused}>
          {value?<span className="cell-value" key={value}>{value}</span>:<span className="pencil-grid">{Array.from({length:9},(_,i)=><span key={i}>{candidates?.includes(i+1)?i+1:''}</span>)}</span>}
          {errors.includes(key)&&<span className="error-dot" aria-label="Rule violation">!</span>}
        </button>;
      })}</div>)}
    </div>
    {paused&&<div className="pause-overlay">Session paused</div>}
  </div>;
}
