"""Boundary and proof-binding regressions exercise failure paths rather than mirror the implementation."""
import copy
import pytest
from backend.tests.test_core import puzzle
from backend.app.core.model import Board
from backend.app.solver.engine import solve
from backend.app.solver.verifier import verify_trace, verify_proof
from backend.app.solver.replay import explain, replay
from backend.app.solver.diagnose import diagnose, hint
from backend.app.generator.generate import generate


@pytest.mark.parametrize('change', ['dimensions','matrix','cell','white_clue','target','empty'])
def test_malformed_boards(change):
    """Invalid representations fail before any search or accidental indexing occurs."""
    p=puzzle()
    if change=='dimensions':p['rows']=True
    if change=='matrix':p['cells'][0].pop()
    if change=='cell':p['cells'][1][1]={'type':'red'}
    if change=='white_clue':p['cells'][1][1]['across']=3
    if change=='target':p['cells'][1][0]['across']=2
    if change=='empty':p['cells']=[[{'type':'black'}]*3 for _ in range(3)]
    with pytest.raises(ValueError):Board(p)


def test_reject_unknown_digit_and_configuration():
    """Invalid coordinates, bool digits and unknown strategies must not be silently coerced."""
    b=Board(puzzle())
    assert not b.valid_solution({'1,1':True})
    for entries in ({'0,0':3},{'1,1':10},{'1,1':True}):
        with pytest.raises(ValueError):solve(puzzle(),givens=entries)
    with pytest.raises(ValueError):solve(puzzle(),strategy='fake')
    with pytest.raises(ValueError):solve(puzzle(),timeout=0)
    assert solve(puzzle(),cancelled=lambda:True)['status']=='limit'


def test_proof_binding_and_explanation():
    """A valid local proof with a fabricated clue must be rejected by the full trace checker."""
    trace=solve(puzzle(),strategy='human')['trace']
    bad=copy.deepcopy(trace)
    event=next(e for e in bad if e['type']=='technique_applied')
    event['justification']['premises']['constraints'][0]['target']=44
    assert verify_trace(puzzle(),bad)['failures']
    assert not verify_proof({})
    assert 'scopes=' in explain(trace[0],'Research')
    assert explain(trace[0],'Beginner')
    assert replay(trace,-1)=={}


def test_inconclusive_diagnosis_and_generator_caps():
    """Budget exhaustion is inconclusive and unsupported generation controls are rejected."""
    assert not diagnose(puzzle(),{},max_states=1)['shortest']
    assert not diagnose(puzzle(),{},timeout=1e-10)['contradiction']
    assert generate(size=5,timeout=1e-10)['puzzle'] is None
    for kwargs in ({'size':4},{'target':'Impossible'},{'mode':'fake'}):
        with pytest.raises(ValueError):generate(**kwargs)
    complete=solve(puzzle())['solution']
    assert 'changes' not in hint(puzzle(),complete,3)
