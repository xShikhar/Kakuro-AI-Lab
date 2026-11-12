// Pure game transitions and replay functions shared by the UI and behavioral tests.
/** Create a clean, serializable game session for local persistence. */
export function initialGame() { return {entries:{}, notes:{}, past:[], future:[], seconds:0, paused:false, mistakes:0, hints:0, completed:false,completionRecorded:false}; }
/** Apply entries and history operations without mutating earlier undo snapshots. */
export function gameReducer(state, action) {
  if (action.type === 'reset') return initialGame();
  if (action.type === 'load') return {...initialGame(), ...action.state};
  if (action.type === 'tick') return state.paused || state.completed ? state : {...state, seconds:state.seconds+1};
  if (action.type === 'pause') return {...state, paused:!state.paused};
  if (action.type === 'meta') return {...state, ...action.changes};
  if (action.type === 'undo') {
    if (!state.past.length) return state;
    return {...state, ...state.past.at(-1), completed:false, past:state.past.slice(0,-1), future:[{entries:state.entries,notes:state.notes},...state.future]};
  }
  if (action.type === 'redo') {
    if (!state.future.length) return state;
    return {...state, ...state.future[0], completed:false, past:[...state.past,{entries:state.entries,notes:state.notes}],future:state.future.slice(1)};
  }
  if (action.type !== 'entry' || state.paused || state.completed) return state;
  const entries = {...state.entries}, notes = {...state.notes};
  if (action.pencil && action.value) {
    const previous = notes[action.key] || [];
    notes[action.key] = previous.includes(action.value) ? previous.filter(v=>v!==action.value) : [...previous,action.value].sort();
  } else if (action.value) { entries[action.key] = action.value; delete notes[action.key]; }
  else { delete entries[action.key]; delete notes[action.key]; }
  return {...state, entries, notes, past:[...state.past.slice(-199),{entries:state.entries,notes:state.notes}],future:[]};
}
/** Reconstruct real solver domains, including complete restoration after backtracking. */
export function reconstruct(events, index) {
  let state = {};
  for (const e of events.slice(0,index+1)) state = e.snapshot ? {...e.snapshot} : {...state,...(e.after||{})};
  return state;
}
/** Move along the requested row or column, skipping clue cells and respecting boundaries. */
export function moveSelection(key, direction, variables) {
  const [r,c] = key.split(',').map(Number);
  const horizontal = ['ArrowRight','ArrowLeft'].includes(direction);
  const positive = ['ArrowRight','ArrowDown'].includes(direction);
  const available = variables.filter(k=> { const [rr,cc]=k.split(',').map(Number); return horizontal ? rr===r && (positive?cc>c:cc<c) : cc===c && (positive?rr>r:rr<r); });
  available.sort((a,b)=> {const aa=a.split(',').map(Number),bb=b.split(',').map(Number); return (positive?1:-1)*(horizontal?aa[1]-bb[1]:aa[0]-bb[0]);});
  return available[0] || key;
}
/** Safely parse locally stored JSON, falling back when storage is corrupt or unavailable. */
export function readLocal(key, fallback) { try {return JSON.parse(localStorage.getItem(key)) ?? fallback;} catch {return fallback;} }
/** Persist bounded user data while allowing private browsing and full storage to remain usable. */
export function writeLocal(key,value) { try {localStorage.setItem(key,JSON.stringify(value));} catch { /* Session remains usable if storage is denied. */ } }
/** Bind a generated session to its exact puzzle content and immutable generation response. */
export function generatedItem(result) {return result?.puzzle?{id:`generated:${JSON.stringify(result.puzzle)}`,name:`Seed study / ${result.seed}`,puzzle:result.puzzle,difficulty:result.difficulty}:null;}
