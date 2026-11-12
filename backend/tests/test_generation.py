"""Seeded generator tests catch disconnected layouts, stale clues and false uniqueness."""
from backend.app.core.model import Board
from backend.app.generator.generate import generate, from_fill, repair
from backend.app.generator.difficulty import rate
from backend.app.solver.engine import solve
import pytest


def test_generated_unique_and_deterministic():
    """Seeded generation returns a valid witness and counts a second solution before claiming unique."""
    a = generate(size=5, seed=18, timeout=15)
    assert a['puzzle'] and a['unique']
    assert Board(a['puzzle']).valid_solution(a['solution'])
    assert solve(a['puzzle'], solution_limit=2)['status'] == 'unique'
    b = generate(size=5, seed=18, timeout=15)
    assert a['puzzle'] == b['puzzle']


def test_ambiguity_repair_changes_real_clues():
    """Disagreement-guided repair must alter clues and preserve a legal witness."""
    fill = {'1,1': 1, '1,2': 4, '2,1': 4, '2,2': 1}
    p = from_fill(3, 3, fill)
    result = solve(p, solution_limit=2)
    assert result['status'] == 'multiple'
    fixed, witness, log = repair(p, fill, result['solutions'], __import__('random').Random(4))
    assert fixed != p and log['ambiguous_cells']
    assert Board(fixed).valid_solution(witness)


def test_difficulty_comes_from_trace():
    """Actual certified technique ranks and guess levels determine the published score."""
    assert rate({'trace': [{'type':'technique_applied', 'justification':{'rank':2}}], 'metrics': {'guess_levels':1}})['score'] == 12.5


@pytest.mark.parametrize('size', range(5, 13))
def test_every_selectable_size_generates_a_verified_puzzle(size):
    """Larger selectable grids must generate rather than spend the whole budget in dense tuple tables."""
    result=generate(size=size,seed=42,timeout=3)
    assert result['unique'] and result['puzzle'], (size,result.get('message'))
    board=Board(result['puzzle'])
    assert board.rows==board.cols==size
    assert Board(result['puzzle']).valid_solution(result['solution'])
    assert solve(result['puzzle'],solution_limit=2,trace=False,timeout=3)['status']=='unique'
    # New large-board layouts must span the requested grid, rather than pad a small puzzle.
    if size>=7:
        coordinates=[tuple(map(int,key.split(','))) for key in board.variables]
        assert {r for r,c in coordinates}==set(range(1,size))
        assert {c for r,c in coordinates}==set(range(1,size))


@pytest.mark.parametrize('size', (5,8,12))
def test_verified_fallback_when_random_fill_cannot_progress(size, monkeypatch):
    """Failure of random coloring must not prevent a fresh, independently checked constructive attempt."""
    import importlib
    generator=importlib.import_module('backend.app.generator.generate')
    monkeypatch.setattr(generator,'randomized_fill',lambda board,rng:None)
    result=generate(size=size,seed=42,attempts=1,timeout=3)
    assert result['unique'] and result['method']=='constructive'
    assert result['target_matched']
    assert Board(result['puzzle']).valid_solution(result['solution'])
    assert solve(result['puzzle'],solution_limit=2,trace=False)['status']=='unique'


def test_fallback_never_claims_uniqueness_without_counting(monkeypatch):
    """A solver limit must remain a failure even when the constructive witness is legal."""
    import importlib
    generator=importlib.import_module('backend.app.generator.generate')
    monkeypatch.setattr(generator,'randomized_fill',lambda board,rng:None)
    monkeypatch.setattr(generator,'solve',lambda *args,**kwargs:{'status':'limit'})
    result=generate(size=12,seed=42,attempts=1,timeout=1)
    assert not result['unique'] and result['puzzle'] is None


def test_slow_rating_cannot_consume_recovery_reserve(monkeypatch):
    """A unique random board whose human rating times out must leave recovery time available."""
    import importlib,random
    generator=importlib.import_module('backend.app.generator.generate')
    witness=generator.transformed_ribbon(5,random.Random(1),extreme=True)
    board=Board(from_fill(5,5,witness))
    clock=[0.0]
    monkeypatch.setattr(generator,'perf_counter',lambda:clock[0])
    monkeypatch.setattr(generator,'layout',lambda size,rng:board)
    monkeypatch.setattr(generator,'randomized_fill',lambda board,rng:dict(witness))
    actual_solve=generator.solve
    rating_calls=[0]

    def slow_first_rating(*args,**kwargs):
        """Exhaust only the first rating's allocated time; all verification still uses the real solver."""
        if kwargs.get('strategy')=='human':
            rating_calls[0]+=1
            if rating_calls[0]==1:
                clock[0]+=kwargs['timeout']
                return {'solution':None,'status':'limit'}
        return actual_solve(*args,**kwargs)

    monkeypatch.setattr(generator,'solve',slow_first_rating)
    result=generate(size=5,seed=42,attempts=1,timeout=3)
    assert result['unique'] and result['method']=='constructive'
    assert result['wall_time_ms']<=3000
