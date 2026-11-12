"""Seven genuine strategy configurations sharing bounded search, metrics and replayable events."""
from time import perf_counter
from .constraints import consistent, supported_tuples
from .replay import snapshot
from ..core.model import Board

STRATEGIES = ['baseline', 'mrv', 'degree', 'lcv', 'propagation', 'full', 'human']


class SearchLimit(Exception):
    """Signal incomplete enumeration without incorrectly reporting unsatisfiability."""


def solve(puzzle, strategy='full', givens=None, node_limit=100000, timeout=10,
          solution_limit=1, trace=True, emit=None, cancelled=None):
    """Solve/count a Kakuro CSP with custom search; return verified solutions and actual metrics."""
    if strategy not in STRATEGIES:
        raise ValueError('Unknown solver strategy.')
    if node_limit < 1 or timeout <= 0 or solution_limit < 1:
        raise ValueError('Search limits must be positive.')
    board = Board(puzzle)
    givens = givens or {}
    board.validate_entries(givens)
    start = perf_counter()
    domains = {k: {givens[k]} if k in givens else set(range(1, 10)) for k in board.variables}
    metrics = dict(nodes=0, backtracks=0, assignments=0, constraint_checks=0,
                   candidate_eliminations=0, max_depth=0, solutions_found=0,
                   technique_steps=0, guess_levels=0)
    events, solutions, step = [], [], 0

    def check():
        """Enforce wall-clock and cancellation budgets even during tuple enumeration."""
        if perf_counter() - start >= timeout or cancelled and cancelled():
            raise SearchLimit()

    def event(kind, state, cells=(), runs=(), before=None, after=None, reason='', **extra):
        """Record a stable real operation; callbacks stream the same events used for replay."""
        nonlocal step
        if not trace and emit is None:
            return
        item = dict(step=step, type=kind, cells=list(cells), runs=list(runs),
                    before=before or {}, after=after or {}, reason=reason, **extra)
        if kind in ('domain_init', 'backtrack', 'solved'):
            item['snapshot'] = snapshot(state)
        step += 1
        if trace:
            events.append(item)
        if emit:
            emit(item)

    def reduce(state, changes, kind, runs, reason, proof=None):
        """Apply only supported removals and expose forced singletons as assignment events."""
        before = {k: sorted(state[k]) for k in changes}
        metrics['candidate_eliminations'] += sum(len(state[k] - set(v)) for k, v in changes.items())
        for k, v in changes.items():
            state[k] = set(v)
        extra = {'justification': proof} if proof else {}
        event(kind, state, changes, runs, before, {k: sorted(v) for k, v in changes.items()}, reason, **extra)
        for k in changes:
            if len(state[k]) == 1 and len(before[k]) > 1:
                metrics['assignments'] += 1
                event('assign', state, [k], runs, {k: before[k]}, {k: sorted(state[k])}, f'{k} is forced to {next(iter(state[k]))}.', forced=True, **extra)

    def propagate(state):
        """Reach a fixed point: every surviving candidate must have support in each run."""
        while True:
            changed = False
            for run in board.runs:
                metrics['constraint_checks'] += 1
                tuples = supported_tuples(run, state, check)
                event('constraint_eval', state, run.cells, [run.id], reason=f'{run.id}: {len(tuples)} supported tuples sum to {run.target}.')
                if not tuples:
                    event('contradiction', state, run.cells, [run.id], reason=f'No distinct-digit tuple can satisfy sum {run.target}.')
                    return False
                changes = {k: state[k] & {t[i] for t in tuples} for i, k in enumerate(run.cells) if state[k] - {t[i] for t in tuples}}
                if changes:
                    reduce(state, changes, 'eliminate_candidate', [run.id], f'Remove values with no support in {run.id} (sum {run.target}).')
                    changed = True
            if not changed:
                return True

    def human(state):
        """Apply the easiest available named deduction, recording its complete certificate."""
        from .techniques import applications
        while True:
            check()
            if any(not d for d in state.values()):
                return False
            apps = applications(board, state, check, first=True)
            if not apps:
                return True
            proof = apps[0]
            metrics['technique_steps'] += 1
            metrics['constraint_checks'] += len(proof['premises']['constraints'])
            reduce(state, proof['conclusion'], 'technique_applied', proof['runs'], f"{proof['technique']} narrows {', '.join(proof['cells'])}.", proof)
            if any(not state[k] for k in proof['cells']):
                event('contradiction', state, proof['cells'], proof['runs'], reason='The certified deduction leaves an empty candidate domain.', justification=proof)
                return False

    def legal_values(key, entries):
        """Compute current legal moves without changing any domains (MRV search variants)."""
        values = []
        for v in domains[key]:
            trial = {**entries, key: v}
            ok = True
            for run in board.cell_runs[key]:
                metrics['constraint_checks'] += 1
                if not consistent(run, trial):
                    ok = False
                    break
            if ok:
                values.append(v)
        return sorted(values)

    def search(state, entries, depth):
        """Copy child domains so every failed branch can restore its parent exactly."""
        check()
        if metrics['nodes'] >= node_limit:
            raise SearchLimit()
        metrics['nodes'] += 1
        metrics['max_depth'] = max(metrics['max_depth'], depth)
        if strategy in ('propagation', 'full') and not propagate(state) or strategy == 'human' and not human(state):
            return
        if strategy in ('propagation', 'full', 'human'):
            entries = {k: next(iter(d)) for k, d in state.items() if len(d) == 1}
        for run in board.runs:
            metrics['constraint_checks'] += 1
            if not consistent(run, entries):
                event('contradiction', state, run.cells, [run.id], reason=f'{run.id}: duplicate or unattainable sum {run.target}; abandon this branch.', depth=depth)
                return
        remaining = [k for k in board.variables if k not in entries]
        if not remaining:
            if board.valid_solution(entries):
                solutions.append(dict(entries))
                metrics['solutions_found'] += 1
                event('solved', {k: {v} for k, v in entries.items()}, entries, reason='All sum and distinctness constraints independently validated.', depth=depth)
            return
        candidates = {k: sorted(state[k]) for k in remaining}
        if strategy in ('mrv', 'degree', 'lcv'):
            candidates = {k: legal_values(k, entries) for k in remaining}
        degree = {k: len(board.neighbors[k] & set(remaining)) for k in remaining}
        if strategy in ('baseline', 'propagation'):
            key = remaining[0]
        else:
            key = min(remaining, key=lambda k: (len(candidates[k]), -degree[k] if strategy != 'mrv' else 0, board.variables.index(k)))
        values = candidates[key]
        scores = {}
        if strategy in ('lcv', 'full', 'human'):
            for v in values:
                # Count neighbor values ruled out by tentative assignment: lower is less constraining.
                impact = 0
                for n in board.neighbors[key] & set(remaining):
                    for nv in candidates[n]:
                        trial = {**entries, key: v, n: nv}
                        for run in board.cell_runs[n]:
                            metrics['constraint_checks'] += 1
                            if not consistent(run, trial):
                                impact += 1
                                break
                scores[v] = impact
            values = sorted(values, key=lambda v: (scores[v], v))
        event('heuristic_select', state, [key], [r.id for r in board.cell_runs[key]], reason=f"{strategy}: select {key} by "+('fixed row order' if strategy in ('baseline','propagation') else 'minimum remaining values'+(' and degree tie-break' if strategy!='mrv' else ''))+f"; {len(values)} candidate values, {degree[key]} unassigned neighbors; LCV impacts {scores}.", candidates={k: len(v) for k, v in candidates.items()}, degree=degree[key], lcv=scores, depth=depth)
        if not values:
            event('contradiction', state, [key], [r.id for r in board.cell_runs[key]], reason=f'{key} has no legal value under the current decisions.', depth=depth)
        if strategy == 'human':
            metrics['guess_levels'] = max(metrics['guess_levels'], depth + 1)
        for value in values:
            child = {k: set(d) for k, d in state.items()}
            child[key] = {value}
            metrics['assignments'] += 1
            event('branch', child, [key], before={key: sorted(state[key])}, after={key: [value]}, reason=f'Try {key} = {value}; this is an assumption, not a proved deduction.', depth=depth, value=value)
            event('assign', child, [key], before={key: sorted(state[key])}, after={key: [value]}, reason=f'Search decision {key} = {value}.', forced=False, depth=depth)
            before_count = len(solutions)
            search(child, {**entries, key: value}, depth + 1)
            if len(solutions) >= solution_limit:
                return
            metrics['backtracks'] += 1
            event('backtrack', state, [key], reason=f'Restore parent domains after {key} = {value}; '+('no solution in this branch.' if before_count == len(solutions) else 'continue solution counting.'), depth=depth)

    event('domain_init', domains, board.variables, reason='Each white cell starts with digits 1–9, restricted by supplied entries.')
    exhausted = True
    try:
        search(domains, dict(givens), 0)
    except SearchLimit:
        exhausted = False
    metrics['wall_time_ms'] = round((perf_counter() - start) * 1000, 4)
    status = 'limit' if not exhausted else 'multiple' if len(solutions) >= 2 else 'unique' if len(solutions) == 1 and solution_limit > 1 else 'solved' if solutions else 'unsatisfiable'
    return dict(strategy=strategy, status=status, solution=solutions[0] if solutions else None,
                solutions=solutions, metrics=metrics, trace=events, exhaustive=exhausted and len(solutions) < solution_limit)
