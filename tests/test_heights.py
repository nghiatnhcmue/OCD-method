import random
import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings

settings.preload_native_libs()
from common import runner
from methods import dothac as D
from methods.common import Dendrogram

A = runner.load_method("proposed").algorithm


def rho(node):
    return max(0.0, (node.h_death - node.h_birth) / node.h_death) if node.h_death else 0.0


def random_dendrogram(n, rng, full=True):
    alive, merges = list(range(n)), []
    steps = n - 1 if full else rng.randint(0, n - 1)
    for k in range(steps):
        a, b = rng.sample(alive, 2)
        alive.remove(a)
        alive.remove(b)
        merges.append((a, b, rng.random()))
        alive.append(n + k)
    return Dendrogram(leaves=[[i] for i in range(n)], merges=merges)


def test_example_from_review():
    d = Dendrogram(leaves=[[0], [1], [2], [3]], merges=[(0, 1, 1.0), (2, 3, 1.2), (4, 5, 0.9)])
    nodes = d.tree_nodes(monotone=True)
    c, s, p = nodes[4], nodes[5], nodes[6]
    assert p.h_birth == 1.2
    assert rho(s) == 0.0
    assert rho(c) == pytest.approx(1 / 6)
    old = d.tree_nodes()
    assert old[6].h_birth == 0.9 and rho(old[4]) == 0.0 and rho(old[5]) == 0.0
    assert d.merges[2][2] == 0.9


def test_envelope_never_decreases_towards_root():
    rng = random.Random(42)
    for _ in range(300):
        d = random_dendrogram(rng.randint(2, 60), rng, full=rng.random() < 0.7)
        nodes = d.tree_nodes(monotone=True)
        n = len(d.leaves)
        for k, (a, b, h) in enumerate(d.merges):
            p = nodes[n + k]
            assert p.h_birth == max(h, nodes[a].h_birth, nodes[b].h_birth)
            assert nodes[a].h_death == nodes[b].h_death == p.h_birth
            assert nodes[a].h_birth <= p.h_birth and nodes[b].h_birth <= p.h_birth
        for node in nodes:
            assert rho(node) >= 0.0
            if node.h_death:
                assert node.h_death - node.h_birth >= 0.0


def test_no_inversion_changes_nothing():
    rng = random.Random(7)
    g = nx.les_miserables_graph()
    g = nx.convert_node_labels_to_integers(g, ordering="sorted")
    W = sum(float(x.get("weight", 1.0)) for _, _, x in g.edges(data=True))
    for _ in range(50):
        d = random_dendrogram(g.number_of_nodes(), rng)
        heights = sorted(h for _, _, h in d.merges)
        d.merges = [(a, b, h) for (a, b, _), h in zip(d.merges, heights)]
        old, new = d.tree_nodes(), d.tree_nodes(monotone=True)
        assert [(x.h_birth, x.h_death) for x in old] == [(x.h_birth, x.h_death) for x in new]
        assert D.mos_v1_select(old, g, W) == D.mos_v1_select(new, g, W)
        assert A._select_sets(d, g, "psi") == A._select_sets(d, g, "psi", monotone=True)


def test_config_versions():
    v2 = A.load_config(A.HERE / "config_v2.json")
    v3 = A.load_config()
    assert v2["version"] == 2 and v2["monotone_heights"] is False
    assert v3["version"] == 3 and v3["monotone_heights"] is True
    shared = set(v2) - {"version", "monotone_heights", "q_bh"} - {k for k in v2 if k.startswith("phase2_")}
    assert {k: v2[k] for k in shared} == {k: v3[k] for k in shared}
    # q và họ kiểm định của v3 chọn trên tập chọn (results/round_c/PROTOCOL.md, tag v3-frozen)
    assert v2["q_bh"] == 0.001 and v3["q_bh"] == 0.05
    assert v3["phase2_pvalue"] == "cpoisson" and v3["phase2_family"] == "node"
