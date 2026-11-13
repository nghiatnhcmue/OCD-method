"""Bài kiểm tra nhanh: mọi phương pháp chạy trọn quy trình trên một mạng LFR N = 200, tổng thời gian dưới 5 phút.

python3 tests/smoke.py
"""
from __future__ import annotations

import json
import sys
import time
from importlib import metadata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S

FIX = Path(__file__).resolve().parent / "fixtures"
LIMIT = 300


def check_versions():
    bad = []
    for line in (S.ROOT / "requirements.txt").read_text().splitlines():
        if "==" not in line:
            continue
        name, want = line.strip().split("==")
        try:
            have = metadata.version(name)
        except metadata.PackageNotFoundError:
            have = None
        if have != want:
            bad.append("%s: cần %s, có %s" % (name, want, have))
    return bad


def main():
    S.preload_native_libs()
    import networkx as nx
    import wom_dot
    from common import evaluate, runner
    bad = check_versions()
    for b in bad:
        print("PHIÊN BẢN KHÁC:", b)
    g0 = nx.Graph()
    for line in (FIX / "lfr200.tsv").read_text().splitlines():
        u, v, w = line.split()
        g0.add_edge(int(u), int(v), weight=float(w))
    truth = [set(c) for c in json.loads((FIX / "lfr200_gt.json").read_text())]
    g = wom_dot.canonical_graph(g0)
    failed, t_all = [], time.perf_counter()
    for m in S.METHODS:
        t0 = time.perf_counter()
        try:
            cover, _ = runner.load_method(m).run(g.copy())
            s = evaluate.evaluate("test2", g0, [set(c) for c in cover if c], truth)
            print("%-11s %6.1f s  ONMI %.3f  %d cụm" % (m, time.perf_counter() - t0, s["onmi_mgh"], len(cover)), flush=True)
        except Exception as e:
            failed.append(m)
            print("%-11s LỖI %s: %s" % (m, type(e).__name__, e), flush=True)
    total = time.perf_counter() - t_all
    print("Tổng %.1f s" % total)
    if failed or bad or total > LIMIT:
        sys.exit("KHÔNG ĐẠT: lỗi %s, phiên bản khác %d, thời gian %.0f s" % (failed, len(bad), total))
    print("ĐẠT")


if __name__ == "__main__":
    main()
