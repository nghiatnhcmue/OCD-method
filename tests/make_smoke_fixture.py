"""Sinh mạng LFR N = 200 cho bài kiểm tra nhanh, bằng chương trình LFR gốc đã dùng cho Kiểm tra 2."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S

LFR = S.REPO / "results" / "phat_trien_v2" / "tai_ve" / "lfr_goc" / "src" / "weighted_undirected" / "benchmark"
OUT = Path(__file__).resolve().parent / "fixtures"
SEED = 20261112
ARGS = ["-N", "200", "-k", "10", "-maxk", "20", "-mut", "0.2", "-muw", "0.2", "-beta", "1.5", "-t1", "2", "-t2", "1",
        "-minc", "10", "-maxc", "25", "-on", "20", "-om", "2"]

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "time_seed.dat").write_text("%d\n" % SEED)
        subprocess.run([str(LFR)] + ARGS, cwd=tmp, check=True, capture_output=True)
        w = {}
        for line in (tmp / "network.dat").read_text().splitlines():
            u, v, x = line.split()
            u, v = int(u) - 1, int(v) - 1
            if u != v:
                w.setdefault((min(u, v), max(u, v)), float(x))
        comm = {}
        for line in (tmp / "community.dat").read_text().splitlines():
            f = line.split()
            for c in f[1:]:
                comm.setdefault(int(c), []).append(int(f[0]) - 1)
    (OUT / "lfr200.tsv").write_text("".join("%d\t%d\t%r\n" % (u, v, x) for (u, v), x in sorted(w.items())))
    (OUT / "lfr200_gt.json").write_text(json.dumps([sorted(c) for _, c in sorted(comm.items())]))
    (OUT / "lfr200.json").write_text(json.dumps({"generator": str(LFR.relative_to(S.REPO)), "args": ARGS, "seed": SEED}))
    print("%d cạnh, %d cộng đồng" % (len(w), len(comm)))
