// User-facing game-state contracts catch lost undo history and incorrect replay restoration.
import { describe, it, expect } from 'vitest';
import { gameReducer, initialGame, reconstruct, moveSelection, generatedItem } from '../src/store.js';
describe('persistent game operations', () => {
  it('supports entry, pencil marks, undo and redo without corrupting history', () => {
    let s = initialGame();
    s = gameReducer(s, {type:'entry', key:'1,1', value:3});
    s = gameReducer(s, {type:'entry', key:'1,2', value:4, pencil:true});
    expect(s.entries).toEqual({'1,1':3});
    expect(s.notes['1,2']).toEqual([4]);
    s = gameReducer(s, {type:'undo'});
    expect(s.notes['1,2']).toBeUndefined();
    s = gameReducer(s, {type:'redo'});
    expect(s.notes['1,2']).toEqual([4]);
  });
  it('restores branch state instead of retaining failed assignments', () => {
    const events = [{snapshot:{a:[1,2],b:[3,4]}}, {after:{a:[1],b:[4]}}, {snapshot:{a:[1,2],b:[3,4]}}];
    expect(reconstruct(events, 2)).toEqual({a:[1,2],b:[3,4]});
  });
  it('moves to the next white cell without landing on a clue', () => {
    expect(moveSelection('1,1', 'ArrowRight', ['1,1','1,3','2,1'])).toBe('1,3');
  });
  it('unlocks an incomplete board after undoing a completed solve',()=>{
    let s=gameReducer(initialGame(),{type:'entry',key:'1,1',value:3});
    s=gameReducer(s,{type:'meta',changes:{completed:true}});
    s=gameReducer(s,{type:'undo'});
    expect(s.completed).toBe(false);
    s=gameReducer(s,{type:'entry',key:'1,1',value:4});
    expect(s.entries['1,1']).toBe(4);
  });
  it('identifies generated games by puzzle content and the returned seed',()=>{
    const first=generatedItem({seed:42,puzzle:{rows:5,cells:[[1]]},difficulty:{}});
    const other=generatedItem({seed:42,puzzle:{rows:5,cells:[[2]]},difficulty:{}});
    expect(first.id).not.toBe(other.id);
    expect(first.name).toContain('42');
  });
});
