"""Library acceptance: all levels are real and the demonstration actually propagates and backtracks."""
import json
from pathlib import Path
from backend.app.core.model import Board
from backend.app.solver.engine import solve
from backend.app.solver.verifier import verify_trace


def test_verified_library_and_real_demonstration():
    """Prevent a deduction-only puzzle being selected for a demo promising heuristic decisions and backtracking."""
    library=json.loads((Path(__file__).resolve().parents[2]/'data/puzzles.json').read_text())
    assert len(library)>=10
    assert {p['difficulty']['label'] for p in library}=={'Beginner','Easy','Medium','Hard','Expert'}
    assert any(p['difficulty']['guess_levels']>0 for p in library)
    for item in library:
        assert Board(item['puzzle']).valid_solution(item['solution'])
        assert solve(item['puzzle'],solution_limit=2,trace=False)['status']=='unique'
    demo=next(p for p in library if p.get('demo'))
    events={e['type'] for e in solve(demo['puzzle'],strategy='full')['trace']}
    assert {'domain_init','eliminate_candidate','heuristic_select','backtrack','solved'}<=events
    result=solve(demo['puzzle'],strategy='human',solution_limit=2)
    assert verify_trace(demo['puzzle'],result['trace'])['valid']
