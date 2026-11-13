from __future__ import annotations

import settings
from common.baselines import run_baseline

USES_WEIGHTS = False


def run(g):
    info = {}
    return run_baseline("SLPA", g, {}, info), info
