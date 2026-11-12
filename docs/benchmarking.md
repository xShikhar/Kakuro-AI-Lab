# Reproducing the measurements

From the repository root, install `requirements-dev.txt`, then run:

```powershell
.\.venv\Scripts\python -m scripts.experiments --count 200 --sizes 5 6 --budget 0.6
.\.venv\Scripts\python -m scripts.build_library
.\.venv\Scripts\python -m scripts.oracle_corpus
.\.venv\Scripts\python -m pytest --cov=backend/app/core --cov=backend/app/solver --cov=backend/app/generator --cov-report=term-missing
```

The paired experiment has 200 seeds for each of two sizes and two modes: 800 generation runs. Repair and random modes share a seed, 20 outer attempts and a 0.6-second cap. Their random streams diverge after the first method-specific action; this is a paired-seed comparison, not a claim that all later layouts are identical. Repair gets up to 20 targeted changes per outer attempt; random regeneration gets one fill per attempt. Both budgets are documented, so the result is specific to these settings.

Calibration supplements the paired successes with fresh seeds until there are 200 accepted unique puzzles per size. Failed paired attempts remain in `generation.csv`. The 400 accepted puzzles and metadata are in `generated_corpus.json`. Calibration quantiles are in `calibration.json`; they are relative to size and generator distribution, not population-wide human difficulty norms. Spearman correlation uses human scores and independently run fixed-order baseline node counts; censored runs are excluded and counted. Correlation does not establish causation, and bigger boards can confound the pooled relationship.

Arena measurements call `solve(trace=False)` with identical node/time limits and no replay or proof-checking overhead. Nodes count recursive search states, assignments count guesses plus forced singleton reductions, backtracks count parent restorations, and constraint checks count high-level run evaluations. The latter is not a count of every arithmetic operation inside tuple enumeration. Human steps and guess depth are shown alongside common search metrics. Timing includes model construction only insofar as the engine timer starts after `Board` parsing; it excludes JSON serialization, UI and network latency. Single-run timing is noisy; rerun before making close speed claims.

`benchmark.csv` records seven strategies across ten library puzzles (70 rows). `benchmark.json` adds a measured analysis string. `difficulty-effort.png` and `repair-vs-random.png` are generated from recorded observations. `scripts/report.py` adds ablation and difficulty-group plots and tables. Raw data is retained for independent analysis.

The OR-tools CP-SAT cross-check exists only in `backend/tests/test_oracle.py`. For 300 recorded seeded unique 5×5 puzzles, it directly encodes digit domains, AllDifferent and equality sums. All seven custom configurations must count exactly one solution and agree with the oracle; human traces must also pass the independent verifier. This validates a sampled distribution, not every possible Kakuro board.
