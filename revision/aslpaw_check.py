"""Kiểm tính tất định của ASLPAw và độ dao động của kết quả đã lưu.

python3 revision/aslpaw_check.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S

OUT = S.RESULTS / "round_c" / "aslpaw_check"
FIX = S.ROOT / "tests" / "fixtures"
NETS = [("test1", "KT1_997001500_INJ"), ("test2", "lfrw_n1000_mut0.3_muw0.3_on100_om2_seed1")]
REPEATS = 3


def load(dataset, net_id):
    import networkx as nx
    from common import datasets
    if dataset == "fixture":
        g = nx.Graph()
        for line in (FIX / "lfr200.tsv").read_text().splitlines():
            u, v, w = line.split()
            g.add_edge(int(u), int(v), weight=float(w))
        return g, [set(c) for c in json.loads((FIX / "lfr200_gt.json").read_text())]
    return datasets.load_network(datasets.find_network(dataset, net_id))


def one(method, dataset, net_id, k):
    S.preload_native_libs()
    import wom_dot
    from common import evaluate, runner
    g0, truth = load(dataset, net_id)
    t0 = time.perf_counter()
    cover, info = runner.load_method(method).run(wom_dot.canonical_graph(g0))
    rec = {"method": method, "dataset": dataset, "net_id": net_id, "k": int(k), "seconds": time.perf_counter() - t0,
           "cover": sorted(sorted(int(x) for x in c) for c in cover if c),
           "scores": evaluate.evaluate(dataset if dataset != "fixture" else "test2", g0, [set(c) for c in cover if c], truth)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("%s_%s_%s_%s.json" % (method, dataset, net_id, k))).write_text(json.dumps(rec, default=float))


def jobs():
    js = [(m, "fixture", "lfr200", k) for m in ("aslpaw", "aslpaw_seeded") for k in (1, 2)]
    js += [("aslpaw", ds, n, k) for ds, n in NETS for k in range(1, REPEATS + 1)]
    return js


def run_job(j):
    f = OUT / ("%s_%s_%s_%s.json" % j)
    if f.exists():
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / ("%s_%s_%s_%s.log" % j)).open("w") as fh:
        return subprocess.call([sys.executable, __file__, "one", *map(str, j)], stdout=fh, stderr=subprocess.STDOUT)


def summary():
    from metrics.scoring import score
    from common import runner
    L = ["# ASLPAw: tính tất định", ""]
    recs = [json.loads(p.read_text()) for p in sorted(OUT.glob("*.json"))]
    g, _ = load("fixture", "lfr200")
    for m in ("aslpaw", "aslpaw_seeded"):
        r = [x for x in recs if x["method"] == m and x["dataset"] == "fixture"]
        if len(r) == 2:
            same = r[0]["cover"] == r[1]["cover"]
            L.append("- %s, mạng N = 200, hai tiến trình: phủ %s; ONMI so nhãn %.3f và %.3f; ONMI giữa hai phủ %.3f" % (
                m, "trùng khít" if same else "KHÁC", r[0]["scores"]["onmi_mgh"], r[1]["scores"]["onmi_mgh"],
                1.0 if same else score(g, r[0]["cover"], r[1]["cover"])["onmi_mgh"]))
    L += ["", "Chạy lại ASLPAw như bảng đã công bố (5 lần khởi tạo lại, giữ lần nhiều cộng đồng nhất):", "",
          "| Mạng | ONMI đã lưu | ONMI các lần chạy lại | Trùng phủ đã lưu |", "|---|---:|---|---:|"]
    for ds, n in NETS:
        stored = json.loads(runner.raw_path(ds, "aslpaw", n).read_text())
        st = json.loads(runner.score_path(ds, "aslpaw", n).read_text())["scores"]["onmi_mgh"]
        r = [x for x in recs if x["net_id"] == n]
        same = sum(sorted(sorted(c) for c in stored["cover"]) == x["cover"] for x in r)
        L.append("| %s | %.3f | %s | %d/%d |" % (n, st, ", ".join("%.3f" % x["scores"]["onmi_mgh"] for x in r), same, len(r)))
    (OUT / "SUMMARY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "one":
        one(*sys.argv[2:])
    else:
        with ThreadPoolExecutor(max_workers=10) as ex:
            print("rc:", list(ex.map(run_job, jobs())), flush=True)
        summary()
