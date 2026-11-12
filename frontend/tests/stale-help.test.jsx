// A delayed network response must never edit the different puzzle now displayed by the player.
import React, { useEffect,useReducer } from 'react';
import { it,expect,vi,afterEach } from 'vitest';
import { render,screen,fireEvent,act,cleanup } from '@testing-library/react';
import Play from '../src/pages/Play';
import { gameReducer,initialGame } from '../src/store';
const base={name:'Fixture',difficulty:{label:'Easy'},puzzle:{rows:3,cols:3,cells:[[{type:'black'},{type:'black',down:4},{type:'black',down:6}],[{type:'black',across:3},{type:'white'},{type:'white'}],[{type:'black',across:7},{type:'white'},{type:'white'}]]}};
/** Exercise the real reducer and Play component while controlling only HTTP response timing. */
function Harness({item}){const [game,dispatch]=useReducer(gameReducer,undefined,initialGame);useEffect(()=>dispatch({type:'reset'}),[item.id]);return <Play item={item} selected="1,1" setSelected={()=>{}} session={{game,dispatch}} loadNext={()=>{}}/>;}
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
it('ignores a reveal response after switching puzzle identity',async()=>{
  let finish;
  vi.stubGlobal('fetch',vi.fn(()=>new Promise(resolve=>{finish=resolve;})));
  const {rerender}=render(<Harness item={{...base,id:'first'}}/>);
  fireEvent.click(screen.getByRole('button',{name:'Reveal cell'}));
  rerender(<Harness item={{...base,id:'second'}}/>);
  await act(async()=>finish({ok:true,json:async()=>({solution:{'1,1':9}})}));
  expect(screen.getByRole('gridcell',{name:/Row 2, column 2/}).textContent).toBe('');
});
