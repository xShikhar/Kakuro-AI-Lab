# PROJECT: KAKURO AI LAB
## An Explainable AI Platform for Constraint Satisfaction, Intelligent Search and Interactive Puzzle Solving

You are acting as a senior full-stack engineer, AI/algorithm designer, technical writer, and an award-winning UI/UX designer.

DESIGN, IMPLEMENT, TEST AND COMPLETE a production-quality academic AI project called **Kakuro AI Lab**. It is worth 20% of an Artificial Intelligence university course grade, so it must show algorithmic correctness, real depth, two meaningful and genuinely unique novelties, and a premium user experience.

Do NOT build a basic Kakuro game with simple backtracking. Build a complete interactive platform that shows how an AI reasons, searches, justifies each decision, detects contradictions, and improves search efficiency. Do not stop at a plan or mockup. Implement everything and make it run.

---

# 0. GROUND RULES (apply throughout)

1. Inspect the existing repository first (framework, dependencies, entry points, what already exists). Preserve useful existing work. If empty, choose the stack below.
2. NO fake anything: no hardcoded solutions or AI decisions, no random numbers simulating performance, no decorative visualizations disconnected from the real engine, no dead buttons or navigation links. If a feature cannot be fully implemented, say so explicitly instead of faking it.
3. No external LLM or paid API. The app must work fully offline after installation.
4. Work in the phases listed in section 14. Run and test after each phase. Do not wait for approval between phases unless there is a genuine blocker.
5. The AI engine must be independent of the frontend (pure Python, no UI imports).
6. Handle invalid input and API errors gracefully; include loading and empty states; no console errors.

---

# 1. TECH STACK

- Backend and AI engine: Python 3.11+, FastAPI, pydantic. All core AI logic is custom, pure Python (no CP/SAT/solver libraries in the engine). OR-tools CP-SAT is allowed ONLY inside tests as an independent cross-check.
- Frontend: React + Vite (JavaScript or TypeScript, your choice; keep it simple and readable). CSS or Tailwind is fine. Use Recharts or Chart.js for charts. Keep dependencies minimal.
- Streaming of solver steps: REST for puzzle operations; WebSocket or an equivalent for long runs. Heavy runs must not freeze the UI.
- Persistence: browser localStorage/IndexedDB for saved games and stats. No login, no external database.
- One simple command each for backend and frontend, documented in the README.

---

# 2. KAKURO AND CSP FORMULATION

Rules: fill every white cell with 1-9; every horizontal and vertical run sums to its clue; no repeated digit within a run; the same digit may repeat across intersecting runs.

CSP model:
- Variables: every white cell. Domains: {1..9}.
- Constraints: for each run, AllDifferent + Sum. Each white cell belongs to exactly one horizontal and one vertical run.
- Precompute valid digit combinations for every (run length, sum) pair and cache them.

Required internal representation: variables, domains, horizontal/vertical runs, sum targets, cell-to-run maps, constraint relationships, assignment state. Use reversible state or correct copying so backtracking never corrupts domains.

Puzzle JSON format: {rows, cols, cells: [[{"type":"white"} | {"type":"black","across":int|null,"down":int|null}]]}. Provide at least 10 verified sample puzzles across five difficulty levels (Beginner, Easy, Medium, Hard, Expert), including some that genuinely require guessing.

---

# 3. THE KAKURO GAME (fully functional)

Interactive board: clue cells with diagonal split and sums, white cells, selected-cell and run highlighting, mouse and keyboard navigation, digit entry 1-9, delete, pencil marks, undo/redo, timer with pause/resume, reset, new puzzle, difficulty selection, mistake highlighting.

Feedback on entry: distinguish (a) a rule violation (duplicate in run, sum exceeded) from (b) a move that is locally valid but incompatible with the unique solution. Do not reveal the solution automatically.
Help tools: Hint, Check board, Reveal cell, Reveal run, Reveal solution (with confirmation).
Completion: animation, time, mistakes, hints used, difficulty, performance summary. Store statistics locally.

---

# 4. SOLVERS (all behind one common interface, all emitting a replayable event trace)

Implement these configurations, and make sure they genuinely differ in implementation:
1. Basic Backtracking (fixed order).
2. Backtracking + MRV.
3. Backtracking + MRV + Degree (tie-break).
4. MRV + Degree + LCV.
5. Full CSP: MRV + Degree + LCV + constraint propagation (tuple-based support checking, fixed-point propagation, forced-assignment detection, contradiction detection).
6. HumanLogicSolver (Novelty 1, section 5).

Every solver returns: solution, nodes, backtracks, assignments, constraint checks, candidate eliminations, max depth, solutions found, wall time, and the trace. Support configurable node limit and timeout, solution counting up to a limit, unsolvable-puzzle detection, and non-uniqueness detection. Every returned solution must be validated against ALL constraints.

Trace event types: domain_init, constraint_eval, eliminate_candidate, assign, heuristic_select, branch, contradiction, backtrack, technique_applied, solved. Each event stores step number, affected cells/runs, candidates before and after, the reason, and related constraints.

---

# 5. NOVELTY 1: Proof-carrying human-technique solver with minimal conflict diagnosis

### 5a. Technique catalogue
Solve the way a human expert does, using named techniques ordered by difficulty rank, guessing only when none applies (guess levels recorded). At minimum:
1. Unique-combination runs (e.g. length 2, sum 3 forces {1,2})
2. Min/max bound pruning
3. Combination-set pruning (candidates must lie in the union of valid digit sets for the run given current candidates)
4. Run intersection (row-run and column-run candidate sets)
5. Naked pairs/triples within a run
6. Hidden singles within a run
7. Cross-run combination elimination
Each application produces a Justification: {technique, runs, cells, premises (the exact clues and candidate states used), conclusion}. All generated from real solver state.

### 5b. Independent proof verifier
Write a SEPARATE module that re-validates every step of a HumanLogicSolver trace using only brute-force enumeration over the step's premises, never reusing the technique's own code. The UI shows "N/N steps formally verified". A test must prove the verifier rejects deliberately corrupted steps.

### 5c. "Why is this wrong?" minimal conflict explanation
When the player enters a digit that contradicts the unique solution, find the SHORTEST chain of deductions (BFS or iterative deepening over technique applications, starting from the clues plus that wrong digit) that reaches a contradiction. Return plain-English ordered steps and the minimal set of involved cells/clues, highlighted on the board.

### 5d. Escalating hints
Three levels: nudge (which run to look at) -> technique name -> reveal. Always the easiest applicable technique.

### 5e. Explainability UI
- Live reasoning timeline of every AI action (event fields as in section 4).
- Visual candidate elimination: animate removals, highlight the responsible clue, show the reason and updated domain size.
- Decision explanations: why a variable was selected (MRV values, degree tie-break) and why a value was preferred (LCV).
- Contradiction explanations: which constraint failed, which earlier decision led to the branch, why backtracking is necessary.
- Replay: play, pause, resume, step forward/back, speed control, jump to any event, inspect the board at any past step. Implement genuine event-sourced or snapshot-based replay that reconstructs real solver state.
- Three explanation levels: Beginner, Technical, Research. Deterministic, generated from solver operations, no LLM.

---

# 6. NOVELTY 2: Ambiguity-guided generator with solver-derived difficulty

### 6a. Generation pipeline
Valid layout (every white cell in two runs of length >= 2, connected, no run longer than 9, configurable sizes ~5x5 to 12x12) -> randomized valid fill -> derive clues -> count solutions with the solver (stop at 2).

### 6b. Ambiguity-guided repair (NOT random retry)
If the puzzle has more than one solution, compute the difference between two solutions to locate the ambiguous cells (the swap cycle). Repair minimally (convert a cell in the cycle into a clue cell, or adjust a clue), then re-verify. Log each repair step and show it in the UI ("Ambiguity in cells {...} -> repaired by ..."). Include a timeout and size limits.

### 6c. Difficulty from solving behaviour, not clue count
difficulty_score = sum of technique weights (by rank) over the HumanLogicSolver trace + 10 * guess_levels + 0.5 * number_of_steps. Labels Easy/Medium/Hard/Expert (plus Beginner) with thresholds tuned empirically on 200+ generated puzzles per size. The generator can target a difficulty and retry/repair until the label matches (with an attempt cap).

### 6d. Experiments (real data only)
- Repair vs random regeneration: success rate and time over 200+ puzzles.
- Spearman correlation between difficulty_score and Basic Backtracking node count over 200+ puzzles, shown as a scatter plot.

---

# 7. EVALUATION: Strategy Arena and ablation

Let the user pick one puzzle, several, a difficulty level, or all benchmark puzzles. Run every configuration on identical input with identical stopping conditions and consistent metrics. Measure timing separately from visualization overhead.

Dashboard: time, nodes, backtracks, constraint checks comparisons; search-tree visualization; performance by difficulty; comparison tables; highlight the fastest but never assume the full CSP solver wins every metric. Show actual results.

Ablation study section comparing: Baseline, +MRV, +MRV+Degree, +MRV+Degree+LCV, +Propagation only, Full CSP, plus HumanLogicSolver (report steps/techniques/guess levels where raw nodes do not apply). Include short written analysis of which technique contributes most, based on the measured data.

---

# 8. DEMONSTRATION MODE

One dedicated mode for presenting to the professor: open a preselected challenging puzzle -> show initial candidate domains -> run the solver -> watch propagation -> inspect eliminations -> see MRV/Degree/LCV decisions -> watch a real backtrack -> final solution -> open Strategy Arena -> compare against basic backtracking -> inspect results. One-click reset to repeat. Must use the real engine, never a scripted fake.

---

# 9. UI/UX DESIGN DIRECTION

Act as an award-winning UI/UX designer. You have full creative freedom. Design a distinctive, polished, professional product that does not look like a generic AI-generated dashboard. The Kakuro board is the visual centrepiece and must stay readable even with candidate marks and AI highlights. Keep it responsive (desktop and mobile, no horizontal overflow), accessible, with a consistent design system, purposeful animation (animations must communicate state changes such as eliminations, backtracks, placements), and no clutter.

Required sections (navigation must be consistent and keep state): Home, Play, AI Solver Lab, Strategy Arena, Puzzle Generator, Demonstration Mode. A short in-app "How it works" explanation of CSP concepts is welcome but must stay small; do not build a textbook.

---

# 10. CODE ORGANIZATION AND COMMENTING (important: this will be presented)

The team will present this project, so the codebase must be easy to walk through.

- Keep files small, single-purpose and logically grouped. Suggested layout (improve if needed):
  backend/app/{main.py, api/, core/ (board, runs, constraints, domains), solver/ (backtracking, heuristics, propagation, optimized_solver, human_solver, techniques, verifier, diagnose, explanation, events, metrics), generator/ (puzzle_generator, repair, difficulty), validation/, tests/}
  frontend/src/{components/, pages/, hooks/, services/, store/, utils/}
  data/ (puzzles), scripts/ (benchmark and experiment runners), results/ (generated CSV and charts), docs/
- Every file starts with a header comment explaining its purpose and where it fits in the system.
- Every function and class has a docstring: what it does, why it exists, inputs/outputs. For AI-specific code, explain the underlying concept in plain words (CSP, arc consistency, MRV, degree, LCV, constraint propagation, backtracking, proof verification) so a student can read the code and explain it aloud.
- Comment the non-obvious logic inline (propagation loops, the repair algorithm, shortest-conflict search, the verifier). Do not over-comment trivial lines.
- Clear naming, no giant components, no duplicated logic.

---

# 11. README.md (the presentation will be built from this file ONLY, so make it exceptional)

Write a fully detailed, well-structured README that works as presentation material. Use clear headings, tables, diagrams (Mermaid or ASCII), and short paragraphs. It must contain, in this order:

1. Project title, tagline and a one-paragraph overview.
2. Problem statement and motivation (why Kakuro, why it suits AI).
3. Objectives.
4. Kakuro rules with a small worked example.
5. AI formulation: Kakuro as a CSP (variables, domains, constraints, with the math).
6. System architecture: diagram, module-by-module description, data flow from UI -> API -> engine -> trace -> replay.
7. Algorithms explained simply, one subsection each: backtracking, MRV, Degree, LCV, constraint propagation, HumanLogicSolver. For each: intuition, pseudocode, small example, complexity (note CSP search is exponential in the worst case).
8. Novelty 1 in depth: the problem it solves, how it works (technique catalogue table, proof verifier, minimal conflict diagnosis), a worked example, why it is different from a normal solver or step log.
9. Novelty 2 in depth: the problem it solves, ambiguity-guided repair explained with a worked example, difficulty scoring formula, why it is better than random regeneration and clue-count difficulty.
10. Experimental methodology: setup, metrics, fairness controls, how to reproduce.
11. Results: REAL measured tables and charts produced by the scripts (insert them after running benchmarks), ablation analysis, repair-vs-random results, difficulty-correlation result, honest discussion of limitations.
12. Feature tour with screenshot placeholders for each page (list exactly which screenshots to capture and where they go).
13. Testing: what is tested, how to run it, coverage summary.
14. Installation and run instructions (exact commands, requirements, troubleshooting).
15. Presentation guide: a suggested slide-by-slide outline mapped to README sections, a 5-minute demo script using Demonstration Mode, and a list of likely professor questions with concise answers.
16. Future improvements, references (Russell & Norvig CSP chapter, Kakuro/CSP literature), and project structure tree.

Also create short docs in docs/: architecture.md, algorithms.md, benchmarking.md (the README can link to them, but the README itself must be self-sufficient).

---

# 12. TESTING (mandatory, automated)

- Rules: sums, duplicates, invalid digits, run lengths.
- CSP: domain init, consistency, elimination, forced assignments, propagation, contradiction detection, state restoration on backtrack.
- Every solver configuration, with all solvers agreeing on the solution across 300 random generated puzzles; cross-check against OR-tools CP-SAT in tests only.
- Uniqueness counter, unsolvable-puzzle detection.
- Generator: valid structure, valid clues, unique solution when requested, repair logic, difficulty classification.
- Novelty 1: every assignment and elimination has a valid justification; the verifier accepts valid traces and rejects corrupted ones; minimal-conflict explanations are actually shortest and actually contradictory; replay reconstructs correct intermediate states.
- Frontend: digit entry, keyboard navigation, undo/redo, hints, timer, completion detection, replay controls.
Target >85% coverage on core engine modules.

---

# 13. DATA AND PERSISTENCE

Built-in puzzles with metadata and verified solutions, game history, user stats, saved progress, stored benchmark results. No registration.

---

# 14. EXECUTION PHASES

1. Inspect repo, set up structure, commenting and docs conventions.
2. Kakuro model, runs, combinations table, validator + tests.
3. Baseline solver, heuristics (MRV, Degree, LCV), constraint propagation + tests.
4. Event trace, replay engine, explanation engine (three levels).
5. HumanLogicSolver, technique catalogue, independent verifier, minimal-conflict diagnosis, hints.
6. Puzzle generator, uniqueness counting, ambiguity-guided repair, difficulty scoring.
7. Strategy Arena, benchmark and experiment scripts, ablation.
8. Full frontend and API integration (Play, Solver Lab, Arena, Generator, Demonstration Mode).
9. Run all experiments, generate results and charts, write the full README and docs with REAL numbers.
10. Run the whole test suite, run backend and frontend, walk through every user journey, fix all errors, polish the UI.

After finishing: give exact launch commands, list anything not fully implemented, and summarize measured results.

---

# 15. FINAL ACCEPTANCE CHECKLIST

[ ] Complete playable Kakuro game with verified puzzles and difficulty levels
[ ] Real CSP engine: propagation, backtracking, MRV, Degree, LCV
[ ] Novelty 1: proof-carrying human-technique solver, independent verifier, minimal "Why is this wrong?"
[ ] Explainable reasoning timeline, candidate-elimination visualization, contradiction/backtracking explanations
[ ] Genuine step-by-step replay with state reconstruction
[ ] Novelty 2: ambiguity-guided generator, uniqueness validation, solver-derived difficulty
[ ] Strategy Arena with real benchmarking and ablation study
[ ] Experiments: repair vs random regeneration, difficulty-vs-effort correlation
[ ] Demonstration Mode using the real engine
[ ] Premium, responsive, award-quality UI
[ ] Clean, well-organized, thoroughly commented code
[ ] Detailed README suitable for building the presentation, plus docs/
[ ] All automated tests passing
[ ] Simple local run instructions

The two signature contributions are:
1. **Proof-carrying explainable solving with minimal conflict diagnosis.**
2. **Ambiguity-guided puzzle generation with solver-derived difficulty.**
Both must be deeply integrated into the application, not superficial extras.

Build the complete project now.