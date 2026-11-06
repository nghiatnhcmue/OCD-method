# BigCLAM (SNAP); trọng số chỉ dùng khi ước lượng số cộng đồng.

from __future__ import annotations

import settings  # đặt sys.path và số luồng
from common.baselines import run_baseline

USES_WEIGHTS = False


def run(g):
    info = {}
    return run_baseline("BigCLAM", g, {}, info), info
