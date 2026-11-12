# Algorithm walk-through

## Search

Each recursive node copies domains. Baseline visits cells in row order and tests only partial AllDifferent and attainable sum bounds. MRV dynamically computes legal values without mutating domains. Degree breaks equal-MRV ties by the number of unassigned neighbors. LCV orders values by the number of neighbor candidates made inconsistent under a tentative assignment. Propagation-only uses fixed row order plus generalized arc consistency. Full CSP combines propagation, MRV, degree and LCV. Human Logic applies ranked techniques to a fixed point before using explicit guesses.

Run consistency is necessary but not sufficient for global satisfiability. Exact tuple support means each retained candidate appears in a legal distinct-digit run assignment under current domains. Iterate these support reductions until no domain changes. Empty support proves a branch contradiction; singleton domains give forced assignments. Every final solution is checked against every clue and digit rule.

Search is exponential in the worst case, up to `9^n`. A length-k run has at most `9!/(9-k)!` tuples; materializing those tuples is expensive. GAC can spend more CPU per node than baseline, which the real benchmarks demonstrate. The wall-clock deadline is checked inside tuple recursion, not only between search nodes.

## Certificates

Every human reduction carries exact antecedent domains, ordered clue scopes, targets, a named technique, rank and resulting domain subsets. Seven techniques are implemented: unique combination, min/max bounds, combination-set union, run intersection, naked pairs/triples, mandatory-digit hidden singles and crossing-run tuple support.

The independent checker brute-force enumerates each premise run with its own recursion, then joins their information by iterated support filtering. It rejects deletion of any independently supported value. A full-trace check additionally binds premise domains to replay state and scopes/targets to the original board. It verifies deductions conditional on any earlier explicitly marked guesses. It does not claim that a guessed digit is a theorem, or that a technique label proves uniqueness.

## Diagnosis

Starting from clues and player entries, breadth-first search explores individual catalogue applications. The first dequeued contradiction has minimum deduction count in this catalogue graph (including the final contradiction step). Time/state caps may prevent a result; the response is then inconclusive, never a claim of correctness. A second bounded search enumerates clue subsets in increasing cardinality and decides each with complete custom CSP search. If it finishes at an unsatisfiable subset, it proves the minimum number of clues **conditional on the supplied player entries**. This is not a minimum joint set of clues and entry assumptions.

## Generation

Generate a valid connected mask, assign randomized digits obeying both runs, and derive sums. Count solutions up to two. If two exist, compare them cell by cell. Among disagreement cells, select a legal one-digit witness edit favoring fewer distinct digit combinations in the two affected runs. Update both clues consistently and count again. Track visited witness fills to avoid repair cycles. A repaired puzzle is accepted only after complete enumeration finds exactly one solution. Layout, repair, attempt and wall-time budgets prevent endless generation. Target mismatches are explicit.

Large grids (7–12) use connected short-run layouts to avoid factorial tuple tables. Repair mode reserves a bounded part of the same deadline for one fresh constructive short-run fill if random attempts never yield a rated unique puzzle. Both solution counting and human rating still run; recovery is identified in the response. See [generator reliability](generator-reliability.md). Original paired experiment outputs describe the earlier policy.

Score = sum of technique ranks + 10 × deepest guess level + 0.5 × number of technique applications. Calibrated 5×5 and 6×6 thresholds are empirical quintiles of 200 successful unique generations each. Other sizes currently use provisional thresholds and advertise `calibrated: false`.
