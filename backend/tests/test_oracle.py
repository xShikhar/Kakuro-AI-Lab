"""300 independent CP-SAT cross-checks; OR-tools is imported exclusively in this test module."""
import json
from pathlib import Path
import pytest
from ortools.sat.python import cp_model
from backend.app.core.model import Board
from backend.app.generator.generate import generate
from backend.app.solver.engine import STRATEGIES, solve
from backend.app.solver.verifier import verify_trace


def oracle(puzzle):
    """Express the mathematical rules directly in an independent constraint system."""
    board = Board(puzzle)
    model = cp_model.CpModel()
    variables = {k: model.new_int_var(1, 9, k) for k in board.variables}
    for run in board.runs:
        model.add_all_different([variables[k] for k in run.cells])
        model.add(sum(variables[k] for k in run.cells) == run.target)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = 3
    assert solver.solve(model) in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    return {k: solver.value(v) for k, v in variables.items()}


@pytest.mark.parametrize('seed', range(300))
def test_300_puzzle_strategy_and_independent_oracle_agreement(seed):
    """Catch any solver or generator that returns a digit assignment violating the independent oracle."""
    # Reuse recorded seeds when available; otherwise regenerate deterministic small unique puzzles.
    path = Path(__file__).resolve().parents[2] / 'results' / 'oracle_corpus.json'
    if path.exists():
        generated = json.loads(path.read_text())[seed]
    else:
        generated = generate(size=5, seed=seed + 9000, timeout=5)
    assert generated['unique'], f'No unique puzzle generated for seed {seed}'
    puzzle = generated['puzzle']
    expected = oracle(puzzle)
    for strategy in STRATEGIES:
        result = solve(puzzle, strategy=strategy, timeout=10, solution_limit=2, trace=strategy=='human')
        assert result['status'] == 'unique', (seed, strategy, result['status'])
        assert result['solution'] == expected, (seed, strategy)
        if strategy == 'human':
            report = verify_trace(puzzle, result['trace'])
            assert report['verified'] == report['total'], (seed, report)
