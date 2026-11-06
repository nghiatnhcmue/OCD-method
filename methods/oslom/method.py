# OSLOM2 (tệp nhị phân gốc), có trọng số.

from __future__ import annotations

import settings  # đặt sys.path và số luồng
from common.baselines import run_baseline

USES_WEIGHTS = True


def run(g):
    info = {}
    return run_baseline("OSLOM", g, {"require_original": True, "timeout_sec": 7000}, info), info
