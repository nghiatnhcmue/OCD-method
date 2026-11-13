from __future__ import annotations

import csv

import networkx as nx
import numpy as np

import settings as S
from timing.run_timing import SEED

D = S.ROOT / "applications" / "data"
NETS = ("celegans_varshney", "netscience", "brain_coactivation")
DROP = 0.05


def load(net):
    g = nx.Graph()
    for line in (D / net / ("%s.tsv" % net)).read_text().splitlines():
        u, v, w = line.split("\t")
        g.add_edge(int(u), int(v), weight=float(w))
    # mạng đồng tác giả: thành phần liên thông lớn nhất, như Newman (2006) đã phân tích
    if net == "netscience":
        g = g.subgraph(max(nx.connected_components(g), key=len)).copy()
    return g


def node_table(net):
    with (D / net / ("%s_nodes.tsv" % net)).open(newline="") as f:
        return {int(r["id"]): r for r in csv.DictReader(f, delimiter="\t")}


# bản nhiễu r (r >= 1): bỏ ngẫu nhiên 5% số cạnh, trừ cạnh mà bỏ đi thì một đầu mút không còn cạnh nào
def perturb(g, r):
    edges = sorted((min(u, v), max(u, v)) for u, v in g.edges())
    k = int(round(DROP * len(edges)))
    deg = dict(g.degree())
    removed = []
    for i in np.random.default_rng(SEED + r).permutation(len(edges)):
        u, v = edges[i]
        if deg[u] > 1 and deg[v] > 1:
            removed.append((u, v))
            deg[u] -= 1
            deg[v] -= 1
            if len(removed) == k:
                break
    if len(removed) != k:
        raise RuntimeError("Chỉ bỏ được %d/%d cạnh" % (len(removed), k))
    h = g.copy()
    h.remove_edges_from(removed)
    return h, sorted(removed)
