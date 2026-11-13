"""Bảng của Đợt C: chọn cấu hình Pha II trên tập chọn, kết quả v3 trên 162 mạng và N = 5000, K thật, quy ước chấm,
độ đo phức hợp protein, tập khóa. Ghi results/round_c/REPORT.md.

python3 revision/round_c_report.py [--tune-only]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from audit.aggregates import wilcoxon_table
from common import datasets

OUT = S.RESULTS / "round_c"
PHASE2 = S.RESULTS / "revision" / "phase2"
TREES = S.RESULTS / "revision" / "trees"
CANDIDATES = ["cp_%s_%s" % (f, q) for f in ("node", "global") for q in (0.001, 0.01, 0.05)]
TIE = 0.005
NAMES = dict(S.ALL_METHODS, proposed="DOT-CCM v2 (đã công bố)", proposed_v3="DOT-CCM v3")
METRICS = ["onmi_mgh", "onmi_lfk", "onf1", "f1", "omega"]


def f3(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else "%.3f" % x


def md(df, cols, labels=None):
    labels = labels or cols
    L = ["| " + " | ".join(labels) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        L.append("| " + " | ".join(f3(r[c]) if isinstance(r[c], float) else str(r[c]) for c in cols) + " |")
    return L


def phase2_rows(sets, configs=None):
    rows = []
    for ds in sets:
        for p in sorted((PHASE2 / ds).glob("*.json")):
            r = json.loads(p.read_text())
            tree = json.loads((TREES / ds / p.name).read_text())
            base = {"dataset": ds, "net_id": p.stem, "overlap_truth": r["overlap_truth"]}
            rows.append(dict(base, config="v2", added=tree["variants"]["off"]["added"],
                             false_added=r["v2_false_added"], **tree["variants"]["off"]["scores_final"]))
            rows.append(dict(base, config="phase1_only", added=0, false_added=0, **tree["variants"]["on"]["scores_pre"]))
            for name, v in r["configs"].items():
                if configs is None or name in configs:
                    rows.append(dict(base, config=name, added=v["added"], false_added=v["false_added"], **v["scores"]))
    return pd.DataFrame(rows)


def choose(tune):
    g = tune[tune.config.isin(CANDIDATES)]
    t = g.groupby("config").agg(onmi=("onmi_mgh", "mean"), n=("net_id", "count"))
    t["false_disjoint"] = g[~g.overlap_truth].groupby("config").false_added.mean()
    t["q"] = [float(c.rsplit("_", 1)[1]) for c in t.index]
    best = t.onmi.max()
    near = t[t.onmi >= best - TIE].sort_values(["false_disjoint", "q"])
    return t.sort_values("onmi", ascending=False), near.index[0]


def tune_section(L):
    tune = phase2_rows(datasets.TUNE)
    table, chosen = choose(tune)
    ref = tune[tune.config.isin(["v2", "phase1_only"])].groupby("config").onmi_mgh.mean()
    L += ["## 1. Chọn họ kiểm định và q trên tập chọn (%d mạng)" % tune.net_id.nunique(), "",
          "Luật chọn: `results/round_c/PROTOCOL.md`. ONMI-MGH trung bình; mức thuộc sai trung bình trên mạng không chồng lấn.", "",
          "| Cấu hình | ONMI | Mức thuộc sai (không chồng lấn) | Số mạng |", "|---|---:|---:|---:|"]
    for c, r in table.iterrows():
        L.append("| %s%s | %.3f | %.2f | %d |" % (c, " **(chọn)**" if c == chosen else "", r.onmi, r.false_disjoint, r.n))
    L += ["", "Đối chứng trên cùng tập: v2 %.3f; Pha I v3 không Pha II %.3f." % (ref["v2"], ref["phase1_only"]), ""]
    by = tune[tune.config.isin(CANDIDATES + ["v2", "phase1_only"])].groupby(["dataset", "config"]).onmi_mgh.mean().unstack(0)
    L += ["Theo bộ:", "", "| Cấu hình | tune1 (như KT1) | tune2 (như KT2) |", "|---|---:|---:|"]
    for c, r in by.iterrows():
        L.append("| %s | %.3f | %.3f |" % (c, r["tune1"], r["tune2"]))
    L.append("")
    return chosen


def runs_frame():
    runs = pd.read_csv(OUT / "rescore" / "runs.csv")
    runs = runs[runs.status == "ok"]
    meta = pd.DataFrame([{k: d[k] for k in ("dataset", "net_id", "topology_id", "on")} for ds in ("test1", "test2", "test3")
                         for d in datasets.list_networks(ds)])
    return runs.merge(meta, on=["dataset", "net_id"], how="left")


def check_drop(runs, L):
    old = pd.read_csv(S.RESULTS / "scores_all.csv")
    old = old[old.status == "ok"][["dataset", "method", "net_id", "onmi_mgh"]]
    m = runs[runs.convention == "drop"].merge(old, on=["dataset", "method", "net_id"], suffixes=("", "_old"))
    diff = (m.onmi_mgh - m.onmi_mgh_old).abs().max()
    L += ["Kiểm tra: chấm lại theo quy ước cũ trùng `results/scores_all.csv` trên %d lượt, sai lệch ONMI lớn nhất %.1e." %
          (len(m), diff), ""]
    return diff


def main_tables(runs, chosen, L):
    order = ["proposed_v3", "proposed"] + [m for m in S.METHODS if m != "proposed"] + list(S.EXTRA_METHODS)
    for conv, title in (("drop", "đỉnh không được gán để ngoài (như bài)"), ("singletons", "đỉnh không được gán thành đơn tử")):
        L += ["## 2%s. Kiểm tra 1 và 2, %s" % ("a" if conv == "drop" else "b", title), "",
              "DOT-CCM v3 = Pha I có bao đơn điệu + p-value compound Poisson, cấu hình `%s`. ONF1 lấy trung bình trên mạng "
              "có chồng lấn. Wilcoxon + Holm: v3 so với từng phương pháp, KT1 theo 36 tô-pô (trung bình ba chế độ trọng "
              "số), KT2 theo 50 mạng." % chosen, ""]
        r = runs[runs.convention == conv]
        w = wilcoxon_table(r.replace({"method": {"proposed": "proposed_v2"}}).replace({"method": {"proposed_v3": "proposed"}}))
        for ds in ("test1", "test2"):
            d = r[r.dataset == ds]
            rows = []
            for m in order:
                x = d[d.method == m]
                if not len(x):
                    continue
                row = {"Phương pháp": NAMES[m], "n": len(x)}
                for k in METRICS:
                    row[k] = float((x[x["on"].astype(float) > 0] if k == "onf1" else x)[k].mean())
                ww = w[(w.dataset == ds) & (w.metric == "onmi_mgh") & (w.vs == ("proposed_v2" if m == "proposed" else m))]
                row["v3 thắng/thua, Holm"] = "-" if m == "proposed_v3" or not len(ww) else "%d/%d, %.1e" % (
                    ww.win.iloc[0], ww.lose.iloc[0], ww.p_holm.iloc[0])
                rows.append(row)
            t = pd.DataFrame(rows)
            L += ["**%s**" % ("Kiểm tra 1 (108 mạng)" if ds == "test1" else "Kiểm tra 2 (50 mạng)"), ""]
            L += md(t, ["Phương pháp", "n"] + METRICS + ["v3 thắng/thua, Holm"],
                    ["Phương pháp", "n", "ONMI-MGH", "ONMI-LFK", "ONF1", "F1", "Omega", "v3 thắng/thua (ONMI), Holm"])
            L.append("")
        w.to_csv(OUT / ("wilcoxon_%s.csv" % conv), index=False)
    L += ["Bảng Wilcoxon + Holm đủ 5 độ đo: `results/round_c/wilcoxon_drop.csv`, `wilcoxon_singletons.csv`.", ""]


def ppi_table(runs, L):
    order = ["proposed_v3", "proposed"] + [m for m in S.METHODS if m != "proposed"] + list(S.EXTRA_METHODS)
    cols = ["onmi_mgh", "labeled_onmi_mgh", "cx_onmi_mgh", "cx_mmr", "cx_acc", "cx_frac", "cx_coverage"]
    L += ["## 3. Mạng protein (4 mạng, CYC2008)", "",
          "Cột cx_: chỉ chấm trên protein có trong cả mạng lẫn CYC2008, bỏ cụm dự đoán còn dưới 3 protein "
          "(`common/complex_metrics.py`). MMR, Acc = √(Sn·PPV), Frac (ω > 0,25) theo Nepusz, Yu và Paccanaro (2012, đã đối chiếu Online Methods); Sn, PPV theo Brohée và van Helden (2006). "
          "ONMI toàn mạng ở hai quy ước.", ""]
    rows = []
    for m in order:
        x = runs[(runs.dataset == "test3") & (runs.method == m)]
        if not len(x):
            continue
        dr, sg = x[x.convention == "drop"], x[x.convention == "singletons"]
        rows.append({"Phương pháp": NAMES[m], "onmi_drop": float(dr.onmi_mgh.mean()), "onmi_single": float(sg.onmi_mgh.mean()),
                     **{c: float(dr[c].mean()) for c in cols[1:]}})
    t = pd.DataFrame(rows).sort_values("cx_mmr", ascending=False)
    L += md(t, ["Phương pháp", "onmi_drop", "onmi_single"] + cols[1:],
            ["Phương pháp", "ONMI toàn mạng (để ngoài)", "ONMI toàn mạng (đơn tử)", "ONMI có nhãn (cũ)", "ONMI cx",
             "MMR", "Acc", "Frac", "Độ phủ cx"])
    L.append("")


def n5000_table(chosen, L):
    v3 = phase2_rows([datasets.LARGE], configs=[chosen])
    sc = pd.read_csv(S.RESULTS / "timing_n5000" / "scores.csv")
    rows = []
    for name, x in [("DOT-CCM v3", v3[v3.config == chosen]), ("DOT-CCM v2 (đã công bố)", v3[v3.config == "v2"])] + [
            (S.METHODS[m], sc[sc.method == m]) for m in S.METHODS if m not in ("proposed", "wghac")]:
        on = x.net_id.str.contains("_on0_")
        rows.append({"Phương pháp": name, "rời": float(x[on].onmi_mgh.mean()), "chồng lấn": float(x[~on].onmi_mgh.mean()),
                     "TB": float(x.onmi_mgh.mean())})
    t = pd.DataFrame(rows).sort_values("TB", ascending=False)
    L += ["## 4. N = 5000 (6 mạng), ONMI-MGH", ""] + md(t, ["Phương pháp", "rời", "chồng lấn", "TB"]) + [""]


def locked_section(chosen, L):
    if not all((PHASE2 / ds).is_dir() for ds in datasets.LOCKED):
        L += ["## 5. Tập khóa", "", "Chưa chạy.", ""]
        return
    d = phase2_rows(datasets.LOCKED, configs=[chosen])
    L += ["## 5. Tập khóa (%d mạng, chạy một lần với cấu hình `%s`)" % (d.net_id.nunique(), chosen), "",
          "| Dòng | Bộ | ONMI-MGH | ONMI-LFK | ONF1 | F1 | Omega | Mức thuộc thêm (TB) | Sai (TB) |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    labels = {chosen: "DOT-CCM v3", "v2": "DOT-CCM v2", "phase1_only": "Pha I v3, không Pha II"}
    for ds in datasets.LOCKED:
        for c in (chosen, "v2", "phase1_only"):
            x = d[(d.dataset == ds) & (d.config == c)]
            L.append("| %s | %s | %s | %s | %s | %s | %s | %.1f | %.1f |" % (
                labels[c], ds, f3(x.onmi_mgh.mean()), f3(x.onmi_lfk.mean()), f3(x[x.overlap_truth].onf1.mean()),
                f3(x.f1.mean()), f3(x.omega.mean()), x.added.mean(), x.false_added.mean()))
        o = [json.loads(p.read_text()) for p in sorted((S.SCORES / ds / "oslom").glob("*.json"))]
        o = [r for r in o if r["status"] == "ok"]
        if o:
            sc = pd.DataFrame([r["scores"] for r in o])
            L.append("| OSLOM | %s | %s | %s | - | %s | %s | - | - |" % (ds, f3(sc.onmi_mgh.mean()), f3(sc.onmi_lfk.mean()),
                                                                         f3(sc.f1.mean()), f3(sc.omega.mean())))
    L.append("")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune-only", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    L = ["# Đợt C: kết quả", "", "Sinh bằng `python3 revision/round_c_report.py`.", ""]
    chosen = tune_section(L)
    print("Cấu hình chọn:", chosen)
    if not a.tune_only:
        runs = runs_frame()
        check_drop(runs, L)
        main_tables(runs, chosen, L)
        ppi_table(runs, L)
        n5000_table(chosen, L)
        locked_section(chosen, L)
    (OUT / ("TUNE.md" if a.tune_only else "REPORT.md")).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
