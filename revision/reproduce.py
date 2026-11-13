from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from common import runner

OUT = S.RESULTS / "revision" / "reproduce"
LOGS = S.LOGS / "revision" / "reproduce"
NETS = (("applications", "celegans_varshney"), ("applications", "netscience"), ("test1", "KT1_997000100_INJ"))


def config_v2():
    A = runner.load_method("proposed").algorithm
    p = A.HERE / "config_v2.json"
    return A.load_config(p if p.exists() else None)


def load(dataset, net_id):
    from common import datasets
    if dataset == "applications":
        from applications import networks
        return networks.load(net_id), None
    return datasets.load_network(datasets.find_network(dataset, net_id))


def stored(dataset, net_id):
    if dataset == "applications":
        return json.loads((S.RESULTS / "applications" / net_id / "proposed.json").read_text()), None
    raw = json.loads(runner.raw_path(dataset, "proposed", net_id).read_text())
    return raw, json.loads(runner.score_path(dataset, "proposed", net_id).read_text())


def sets(cover):
    return sorted(sorted(int(x) for x in c) for c in cover if c)


def same(a, b, tol=1e-12):
    if a is None or b is None:
        return a is None and b is None
    a, b = float(a), float(b)
    if math.isnan(a) or math.isnan(b):
        return math.isnan(a) and math.isnan(b)
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def run_one(dataset, net_id):
    S.preload_native_libs()
    import wom_dot
    from common import evaluate
    A = runner.load_method("proposed").algorithm
    g, truth = load(dataset, net_id)
    h = wom_dot.canonical_graph(g)
    t0 = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
    out = A.run_dot_ccm_v2(h, config_v2(), details=True)
    seconds = time.clock_gettime(time.CLOCK_MONOTONIC_RAW) - t0
    foreign = S.foreign_modules()
    if foreign:
        raise RuntimeError("Có module nạp từ ngoài thư mục thực nghiệm: %s" % ", ".join(foreign))
    raw, score = stored(dataset, net_id)
    checks = {"cover": sets(out["cover"]) == sets(raw["cover"])}
    if dataset == "applications":
        checks["pre_cover"] = sets(out["pre_cover"]) == sets(raw["pre_cover"])
        checks["cores"] = sets(out["cores"]) == sets(raw["cores"])
        table = out["table"]
        new_adds = [[int(u), int(c), float(table[u][c][3])] for u, c in out["adds"]]
        old_adds = [[int(a[0]), int(a[1]), float(a[5])] for a in raw["adds"]]
        checks["adds"] = [a[:2] for a in new_adds] == [a[:2] for a in old_adds]
        checks["adds_p"] = checks["adds"] and all(same(a[2], b[2]) for a, b in zip(new_adds, old_adds))
        for k in ("kappa", "eta", "c_max"):
            checks[k] = same(out[k], raw[k])
    else:
        cover = [set(c) for c in out["cover"] if c]
        new = evaluate.evaluate(dataset, h, cover, truth)
        old = score["scores"]
        checks["scores"] = set(new) == set(old) and all(same(new[k], old[k]) for k in old)
        stats = evaluate.cover_stats(h, cover)
        checks["cover_stats"] = all(same(stats[k], score["cover_stats"][k]) for k in score["cover_stats"])
    rec = {"dataset": dataset, "net_id": net_id, "seconds": seconds, "clock": "CLOCK_MONOTONIC_RAW",
           "config_version": config_v2()["version"], "checks": checks, "ok": all(checks.values())}
    runner.write_json(OUT / dataset / ("%s.json" % net_id), rec)
    print("[DONE] %s %s ok=%s %.0fs %s" % (dataset, net_id, rec["ok"], seconds, checks))


def _job(job):
    dataset, net_id = job
    log = LOGS / dataset / ("%s.log" % net_id)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w") as fh:
        return subprocess.call([sys.executable, str(Path(__file__).resolve()), "one", dataset, net_id],
                               stdout=fh, stderr=subprocess.STDOUT)


def main():
    with ThreadPoolExecutor(max_workers=len(NETS)) as ex:
        rcs = list(ex.map(_job, NETS))
    for (dataset, net_id), rc in zip(NETS, rcs):
        p = OUT / dataset / ("%s.json" % net_id)
        rec = json.loads(p.read_text()) if p.exists() and rc == 0 else {"ok": False, "checks": {"exit_code": rc}}
        print("%s %s ok=%s %s" % (dataset, net_id, rec["ok"], rec["checks"]))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "one":
        run_one(*sys.argv[2:])
    else:
        main()
