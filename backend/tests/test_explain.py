"""Independent certificate and replay tests catch unsound eliminations and stale branch state."""
import copy
from backend.tests.test_core import puzzle
from backend.app.solver.engine import solve
from backend.app.solver.verifier import verify_trace, verify_proof
from backend.app.solver.replay import replay
from backend.app.solver.diagnose import diagnose, hint


def test_proofs_reject_corruption():
    """Changing a supported candidate to an unsupported conclusion must fail verification."""
    result = solve(puzzle(), strategy='human')
    report = verify_trace(puzzle(), result['trace'])
    assert report['total'] > 0 and report['verified'] == report['total']
    proof = copy.deepcopy(next(e['justification'] for e in result['trace'] if e['type'] == 'technique_applied'))
    cell = next(iter(proof['conclusion']))
    proof['conclusion'][cell] = []
    assert not verify_proof(proof)


def test_replay_and_hint():
    """Replay ends at the actual solution and a nudge never leaks its revealed digit."""
    result = solve(puzzle(), strategy='human')
    state = replay(result['trace'], len(result['trace']) - 1)
    assert {k: v[0] for k, v in state.items()} == result['solution']
    assert 'value' not in hint(puzzle(), {}, 1)
    assert hint(puzzle(), {}, 3)['changes']


def test_third_hint_reveals_a_verified_digit():
    """The last escalation returns a real cell digit, rather than only another candidate list."""
    answer=hint(puzzle(),{},3)
    assert answer['value'] in (1,2,3,4)
    assert solve(puzzle())['solution'][answer['cell']]==answer['value']


def test_shortest_contradiction():
    """A wrong digit conflicting with a two-cell sum has a one-edge refutation."""
    result = diagnose(puzzle(), {'1,1': 9}, max_states=1000)
    assert result['contradiction'] and result['shortest']
    assert len(result['steps']) == 1


def test_verifier_rejects_uncertified_mutations_and_snapshots():
    """A valid proof prefix cannot authenticate a forged forced digit, initial state or solved snapshot."""
    result=solve(puzzle(),strategy='human')
    bad=copy.deepcopy(result['trace'])
    bad.append({'step':len(bad),'type':'assign','after':{'1,1':[9]},'forced':True})
    report=verify_trace(puzzle(),bad)
    assert report['failures'] and not report['valid']
    bad=copy.deepcopy(result['trace']);bad[0]['snapshot']['1,1']=[9]
    assert not verify_trace(puzzle(),bad)['valid']
    bad=copy.deepcopy(result['trace']);bad[-1]['snapshot']['1,1']=[9]
    assert not verify_trace(puzzle(),bad)['valid']
