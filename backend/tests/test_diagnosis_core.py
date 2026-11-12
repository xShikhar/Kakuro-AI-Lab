"""Minimum clue-core tests use a hand-checkable wrong digit and fixed player assumptions."""
from backend.tests.test_core import puzzle
from backend.app.solver.diagnose import minimum_clue_core
from backend.app.solver.constraints import supported_tuples
from backend.app.core.model import Board


def test_minimum_clue_core_is_actually_unsatisfiable_and_minimum():
    """No zero-clue CSP can contradict digit 9; a single sum-3 clue already does."""
    core=minimum_clue_core(puzzle(),{'1,1':9},timeout=2)
    assert core['minimum']
    assert len(core['runs'])==1
    assert core['runs'][0] in ('across:1,0','down:0,1')


def test_two_step_chain_and_two_clue_core_have_no_shorter_refutation():
    """Every initial run has support, so a two-step catalogue refutation cannot be shortened to one."""
    from backend.app.solver.diagnose import diagnose
    b=Board(puzzle())
    domains={k:{1} if k=='1,2' else set(range(1,10)) for k in b.variables}
    assert all(supported_tuples(r,domains) for r in b.runs)
    result=diagnose(puzzle(),{'1,2':1})
    assert result['shortest'] and len(result['steps'])==2
    assert result['core']['minimum'] and len(result['core']['runs'])==2
