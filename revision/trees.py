from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from common import runner

OUT = S.RESULTS / "revision" / "trees"
LOGS = S.LOGS / "revision" / "trees"
APPS = ("celegans_varshney", "netscience", "brain_coactivation")


def all_jobs(sets=None):
    from common import datasets
    jobs = [("applications", n) for n in APPS] if not sets else []
    for ds in sets or ("test1", "test2", "test3", datasets.LARGE):
        jobs += [(ds, d["net_id"]) for d in datasets.list_networks(ds)]
    return jobs


def out_path(dataset, net_id):
    return OUT / dataset / ("%s.json" % net_id)


def load(dataset, net_id):
    from common import datasets
    if dataset == "applications":
        from applications import networks
        return networks.load(net_id), None
    return datasets.load_network(datasets.find_network(dataset, net_id))


def stored_cover(dataset, net_id):
    from common import datasets
    if dataset == "applications":
        p = S.RESULTS / "applications" / net_id / "proposed.json"
    elif dataset == datasets.LARGE:
        p = S.RESULTS / "timing_n5000" / "proposed" / ("%s.json" % net_id)
    else:
        p = runner.raw_path(dataset, "proposed", net_id)
    return json.loads(p.read_text())["cover"]


def sets(cover, keep_empty=False):
    return [sorted(int(x) for x in c) for c in cover if c or keep_empty]


def clock():
    return time.clock_gettime(time.CLOCK_MONOTONIC_RAW)


def rho(node):
    return max(0.0, (node.h_death - node.h_birth) / node.h_death) if node.h_death and node.h_death > 0 else 0.0


def run_one(dataset, net_id):
    S.preload_native_libs()
    import wom_dot
    import methods.dothac as D
    from common import evaluate
    from metrics.scoring import score
    A = runner.load_method("proposed").algorithm
    cfg = A.load_config(A.HERE / "config_v2.json")
    g0, truth = load(dataset, net_id)
    g = wom_dot.canonical_graph(g0)
    t0 = clock()
    ctx, dendrogram, timing = A.phase_one(g, cfg)
    tree_seconds = clock() - t0
    W = sum(float(x.get("weight", 1.0)) for _, _, x in g.edges(data=True))
    phi = [D._weighted_conductance(g, t.members, W) for t in dendrogram.tree_nodes()]
    rec = {"dataset": dataset, "net_id": net_id, "status": "ok", "clock": "CLOCK_MONOTONIC_RAW",
           "tree_seconds": tree_seconds, "phase1_seconds": timing, "n_nodes": g.number_of_nodes(),
           "n_edges": g.number_of_edges(), "eta": ctx.eta, "c_max": ctx.c_max, "leaves": [int(x) for x in ctx.nodes],
           "merges": [[int(a), int(b), float(h)] for a, b, h in dendrogram.merges], "variants": {}}
    psi, rhos = {}, {}
    for name, flag in (("off", False), ("on", True)):
        c = dict(cfg, monotone_heights=flag)
        nodes = dendrogram.tree_nodes(monotone=flag)
        rhos[name] = [rho(t) for t in nodes]
        psi[name] = [r * (1.0 - f) * len(t.members) for r, f, t in zip(rhos[name], phi, nodes)]
        t1 = clock()
        selected, cover, cores = A.phase_one_cover(g, ctx, dendrogram, c)
        final, adds, _, kappa = A._phase_two(g, cover, cores, c["q_bh"])
        v = {"selected": D.mos_v1_select(nodes, g, W), "pre_cover": sets(cover, True), "cores": sets(cores, True),
             "final": sets(final), "added": len(adds), "kappa": kappa, "seconds": clock() - t1}
        if truth is not None:
            pre, fin = [set(x) for x in cover if x], [set(x) for x in final if x]
            v["scores_pre"] = evaluate.evaluate(dataset, g, pre, truth)
            v["scores_final"] = evaluate.evaluate(dataset, g, fin, truth)
            v["stats_final"] = evaluate.cover_stats(g, fin)
        rec["variants"][name] = v
    off, on = rec["variants"]["off"], rec["variants"]["on"]
    rec["n_rho_changed"] = sum(1 for a, b in zip(rhos["off"], rhos["on"]) if abs(a - b) > 1e-12)
    rec["n_psi_changed"] = sum(1 for a, b in zip(psi["off"], psi["on"]) if abs(a - b) > 1e-12)
    rec["selected_same"] = off["selected"] == on["selected"]
    for part in ("pre_cover", "final"):
        a, b = [x for x in off[part] if x], [x for x in on[part] if x]
        rec["onmi_on_off_" + part] = 1.0 if sorted(a) == sorted(b) else score(g, b, a)["onmi_mgh"]
    from common import datasets
    if dataset not in datasets.EXTRA_DIRS:
        rec["matches_main"] = sorted(off["final"]) == sorted(sets(stored_cover(dataset, net_id)))
    foreign = S.foreign_modules()
    if foreign:
        raise RuntimeError("Có module nạp từ ngoài thư mục thực nghiệm: %s" % ", ".join(foreign))
    runner.write_json(out_path(dataset, net_id), rec)
    print("[DONE] %s %s %.0fs matches_main=%s selected_same=%s" % (dataset, net_id, tree_seconds,
                                                                 rec.get("matches_main"), rec["selected_same"]))


def _is_ok(path):
    try:
        return json.loads(path.read_text()).get("status") == "ok"
    except (OSError, ValueError):
        return False


def _run_job(job, time_limit):
    dataset, net_id = job
    log = LOGS / dataset / ("%s.log" % net_id)
    log.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with log.open("w") as fh:
        p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "one", dataset, net_id],
                             stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = p.wait(timeout=time_limit)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait()
            rc = 124
    f = out_path(dataset, net_id)
    if rc != 0 and not _is_ok(f):
        runner.write_json(f, {"dataset": dataset, "net_id": net_id, "status": "timeout" if rc == 124 else "error",
                              "exit_code": rc, "time_limit": time_limit, "seconds": time.time() - t0})
    with (S.LOGS / "revision" / "trees.txt").open("a") as fh:
        fh.write("%s rc=%d s=%d %s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), rc, time.time() - t0, dataset, net_id))
    return rc


def main(argv=None):
    from common import datasets
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[], help="bộ:mạng")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--large-workers", type=int, default=2)
    ap.add_argument("--time-limit", type=int, default=S.TIME_LIMIT)
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--sets", nargs="*", default=[], help="chỉ các bộ này (mặc định: 162 mạng, N = 5000, ứng dụng)")
    a = ap.parse_args(argv)
    jobs = all_jobs(a.sets)
    if a.only:
        wanted = [tuple(x.split(":", 1)) for x in a.only]
        unknown = set(wanted) - set(jobs)
        if unknown:
            raise SystemExit("Không có: %s" % ", ".join(":".join(x) for x in sorted(unknown)))
        jobs = [j for j in jobs if j in set(wanted)]
    jobs = [j for j in jobs if a.rerun or not _is_ok(out_path(*j))]
    heavy_sets = (datasets.LARGE, "test3")
    heavy = deque(sorted((j for j in jobs if j[0] in heavy_sets), key=lambda j: j[0] != datasets.LARGE))
    light = deque(j for j in jobs if j[0] not in heavy_sets)
    n_heavy = max(1, min(a.large_workers, a.workers))
    lock = threading.Lock()
    rcs = []

    def worker(takes_heavy):
        while True:
            with lock:
                if takes_heavy and heavy:
                    job = heavy.popleft()
                elif light:
                    job = light.popleft()
                else:
                    return
            rc = _run_job(job, a.time_limit)
            with lock:
                rcs.append(rc)
    (S.LOGS / "revision").mkdir(parents=True, exist_ok=True)
    with (S.LOGS / "revision" / "trees.txt").open("a") as fh:
        fh.write("%s START jobs=%d workers=%d time_limit=%d\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), len(jobs),
                                                                  a.workers, a.time_limit))
    print("Dựng cây: %d mạng, %d tiến trình" % (len(jobs), a.workers), flush=True)
    threads = [threading.Thread(target=worker, args=(i < n_heavy,)) for i in range(a.workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Xong: %d ok, %d quá giờ, %d lỗi" % (rcs.count(0), rcs.count(124), len(rcs) - rcs.count(0) - rcs.count(124)))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "one":
        run_one(*sys.argv[2:])
    else:
        main()
