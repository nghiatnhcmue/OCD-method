# Phần của DOT-HAC dùng lại trong phương pháp đề xuất: PPR đẩy cục bộ, khoảng cách vận tải, độ dẫn,
# chọn tập trên cây.

from __future__ import annotations

import heapq
from collections import defaultdict

import networkx as nx
import numpy as np
import ot

from methods.common import TreeNode


def _push_ppr(adjacency: dict, weights: dict, u, alpha: float,
              eps: float) -> dict:
    p: dict = defaultdict(float)
    r: dict = defaultdict(float)
    r[u] = 1.0
    queue = [u]
    in_queue = {u}
    while queue:
        v = queue.pop()
        in_queue.discard(v)
        degree = weights[v]
        if degree <= 0.0 or r[v] <= eps * max(len(adjacency[v]), 1):
            continue
        mass = r[v]
        r[v] = 0.0
        p[v] += alpha * mass
        share = (1.0 - alpha) * mass
        for nbr, w in adjacency[v]:
            r[nbr] += share * (w / degree)
            if nbr not in in_queue and r[nbr] > eps * max(
                    len(adjacency[nbr]), 1):
                queue.append(nbr)
                in_queue.add(nbr)
    return dict(p)


def _cap_normalize(signature: dict, s_max: int) -> dict:
    if len(signature) > s_max:
        top = sorted(signature.items(), key=lambda kv: (-kv[1], str(kv[0])))
        signature = dict(top[:s_max])
    total = sum(signature.values())
    if total <= 0.0:
        return signature
    return {k: v / total for k, v in signature.items()}


def _overlap(sig_a: dict, sig_b: dict) -> float:
    if len(sig_a) > len(sig_b):
        sig_a, sig_b = sig_b, sig_a
    return sum(min(v, sig_b[k]) for k, v in sig_a.items() if k in sig_b)


class DTDContext:
    def __init__(self, graph: nx.Graph, *, alpha=0.15, eps=1e-4, s_max=200,
                 radius_hops=3, eta_factor=0.05, log_weights=True,
                 multiscale=False):
        self.graph = graph
        self.nodes = sorted(graph.nodes(), key=str)
        self.log_weights = log_weights
        self.adjacency: dict = {}
        self.wdeg: dict = {}
        for node in self.nodes:
            entries = []
            for nbr in graph.neighbors(node):
                weight = float(graph[node][nbr].get("weight", 1.0))
                w_tilde = np.log1p(weight) if log_weights else weight
                if w_tilde > 0:
                    entries.append((nbr, w_tilde))
            self.adjacency[node] = entries
            self.wdeg[node] = sum(w for _, w in entries)
        alphas = (0.05, 0.15, 0.30) if multiscale else (alpha,)
        self.signatures = {}
        for node in self.nodes:
            merged: dict = {}
            for a in alphas:
                for key, mass in _push_ppr(
                        self.adjacency, self.wdeg, node, a, eps).items():
                    merged[key] = merged.get(key, 0.0) + mass / len(alphas)
            self.signatures[node] = _cap_normalize(merged, s_max)
        self.s_max = s_max
        self._cost: dict = {}
        max_cost = 0.0
        for source in self.nodes:
            reached = self._truncated_dijkstra(source, radius_hops)
            self._cost[source] = reached
            if reached:
                max_cost = max(max_cost, max(reached.values()))
        self.c_max = 1.25 * max_cost if max_cost > 0 else 1.0
        costs = [c for row in self._cost.values() for c in row.values() if c > 0]
        self.eta = eta_factor * float(np.median(costs)) if costs else 0.05

    def _truncated_dijkstra(self, source, radius_hops: int) -> dict:
        best = {source: (0.0, 0)}
        heap = [(0.0, 0, str(source), source)]
        while heap:
            dist, hops, _, node = heapq.heappop(heap)
            if (dist, hops) != best.get(node, (None, None)):
                continue
            if hops >= radius_hops:
                continue
            for nbr, w in self.adjacency[node]:
                nd = dist + 1.0 / w
                nh = hops + 1
                if nbr not in best or nd < best[nbr][0]:
                    best[nbr] = (nd, nh)
                    heapq.heappush(heap, (nd, nh, str(nbr), nbr))
        return {node: d for node, (d, _) in best.items()}

    def cost(self, i, j) -> float:
        if i == j:
            return 0.0
        row = self._cost.get(i, {})
        return row.get(j, self.c_max)

    def dtd(self, sig_a: dict, sig_b: dict) -> float:
        keys_a = sorted(sig_a, key=str)
        keys_b = sorted(sig_b, key=str)
        a = np.array([sig_a[k] for k in keys_a], dtype=np.float64)
        b = np.array([sig_b[k] for k in keys_b], dtype=np.float64)
        a /= a.sum()
        b /= b.sum()
        cost = np.array(
            [[self.cost(i, j) for j in keys_b] for i in keys_a],
            dtype=np.float64)
        if min(len(keys_a), len(keys_b)) < 10:
            return float(ot.emd2(a, b, cost))
        value = float(ot.sinkhorn2(a, b, cost, reg=self.eta,
                                   numItermax=200))
        if not np.isfinite(value):
            value = float(ot.emd2(a, b, cost))
        return value


def _weighted_conductance(graph: nx.Graph, members: set,
                          total_weight: float) -> float:
    # C = V: phi = 1, không tính qua hiệu 2W - vol (phần dư số thực)
    if len(members) >= graph.number_of_nodes():
        return 1.0
    cut = 0.0
    vol = 0.0
    for node in members:
        for nbr in graph.neighbors(node):
            weight = float(graph[node][nbr].get("weight", 1.0))
            vol += weight
            if nbr not in members:
                cut += weight
    other = 2.0 * total_weight - vol
    denom = min(vol, other)
    if denom <= 0.0:
        return 1.0
    return min(cut / denom, 1.0)


def mos_v1_select(nodes: list[TreeNode], graph: nx.Graph,
                  total_weight: float) -> list[int]:
    gains = []
    for tree_node in nodes:
        rho = 0.0
        if tree_node.h_death and tree_node.h_death > 0:
            rho = max(0.0, (tree_node.h_death - tree_node.h_birth)
                      / tree_node.h_death)
        quality = 1.0 - _weighted_conductance(
            graph, tree_node.members, total_weight)
        gains.append(rho * quality * len(tree_node.members))
    f = [0.0] * len(nodes)
    pick_self = [True] * len(nodes)
    for idx, tree_node in enumerate(nodes):
        child_sum = sum(f[c] for c in tree_node.children)
        if tree_node.children and child_sum > gains[idx]:
            f[idx] = child_sum
            pick_self[idx] = False
        else:
            f[idx] = gains[idx]
    selected: list[int] = []
    roots = set(range(len(nodes)))
    for tree_node in nodes:
        for child in tree_node.children:
            roots.discard(child)
    stack = sorted(roots, reverse=True)
    while stack:
        idx = stack.pop()
        if pick_self[idx] or not nodes[idx].children:
            if gains[idx] > 0.0 or not nodes[idx].children:
                selected.append(idx)
        else:
            stack.extend(nodes[idx].children)
    return selected
