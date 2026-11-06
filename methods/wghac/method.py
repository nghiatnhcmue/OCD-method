# wGHAC: khoảng cách CT có trọng số, liên kết trung bình, mức cắt cây theo silhouette.

from __future__ import annotations

import os

import settings  # đặt sys.path và số luồng
from common.baselines import temp_workdir

USES_WEIGHTS = True


def run(g):
    from methods.wghac import run_wghac
    with temp_workdir("wghac"):
        out = run_wghac(g, min_comm_size=5, al_paper_denominator=False, temp_prefix="tn_%d" % os.getpid())
    info = {k: out.get(k) for k in ("status", "selected_level", "si", "n_cliques", "core_nodes", "removed_nodes")}
    return out["cover"], info
