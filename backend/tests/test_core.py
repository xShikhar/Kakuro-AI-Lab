"""Model and solver contract tests: hand-checked fixtures catch invalid CSP reasoning."""
import copy
import pytest
from backend.app.core.model import Board
from backend.app.solver.constraints import combinations_for
from backend.app.solver.engine import solve, STRATEGIES


def puzzle():
    """Return a 2x2 white square with the unique solution [1,2;3,4]."""
    return {"rows": 3, "cols": 3, "cells": [
        [{"type": "black"}, {"type": "black", "down": 4}, {"type": "black", "down": 6}],
        [{"type": "black", "across": 3}, {"type": "white"}, {"type": "white"}],
        [{"type": "black", "across": 7}, {"type": "white"}, {"type": "white"}]]}


def test_model_and_combinations():
    """Reject missing run membership and use distinct-digit sum combinations."""
    b = Board(puzzle())
    assert len(b.runs) == 4
    assert combinations_for(2, 3) == ((1, 2),)
    assert combinations_for(2, 2) == ()
    bad = puzzle()
    bad['cells'][0][1].pop('down')
    with pytest.raises(ValueError):
        Board(bad)
    assert b.violations({'1,1': 2, '1,2': 2})
    assert not b.valid_solution({'1,1': 1, '1,2': 2, '2,1': 3, '2,2': 4}) is False


@pytest.mark.parametrize('strategy', STRATEGIES)
def test_solvers_and_restoration(strategy):
    """All strategy paths must produce the unique hand-derived solution."""
    p = puzzle()
    original = copy.deepcopy(p)
    result = solve(p, strategy=strategy, solution_limit=2)
    assert result['status'] == 'unique'
    assert result['solution'] == {'1,1': 1, '1,2': 2, '2,1': 3, '2,2': 4}
    assert result['metrics']['solutions_found'] == 1
    assert p == original


def test_unsat_multiple_and_limits():
    """Never confuse incomplete enumeration with uniqueness or unsatisfiability."""
    assert solve(puzzle(), givens={'1,1': 9})['status'] == 'unsatisfiable'
    p = puzzle()
    for row in p['cells']:
        for cell in row:
            for key in ('across', 'down'):
                if key in cell:
                    cell[key] = 5
    assert solve(p, solution_limit=2)['status'] == 'multiple'
    assert solve(p, strategy='baseline', node_limit=1)['status'] == 'limit'
    with pytest.raises(ValueError):
        solve(p, givens={'1,1': 0})
