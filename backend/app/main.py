"""Validated local REST API and bounded NDJSON worker streaming; no external AI services."""
import asyncio
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from threading import Event
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field, StrictInt
from .core.model import Board
from .solver.engine import solve, STRATEGIES
from .solver.verifier import verify_trace
from .solver.diagnose import hint, diagnose
from .generator.generate import generate
from .arena import benchmark

ROOT = Path(__file__).resolve().parents[2]
app = FastAPI(title='Kakuro AI Lab', version='1.0.0')
workers = ThreadPoolExecutor(max_workers=2, thread_name_prefix='kakuro')


class PuzzleRequest(BaseModel):
    """A structurally validated JSON puzzle and optional player entries."""
    puzzle: dict
    entries: dict[str, StrictInt] = Field(default_factory=dict)


class SolveRequest(PuzzleRequest):
    """Consistent bounded-search settings shared by REST and streaming."""
    strategy: Literal['baseline','mrv','degree','lcv','propagation','full','human'] = 'full'
    node_limit: int = Field(default=100000, ge=1, le=1000000)
    timeout: float = Field(default=10, gt=0, le=30)
    solution_limit: int = Field(default=1, ge=1, le=10)


class HintRequest(PuzzleRequest):
    """Three escalating levels: scope, technique and candidate conclusion."""
    level: int = Field(default=1, ge=1, le=3)


class GenerateRequest(BaseModel):
    """Seeded generator controls with explicit attempt and time caps."""
    size: int = Field(default=5, ge=5, le=12)
    seed: int = 42
    target: str | None = None
    attempts: int = Field(default=20, ge=1, le=100)
    timeout: float = Field(default=15, gt=0, le=30)


class ArenaRequest(BaseModel):
    """An explicit puzzle set or built-in IDs; all configurations share the same caps."""
    puzzles: list[dict] = Field(default_factory=list, max_length=10)
    ids: list[str] = Field(default_factory=list, max_length=20)
    strategies: list[str] = Field(default_factory=lambda: list(STRATEGIES), max_length=7)
    timeout: float = Field(default=3, gt=0, le=10)
    node_limit: int = Field(default=100000, ge=1, le=1000000)


def validate(request):
    """Normalize domain errors into readable API validation responses before starting work."""
    try:
        board = Board(request.puzzle)
        board.validate_entries(request.entries)
        return board
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc


def load_puzzles():
    """Read verified built-ins without returning hidden witness solutions to the browser."""
    path = ROOT / 'data' / 'puzzles.json'
    return json.loads(path.read_text()) if path.exists() else []


@app.get('/api/health')
def health():
    """Expose local service readiness and available strategies."""
    return {'ok': True, 'strategies': STRATEGIES}


@app.get('/api/puzzles')
def puzzles():
    """Return the library with measured metadata, keeping solutions server-side."""
    return [{k: v for k, v in p.items() if k != 'solution'} for p in load_puzzles()]


@app.post('/api/solve')
def solve_api(request: SolveRequest):
    """Run in FastAPI's thread pool; independently check human certificates after solving."""
    validate(request)
    result = solve(request.puzzle, strategy=request.strategy, givens=request.entries,
                   node_limit=request.node_limit, timeout=request.timeout, solution_limit=request.solution_limit)
    if request.strategy == 'human':
        result['verification'] = verify_trace(request.puzzle, result['trace'],request.entries)
    return result


@app.post('/api/solve/stream')
def stream_api(request: SolveRequest):
    """Send real events as NDJSON from a bounded queue; disconnect cancels the worker."""
    validate(request)
    queue, stopped = Queue(maxsize=512), Event()

    def put(value):
        """Apply backpressure without retaining an unbounded trace or blocking cancellation."""
        from queue import Full
        while not stopped.is_set():
            try:
                queue.put(value, timeout=.1)
                return
            except Full:
                continue

    def work():
        """Compute on a worker so long runs cannot block the API event loop."""
        try:
            result = solve(request.puzzle, strategy=request.strategy, givens=request.entries,
                           node_limit=request.node_limit, timeout=request.timeout, solution_limit=request.solution_limit,
                           trace=request.strategy=='human', emit=lambda event: put({'kind':'event', 'event':event}), cancelled=stopped.is_set)
            if request.strategy == 'human' and not stopped.is_set():
                result['verification'] = verify_trace(request.puzzle, result['trace'],request.entries)
            result['trace'] = []  # Already streamed; do not transmit the potentially large trace twice.
            put({'kind':'result', 'result': result})
        except Exception as exc:
            put({'kind':'error', 'message': str(exc)})
        finally:
            put(None)

    async def lines():
        """Drain the worker incrementally and propagate client disconnects to its budget check."""
        workers.submit(work)
        try:
            while True:
                try:
                    item = queue.get_nowait()
                except Empty:
                    await asyncio.sleep(.01)
                    continue
                if item is None:
                    break
                yield json.dumps(item) + '\n'
        finally:
            stopped.set()

    return StreamingResponse(lines(), media_type='application/x-ndjson', headers={'X-Accel-Buffering':'no'})


@app.post('/api/check')
def check_api(request: PuzzleRequest):
    """Separate explicit rule violations from locally legal but globally incompatible entries."""
    board = validate(request)
    issues = board.violations(request.entries)
    if issues:
        return {'classification':'rule_violation', 'violations':issues, 'complete':False}
    result = solve(request.puzzle, givens=request.entries, timeout=3, trace=False)
    return {'classification':'solution_incompatible' if result['status'] == 'unsatisfiable' else 'unknown' if result['status'] == 'limit' else 'compatible',
            'violations':[], 'complete':board.valid_solution(request.entries)}


@app.post('/api/hint')
def hint_api(request: HintRequest):
    """Offer a real easiest-ranked deduction, with no hidden solution exposed by nudges."""
    validate(request)
    return hint(request.puzzle, request.entries, request.level)


@app.post('/api/diagnose')
def diagnose_api(request: PuzzleRequest):
    """Return a bounded BFS refutation, explicitly identifying unproved minimality claims."""
    validate(request)
    return diagnose(request.puzzle, request.entries)


@app.post('/api/generate')
def generate_api(request: GenerateRequest):
    """Generate and uniqueness-check a puzzle before it can be loaded into Play."""
    try:
        return generate(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post('/api/arena')
def arena_api(request: ArenaRequest):
    """Compare selected built-ins or custom puzzles with visualization disabled during timing."""
    if any(s not in STRATEGIES for s in request.strategies) or not request.strategies:
        raise HTTPException(422, 'Choose valid strategies.')
    selected = request.puzzles + [p for p in load_puzzles() if p['id'] in request.ids]
    if not selected:
        raise HTTPException(422, 'Select at least one puzzle.')
    try:
        return benchmark(selected, request.strategies, request.node_limit, request.timeout)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get('/api/experiments')
def experiments_api():
    """Serve only recorded experiment outputs, never generated sample metrics."""
    path = ROOT / 'results' / 'summary.json'
    return json.loads(path.read_text()) if path.exists() else {'message':'Run scripts/experiments.py to produce measured results.'}


@app.get('/api/results/{filename}')
def result_file(filename: str):
    """Expose a restricted list of generated CSV, JSON and chart artifacts."""
    path = ROOT / 'results' / filename
    if Path(filename).name != filename or path.suffix not in ('.csv','.json','.png') or not path.is_file():
        raise HTTPException(404, 'Result artifact not found.')
    return FileResponse(path)
