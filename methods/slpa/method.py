# SLPA của cdlib (t = 21, r = 0.1), không dùng trọng số.

from __future__ import annotations

import settings  # đặt sys.path và số luồng
from common.baselines import run_baseline

USES_WEIGHTS = False


def run(g):
    info = {}
    return run_baseline("SLPA", g, {}, info), info
