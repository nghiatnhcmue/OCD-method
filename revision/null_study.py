from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from common import runner

OUT = S.RESULTS / "revision" / "null"
FIG = S.RESULTS / "revision" / "figures"
LOGS = S.LOGS / "revision" / "null"
TREES = S.RESULTS / "revision" / "trees"
NETS = (("test2", "lfrw_n1000_mut0.3_muw0.3_on0_omx_seed1"), ("test2_n5000", "lfrw_n5000_mut0.3_muw0.3_on0_omx_seed1"),
        ("test3", "collins2007"), ("test1", "KT1_997000100_INJ"))
KINDS = ("gamma", "empirical")
METHODS = ("normal", "cpoisson", "count")
FAMILIES = ("node_all", "node", "global")
ALPHAS = (0.001, 0.01, 0.05)
QS = (0.001, 0.01, 0.05)
SEED = 42


def null_graph(model, kind, xi, rng):
    import networkx as nx
    n = len(model.nodes)
    edges = []
    for i in range(n - 1):
        j = np.arange(i + 1, n)
        p = np.minimum(1.0, model.d[i] * model.d[j] / model.dT)
        hit = rng.random(j.size) < p
        if not hit.any():
            continue
        jj = j[hit]
        f = model.s[i] * model.s[jj] / model.sT / p[hit]
        if kind == "empirical":
            z = rng.choice(xi, size=jj.size)
        elif model.kappa > 0:
            z = rng.gamma(1.0 / model.kappa, model.kappa, size=jj.size)
        else:
            z = np.ones(jj.size)
        edges += [(model.nodes[i], model.nodes[k], w) for k, w in zip(jj, f * z)]
    h = nx.Graph()
    h.add_nodes_from(model.nodes)
    h.add_weighted_edges_from(edges)
    return h


def run_one(dataset, net_id, kind, reps):
    S.preload_native_libs()
    import ccm_tail as C
    import wom_dot
    from common import datasets
    from wom_v1 import CCM
    A = runner.load_method("proposed").algorithm
    tree = json.loads((TREES / dataset / ("%s.json" % net_id)).read_text())
    cover = [set(c) for c in tree["variants"]["off"]["pre_cover"]]
    cores = [set(c) for c in tree["variants"]["off"]["cores"]]
    g = wom_dot.canonical_graph(datasets.load_network(datasets.find_network(dataset, net_id))[0])
    model0 = CCM(g)
    xi = C.xi_sample(g, model0)
    reps_out, pooled = [], {m: [] for m in METHODS}
    n_family = 0
    for r in range(reps):
        t0 = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
        h = wom_dot.canonical_graph(null_graph(model0, kind, xi, np.random.default_rng(SEED + r)))
        model = CCM(h)
        member = np.zeros((len(model.nodes), len(cores)), dtype=bool)
        for c, com in enumerate(cover):
            for u in com:
                member[model.idx[u], c] = True
        rec = {"rep": r, "seed": SEED + r, "n_edges": h.number_of_edges(), "kappa": model.kappa, "rates": {},
               "adds": {}, "nodes_with_adds": {}, "seconds": {}}
        for m in METHODS:
            t1 = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
            P, T, E, in_core, _ = A.phase_two_pvalues(h, cores, {"phase2_pvalue": m, "phase2_xi": "gamma"}, model)
            rec["seconds"][m] = time.clock_gettime(time.CLOCK_MONOTONIC_RAW) - t1
            fam = ~in_core
            pf = P[fam]
            n_family = pf.size
            rec["rates"][m] = {str(a): float((pf <= a).mean()) for a in ALPHAS}
            pooled[m].append(pf[pf < 1.0])
            for family in FAMILIES:
                for q in QS:
                    acc = C.accept(P, E, in_core, family, q) & ~member
                    key = "%s_%s" % (family, q)
                    rec["adds"].setdefault(m, {})[key] = int(acc.sum())
                    rec["nodes_with_adds"].setdefault(m, {})[key] = int(acc.any(axis=1).sum())
        rec["seconds"]["total"] = time.clock_gettime(time.CLOCK_MONOTONIC_RAW) - t0
        reps_out.append(rec)
        print("[rep %d] edges=%d kappa=%.3f old_adds=%d new_adds=%d %.0fs" % (
            r, rec["n_edges"], model.kappa, rec["adds"]["normal"]["node_all_0.001"],
            rec["adds"]["cpoisson"]["node_0.001"], rec["seconds"]["total"]), flush=True)
    summary = {"rates": {m: {str(a): float(np.mean([x["rates"][m][str(a)] for x in reps_out])) for a in ALPHAS}
                         for m in METHODS},
               "adds_mean": {m: {k: float(np.mean([x["adds"][m][k] for x in reps_out])) for k in reps_out[0]["adds"][m]}
                             for m in METHODS},
               "adds_max": {m: {k: int(max(x["adds"][m][k] for x in reps_out)) for k in reps_out[0]["adds"][m]}
                            for m in METHODS},
               "nodes_with_adds_mean": {m: {k: float(np.mean([x["nodes_with_adds"][m][k] for x in reps_out]))
                                            for k in reps_out[0]["nodes_with_adds"][m]} for m in METHODS},
               "n_family_pairs": n_family, "n_cores": len(cores), "n_nodes": len(model0.nodes)}
    qq = {}
    for m in METHODS:
        p = np.sort(np.concatenate(pooled[m]))
        total = n_family * reps
        k = np.unique(np.round(np.geomspace(1, max(len(p), 1), 400)).astype(int)) if len(p) else np.array([], int)
        qq[m] = {"expected": ((k) / (total + 1)).tolist(), "observed": p[k - 1].tolist() if len(p) else [],
                 "n_below_one": int(len(p)), "n_total": int(total)}
    runner.write_json(OUT / kind / dataset / ("%s.json" % net_id), {
        "dataset": dataset, "net_id": net_id, "null": kind, "reps": reps, "summary": summary, "qq": qq,
        "replicates": reps_out, "clock": "CLOCK_MONOTONIC_RAW"})
    plot(dataset, net_id, kind, qq)


def plot(dataset, net_id, kind, qq):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    labels = {"normal": "xấp xỉ chuẩn (mã cũ)", "cpoisson": "compound Poisson (mới)", "count": "số cạnh, Poisson-nhị thức"}
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    top = max((-np.log10(np.array(qq[m]["expected"]))).max() for m in METHODS if qq[m]["expected"])
    ax.plot([0, top], [0, top], color="black", lw=1.0, ls="--", zorder=1, label="đường chéo: p hợp lệ nằm dưới")
    for m in METHODS:
        e, o = np.array(qq[m]["expected"]), np.array(qq[m]["observed"])
        if len(e):
            ax.plot(-np.log10(e), -np.log10(np.maximum(o, 1e-300)), lw=1.4, zorder=2, label=labels[m])
    ax.set_xlabel("−log10 p kỳ vọng")
    ax.set_ylabel("−log10 p quan sát (xấp xỉ chuẩn vượt khỏi khung)")
    ax.set_xlim(0, top * 1.03)
    ax.set_ylim(0, top * 1.5)
    ax.set_title("%s (null %s)" % (net_id, kind), fontsize=8)
    ax.legend(fontsize=7)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / ("qq_%s_%s.png" % (kind, net_id)), dpi=150)
    plt.close(fig)


def summarize():
    L = ["# Pha II trên đồ thị null", "",
         "Mỗi mạng: lõi và phủ Pha I lấy từ đồ thị gốc (mã hiện tại), 20 đồ thị null sinh từ CCM đã khớp, CCM khớp lại "
         "trên từng đồ thị null. Mọi mức thuộc được thêm trên đồ thị null đều sai. Họ kiểm định khi tính tỉ lệ: mọi cặp "
         "(u, j) với u không thuộc lõi K_j (cặp có T = 0 nhận p = 1).", ""]
    files = sorted(OUT.glob("*/*/*.json"))
    L += ["## Tỉ lệ p ≤ α", "",
          "Ngưỡng chấp nhận: α + 3·SE với SE = √(α(1−α)/n), n = số cặp × số đồ thị null.", "",
          "| Mạng | ξ của null | Số cặp | p chuẩn (mã cũ) α = 0,001 / 0,01 / 0,05 | compound Poisson | số cạnh | p mới ≤ ngưỡng |",
          "|---|---|---:|---|---|---|:---:|"]
    verdicts = []
    for p in files:
        r = json.loads(p.read_text())
        s = r["summary"]
        n = s["n_family_pairs"] * r["reps"]
        ok = all(s["rates"][m][str(a)] <= a + 3 * np.sqrt(a * (1 - a) / n) for m in ("cpoisson", "count") for a in ALPHAS)
        verdicts.append(ok)
        L.append("| %s | %s | %d | %s | %s | %s | %s |" % (
            r["net_id"], r["null"], s["n_family_pairs"],
            *[" / ".join("%.4f" % s["rates"][m][str(a)] for a in ALPHAS) for m in METHODS], "có" if ok else "KHÔNG"))
    L += ["", "## Số mức thuộc sai trên mỗi đồ thị null (trung bình / lớn nhất)", "",
          "Mã cũ = p chuẩn, BH theo đỉnh trên mọi lõi (node_all), q = 0,001.", "",
          "| Mạng | ξ | Mã cũ | p chuẩn, node, 0,001 | CP node 0,001 | CP node 0,01 | CP node 0,05 | CP global 0,001 "
          "| CP global 0,01 | CP global 0,05 | Số cạnh, node, 0,001 |", "|---|---|" + "---:|" * 9]
    cols = [("normal", "node_all_0.001"), ("normal", "node_0.001"), ("cpoisson", "node_0.001"), ("cpoisson", "node_0.01"),
            ("cpoisson", "node_0.05"), ("cpoisson", "global_0.001"), ("cpoisson", "global_0.01"),
            ("cpoisson", "global_0.05"), ("count", "node_0.001")]
    for p in files:
        r = json.loads(p.read_text())
        s = r["summary"]
        L.append("| %s | %s | %s |" % (r["net_id"], r["null"], " | ".join(
            "%.1f / %d" % (s["adds_mean"][m][k], s["adds_max"][m][k]) for m, k in cols)))
    L += ["", "Biểu đồ QQ: `results/revision/figures/qq_<ξ>_<mạng>.png`.", ""]
    (OUT / "SUMMARY.md").write_text("\n".join(L))
    print("\n".join(L))
    return all(verdicts)


def _job(job, reps):
    dataset, net_id, kind = job
    log = LOGS / kind / dataset / ("%s.log" % net_id)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w") as fh:
        return subprocess.call([sys.executable, str(Path(__file__).resolve()), "one", dataset, net_id, kind, str(reps)],
                               stdout=fh, stderr=subprocess.STDOUT)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", nargs="*", default=[], help="bộ:mạng")
    ap.add_argument("--kinds", nargs="*", default=list(KINDS))
    a = ap.parse_args(argv)
    nets = [n for n in NETS if not a.only or "%s:%s" % n in a.only]
    jobs = [(ds, net, kind) for kind in a.kinds for ds, net in nets]
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        rcs = list(ex.map(lambda j: _job(j, a.reps), jobs))
    for j, rc in zip(jobs, rcs):
        print(j, "rc=%d" % rc)


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "one":
        run_one(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]))
    elif len(sys.argv) == 2 and sys.argv[1] == "summary":
        summarize()
    elif len(sys.argv) == 2 and sys.argv[1] == "plots":
        for f in sorted(OUT.glob("*/*/*.json")):
            r = json.loads(f.read_text())
            plot(r["dataset"], r["net_id"], r["null"], r["qq"])
    else:
        main()
