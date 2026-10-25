"""Kruskal vs Prim on identical graphs.  Run from repo root: python tools/benchmark.py
Timer: time.perf_counter().  Boundary: the algorithm function on an already-parsed
in-memory edge list (adjacency/DSU construction and sorting INSIDE the function are
counted for both; JSON parsing and stdout are NOT counted for either)."""
import os, platform, random, statistics, sys, time, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "Python"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))
from algorithms import kruskal, prim
import checkers as C

SEED = 12345
SIZES = [(10_000, 25_000), (50_000, 125_000), (100_000, 250_000)]
REPS = 5
rows = []
for n, m in SIZES:
    rg = random.Random(SEED + n)
    edges = [[rg.randrange(n), rg.randrange(n), rg.randint(-10**9, 10**9)] for _ in range(m)]
    R = {"n": n, "edges": edges}
    k, p = kruskal(R), prim(R)
    assert k["cost"] == p["cost"] and k["components"] == p["components"], "cost/components mismatch"
    C.check_msf(n, edges, k); C.check_msf(n, edges, p, k["cost"])      # valid forests, optimum cost
    kruskal(R); prim(R)                                  # warm-up (not recorded)
    tk, tp = [], []
    for _ in range(REPS):                                              # interleaved to cancel drift
        t = time.perf_counter(); kruskal(R); tk.append(time.perf_counter() - t)
        t = time.perf_counter(); prim(R);    tp.append(time.perf_counter() - t)
    rows.append(dict(n=n, m=m, cost=k["cost"], components=k["components"],
                     kruskal=[round(x, 4) for x in tk], kruskal_median=round(statistics.median(tk), 4),
                     prim=[round(x, 4) for x in tp], prim_median=round(statistics.median(tp), 4)))
    print(json.dumps(rows[-1]))
print(f"\nPython {platform.python_version()} on {platform.platform()}")
json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "benchmark_results.json"), "w"), indent=1)
print("| n | m | Kruskal runs (s) | Kruskal median | Prim runs (s) | Prim median |\n|---|---|---|---|---|---|")
for r in rows:
    print(f"| {r['n']} | {r['m']} | {', '.join(map(str, r['kruskal']))} | {r['kruskal_median']} | {', '.join(map(str, r['prim']))} | {r['prim_median']} |")
