from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable

import networkx as nx

import wghac.functions  # vá nf1 cho scipy >= 1.11
from cdlib import NodeClustering, evaluation


def _clustering(graph: nx.Graph, cover: Iterable[Iterable]) -> NodeClustering:
    communities = [list(c) for c in cover if len(list(c)) > 0]
    return NodeClustering(communities, graph=graph, overlap=True)


def score(graph: nx.Graph, pred_cover, true_cover) -> dict:
    pred = _clustering(graph, pred_cover)
    true = _clustering(graph, true_cover)
    out: dict[str, float] = {}

    def _try(name, fn):
        try:
            value = fn()
            out[name] = float(getattr(value, "score", value))
        except Exception:
            out[name] = float("nan")

    _try("onmi_mgh", lambda: evaluation
         .overlapping_normalized_mutual_information_MGH(true, pred))
    _try("onmi_lfk", lambda: evaluation
         .overlapping_normalized_mutual_information_LFK(true, pred))

    def _omega():
        all_nodes = list(set(graph.nodes()) | {u for c in pred.communities for u in c} | {u for c in true.communities for u in c})
        N = len(all_nodes)
        if N < 2:
            return 1.0
        N_pairs = N * (N - 1) // 2

        pair_c1 = defaultdict(int)
        for c in pred.communities:
            c_list = sorted(list(c))
            for i in range(len(c_list)):
                u = c_list[i]
                for j in range(i + 1, len(c_list)):
                    pair_c1[(u, c_list[j])] += 1

        pair_c2 = defaultdict(int)
        for c in true.communities:
            c_list = sorted(list(c))
            for i in range(len(c_list)):
                u = c_list[i]
                for j in range(i + 1, len(c_list)):
                    pair_c2[(u, c_list[j])] += 1

        all_pairs = set(pair_c1.keys()) | set(pair_c2.keys())
        max1 = max(pair_c1.values()) if pair_c1 else 0
        max2 = max(pair_c2.values()) if pair_c2 else 0
        max_k = min(max1, max2)

        agree = defaultdict(int)
        agree[0] = N_pairs - len(all_pairs)
        for pair in all_pairs:
            c1 = pair_c1.get(pair, 0)
            c2 = pair_c2.get(pair, 0)
            if c1 == c2:
                agree[c1] += 1

        obs = sum(agree[j] for j in range(max_k + 1)) / N_pairs

        dist1 = Counter(pair_c1.values())
        dist1[0] = N_pairs - len(pair_c1)
        dist2 = Counter(pair_c2.values())
        dist2[0] = N_pairs - len(pair_c2)

        exp = sum(dist1[j] * dist2[j] for j in range(max_k + 1)) / (N_pairs * N_pairs)
        if exp == obs == 1:
            return 1.0
        if 1 - exp == 0:
            return 1.0
        return (obs - exp) / (1 - exp)

    _try("omega", _omega)
    _try("avg_f1", lambda: evaluation.f1(true, pred))

    sizes = [len(c) for c in pred.communities]
    n_nodes = graph.number_of_nodes()
    covered = set()
    memberships = 0
    for community in pred.communities:
        covered.update(community)
        memberships += len(community)
    out.update({
        "n_comms": len(sizes),
        "avg_size": (sum(sizes) / len(sizes)) if sizes else 0.0,
        "avg_memberships": (memberships / len(covered)) if covered else 0.0,
        "coverage": (len(covered) / n_nodes) if n_nodes else 0.0,
    })
    return out
