"""Run: python tests/run_tests.py   (from the repo root)
Writes tests/cases.jsonl (inputs), tests/actual_outputs.jsonl (outputs) and prints a report."""
import json, os, random, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src", "Python"))
sys.path.insert(0, HERE)
import algorithms as A
from main import handle
import checkers as C

passed = failed = 0
log_in, log_out = [], []


def record(name, ok, extra=""):
    global passed, failed
    passed += ok
    failed += (not ok)
    print(("PASS " if ok else "FAIL ") + name + (" " + extra if extra else ""))


def run(req, store=True):
    out = handle(json.loads(json.dumps(req)))
    if store:
        log_in.append(req); log_out.append(out)
    return out


def expect(name, req, want):
    out = run(req)
    record(name, out == want, "" if out == want else f"got {out} want {want}")


def validates(name, fn, *args, **kw):
    try:
        fn(*args, **kw)
        record(name, True)
    except C.Invalid as e:
        record(name, False, str(e))


def rejects(name, fn, *args, **kw):
    try:
        fn(*args, **kw)
        record(name, False, "checker accepted an invalid witness")
    except C.Invalid:
        record(name, True)


# ===================== 1. hand-justified cases =========================
print("== DSU ==")
expect("dsu spec example", {"task": "dsu", "n": 4, "operations": [[0, 1], [1, 2], [0, 2], [3, 3]]},
       {"states": [[3, 2], [2, 3], [2, 3], [2, 3]]})
expect("dsu n=0", {"task": "dsu", "n": 0, "operations": []}, {"states": []})
expect("dsu n=1 self-union (largest stays 1)", {"task": "dsu", "n": 1, "operations": [[0, 0]]}, {"states": [[1, 1]]})
expect("dsu repeated unions", {"task": "dsu", "n": 3, "operations": [[0, 1], [1, 0], [0, 1]]},
       {"states": [[2, 2], [2, 2], [2, 2]]})
expect("dsu no operations", {"task": "dsu", "n": 5, "operations": []}, {"states": []})
expect("dsu merge two big comps (rank!=size trap)",
       {"task": "dsu", "n": 6, "operations": [[0, 1], [2, 3], [3, 4], [0, 2], [5, 5]]},
       {"states": [[5, 2], [4, 2], [3, 3], [2, 5], [2, 5]]})

print("== Kruskal / Prim ==")
for t in ("kruskal", "prim"):
    out = run({"task": t, "n": 4, "edges": [[0, 1, 4], [1, 2, 2], [0, 2, 3]]})
    record(f"{t} spec example (cost 5, 2 comps)", out["cost"] == 5 and sorted(out["edge_ids"]) == [1, 2] and out["components"] == 2)
    expect(f"{t} n=0", {"task": t, "n": 0, "edges": []}, {"cost": 0, "edge_ids": [], "components": 0})
    expect(f"{t} isolated vertices only", {"task": t, "n": 3, "edges": []}, {"cost": 0, "edge_ids": [], "components": 3})
    out = run({"task": t, "n": 2, "edges": [[0, 0, -5], [0, 1, 7], [1, 1, -9]]})
    record(f"{t} self-loops with negative weight ignored", out["cost"] == 7 and out["edge_ids"] == [1])
    out = run({"task": t, "n": 2, "edges": [[0, 1, 5], [0, 1, 3], [1, 0, 3]]})
    record(f"{t} parallel edges pick weight 3", out["cost"] == 3 and len(out["edge_ids"]) == 1 and out["edge_ids"][0] in (1, 2))
    big = 10**9
    out = run({"task": t, "n": 5, "edges": [[0, 1, big], [1, 2, big], [2, 3, big], [3, 4, big], [0, 4, big]]})
    record(f"{t} total beyond 32 bits (4e9)", out["cost"] == 4 * big)
    out = run({"task": t, "n": 4, "edges": [[0, 1, -big], [1, 2, -big], [2, 3, -big]]})
    record(f"{t} negative total -3e9", out["cost"] == -3 * big)

print("== SCC ==")
out = run({"task": "scc", "n": 4, "edges": [[0, 1], [1, 0], [1, 2], [0, 2], [2, 3]]})
record("scc spec example", out["component"][0] == out["component"][1] and len({*out["component"]}) == 3 and len(out["condensation"]) == 2)
validates("scc spec example semantic", C.check_scc, 4, [[0, 1], [1, 0], [1, 2], [0, 2], [2, 3]], out)
expect("scc n=0", {"task": "scc", "n": 0, "edges": []}, {"component": [], "condensation": []})
out = run({"task": "scc", "n": 3, "edges": []})
record("scc isolates are separate SCCs", len(set(out["component"])) == 3 and out["condensation"] == [])
out = run({"task": "scc", "n": 2, "edges": [[0, 0], [0, 1], [0, 1], [0, 1]]})
record("scc self-loop + duplicate cross edges dedup'd", len(out["condensation"]) == 1)

print("== Topological order ==")
expect("topo spec example", {"task": "topo", "n": 4, "edges": [[0, 2], [1, 2], [2, 3]]}, {"acyclic": True, "order": [1, 0, 2, 3]})
expect("topo n=0", {"task": "topo", "n": 0, "edges": []}, {"acyclic": True, "order": []})
expect("topo self-loop is a cycle", {"task": "topo", "n": 2, "edges": [[1, 1]]}, {"acyclic": False, "order": []})
expect("topo 2-cycle", {"task": "topo", "n": 2, "edges": [[0, 1], [1, 0]]}, {"acyclic": False, "order": []})
out = run({"task": "topo", "n": 4, "edges": [[0, 1], [0, 2], [1, 3], [2, 3], [0, 3], [0, 1]]})
validates("topo diamond + shortcut + duplicate edge (finished-vertex edge is NOT a cycle)", C.check_topo, 4,
          [[0, 1], [0, 2], [1, 3], [2, 3], [0, 3], [0, 1]], out, True)
out = run({"task": "topo", "n": 6, "edges": [[4, 5], [5, 4]]})
record("topo cycle in a later component is found", out["acyclic"] is False)

print("== DAG shortest paths ==")
req = {"task": "dag", "n": 5, "source": 0, "edges": [[0, 1, 3], [0, 2, 8], [1, 2, -7], [2, 3, 4]]}
expect("dag spec example", req, {"acyclic": True, "distance": [0, 3, -4, 0, None], "parent_edge": [-1, 0, 2, 3, -1]})
expect("dag n=1", {"task": "dag", "n": 1, "source": 0, "edges": []}, {"acyclic": True, "distance": [0], "parent_edge": [-1]})
expect("dag cycle unreachable from source still rejected",
       {"task": "dag", "n": 3, "source": 0, "edges": [[1, 2, 1], [2, 1, 1]]}, {"acyclic": False, "distance": [], "parent_edge": []})
expect("dag self-loop is cyclic", {"task": "dag", "n": 2, "source": 0, "edges": [[1, 1, 0]]},
       {"acyclic": False, "distance": [], "parent_edge": []})
out = run({"task": "dag", "n": 4, "source": 0, "edges": [[1, 2, -100], [0, 3, 1]]})
record("dag never relaxes from unreachable vertex (1->2 weight -100 ignored)", out["distance"] == [0, None, None, 1])
out = run({"task": "dag", "n": 3, "source": 0, "edges": [[0, 1, -1], [1, 2, -1]]})
record("dag finite distance -1 is not 'unreachable'", out["distance"] == [0, -1, -2])
out = run({"task": "dag", "n": 5, "source": 2, "edges": [[0, 1, 1], [2, 3, 10**9], [3, 4, 10**9]]})
record("dag distance beyond 32 bits (2e9), source not vertex 0", out["distance"] == [None, None, 0, 10**9, 2 * 10**9])

print("== Route helper ==")
edges = [[0, 1, 3], [0, 2, 8], [1, 2, -7], [2, 3, 4]]
r = run(req)
pe = r["parent_edge"]
rt = A.route(0, 3, pe, edges)
record("route reachable 0->3 == [0,1,2,3]", rt == [0, 1, 2, 3])
record("route weight along path == distance (0)", sum(w for (u, v, w) in (edges[i] for i in [0, 2, 3])) == r["distance"][3])
record("route to source == [source]", A.route(0, 0, pe, edges) == [0])
record("route to unreachable vertex 4 == [] (documented)", A.route(0, 4, pe, edges) == [])
tied = [[0, 1, 5], [0, 1, 5], [0, 2, 1], [2, 1, 4]]       # three tied routes to vertex 1, parallel edges 0 and 1
r2 = run({"task": "dag", "n": 3, "source": 0, "edges": tied})
rt2 = A.route(0, 1, r2["parent_edge"], tied)
def _route_cost(rt_, pe_, es):
    return sum(es[pe_[v]][2] for v in rt_[1:])        # each vertex's chosen incoming edge


ok = (r2["distance"][1] == 5 and r2["parent_edge"][1] in (0, 1, 3)
      and rt2[0] == 0 and rt2[-1] == 1
      and all(tied[r2["parent_edge"][v]][1] == v for v in rt2[1:])      # every chosen edge ends at its vertex
      and all(tied[r2["parent_edge"][v]][0] == rt2[k] for k, v in enumerate(rt2[1:])) # and starts at the previous vertex
      and _route_cost(rt2, r2["parent_edge"], tied) == 5)                # route cost equals distance
record(f"route with tied/parallel edges (selected id {r2['parent_edge'][1]}, route {rt2})", ok)
validates("tied/parallel dag witness valid", C.check_dag, 3, tied, 0, r2)

print("== Checker sanity: accepts alternative valid answers, rejects invalid witnesses ==")
E = [[0, 1, 4], [1, 2, 2], [0, 2, 3]]
validates("msf accepts ids [1,2]", C.check_msf, 4, E, {"cost": 5, "edge_ids": [1, 2], "components": 2}, 5)
validates("msf accepts alternative order [2,1]", C.check_msf, 4, E, {"cost": 5, "edge_ids": [2, 1], "components": 2}, 5)
rejects("msf rejects suboptimal forest {0,1}", C.check_msf, 4, E, {"cost": 6, "edge_ids": [0, 1], "components": 2}, 5)
rejects("msf rejects wrong cost claim", C.check_msf, 4, E, {"cost": 4, "edge_ids": [1, 2], "components": 2}, 5)
rejects("msf rejects cycle edges", C.check_msf, 4, E, {"cost": 9, "edge_ids": [0, 1, 2], "components": 2})
S = [[0, 1], [1, 0], [1, 2]]
validates("scc accepts labels [9,9,2]", C.check_scc, 3, S, {"component": [9, 9, 2], "condensation": [[9, 2]]})
rejects("scc rejects merged labels", C.check_scc, 3, S, {"component": [1, 1, 1], "condensation": []})
rejects("scc rejects missing condensation edge", C.check_scc, 3, S, {"component": [0, 0, 1], "condensation": []})
rejects("scc rejects duplicate condensation pair", C.check_scc, 3, S, {"component": [0, 0, 1], "condensation": [[0, 1], [0, 1]]})
T = [[0, 2], [1, 2], [2, 3]]
validates("topo accepts [0,1,2,3]", C.check_topo, 4, T, {"acyclic": True, "order": [0, 1, 2, 3]}, True)
rejects("topo rejects [2,0,1,3]", C.check_topo, 4, T, {"acyclic": True, "order": [2, 0, 1, 3]}, True)
D = {"acyclic": True, "distance": [0, 3, -4, 0, None], "parent_edge": [-1, 0, 2, 3, -1]}
validates("dag accepts the spec answer", C.check_dag, 5, edges + [], 0, D)
bad = dict(D, parent_edge=[-1, 0, 1, 3, -1])         # edge 1 is 0->2 weight 8: not tight
rejects("dag rejects non-tight parent edge", C.check_dag, 5, edges, 0, bad)
bad = dict(D, parent_edge=[-1, 0, 2, 2, -1])         # edge 2 ends at 2, not 3
rejects("dag rejects parent edge not ending at vertex", C.check_dag, 5, edges, 0, bad)

# ===================== 2. randomized differential tests ================
print("== Randomized differential tests (seeded) ==")
rnd = random.Random(20260101)
fails = 0
for it in range(400):
    n = rnd.randint(0, 7)
    m = rnd.randint(0, 9) if n else 0
    ue = [[rnd.randrange(n), rnd.randrange(n), rnd.randint(-5, 5)] for _ in range(m)]
    de = [[e[0], e[1]] for e in ue]
    ops = [[rnd.randrange(n), rnd.randrange(n)] for _ in range(m)]
    try:
        opt = C.msf_cost_bruteforce(n, ue) if len(ue) <= 9 else None
        for t in ("kruskal", "prim"):
            C.check_msf(n, ue, run({"task": t, "n": n, "edges": ue}, store=it < 20), opt)
        C.check_scc(n, de, run({"task": "scc", "n": n, "edges": de}, store=it < 20))
        cyc = C.has_cycle_bruteforce(n, de)
        C.check_topo(n, de, run({"task": "topo", "n": n, "edges": de}, store=it < 20), not cyc)
        C.check_dsu(n, ops, run({"task": "dsu", "n": n, "operations": ops}, store=it < 20))
        if n:
            s = rnd.randrange(n)
            # make DAGs likely: half of the iterations orient edges low->high
            if it % 2 == 0:
                ue2 = [[min(a, b), max(a, b), w] for a, b, w in ue if a != b]
            else:
                ue2 = ue
            ref = {"cyclic": C.has_cycle_bruteforce(n, [[a, b] for a, b, _ in ue2]),
                   "dist": C.bellman_ford(n, ue2, s)}
            out = run({"task": "dag", "n": n, "source": s, "edges": ue2}, store=it < 20)
            if ref["cyclic"] is False:
                C.check_dag(n, ue2, s, out, ref)
            else:
                C.check_dag(n, ue2, s, out, ref)
    except C.Invalid as e:
        fails += 1
        print("  mismatch:", n, ue, e)
record("400 random small instances: all six methods vs brute-force oracles", fails == 0)

# ===================== 3. state reset: mixed batch repeated ===========
print("== State reset: mixed requests repeated in ONE process ==")
batch = [{"task": "ping"},
         {"task": "dsu", "n": 5, "operations": [[0, 1], [2, 3], [1, 3]]},
         {"task": "dsu", "n": 5, "operations": [[4, 4]]},
         {"task": "kruskal", "n": 4, "edges": E},
         {"task": "prim", "n": 4, "edges": E},
         {"task": "scc", "n": 4, "edges": [[0, 1], [1, 0], [2, 3]]},
         {"task": "topo", "n": 3, "edges": [[0, 1], [1, 2], [2, 0]]},
         {"task": "topo", "n": 3, "edges": [[0, 1]]},
         req, {"task": "dag", "n": 1, "source": 0, "edges": []}]
first = [handle(b) for b in batch]
again = [handle(b) for _ in range(3) for b in batch]
record("three further repeats identical to first pass", again == first * 3)
log_in.extend(batch); log_out.extend(first)

# ===================== 4. large / deep inputs (limits) ================
print("== Large inputs at published limits ==")
N, M = 100000, 250000
rg = random.Random(7)


def timed(name, req, check=None):
    t0 = time.perf_counter()
    out = handle(json.loads(json.dumps(req)))
    dt = time.perf_counter() - t0
    ok = True
    if check:
        try:
            check(out)
        except (C.Invalid, AssertionError) as e:
            ok = False
            print("   ", e)
    record(f"{name}", ok, f"[{dt:.2f}s incl. request JSON round-trip]")
    return out


big_u = [[rg.randrange(N), rg.randrange(N), rg.randint(-10**9, 10**9)] for _ in range(M)]
ops = [[rg.randrange(N), rg.randrange(N)] for _ in range(250000)]


def chk_dsu(o):
    s = o["states"]
    assert len(s) == 250000 and s[-1][0] == components_after(ops) , "final components wrong"
    assert all(s[i][0] >= s[i + 1][0] for i in range(len(s) - 1)), "components not monotone"
    assert all(s[i][1] <= s[i + 1][1] for i in range(len(s) - 1)), "largest not monotone"


def components_after(ops_):
    return C.components_bruteforce(N, ops_)


timed("dsu n=1e5 q=250000", {"task": "dsu", "n": N, "operations": ops}, chk_dsu)
ok_cost = {}
o1 = timed("kruskal n=1e5 m=250000 random weights ±1e9", {"task": "kruskal", "n": N, "edges": big_u},
           lambda o: C.check_msf(N, big_u, o))
o2 = timed("prim    n=1e5 m=250000 random weights ±1e9", {"task": "prim", "n": N, "edges": big_u},
           lambda o: C.check_msf(N, big_u, o, o1["cost"]))
record("kruskal and prim agree on cost and components at scale", o1["cost"] == o2["cost"] and o1["components"] == o2["components"])

big_d = [[rg.randrange(N), rg.randrange(N)] for _ in range(M)]


def tarjan_labels(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
    idx = [-1] * n; low = [0] * n; on = [False] * n; st = []; comp = [-1] * n; c = 0; counter = 0
    for s in range(n):
        if idx[s] != -1:
            continue
        work = [(s, 0)]
        idx[s] = low[s] = counter; counter += 1; st.append(s); on[s] = True
        while work:
            v, i = work[-1]
            if i < len(adj[v]):
                work[-1] = (v, i + 1)
                w = adj[v][i]
                if idx[w] == -1:
                    idx[w] = low[w] = counter; counter += 1; st.append(w); on[w] = True
                    work.append((w, 0))
                elif on[w]:
                    low[v] = min(low[v], idx[w])
            else:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[v])
                if low[v] == idx[v]:
                    while True:
                        w = st.pop(); on[w] = False; comp[w] = c
                        if w == v:
                            break
                    c += 1
    return comp


def chk_scc_big(o):
    ref = tarjan_labels(N, big_d)
    mp = {}
    for a, b in zip(o["component"], ref):
        assert mp.setdefault(a, b) == b, "partition differs from Tarjan oracle"
    assert len(set(o["component"])) == len(set(ref)), "partition differs from Tarjan oracle"
    want = {(o["component"][u], o["component"][v]) for u, v in big_d if o["component"][u] != o["component"][v]}
    got = [tuple(p) for p in o["condensation"]]
    assert len(got) == len(set(got)) and set(got) == want, "condensation wrong"


timed("scc random n=1e5 m=250000 (vs independent iterative Tarjan)", {"task": "scc", "n": N, "edges": big_d}, chk_scc_big)

chain = [[i, i + 1] for i in range(N - 1)]
o = timed("scc deep chain n=1e5 (all singletons)", {"task": "scc", "n": N, "edges": chain},
          lambda o: (_ for _ in ()).throw(C.Invalid("labels")) if len(set(o["component"])) != N or len(o["condensation"]) != N - 1 else None)
ring = chain + [[N - 1, 0]]
timed("scc one huge cycle n=1e5 (single SCC)", {"task": "scc", "n": N, "edges": ring},
      lambda o: (_ for _ in ()).throw(C.Invalid("not one SCC")) if len(set(o["component"])) != 1 or o["condensation"] else None)


def chk_chain_topo(o):
    assert o["acyclic"] and o["order"] == list(range(N)), "chain order must be 0..n-1"


timed("topo deep chain n=1e5", {"task": "topo", "n": N, "edges": chain}, chk_chain_topo)
timed("topo chain closed into a ring (cycle at depth 1e5)", {"task": "topo", "n": N, "edges": ring},
      lambda o: (_ for _ in ()).throw(C.Invalid("should be cyclic")) if o["acyclic"] or o["order"] else None)
rev_chain = [[i + 1, i] for i in range(N - 1)]
timed("topo reversed deep chain n=1e5", {"task": "topo", "n": N, "edges": rev_chain},
      lambda o: (_ for _ in ()).throw(C.Invalid("order")) if o["order"] != list(range(N - 1, -1, -1)) else None)

wchain = [[i, i + 1, -(10**9)] for i in range(N - 1)]


def chk_dag_chain(o):
    assert o["acyclic"] and o["distance"][N - 1] == -(10**9) * (N - 1), "chain distance (≈ -1e14) wrong"
    assert o["parent_edge"][N - 1] == N - 2 and o["parent_edge"][0] == -1


timed("dag chain n=1e5 weights -1e9 (distance -9.9999e13)", {"task": "dag", "n": N, "source": 0, "edges": wchain}, chk_dag_chain)
dag_edges = []
for _ in range(M):
    a, b = rg.randrange(N), rg.randrange(N)
    if a != b:
        dag_edges.append([min(a, b), max(a, b), rg.randint(-10**9, 10**9)])


def chk_dag_big(o):
    ref_d = [None] * N
    ref_d[0] = 0
    for i in sorted(range(len(dag_edges)), key=lambda i: dag_edges[i][0]):   # edges are low->high, so by tail index
        u, v, w = dag_edges[i]
        if ref_d[u] is not None and (ref_d[v] is None or ref_d[u] + w < ref_d[v]):
            ref_d[v] = ref_d[u] + w
    assert o["distance"] == ref_d, "distances differ from independent index-order DP"
    C.check_dag(N, dag_edges, 0, o)


timed("dag random DAG n=1e5 m≈250000 (vs index-order DP + witness check)",
      {"task": "dag", "n": N, "source": 0, "edges": dag_edges}, chk_dag_big)
cyc_edges = dag_edges + [[N - 1, N - 2, 0], [N - 2, N - 1, 0]]
timed("dag cycle hidden far from the source", {"task": "dag", "n": N, "source": 0, "edges": cyc_edges},
      lambda o: (_ for _ in ()).throw(C.Invalid("should be cyclic")) if o["acyclic"] else None)

# ===================== 5. end-to-end CLI with mixed batch ==============
print("== End-to-end through main.py (stdin/stdout), batch twice in one process ==")
lines = "\n".join(json.dumps(x, separators=(",", ":")) for x in batch + batch) + "\n"
p = subprocess.run([sys.executable, os.path.join(ROOT, "src", "Python", "main.py")], input=lines, capture_output=True, text=True)
outs = [json.loads(l) for l in p.stdout.splitlines()]
record("CLI returns one line per request, stdout clean", p.returncode == 0 and len(outs) == 2 * len(batch) and p.stderr == "")
record("CLI second pass equals first pass", outs[:len(batch)] == outs[len(batch):] and outs[0] == {"status": "ready"})

with open(os.path.join(HERE, "cases.jsonl"), "w") as f:
    for x in log_in:
        f.write(json.dumps(x, separators=(",", ":")) + "\n")
with open(os.path.join(HERE, "actual_outputs.jsonl"), "w") as f:
    for x in log_out:
        f.write(json.dumps(x, separators=(",", ":")) + "\n")
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
