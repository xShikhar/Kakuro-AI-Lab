"""API boundary tests exercise real engine responses and streamed failures without external services."""
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.tests.test_core import puzzle

client = TestClient(app)


def test_solve_and_validation():
    """Reject malformed payloads and return real certified solver results."""
    assert client.post('/api/solve', json={'puzzle': {}}).status_code == 422
    result = client.post('/api/solve', json={'puzzle': puzzle(), 'strategy': 'human'}).json()
    assert result['solution']['1,1'] == 1
    assert result['verification']['verified'] == result['verification']['total'] > 0


def test_stream_and_check():
    """Stream an initial domain event and completion; distinguish local from global mistakes."""
    response = client.post('/api/solve/stream', json={'puzzle': puzzle(), 'strategy': 'full'})
    assert 'domain_init' in response.text and '"kind": "result"' in response.text
    checked = client.post('/api/check', json={'puzzle': puzzle(), 'entries': {'1,1': 2}}).json()
    assert checked['classification'] == 'solution_incompatible'
    assert not checked['violations']
    assert client.post('/api/hint', json={'puzzle':puzzle(), 'level':1}).status_code == 200


def test_bool_digits_and_trace_integrity():
    """API coercion cannot turn a boolean into a digit, and human results attest full trace integrity."""
    assert client.post('/api/check',json={'puzzle':puzzle(),'entries':{'1,1':True}}).status_code==422
    result=client.post('/api/solve',json={'puzzle':puzzle(),'strategy':'human','entries':{'1,1':1}}).json()
    assert result['verification']['valid']
