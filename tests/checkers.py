"""Semantic validators for non-unique answers + independent brute-force oracles."""
import itertools
from collections import deque


class Invalid(Exception):
    pass


def _need(cond, msg):
    if not cond:
        raise Invalid(msg)


# ---- oracles (deliberately different algorithms from the solution) ----
def components_bruteforce(n, edges):
    adj = [[] for _ in range(n)]
    for e in edges:
        adj[e[0]].append(e[1]); adj[e[1]].append(e[0])
    seen = [False] * n
    c = 0
    for s in range(n):
        if not seen[s]:
            c += 1
            seen[s] = True
            q = deque([s])
            while q:
                x = q.popleft()
                for y in adj[x]:
                    if not seen[y]:
                        seen[y] = True
                        q.append(y)
    return c


def msf_cost_bruteforce(n, edges):
    """Try every subset of edges (tiny graphs): min-cost acyclic subset with n-c edges."""
    c = components_bruteforce(n, edges)
    need = n - c
    best = None
    for sub in itertools.combinations(range(len(edges)), need):
        if _is_forest(n, edges, sub):
            cost = sum(edges[i][2] for i in sub)
            if best is None or cost < best:
                best = cost
    return best if best is not None else 0


def _is_forest(n, edges, ids):
    p = list(range(n))
    def f(x):
        while p[x] != x:
            p[x] = p[p[x]]; x = p[x]
        return x
    for i in ids:
        a, b = f(edges[i][0]), f(edges[i][1])
        if a == b:
            return False
        p[a] = b
    return True


def reach_matrix(n, edges):
    r = [[i == j for j in range(n)] for i in range(n)]
    for u, v in edges:
        r[u][v] = True
    for k in range(n):
        for i in range(n):
            if r[i][k]:
                for j in range(n):
                    if r[k][j]:
                        r[i][j] = True
    return r


def bellman_ford(n, edges, s):
    INF = None
    d = [INF] * n
    d[s] = 0
    for _ in range(n):
        for u, v, w in edges:
            if d[u] is not INF and (d[v] is INF or d[u] + w < d[v]):
                d[v] = d[u] + w
    return d


def has_cycle_bruteforce(n, edges):
    r = reach_matrix(n, edges)
    return any(r[v][u] for u, v in edges)


# ---- validators -------------------------------------------------------
def check_msf(n, edges, out, expected_cost=None):
    ids = out["edge_ids"]
    _need(len(set(ids)) == len(ids), "repeated edge id")
    _need(all(0 <= i < len(edges) for i in ids), "edge id out of range")
    _need(all(edges[i][0] != edges[i][1] for i in ids), "self-loop selected")
    c = components_bruteforce(n, edges)
    _need(out["components"] == c, f"components {out['components']} != {c}")
    _need(len(ids) == n - c, "forest must have n-c edges")
    _need(_is_forest(n, edges, ids), "selected edges contain a cycle")
    _need(out["cost"] == sum(edges[i][2] for i in ids), "cost != sum of selected weights")
    if expected_cost is not None:
        _need(out["cost"] == expected_cost, f"cost {out['cost']} != optimum {expected_cost}")


def check_scc(n, edges, out):
    comp = out["component"]
    _need(len(comp) == n and all(isinstance(x, int) and x >= 0 for x in comp), "bad labels")
    r = reach_matrix(n, edges)
    for i in range(n):
        for j in range(n):
            same = r[i][j] and r[j][i]
            _need(same == (comp[i] == comp[j]), f"vertices {i},{j}: SCC membership wrong")
    want = {(comp[u], comp[v]) for u, v in edges if comp[u] != comp[v]}
    got = [tuple(p) for p in out["condensation"]]
    _need(len(got) == len(set(got)), "duplicate condensation pair")
    _need(set(got) == want, "condensation edge set wrong")


def check_topo(n, edges, out, expect_acyclic=None):
    if expect_acyclic is not None:
        _need(out["acyclic"] == expect_acyclic, "acyclic flag wrong")
    if not out["acyclic"]:
        _need(out["order"] == [], "cyclic graph must return order=[]")
        return
    o = out["order"]
    _need(sorted(o) == list(range(n)), "order is not a permutation")
    pos = {v: i for i, v in enumerate(o)}
    for u, v in edges:
        _need(pos[u] < pos[v], f"edge {u}->{v} goes backwards")


def check_dag(n, edges, source, out, ref=None):
    cyc = ref["cyclic"] if ref else None
    if not out["acyclic"]:
        _need(out["distance"] == [] and out["parent_edge"] == [], "cyclic must return empty arrays")
        if cyc is not None:
            _need(cyc, "reported cyclic but graph is acyclic")
        return
    if cyc is not None:
        _need(not cyc, "reported acyclic but graph has a cycle")
    d, pe = out["distance"], out["parent_edge"]
    _need(len(d) == n and len(pe) == n, "array length")
    if ref:
        _need(d == ref["dist"], "distances differ from Bellman-Ford")
    _need(d[source] == 0 and pe[source] == -1, "source entry wrong")
    for v in range(n):
        if v == source:
            continue
        if d[v] is None:
            _need(pe[v] == -1, "unreachable vertex must have parent -1")
            continue
        i = pe[v]
        _need(0 <= i < len(edges) and edges[i][1] == v, f"parent edge of {v} does not end at it")
        u = edges[i][0]
        _need(d[u] is not None and d[u] + edges[i][2] == d[v], f"parent edge of {v} not tight")
        # follow parents to source (bounded)
        x, steps = v, 0
        while x != source:
            x = edges[pe[x]][0]
            steps += 1
            _need(steps <= n, "parent chain does not reach source")


def check_dsu(n, ops, out):
    p = list(range(n))
    def f(x):
        while p[x] != x:
            p[x] = p[p[x]]; x = p[x]
        return x
    want = []
    for u, v in ops:
        a, b = f(u), f(v)
        if a != b:
            p[a] = b
        roots = {}
        for x in range(n):
            roots[f(x)] = roots.get(f(x), 0) + 1
        want.append([len(roots), max(roots.values()) if roots else 0])
    _need(out["states"] == want, "DSU states differ from naive recomputation")
