from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S

TEX = S.REPO / "luan_van" / "ieee_manuscript.tex"
OUT = S.RESULTS / "audit"
NAMES = {"DOT-CCM": "proposed", "wGHAC": "wghac", "OSLOM": "oslom", "SLPA": "slpa", "Infomap": "infomap",
         "BigCLAM": "bigclam", "DANMF": "danmf", "ClusterONE": "clusterone", "ASLPAw": "aslpaw"}
NUM = re.compile(r"-?\d[\d,]*\.?\d*")


def table_rows(label):
    text = TEX.read_text()
    body = text[text.index("\\label{tab:%s}" % label):]
    body = body[:body.index("\\bottomrule")]
    rows = []
    for line in body.splitlines():
        if "&" not in line or "toprule" in line:
            continue
        cells = [re.sub(r"\\cite\{[^}]*\}|\\textbf|\\textit|\\multirow\{[^}]*\}\{[^}]*\}|\\makecell\[?l?\]?|[{}$~\\]", "", c)
                 .strip() for c in line.rstrip("\\ \n").split("&")]
        rows.append(cells)
    return rows


def method_of(cells):
    for c in cells[:2]:
        for k, v in NAMES.items():
            if c.startswith(k) or c.startswith(k.replace("-", "")):
                return v
    return None


def nums(cell):
    return [float(x.replace(",", "")) for x in NUM.findall(cell)]


def close(printed, value, cell):
    dec = len(re.match(r"\d*", cell.split(".")[1]).group()) if "." in cell else 0
    return abs(round(value, dec) - printed) <= 10 ** -dec * 0.51 + 1e-12


report = []


def check(table, row, col, cell, value):
    if value is None or value != value:
        report.append((table, row, col, cell, "không tính lại được", ""))
        return
    p = nums(cell)
    if not p:
        return
    ok = close(p[0], value, cell)
    report.append((table, row, col, cell, "%.4f" % value, "khớp" if ok else "LỆCH"))


def main():
    df = pd.read_csv(S.RESULTS / "scores_all.csv")
    df = df[df.status == "ok"]
    w = pd.read_csv(OUT / "wilcoxon_holm.csv")
    # bảng chính
    corpus = None
    for cells in table_rows("main_results"):
        if "Benchmark 1" in cells[0]:
            corpus = "test1"
        elif "Benchmark 2" in cells[0]:
            corpus = "test2"
        m = method_of(cells)
        if not m or not corpus:
            continue
        d = df[(df.dataset == corpus) & (df.method == m)]
        vals = cells[-7:]
        check("main", "%s/%s" % (corpus, m), "completed", vals[0], float(len(d)))
        for col, cell in zip(["onmi_mgh", "onmi_lfk", "onf1", "f1", "omega"], vals[1:6]):
            check("main", "%s/%s" % (corpus, m), col, cell, d[col].mean())
        if m != "proposed":
            r = w[(w.dataset == corpus) & (w.metric == "onmi_mgh") & (w.vs == m)].iloc[0]
            p = vals[6]
            check("main", "%s/%s" % (corpus, m), "wilcoxon_raw", p.split("/")[0], r.p)
            check("main", "%s/%s" % (corpus, m), "wilcoxon_holm", p.split("/")[1].split("(")[0], r.p_holm)
            check("main", "%s/%s" % (corpus, m), "won", p.split("won")[1], float(r.win))
    # mạng protein
    for cells in table_rows("ppi_results"):
        m = method_of(cells)
        if not m:
            continue
        d = df[(df.dataset == "test3") & (df.method == m)]
        for col, cell in zip(["onmi_mgh", "labeled_onmi_mgh", "labeled_f1", "labeled_omega"], cells[1:5]):
            check("ppi", m, col, cell, d[col].mean())
        check("ppi", m, "labeled_coverage", cells[5], 100 * d.labeled_coverage.mean())
    # thời gian
    def wall(ds, m, net=None):
        v = [json.loads(p.read_text()) for p in (S.RESULTS / "timing" / ds / m).glob("*.json")]
        v = [x["wall_seconds"] for x in v if x.get("status") == "ok" and (net is None or x["net_id"] == net)]
        return statistics.median(v) if v else None
    for cells in table_rows("timing_results"):
        key = {"Benchmark 1": ("test1", None), "Benchmark 2": ("test2", None), "Collins": ("test3", "collins2007"),
               "Gavin": ("test3", "gavin2006"), "Krogan Core": ("test3", "krogan2006_core"),
               "Krogan Ext": ("test3", "krogan2006_extended")}
        k = next((v for n, v in key.items() if cells[0].startswith(n)), None)
        if not k:
            continue
        a, b, o = wall(*k[:1], "proposed", k[1]), wall(k[0], "wghac", k[1]), wall(k[0], "oslom", k[1])
        check("timing", cells[0], "proposed", cells[1], a)
        check("timing", cells[0], "wghac", cells[2], b)
        check("timing", cells[0], "speedup", cells[3], b / a if a and b else None)
        check("timing", cells[0], "oslom", cells[4], o)
    # bóc tách
    ab = []
    for p in (S.RESULTS / "ablation").glob("*/*/*.json"):
        r = json.loads(p.read_text())
        for v, x in (r.get("variants") or {}).items():
            ab.append({"group": r["group"], "dataset": r["dataset"], "net_id": r["net_id"], "variant": v, **x["scores"]})
    ab = pd.DataFrame(ab)
    rowmap = {"Full DOT-CCM": ("base", "full"), "wo Phase II": ("base", "no_phase2"), "wo Log": ("no_log", "no_log"),
              "wo Optimal": ("no_ot", "no_ot"), "Tree Obj.": ("base", "density")}
    for cells in table_rows("ablation"):
        k = next((v for n, v in rowmap.items() if cells[0].replace("/", "").startswith(n)), None)
        if not k:
            continue
        for ds, cell, col in (("test1", cells[1], "onmi_mgh"), ("test2", cells[2], "onmi_mgh"),
                              ("test3", cells[3], "labeled_onmi_mgh")):
            x = ab[(ab.group == k[0]) & (ab.dataset == ds) & (ab.variant == k[1])]
            if "---" not in cell:
                check("ablation", cells[0], ds, cell, x[col].mean() if len(x) else None)
    # N = 5000
    sc = pd.read_csv(S.RESULTS / "timing_n5000" / "scores.csv")
    me = ab[(ab.group == "min_edges") & (ab.dataset == "test2_n5000")]
    for cells in table_rows("scale_5000"):
        m = method_of(cells)
        if cells[0].startswith("Phase I"):
            x, ov = me[me.variant == "no_phase2"], None
        elif "2 Core" in cells[0]:
            x = me[me.variant == "min_edges"]
        elif m and m != "wghac":
            x = sc[sc.method == m]
        else:
            continue
        if "on" not in x:
            x = x.assign(on=[0 if "_on0_" in n else 1 for n in x.net_id])
        dis, ovl = x[x["on"] == 0].onmi_mgh.mean(), x[x["on"] > 0].onmi_mgh.mean()
        check("n5000", cells[0], "disjoint", cells[1], dis)
        check("n5000", cells[0], "overlapping", cells[2], ovl)
        check("n5000", cells[0], "macro", cells[3], x.onmi_mgh.mean())
    rep = pd.DataFrame(report, columns=["table", "row", "column", "printed", "recomputed", "verdict"])
    rep.to_csv(OUT / "tables_check.csv", index=False)
    print(rep.verdict.value_counts().to_dict())
    print(rep[rep.verdict != "khớp"].to_string())


if __name__ == "__main__":
    main()
