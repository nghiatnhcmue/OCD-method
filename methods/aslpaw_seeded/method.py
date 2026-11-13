from __future__ import annotations

import settings
from common.baselines import run_baseline

USES_WEIGHTS = True


def run(g):
    # như methods/aslpaw, nhưng seed của từng lần khởi tạo lại được truyền tới ASLPAw và tới phép xáo đỉnh của nó
    info = {"seeded": True}
    return run_baseline("ASLPAW", g, {"seeded": True}, info), info
