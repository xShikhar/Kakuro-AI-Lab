// Hook lifecycle tests exercise actual local persistence and timer transitions at the API boundary.
import { afterEach, it, expect, vi } from 'vitest';
import { renderHook, act, cleanup } from '@testing-library/react';
import { useGame } from '../src/hooks/useGame';
const item={id:'timer-fixture',puzzle:{}};
afterEach(()=>{cleanup();vi.useRealTimers();vi.unstubAllGlobals();localStorage.clear();});
it('pauses and resumes the timer, persisting actual elapsed session time',async()=>{
  vi.useFakeTimers();
  // The network boundary returns a completed HTTP response; the hook and reducer remain real.
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({classification:'compatible',violations:[],complete:false})})));
  const {result}=renderHook(()=>useGame(item));
  await act(async()=>vi.advanceTimersByTimeAsync(2000));expect(result.current.game.seconds).toBe(2);
  act(()=>result.current.dispatch({type:'pause'}));
  await act(async()=>vi.advanceTimersByTimeAsync(3000));expect(result.current.game.seconds).toBe(2);
  act(()=>result.current.dispatch({type:'pause'}));
  await act(async()=>vi.advanceTimersByTimeAsync(1000));expect(result.current.game.seconds).toBe(3);
  expect(JSON.parse(localStorage.getItem('kakuro:game:timer-fixture')).seconds).toBe(3);
});
it('records completion once and stops the timer when all constraints pass',async()=>{
  vi.useFakeTimers();
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({classification:'compatible',violations:[],complete:true})})));
  const {result}=renderHook(()=>useGame({...item,id:'completion-fixture'}));
  await act(async()=>vi.advanceTimersByTimeAsync(400));
  expect(result.current.game.completed).toBe(true);
  act(()=>vi.advanceTimersByTime(3000));expect(result.current.game.seconds).toBe(0);
  expect(JSON.parse(localStorage.getItem('kakuro:history'))).toHaveLength(1);
});
