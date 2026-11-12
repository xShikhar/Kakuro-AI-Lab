"""Parse Kakuro JSON into a validated run graph, independent of UI and web frameworks."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Run:
    """An ordered AllDifferent+Sum scope, identified by its direction and clue cell."""
    id: str
    cells: tuple[str, ...]
    target: int
    clue: str
    direction: str


class Board:
    """Validate dimensions, clue placement, connectivity and exactly two runs per variable."""

    def __init__(self, puzzle: dict):
        """Build immutable run metadata from JSON; reject malformed or impossible clues."""
        self.puzzle = puzzle
        self.rows, self.cols = puzzle.get('rows'), puzzle.get('cols')
        self.cells = puzzle.get('cells', [])
        if type(self.rows) is not int or type(self.cols) is not int or not 3 <= self.rows <= 12 or not 3 <= self.cols <= 12:
            raise ValueError('Board dimensions must be integers between 3 and 12.')
        if len(self.cells) != self.rows or any(not isinstance(row, list) or len(row) != self.cols for row in self.cells):
            raise ValueError('Cell matrix does not match dimensions.')
        self.variables = []
        self.runs = []
        self.cell_runs = {}
        for r, row in enumerate(self.cells):
            for c, cell in enumerate(row):
                if not isinstance(cell, dict) or cell.get('type') not in ('white', 'black'):
                    raise ValueError('Each cell must be white or black.')
                key = f'{r},{c}'
                if cell['type'] == 'white':
                    if cell.get('across') is not None or cell.get('down') is not None:
                        raise ValueError('White cells cannot carry clues.')
                    self.variables.append(key)
                    self.cell_runs[key] = []
        if not self.variables:
            raise ValueError('A puzzle must contain white cells.')
        for r, row in enumerate(self.cells):
            for c, cell in enumerate(row):
                if cell['type'] != 'black':
                    continue
                for direction, dr, dc in [('across', 0, 1), ('down', 1, 0)]:
                    target = cell.get(direction)
                    if target is None:
                        continue
                    scope, rr, cc = [], r + dr, c + dc
                    while rr < self.rows and cc < self.cols and self.cells[rr][cc]['type'] == 'white':
                        scope.append(f'{rr},{cc}')
                        rr, cc = rr + dr, cc + dc
                    n = len(scope)
                    if not 2 <= n <= 9 or type(target) is not int or not n * (n + 1) // 2 <= target <= n * (19 - n) // 2:
                        raise ValueError(f'Invalid {direction} run at {r},{c}: length 2–9 and feasible integer sum required.')
                    run = Run(f'{direction}:{r},{c}', tuple(scope), target, f'{r},{c}', direction)
                    self.runs.append(run)
                    for key in scope:
                        self.cell_runs[key].append(run)
        if any(len(rs) != 2 or {r.direction for r in rs} != {'across', 'down'} for rs in self.cell_runs.values()):
            raise ValueError('Each white cell must belong to exactly one across and one down clue.')
        self.neighbors = {k: set().union(*(set(run.cells) for run in rs)) - {k} for k, rs in self.cell_runs.items()}
        reached, pending = set(), [self.variables[0]]
        while pending:
            key = pending.pop()
            if key not in reached:
                reached.add(key)
                pending.extend(self.neighbors[key] - reached)
        if len(reached) != len(self.variables):
            raise ValueError('White cells must form a connected constraint graph.')

    def validate_entries(self, entries: dict):
        """Reject unknown coordinates and non-integer digits before any search begins."""
        if not isinstance(entries, dict) or any(k not in self.cell_runs or type(v) is not int or not 1 <= v <= 9 for k, v in entries.items()):
            raise ValueError('Entries must map white-cell coordinates to integer digits 1–9.')

    def violations(self, entries: dict) -> list[dict]:
        """Return local rule violations; absence does not establish global compatibility."""
        self.validate_entries(entries)
        issues = []
        for run in self.runs:
            digits = [entries[k] for k in run.cells if k in entries]
            if len(digits) != len(set(digits)):
                issues.append({'run': run.id, 'cells': list(run.cells), 'reason': 'Repeated digit in a run.'})
            if sum(digits) > run.target or len(digits) == len(run.cells) and sum(digits) != run.target:
                issues.append({'run': run.id, 'cells': list(run.cells), 'reason': f'Run must sum to {run.target}.'})
        return issues

    def valid_solution(self, entries: dict) -> bool:
        """Validate every digit, run sum and AllDifferent constraint of a complete solution."""
        try:
            return set(entries) == set(self.variables) and not self.violations(entries)
        except ValueError:
            return False
