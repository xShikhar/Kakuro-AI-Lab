# Kakuro AI Lab

### Small cells. Deep reasoning.

Kakuro AI Lab is an offline, explainable constraint-satisfaction platform: a playable puzzle room, a live solver laboratory, a fair strategy arena and an ambiguity-guided generator. Its two project contributions are **proof-carrying human-technique deductions with bounded shortest-conflict diagnosis**, and **solution-disagreement-guided clue repair with behavior-based difficulty**. Every decision, elimination, branch and benchmark comes from a custom pure Python engine. React makes that reasoning inspectable and reversible; FastAPI connects the two without external AI services. These are contributions to this academic project, not claims of being the first such ideas in the research literature.

> **Final audit: 13 November 2026, after a PC restart.** The implementation passed 345 backend tests, 13 frontend tests, the production build and the live HTTP smoke test. Core line coverage is 95.23%. All ten library puzzles were rechecked for uniqueness, stored solutions, difficulty scores and human proof validity; the current generator passed 80/80 fresh requests across sizes 5–12. The main research tables are frozen historical measurements, distinguished from this current-code audit below. Calibration for sizes 7–12 and rendered browser/mobile QA remain incomplete. Use the evidence and claim limits in this file when creating the presentation.

**Repository:** [xShikhar/Kakuro-AI-Lab](https://github.com/xShikhar/Kakuro-AI-Lab) · **Audit evidence:** [`results/final-audit.json`](results/final-audit.json) · **Start after a restart:** [section 13](#13-installation-launch-and-troubleshooting) · **Slide outline and demo:** [section 14](#14-presentation-guide)

## 1. Problem statement and motivation

A solved grid hides most of the intelligence needed to obtain it. A normal puzzle game tells a player whether a digit is right; a normal solver often returns only an answer. Neither makes it easy to understand why a candidate disappeared, why a branch failed or why one search heuristic helped.

Kakuro is a useful AI laboratory because small local constraints interact through shared variables. Each white cell must satisfy a horizontal sum and a vertical sum simultaneously, while each run also forbids repeated digits. Local legality does not guarantee global consistency. This provides concrete examples of representation, inference, heuristics, search, contradiction and empirical evaluation without requiring a neural model or paid API.

## 2. Objectives

- Make a complete Kakuro game usable with mouse, keyboard and touch-sized controls.
- Compare fixed-order backtracking, MRV, degree, LCV and propagation on identical inputs.
- Explain real domain changes and reconstruct any recorded search state.
- Carry independently checked local proofs with human deductions and identify wrong-entry conflicts.
- Generate unique puzzles by using two solutions to locate and repair ambiguity.
- Measure difficulty from solving behavior, then evaluate it against actual search effort.
- Provide reproducible source, data, tests and presentation material, with explicit limitations.

## 3. Kakuro rules and a worked example

Fill every white cell with a digit from 1 to 9. Each consecutive white run must add to its clue; digits cannot repeat **within that run**. The same digit can appear in other runs. Clue cells have a diagonal split: the top-right number is the sum across, the bottom-left number is the sum down.

This small complete example is also a hand-checked test fixture:

| | ↓ 4 | ↓ 6 |
|---|---:|---:|
| → 3 | 1 | 2 |
| → 7 | 3 | 4 |

Across 3 in two cells permits only the set `{1,2}`. Down 4 in the left column permits `{1,3}`. Their intersection forces the top-left cell to 1; the other three values follow. A digit 9 in the top-left cell immediately contradicts the across-3 clue. A digit 2 there is locally legal, but cannot extend to the unique full solution. The Play page distinguishes these two mistake classes without automatically exposing the solution.

## 4. Kakuro as a constraint satisfaction problem

For white cells `V`, define a variable `X_rc` for each coordinate `(r,c)` with domain `D_rc ⊆ {1,…,9}`. For every horizontal or vertical run `R` with clue `t_R`:

```text
Σ X_i = t_R               for i ∈ R
AllDifferent(X_i : i ∈ R)
X_i ∈ {1,2,…,9}
```

Each variable belongs to exactly one across and one down run. The model stores ordered scopes, clue targets, clue coordinates, cell-to-run maps and neighbor relationships. The initial domain is all nine digits, except player-supplied assignments. Distinct digit sets are cached by `(run length, target sum)`. A run's domain-compatible ordered tuples provide exact support for candidate pruning.

The JSON boundary is deliberately simple:

```json
{"rows":3,"cols":3,"cells":[
  [{"type":"black"},{"type":"black","down":4},{"type":"black","down":6}],
  [{"type":"black","across":3},{"type":"white"},{"type":"white"}],
  [{"type":"black","across":7},{"type":"white"},{"type":"white"}]
]}
```

Rows/columns must match the matrix. Runs have length 2–9, feasible distinct-digit sums and a preceding clue. Every white cell has both memberships, and the white-cell constraint graph is connected. Complete solutions are validated against all rules before being returned.

## 5. System architecture and data flow

```mermaid
flowchart LR
    Player[React / Play] --> REST[FastAPI REST validation]
    Lab[Solver Lab] --> Stream[NDJSON stream]
    REST --> Engine[Pure Python CSP engine]
    Stream --> Worker[Bounded worker + queue]
    Worker --> Engine
    Engine --> Trace[Immutable domain deltas / snapshots]
    Trace --> Replay[Timeline and replayed board]
    Engine --> Cert[Human proof certificates]
    Cert --> Verifier[Independent enumeration verifier]
    Generator[Layout / fill / clue derivation] --> Engine
    Engine --> Ambiguity[Compare two solutions]
    Ambiguity --> Repair[Targeted clue repair]
    Repair --> Generator
    Player --> Storage[Browser localStorage]
    Experiments[Seeded scripts] --> CSV[CSV / JSON / PNG evidence]
```

| Module | Responsibility |
|---|---|
| `backend/app/core/model.py` | Parse and validate the board; construct the constraint graph |
| `solver/constraints.py` | Cache digit sets; enumerate exact supported tuples |
| `solver/engine.py` | Seven strategies, bounded search, metrics and events |
| `solver/techniques.py` | Ranked human deductions with captured premises |
| `solver/verifier.py` | Independent proof enumeration and trace-state integrity |
| `solver/diagnose.py` | BFS contradiction chains, minimum clue core, escalating hints |
| `solver/replay.py` | Domain reconstruction and deterministic explanation wording |
| `generator/generate.py` | Seeded layout, valid fill, uniqueness and ambiguity repair |
| `generator/difficulty.py` | Trace-derived score and per-size empirical thresholds |
| `backend/app/main.py` | Validated REST endpoints and worker-backed NDJSON streaming |
| `backend/app/arena.py` | Equal-input, equal-limit, trace-free comparisons |
| `frontend/src/store.js` | Pure undo/redo and replay operations; safe local persistence |
| `frontend/src/hooks/useGame.js` | Timer, saved sessions, debounced checks and completion history |
| `frontend/src/components/` | Accessible board, timeline, search tree and common UI |
| `frontend/src/pages/` | Six coherent product destinations |
| `scripts/` / `results/` | Reproducible experiments and recorded evidence |

The frontend sends JSON to the API. The API validates structure, then calls the pure engine. A solver worker emits actual events through a bounded queue; React incrementally receives them and reconstructs domains. Candidate removals are deltas; initialization, restoration and solved events include snapshots. Playback therefore reproduces both successful and failed branches. The API cancels streamed work after client disconnection. No UI imports enter the engine.

Saved entries, notes, undo/redo stacks, timer, completed-game history and the most recent arena results stay in browser localStorage. Generated games use puzzle-content identity so two different outputs cannot accidentally share saved entries. Built-in witness solutions remain server-side until an explicit reveal/solve request.

### Runtime boundaries

| Boundary | Current contract |
|---|---|
| Board model | JSON dimensions 3–12; every white cell has an across and down run of length 2–9 |
| Built-in library | Ten verified 6×6 boards, two per difficulty; board size includes black/clue cells |
| Generator | Sizes 5–12; random fill, ambiguity repair, then bounded constructive recovery if needed |
| Solver Lab | One selected puzzle; 100,000-node / 15-second solve cap; real NDJSON events |
| Strategy Arena | Selected built-ins/current puzzle; all chosen strategies share a 100,000-node / 3-second cap |
| Proof verification | Runs after human solving; its time is excluded from the displayed engine solve time |
| Storage | Browser localStorage; no database, account, registration or external LLM |
| Offline operation | Both local services must be running; dependencies are installed once; this is not a PWA |

API routes are `GET /api/health`, `/api/puzzles`, `/api/experiments`, `/api/results/{filename}`, and `POST /api/solve`, `/api/solve/stream`, `/api/check`, `/api/hint`, `/api/diagnose`, `/api/generate`, `/api/arena`. FastAPI's local `/docs` describes request fields and validation. Library responses omit witness solutions; the explicit solver endpoints return them.

Solver Lab elapsed time includes trace creation and event-emission/queue overhead inside the solve. Arena disables tracing/emission, so it is the appropriate interface for algorithm timing comparisons.

## 6. Algorithms, simply explained

All configurations implement the same bounded interface and return a validated solution, solution count, status, metrics and optional trace. `limit` is distinct from `unsatisfiable`. `unique` is returned only after enumeration with a solution limit of at least two finishes with one solution. Reaching two proves `multiple`. Finding one while counting stops early only establishes `solved`.

| Configuration key | Variable order | Value order | Inference before branching |
|---|---|---|---|
| `baseline` | Fixed row order | Ascending digits | Partial distinctness and attainable-sum checks |
| `mrv` | Minimum current legal-value count | Ascending legal digits | Same partial checks; no domain propagation |
| `degree` | MRV, then most unassigned neighbors | Ascending legal digits | Same partial checks; no domain propagation |
| `lcv` | MRV + degree | Estimated least neighbor impact first | Same partial checks; no fixed-point propagation |
| `propagation` | Fixed row order | Ascending remaining digits | Exact run-tuple support to a fixed point |
| `full` | MRV + degree | LCV | Exact run-tuple support to a fixed point |
| `human` | Easiest deduction first; MRV + degree when guessing | LCV when guessing | Ranked technique catalogue, including crossing-run support |

LCV estimates direct neighbor impact using partial run consistency; it does not perform a complete hypothetical solve for every value. Heuristics only reorder search and cannot add a valid solution or remove one.

### Basic backtracking

**Intuition:** choose the first unassigned cell, try a digit, reject partial duplicate or sum-bound violations, and undo a failed choice. **Example:** if a two-cell sum-3 run starts with 9, reject that branch immediately.

```text
search(state):
  if any run is inconsistent: return
  if all cells assigned: validate all rules; record solution
  else:
    x = first unassigned cell in row order
    for v in 1..9:
      search(copy(state) with x=v)
```

Worst-case time is exponential, `O(9^n)` search states with run-check overhead. Copying domains at each child provides straightforward, correct restoration. Baseline does not quietly perform full propagation.

Domain copies use roughly `O(n × search depth)` storage along the active recursion path. Tuple tables and the optional event trace add separate storage costs; a complete trace can grow with explored search. Node/time caps bound the run's work, rather than constituting a hard memory quota.

### Minimum Remaining Values (MRV)

**Intuition:** confront the hardest immediate choice first. Compute currently legal moves without mutating domains; choose the smallest set. **Example:** pick a cell with `{2,7}` before one with `{1,3,4,6}`.

```text
legal[x] = digits consistent with x's two runs
x = argmin size(legal[x]) among unassigned cells
```

Selecting a variable adds candidate/run-check work per node. Worst-case search remains exponential; fewer nodes are an empirical outcome, not a guarantee.

### Degree tie-break

**Intuition:** when MRV ties, choose the cell constraining the most remaining neighbors. **Example:** between two size-2 domains, prefer the cell sharing runs with six unassigned neighbors over one sharing with two.

```text
x = argmin (legal-domain size, -unassigned-neighbor count, row order)
```

Graph-based degree counting adds roughly neighbor-set work per selection. It changes ordering, not the set of legal solutions or exponential worst-case complexity.

### Least Constraining Value (LCV)

**Intuition:** try the value that removes the fewest legal neighbor choices. For each tentative digit, count neighbor candidates made inconsistent by the run constraints. **Example:** if 2 rules out one neighbor value and 7 rules out five, try 2 first.

```text
impact[v] = count of neighbor values inconsistent after x=v
try values ordered by (impact[v], digit)
```

The look-ahead costs additional constraint evaluations, approximately domain × neighbors × neighbor-domain work per selection. It can increase total runtime or even lead to more nodes on an individual puzzle. The measured arena includes such cases.

### Constraint propagation

**Intuition:** keep a digit only if it appears in some complete legal tuple for each of the cell's runs. Repeat because removing a candidate can invalidate support in an intersecting run. **Example:** across-3 gives `{1,2}`; crossing down-4 gives `{1,3}`; the intersection forces 1.

```text
repeat until no domain changes:
  for each run R:
    T = all distinct-digit tuples satisfying sum(R) under current domains
    if T is empty: contradiction
    for cell i in R: D[i] = D[i] ∩ values at position i in T
```

This is generalized arc consistency for the joint run-sum and AllDifferent relation. A length-k run has at most `9!/(9-k)!` ordered tuples. Tuple materialization can dominate runtime. Propagation-only retains fixed cell order; Full CSP also uses MRV, degree and LCV. Neither makes worst-case search polynomial.

### Human Logic solver

**Intuition:** use the easiest applicable named human deduction before guessing. Every application captures its exact premises and conclusion. If the catalogue reaches a fixed point, choose a search variable with MRV/degree and values with LCV; explicitly mark that choice as an assumption.

```text
while an applicable technique exists:
  choose the lowest-rank application
  capture clue/domain premises and reduced domains
  emit certificate; apply reduction
  if a domain becomes empty: contradiction
if unfinished: branch with MRV + degree + LCV
```

It shares CSP search's exponential worst case. Independent proof checking costs extra enumeration and is excluded from arena solve timing. A local proof is conditional on prior branch assumptions; a guess is never labeled a proved deduction.

## 7. Novelty 1 — reasoning with receipts

### The problem

A plausible explanation string does not establish that a candidate removal was valid. A useful explanation must expose the state used, make the conclusion checkable and distinguish inference from a search assumption.

### Technique catalogue

| Rank / weight | Technique | Sound deduction |
|---:|---|---|
| 1 | Unique-combination run | Restrict to the only distinct digit set for length and sum |
| 2 | Min/max bounds | Remove digits outside attainable remaining-sum bounds |
| 3 | Combination-set pruning | Restrict to the union of still-feasible digit sets |
| 4 | Run intersection | Intersect the two run-level digit-set possibilities |
| 5 | Naked pairs/triples | An n-cell domain union of size n reserves those digits in that run |
| 6 | Hidden single | A digit required by every feasible combination has exactly one candidate location |
| 7 | Cross-run combination elimination | Remove values without exact support after intersecting crossing-run tuple information |

Hidden singles require that the digit be mandatory in the run, since Kakuro does not require every digit 1–9 to appear. This distinction prevents importing an unsound Sudoku rule.

Each certificate contains `technique`, `rank`, `runs`, `cells`, `premises.domains`, `premises.constraints` and `conclusion`. The premises record the exact current candidate sets and clue scopes/targets. The conclusion records the reduced domains. A separate module, importing no technique implementation, brute-force enumerates the premises and checks that every deleted candidate lacks support.

The trace verifier additionally checks initialization against supplied entries, binds clues to the actual board, validates branch/assignment transitions, checks exact parent restoration and validates solved snapshots. A valid prefix cannot authenticate a fabricated later forced digit. The UI reports verified deduction/forced-assignment steps separately from assumptions; corrupted proof and mutation regression tests exercise this boundary.

**Exactly what the verification counter means:** it counts `technique_applied`, `eliminate_candidate` and forced-assignment announcements that pass independent entailment/state checks. A forced assignment can announce a singleton already established by a technique event, so the count is not the number of distinct human techniques. Search branches are explicit assumptions. Non-mutating `constraint_eval`, `heuristic_select` and `contradiction` timeline messages are structurally checked but their wording, numeric summaries and semantic assertions are not independently certified. A valid report therefore does **not** mean that every sentence in the timeline has been formally proved. The separate diagnosis algorithm's shortest-chain/core claims have the bounded objectives described below.

### Worked proof and conflict

In the example grid, across-3 over two cells allows only `{1,2}`. A certificate begins with both domains `{1,…,9}` and concludes both are `{1,2}`. Independent enumeration finds `(1,2)` and `(2,1)`; therefore every removed digit is unsupported. Down-4 then intersects the left cell to `{1}`. The forced assignment follows from a real domain reduction.

If the player supplies 9 in the first cell, BFS finds a contradiction in one step: there is no other distinct positive digit that can make the across total 3. A minimum-cardinality clue-core search can certify that **one clue** suffices, conditioned on that supplied entry; zero clues impose no sum contradiction.

For harder mistakes, breadth-first search explores technique applications until the first contradiction is dequeued. This proves shortest deduction length **within the implemented catalogue**, including the terminal contradiction. A separate exact subset search finds a minimum number of conflicting clue constraints under fixed player entries, if it completes. It does not claim a minimum joint set of clues and entry assumptions. Both searches return an explicit inconclusive result when their budgets expire.

### Escalating help and replay

Hints progress from run nudge, to easiest technique name, to a cell reveal established by uniqueness checking. The first levels never reveal a solution. Check board distinguishes immediate rule violations from global incompatibility. Reveal cell, across run and complete solution are explicit actions; full reveal asks for confirmation.

The lab shows real domain initialization, constraint evaluation, candidate elimination, assignment, heuristic selection, branching, contradiction, backtracking, technique application and solved events. Before/after domains, affected scopes, reasons, MRV candidate counts, degree and LCV impacts remain inspectable. Beginner, Technical and Research wording is deterministic. Playback supports play/pause, forward/back, speed, first/last and event-slider jumps. The search topology visualizes actual branch depths; a deduction-only solve correctly has no search tree.

The verified demonstration puzzle is **`expert-1` / “A beautiful contradiction”**. Its human run emits 102 actual events, including 59 technique applications and four branch assumptions; 86 deduction/forced-assignment announcements pass the verifier. The larger verified-step count includes singleton announcements after deductions. The demo's Full CSP run also contains genuine heuristic selection and backtracking, which is asserted by the library regression test.

The contribution is the **checkable connection between explanation and state**, plus bounded shortest conflict analysis, rather than an attractive log of unverifiable prose.

## 8. Novelty 2 — use ambiguity as a signal

### The pipeline

1. Sample a connected white-cell mask and remove singleton fragments. Validate every run and membership.
2. Randomly color cells with digits absent from both intersecting runs.
3. Derive every clue from that legal witness fill.
4. Run the custom solver with solution limit two.
5. If two solutions exist, compare them to find disagreement cells.
6. At a disagreement cell, edit the witness to a digit absent from its neighbors, update the two affected clue sums and re-count.
7. Accept only after complete enumeration establishes uniqueness; solve with Human Logic to rate difficulty.

Repairs favor edits with fewer valid digit combinations in the affected runs and avoid previously visited witness fills. They are targeted one-cell witness edits affecting two clues; they are **not** claimed to be globally optimal minimum-edit repairs. If no legal edit works or budgets expire, generation may restart or return no verified puzzle. Target difficulty mismatches remain visible instead of being relabeled.

**Generation reliability update:** grids 7–12 use connected, randomized short-run layouts. If random repair attempts yield no rated unique puzzle, a reserved part of the same deadline permits one fresh constructive fill, followed by complete uniqueness checking and real difficulty rating. The response identifies recovery explicitly. The original paired experiment tables below were recorded before this policy change and are historical results, not new measurements of recovery. See [the diagnosis and regression notes](docs/generator-reliability.md).

The current policy reserves `min(1 second, 25% of the total timeout)` for recovery; ordinary human rating cannot consume that reserve. Random mode has no constructive recovery. A recovery fill uses an algorithmic three-color pattern with a randomized orientation/extremal palette; its solution is not looked up from the library. It still must pass solution counting and actual human rating. This path has less layout/digit diversity than general random fill and can return a different measured difficulty than requested; the response identifies the method and target mismatch. A generator timeout remains possible under sufficiently small limits or slow hardware.

### Recorded repair example

The first logged 5×5 calibration example found disagreement at `(2,1), (2,4), (3,1), (3,2), (3,4), (4,1), (4,2)` (zero-based coordinates). Repair changed witness cell `(3,4)` from 7 to 3, updating `down:1,4` and `across:3,0`, then counted solutions again. This is an actual record in `results/generated_corpus.json`, not a scripted explanation. A single repair is not assumed to establish uniqueness; only the subsequent solution count can do that.

### Behavior-based difficulty

```text
difficulty_score = Σ technique ranks
                 + 10 × deepest guess level
                 + 0.5 × number of technique applications
```

The trace includes work on failed branches because that is real solving effort. Beginner/Easy/Medium/Hard/Expert thresholds are empirical quintiles per grid size, with tied scores kept in the lower class. The recorded thresholds are `[13,20.5,34.5,47.5]` for 5×5 and `[27.5,44.5,62,84]` for 6×6, each calibrated on 200 accepted unique puzzles. A label is relative to size; an Easy 6×6 score can exceed a Medium 5×5 score.

Technique ranks/weights 1–7 are design choices, not learned coefficients. Quantiles describe the recorded generator sample; no human-participant study or held-out human difficulty validation has been performed. Seeds control random choices, while time caps and machine load can change which attempt completes and whether recovery is needed.

This uses solver behavior rather than clue count, and makes ambiguity informative rather than discarding every ambiguous fill. It is still an empirical proxy for human difficulty. Sizes 7–12 currently use provisional thresholds and explicitly return `calibrated: false`; the requested 200-success calibration for each of those larger sizes remains unfinished.

### Current generator regression evidence

The post-restart audit generated ten seeds (`0–9`) at each of sizes 5–12 under a three-second cap: **80/80 returned unique puzzles**. Each returned witness was checked against every constraint, then each puzzle was counted again to two solutions. These are current-policy regression observations, not a replacement for a 200-seed-per-size research study or a universal success/latency guarantee. Per-run times, methods and the maximum observed time are recorded in [`results/final-audit.json`](results/final-audit.json).

## 9. Experimental methodology

The recorded environment is Python 3.11.9 on Windows. The arena tests ten unique built-ins, two per level, using all seven configurations with 100,000 nodes and a 3-second cap per run. Input JSON, stopping rules, digit order and metric definitions are consistent. Tracing, streaming, rendering and independent proof verification are disabled during timed arena solves.

Metrics are recursive nodes, parent restorations/backtracks, assignments including forced singletons, recorded constraint checks, candidate eliminations, maximum depth, solutions found and elapsed milliseconds. Human technique steps and guess depth are reported separately. For the six non-human configurations, checks record calls to high-level run predicates/support evaluation; they do not count every arithmetic operation inside tuple enumeration. **Human's checks count accepted certificate premise scopes and omit unsuccessful catalogue-search evaluations. They are not directly comparable as total constraint-evaluation work.** Use elapsed time, technique steps, guess depth and nodes with this caveat. The timer starts after board parsing; UI, network, JSON and independent proof verification costs are excluded. Single-run timing is noisy; close speed differences should not be overinterpreted.

The generation comparison uses paired seeds 0–199 at each of sizes 5 and 6: 800 runs total across repair and random modes. Both have 20 outer attempts and a 0.6-second cap. Repair may make up to 20 targeted changes per attempt; random mode tries one fresh fill per attempt. Random streams diverge after method-specific operations. The measured result applies to these declared budgets and generator distribution.

Calibration supplements successful paired repair runs with additional fresh seeds until there are 200 unique puzzles per size. The 400 accepted puzzles supply the effort-correlation experiment. Baseline runs have a one-second/100,000-node cap; censored observations would be excluded and counted. The pooled correlation can be influenced by puzzle size and is not causal evidence.

### Recompute the frozen evidence without rerunning generation

The 13 November audit recomputed the four generation success rates and mean timings from the 800 CSV rows, recomputed Spearman correlation from the 400 recorded corpus entries, and recomputed both calibration quantile sets. All matched the stored summaries. The audit includes SHA-256 hashes of the underlying files. The tables and charts below can be rebuilt from these frozen records:

```powershell
.\.venv\Scripts\python -m scripts.report
```

### Run a new experiment with the current generator

The following commands **create a new current-policy dataset**. They do not reproduce the pre-recovery generation algorithm or its exact historical rates. The repository's initial published commit already contains the recovery fix, so an exact pre-fix executable revision is not included. Existing raw observations remain available for independent reanalysis.

The experiment and library scripts currently write directly to `results/` and `data/puzzles.json`; use a separate checkout or preserve those directories before running them if the frozen presentation evidence should remain unchanged:

```powershell
.\.venv\Scripts\python -m scripts.experiments --count 200 --sizes 5 6 --budget 0.6
.\.venv\Scripts\python -m scripts.build_library
.\.venv\Scripts\python -m scripts.report
.\.venv\Scripts\python -m scripts.oracle_corpus
```

The current CSV runner records requested mode (`repair`/`random`), rather than each returned generation method. A new `repair` run therefore includes any constructive recovery; it is not a method-stratified isolation of repair alone. A new research claim about repair versus recovery needs that additional instrumentation and a fresh study.

## 10. Real measured results and ablation analysis

**Dataset identity:** the strategy table is the recorded 70-run comparison on the shipped ten-puzzle library. The generator table and correlation are the **historical pre-recovery policy**, using 200 paired seeds per size/method at sizes 5 and 6. Current-policy generation reliability is reported separately in section 8. Do not label the historical rates as success rates for the current recovery-enabled generator. The paired comparison also uses different per-attempt work (up to 20 repairs versus one fresh fill), a fixed strategy order and single timings; it is evidence for the declared implementation/budgets, not an isolated universal causal effect of repair.

<!-- MEASURED_RESULTS_START -->

| Configuration | Nodes | Backtracks | Run checks | Total ms |
|---|---:|---:|---:|---:|
| baseline | 12,664 | 12,536 | 57,072 | 255.91 |
| mrv | 293 | 165 | 31,845 | 86.86 |
| degree | 233 | 105 | 22,967 | 63.13 |
| lcv | 268 | 140 | 32,122 | 88.77 |
| propagation | 18 | 4 | 657 | 68.75 |
| full | 18 | 3 | 978 | 68.17 |
| human | 18 | 3 | 710 | 61.45 |

All 70 library runs solved within the identical 100,000-node / 3-second caps. Timing is a single run per puzzle/configuration.

| Grid | Method | Runs | Unique success | Mean ms |
|---|---|---:|---:|---:|
| 5×5 | repair | 200 | 97.0% | 104.88 |
| 5×5 | random | 200 | 50.5% | 217.71 |
| 6×6 | repair | 200 | 68.0% | 283.98 |
| 6×6 | random | 200 | 5.0% | 583.53 |

Spearman difficulty/effort correlation: **ρ = 0.7777, n = 400, p = 2.87e-82**; 0 baseline runs censored. Each size has 200 accepted unique calibration puzzles. The paired comparison uses 200 seeds per size/method, 20 attempts and a 0.6-second cap.

Recorded environment: Python 3.11.9 on Windows-10-10.0.26300-SP0. Experiment wall time: 272.37s.

<!-- MEASURED_RESULTS_END -->

**Check-count footnote:** Human's 710 recorded checks count accepted proof-premise scopes, while unsuccessful technique searches are omitted. It is not a total work count comparable to the other rows. The node, backtrack and timing columns retain their documented meanings; timing includes technique-search work.

![Ablation: actual node counts and runtime](results/ablation.png)
![Search effort by measured difficulty](results/by-difficulty.png)
![Paired repair versus random generation](results/repair-vs-random.png)
![Difficulty score versus baseline search effort](results/difficulty-effort.png)

**What contributed most?** On these ten puzzles, MRV reduced total baseline nodes from 12,664 to 293 (97.7%). Adding degree reduced that to 233. Adding LCV increased the total to 268 in the no-propagation chain, showing that a heuristic is not automatically beneficial on every instance. Propagation-only and Full CSP both used 18 nodes, while Full CSP made three parent restorations versus propagation-only's four.

**Nodes are not time.** On `easy-1`, MRV took 3.26 ms while Full CSP took 21.70 ms despite using one node; exact tuple enumeration cost more than the saved search. On `expert-2`, baseline used 446 nodes while MRV used 101 but took substantially longer. This is why the dashboard exposes actual time and constraint checks alongside nodes rather than declaring a predetermined winner.

**Generation evidence.** Repair improved success rates and reduced mean elapsed time under the tested paired caps. This supports targeted ambiguity repair for this generator, not universal dominance over every random-generation design. The correlation indicates useful association with search effort, but human studies, size-stratified analysis, larger boards, repeated timings and confidence intervals remain future work.

Raw evidence: [`generation.csv`](results/generation.csv), [`generated_corpus.json`](results/generated_corpus.json), [`calibration.json`](results/calibration.json), [`benchmark.csv`](results/benchmark.csv), [`summary.json`](results/summary.json), [`coverage.json`](results/coverage.json). No synthetic performance numbers or hardcoded AI traces are used.

## 11. Feature tour and screenshot capture list

| Destination | What to demonstrate | Exact screenshot to capture |
|---|---|---|
| Home | Editorial introduction, real current puzzle, local notebook and working navigation | `docs/screenshots/01-home.png`: full desktop home after library load |
| Play | Input, run highlights, notes, history, timer, checks, three hint levels and reveals | `docs/screenshots/02-play.png`: a selected cell with notes and an open hint |
| AI Solver Lab | Streamed candidate reductions, heuristic explanation, proof counts and replay | `docs/screenshots/03-lab.png`: Human Logic at a certified deduction, premises expanded |
| Strategy Arena | Identical-input comparison, ablation chart, complete rows and experiment evidence | `docs/screenshots/04-arena.png`: current Expert puzzle after all strategies finish |
| Puzzle Generator | Seed controls, uniqueness, honest target result and repair notebook | `docs/screenshots/05-generator.png`: accepted puzzle plus its real repair log; label the attempt number |
| Demonstration Mode | Real initial domains, propagation, decisions, backtrack and solution | `docs/screenshots/06-demo.png`: Expert trace paused at a real backtrack |

These are deliberate screenshot placeholders, not claims that images have been captured. A retry after the PC restart still failed during the browser tool's Statsig initialization; the earlier native fallback had also stopped at Windows URL safety detection. Rendered desktop/mobile and console QA remain unverified. Before presenting, capture these six files and inspect 320, 768, 1024 and 1440px widths. See [`docs/verification.md`](docs/verification.md).

The repair notebook retains logs across failed and accepted attempts. Selecting a log overlays its coordinates on the final accepted canvas; it does **not** reconstruct the historical board or the witness before that repair. An earlier attempt can have a different layout, and even a log from the accepted attempt can precede later clue edits. Present the notebook as a recorded repair explanation with coordinate highlighting, not as event-sourced generator replay. Solver replay, by contrast, reconstructs actual past domains.

Four real chart assets are ready for the presentation: `results/ablation.png`, `results/by-difficulty.png`, `results/repair-vs-random.png` and `results/difficulty-effort.png`. Keep the historical-policy label on the last two. Use the worked grid in section 3 for an editable diagram; do not fabricate UI screenshots.

The UI uses local system fonts, paper/ink/sage/orange tokens, semantic buttons, keyboard focus indicators and reduced-motion support. All six destinations preserve the current puzzle and shared solver/game state. Candidate and clue highlights communicate real engine state. The board remains the visual center of the app.

## 12. Testing and evidence

The latest full coverage run passed **345 backend tests at 95% core line coverage** (698/733 statements). Model coverage is 96%, engine 99%, technique catalogue 97%, diagnosis 92% and the hardened independent verifier 92%. **Thirteen frontend tests** pass. Read-only review findings and the generator budget failure were corrected with regression coverage; see `docs/verification.md`.

Tests cover malformed boards, digit/sum/duplicate constraints, all strategies, unique/multiple/unsatisfiable states, budget/cancellation behavior, state restoration, real generation and repairs, difficulty score, independent proof rejection, trace mutation rejection, bounded diagnosis, minimum clue cores, hints, replay and API streaming/check feedback.

**Independent oracle:** 300 recorded randomly generated unique 5×5 puzzles are encoded separately in OR-tools CP-SAT, with integer domains, AllDifferent and sum equations. Every custom strategy must count a unique solution and agree with the oracle. Human traces must also pass the independent proof checker. OR-tools is never imported by production engine code.

This is independence of the solving algorithm: the CP-SAT test reuses `Board` to obtain run scopes, so it is not an independent JSON/parser implementation. Hand-checked structure/invalid-input tests provide separate model-boundary evidence. Likewise, the 300 samples are small 5×5 generated puzzles, not a claim of exhaustive verification over all sizes.

Frontend tests exercise real reducer transitions and DOM controls: entry/delete, pencil marks, undo/redo, completed-game reopening, distinct generated identities, keyboard navigation, paused state, replay stepping/slider/play, timer persistence, completion recording and stale reveal protection. Only the HTTP boundary is controlled for timing-dependent component tests.

```powershell
.\.venv\Scripts\python -m pytest --cov=backend/app/core --cov=backend/app/solver --cov=backend/app/generator --cov-report=term-missing --cov-report=json:results/coverage.json
npm --prefix frontend test
npm --prefix frontend run build
```

With both services running, `.\.venv\Scripts\python -m scripts.smoke` exercises the actual HTTP stream, verified proofs, all hint levels, completion/mistake checks, diagnosis, seven-strategy arena, generation and artifact downloads. It passed again after the PC restart; see [`results/live-smoke.json`](results/live-smoke.json). This is API verification rather than rendered browser QA. The independent final audit additionally validates the library scores/proofs and reanalyzes the frozen research files; see [`results/final-audit.json`](results/final-audit.json).

On a restrictive Windows sandbox, FastAPI TestClient may hang while asyncio creates a loopback socket pair. Run these API tests from a normal local terminal with loopback access. This environment also emitted a Starlette/httpx migration deprecation warning; it did not invalidate the passing API tests.

## 13. Installation, launch and troubleshooting

Requirements: **Python 3.11+**, **Node.js 22.12+ or a supported newer LTS** (tested with Node 24), npm, and Internet access for the initial package installation only. No API keys or accounts are needed.

### After restarting this PC — no reinstallation needed

Open two terminals in `C:\Project\AI PROJECT`. Start the backend and frontend with the two commands below, then open [the app](http://127.0.0.1:5173). The processes stop when Windows restarts; restarting the PC does not automatically relaunch them. The existing `.venv`, `frontend/node_modules`, data and results remain installed on disk. Browser localStorage progress remains available when using the same browser profile and the same URL/port.

```powershell
# Terminal 1, in C:\Project\AI PROJECT
.\.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

```powershell
# Terminal 2, in C:\Project\AI PROJECT
npm --prefix frontend run dev -- --port 5173 --strictPort
```

`--strictPort` avoids silently moving to a different frontend origin and making saved games appear missing. Verify [backend health](http://127.0.0.1:8000/api/health) and the app before class. No PowerShell activation-policy change is needed because the commands call the virtual-environment interpreter directly.

### First installation on a new machine

```powershell
git clone https://github.com/xShikhar/Kakuro-AI-Lab.git
cd Kakuro-AI-Lab
```

From the repository root (`C:\Project\AI PROJECT` on this PC, or the cloned directory on a new machine), install:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
npm --prefix frontend ci
```

Runtime-only Python installation can use `requirements.txt`. The dev requirements add the independent oracle, test coverage, statistics and plotting packages. `requirements-lock.txt` records the tested Python environment; `frontend/package-lock.json` records npm dependencies.

The final audited environment was Python 3.11.9, Node v24.14.0 and Windows 10 build 26300. Tests/build were rerun after the restart rather than inferred from the earlier session. For the installed Python versions exactly, use `requirements-lock.txt`; the range-based files allow compatible updates.

**Backend — one command in terminal 1, from the repository root:**

```powershell
.\.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

**Frontend — one command in terminal 2, from the repository root:**

```powershell
npm --prefix frontend run dev -- --port 5173 --strictPort
```

Open [Kakuro AI Lab](http://127.0.0.1:5173). Interactive API documentation is at [FastAPI docs](http://127.0.0.1:8000/docs). After installation, disconnect from the Internet: browser assets and reasoning remain local. Keep both local services running; this is a local web application, not an installable offline PWA. To stop a service, press Ctrl+C in its terminal.

| Symptom | Resolution |
|---|---|
| Backend unavailable banner | Start the backend on port 8000; reload the browser |
| Port already in use | Stop the earlier server, or update Vite's proxy when changing the backend port |
| `No module named …` | Use the `.venv` interpreter and install the relevant requirements |
| `npm ci` fails | Check initial network access and Node version; retain the lockfile |
| Empty library | Restore the shipped `data/puzzles.json` from Git; only rebuild experiments/library intentionally, since those scripts overwrite frozen data |
| Generator returns no puzzle | This is an honest budget failure; try a smaller grid, another seed or Any target |
| Target not reached | Inspect the measured returned label; generation does not silently fake the requested level |
| Solver says `limit` | No unsatisfiability or uniqueness claim follows; use another configuration or larger allowed cap |
| Private browsing/full storage | The session remains usable; browser persistence may be unavailable |

On macOS/Linux use `python3 -m venv .venv` and `.venv/bin/python` in place of the Windows interpreter path. Run from the repository root so module imports resolve. Installation does not contact a paid service or download an AI model.

## 14. Presentation guide

### Evidence that can go directly onto slides

| Claim | Exact evidence and qualification |
|---|---|
| “Custom offline CSP engine with explainable search” | Standard-library Python engine; seven configurations; local FastAPI/React operation; no external LLM |
| “Proof-carrying human deductions” | Seven ranked techniques; independent entailment enumeration; `expert-1` human run has 86/86 verified deduction/forced-assignment announcements, with four assumptions separately identified |
| “Bounded shortest conflict diagnosis” | BFS minimizes catalogue applications when it reaches a contradiction; clue-cardinality minimization is separate and conditions on fixed entries |
| “Propagation reduced search on our benchmark” | Recorded library totals: baseline 12,664 nodes; Full CSP 18; all ten identical puzzles solved by all seven configurations |
| “Repair helped our original generator” | Historical 800-run paired study: 5×5 97% vs 50.5%, 6×6 68% vs 5%, under stated budgets; these are not current recovery-policy success rates |
| “Difficulty is associated with search effort” | Recomputed historical pooled Spearman ρ = 0.7777, n = 400; not causal, not human difficulty validation, potentially size-confounded |
| “Current generation works across the selectable sizes” | Final audit: 80/80 seeded requests across sizes 5–12 under a three-second cap, followed by re-counting; a sampled regression result, not a universal guarantee |
| “The automated verification passes” | Post-restart 345 backend tests, 13 frontend tests, 95.23% core coverage, production build and live API smoke pass; rendered browser/mobile QA is still unverified |

Do not claim world-first research novelty, proof of every timeline sentence, globally shortest mathematical proofs, a minimum joint clue/cell/entry core, minimum-edit repairs, empirical calibration at all eight sizes, universal generator success, human-validated difficulty, or a completed visual/accessibility audit. The implementation and measured observations support the narrower claims in this table.

### Dataset and asset mapping

Use the architecture diagram and worked CSP grid in sections 3–5 as editable explanatory visuals. Use the four chart PNGs in section 10 with their dataset/policy labels. Use `results/benchmark.csv` for editable strategy tables/charts, `results/generation.csv` for the historical generator comparison, and `results/final-audit.json` for current regression/library evidence. The ten-puzzle benchmark is entirely 6×6; it is not a benchmark spanning every generated size. No real UI screenshots have been captured yet.

### Suggested slide outline, drawn entirely from this README

| Slide | Message | Source section |
|---:|---|---|
| 1 | Kakuro AI Lab: explain the thinking, not just the answer | Opening overview |
| 2 | Why local arithmetic creates an AI search problem | 1–3 |
| 3 | Variables, domains, AllDifferent + Sum | 4 |
| 4 | UI → API → pure engine → events → replay | 5 |
| 5 | Baseline, MRV, degree and LCV | 6 |
| 6 | Tuple support and fixed-point propagation | 6 |
| 7 | Novelty 1: certificates, independent checking and wrong-entry diagnosis | 7 |
| 8 | Novelty 2: disagreement-guided clue repair and measured difficulty | 8 |
| 9 | Fair methodology and independent oracle | 9 and 12 |
| 10 | Actual ablation, repair and correlation results | 10 |
| 11 | Live demonstration | Below |
| 12 | Limitations, responsible claims and next steps | 15 |

### Five-minute live demonstration

**0:00–0:35:** Open Demonstration Mode and Reset demonstration. Confirm **`expert-1` / “A beautiful contradiction”** and **Full CSP**. The default configuration is Full CSP, not baseline. Explain the initial nine-digit domains and the two run constraints per cell. The library test establishes that this exact puzzle/configuration includes real backtracking.

**0:35–1:20:** Select Full CSP and Run solver. Jump to Propagation, inspect a real candidate removal and the responsible clue. Step forward/back to show domains reconstruct, rather than repainting a fixed animation.

**1:20–2:05:** Jump to Decision. Read actual MRV counts, degree and LCV impacts in the event. Jump to Backtrack on this same Full CSP trace and explain why the parent snapshot is restored. Search-tree nodes come from real branch events; they are not a scripted search animation.

**2:05–2:45:** Run Human Logic + Proofs. Inspect one certificate's actual clue/domain premises, the 86/86 deduction/forced-assignment count and the four separately labeled assumptions. There are 59 technique applications; singleton announcements account for the extra verified items. State that the verifier is a different enumerator and does not certify every non-mutating timeline message.

**2:45–3:15:** Open Play for that same Expert puzzle. For a repeatable clean demonstration, reset its saved session first, select **row 3, column 2** in the UI (zero-based coordinate `2,1`) and enter **1**. Use Why is this wrong? The four-cell downward clue totals 27: with 1 fixed, the other three distinct digits total at most 9+8+7, giving only 25, so no completion exists. The tested result is a one-step contradiction and a one-clue minimum core under that fixed entry. Clear the wrong digit afterward. If a different saved state or puzzle is used, treat any budget/inconclusive response honestly rather than expecting this exact explanation.

**3:15–4:05:** Open Strategy Arena, select the current puzzle and run all configurations. Compare actual time and nodes. Point out that fewer nodes need not mean faster runtime, and Human's check counter excludes unsuccessful catalogue work. The lower experiment panel/scatter displays frozen historical observations; label those separately from the arena run you just executed.

**4:05–4:45:** Generate a 5×5 puzzle with seed 42 and Any target. Inspect the actual ambiguity repair notebook, uniqueness result, method message and measured difficulty score; load it into Play. Explain that log highlighting overlays coordinates on the final canvas and is not historical generator-state replay. If recovery runs, identify it as constructive recovery followed by real uniqueness checking.

**4:45–5:00:** Return to Demonstration Mode and reset. Close with the two contributions and the explicit calibration/browser-verification limits.

### Likely professor questions

| Question | Concise answer |
|---|---|
| Is this just backtracking? | Backtracking completes the search, but the project compares multiple orderings, exact support propagation, named human deductions and independent proof checking. |
| Why is it a CSP? | Cells are variables, digits are domains, and each run imposes a sum equation plus AllDifferent. |
| Does propagation solve everything? | No. Some unique library puzzles reach a fixed point and require explicit guesses; the trace records their depth and failed branches. |
| Is the verifier independent? | It imports no engine/technique code and uses its own premise enumeration, while sharing the board's structural schema and replay data format. |
| What exactly is proved? | Candidate reductions/forced assignments are entailed by recorded premises under explicit assumptions; state transitions and final solutions are checked. Non-mutating timeline messages are not semantically certified. |
| Is the conflict globally shortest? | Shortest in the implemented deduction-application graph when BFS completes. Minimum clue-cardinality is a separate bounded exact search conditioned on supplied entries. |
| Why not OR-tools in the engine? | The course project demonstrates custom CSP logic. OR-tools is reserved for an independent test oracle. |
| Can you guarantee uniqueness? | Only completed solution counting with a limit of at least two establishes unique/multiple status. A timeout is inconclusive. |
| How is repair different from random retry? | The two solutions identify disagreement cells, and the repair edits one of those witness digits and its two clue sums before recounting. |
| Does changing a clue preserve the witness? | Both affected clue sums are recomputed after a digit legal in both runs is chosen, so the edited witness remains a valid fill. |
| Are difficulty labels human-validated? | No. They are per-size empirical quantiles of solver behavior; the correlation measures search effort association, not human difficulty. |
| Does Full CSP always win? | No. Exact tuple work can exceed the search it saves. The raw table includes cases where MRV or baseline is faster. Human's recorded check count also has narrower instrumentation, so it is not a total-work comparison. |
| Can the historical generator rates be reproduced by rerunning today's command? | The raw statistics can be recomputed exactly. Today's generator includes recovery and produces a new-policy study; the pre-fix executable revision is not included in the published history. |
| Does the repair log show the old board? | No. It records actual edits and overlays coordinates on the accepted final canvas. Only solver replay reconstructs past domain states. |
| What works offline? | All game, solver, generation, replay and persistence operations, once local dependencies are installed and the two local services are running. |
| What remains incomplete? | Empirical calibration for sizes 7–12, rendered browser/mobile QA and stronger research validation such as human studies and repeated timing intervals. |

## 15. Limitations, future work, references and project tree

### Final acceptance audit

“Implemented / automated evidence” means the code and stated tests/API checks support the feature; it does not imply rendered visual QA. “Partial” identifies an original requirement that is broader than the current implementation or evidence.

| Original acceptance area | Final status | Evidence or remaining boundary |
|---|---|---|
| Playable game and five difficulty levels | Implemented / automated evidence | Ten unique built-ins, entries/notes/history/timer/help/completion tests; persisted local sessions |
| CSP search, MRV, degree, LCV and propagation | Implemented / automated evidence | Seven configurations; all match CP-SAT over the 300-puzzle test corpus |
| Proof-carrying Human Logic | Implemented with stated proof scope | Seven techniques; independent local entailment; guesses and non-certified narrative events distinguished |
| Minimal “Why is this wrong?” | Partial relative to a global minimum objective | Bounded catalogue-shortest BFS and conditional minimum clue count; not a global joint cells/clues/entries minimum |
| Reasoning timeline and candidate highlights | Implemented / rendering unverified | Real event payloads and board/highlight handlers; no rendered animation/console walkthrough completed |
| Genuine solver replay | Implemented / automated evidence | Domain deltas, branch/restore snapshots, replay-state and control tests |
| Unique generator and ambiguity-guided repair | Implemented with bounded recovery | Real counts; targeted digit/two-clue edits; sizes 5–12 tested; minimum edit count not established |
| Solver-derived difficulty across all sizes | Partial | Empirical 200-sample calibration at sizes 5 and 6 only; sizes 7–12 provisional |
| Strategy Arena and ablation | Implemented with measurement caveats | Seventy recorded runs plus live comparisons; single timings and unequal Human check instrumentation |
| Repair/random and difficulty/effort experiments | Real data; policy coverage partial | Historical 800-run paired comparison and 400-puzzle correlation; not a full current-policy study at every size |
| Demonstration Mode | Implemented / real-engine API evidence | Tested `expert-1` Full CSP trace includes propagation, decisions and backtracking; current human stream verifies |
| Responsive premium UI and accessibility | Implemented CSS/controls; visual audit incomplete | Production build and DOM tests pass; screenshots, mobile/console and accessibility audit remain open |
| Organized/commented code | Implemented modular source | Separate model/search/techniques/verifier/diagnosis/generator/API and React modules; no claim of a completed external style audit |
| Presentation README, supporting docs, reproducible data | Updated and evidence-checked | This self-contained source, raw records/charts and a dated final audit; historical reanalysis distinguished from current reruns |
| Automated tests and simple launch | Passed after restart | 345 backend, 13 frontend, 95.23% core coverage, build, live HTTP smoke; two commands to restart |

The project is suitable for an accurate presentation using the supported claims above. It is **not** accurate to check every original acceptance item as unconditionally complete. Remaining research/visual validation must stay on the limitations slide unless it is actually completed later.

The core is extensively sampled and independently checked, but that does not prove correctness for every possible puzzle. The 300-oracle set contains small unique 5×5 boards. Larger layouts, long runs, malformed inputs, nonunique boards and caps have focused tests, but not an exhaustive oracle corpus. Generation for 7–12 can exhaust its cap and uses provisional difficulty thresholds. A verified unique output is never substituted with an unverified one.

Shortest diagnosis is catalogue-relative. Minimum clue cores condition on all player entries and do not optimize the joint entry/clue assumption set. Minimum-edit repair is not claimed. Proof checking establishes local entailment under recorded assumptions, not a universal human reasoning theory or certification of every timeline message. Human check counts omit unsuccessful catalogue work. Single-run timings lack confidence intervals; the pooled correlation may be size-confounded. Current recovery and historical repair-only policy results are distinct, and the repair notebook does not reconstruct old generator boards.

Browser automation was retried after the restart and still failed during its Statsig initialization; the earlier native fallback had stopped at Windows URL safety detection. Production build, API tests, DOM tests and local HTTP readiness passed, but rendered desktop/mobile, console, keyboard walkthrough and accessibility audit remain to be completed. See [`docs/verification.md`](docs/verification.md) for the evidence and [`results/final-audit.json`](results/final-audit.json) for the dated data checks.

Future work: calibrate 200+ unique puzzles at every supported size; stratify correlations by size; run repeated shuffled-order benchmark trials with intervals; recruit human solvers for difficulty validation; improve bounded conflict search; optimize tuple tables and reversible domains; add a service worker/PWA and a single distributable launcher; complete visual and accessibility audits.

References:

- Stuart Russell and Peter Norvig, *Artificial Intelligence: A Modern Approach*, chapter on Constraint Satisfaction Problems — [official book site](https://aima.cs.berkeley.edu/).
- Alan K. Mackworth (1977), “Consistency in Networks of Relations,” *Artificial Intelligence* 8(1), 99–118 — foundational arc-consistency work.
- Rina Dechter, *Constraint Processing*, Morgan Kaufmann (2003) — propagation, search and constraint networks.
- Helmut Simonis, “Kakuro as a Constraint Problem,” CP Workshop on Modelling and Reformulating Constraint Satisfaction Problems (2008) — [paper](https://citeseerx.ist.psu.edu/document?doi=d6506197aa02eb5a9e47e7a46983b7aa4e4dc41d&repid=rep1&type=pdf).
- [FastAPI concurrency documentation](https://fastapi.tiangolo.com/async/) — synchronous endpoint thread-pool behavior.
- [Vite getting started](https://vite.dev/guide/) — frontend development/build requirements.
- [OR-tools CP-SAT documentation](https://developers.google.com/optimization/cp/cp_solver) — independent test oracle only.

```text
AI PROJECT/
├── README.md
├── requirements.txt / requirements-dev.txt / requirements-lock.txt
├── backend/
│   ├── app/
│   │   ├── main.py / arena.py
│   │   ├── core/model.py
│   │   ├── solver/
│   │   │   ├── constraints.py / engine.py / techniques.py
│   │   │   └── verifier.py / diagnose.py / replay.py
│   │   └── generator/generate.py / layouts.py / difficulty.py
│   └── tests/
├── frontend/
│   ├── package.json / package-lock.json / vite.config.js
│   ├── src/
│   │   ├── App.jsx / main.jsx / styles.css / store.js
│   │   ├── components/Board.jsx / Timeline.jsx / UI.jsx
│   │   ├── hooks/useGame.js
│   │   ├── services/api.js
│   │   └── pages/Home.jsx / Play.jsx / Lab.jsx / Arena.jsx / Generator.jsx
│   └── tests/
├── data/puzzles.json
├── scripts/experiments.py / build_library.py / oracle_corpus.py / report.py
├── results/  (raw CSV, corpus JSON, calibration, coverage, final-audit.json and PNG charts)
└── docs/architecture.md / algorithms.md / benchmarking.md / verification.md / generator-reliability.md / specification.md
```
