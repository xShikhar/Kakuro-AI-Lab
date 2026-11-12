// Real DOM input tests cover board accessibility, keyboard navigation and visible candidate states.
import React from 'react';
import { afterEach, describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import Board from '../src/components/Board';
import Timeline from '../src/components/Timeline';
import { ProofStatus } from '../src/components/UI';
const item={id:'test',puzzle:{rows:3,cols:3,cells:[[{type:'black'},{type:'black',down:4},{type:'black',down:6}],[{type:'black',across:3},{type:'white'},{type:'white'}],[{type:'black',across:7},{type:'white'},{type:'white'}]]}};
afterEach(cleanup);
describe('interactive constraint board',()=>{
  it('enters digits, deletes and navigates between white cells',()=>{
    const entry=vi.fn(),select=vi.fn();
    render(<Board item={item} selected="1,1" onEntry={entry} onSelect={select}/>);
    const cell=screen.getByRole('gridcell',{name:/Row 2, column 2/});
    fireEvent.keyDown(cell,{key:'4'});expect(entry).toHaveBeenCalledWith('1,1',4);
    fireEvent.keyDown(cell,{key:'Delete'});expect(entry).toHaveBeenCalledWith('1,1',0);
    fireEvent.keyDown(cell,{key:'ArrowRight'});expect(select).toHaveBeenCalledWith('1,2');
  });
  it('renders pencil candidates, explicit values and disabled paused state',()=>{
    const {rerender}=render(<Board item={item} selected="1,1" entries={{'1,2':2}} notes={{'1,1':[1,3]}}/>);
    expect(screen.getByRole('gridcell',{name:/Row 2, column 2/}).textContent).toBe('13');
    expect(screen.getByRole('gridcell',{name:/Row 2, column 3/}).textContent).toBe('2');
    rerender(<Board item={item} selected="1,1" paused/>);
    expect(screen.getByRole('gridcell',{name:/Row 2, column 2/}).disabled).toBe(true);
    expect(screen.getByText('Session paused')).toBeTruthy();
  });
});
describe('real event playback',()=>{
  it('shows failed trace integrity instead of a misleading verified-prefix count',()=>{
    render(<ProofStatus report={{valid:false,verified:6,total:6,failures:[18],assumptions:0}}/>);
    expect(screen.getByRole('alert').textContent).toContain('18');
    expect(screen.queryByText(/6\/6/)).toBeNull();
  });
  it('steps forward, plays and jumps to an emitted event',()=>{
    const index=vi.fn(),play=vi.fn();
    const events=[{step:0,type:'domain_init',reason:'Initialize domains'},{step:1,type:'assign',reason:'A forced digit'}];
    render(<Timeline events={events} index={0} setIndex={index} playing={false} setPlaying={play} speed={300} setSpeed={()=>{}} level="Technical" setLevel={()=>{}}/>);
    fireEvent.click(screen.getByRole('button',{name:'Next event'}));expect(index).toHaveBeenCalledWith(1);
    fireEvent.click(screen.getByRole('button',{name:'Play replay'}));expect(play).toHaveBeenCalledWith(true);
    fireEvent.change(screen.getByRole('slider'),{target:{value:1}});expect(index).toHaveBeenCalledWith(1);
    expect(screen.getByText('A forced digit')).toBeTruthy();
  });
});
