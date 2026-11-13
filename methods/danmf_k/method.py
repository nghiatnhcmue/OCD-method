from __future__ import annotations

import settings
from common.baselines import run_baseline

USES_WEIGHTS = True
USES_TRUE_K = True


def run(g, k):
    # như methods/danmf, chỉ thay K ước lượng bằng K thật; tầng đầu giữ công thức max(2K, K + 16)
    mean_w = sum(float(d["weight"]) for _, _, d in g.edges(data=True)) / max(g.number_of_edges(), 1)
    h = g.copy()
    for _, _, d in h.edges(data=True):
        w = float(d["weight"]) / mean_w
        d["weight"], d["weight_normalized"], d["cost"] = w, w, 1.0 / w
    info = {"weight_divisor": mean_w, "k_source": "truth", "k": k}
    return run_baseline("DANMF", h, {"layers": [max(2 * k, k + 16), k]}, info), info
