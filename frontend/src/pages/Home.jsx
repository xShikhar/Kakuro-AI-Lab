// Editorial landing workspace uses the current real puzzle and actual local session history.
import React from 'react';
import { ArrowUpRight, ArrowRight, ShieldCheck, GitBranch, Layers } from 'lucide-react';
import Board from '../components/Board';
import { Button, clock } from '../components/UI';
import { readLocal } from '../store';
/** Introduce the platform through a playable puzzle and concrete paths into the research tools. */
export default function Home({item,selected,setSelected,session,navigate,puzzles}) {
  const history=readLocal('kakuro:history',[]),white=item?.puzzle.cells.flat().filter(c=>c.type==='white').length;
  return <>
    <div className="home-topline"><span className="eyebrow">AN EXPLAINABLE AI PLAYGROUND</span><span className="edition">CONSTRAINTS / CURIOSITY / CLARITY</span></div>
    <section className="hero"><div className="hero-copy"><div className="hero-kicker"><span className="status-dot"/> INTELLIGENCE, IN PLAIN SIGHT</div><h1>Small cells.<br/><em>Deep reasoning.</em></h1><p>A puzzle is more interesting when you can see the thinking. Play Kakuro, explore intelligent search, and follow every “why” to its proof.</p><div className="hero-actions"><Button onClick={()=>navigate('Play')}>Find your flow <ArrowUpRight size={19}/></Button><button className="text-button" onClick={()=>navigate('AI Solver Lab')}>Open the solver lab <ArrowRight size={17}/></button></div><div className="hero-foot"><span>01—09</span><p>Nine digits. Two directions.<br/>A whole world of constraints.</p></div></div>
    <div className="hero-board"><div className="preview-caption"><span className="eyebrow">ON THE TABLE TODAY</span><span className="pill">{item?.difficulty?.label||'Loading'}</span></div><Board compact item={item} entries={session.game.entries} notes={session.game.notes} selected={selected} onSelect={setSelected} onEntry={(key,value)=>session.dispatch({type:'entry',key,value})}/><div className="preview-bottom"><div><strong>{item?.name||'Preparing your puzzle'}</strong><span>{white??'—'} variables · {item?.puzzle.rows} × {item?.puzzle.cols} grid</span></div><button onClick={()=>navigate('Play')} aria-label="Continue puzzle"><ArrowUpRight size={24}/></button></div></div></section>
    <section className="explore-row"><div className="explore-intro"><span className="eyebrow">MORE THAN THE ANSWER</span><h2>Make the invisible<br/>understandable.</h2></div>{[
      {icon:ShieldCheck,n:'01',title:'Reason with receipts.',text:'Human techniques with independently enumerated proof certificates.',page:'AI Solver Lab'},
      {icon:GitBranch,n:'02',title:'Put strategies to the test.',text:'Same puzzle. Same limits. Actual search effort, measured fairly.',page:'Strategy Arena'},
      {icon:Layers,n:'03',title:'Find the ambiguity.',text:'Generate puzzles, inspect disagreements, and follow each clue repair.',page:'Puzzle Generator'}
    ].map(x=><button className="explore-item" key={x.n} onClick={()=>navigate(x.page)}><div><x.icon size={23}/><span>{x.n}</span></div><h3>{x.title}</h3><p>{x.text}</p><ArrowUpRight size={18}/></button>)}</section>
    <section className="bottom-strip"><div><span className="eyebrow">YOUR LOCAL NOTEBOOK</span><p>{history.length?`${history.length} completed puzzles · last solve ${clock(history.at(-1).seconds)}`:'A fresh page. Your progress stays on this device.'}</p></div><span>{puzzles.length} verified puzzles in the library</span><button className="text-button" onClick={()=>navigate('Demonstration Mode')}>Take the guided demonstration <ArrowRight size={16}/></button></section>
  </>;
}
