from __future__ import annotations

import settings

USES_WEIGHTS = True


def run(g):
    import wghac.sota_methods as sm
    return sm.run_infomap(g), {}
