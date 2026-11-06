# Kiểm định đỉnh - lõi dưới mô hình cấu hình liên tục (Palowitch, Bhamidi và Nobel, 2018) và thủ tục BH.

from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm


def bh(pvalues, alpha):
    m = len(pvalues)
    if not m:
        return []
    order = sorted(range(m), key=lambda i: (pvalues[i], i))
    cutoff = None
    for j, i in enumerate(order, 1):
        if pvalues[i] <= alpha * j / m:
            cutoff = pvalues[i]
    return [i for i, p in enumerate(pvalues) if cutoff is not None and p <= cutoff]


class CCM:
    def __init__(self, graph):
        self.nodes = sorted(graph.nodes())
        self.idx = {u: i for i, u in enumerate(self.nodes)}
        self.d = np.array([graph.degree(u) for u in self.nodes], dtype=float)
        self.s = np.array([graph.degree(u, weight="weight") for u in self.nodes], dtype=float)
        self.dT, self.sT = float(self.d.sum()), float(self.s.sum())
        num = den = 0.0
        if self.sT > 0:
            for u, v, w in graph.edges(data="weight"):
                i, j = self.idx[u], self.idx[v]
                f = self._f(i, np.array([j]))[0]
                num += (float(w) - f) ** 2
                den += f * f
        self.kappa = num / den if den > 0 else 0.0

    def _f(self, i, js):
        rs = self.s[i] * self.s[js] / self.sT
        rt = np.minimum(1.0, self.d[i] * self.d[js] / self.dT)
        return rs / rt

    def moments(self, i, js):
        js = js[self.d[js] > 0] if len(js) else js
        if self.sT <= 0 or len(js) == 0 or self.s[i] <= 0:
            return 0.0, 0.0
        rs = self.s[i] * self.s[js] / self.sT
        rt = np.minimum(1.0, self.d[i] * self.d[js] / self.dT)
        f = rs / rt
        var = rs * f * (1.0 - rt + self.kappa)
        return float(rs.sum()), float(max(var.sum(), 0.0))


def pvalue(t, mu, var):
    if t <= 0 or var <= 0 or not math.isfinite(var):
        return 1.0
    return float(norm.sf((t - mu) / math.sqrt(var)))


def node_core_table(graph, cores, model=None):
    model = model or CCM(graph)
    core_arr = [np.array(sorted(model.idx[v] for v in c), dtype=int) for c in cores]
    inverse = {u: [] for u in graph}
    for i, c in enumerate(cores):
        for v in c:
            inverse[v].append(i)
    table = {}
    for u in graph:
        iu = model.idx[u]
        t = np.zeros(len(cores))
        for v, data in graph[u].items():
            if v == u:
                continue
            for c in inverse[v]:
                t[c] += float(data["weight"])
        rows = []
        for c, arr in enumerate(core_arr):
            js = arr[arr != iu]
            mu, var = model.moments(iu, js)
            rows.append((float(t[c]), mu, var, pvalue(t[c], mu, var)))
        table[u] = rows
    return table, model
