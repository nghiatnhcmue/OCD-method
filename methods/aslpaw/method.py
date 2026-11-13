from __future__ import annotations

import settings
from common.baselines import run_baseline

USES_WEIGHTS = True


def run(g):
    info = {}
    return run_baseline("ASLPAW", g, {}, info), info
