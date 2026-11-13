from __future__ import annotations

import argparse
import os
import queue
import resource
import signal
import subprocess
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from common import runner
from timing.run_timing import CORES, _busy, _cpu, _is_ok
from applications import networks

# RUN_TAG=round_c ghi sang results/round_c/applications/, không đụng kết quả cũ
TAG = os.environ.get("RUN_TAG", "")
OUT = S.RESULTS / TAG / "applications"
METHODS = ("wghac", "proposed")


def _rel(net, method, r):
    return Path(net, method) if r == 0 else Path("stability", net, method, "r%d" % r)


def out_path(net, method, r=0):
    return OUT / _rel(net, method, r).with_suffix(".json")


def _sets(cover):
    return [sorted(int(x) for x in c) for c in cover if c]


def _proposed_details(module, h):
    out = module.algorithm.run_dot_ccm_v2(h, details=True)
    table = out["table"]
    info = {"status": out["status"], "added_memberships": out["added_memberships"], "step_seconds": out["timing"]}
    details = {"pre_cover": _sets(out["pre_cover"]), "cores": _sets(out["cores"]),
               "adds": [[int(u), int(c)] + [float(x) for x in table[u][c]] for u, c in out["adds"]],
               "adds_columns": ["node", "community", "weight_to_core", "expected", "variance", "p"],
               "kappa": float(out["kappa"]), "eta": float(out["eta"]), "c_max": float(out["c_max"])}
    return out["cover"], info, details


def measure_one(net, method, r, cores):
    r = int(r)
    S.preload_native_libs()
    import wom_dot
    g = networks.load(net)
    extra = {}
    if r:
        g, removed = networks.perturb(g, r)
        extra = {"seed": networks.SEED + r, "removed_edges": len(removed)}
    module = runner.load_method(method)
    h = wom_dot.canonical_graph(g)
    s0, c0 = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    t0 = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
    if method == "proposed" and r == 0:
        cover, info, details = _proposed_details(module, h)
    else:
        (cover, info), details = module.run(h), {}
    t1 = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
    s1, c1 = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    foreign = S.foreign_modules()
    if foreign:
        raise RuntimeError("Có module nạp từ ngoài thư mục thực nghiệm: %s" % ", ".join(foreign))
    cover = _sets(cover)
    runner.write_json(out_path(net, method, r), {
        "net": net, "method": method, "perturbation": r, "status": "ok", **extra,
        "n_nodes": h.number_of_nodes(), "n_edges": h.number_of_edges(), "wall_seconds": t1 - t0,
        "clock": "CLOCK_MONOTONIC_RAW", "cpu_seconds": (_cpu(s1) - _cpu(s0)) + (_cpu(c1) - _cpu(c0)), "cores": cores,
        "affinity": sorted(os.sched_getaffinity(0)), "n_communities": len(cover), "cover": cover, "info": info,
        **details, "finished": time.strftime("%Y-%m-%d %H:%M:%S")})
    print("[DONE] %s %s r%d %.1fs" % (net, method, r, t1 - t0))


def _run_job(job, free_cores, time_limit, workers):
    net, method, r = job
    a, b = free_cores.get()
    cores = "%d,%d" % (a, b)
    log = S.LOGS / TAG / "applications" / _rel(net, method, r).with_suffix(".log")
    log.parent.mkdir(parents=True, exist_ok=True)
    load = os.getloadavg()[0]
    t0 = time.time()
    try:
        with log.open("w") as fh:
            p = subprocess.Popen(["taskset", "-c", cores, sys.executable, str(Path(__file__).resolve()), "one",
                                  net, method, str(r), cores], stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
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
    f = out_path(net, method, r)
    if rc != 0 and not _is_ok(f):
        runner.write_json(f, {"net": net, "method": method, "perturbation": r,
                              "status": "timeout" if rc == 124 else "error", "exit_code": rc, "time_limit": time_limit,
                              "wall_seconds": time.time() - t0, "cpu_seconds": None, "cores": cores,
                              "finished": time.strftime("%Y-%m-%d %H:%M:%S")})
    with (S.LOGS / TAG / "applications.txt").open("a") as fh:
        fh.write("%s rc=%d s=%d cores=%s load_at_start=%.2f workers=%d %s %s r%d\n"
                 % (time.strftime("%Y-%m-%d %H:%M:%S"), rc, time.time() - t0, cores, load, workers, net, method, r))
    return rc


def _idle():
    busy, load = _busy()
    ps = subprocess.run(["pgrep", "-af", "applications/run.py one"], capture_output=True, text=True).stdout.splitlines()
    return busy + [p for p in ps if "pgrep" not in p], load


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--methods", nargs="*", default=list(METHODS))
    ap.add_argument("--nets", nargs="*", default=list(networks.NETS))
    ap.add_argument("--perturbations", type=int, default=10)
    ap.add_argument("--workers", type=int, default=len(CORES))
    ap.add_argument("--time-limit", type=int, default=S.TIME_LIMIT)
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--skip-idle-check", action="store_true")
    a = ap.parse_args(argv)
    if not 1 <= a.workers <= len(CORES):
        raise SystemExit("--workers phải trong 1..%d" % len(CORES))
    busy, load = _idle()
    if (busy or load > 1.5) and not a.skip_idle_check:
        raise SystemExit("Máy chưa rảnh (tải 1 phút %.2f; tiến trình thực nghiệm: %d). Đợi các lô khác xong rồi chạy lại.\n%s"
                         % (load, len(busy), "\n".join(busy[:10])))

    def todo(net, m, r):
        return a.rerun or not _is_ok(out_path(net, m, r))

    def perturbations(net, m):
        return [(net, m, r) for r in range(1, a.perturbations + 1) if todo(net, m, r)]

    nets = sorted(a.nets, key=lambda n: -networks.load(n).number_of_edges())
    pending = [(n, m, 0) for n in nets for m in a.methods if todo(n, m, 0)]
    pending += [j for n in nets for m in a.methods if not todo(n, m, 0) for j in perturbations(n, m)]
    free_cores = queue.Queue()
    for c in CORES[:a.workers]:
        free_cores.put(c)
    (S.LOGS / TAG).mkdir(parents=True, exist_ok=True)
    with (S.LOGS / TAG / "applications.txt").open("a") as fh:
        fh.write("%s START jobs=%d workers=%d time_limit=%d load=%.2f\n"
                 % (time.strftime("%Y-%m-%d %H:%M:%S"), len(pending), a.workers, a.time_limit, load))
    print("Mạng ứng dụng: %d lượt chờ (chưa kể bản nhiễu của lượt gốc chưa xong), %d tiến trình, giới hạn %d giây"
          % (len(pending), a.workers, a.time_limit), flush=True)
    rcs, running = [], {}
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        while pending or running:
            while pending and len(running) < a.workers:
                job = pending.pop(0)
                running[ex.submit(_run_job, job, free_cores, a.time_limit, a.workers)] = job
            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for f in done:
                net, m, r = running.pop(f)
                rcs.append(f.result())
                if r == 0 and rcs[-1] == 0:
                    pending += perturbations(net, m)
    print("Xong: %d ok, %d quá giờ, %d lỗi" % (rcs.count(0), rcs.count(124), len(rcs) - rcs.count(0) - rcs.count(124)))


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "one":
        measure_one(*sys.argv[2:])
    else:
        main()
