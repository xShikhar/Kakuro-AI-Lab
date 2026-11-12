// Application shell preserves puzzle, game and replay state across all six navigation destinations.
import React, { useEffect, useState } from 'react';
import { Grid2X2, House, Puzzle, FlaskConical, ChartNoAxesCombined, WandSparkles, Presentation, ArrowUpRight, CircleHelp, X, Menu } from 'lucide-react';
import { api } from './services/api';
import { readLocal,writeLocal } from './store';
import { useGame } from './hooks/useGame';
import { Notice } from './components/UI';
import Home from './pages/Home';
import Play from './pages/Play';
import Lab, { useSolver } from './pages/Lab';
import Arena from './pages/Arena';
import Generator from './pages/Generator';
const routes=[['Home',House],['Play',Puzzle],['AI Solver Lab',FlaskConical],['Strategy Arena',ChartNoAxesCombined],['Puzzle Generator',WandSparkles],['Demonstration Mode',Presentation]];
/** Own shared workspace state and load only verified server library puzzles or saved generated puzzles. */
export default function App() {
  const [page,setPage]=useState('Home'),[puzzles,setPuzzles]=useState([]),[item,setItem]=useState(null),[selected,setSelected]=useState(''),[error,setError]=useState(''),[difficulty,setDifficulty]=useState('All levels'),[how,setHow]=useState(false),[menu,setMenu]=useState(false);
  const session=useGame(item),solver=useSolver(item);
  useEffect(()=>{api('puzzles').then(data=>{setPuzzles(data);const saved=readLocal('kakuro:current',null);setItem(data.find(p=>p.id===saved?.id)||saved||data[0]);if(!data.length)setError('Puzzle library is empty. Run scripts/build_library.py.');}).catch(e=>setError(`Backend unavailable: ${e.message}. Start the Python service and reload.`));},[]);
  useEffect(()=>{if(item){writeLocal('kakuro:current',item);const r=item.puzzle.cells.findIndex(row=>row.some(c=>c.type==='white'));setSelected(`${r},${item.puzzle.cells[r].findIndex(c=>c.type==='white')}`);}},[item?.id]);
  /** Change the destination while keeping the current puzzle, game, solver and replay intact. */
  function navigate(next){setPage(next);setMenu(false);window.scrollTo({top:0,behavior:'smooth'});}
  /** Select a verified challenging puzzle whose measured baseline actually backtracks. */
  function demoPuzzle(){const candidate=puzzles.find(p=>p.demo)||puzzles.at(-1);if(candidate)setItem(candidate);solver.setStrategy('full');}
  /** Advance deterministically through the current difficulty's verified puzzle library. */
  function loadNext(){const choices=puzzles.filter(p=>difficulty==='All levels'||p.difficulty.label===difficulty);if(!choices.length)return;const index=choices.findIndex(p=>p.id===item?.id);setItem(choices[(index+1)%choices.length]);}
  const filtered=puzzles.filter(p=>difficulty==='All levels'||p.difficulty.label===difficulty);
  return <div className="app-shell">
    <aside className={`sidebar ${menu?'open':''}`}><button className="brand" onClick={()=>navigate('Home')} aria-label="Kakuro AI Lab home"><span className="brand-mark"><Grid2X2 size={25}/></span><span>KAKURO<span>AI LAB</span></span><span className="brand-period">.</span></button><div className="sidebar-label">YOUR WORKSPACE</div><nav aria-label="Main navigation">{routes.map(([name,Icon],i)=><button key={name} className={page===name?'active':''} aria-current={page===name?'page':undefined} onClick={()=>{if(name==='Demonstration Mode'&&page!==name)demoPuzzle();navigate(name);}}><Icon size={18}/><span>{name}</span><small>{String(i).padStart(2,'0')}</small></button>)}</nav><div className="sidebar-bottom"><div className="lab-note"><span className="note-symbol">∑</span><p>Not just the solution.<br/><strong>The thought behind it.</strong></p></div><button className="how-link" onClick={()=>setHow(true)}><CircleHelp size={17}/> How it works <ArrowUpRight size={15}/></button><div className="offline-note"><span className="status-dot"/> Local first. Always curious.</div></div></aside>
    <div className="main-shell"><header className="topbar"><button className="mobile-menu" aria-label="Toggle navigation" onClick={()=>setMenu(!menu)}><Menu size={21}/></button><div className="breadcrumb">Workspace <span>/</span> <strong>{page}</strong></div><div className="topbar-right"><span className="local-badge"><span className="status-dot"/> OFFLINE-CAPABLE</span><span className="version">V.01</span></div></header>
    <main><Notice error>{error}</Notice><div className="puzzle-switcher"><label className="sr-only" htmlFor="difficulty">Difficulty</label><select id="difficulty" value={difficulty} onChange={e=>{setDifficulty(e.target.value);const p=puzzles.find(p=>e.target.value==='All levels'||p.difficulty.label===e.target.value);if(p)setItem(p);}}>{['All levels','Beginner','Easy','Medium','Hard','Expert'].map(v=><option key={v}>{v}</option>)}</select><label className="sr-only" htmlFor="puzzle">Puzzle</label><select id="puzzle" value={item?.id||''} onChange={e=>setItem(puzzles.find(p=>p.id===e.target.value))}>{!puzzles.some(p=>p.id===item?.id)&&item&&<option value={item.id}>{item.name}</option>}{filtered.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></div>
      {page==='Home'&&<Home {...{item,selected,setSelected,session,navigate,puzzles}}/>}
      {page==='Play'&&<Play {...{item,selected,setSelected,session,loadNext}}/>}
      {(page==='AI Solver Lab'||page==='Demonstration Mode')&&<Lab {...{item,selected,setSelected,solver}} demo={page==='Demonstration Mode'} onArena={()=>navigate('Strategy Arena')} onDemoPuzzle={demoPuzzle}/>}
      <div hidden={page!=='Strategy Arena'}><Arena {...{item,puzzles}} active={page==='Strategy Arena'}/></div>
      <div hidden={page!=='Puzzle Generator'}><Generator onLoad={p=>{setItem(p);navigate('Play');}}/></div>
      <footer className="page-footer"><span>KAKURO AI LAB</span><span>Built to question. Designed to explain.</span><span>NO CLOUD. NO BLACK BOX.</span></footer>
    </main></div>
    {how&&<div className="modal-backdrop" role="presentation" onClick={()=>setHow(false)}><section className="modal panel" role="dialog" aria-modal="true" aria-labelledby="how-title" onClick={e=>e.stopPropagation()} onKeyDown={e=>{if(e.key==='Escape')setHow(false);}}><button className="modal-close" aria-label="Close explanation" onClick={()=>setHow(false)} autoFocus><X size={20}/></button><span className="eyebrow">A SMALL GUIDE TO A BIG IDEA</span><h2 id="how-title">A puzzle is a conversation<br/>between constraints.</h2><p>Fill white cells with 1–9. A clue at the top right gives the sum across; a clue at the bottom left gives the sum down. Digits cannot repeat in either run.</p><p><strong>Variables</strong> are the empty cells. <strong>Domains</strong> are their candidate digits. <strong>Constraints</strong> say which combinations work together.</p><p>The AI removes candidates with no support, chooses constrained cells first, and backtracks when an assumption fails. The Human Logic solver attaches an independently checked proof to each deduction.</p><p>Open the Solver Lab, choose Human Logic + Proofs, and step through the reasoning. All computation runs on your machine.</p><button className="button" onClick={()=>{setHow(false);navigate('AI Solver Lab');}}>Explore the reasoning →</button></section></div>}
  </div>;
}
