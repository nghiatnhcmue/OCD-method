from __future__ import annotations

import settings
from common.baselines import run_baseline

USES_WEIGHTS = False
USES_TRUE_K = True


def run(g, k):
    info = {"k_source": "truth", "k": k}
    return run_baseline("BigCLAM", g, {"dimensions": k}, info), info
