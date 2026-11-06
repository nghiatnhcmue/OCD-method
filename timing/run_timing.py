# Đo thời gian chạy của 9 phương pháp trên timing/subset.py: chỉ chạy khi máy rảnh, tối đa 5 lượt cùng
# lúc, mỗi lượt gắn một cặp nhân và một luồng tính, thứ tự xáo với hạt giống cố định.
#   python3 timing/run_timing.py [--methods ...] [--workers 5] [--time-limit 21600] [--rerun]

from __future__ import annotations

import argparse
import json
import os
import queue
import random
import resource
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from common import runner

TIMING = S.RESULTS / "timing"
CORES = [(2, 3), (4, 5), (6, 7), (8, 9), (10, 11)]
SEED = 2026


def timing_path(dataset, method, net_id):
    return TIMING / dataset / method / ("%s.json" % net_id)


def _is_ok(path):
    try:
        return json.loads(path.read_text()).get("status") == "ok"
    except (OSError, ValueError):
        return False


def _cpu(r):
    return r.ru_utime + r.ru_stime


def measure_one(dataset, method, net_id, cores):
    S.preload_native_libs()
    import wom_dot
    from common import datasets
    g, _ = datasets.load_network(datasets.find_network(dataset, net_id))
    module = runner.load_method(method)
    h = wom_dot.canonical_graph(g)
    s0, c0 = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    # đồng hồ thô: perf_counter (CLOCK_MONOTONIC) trong WSL bị nhân chỉnh nhịp, chạy nhanh 2-5%
    t0 = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
    cover, info = module.run(h)
    t1 = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
    s1, c1 = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    foreign = S.foreign_modules()
    if foreign:
        raise RuntimeError("Có module nạp từ ngoài thư mục thực nghiệm: %s" % ", ".join(foreign))
    cover = [sorted(int(x) for x in c) for c in cover if c]
    runner.write_json(timing_path(dataset, method, net_id), {
        "dataset": dataset, "net_id": net_id, "method": method, "status": "ok", "wall_seconds": t1 - t0,
        "clock": "CLOCK_MONOTONIC_RAW",
        "cpu_seconds": (_cpu(s1) - _cpu(s0)) + (_cpu(c1) - _cpu(c0)), "cores": cores,
        "affinity": sorted(os.sched_getaffinity(0)), "n_communities": len(cover), "cover": cover, "info": info,
        "finished": time.strftime("%Y-%m-%d %H:%M:%S")})
    print("[DONE] %s %s %s %.1fs" % (dataset, method, net_id, t1 - t0))


def _busy():
    ps = subprocess.run(["pgrep", "-af", "runner.py one|chay_kiem_tra.py chay|rescore.py|run_timing.py one"],
                        capture_output=True, text=True).stdout.splitlines()
    return [p for p in ps if "pgrep" not in p], os.getloadavg()[0]


def _run_job(job, free_cores, time_limit, workers):
    item, method = job
    dataset, net_id = item["dataset"], item["net_id"]
    a, b = free_cores.get()
    cores = "%d,%d" % (a, b)
    log = S.LOGS / "timing" / dataset / method / ("%s.log" % net_id)
    log.parent.mkdir(parents=True, exist_ok=True)
    load = os.getloadavg()[0]
    t0 = time.time()
    try:
        with log.open("w") as fh:
            p = subprocess.Popen(["taskset", "-c", cores, sys.executable, str(Path(__file__).resolve()), "one",
                                  dataset, method, net_id, cores], stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                rc = p.wait(timeout=time_limit)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                p.wait()
                rc = 124
    finally:
        free_cores.put((a, b))
    f = timing_path(dataset, method, net_id)
    if rc != 0 and not _is_ok(f):
        runner.write_json(f, {"dataset": dataset, "net_id": net_id, "method": method,
                              "status": "timeout" if rc == 124 else "error", "exit_code": rc, "time_limit": time_limit,
                              "wall_seconds": time.time() - t0, "cpu_seconds": None, "cores": cores,
                              "finished": time.strftime("%Y-%m-%d %H:%M:%S")})
    with (S.LOGS / "timing.txt").open("a") as fh:
        fh.write("%s rc=%d s=%d cores=%s load_at_start=%.2f workers=%d %s %s %s\n"
                 % (time.strftime("%Y-%m-%d %H:%M:%S"), rc, time.time() - t0, cores, load, workers, dataset, method, net_id))
    return rc


def main(argv=None):
    from timing.subset import timing_subset
    ap = argparse.ArgumentParser()
    ap.add_argument("--methods", nargs="*", default=list(S.METHODS))
    ap.add_argument("--workers", type=int, default=len(CORES))
    ap.add_argument("--time-limit", type=int, default=S.TIME_LIMIT)
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--skip-idle-check", action="store_true")
    a = ap.parse_args(argv)
    if not 1 <= a.workers <= len(CORES):
        raise SystemExit("--workers phải trong 1..%d" % len(CORES))
    busy, load = _busy()
    if (busy or load > 1.5) and not a.skip_idle_check:
        raise SystemExit("Máy chưa rảnh (tải 1 phút %.2f; tiến trình thực nghiệm: %d). Đợi các lô khác xong rồi chạy lại.\n%s"
                         % (load, len(busy), "\n".join(busy[:10])))
    jobs = [(item, m) for item in timing_subset() for m in a.methods
            if a.rerun or not _is_ok(timing_path(item["dataset"], m, item["net_id"]))]
    random.Random(SEED).shuffle(jobs)
    free_cores = queue.Queue()
    for c in CORES[:a.workers]:
        free_cores.put(c)
    S.LOGS.mkdir(parents=True, exist_ok=True)
    with (S.LOGS / "timing.txt").open("a") as fh:
        fh.write("%s START jobs=%d workers=%d time_limit=%d load=%.2f\n"
                 % (time.strftime("%Y-%m-%d %H:%M:%S"), len(jobs), a.workers, a.time_limit, load))
    print("Đo thời gian: %d lượt, %d tiến trình, giới hạn %d giây" % (len(jobs), a.workers, a.time_limit), flush=True)
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        rcs = list(ex.map(lambda j: _run_job(j, free_cores, a.time_limit, a.workers), jobs))
    print("Xong: %d ok, %d quá giờ, %d lỗi" % (rcs.count(0), rcs.count(124), len(rcs) - rcs.count(0) - rcs.count(124)))


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "one":
        measure_one(*sys.argv[2:])
    else:
        main()
