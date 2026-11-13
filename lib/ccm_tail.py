from __future__ import annotations

import numpy as np
from scipy.special import gammainc

# biên sai số số học của 1 - tổng xác suất, cộng vào để p không bao giờ nhỏ hơn giá trị đúng
EPS = 1e-12
MAX_RATE = 700.0


class XiLaw:
    def __init__(self, kappa, sample=None):
        self.kappa = float(kappa)
        self.sample = None if sample is None else np.sort(np.asarray(sample, dtype=float))

    def cdf(self, x):
        if self.sample is not None:
            return np.searchsorted(self.sample, x, side="right") / self.sample.size
        if self.kappa <= 0.0:
            return (x >= 1.0).astype(float)
        return gammainc(1.0 / self.kappa, np.maximum(x, 0.0) / self.kappa)


def xi_sample(graph, model):
    out = []
    for u, v, w in graph.edges(data="weight"):
        f = model._f(model.idx[u], np.array([model.idx[v]]))[0]
        if f > 0:
            out.append(float(w) / f)
    return np.array(out)


def make_law(graph, model, kind):
    if kind == "gamma":
        return XiLaw(model.kappa)
    if kind == "empirical":
        return XiLaw(model.kappa, xi_sample(graph, model))
    raise ValueError(kind)


def _grid_cdf(law, t, f, w, grid):
    # F_X tại các điểm j*h, j = 0..grid-1, h = t/grid; X là hỗn hợp theo w của f_v * xi
    j = np.arange(grid, dtype=float)
    x = (t / grid)[:, None, None] * j[None, None, :] / f[:, :, None]
    return np.einsum("bl,blk->bk", w, law.cdf(x))


def _panjer(rate, pmf):
    B, K = pmf.shape
    g = np.zeros((B, K))
    g[:, 0] = np.exp(-rate * (1.0 - pmf[:, 0]))
    jf = pmf * np.arange(K, dtype=float)[None, :]
    for k in range(1, K):
        g[:, k] = rate / k * np.einsum("bj,bj->b", jf[:, 1:k + 1], g[:, k - 1::-1])
    return g


def cp_tails(ts, ps, fs, law, grid=400, cells=4_000_000, stats=None):
    # P(T' >= t) bảo thủ: Bernoulli(p_v) thay bằng Poisson(-ln(1 - p_v)), bước nhảy làm tròn lên lưới t/grid
    ts = np.asarray(ts, dtype=float)
    out = np.ones(len(ts))
    lengths = np.array([max(len(p), 1) for p in ps], dtype=int)
    order = np.argsort(lengths, kind="stable")
    stats = {} if stats is None else stats
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and (j - i + 1) * lengths[order[j]] * grid <= cells:
            j += 1
        idx = order[i:j]
        L = int(lengths[idx].max())
        i = j
        idx = idx[ts[idx] > 0]
        if not len(idx):
            continue
        f = np.ones((len(idx), L))
        rate_v = np.zeros((len(idx), L))
        sure = []
        for r, k in enumerate(idx):
            p, fv = np.asarray(ps[k], dtype=float), np.asarray(fs[k], dtype=float)
            f[r, :len(p)] = fv
            soft = p < 1.0
            rate_v[r, :len(p)][soft] = -np.log1p(-p[soft])
            sure.append(fv[~soft])
        rate = rate_v.sum(axis=1)
        w = rate_v / np.where(rate > 0, rate, 1.0)[:, None]
        t = ts[idx]
        pmf = np.diff(_grid_cdf(law, t, f, w, grid), axis=1, prepend=0.0)
        big = rate > MAX_RATE
        g = _panjer(np.where(big, 0.0, rate), pmf)
        for r, fv in enumerate(sure):
            for fx in fv:
                q = np.diff(_grid_cdf(law, t[r:r + 1], np.array([[fx]]), np.ones((1, 1)), grid)[0], prepend=0.0)
                g[r] = np.convolve(g[r], q)[:grid]
        tail = np.minimum(1.0, np.maximum(1.0 - g.sum(axis=1), 0.0) + EPS)
        tail[big] = 1.0
        out[idx] = tail
        stats["tests"] = stats.get("tests", 0) + len(idx)
        stats["rate_too_large"] = stats.get("rate_too_large", 0) + int(big.sum())
        stats["sure_jumps"] = stats.get("sure_jumps", 0) + sum(len(x) for x in sure)
    return out


def count_tails(ns, ps):
    # kiểm định số cạnh: P(N >= n), N là tổng Bernoulli(p_v) độc lập (Poisson-nhị thức), tính chính xác
    out = np.ones(len(ns))
    for k, (n, p) in enumerate(zip(ns, ps)):
        n = int(n)
        if n <= 0:
            continue
        dist = np.zeros(n)
        dist[0] = 1.0
        for pv in np.asarray(p, dtype=float):
            dist[1:] = dist[1:] * (1.0 - pv) + dist[:-1] * pv
            dist[0] *= 1.0 - pv
        out[k] = min(1.0, max(1.0 - dist.sum(), 0.0) + EPS)
    return out


def pair_stats(graph, cores, model):
    N, K = len(model.nodes), len(cores)
    T, E = np.zeros((N, K)), np.zeros((N, K), dtype=int)
    in_core = np.zeros((N, K), dtype=bool)
    inverse = {u: [] for u in graph}
    for c, core in enumerate(cores):
        for v in core:
            inverse[v].append(c)
            in_core[model.idx[v], c] = True
    for u in graph:
        iu = model.idx[u]
        for v, data in graph[u].items():
            if v == u:
                continue
            for c in inverse[v]:
                T[iu, c] += float(data["weight"])
                E[iu, c] += 1
    return T, E, in_core


def _pair_params(model, iu, js):
    js = js[(js != iu) & (model.d[js] > 0)]
    p = np.minimum(1.0, model.d[iu] * model.d[js] / model.dT)
    f = model.s[iu] * model.s[js] / model.sT / p
    return p, f


def node_core_pvalues(graph, cores, model, method, law=None, grid=400, stats=None):
    T, E, in_core = pair_stats(graph, cores, model)
    P = np.ones(T.shape)
    core_idx = [np.array(sorted(model.idx[v] for v in c), dtype=int) for c in cores]
    rows, cols = np.nonzero(T > 0)
    ok = (model.s[rows] > 0) & (model.sT > 0)
    rows, cols = rows[ok], cols[ok]
    params = [_pair_params(model, iu, core_idx[c]) for iu, c in zip(rows, cols)]
    if method == "cpoisson":
        P[rows, cols] = cp_tails(T[rows, cols], [a for a, _ in params], [b for _, b in params], law, grid,
                                 stats=stats)
    elif method == "count":
        P[rows, cols] = count_tails(E[rows, cols], [a for a, _ in params])
    else:
        raise ValueError(method)
    return P, T, E, in_core


def bh_mask(p, q):
    p = np.asarray(p, dtype=float)
    m = p.size
    if not m:
        return np.zeros(0, dtype=bool)
    order = np.argsort(p, kind="stable")
    hit = np.nonzero(p[order] <= q * np.arange(1, m + 1) / m)[0]
    if not len(hit):
        return np.zeros(m, dtype=bool)
    return p <= p[order][hit.max()]


def accept(P, E, in_core, family, q, min_edges=0):
    N, K = P.shape
    acc = np.zeros((N, K), dtype=bool)
    if family == "global":
        fam = ~in_core
        acc[fam] = bh_mask(P[fam], q)
    elif family in ("node", "node_all"):
        for i in range(N):
            fam = np.ones(K, dtype=bool) if family == "node_all" else ~in_core[i]
            acc[i, fam] = bh_mask(P[i, fam], q)
    else:
        raise ValueError(family)
    if min_edges:
        acc &= E >= min_edges
    return acc
