# Tests

All commands are run from the repository root. No packages need to be installed.

## How to run

```sh
python tests/run_tests.py                       # full suite: 75 checks, prints PASS/FAIL, exits 1 on failure
python tools/run.py --input tests/cases.jsonl   # feed my inputs through the supplied launcher (prints actual results)
python tools/benchmark.py                       # Kruskal vs Prim benchmark (see ANALYSIS.md, section 9)
```

## Files

| File | Content |
|---|---|
| `run_tests.py` | The test suite. Calls the supplied `main.handle` and the route helper `algorithms.route` directly |
| `checkers.py` | Semantic validators for non-unique answers and independent brute-force oracles |
| `cases.jsonl` | Inputs (JSON Lines) that the suite sent to the program |
| `actual_outputs.jsonl` | Actual outputs; line *i* answers line *i* of `cases.jsonl` |
| `test_report.txt` | PASS/FAIL log of the last run |
| `benchmark_output.txt`, `benchmark_results.json` | Raw Kruskal vs Prim timings |

## What is tested

* **Hand-justified cases.** All six examples from the assignment, plus `n=0`, `n=1`, isolated vertices, repeated and self unions,
  self-loops with negative weights, parallel and tied edges, totals beyond 32 bits (4·10⁹, −3·10⁹, 2·10⁹), a cycle unreachable
  from the DAG source, a cycle in a later component, and a negative edge leaving an unreachable vertex. Expected values were
  derived by hand (for example the spanning forest of the example triangle uses the weights 2 and 3, so cost 5; the route
  0→1→2→3 costs 3 − 7 + 4 = 0).
* **Route helper.** Reachable target (`[0,1,2,3]`), the source (`[0]`), an unreachable target (`[]`, the documented no-route result),
  and tied/parallel edges (every chosen edge ends at its vertex, starts at the previous vertex, route cost equals the distance).
* **Checker sanity.** The checkers accept alternative valid answers (other edge-ID order, other SCC labels, other topological order)
  and reject invalid witnesses (suboptimal forest, wrong cost, cycle in the forest, merged SCCs, missing or duplicate condensation
  pair, backward topological order, parent edge that is not tight or does not end at its vertex).
* **Randomized differential tests.** 400 seeded random instances with `n ≤ 7`, compared against methods different from the
  solution: subset search for the minimum spanning forest, Floyd–Warshall reachability for SCC and cycles, naive recomputation for
  DSU, Bellman–Ford for DAG distances.
* **State reset.** A mixed batch of all six methods runs three more times in one process; the supplied `main.py` is also run through
  stdin/stdout with the batch twice in one process and the outputs must match.
* **Limits.** n = 10⁵ with m or q up to 2.5·10⁵: DSU, Kruskal and Prim (equal cost, valid forest), random SCC (against an
  independent iterative Tarjan), chains and a ring of 10⁵ vertices for SCC and topological order, a DAG chain with weights −10⁹
  (distance about −10¹⁴), a random DAG (against an independent DP), and a cycle hidden far from the source.