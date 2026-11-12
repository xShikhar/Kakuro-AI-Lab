// Persistent game lifecycle, timer and real backend feedback kept outside board rendering.
import { useEffect, useReducer, useState, useRef } from 'react';
import { gameReducer, initialGame, readLocal, writeLocal } from '../store';
import { api } from '../services/api';
/** Maintain a distinct saved game per puzzle, debounce checks and record completions exactly once. */
export function useGame(item) {
  const [game,dispatch]=useReducer(gameReducer,undefined,initialGame);
  const [feedback,setFeedback]=useState(null),[error,setError]=useState('');
  const current=useRef(null), mistaken=useRef(new Set());
  useEffect(()=> {
    if(!item) return;
    current.current=item.id;
    mistaken.current=new Set(); setFeedback(null);
    dispatch({type:'load',state:readLocal(`kakuro:game:${item.id}`,initialGame())});
  },[item?.id]);
  useEffect(()=> {if(item && current.current===item.id) writeLocal(`kakuro:game:${item.id}`,game);},[game]);
  useEffect(()=> {const timer=setInterval(()=>dispatch({type:'tick'}),1000);return ()=>clearInterval(timer);},[]);
  useEffect(()=> {
    if(!item || current.current!==item.id) return;
    const controller=new AbortController();
    const timer=setTimeout(async()=> {
      try {
        const data=await api('check',{puzzle:item.puzzle,entries:game.entries},controller.signal);
        setFeedback(data); setError('');
        const signature=JSON.stringify(game.entries);
        if(['rule_violation','solution_incompatible'].includes(data.classification) && !mistaken.current.has(signature)) {
          mistaken.current.add(signature); dispatch({type:'meta',changes:{mistakes:game.mistakes+1}});
        }
        if(data.complete && !game.completed) {
          dispatch({type:'meta',changes:{completed:true,completionRecorded:true}});
          if(!game.completionRecorded){
            const history=readLocal('kakuro:history',[]);
            writeLocal('kakuro:history',[...history,{id:item.id,name:item.name,difficulty:item.difficulty?.label,seconds:game.seconds,mistakes:game.mistakes,hints:game.hints,date:new Date().toISOString()}].slice(-200));
          }
        }
      } catch(e) {if(e.name!=='AbortError') setError(e.message);}
    },300);
    return ()=> {clearTimeout(timer);controller.abort();};
  },[item?.id,game.entries]);
  return {game,dispatch,feedback,error};
}
