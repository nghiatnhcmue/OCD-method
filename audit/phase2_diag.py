import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "common"))
import settings as S  # noqa: E402
from common import datasets, evaluate, runner  # noqa: E402

OUT = S.RESULTS / "audit" / "phase2_diag"
SMALL = ["lfrw_n1000_mut0.3_muw0.3_on0_omx_seed1", "lfrw_n1000_mut0.3_muw0.3_on0_omx_seed2",
         "lfrw_n1000_mut0.3_muw0.3_on100_om2_seed1", "lfrw_n1000_mut0.3_muw0.3_on100_om2_seed2"]


def jobs():
    return [(datasets.LARGE, d["net_id"]) for d in datasets.list_networks(datasets.LARGE)] + [("test2", n) for n in SMALL]


def one(dataset, net_id):
    S.preload_native_libs()
    A = runner.load_method("proposed").algorithm
    g, truth = datasets.load_network(datasets.find_network(dataset, net_id))
    t0 = time.time()
    r = A.run_dot_ccm_v2(g, details=True)
    secs = time.time() - t0
    if dataset == datasets.LARGE:
        ref = json.loads((S.RESULTS / "timing_n5000" / "proposed" / ("%s.json" % net_id)).read_text())
    else:
        ref = json.loads(runner.raw_path(dataset, "proposed", net_id).read_text())
    final = sorted(sorted(int(x) for x in c) for c in r["cover"] if c)
    same = final == sorted(sorted(int(x) for x in c) for c in ref["cover"] if c)
    pre = [set(c) for c in r["pre_cover"] if c]
    cores = [set(c) for c in r["cores"]]
    best = []
    for c in cores:
        best.append(max(range(len(truth)), key=lambda i: len(truth[i] & c)))
    adds = []
    for u, c in r["adds"]:
        t, mu, var, p = r["table"][u][c]
        k = sum(1 for v in g[u] if v in cores[c])
        s = g.degree(u, weight="weight")
        adds.append({"k": k, "deg": g.degree(u), "share": t / s if s > 0 else 0.0, "z": (t - mu) / var ** 0.5 if var > 0 else 0.0,
                     "p": p, "mu_share": mu / s if s > 0 else 0.0, "correct": u in truth[best[c]]})
    pre_sets = [set(c) for c in pre]
    rec = {"dataset": dataset, "net_id": net_id, "seconds": secs, "same_as_reference": same, "n_cores": len(cores),
           "kappa": r["kappa"], "n_adds": len(adds),
           "final": {**evaluate.cover_stats(g, [set(c) for c in final]), **evaluate.evaluate(dataset, g, [set(c) for c in final], truth)},
           "phase1": {**evaluate.cover_stats(g, pre_sets), **evaluate.evaluate(dataset, g, pre_sets, truth)},
           "adds": adds}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("%s.json" % net_id)).write_text(json.dumps(rec, default=float))
    print("[DONE] %s same=%s adds=%d onmi final %.3f phase1 %.3f %.0fs" % (
        net_id, same, len(adds), rec["final"]["onmi_mgh"], rec["phase1"]["onmi_mgh"], secs), flush=True)


def run_job(job):
    dataset, net_id = job
    if (OUT / ("%s.json" % net_id)).exists():
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / ("%s.log" % net_id)).open("w") as fh:
        return subprocess.call([sys.executable, __file__, "one", dataset, net_id], stdout=fh, stderr=subprocess.STDOUT)


def main(workers):
    js = jobs()
    print("%s %d jobs, %d workers" % (time.strftime("%H:%M:%S"), len(js), workers), flush=True)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        rcs = list(ex.map(run_job, js))
    print("%s done rc=%s" % (time.strftime("%H:%M:%S"), rcs), flush=True)
    for f in sorted(OUT.glob("*.json")):
        r = json.loads(f.read_text())
        a = r["adds"]
        ks = np.array([x["k"] for x in a]) if a else np.array([0])
        print("%s same=%s cores=%d adds=%d correct=%.2f k=1:%d k=2:%d k>=3:%d share_med=%.3f | ONMI final %.3f phase1 %.3f | "
              "mem final %.2f phase1 %.2f" % (
                  r["net_id"], r["same_as_reference"], r["n_cores"], r["n_adds"],
                  np.mean([x["correct"] for x in a]) if a else float("nan"), (ks == 1).sum(), (ks == 2).sum(), (ks >= 3).sum(),
                  np.median([x["share"] for x in a]) if a else float("nan"), r["final"]["onmi_mgh"], r["phase1"]["onmi_mgh"],
                  r["final"]["mean_memberships"], r["phase1"]["mean_memberships"]))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "one":
        one(sys.argv[2], sys.argv[3])
    else:
        main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
