# Verification and remaining limitations

## Evidence

- 345 backend tests passed, including 300 independent CP-SAT cross-checks over all seven strategies, generator recovery regressions and full trace-integrity regressions.
- Core/model/solver/generator line coverage: 95% (698/733 statements); see `results/coverage.json`.
- Thirteen frontend tests cover entries, notes, undo/redo, navigation, candidate rendering, pause state, replay stepping, timer persistence, completion history, puzzle-content identity, stale help responses, failed-proof UI and truthful generation-failure states.
- Vite production build passed. Local frontend and backend readiness checks returned HTTP 200.
- Final live HTTP smoke test passed all service flows: Expert human stream (102 actual events, 86/86 verified deductions/forced assignments, four assumptions), three escalating hints, completion/mistake checking, shortest diagnosis, seven-strategy arena, unique generation and real chart/CSV downloads. See `results/live-smoke.json`; reproduce with `python -m scripts.smoke` while both services run.
- 800 paired generator runs, plus supplemental accepted calibration samples. 400 unique puzzles supply the difficulty/effort analysis.
- After the generator reliability fix, 80/80 generation requests (seeds 0–9, sizes 5–12) returned unique puzzles within a three-second cap. Eight actual HTTP requests at seed 42 returned valid unique puzzles in 21–743 ms, including the previously failing 12×12 size. Raw regression observations are in `results/generator-regression.json` and `results/generator-live-regression.json`. These are regression samples, not replacements for the historical paired experiment.

## Browser QA limit

The in-app browser tool timed out on its Statsig initialization. A native Chrome fallback was then stopped by the Computer Use tool because it could not confidently determine the current Windows browser URL for its safety checks. No browser input continued after that stop. Therefore visual, mobile viewport, console and full browser-journey QA are **unverified**. DOM interaction tests and real API integration tests passed, but they do not substitute for rendered browser inspection. Capture the README's six screenshots and test 320/768/1024/1440px before presenting.

## Explicit scope limits

- Empirical calibration covers sizes 5 and 6, with 200 successful puzzles per size. Sizes 7–12 are supported under generation caps but use provisional thresholds, and larger unique generation can exhaust its budget. No 200-puzzle-per-size calibration or success-rate claim is made for those sizes.
- Diagnosis certifies a shortest chain in the implemented technique catalogue, not among all possible mathematical proofs. The separate minimum clue core is conditional on fixed player entries, not a minimum joint set of entry assumptions and clues. Both can return inconclusive under caps.
- The independent verifier checks local entailment of deductions under recorded assumptions. Search guesses are counted separately and are not presented as formally proved assignments.
- Difficulty classes are per-size quintiles from this generator. They are not validated against human participants, and the 300-oracle sample consists of small generated puzzles.
- Arena uses single runs and high-level run-check counts. CPU caches, background load and tuple work affect elapsed time; there are no confidence intervals or multi-process CPU jobs.
- No automated accessibility audit or rendered mobile QA was possible in this environment. Semantic controls, keyboard handlers, reduced-motion support and responsive CSS are implemented but full WCAG certification is not claimed.

The project is usable locally and its algorithmic results are real. It should not be described as satisfying every requested research validation or production acceptance item until these limits are addressed.

## Final review fixes

A separate read-only review found four important issues: generated save-key collisions, stale reveal responses, completed-game undo locking and uncertified trace mutations. Regression tests reproduced the failures; all were corrected. Hint level three now reveals a digit only after uniqueness checking, across-run reveal filters the correct direction, and the UI includes the actual paired generation comparison. The demonstration selection is tested to contain real propagation, heuristic decisions, backtracking and a validated final solution.
