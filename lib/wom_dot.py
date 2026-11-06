# Chuẩn hóa đồ thị đầu vào và lấy lõi của các cộng đồng.

import cdlib  # nạp libgomp của hệ thống trước
import networkx as nx
import numpy as np


def canonical_graph(graph):
    if graph.is_directed() or graph.is_multigraph():
        raise ValueError('Expected simple undirected graph')
    if any(not isinstance(u, (int, np.integer)) for u in graph):
        raise ValueError('Expected integer node IDs')
    clean = nx.Graph()
    clean.add_nodes_from(sorted(int(u) for u in graph))
    for u, v in sorted((min(int(u), int(v)), max(int(u), int(v))) for u, v in graph.edges() if u != v):
        w = float(graph.edges[u, v].get('weight', graph.edges[u, v].get('weight_normalized', 1.)))
        if not np.isfinite(w) or w <= 0:
            raise ValueError('Weights must be finite and positive')
        clean.add_edge(u, v, weight=w, weight_normalized=w, cost=1/w)
    return clean


def extract_cores(cover, selected):
    pairs = []
    for i, c in enumerate(cover):
        for j, s in enumerate(selected):
            overlap = len(c & s)
            if overlap:
                pairs.append((-overlap, len(s-c), i, j))
    used_c, used_s = set(), set()
    cores = [set() for _ in cover]
    for _, _, i, j in sorted(pairs):
        if i not in used_c and j not in used_s:
            cores[i] = cover[i] & selected[j]
            used_c.add(i)
            used_s.add(j)
    return cores
