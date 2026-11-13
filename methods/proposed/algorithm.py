from __future__ import annotations

import heapq
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

import cdlib  # nạp libgomp của hệ thống trước POT

HERE = Path(__file__).resolve().parent


def load_config(path=None) -> dict:
    return json.loads(Path(path or HERE / "config.json").read_text())


def _signatures(g, cfg):
    import methods.dothac as D
    ctx = object.__new__(D.DTDContext)
    ctx.graph = g
    ctx.nodes = sorted(g.nodes(), key=str)
    ctx.log_weights = True
    ctx.adjacency, ctx.wdeg = {}, {}
    for node in ctx.nodes:
        entries = []
        for nbr in g.neighbors(node):
            w_tilde = np.log1p(float(g[node][nbr].get("weight", 1.0)))
            if w_tilde > 0:
                entries.append((nbr, w_tilde))
        ctx.adjacency[node] = entries
        ctx.wdeg[node] = sum(w for _, w in entries)
    ctx.signatures = {}
    for node in ctx.nodes:
        merged = {}
        for key, mass in D._push_ppr(ctx.adjacency, ctx.wdeg, node, cfg["alpha"], cfg["eps"]).items():
            merged[key] = merged.get(key, 0.0) + mass / 1
        ctx.signatures[node] = D._cap_normalize(merged, cfg["s_max"])
    ctx.s_max = cfg["s_max"]
    return ctx


def _candidates(ctx, knn):
    inverted = defaultdict(list)
    for node in ctx.nodes:
        for key in ctx.signatures[node]:
            inverted[key].append(node)
    ov_acc = defaultdict(float)
    for node in ctx.nodes:
        sig = ctx.signatures[node]
        seen = {}
        for key, mass in sig.items():
            for other in inverted[key]:
                if str(other) <= str(node):
                    continue
                seen[other] = seen.get(other, 0.0) + min(mass, ctx.signatures[other][key])
        for other, ov in seen.items():
            ov_acc[(node, other)] = ov
    neighbor_lists = defaultdict(list)
    for (u, v), ov in ov_acc.items():
        neighbor_lists[u].append((ov, v))
        neighbor_lists[v].append((ov, u))
    cand = set()
    for node in ctx.nodes:
        top = sorted(neighbor_lists[node], key=lambda t: (-t[0], str(t[1])))[:knn]
        for _, other in top:
            cand.add(tuple(sorted((node, other), key=str)))
    return cand


def _base_costs(ctx, cfg):
    ctx._cost = {}
    max_cost = 0.0
    for source in ctx.nodes:
        reached = ctx._truncated_dijkstra(source, cfg["radius_hops"])
        ctx._cost[source] = reached
        if reached:
            max_cost = max(max_cost, max(reached.values()))
    ctx.c_max = 1.25 * max_cost if max_cost > 0 else 1.0
    costs = [c for row in ctx._cost.values() for c in row.values() if c > 0]
    ctx.eta = cfg["eta_factor"] * float(np.median(costs)) if costs else 0.05


def _agglomerate(ctx, cand, beta):
    import methods.dothac as D
    from methods.common import Dendrogram
    nodes = ctx.nodes
    index = {node: i for i, node in enumerate(nodes)}
    clusters = {i: {"members": {node}, "sig": ctx.signatures[node], "alive": True, "size": 1}
                for i, node in enumerate(nodes)}

    def d_value(a, b):
        value = ctx.dtd(clusters[a]["sig"], clusters[b]["sig"])
        ov = D._overlap(clusters[a]["sig"], clusters[b]["sig"])
        return value / (1.0 + beta * ov)

    neighbors = defaultdict(set)
    heap = []
    counter = 0
    for u, v in sorted(cand, key=lambda p: (str(p[0]), str(p[1]))):
        a, b = index[u], index[v]
        neighbors[a].add(b)
        neighbors[b].add(a)
        heapq.heappush(heap, (d_value(a, b), counter, a, b))
        counter += 1
    dendrogram = Dendrogram(leaves=[[node] for node in nodes])
    next_id = len(nodes)
    id_map = {i: i for i in range(len(nodes))}
    merges_done = 0
    while heap:
        dist, _, a, b = heapq.heappop(heap)
        if not (clusters.get(a, {}).get("alive") and clusters.get(b, {}).get("alive")):
            continue
        size_a, size_b = clusters[a]["size"], clusters[b]["size"]
        merged_sig = defaultdict(float)
        for cid, size in ((a, size_a), (b, size_b)):
            for key, mass in clusters[cid]["sig"].items():
                merged_sig[key] += size * mass
        merged_sig = D._cap_normalize(dict(merged_sig), ctx.s_max)
        clusters[a]["alive"] = False
        clusters[b]["alive"] = False
        new_id = next_id
        next_id += 1
        clusters[new_id] = {"members": clusters[a]["members"] | clusters[b]["members"],
                            "sig": merged_sig, "alive": True, "size": size_a + size_b}
        dendrogram.merges.append((id_map[a], id_map[b], max(dist, 0.0)))
        id_map[new_id] = len(nodes) + merges_done
        merges_done += 1
        merged_neighbors = (neighbors[a] | neighbors[b]) - {a, b}
        live = {n for n in merged_neighbors if clusters.get(n, {}).get("alive")}
        neighbors[new_id] = live
        for other in sorted(live):
            neighbors[other].add(new_id)
            heapq.heappush(heap, (d_value(new_id, other), counter, new_id, other))
            counter += 1
    return dendrogram


def _select_sets(dendrogram, g, mode, monotone=False):
    import methods.dothac as D
    nodes = dendrogram.tree_nodes(monotone=monotone)
    W = sum(float(d.get("weight", 1.0)) for _, _, d in g.edges(data=True))
    if mode == "psi":
        ids = D.mos_v1_select(nodes, g, W)
    elif mode == "density":
        n = g.number_of_nodes()
        w_max = max(float(d.get("weight", 1.0)) for _, _, d in g.edges(data=True))
        gains = []
        for t in nodes:
            m = len(t.members)
            if m >= 2:
                internal = sum(float(d.get("weight", 1.0)) for _, _, d in g.subgraph(t.members).edges(data=True))
                first = 2 * internal / (m * (m - 1) * w_max)
            else:
                first = 0.0
            phi = 0.0 if m == n else D._weighted_conductance(g, t.members, W)
            gains.append(first * (1.0 - phi) * len(t.members))
        f = [0.0] * len(nodes)
        pick_self = [True] * len(nodes)
        for idx, tree_node in enumerate(nodes):
            child_sum = sum(f[c] for c in tree_node.children)
            if tree_node.children and child_sum > gains[idx]:
                f[idx] = child_sum
                pick_self[idx] = False
            else:
                f[idx] = gains[idx]
        ids = []
        roots = set(range(len(nodes)))
        for tree_node in nodes:
            for child in tree_node.children:
                roots.discard(child)
        stack = sorted(roots, reverse=True)
        while stack:
            idx = stack.pop()
            if pick_self[idx] or not nodes[idx].children:
                if gains[idx] > 0.0 or not nodes[idx].children:
                    ids.append(idx)
            else:
                stack.extend(nodes[idx].children)
    else:
        raise ValueError(mode)
    sel = [set(nodes[k].members) for k in ids]
    return sel if sel else [set(g.nodes())]


def _cover_from_sets(nodes, sigs, selected, tau, m):
    soft = {}
    for node in nodes:
        sig = sigs[node]
        masses = [sum(sig.get(x, 0.0) for x in community) for community in selected]
        total = sum(masses)
        soft[node] = [x / total for x in masses] if total > 0 else [0.0] * len(selected)
    cover = [set() for _ in selected]
    for node in nodes:
        row = soft[node]
        peak = max(row) if row else 0.0
        placed = False
        for idx, value in enumerate(row):
            if peak > 0 and value >= tau * peak:
                cover[idx].add(node)
                placed = True
        if not placed and row:
            fallback = row if max(row) > 0 else soft[node]
            cover[int(np.argmax(fallback))].add(node)
    kept, dropped = [], []
    for community in cover:
        if len(community) >= m:
            kept.append(community)
        else:
            dropped.extend(community)
    if not kept:
        kept = [set(nodes)]
    for node in dropped:
        row = soft[node]
        order = np.argsort([-v for v in row])
        for idx in order:
            if len(cover[idx]) >= m and node not in kept[0]:
                target = selected[idx]
                for community in kept:
                    if community == cover[idx] or community >= target:
                        community.add(node)
                        break
                break
        else:
            kept[0].add(node)
    return kept


def _phase_two(g, cover, cores, q):
    from wom_v1 import CCM, bh, node_core_table
    table, model = node_core_table(g, cores, CCM(g))
    member = [set(c) for c in cover]
    accepted = set()
    for u in list(g):
        for j in bh([table[u][c][3] for c in range(len(cores))], q):
            accepted.add((u, j))
    adds = sorted((u, c) for u, c in accepted if u not in member[c])
    for u, c in adds:
        member[c].add(u)
    return member, adds, table, model.kappa


def _old_phase_two(cfg):
    return (cfg.get("phase2_pvalue", "normal") == "normal" and cfg.get("phase2_family", "node_all") == "node_all"
            and not cfg.get("phase2_min_core_edges", 0))


def phase_two_pvalues(g, cores, cfg, model=None, stats=None):
    import ccm_tail
    from wom_v1 import CCM, node_core_table
    model = model or CCM(g)
    method = cfg.get("phase2_pvalue", "normal")
    if method == "normal":
        table, _ = node_core_table(g, cores, model)
        T, E, in_core = ccm_tail.pair_stats(g, cores, model)
        P = np.ones(T.shape)
        for u, rows in table.items():
            P[model.idx[u]] = [r[3] for r in rows]
        return P, T, E, in_core, model
    law = ccm_tail.make_law(g, model, cfg.get("phase2_xi", "gamma")) if method == "cpoisson" else None
    P, T, E, in_core = ccm_tail.node_core_pvalues(g, cores, model, method, law, cfg.get("phase2_grid", 400), stats)
    return P, T, E, in_core, model


def _phase_two_v3(g, cover, cores, cfg):
    import ccm_tail
    P, T, E, in_core, model = phase_two_pvalues(g, cores, cfg)
    acc = ccm_tail.accept(P, E, in_core, cfg.get("phase2_family", "node_all"), cfg["q_bh"],
                          cfg.get("phase2_min_core_edges", 0))
    member = [set(c) for c in cover]
    core_arr = [np.array(sorted(model.idx[v] for v in c), dtype=int) for c in cores]
    table = {}
    rows, cols = np.nonzero(acc)
    for i, c in zip(rows, cols):
        mu, var = model.moments(i, core_arr[c][core_arr[c] != i])
        table.setdefault(model.nodes[i], {})[int(c)] = (float(T[i, c]), mu, var, float(P[i, c]))
    adds = sorted((model.nodes[i], int(c)) for i, c in zip(rows, cols) if model.nodes[i] not in member[c])
    for u, c in adds:
        member[c].add(u)
    return member, adds, table, model.kappa


def phase_one(g, cfg):
    T = {}
    t0 = time.perf_counter()
    ctx = _signatures(g, cfg)
    T["A_signatures"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    cand = _candidates(ctx, cfg["knn"])
    T["B_candidates"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    _base_costs(ctx, cfg)
    T["C_costs"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    dendrogram = _agglomerate(ctx, cand, cfg["beta"])
    T["C_merge"] = time.perf_counter() - t0
    return ctx, dendrogram, T


def phase_one_cover(g, ctx, dendrogram, cfg, T=None):
    import wom_dot
    T = {} if T is None else T
    t0 = time.perf_counter()
    # khóa thiếu trong cấu hình thì giữ hành vi phiên bản 2
    selected = _select_sets(dendrogram, g, cfg["tree_selection"], cfg.get("monotone_heights", False))
    T["D_select"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    cover = _cover_from_sets(ctx.nodes, ctx.signatures, selected, cfg["tau_m"], cfg["min_comm_size"])
    cores = wom_dot.extract_cores([set(c) for c in cover], [set(s) for s in selected])
    T["E_cover"] = time.perf_counter() - t0
    return selected, cover, cores


def run_dot_ccm_v2(graph, config=None, details=False) -> dict:
    import wom_dot
    cfg = load_config() if config is None else dict(config)
    g = wom_dot.canonical_graph(graph)
    if g.number_of_nodes() < 3:
        return {"cover": [set(g.nodes())], "status": "tiny", "timing": {}, "added_memberships": 0}
    if g.number_of_edges() == 0:
        return {"cover": [set(g.nodes())], "status": "no_edges", "timing": {}, "added_memberships": 0}
    ctx, dendrogram, T = phase_one(g, cfg)
    selected, cover, cores = phase_one_cover(g, ctx, dendrogram, cfg, T)
    t0 = time.perf_counter()
    if _old_phase_two(cfg):
        final, adds, table, kappa = _phase_two(g, cover, cores, cfg["q_bh"])
    else:
        final, adds, table, kappa = _phase_two_v3(g, cover, cores, cfg)
    T["F_phase2"] = time.perf_counter() - t0
    T["total"] = sum(T.values())
    out = {"cover": [set(c) for c in final if c], "status": "ok", "timing": T, "added_memberships": len(adds)}
    if details:
        out.update(selected=selected, pre_cover=[set(c) for c in cover], cores=cores, dendrogram=dendrogram,
                   kappa=kappa, eta=ctx.eta, c_max=ctx.c_max, adds=adds, table=table)
    return out
