from __future__ import annotations

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from common import runner

OUT = S.RESULTS / "audit" / "rerun"
LOGS = S.LOGS / "audit" / "rerun"
NET = ("test2", "lfrw_n1000_mut0.1_muw0.1_on0_omx_seed1")
JOBS = [(m, NET[0], NET[1], 1) for m in ("oslom", "slpa", "infomap", "bigclam", "clusterone", "aslpaw", "wghac", "danmf")]
JOBS += [("proposed", "applications", n, k) for n in ("celegans_varshney", "netscience") for k in (1, 2)]


def load(dataset, net_id):
    from common import datasets
    if dataset == "applications":
        from applications import networks
        return networks.load(net_id), None
    return datasets.load_network(datasets.find_network(dataset, net_id))


def stored(method, dataset, net_id):
    if dataset == "applications":
        return json.loads((S.RESULTS / "applications" / net_id / "proposed.json").read_text())
    return json.loads(runner.raw_path(dataset, method, net_id).read_text())


def run_one(method, dataset, net_id, k):
    S.preload_native_libs()
    import wom_dot
    g, truth = load(dataset, net_id)
    module = runner.load_method(method)
    t0 = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
    cover, info = module.run(wom_dot.canonical_graph(g))
    seconds = time.clock_gettime(time.CLOCK_MONOTONIC_RAW) - t0
    cover = sorted(sorted(int(x) for x in c) for c in cover if c)
    old = sorted(sorted(int(x) for x in c) for c in stored(method, dataset, net_id)["cover"] if c)
    rec = {"method": method, "dataset": dataset, "net_id": net_id, "run": int(k), "seconds": seconds,
           "same_as_stored": cover == old, "n_communities": len(cover), "stored_n_communities": len(old),
           "info": info, "cover": cover}
    if cover != old and truth is not None:
        from metrics.scoring import score
        rec["onmi_vs_stored"] = score(g, cover, old)["onmi_mgh"]
    runner.write_json(OUT / ("%s_%s_%s_%s.json" % (method, dataset, net_id, k)), rec)
    print("[DONE] %s %s same=%s %.0fs" % (method, net_id, rec["same_as_stored"], seconds))


def _job(job):
    log = LOGS / ("%s_%s_%s.log" % (job[0], job[2], job[3]))
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w") as fh:
        return subprocess.call([sys.executable, str(Path(__file__).resolve()), "one", *map(str, job)],
                               stdout=fh, stderr=subprocess.STDOUT, timeout=7200)


def main():
    with ThreadPoolExecutor(max_workers=8) as ex:
        rcs = list(ex.map(_job, JOBS))
    for j, rc in zip(JOBS, rcs):
        p = OUT / ("%s_%s_%s_%s.json" % tuple(j))
        r = json.loads(p.read_text()) if p.exists() else {}
        print(j, "rc=%d" % rc, "same=%s" % r.get("same_as_stored"), r.get("onmi_vs_stored", ""))


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "one":
        run_one(*sys.argv[2:])
    else:
        main()
