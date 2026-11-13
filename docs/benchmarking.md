# Recorded methodology and reproducible reanalysis

The shipped `generation.csv`, corpus and summary are historical measurements of the original pre-recovery generator. Today's generator includes a reserved constructive recovery phase. The first published commit already contains that fix, so the original pre-fix executable revision is not included. Reanalyze the frozen CSV/JSON records from the repository root:

```powershell
.\.venv\Scripts\python -m scripts.report
.\.venv\Scripts\python -m pytest --cov=backend/app/core --cov=backend/app/solver --cov=backend/app/generator --cov-report=term-missing
```

The final audit recomputed all four generation rates/mean times, the Spearman correlation and both threshold sets from their raw records; they matched the summaries. `results/final-audit.json` records these checks, source-file hashes and current-policy generation observations. These checks reproduce the statistical analysis, not the original random-generation execution or wall-clock observations.

For a **new current-policy experiment**, use a separate checkout or preserve the existing `results/` and `data/` first. These scripts write to those directories and can replace the frozen presentation evidence:

```powershell
.\.venv\Scripts\python -m scripts.experiments --count 200 --sizes 5 6 --budget 0.6
.\.venv\Scripts\python -m scripts.build_library
.\.venv\Scripts\python -m scripts.report
.\.venv\Scripts\python -m scripts.oracle_corpus
```

The current runner records the requested mode, not each response's `method` field. Thus a new run labeled `repair` includes repair-policy recovery and cannot isolate pure ambiguity repair from the recovery contribution. Record that policy when presenting a new study; the current runner does not produce a method-stratified research comparison.

The paired experiment has 200 seeds for each of two sizes and two modes: 800 generation runs. Repair and random modes share a seed, 20 outer attempts and a 0.6-second cap. Their random streams diverge after the first method-specific action; this is a paired-seed comparison, not a claim that all later layouts are identical. Repair gets up to 20 targeted changes per outer attempt; random regeneration gets one fill per attempt. Both budgets are documented, so the result is specific to these settings.

Calibration supplements the paired successes with fresh seeds until there are 200 accepted unique puzzles per size. Failed paired attempts remain in `generation.csv`. The 400 accepted puzzles and metadata are in `generated_corpus.json`. Calibration quantiles are in `calibration.json`; they are relative to size and generator distribution, not population-wide human difficulty norms. Spearman correlation uses human scores and independently run fixed-order baseline node counts; censored runs are excluded and counted. Correlation does not establish causation, and bigger boards can confound the pooled relationship.

Arena measurements call `solve(trace=False)` with identical node/time limits and no replay or proof-checking overhead. Nodes count recursive search states, assignments count guesses plus forced singleton reductions and backtracks count parent restorations. For non-human strategies, checks count high-level run predicate/support calls, not primitive arithmetic. Human checks count accepted certificate premise scopes and omit failed catalogue-search evaluations; they are not a total-work count comparable to other configurations. Human steps and guess depth are shown alongside common search metrics. Timing starts after `Board` parsing and excludes JSON serialization, UI/network latency and proof verification. Solver Lab timings include event recording/emission overhead; use Arena for algorithm timing comparisons. Single-run timing is noisy; rerun before making close speed claims.

`benchmark.csv` records seven strategies across ten library puzzles (70 rows). `benchmark.json` adds a measured analysis string. `difficulty-effort.png` and `repair-vs-random.png` are generated from recorded observations. `scripts/report.py` adds ablation and difficulty-group plots and tables. Raw data is retained for independent analysis.

The OR-tools CP-SAT cross-check exists only in `backend/tests/test_oracle.py`. For 300 recorded seeded unique 5×5 puzzles, it directly encodes digit domains, AllDifferent and equality sums. All seven custom configurations must count exactly one solution and agree with the oracle; human traces must also pass the independent verifier. This validates a sampled distribution, not every possible Kakuro board.
