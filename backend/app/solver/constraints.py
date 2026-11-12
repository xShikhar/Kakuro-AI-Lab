"""Cached digit sets and exact domain-compatible run tuples for generalized arc consistency."""
from functools import lru_cache
from itertools import combinations


@lru_cache(maxsize=None)
def combinations_for(length: int, target: int) -> tuple:
    """Return distinct digit sets of the specified size and sum, shared across solves."""
    return tuple(c for c in combinations(range(1, 10), length) if sum(c) == target)


def supported_tuples(run, domains, check=lambda: None):
    """Enumerate legal assignments with distinctness and sum bounds; honor search deadlines."""
    keys = sorted(run.cells, key=lambda k: len(domains[k]))
    found, assignment = [], {}

    def visit(index, used, total):
        """Build one injective tuple, pruning impossible remaining sums before recursion."""
        check()
        if index == len(keys):
            if total == run.target:
                found.append(tuple(assignment[k] for k in run.cells))
            return
        remaining = keys[index:]
        available = [domains[k] - used for k in remaining]
        if any(not d for d in available) or total + sum(min(d) for d in available) > run.target or total + sum(max(d) for d in available) < run.target:
            return
        key = keys[index]
        for value in sorted(domains[key] - used):
            assignment[key] = value
            visit(index + 1, used | {value}, total + value)

    visit(0, set(), 0)
    return found


def consistent(run, entries):
    """Cheap partial sum/duplicate test for baseline search; it does not propagate domains."""
    digits = [entries[k] for k in run.cells if k in entries]
    if len(digits) != len(set(digits)):
        return False
    left = len(run.cells) - len(digits)
    available = sorted(set(range(1, 10)) - set(digits))
    return sum(digits) + sum(available[:left]) <= run.target <= sum(digits) + sum(available[-left:] if left else [])
