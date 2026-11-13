from __future__ import annotations

import settings
from common.baselines import run_baseline

USES_WEIGHTS = True


def run(g):
    mean_w = sum(float(d["weight"]) for _, _, d in g.edges(data=True)) / max(g.number_of_edges(), 1)
    h = g.copy()
    for _, _, d in h.edges(data=True):
        w = float(d["weight"]) / mean_w
        d["weight"], d["weight_normalized"], d["cost"] = w, w, 1.0 / w
    info = {"weight_divisor": mean_w}
    return run_baseline("DANMF", h, {}, info), info
