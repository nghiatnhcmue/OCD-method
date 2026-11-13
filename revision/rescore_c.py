"""Chấm lại mọi lượt chạy theo hai quy ước cho đỉnh không được gán, và thêm MMR, Acc, Frac cho mạng protein.

drop: như bảng đã công bố (đỉnh không được gán bị để ngoài phủ).
singletons: mỗi đỉnh không được gán thành một cụm một đỉnh.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S

OUT = S.RESULTS / "round_c" / "rescore"
METHODS = list(S.METHODS) + list(S.EXTRA_METHODS)
SETS = ("test1", "test2", "test3")
PHASE2 = S.RESULTS / "revision" / "phase2"


def jobs(v3_config):
    out = []
    for ds in SETS:
        for m in METHODS:
            for p in sorted((S.RAW / ds / m).glob("*.json")):
                out.append((ds, m, p.stem, str(p), None))
        if v3_config:
            for p in sorted((PHASE2 / ds).glob("*.json")):
                out.append((ds, "proposed_v3", p.stem, str(p), v3_config))
    return out


def one(job):
    ds, method, net_id, path, cfg = job
    try:
        S.preload_native_libs()
        import wom_dot
        from common import complex_metrics as CX
        from common import datasets, evaluate
        r = json.loads(Path(path).read_text())
        if cfg:
            cover, status = r["configs"][cfg]["cover"], r["status"]
        else:
            cover, status = r.get("cover", []), r.get("status")
        if status != "ok" or not cover:
            return [{"dataset": ds, "method": method, "net_id": net_id, "status": status}]
        g0, truth = datasets.load_network(datasets.find_network(ds, net_id))
        g = wom_dot.canonical_graph(g0) if cfg else g0
        cover = [set(int(x) for x in c) for c in cover if c]
        covered = set().union(*cover)
        rows = []
        for conv in ("drop", "singletons"):
            c = cover if conv == "drop" else cover + [{u} for u in g.nodes() if u not in covered]
            row = {"dataset": ds, "method": method, "net_id": net_id, "status": "ok", "convention": conv,
                   "coverage": len(covered & set(g.nodes())) / g.number_of_nodes(), "n_communities": len(c)}
            row.update(evaluate.evaluate(ds, g, c, truth))
            if ds == "test3":
                pred = CX.restrict(cover, truth)
                row.update({"cx_" + k: v for k, v in CX.complex_scores(pred, truth).items()})
                labeled = set().union(*truth)
                if pred:
                    from common.evaluate import _metrics
                    m = _metrics(g.subgraph(labeled).copy(), pred, truth)
                    row["cx_onmi_mgh"] = m["onmi_mgh"]
                row["cx_coverage"] = len(set().union(*pred)) / len(labeled) if pred else 0.0
            rows.append(row)
        return rows
    except Exception as e:
        return [{"dataset": ds, "method": method, "net_id": net_id, "status": "error: %s: %s" % (type(e).__name__, e)}]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--v3-config", default="", help="tên cấu hình trong results/revision/phase2 cho dòng proposed_v3")
    a = ap.parse_args()
    js = jobs(a.v3_config)
    print("Chấm lại %d lượt, %d tiến trình" % (len(js), a.workers), flush=True)
    rows = []
    with Pool(a.workers) as pool:
        for i, rs in enumerate(pool.imap_unordered(one, js), 1):
            rows += rs
            if i % 200 == 0 or i == len(js):
                print("  %d/%d" % (i, len(js)), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    cols = []
    for r in rows:
        cols += [k for k in r if k not in cols]
    rows.sort(key=lambda r: (r["dataset"], r["method"], r["net_id"], r.get("convention", "")))
    with (OUT / "runs.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    bad = [r for r in rows if r["status"] != "ok"]
    print("Đã ghi %s (%d dòng, %d không ok)" % (OUT / "runs.csv", len(rows), len(bad)))
    for r in bad[:20]:
        print("  ", r)


if __name__ == "__main__":
    main()
