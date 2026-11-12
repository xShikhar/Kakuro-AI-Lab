// Generation failures must not claim an accepted unique fill or offer an unverified board to Play.
import React from 'react';
import { afterEach,it,expect,vi } from 'vitest';
import { render,screen,fireEvent,cleanup } from '@testing-library/react';
import Generator from '../src/pages/Generator';

afterEach(()=>{cleanup();vi.unstubAllGlobals();});
it('shows a real generation failure without claiming an accepted unique fill',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({unique:false,puzzle:null,repairs:[],message:'Generation budget exhausted; no unverified puzzle is returned.'})})));
  render(<Generator onLoad={()=>{throw new Error('An unverified board cannot be loaded');}}/>);
  fireEvent.click(screen.getByRole('button',{name:'Generate a puzzle'}));
  expect(await screen.findByText('Generation budget exhausted; no unverified puzzle is returned.')).toBeTruthy();
  expect(screen.queryByText(/first accepted fill was already unique/)).toBeNull();
  expect(screen.queryByRole('button',{name:/Take it to the puzzle room/})).toBeNull();
});
