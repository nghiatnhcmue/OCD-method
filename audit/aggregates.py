from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from scipy.stats import wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S

OUT = S.RESULTS / "audit"
METRICS = ["onmi_mgh", "onmi_lfk", "f1", "onf1", "omega"]
TOL = 1e-12


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out, best = [1.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        best = max(best, min(1.0, (len(ps) - rank) * ps[i]))
        out[i] = best
    return out


def best_counts(df, ds, metric, only_overlap=False):
    d = df[(df.dataset == ds) & (df.status == "ok")]
    if only_overlap:
        d = d[d["on"].astype(float) > 0]
    x = d.pivot_table(index="net_id", columns="method", values=metric)
    x = x.dropna(subset=["proposed"])
    top = x.max(axis=1)
    strict = sum(1 for n in x.index if x.loc[n, "proposed"] >= top[n] - TOL
                 and (x.loc[n].drop("proposed") < x.loc[n, "proposed"] - TOL).all())
    tie = sum(1 for n in x.index if x.loc[n, "proposed"] >= top[n] - TOL)
    return strict, tie, len(x)


def wilcoxon_table(df):
    rows = []
    for ds in ("test1", "test2"):
        d = df[(df.dataset == ds) & (df.status == "ok")]
        key = "topology_id" if ds == "test1" else "net_id"
        for metric in METRICS:
            dd = d[d["on"].astype(float) > 0] if metric == "onf1" else d
            x = dd.pivot_table(index=key, columns="method", values=metric, aggfunc="mean")
            fam = []
            for m in sorted(c for c in x.columns if c != "proposed"):
                y = x[["proposed", m]].dropna()
                diff = y["proposed"] - y[m]
                p = float(wilcoxon(y["proposed"], y[m]).pvalue) if (diff != 0).any() else 1.0
                fam.append({"dataset": ds, "metric": metric, "vs": m, "n": len(y), "win": int((diff > 0).sum()),
                            "lose": int((diff < 0).sum()), "mean_diff": float(diff.mean()), "p": p})
            for r, ph in zip(fam, holm([r["p"] for r in fam])):
                r["p_holm"] = ph
            rows += fam
    return pd.DataFrame(rows)


def phase2_effect():
    rows = []
    for p in sorted((S.RESULTS / "ablation" / "min_edges").glob("*/*.json")):
        r = json.loads(p.read_text())
        v = r["variants"]
        rows.append({"dataset": r["dataset"], "net_id": r["net_id"], "full": v["full"]["scores"]["onmi_mgh"],
                     "no_phase2": v["no_phase2"]["scores"]["onmi_mgh"]})
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(S.RESULTS / "scores_all.csv")
    print("runs ok per method/dataset:", df[df.status == "ok"].groupby(["method", "dataset"]).size().to_dict())
    print("total ok runs:", int((df.status == "ok").sum()), "rows:", len(df))
    for metric, ov in (("onmi_mgh", False), ("onf1", True)):
        print("test1 best %s: strict %d, with ties %d, of %d" % ((metric,) + best_counts(df, "test1", metric, ov)))
        print("test2 best %s: strict %d, with ties %d, of %d" % ((metric,) + best_counts(df, "test2", metric, ov)))
    # ONF1 trung bình: trên mọi mạng hay chỉ mạng có chồng lấn
    for ds in ("test1", "test2"):
        d = df[(df.dataset == ds) & (df.method == "proposed")]
        print("%s ONF1 mean over rows with value: %.4f (n=%d); nets with on>0: %d" % (
            ds, d.onf1.mean(), d.onf1.notna().sum(), int((d["on"].astype(float) > 0).sum())))
    # Pha II trên 168 mạng
    meta = df.drop_duplicates(["dataset", "net_id"]).set_index(["dataset", "net_id"])["on"].to_dict()
    pe = phase2_effect()
    pe["worse"] = pe.full < pe.no_phase2 - TOL
    pe["on"] = [float(meta.get((d, n), 0) or 0) if d != "test2_n5000" else (0 if "_on0_" in n else 500)
                for d, n in zip(pe.dataset, pe.net_id)]
    print("phase II worse:", int(pe.worse.sum()), pe[pe.worse].groupby("dataset").size().to_dict(),
          "worse & non-overlap N=1000:", int((pe.worse & (pe["on"] == 0) & pe.dataset.isin(["test1", "test2"])).sum()))
    for ds in ("test1", "test2"):
        x = pe[pe.dataset == ds]
        if ds == "test1":
            x = x.assign(topo=[n.rsplit("_", 1)[0] for n in x.net_id]).groupby("topo").agg(
                full=("full", "mean"), no_phase2=("no_phase2", "mean"), on=("on", "first"))
        print("%s full - no_phase2: all %.3f, overlap %.3f, non-overlap %.3f" % (
            ds, (x.full - x.no_phase2).mean(), (x.full - x.no_phase2)[x["on"] > 0].mean(),
            (x.full - x.no_phase2)[x["on"] == 0].mean()))
    # thời gian theo quy trình đo
    for ds in ("test1", "test2", "test3"):
        for m in ("proposed", "wghac"):
            v = [json.loads(p.read_text()) for p in (S.RESULTS / "timing" / ds / m).glob("*.json")]
            s = [x["wall_seconds"] for x in v if x.get("status") == "ok"]
            print("timing %s %s: n=%d median=%.1f mean=%.1f threads_env=%s" % (
                ds, m, len(s), statistics.median(s) if s else -1, statistics.mean(s) if s else -1,
                sorted({str(x.get("threads", "")) for x in v})))
    t3 = {}
    for m in ("proposed", "wghac"):
        for p in (S.RESULTS / "timing" / "test3" / m).glob("*.json"):
            t3.setdefault(p.stem, {})[m] = json.loads(p.read_text()).get("wall_seconds")
    print("test3 timing per network:", t3)
    n5 = [json.loads(p.read_text()) for p in (S.RESULTS / "timing_n5000").glob("*/*.json")]
    print("N=5000 runs:", Counter((x["method"], x["status"]) for x in n5))
    sc = pd.read_csv(S.RESULTS / "timing_n5000" / "scores.csv")
    print("N=5000 scored methods:", sorted(sc.method.unique()), "rows:", len(sc))
    print(sc.groupby("method").onmi_mgh.mean().sort_values(ascending=False).round(3).to_dict())
    w = wilcoxon_table(df)
    w.to_csv(OUT / "wilcoxon_holm.csv", index=False)
    print("wilcoxon rows:", len(w), "not significant (Holm >= 0.05):")
    print(w[w.p_holm >= 0.05][["dataset", "metric", "vs", "win", "lose", "mean_diff", "p_holm"]].to_string())


if __name__ == "__main__":
    main()
