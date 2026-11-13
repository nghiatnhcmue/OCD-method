from __future__ import annotations

import importlib.util
from pathlib import Path

import settings

USES_WEIGHTS = True
_spec = importlib.util.spec_from_file_location("proposed_algorithm", Path(__file__).resolve().parent / "algorithm.py")
algorithm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(algorithm)


def run(g):
    out = algorithm.run_dot_ccm_v2(g)
    return out["cover"], {"status": out["status"], "added_memberships": out["added_memberships"], "step_seconds": out["timing"]}
