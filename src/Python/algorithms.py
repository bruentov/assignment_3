"""Graph algorithms for Assignment 3 (Python 3.12).

All traversals are iterative (no recursion), so 100000-vertex chains are safe.
Every function is pure: it builds all of its state locally, so nothing leaks
between requests handled by the same process.
"""
import heapq


# ---------------------------------------------------------------- 3. DSU
def _dsu(n, operations):
    parent = list(range(n))
    size = [1] * n

    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:           # path compression
            parent[x], x = root, parent[x]
        return root

    components = n
    largest = 1 if n > 0 else 0
    states = []
    for u, v in operations:
        ru, rv = find(u), find(v)
        if ru != rv:
            if size[ru] < size[rv]:        # union by size
                ru, rv = rv, ru
            parent[rv] = ru
            size[ru] += size[rv]
            components -= 1
            if size[ru] > largest:
                largest = size[ru]
        states.append([components, largest])
    return {"states": states}


# ------------------------------------------------------------ 4. Kruskal
def _kruskal(n, edges):
    parent = list(range(n))
    size = [1] * n

    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    order = sorted(range(len(edges)), key=lambda i: edges[i][2])
    cost = 0
    chosen = []
    for i in order:
        u, v, w = edges[i]
        ru, rv = find(u), find(v)
        if ru != rv:                       # self-loops give ru == rv
            if size[ru] < size[rv]:
                ru, rv = rv, ru
            parent[rv] = ru
            size[ru] += size[rv]
            cost += w
            chosen.append(i)
    return {"cost": cost, "edge_ids": chosen, "components": n - len(chosen)}


# --------------------------------------------------------------- 4. Prim
def _prim(n, edges):
    # Adjacency in CSR form: arcs of vertex x are start[x]..start[x+1]-1.
    deg = [0] * (n + 1)
    for u, v, _ in edges:
        if u != v:
            deg[u] += 1
            deg[v] += 1
    start = [0] * (n + 1)
    for x in range(n):
        start[x + 1] = start[x] + deg[x]
    fill = start[:n]
    total = start[n]
    to = [0] * total
    eid = [0] * total
    for i, (u, v, _) in enumerate(edges):
        if u != v:                          # self-loops never enter the forest
            p = fill[u]; to[p] = v; eid[p] = i; fill[u] = p + 1
            p = fill[v]; to[p] = u; eid[p] = i; fill[v] = p + 1

    visited = [False] * n
    cost = 0
    chosen = []
    components = 0
    push, pop = heapq.heappush, heapq.heappop
    for s in range(n):
        if visited[s]:
            continue
        components += 1
        visited[s] = True
        heap = [(edges[eid[p]][2], eid[p], to[p]) for p in range(start[s], start[s + 1])]
        heapq.heapify(heap)
        while heap:
            w, i, v = pop(heap)
            if visited[v]:
                continue
            visited[v] = True
            cost += w
            chosen.append(i)
            for p in range(start[v], start[v + 1]):
                if not visited[to[p]]:
                    j = eid[p]
                    push(heap, (edges[j][2], j, to[p]))
    return {"cost": cost, "edge_ids": chosen, "components": components}


# ------------------------------------------------------- shared helpers
def _csr(n, edges):
    """Forward adjacency as (start, to, edge_id) arrays."""
    start = [0] * (n + 1)
    for e in edges:
        start[e[0] + 1] += 1
    for x in range(n):
        start[x + 1] += start[x]
    fill = start[:n]
    to = [0] * len(edges)
    eid = [0] * len(edges)
    for i, e in enumerate(edges):
        p = fill[e[0]]
        to[p] = e[1]
        eid[p] = i
        fill[e[0]] = p + 1
    return start, to, eid


# --------------------------------------------------------------- 5. SCC
def _scc(n, edges):
    """Kosaraju: pass 1 on G gives finish order, pass 2 on G^T in reverse."""
    start, to, _ = _csr(n, edges)
    rev = [[e[1], e[0]] for e in edges]
    rstart, rto, _ = _csr(n, rev)

    # Pass 1: iterative DFS on G, record finish order.
    seen = [False] * n
    ptr = start[:n]                         # next unexplored arc per vertex
    finish = []
    for s in range(n):
        if seen[s]:
            continue
        seen[s] = True
        stack = [s]
        while stack:
            x = stack[-1]
            p = ptr[x]
            if p < start[x + 1]:
                ptr[x] = p + 1
                y = to[p]
                if not seen[y]:
                    seen[y] = True
                    stack.append(y)
            else:
                finish.append(x)
                stack.pop()

    # Pass 2: DFS on the transpose in decreasing finish order.
    comp = [-1] * n
    label = 0
    for s in reversed(finish):
        if comp[s] != -1:
            continue
        comp[s] = label
        stack = [s]
        while stack:
            x = stack.pop()
            for p in range(rstart[x], rstart[x + 1]):
                y = rto[p]
                if comp[y] == -1:
                    comp[y] = label
                    stack.append(y)
        label += 1

    seen_pairs = set()
    cond = []
    for u, v in edges:
        a, b = comp[u], comp[v]
        if a != b:
            key = a * label + b
            if key not in seen_pairs:
                seen_pairs.add(key)
                cond.append([a, b])
    return {"component": comp, "condensation": cond}


# -------------------------------------------------------------- 6. Topo
def _topo(n, edges):
    """Three-state DFS (0 new, 1 active, 2 finished) with explicit stack."""
    start, to, _ = _csr(n, edges)
    state = [0] * n
    ptr = start[:n]
    finish = []
    for s in range(n):
        if state[s]:
            continue
        state[s] = 1
        stack = [s]
        while stack:
            x = stack[-1]
            p = ptr[x]
            if p < start[x + 1]:
                ptr[x] = p + 1
                y = to[p]
                if state[y] == 1:           # back edge (incl. self-loop)
                    return {"acyclic": False, "order": []}
                if state[y] == 0:
                    state[y] = 1
                    stack.append(y)
            else:
                state[x] = 2
                finish.append(x)
                stack.pop()
    finish.reverse()
    return {"acyclic": True, "order": finish}


# ------------------------------------------------------------- 7. DAG SP
def _dag(n, edges, source):
    t = _topo(n, edges)
    if not t["acyclic"]:
        return {"acyclic": False, "distance": [], "parent_edge": []}
    start, to, eid = _csr(n, edges)
    dist = [None] * n
    parent = [-1] * n
    dist[source] = 0
    for x in t["order"]:
        dx = dist[x]
        if dx is None:                      # never relax from unreachable
            continue
        for p in range(start[x], start[x + 1]):
            y = to[p]
            i = eid[p]
            nd = dx + edges[i][2]
            if dist[y] is None or nd < dist[y]:
                dist[y] = nd
                parent[y] = i
    return {"acyclic": True, "distance": dist, "parent_edge": parent}


def route(source, target, parent_edge, edges):
    """Vertex sequence source -> target from parent_edge IDs.

    No-route convention (documented in ANALYSIS.md): returns [] when the
    target is unreachable. The route to the source itself is [source].
    """
    if target == source:
        return [source]
    if parent_edge[target] == -1:
        return []
    path = [target]
    x = target
    limit = len(parent_edge)
    while x != source:
        i = parent_edge[x]
        if i == -1 or len(path) > limit:    # broken / cyclic witness
            return []
        x = edges[i][0]
        path.append(x)
    path.reverse()
    return path


# ------------------------------------------------ public entry points
# The supplied main.py calls algorithms.<task>(request) with the parsed JSON dict.
def dsu(request):
    """DSU with path compression and union by size; return states."""
    return _dsu(request["n"], request["operations"])


def kruskal(request):
    """Sort edge indices by weight + DSU; return cost, edge_ids, components."""
    return _kruskal(request["n"], request["edges"])


def prim(request):
    """Lazy-heap Prim, restarted for every unvisited component."""
    return _prim(request["n"], request["edges"])


def scc(request):
    """Kosaraju (two iterative DFS passes); return component and condensation."""
    return _scc(request["n"], request["edges"])


def topo(request):
    """Three-state iterative DFS, reverse finish order; return acyclic and order."""
    return _topo(request["n"], request["edges"])


def dag(request):
    """Whole-graph cycle check, then DAG relaxation in topological order."""
    return _dag(request["n"], request["edges"], request["source"])
