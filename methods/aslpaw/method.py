# ASLPAw của cdlib, 5 lần khởi động lại, giữ lần có nhiều cộng đồng nhất; không tất định.

from __future__ import annotations

import settings  # đặt sys.path và số luồng
from common.baselines import run_baseline

USES_WEIGHTS = True


def run(g):
    info = {}
    return run_baseline("ASLPAW", g, {}, info), info
