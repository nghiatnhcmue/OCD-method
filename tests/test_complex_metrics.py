import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.complex_metrics import complex_scores


def brohee_table4():
    """Bảng 4 của Brohée và van Helden (2006): 4 phức hợp, 5 cụm; phức hợp 3 và 4 chung 2 protein, 3 protein của
    phức hợp 3 không được gán, một protein của phức hợp 4 nằm ở hai cụm."""
    a = ["a%d" % i for i in range(7)]
    b = ["b%d" % i for i in range(14)]
    c = ["c%d" % i for i in range(18)] + ["s0", "s1"]
    d = ["s0", "s1"] + ["d%d" % i for i in range(6)]
    complexes = [set(a), set(b), set(c), set(d)]
    clusters = [set(a), set(b[:6]), set(b[6:]), set(c[6:]) | {"d0", "d1"},
                set(c[3:6]) | {"d1", "d2", "d3", "d4", "d5"}]
    return clusters, complexes


def test_brohee_table4():
    clusters, complexes = brohee_table4()
    assert [len(x) for x in clusters] == [7, 6, 8, 16, 8]
    assert [len(x) for x in complexes] == [7, 14, 20, 8]
    s = complex_scores(clusters, complexes)
    assert round(s["sn"], 2) == 0.69
    assert round(s["ppv"], 2) == 0.85
    assert round(s["acc"], 2) == 0.77


def test_mmr_and_frac():
    ref = [{1, 2, 3, 4}, {5, 6, 7}]
    s = complex_scores([{1, 2, 3}, {5, 6, 7, 8}], ref)
    assert s["mmr"] == pytest.approx(0.75)
    assert s["frac"] == 1.0
    # ω = 0,25 đúng ngưỡng không được tính là khớp (bài gốc: ω lớn hơn 0,25)
    s = complex_scores([{1, 9, 10, 11}], [{1, 2, 3, 4}])
    assert s["mmr"] == pytest.approx(1 / 16) and s["frac"] == 0.0
    s = complex_scores([{1, 2, 9, 10}], [{1, 2, 3, 4}])
    assert s["mmr"] == pytest.approx(0.25) and s["frac"] == 0.0
