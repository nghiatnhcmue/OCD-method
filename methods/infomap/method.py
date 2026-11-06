# Infomap: phân hoạch, không chồng lấn.

from __future__ import annotations

import settings  # đặt sys.path và số luồng

USES_WEIGHTS = True


def run(g):
    import wghac.sota_methods as sm
    return sm.run_infomap(g), {}
