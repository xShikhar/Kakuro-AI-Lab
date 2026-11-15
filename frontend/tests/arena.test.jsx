// Arena should never display saved measurements as though they belonged to a different puzzle.
import React from 'react';
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import Arena from '../src/pages/Arena';

afterEach(()=>{cleanup();localStorage.clear();vi.unstubAllGlobals();});

it('marks a saved current-puzzle comparison stale after the current puzzle changes',()=>{
  localStorage.setItem('kakuro:arena',JSON.stringify({
    fastest:'baseline',results:[{puzzle_id:'generated:old',strategy:'baseline',status:'solved',wall_time_ms:1,nodes:1,backtracks:0,constraint_checks:1,technique_steps:0,guess_levels:0}],
    context:{selection:'current',itemId:'generated:old'}
  }));
  vi.stubGlobal('fetch',vi.fn(()=>new Promise(()=>{})));
  render(<Arena item={{id:'generated:new',name:'Seed study / 43'}} puzzles={[]} active/>);
  expect(screen.getByText(/saved comparison is from a different puzzle or set/i)).toBeTruthy();
  expect(screen.queryByRole('table')).toBeNull();
});

it('marks results stale when the selected strategy set changes',()=>{
  localStorage.setItem('kakuro:arena',JSON.stringify({
    fastest:'baseline',results:[{puzzle_id:'puzzle-1',strategy:'baseline',status:'solved',wall_time_ms:1,nodes:1,backtracks:0,constraint_checks:1,technique_steps:0,guess_levels:0}],
    context:{selection:'current',itemId:'puzzle-1',strategies:['baseline','degree','full','human','lcv','mrv','propagation']}
  }));
  vi.stubGlobal('fetch',vi.fn(()=>new Promise(()=>{})));
  render(<Arena item={{id:'puzzle-1',name:'Puzzle 1'}} puzzles={[]} active/>);
  fireEvent.click(screen.getByLabelText('+ MRV'));
  expect(screen.getByText(/saved comparison is from a different puzzle or set/i)).toBeTruthy();
  expect(screen.queryByRole('table')).toBeNull();
});
