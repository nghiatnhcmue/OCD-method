from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from common import runner

OUT = S.RESULTS / "revision" / "phase2"
LOGS = S.LOGS / "revision" / "phase2"
TREES = S.RESULTS / "revision" / "trees"
# (tên, p-value, họ kiểm định, q)
CONFIGS = [("old", "normal", "node_all", 0.001)]
CONFIGS += [("cp_%s_%s" % (fam, q), "cpoisson", fam, q) for fam in ("node", "global") for q in (0.001, 0.01, 0.05)]
CONFIGS += [("count_node_0.001", "count", "node", 0.001)]
ONLY_CONFIGS = [c for c in os.environ.get("PHASE2_CONFIGS", "").split(",") if c]


def clock():
    return time.clock_gettime(time.CLOCK_MONOTONIC_RAW)


def load(dataset, net_id):
    from common import datasets
    if dataset == "applications":
        from applications import networks
        return networks.load(net_id), None
    return datasets.load_network(datasets.find_network(dataset, net_id))


def first_batch():
    from common import datasets
    nets = []
    for p in sorted((S.RESULTS / "ablation" / "min_edges").glob("*/*.json")):
        r = json.loads(p.read_text())
        v = r["variants"]
        if v["full"]["scores"]["onmi_mgh"] < v["no_phase2"]["scores"]["onmi_mgh"] - 1e-12 or r["dataset"] == datasets.LARGE:
            nets.append((r["dataset"], r["net_id"]))
    return nets


def run_one(dataset, net_id):
    S.preload_native_libs()
    import ccm_tail as C
    import wom_dot
    from common import evaluate
    from wom_v1 import CCM
    A = runner.load_method("proposed").algorithm
    tree = json.loads((TREES / dataset / ("%s.json" % net_id)).read_text())
    g0, truth = load(dataset, net_id)
    g = wom_dot.canonical_graph(g0)
    pre = [set(c) for c in tree["variants"]["on"]["pre_cover"]]
    cores = [set(c) for c in tree["variants"]["on"]["cores"]]
    model = CCM(g)
    member = np.zeros((len(model.nodes), len(cores)), dtype=bool)
    for c, com in enumerate(pre):
        for u in com:
            member[model.idx[u], c] = True
    overlap_truth = truth is not None and any(sum(u in t for t in truth) > 1 for u in set().union(*truth))

    def best_match(cover):
        return [max(range(len(truth)), key=lambda i: len(truth[i] & com)) if com else -1 for com in cover]
    best = best_match(pre) if truth else []
    v2_false = None
    if truth:
        off_pre = [set(c) for c in tree["variants"]["off"]["pre_cover"]]
        off_best = best_match(off_pre)
        v2_false = sum(1 for c, fin in enumerate(tree["variants"]["off"]["final"]) for u in set(fin) - off_pre[c]
                       if off_best[c] < 0 or u not in truth[off_best[c]])
    pv, secs, stats = {}, {}, {}
    needed = {m for name, m, _, _ in CONFIGS if not ONLY_CONFIGS or name in ONLY_CONFIGS or name == "old"}
    for m in sorted(needed):
        st = {}
        t0 = clock()
        pv[m] = A.phase_two_pvalues(g, cores, {"phase2_pvalue": m, "phase2_xi": "gamma"}, model, st)[:4]
        secs[m] = clock() - t0
        stats[m] = st
    rec = {"dataset": dataset, "net_id": net_id, "status": "ok", "clock": "CLOCK_MONOTONIC_RAW", "kappa": model.kappa,
           "n_cores": len(cores), "pvalue_seconds": secs, "cpoisson_stats": stats["cpoisson"],
           "overlap_truth": overlap_truth, "v2_false_added": v2_false, "configs": {}}
    for name, method, family, q in CONFIGS:
        if ONLY_CONFIGS and name not in ONLY_CONFIGS and name != "old":
            continue
        P, T, E, in_core = pv[method]
        t0 = clock()
        acc = C.accept(P, E, in_core, family, q) & ~member
        bh_seconds = clock() - t0
        rows, cols = np.nonzero(acc)
        adds = sorted((int(model.nodes[i]), int(c)) for i, c in zip(rows, cols))
        final = [set(c) for c in pre]
        for u, c in adds:
            final[c].add(u)
        cover = [x for x in final if x]
        v = {"pvalue": method, "family": family, "q": q, "added": len(adds),
             "nodes_with_adds": int(acc.any(axis=1).sum()), "phase2_seconds": secs[method] + bh_seconds,
             "cover": [sorted(int(x) for x in c) for c in cover], "stats": evaluate.cover_stats(g, cover)}
        if truth is not None:
            v["false_added"] = sum(1 for u, c in adds if best[c] < 0 or u not in truth[best[c]])
            v["scores"] = evaluate.evaluate(dataset, g, cover, truth)
        rec["configs"][name] = v
    old = sorted(rec["configs"]["old"]["cover"])
    rec["old_matches_tree_cache"] = old == sorted(c for c in tree["variants"]["on"]["final"] if c)
    foreign = S.foreign_modules()
    if foreign:
        raise RuntimeError("Có module nạp từ ngoài thư mục thực nghiệm: %s" % ", ".join(foreign))
    runner.write_json(OUT / dataset / ("%s.json" % net_id), rec)
    print("[DONE] %s %s %s match=%s" % (dataset, net_id, " ".join(
        "%s=%d" % (k, v["added"]) for k, v in rec["configs"].items()), rec["old_matches_tree_cache"]))


def _is_ok(path):
    try:
        return json.loads(path.read_text()).get("status") == "ok"
    except (OSError, ValueError):
        return False


def _run_job(job):
    dataset, net_id = job
    log = LOGS / dataset / ("%s.log" % net_id)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w") as fh:
        rc = subprocess.call([sys.executable, str(Path(__file__).resolve()), "one", dataset, net_id],
                             stdout=fh, stderr=subprocess.STDOUT)
    with (S.LOGS / "revision" / "phase2.txt").open("a") as fh:
        fh.write("%s rc=%d %s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), rc, dataset, net_id))
    return rc


def main(argv=None):
    from common import datasets
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", action="store_true", help="chỉ 35 mạng mà Pha II cũ làm giảm ONMI (gồm 6 mạng N = 5000)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--sets", nargs="*", default=[], help="chỉ các bộ này")
    ap.add_argument("--configs", default="", help="danh sách tên cấu hình, phân cách bằng dấu phẩy (mặc định: tất cả)")
    a = ap.parse_args(argv)
    if a.configs:
        os.environ["PHASE2_CONFIGS"] = a.configs
    ready = [(p.parent.name, p.stem) for p in sorted(TREES.glob("*/*.json")) if _is_ok(p)]
    if a.sets:
        ready = [j for j in ready if j[0] in a.sets]
    else:
        ready = [j for j in ready if j[0] not in datasets.EXTRA_DIRS]
    jobs = [j for j in ready if j in set(first_batch())] if a.first else ready
    jobs = [j for j in jobs if a.rerun or not _is_ok(OUT / j[0] / ("%s.json" % j[1]))]
    jobs.sort(key=lambda j: (j[0] != datasets.LARGE, j[0] != "test3"))
    queue, lock, rcs = deque(jobs), threading.Lock(), []

    def worker():
        while True:
            with lock:
                if not queue:
                    return
                job = queue.popleft()
            rc = _run_job(job)
            with lock:
                rcs.append(rc)
    (S.LOGS / "revision").mkdir(parents=True, exist_ok=True)
    print("Pha II: %d mạng, %d tiến trình" % (len(jobs), a.workers), flush=True)
    threads = [threading.Thread(target=worker) for _ in range(a.workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Xong: %d ok, %d lỗi" % (rcs.count(0), len(rcs) - rcs.count(0)))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "one":
        run_one(*sys.argv[2:])
    else:
        main()
