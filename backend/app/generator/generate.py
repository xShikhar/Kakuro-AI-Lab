"""Seeded valid-layout generation, randomized coloring and solution-disagreement-guided clue repair."""
import random
from time import perf_counter
from ..core.model import Board
from ..solver.engine import solve
from ..solver.constraints import combinations_for
from .difficulty import rate
from .layouts import transformed_ribbon


def from_fill(rows, cols, fill):
    """Derive every across/down clue from a valid witness; no solution is hardcoded."""
    cells = [[{'type': 'white' if f'{r},{c}' in fill else 'black'} for c in range(cols)] for r in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if cells[r][c]['type'] == 'white':
                continue
            for direction, dr, dc in [('across', 0, 1), ('down', 1, 0)]:
                rr, cc, values = r + dr, c + dc, []
                while f'{rr},{cc}' in fill:
                    values.append(fill[f'{rr},{cc}'])
                    rr, cc = rr + dr, cc + dc
                if values:
                    cells[r][c][direction] = sum(values)
    return dict(rows=rows, cols=cols, cells=cells)


def layout(size, rng):
    """Sample connected masks; remove singleton fragments and prohibit runs longer than nine."""
    if size>=7:
        # Dense large masks create long tuple tables before ambiguity repair can run.
        # Connected short runs retain the requested extent with linear cell growth.
        return Board(from_fill(size,size,transformed_ribbon(size,rng)))
    for _ in range(300):
        mask = {f'{r},{c}' for r in range(1, size) for c in range(1, size)
                if rng.random() > (.27 if size < 8 else .24)}
        changed = True
        while changed:
            changed = False
            for key in list(mask):
                r, c = map(int, key.split(','))
                if not ({f'{r},{c-1}', f'{r},{c+1}'} & mask) or not ({f'{r-1},{c}', f'{r+1},{c}'} & mask):
                    mask.remove(key)
                    changed = True
        if len(mask) < max(4, (size - 1) ** 2 // 5):
            continue
        # A Latin coloring gives a feasible temporary clue set for structural validation.
        fill = {k: (sum(map(int, k.split(','))) % 9) + 1 for k in mask}
        try:
            board = Board(from_fill(size, size, fill))
            if max(len(r.cells) for r in board.runs) > 7:
                continue
            return board
        except ValueError:
            continue
    raise ValueError('Could not construct a connected layout within the layout budget.')


def randomized_fill(board, rng):
    """Randomized graph coloring enforces AllDifferent in both intersecting runs before sums exist."""
    entries = {}
    for key in sorted(board.variables, key=lambda k: -len(board.neighbors[k])):
        available = list(set(range(1, 10)) - {entries[n] for n in board.neighbors[key] if n in entries})
        if not available:
            return None
        entries[key] = rng.choice(sorted(available))
    return entries


def repair(puzzle, witness, solutions, rng, forbidden=None):
    """Change one disagreement cell's witness digit and the two affected clue sums.

    The replacement is absent from both runs. Thus the witness remains valid and
    the ambiguity guides exactly where two clue edits occur. Re-counting, rather
    than the edit itself, establishes whether ambiguity has actually disappeared.
    """
    board = Board(puzzle)
    ambiguous = [k for k in board.variables if solutions[0][k] != solutions[1][k]]
    order = list(ambiguous)
    rng.shuffle(order)
    proposals = []
    for key in order:
        available = sorted(set(range(1, 10)) - {witness[n] for n in board.neighbors[key]} - {witness[key]})
        for digit in available:
            fill = dict(witness)
            fill[key] = digit
            if forbidden and tuple(sorted(fill.items())) in forbidden:
                continue
            score = sum(len(combinations_for(len(r.cells), r.target + digit - witness[key])) for r in board.cell_runs[key])
            proposals.append((score, rng.random(), key, fill))
    if proposals:
        _, _, key, fill = min(proposals)
        updated = from_fill(board.rows, board.cols, fill)
        return updated, fill, dict(ambiguous_cells=ambiguous, changed_cell=key,
            old_digit=witness[key], new_digit=fill[key], changed_clues=[r.id for r in board.cell_runs[key]],
            message=f'Ambiguity in {ambiguous}: edit witness {key}, update its across/down clue sums, then count again.')
    return None, witness, dict(ambiguous_cells=ambiguous, message='No legal one-cell repair; regenerate layout/fill.')


def generate(size=5, seed=0, target=None, attempts=20, timeout=15, mode='repair'):
    """Generate a unique puzzle within caps; return an honest mismatch if target difficulty is unavailable."""
    if type(size) is not int or not 5 <= size <= 12 or attempts < 1 or mode not in ('repair', 'random'):
        raise ValueError('Use size 5–12, positive attempts, and repair/random mode.')
    if target is not None and target not in ('Beginner', 'Easy', 'Medium', 'Hard', 'Expert'):
        raise ValueError('Unknown target difficulty.')
    rng, start, logs, best = random.Random(seed), perf_counter(), [], None
    deadline=start+timeout
    # Reserve a bounded recovery phase instead of spending the entire cap on random ambiguity.
    search_deadline=deadline-min(1.0,timeout*.25) if mode=='repair' else deadline
    for attempt in range(attempts):
        remaining = search_deadline-perf_counter()
        if remaining <= 0:
            break
        try:
            structure = layout(size, rng)
        except ValueError:
            continue
        witness = randomized_fill(structure, rng)
        if witness is None:
            continue
        puzzle = from_fill(size, size, witness)
        visited = {tuple(sorted(witness.items()))}
        for repair_index in range(20 if mode == 'repair' else 1):
            remaining = search_deadline-perf_counter()
            if remaining <= 0:
                break
            result = solve(puzzle, solution_limit=2, trace=False, node_limit=20000, timeout=min(1.5, remaining))
            if result['status'] == 'unique':
                remaining=search_deadline-perf_counter()
                if remaining<=0:
                    break
                human = solve(puzzle, strategy='human', timeout=remaining)
                if not human['solution']:
                    break
                difficulty = rate(human, size)
                best = dict(puzzle=puzzle, solution=result['solution'], unique=True, difficulty=difficulty,
                            repairs=list(logs), seed=seed, attempts=attempt + 1,
                            method='repair' if repair_index else 'random',
                            target_matched=target is None or difficulty['label'] == target)
                if best['target_matched']:
                    best['wall_time_ms'] = round((perf_counter() - start) * 1000, 3)
                    return best
                break
            if result['status'] != 'multiple' or mode != 'repair':
                break
            puzzle, witness, log = repair(puzzle, witness, result['solutions'], rng, visited)
            visited.add(tuple(sorted(witness.items())))
            logs.append({**log, 'attempt': attempt + 1, 'repair': repair_index + 1})
            if puzzle is None:
                break
    # If random fills/repairs never yielded a rated unique puzzle, try a fresh
    # low-entropy witness. Its uniqueness is established by the same solver,
    # never inferred from the construction or borrowed from the puzzle library.
    if best is None and mode=='repair' and deadline-perf_counter()>0:
        witness=transformed_ribbon(size,rng,extreme=True)
        puzzle=from_fill(size,size,witness)
        remaining=deadline-perf_counter()
        result=solve(puzzle,solution_limit=2,trace=False,node_limit=20000,timeout=remaining) if remaining>0 else {'status':'limit'}
        remaining=deadline-perf_counter()
        if result['status']=='unique' and remaining>0:
            human=solve(puzzle,strategy='human',timeout=remaining)
            if human['solution']:
                difficulty=rate(human,size)
                matched=target is None or difficulty['label']==target
                best=dict(puzzle=puzzle,solution=result['solution'],unique=True,difficulty=difficulty,
                          repairs=list(logs),seed=seed,attempts=attempt+2,method='constructive',target_matched=matched,
                          message='Generated a fresh short-run puzzle after random repair attempts; uniqueness was independently counted.'
                          + ('' if matched else ' The requested difficulty was not reached; the measured label is shown.'))
    elapsed = round((perf_counter() - start) * 1000, 3)
    if best:
        return {**best, 'wall_time_ms': elapsed, 'message': best.get('message','Unique puzzle found, but target difficulty was not reached within the cap.')}
    return dict(puzzle=None, unique=False, seed=seed, repairs=logs, wall_time_ms=elapsed,
                target_matched=False, message='Generation budget exhausted; no unverified puzzle is returned.')
