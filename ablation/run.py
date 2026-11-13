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

OUT = S.RESULTS / "ablation"
LOGS = S.LOGS / "ablation"


def out_path(group, dataset, net_id):
    return OUT / group / dataset / ("%s.json" % net_id)


def _is_ok(path):
    try:
        return json.loads(path.read_text()).get("status") == "ok"
    except (OSError, ValueError):
        return False


def run_one(group, dataset, net_id):
    S.preload_native_libs()
    from ablation import variants as V
    from common import datasets, evaluate
    g, truth = datasets.load_network(datasets.find_network(dataset, net_id))
    t0 = time.perf_counter()
    covers = V.run_group(group, g, V.A.load_config(V.A.HERE / "config_v2.json"))  # bảng bóc tách đã công bố dùng v2
    seconds = time.perf_counter() - t0
    foreign = S.foreign_modules()
    if foreign:
        raise RuntimeError("Có module nạp từ ngoài thư mục thực nghiệm: %s" % ", ".join(foreign))
    rec = {"group": group, "dataset": dataset, "net_id": net_id, "status": "ok", "seconds": seconds, "variants": {}}
    for name, cover in covers.items():
        cover = [sorted(int(x) for x in c) for c in cover if c]
        sets = [set(c) for c in cover]
        rec["variants"][name] = {"cover": cover, "cover_stats": evaluate.cover_stats(g, sets),
                                 "scores": evaluate.evaluate(dataset, g, sets, truth) if sets else {}}
    if group in ("base", "min_edges"):
        if dataset == datasets.LARGE:
            main = json.loads((S.RESULTS / "timing_n5000" / "proposed" / ("%s.json" % net_id)).read_text())
        else:
            main = json.loads(runner.raw_path(dataset, "proposed", net_id).read_text())
        ref = sorted(sorted(int(x) for x in c) for c in main["cover"] if c)
        rec["matches_main"] = sorted(rec["variants"]["full"]["cover"]) == ref
    runner.write_json(out_path(group, dataset, net_id), rec)
    print("[DONE] %s %s %s %.1fs" % (group, dataset, net_id, seconds))


def _run_job(job, time_limit):
    group, dataset, net_id = job
    log = LOGS / group / dataset / ("%s.log" % net_id)
    log.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with log.open("w") as fh:
        p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "one", group, dataset, net_id],
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
    f = out_path(group, dataset, net_id)
    if rc != 0 and not _is_ok(f):
        runner.write_json(f, {"group": group, "dataset": dataset, "net_id": net_id,
                              "status": "timeout" if rc == 124 else "error", "exit_code": rc,
                              "time_limit": time_limit, "seconds": time.time() - t0})
    with (S.LOGS / "ablation.txt").open("a") as fh:
        fh.write("%s rc=%d s=%d %s %s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), rc, time.time() - t0, group, dataset,
                                              net_id))
    return rc


def main(argv=None):
    from ablation.variants import GROUPS
    from common import datasets
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", nargs="*", default=list(GROUPS))
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--large-workers", type=int, default=2)
    ap.add_argument("--time-limit", type=int, default=S.TIME_LIMIT)
    ap.add_argument("--rerun", action="store_true")
    a = ap.parse_args(argv)
    jobs = [(grp, d["dataset"], d["net_id"]) for grp in a.groups for ds in GROUPS[grp]
            for d in datasets.list_networks(ds) if a.rerun or not _is_ok(out_path(grp, d["dataset"], d["net_id"]))]
    cost = {datasets.LARGE: -1, "test3": 0, "test1": 1, "test2": 1}
    jobs.sort(key=lambda j: (cost[j[1]], j[0] in ("no_ot", "slpa_weighted"), j[0], j[1], j[2]))
    heavy = deque(j for j in jobs if j[1] in (datasets.LARGE, "test3"))
    light = deque(j for j in jobs if j[1] not in (datasets.LARGE, "test3"))
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
    S.LOGS.mkdir(parents=True, exist_ok=True)
    with (S.LOGS / "ablation.txt").open("a") as fh:
        fh.write("%s START jobs=%d workers=%d time_limit=%d\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), len(jobs),
                                                                  a.workers, a.time_limit))
    print("Biến thể: %d lượt, %d tiến trình, giới hạn %d giây" % (len(jobs), a.workers, a.time_limit), flush=True)
    threads = [threading.Thread(target=worker, args=(i < n_heavy,)) for i in range(a.workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Xong: %d ok, %d quá giờ, %d lỗi" % (rcs.count(0), rcs.count(124), len(rcs) - rcs.count(0) - rcs.count(124)))


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "one":
        run_one(*sys.argv[2:])
    else:
        main()
