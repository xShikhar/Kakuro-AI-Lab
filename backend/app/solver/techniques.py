"""Ranked human deductions; each reduction carries the exact local premises it used."""
from itertools import combinations
from .constraints import combinations_for, supported_tuples
from .replay import snapshot

CATALOGUE = [
    ('Unique-combination run', 1), ('Min/max bounds', 2),
    ('Combination-set pruning', 3), ('Run intersection', 4),
    ('Naked pairs/triples', 5), ('Hidden single', 6),
    ('Cross-run combination elimination', 7)]


def certificate(name, rank, runs, domains, changes):
    """Capture complete antecedent domains and clue scopes, not just an explanatory label."""
    scope = set().union(*(set(run.cells) for run in runs))
    return {'technique': name, 'rank': rank, 'runs': [run.id for run in runs],
            'cells': list(changes), 'premises': {'domains': {k: sorted(domains[k]) for k in sorted(scope)},
            'constraints': [{'id': r.id, 'cells': list(r.cells), 'target': r.target} for r in runs]},
            'conclusion': {k: sorted(v) for k, v in changes.items()}}


def applications(board, domains, check=lambda: None, first=False):
    """Enumerate sound deductions ordered by technique rank; optionally stop at the easiest."""
    output = []
    for name, rank in CATALOGUE:
        for run in board.runs:
            check()
            changes, premises_runs = {}, [run]
            combos = combinations_for(len(run.cells), run.target)
            if rank == 1 and len(combos) == 1:
                allowed = set(combos[0])
                changes = {k: domains[k] & allowed for k in run.cells if domains[k] - allowed}
            elif rank == 2:
                for k in run.cells:
                    others = [domains[j] for j in run.cells if j != k]
                    if any(not d for d in others):
                        continue
                    allowed = {v for v in domains[k] if v + sum(min(d) for d in others) <= run.target <= v + sum(max(d) for d in others)}
                    if allowed != domains[k]:
                        changes[k] = allowed
            elif rank == 3:
                feasible = [c for c in combos if all(domains[k] & set(c) for k in run.cells) and all(any(v in domains[k] for k in run.cells) for v in c)]
                allowed = set().union(*(set(c) for c in feasible)) if feasible else set()
                changes = {k: domains[k] & allowed for k in run.cells if domains[k] - allowed}
            elif rank == 4:
                for k in run.cells:
                    crossing = next(r for r in board.cell_runs[k] if r.id != run.id)
                    other_combos = combinations_for(len(crossing.cells), crossing.target)
                    allowed = set().union(*(set(c) for c in combos)) & set().union(*(set(c) for c in other_combos))
                    if domains[k] - allowed:
                        changes[k] = domains[k] & allowed
                        if crossing not in premises_runs:
                            premises_runs.append(crossing)
            elif rank == 5:
                for n in (2, 3):
                    for group in combinations(run.cells, n):
                        union = set().union(*(domains[k] for k in group))
                        if len(union) == n and all(domains[k] for k in group):
                            for k in set(run.cells) - set(group):
                                if domains[k] & union:
                                    changes[k] = changes.get(k, domains[k]) - union
            elif rank == 6:
                # A digit is mandatory only if every feasible digit SET contains it.
                feasible = [set(c) for c in combos if all(domains[k] & set(c) for k in run.cells)]
                mandatory = set.intersection(*feasible) if feasible else set()
                for v in mandatory:
                    locations = [k for k in run.cells if v in domains[k]]
                    if len(locations) == 1 and len(domains[locations[0]]) > 1:
                        k = locations[0]
                        changes[k] = changes.get(k, domains[k]) & {v}
            elif rank == 7:
                premises_runs = [run] + [r for r in board.runs if r.id != run.id and set(r.cells) & set(run.cells)]
                # Enforce exact run support, then support across each crossing run.
                local = {k: set(v) for k, v in domains.items()}
                for scope in premises_runs[1:] + [run]:
                    tuples = supported_tuples(scope, local, check)
                    for i, k in enumerate(scope.cells):
                        local[k] &= {t[i] for t in tuples}
                changes = {k: local[k] for k in run.cells if local[k] != domains[k]}
            if changes:
                output.append(certificate(name, rank, premises_runs, domains, changes))
                if first:
                    return output
        if output and first:
            return output
    return output
