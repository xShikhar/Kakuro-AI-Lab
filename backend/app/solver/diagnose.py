"""Bounded breadth-first deduction refutations and escalating hints, with honest minimality status."""
from collections import deque
from time import perf_counter
from itertools import combinations
from ..core.model import Board
from .constraints import supported_tuples
from .techniques import applications


def minimum_clue_core(puzzle, entries, timeout=2):
    """Find a minimum-cardinality contradictory clue subset, conditioned on fixed player entries.

    Enumerating subsets in increasing size proves minimum cardinality. Every subset
    is decided by a complete custom CSP search. A timeout never becomes a minimum
    claim. This optimizes clue count; the fixed player assumptions are not optimized.
    """
    board=Board(puzzle)
    board.validate_entries(entries)
    start=perf_counter()

    def check():
        """Keep both subset enumeration and each exact satisfiability query bounded."""
        if perf_counter()-start>timeout:
            raise TimeoutError()

    def feasible(runs, state):
        """Decide satisfiability of this subset using exact support propagation and branching."""
        check()
        while True:
            changed=False
            for run in runs:
                tuples=supported_tuples(run,state,check)
                if not tuples:
                    return False
                for i,k in enumerate(run.cells):
                    d=state[k]&{t[i] for t in tuples}
                    if d!=state[k]:
                        state[k]=d
                        changed=True
            if not changed:
                break
        free=[k for k,d in state.items() if len(d)>1]
        if not free:
            return True
        key=min(free,key=lambda k:len(state[k]))
        for value in sorted(state[key]):
            child={k:set(d) for k,d in state.items()}
            child[key]={value}
            if feasible(runs,child):
                return True
        return False

    tested=0
    try:
        for count in range(1,len(board.runs)+1):
            for subset in combinations(board.runs,count):
                check()
                keys=set().union(*(set(r.cells) for r in subset))
                state={k:{entries[k]} if k in entries else set(range(1,10)) for k in keys}
                tested+=1
                if not feasible(subset,state):
                    return dict(minimum=True,runs=[r.id for r in subset],cells=sorted(keys),tested=tested,
                                assumptions={k:v for k,v in entries.items() if k in keys},
                                objective='Minimum number of clue constraints, conditioned on the supplied player entries.')
    except TimeoutError:
        return dict(minimum=False,runs=[],cells=[],tested=tested,message='Minimum clue-core search exhausted its time budget.')
    return dict(minimum=False,runs=[],cells=[],tested=tested,message='The supplied entries are satisfiable under all clues.')


def hint(puzzle, entries, level=1):
    """Return the easiest applicable nudge, named technique or exact candidate reduction."""
    board = Board(puzzle)
    board.validate_entries(entries)
    domains = {k: {entries[k]} if k in entries else set(range(1, 10)) for k in board.variables}
    apps = applications(board, domains, first=True)
    if not apps:
        return {'message': 'No immediate deduction: inspect candidates or use bounded search.', 'level': level}
    proof = apps[0]
    response = dict(level=level, runs=proof['runs'], cells=proof['cells'], message=f"Look at {proof['runs'][0]} and its sum.")
    if level >= 2:
        response.update(technique=proof['technique'], message=f"Use {proof['technique']} on {proof['runs'][0]}.")
    if level >= 3:
        response.update(changes=proof['conclusion'], justification=proof)
        from .engine import solve
        result=solve(puzzle,givens=entries,solution_limit=2,trace=False,timeout=3)
        if result['status']=='unique':
            cell=next((k for k in proof['cells'] if k not in entries),None)
            if cell is None:
                cell=next((k for k in board.variables if k not in entries),None)
            if cell:
                response.update(cell=cell,value=result['solution'][cell],message=f"Reveal {cell} = {result['solution'][cell]}, established by complete uniqueness checking. The easiest local technique is {proof['technique']}.")
        else:
            response['message']='Candidate reduction available, but a unique reveal could not be established within the search budget.'
    return response


def diagnose(puzzle, entries, max_states=2000, timeout=5):
    """Find a shortest contradiction chain in the finite technique-application graph.

    BFS certifies shortest length only when a contradiction is dequeued. On budget
    exhaustion the response is explicitly inconclusive. Highlighted scope is the
    deduction chain's union, not a claimed globally minimum unsatisfiable core.
    """
    board = Board(puzzle)
    board.validate_entries(entries)
    initial = {k: {entries[k]} if k in entries else set(range(1, 10)) for k in board.variables}
    queue, seen, visited = deque([(initial, [])]), set(), 0
    start = perf_counter()

    def check():
        """Stop expensive tuple work at the same deadline as the BFS."""
        if perf_counter() - start > timeout:
            raise TimeoutError()

    try:
        while queue and visited < max_states:
            check()
            state, chain = queue.popleft()
            signature = tuple((k, tuple(sorted(d))) for k, d in state.items())
            if signature in seen:
                continue
            seen.add(signature)
            visited += 1
            for run in board.runs:
                if not supported_tuples(run, state, check):
                    steps = chain + [{'technique': 'Contradiction', 'runs': [run.id], 'cells': list(run.cells), 'conclusion': {}, 'message': f'No distinct digits can reach sum {run.target} in {run.id}.'}]
                    core=minimum_clue_core(puzzle,entries,timeout=min(2,max(.01,timeout-(perf_counter()-start))))
                    return dict(contradiction=True, shortest=True, steps=steps, explored=visited, core=core,
                                cells=core['cells'] if core['minimum'] else sorted(set().union(*(set(s['cells']) for s in steps))),
                                runs=sorted(set().union(*(set(s['runs']) for s in steps))),
                                scope_minimal=core['minimum'], scope_note=core.get('objective',core.get('message')))
            for proof in applications(board, state, check):
                child = {k: set(v) for k, v in state.items()}
                child.update({k: set(v) for k, v in proof['conclusion'].items()})
                queue.append((child, chain + [{**proof, 'message': f"{proof['technique']}: {proof['conclusion']}"}]))
    except TimeoutError:
        pass
    return dict(contradiction=False, shortest=False, steps=[], cells=[], runs=[], explored=visited,
                message='No refutation within the state/time budget. This does not prove the move is correct.')
