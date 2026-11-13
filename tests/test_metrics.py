import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings

settings.preload_native_libs()
from common import evaluate

G = nx.complete_graph(6)


def scores(pred, truth):
    return evaluate._metrics(G, [set(c) for c in pred], [set(c) for c in truth])


def test_identical_covers_score_one():
    cover = [{0, 1, 2, 3}, {3, 4, 5}]
    s = scores(cover, cover)
    for k in ("onmi_mgh", "onmi_lfk", "omega", "f1", "onf1", "P_O", "R_O", "P_mem", "R_mem"):
        assert s[k] == pytest.approx(1.0), k


def test_six_node_hand_values():
    # nhãn: {0,1,2,3}, {3,4,5}; dự đoán: {0,1,2,3,4}, {3,4,5}
    s = scores([{0, 1, 2, 3, 4}, {3, 4, 5}], [{0, 1, 2, 3}, {3, 4, 5}])
    assert s["onf1"] == pytest.approx(2 / 3)
    assert s["P_O"] == pytest.approx(1 / 2)
    assert s["R_O"] == pytest.approx(1.0)
    assert s["f1"] == pytest.approx(17 / 18)
    assert s["omega"] == pytest.approx(4 / 9)


def test_independent_partitions_have_zero_onmi():
    s = scores([{0, 3}, {1, 4}, {2, 5}], [{0, 1, 2}, {3, 4, 5}])
    assert s["onmi_mgh"] == pytest.approx(0.0, abs=1e-9)
    assert s["onmi_lfk"] == pytest.approx(0.0, abs=1e-9)


def test_onf1_undefined_without_true_overlap():
    g = nx.complete_graph(6)
    s = evaluate.evaluate("test1", g, [{0, 1, 2}, {2, 3, 4, 5}], [{0, 1, 2}, {3, 4, 5}])
    assert s["onf1"] != s["onf1"] and s["R_O"] != s["R_O"]
