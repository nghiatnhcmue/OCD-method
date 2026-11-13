import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pytest
from scipy.stats import binom, gamma, poisson

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings

settings.preload_native_libs()
import ccm_tail as C
import wom_dot
from common import runner
from wom_v1 import CCM, pvalue

A = runner.load_method("proposed").algorithm

# N = 5000, mọi đỉnh bậc 20, trọng số trung bình 1, lõi 15 đỉnh, kappa = 0,25
N, DEG, CORE, KAPPA = 5000, 20, 15, 0.25
P_EDGE = DEG * DEG / (N * DEG)
LAW = C.XiLaw(KAPPA)


def homogeneous_model():
    m = CCM.__new__(CCM)
    m.d = np.full(N, float(DEG))
    m.s = np.full(N, float(DEG))
    m.dT = m.sT = float(N * DEG)
    m.kappa = KAPPA
    return m


def new_p(t, law=LAW):
    return C.cp_tails([t], [np.full(CORE, P_EDGE)], [np.ones(CORE)], law)[0]


def exact_tail(t):
    n = np.arange(1, CORE + 1)
    return float(np.sum(binom.pmf(n, CORE, P_EDGE) * gamma.sf(t, n / KAPPA, scale=KAPPA)))


def cp_closed(t):
    lam = -CORE * np.log1p(-P_EDGE)
    n = np.arange(1, 80)
    return float(np.sum(poisson.pmf(n, lam) * gamma.sf(t, n / KAPPA, scale=KAPPA)))


def test_monte_carlo_reference():
    rng = np.random.default_rng(42)
    n = 1_000_000
    k = rng.binomial(CORE, P_EDGE, size=n)
    T = np.zeros(n)
    hit = k > 0
    T[hit] = rng.gamma(k[hit] / KAPPA, KAPPA)
    for t, ref in ((1.0, 0.026), (1.5, 0.0098)):
        mc = (T >= t).mean()
        se = np.sqrt(mc * (1 - mc) / n)
        p = new_p(t)
        assert mc == pytest.approx(ref, rel=0.05)
        assert p >= mc - 3 * se
        assert p <= 1.2 * mc


def test_normal_approximation_reference():
    mu, var = homogeneous_model().moments(0, np.arange(1, CORE + 1))
    assert pvalue(1.0, mu, var) == pytest.approx(2.9e-4, rel=0.05)
    assert pvalue(1.5, mu, var) == pytest.approx(7e-8, rel=0.05)


def test_closed_forms():
    for t in (1.0, 1.5, 2.0, 3.0):
        p = new_p(t)
        assert exact_tail(t) <= cp_closed(t) <= p <= 1.2 * exact_tail(t)
        assert p <= 1.1 * cp_closed(t)


def test_kappa_zero_counts_edges():
    law = C.XiLaw(0.0)
    lam = -CORE * np.log1p(-P_EDGE)
    assert new_p(1.0, law) == pytest.approx(1 - (1 - P_EDGE) ** CORE, abs=2e-12)
    p2 = new_p(2.0, law)
    assert p2 >= 1 - binom.cdf(1, CORE, P_EDGE)
    assert p2 == pytest.approx(1 - poisson.cdf(1, lam), abs=2e-12)


def test_empirical_law_close_to_gamma():
    rng = np.random.default_rng(1)
    law = C.XiLaw(KAPPA, rng.gamma(1 / KAPPA, KAPPA, size=200_000))
    for t in (1.0, 1.5):
        assert new_p(t, law) == pytest.approx(new_p(t), rel=0.05)


def test_sure_jump_against_monte_carlo():
    p, f = np.array([1.0, 0.1, 0.1]), np.array([0.5, 1.0, 1.0])
    rng = np.random.default_rng(3)
    n = 1_000_000
    xi = rng.gamma(1 / KAPPA, KAPPA, size=(n, 3))
    a = np.column_stack([np.ones(n), rng.random((n, 2)) < 0.1])
    T = (a * xi * f).sum(axis=1)
    for t in (1.0, 1.5, 2.0):
        mc = (T >= t).mean()
        se = np.sqrt(mc * (1 - mc) / n)
        pv = C.cp_tails([t], [p], [f], LAW)[0]
        assert mc - 3 * se <= pv <= 2 * mc


def test_zero_weight_gives_one():
    assert C.cp_tails([0.0], [np.full(CORE, P_EDGE)], [np.ones(CORE)], LAW)[0] == 1.0
    assert C.count_tails([0], [np.full(CORE, P_EDGE)])[0] == 1.0


def test_super_uniform_on_heterogeneous_null():
    rng = np.random.default_rng(5)
    L, n, kappa = 30, 20_000, 0.5
    p, f = rng.uniform(0.001, 0.3, L), rng.uniform(0.5, 2.0, L)
    edges = rng.random((n, L)) < p
    T = (edges * rng.gamma(1 / kappa, kappa, size=(n, L)) * f).sum(axis=1)
    pv = C.cp_tails(T, [p] * n, [f] * n, C.XiLaw(kappa))
    pc = C.count_tails(edges.sum(axis=1), [p] * n)
    for alpha in (0.01, 0.05, 0.1):
        tol = 3 * np.sqrt(alpha * (1 - alpha) / n)
        assert (pv <= alpha).mean() <= alpha + tol
        assert (pc <= alpha).mean() <= alpha + tol


def test_bh_mask_matches_old_bh():
    from wom_v1 import bh
    rng = np.random.default_rng(9)
    for _ in range(200):
        p = rng.random(rng.integers(1, 40)) ** rng.uniform(1, 8)
        p[rng.random(p.size) < 0.3] = 1.0
        q = rng.choice([0.001, 0.01, 0.05])
        assert list(np.nonzero(C.bh_mask(p, q))[0]) == bh(list(p), q)


def small_case():
    g = nx.convert_node_labels_to_integers(nx.les_miserables_graph(), ordering="sorted")
    g = wom_dot.canonical_graph(g)
    cfg = A.load_config(A.HERE / "config_v2.json")
    ctx, d, _ = A.phase_one(g, cfg)
    _, cover, cores = A.phase_one_cover(g, ctx, d, cfg)
    return g, cfg, cover, cores


def test_old_phase_two_unchanged():
    g, cfg, cover, cores = small_case()
    old = A._phase_two(g, cover, cores, cfg["q_bh"])
    new = A._phase_two_v3(g, cover, cores, cfg)
    assert old[1] == new[1]
    assert [sorted(c) for c in old[0]] == [sorted(c) for c in new[0]]
    for u, c in old[1]:
        assert new[2][u][c][3] == old[2][u][c][3]


def test_full_run_dispatch():
    g, cfg, cover, cores = small_case()
    old = A._phase_two(g, cover, cores, cfg["q_bh"])[0]
    v2 = A.run_dot_ccm_v2(g, cfg)
    assert sorted(sorted(c) for c in v2["cover"]) == sorted(sorted(c) for c in old if c)
    v3 = A.run_dot_ccm_v2(g)
    assert v3["status"] == "ok" and v3["cover"]


def test_new_phase_two_runs():
    g, cfg, cover, cores = small_case()
    v3 = A.load_config()
    for family in ("node", "global"):
        member, adds, table, _ = A._phase_two_v3(g, cover, cores, dict(v3, phase2_family=family))
        assert all(u in member[c] for u, c in adds)
        assert all(table[u][c][3] <= 1.0 for u, c in adds)
