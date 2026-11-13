from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S

S.preload_native_libs()
import networkx as nx

from common import evaluate

# cùng một dự đoán, khác ở cách biểu diễn ba đỉnh không được gán
G = nx.complete_graph(6)
TRUTH = [{0, 1, 2}, {3, 4, 5}]
CASES = {"bỏ trống 3, 4, 5": [{0, 1, 2}], "3, 4, 5 thành đơn tử": [{0, 1, 2}, {3}, {4}, {5}],
         "3, 4, 5 gộp một cụm": [{0, 1, 2}, {3, 4, 5}], "3, 4, 5 vào cụm đầu": [{0, 1, 2, 3, 4, 5}]}
for name, pred in CASES.items():
    s = evaluate._metrics(G, pred, TRUTH)
    print("%-22s " % name + " ".join("%s=%.3f" % (k, s[k]) for k in ("onmi_mgh", "onmi_lfk", "omega", "f1")))
