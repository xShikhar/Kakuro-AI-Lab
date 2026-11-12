"""Fair, trace-free strategy comparisons and data-derived ablation commentary."""
from .solver.engine import solve, STRATEGIES


def benchmark(puzzles, strategies=None, node_limit=100000, timeout=5):
    """Run every requested solver on identical inputs and caps; report censored runs explicitly."""
    results = []
    for item in puzzles:
        for strategy in strategies or STRATEGIES:
            result = solve(item.get('puzzle', item), strategy=strategy, node_limit=node_limit,
                           timeout=timeout, trace=False)
            # Human technique statistics are counted by the engine even with trace disabled.
            results.append(dict(puzzle_id=item.get('id', 'custom'), difficulty=item.get('difficulty', {}).get('label', 'Custom'),
                                strategy=strategy, status=result['status'], **result['metrics']))
    complete = [r for r in results if r['status'] in ('solved', 'unique', 'multiple')]
    totals = {s: sum(r['nodes'] for r in complete if r['strategy'] == s) for s in strategies or STRATEGIES}
    winner = min(complete, key=lambda r: r['wall_time_ms'])['strategy'] if len(puzzles) == 1 and complete else None
    return dict(results=results, fastest=winner,
                analysis='Compare paired successful runs; limit rows are censored and cannot establish a winner. '
                + (f"Total successful-run nodes by configuration: {totals}." if complete else 'No solver completed within the selected caps.'))
