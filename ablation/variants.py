from __future__ import annotations

import random
from collections import defaultdict

import numpy as np

import settings as S
from common import runner

A = runner.load_method("proposed").algorithm


def _signatures(g, cfg, log_weights):
    if log_weights:
        return A._signatures(g, cfg)
    import methods.dothac as D
    ctx = object.__new__(D.DTDContext)
    ctx.graph = g
    ctx.nodes = sorted(g.nodes(), key=str)
    ctx.log_weights = False
    ctx.adjacency, ctx.wdeg = {}, {}
    for node in ctx.nodes:
        entries = []
        for nbr in g.neighbors(node):
            w = float(g[node][nbr].get("weight", 1.0))
            if w > 0:
                entries.append((nbr, w))
        ctx.adjacency[node] = entries
        ctx.wdeg[node] = sum(w for _, w in entries)
    ctx.signatures = {}
    for node in ctx.nodes:
        ctx.signatures[node] = D._cap_normalize(D._push_ppr(ctx.adjacency, ctx.wdeg, node, cfg["alpha"], cfg["eps"]),
                                                cfg["s_max"])
    ctx.s_max = cfg["s_max"]
    return ctx


def tree(graph, cfg, log_weights=True, transport=True):
    import methods.dothac as D
    import wom_dot
    g = wom_dot.canonical_graph(graph)
    ctx = _signatures(g, cfg, log_weights)
    cand = A._candidates(ctx, cfg["knn"])
    if transport:
        A._base_costs(ctx, cfg)
        dendrogram = A._agglomerate(ctx, cand, cfg["beta"])
    else:
        ctx.dtd = lambda a, b: 1.0 - D._overlap(a, b)
        dendrogram = A._agglomerate(ctx, cand, 0.0)
    return g, ctx, dendrogram


def _sets(cover):
    return [set(c) for c in cover if c]


def finish(g, ctx, dendrogram, cfg, mode="psi"):
    import wom_dot
    from wom_v1 import bh
    selected = A._select_sets(dendrogram, g, mode)
    cover = A._cover_from_sets(ctx.nodes, ctx.signatures, selected, cfg["tau_m"], cfg["min_comm_size"])
    cores = wom_dot.extract_cores([set(c) for c in cover], [set(s) for s in selected])
    final, adds, table, kappa = A._phase_two(g, cover, cores, cfg["q_bh"])
    keep = [set(c) for c in cores]
    for u in g:
        for j in bh([table[u][c][3] for c in range(len(cores))], cfg["q_bh"]):
            keep[j].add(u)
    core_sets = [set(c) for c in cores]
    floor = [set(c) for c in cover]
    for u, c in adds:
        if sum(1 for v in g[u] if v in core_sets[c]) >= 2:
            floor[c].add(u)
    return {"full": _sets(final), "no_phase2": _sets(cover), "min_edges": _sets(floor),
            "prune": [c for c in keep if len(c) >= cfg["min_comm_size"]]}


# SLPA của cdlib (SLPA_nx), chỉ khác ở luật nghe: nhãn được cộng trọng số cạnh thay vì cộng 1
def slpa_weighted(g, T=21, r=0.1, seed=42, weighted=True):
    random.seed(seed)
    np.random.seed(seed)
    memory = {i: {i: 1} for i in g.nodes()}
    for _ in range(T):
        order = list(g.nodes())
        np.random.shuffle(order)
        for listener in order:
            speakers = g[listener].keys()
            if len(speakers) == 0:
                continue
            labels = defaultdict(float)
            for speaker in speakers:
                total = float(sum(memory[speaker].values()))
                label = list(memory[speaker].keys())[
                    np.random.multinomial(1, [freq / total for freq in memory[speaker].values()]).argmax()]
                labels[label] += float(g[listener][speaker].get("weight", 1.0)) if weighted else 1
            accepted = max(labels, key=labels.get)
            memory[listener][accepted] = memory[listener].get(accepted, 0) + 1
    for mem in memory.values():
        for label, freq in list(mem.items()):
            if freq / float(T + 1) < r:
                del mem[label]
    communities = {}
    for node, mem in memory.items():
        for label in mem:
            communities.setdefault(label, set()).add(node)
    nested = set()
    keys = list(communities)
    for i, a in enumerate(keys[:-1]):
        for b in keys[i + 1:]:
            if communities[a].issubset(communities[b]):
                nested.add(a)
            elif communities[a].issuperset(communities[b]):
                nested.add(b)
    return [c for k, c in communities.items() if k not in nested and len(c) >= 2]


GROUPS = {"base": ("test1", "test2", "test3"), "no_log": ("test1", "test2"), "no_ot": ("test1", "test2"),
          "slpa_weighted": ("test1", "test2", "test3"), "min_edges": ("test1", "test2", "test3", "test2_n5000")}


def run_group(group, graph, cfg):
    if group == "slpa_weighted":
        import wom_dot
        return {"slpa_weighted": slpa_weighted(wom_dot.canonical_graph(graph))}
    if group == "base":
        g, ctx, dendrogram = tree(graph, cfg)
        out = finish(g, ctx, dendrogram, cfg)
        out["density"] = finish(g, ctx, dendrogram, cfg, mode="density")["full"]
        return out
    if group == "min_edges":
        g, ctx, dendrogram = tree(graph, cfg)
        out = finish(g, ctx, dendrogram, cfg)
        return {k: out[k] for k in ("full", "no_phase2", "min_edges")}
    if group == "no_log":
        g, ctx, dendrogram = tree(graph, cfg, log_weights=False)
        return {"no_log": finish(g, ctx, dendrogram, cfg)["full"]}
    if group == "no_ot":
        g, ctx, dendrogram = tree(graph, cfg, transport=False)
        return {"no_ot": finish(g, ctx, dendrogram, cfg)["full"]}
    raise ValueError(group)
