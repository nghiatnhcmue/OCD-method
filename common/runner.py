"""Chạy một phương pháp trên một bộ kiểm tra, mỗi mạng một tiến trình con có giới hạn thời gian.

    python3 methods/<phương pháp>/run_test<k>.py [net_id ...] [--workers 4] [--time-limit 21600] [--rerun]
    python3 common/runner.py one <bộ> <phương pháp> <net_id>
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from common import datasets


def raw_path(dataset, method, net_id):
    return S.RAW / dataset / method / ("%s.json" % net_id)


def score_path(dataset, method, net_id):
    return S.SCORES / dataset / method / ("%s.json" % net_id)


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=float))
    tmp.replace(path)


def load_method(method):
    spec = importlib.util.spec_from_file_location("method_" + method, S.ROOT / "methods" / method / "method.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def score_and_write(item, method, raw, g=None, truth=None):
    from common import evaluate
    if g is None:
        g, truth = datasets.load_network(item)
    cover = [set(c) for c in raw.get("cover", [])]
    ok = raw.get("status") == "ok" and cover
    rec = {k: item[k] for k in ("dataset", "net_id", "topology_id", "regime", "mu", "mu_w", "on", "om", "replicate")}
    rec.update(method=method, method_name=S.METHODS[method], status=raw.get("status"), seconds=raw.get("seconds"),
               n_nodes=g.number_of_nodes(), n_edges=g.number_of_edges(),
               cover_stats=evaluate.cover_stats(g, cover) if ok else {},
               scores=evaluate.evaluate(item["dataset"], g, cover, truth) if ok else {},
               source=raw.get("source", "Thuc_Nghiem"))
    write_json(score_path(item["dataset"], method, item["net_id"]), rec)
    return rec


def run_one(dataset, method, net_id):
    S.preload_native_libs()
    import wom_dot
    item = datasets.find_network(dataset, net_id)
    g, truth = datasets.load_network(item)
    module = load_method(method)
    t0 = time.perf_counter()
    cover, info = module.run(wom_dot.canonical_graph(g))
    seconds = time.perf_counter() - t0
    foreign = S.foreign_modules()
    if foreign:
        raise RuntimeError("Có module nạp từ ngoài thư mục thực nghiệm: %s" % ", ".join(foreign))
    raw = {"dataset": dataset, "net_id": net_id, "method": method, "seconds": seconds, "status": "ok", "info": info,
           "cover": [sorted(int(x) for x in c) for c in cover if c], "source": "Thuc_Nghiem"}
    write_json(raw_path(dataset, method, net_id), raw)
    score_path(dataset, method, net_id).unlink(missing_ok=True)
    rec = score_and_write(item, method, raw, g, truth)
    print("[DONE] %s %s %s ONMI=%.4f %.1fs" % (dataset, net_id, method, rec["scores"].get("onmi_mgh", float("nan")), seconds))


def has_ok_result(dataset, method, net_id):
    try:
        return json.loads(raw_path(dataset, method, net_id).read_text()).get("status") == "ok"
    except (OSError, ValueError):
        return False


def _run_subprocess(dataset, method, net_id, time_limit):
    log = S.LOGS / dataset / method / ("%s.log" % net_id)
    log.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with log.open("w") as fh:
        p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "one", dataset, method, net_id],
                             stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = p.wait(timeout=time_limit)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait()
            rc = 124  # hết giờ
    seconds = time.time() - t0
    # lượt chạy lại thất bại không ghi đè kết quả ok đã có
    if rc != 0 and not has_ok_result(dataset, method, net_id):
        raw = {"dataset": dataset, "net_id": net_id, "method": method, "seconds": seconds,
               "status": "timeout" if rc == 124 else "error", "time_limit": time_limit, "exit_code": rc, "cover": [],
               "source": "Thuc_Nghiem"}
        write_json(raw_path(dataset, method, net_id), raw)
        score_and_write(datasets.find_network(dataset, net_id), method, raw)
    S.LOGS.mkdir(parents=True, exist_ok=True)
    with (S.LOGS / "progress.txt").open("a") as fh:
        fh.write("%s rc=%d s=%d %s %s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), rc, seconds, dataset, method, net_id))
    return rc


def run_dataset(dataset, method, argv=None):
    ap = argparse.ArgumentParser(description="%s trên %s" % (S.METHODS[method], S.DATASETS[dataset]))
    ap.add_argument("networks", nargs="*", help="net_id (mặc định: mọi mạng của bộ)")
    ap.add_argument("--workers", type=int, default=S.WORKERS, help="số tiến trình song song")
    ap.add_argument("--time-limit", type=int, default=S.TIME_LIMIT, help="giới hạn giây cho một mạng")
    ap.add_argument("--rerun", action="store_true", help="chạy lại cả mạng đã có kết quả ok")
    a = ap.parse_args(argv)
    nets = [d["net_id"] for d in datasets.list_networks(dataset)]
    if a.networks:
        unknown = set(a.networks) - set(nets)
        if unknown:
            raise SystemExit("Không có trong %s: %s" % (dataset, ", ".join(sorted(unknown))))
        nets = [n for n in nets if n in set(a.networks)]
    todo = [n for n in nets if a.rerun or not has_ok_result(dataset, method, n)]
    print("%s / %s: %d mạng cần chạy (bỏ qua %d đã có), %d tiến trình, giới hạn %d giây"
          % (S.METHODS[method], dataset, len(todo), len(nets) - len(todo), a.workers, a.time_limit), flush=True)
    S.LOGS.mkdir(parents=True, exist_ok=True)
    with (S.LOGS / "progress.txt").open("a") as fh:
        fh.write("%s START %s %s networks=%d workers=%d time_limit=%d\n"
                 % (time.strftime("%Y-%m-%d %H:%M:%S"), dataset, method, len(todo), a.workers, a.time_limit))
    with ThreadPoolExecutor(max_workers=max(1, a.workers)) as ex:
        rcs = list(ex.map(lambda n: _run_subprocess(dataset, method, n, a.time_limit), todo))
    print("Xong: %d ok, %d quá giờ, %d lỗi" % (rcs.count(0), rcs.count(124), len(rcs) - rcs.count(0) - rcs.count(124)))


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "one":
        run_one(*sys.argv[2:])
    else:
        print(__doc__)
        sys.exit(1)
