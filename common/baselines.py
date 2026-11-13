from __future__ import annotations

import contextlib
import os
import shutil
import tempfile
from pathlib import Path

import settings as S


class _TempfileIn:
    def __init__(self, base):
        self.base = base

    def __getattr__(self, name):
        return getattr(tempfile, name)

    def mkdtemp(self, suffix=None, prefix=None, dir=None):
        return tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=str(self.base))


@contextlib.contextmanager
def temp_workdir(tag):
    S.TMP.mkdir(parents=True, exist_ok=True)
    base = Path(tempfile.mkdtemp(prefix="%s_" % tag, dir=str(S.TMP)))
    cwd = os.getcwd()
    os.chdir(base)
    try:
        yield base
    finally:
        os.chdir(cwd)
        shutil.rmtree(base, ignore_errors=True)


def run_baseline(name, g, config, info=None):
    import wghac.sota_methods as sm
    captured = {"eval": {}}
    original = sm._evaluate_communities

    def _capture(graph_gcc, communities, gt_communities):
        captured["cover"] = [set(c) for c in communities]
        return captured["eval"]
    sm._evaluate_communities = _capture
    tf = sm.tempfile
    try:
        with temp_workdir(name.lower()) as base:
            sm.tempfile = _TempfileIn(base)
            sm.run_sota_method(name, g, [], config=dict(config))
    finally:
        sm._evaluate_communities = original
        sm.tempfile = tf
    cover = captured.get("cover", [])
    if not cover:
        raise ValueError("%s không trả cộng đồng nào" % name)
    if info is not None:
        info["implementation"] = captured["eval"].get("metric_status", {}).get("sota_output")
    return cover
