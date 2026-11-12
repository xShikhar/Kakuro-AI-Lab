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