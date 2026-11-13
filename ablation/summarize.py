from __future__ import annotations

import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd
from scipy.stats import wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from ablation.run import OUT
from common import datasets

METRICS = [("onmi_mgh", "ONMI"), ("onmi_lfk", "ONMI-LFK"), ("onf1", "ONF1"), ("f1", "F1"), ("omega", "Omega")]
LABELED = [("onmi_mgh", "ONMI toàn mạng"), ("labeled_onmi_mgh", "ONMI có nhãn"), ("labeled_f1", "F1 có nhãn"),
           ("labeled_omega", "Omega có nhãn"), ("labeled_coverage", "Độ phủ có nhãn"), ("coverage", "Độ phủ toàn mạng")]
VARIANTS = {"full": "Đầy đủ", "no_phase2": "Bỏ Pha II", "density": "Chọn tập theo mật độ thay cho Ψ",
            "no_log": "Bỏ nén log", "no_ot": "Bỏ vận tải tối ưu", "prune": "Kiểm định hai chiều, cho phép bỏ đỉnh",
            "min_edges": "Pha II cần ít nhất 2 cạnh tới lõi"}
NAME = {"test1": "Kiểm tra 1", "test2": "Kiểm tra 2", "test3": "Kiểm tra 3", datasets.LARGE: "N = 5000"}


def _f(x, nd=3):
    return "-" if x is None or x != x else "%.*f" % (nd, x)


def _p(x):
    return "-" if x is None or x != x else "%.2g" % x


def load():
    meta = {(d["dataset"], d["net_id"]): d for ds in NAME for d in datasets.list_networks(ds)}
    rows, status, match = [], Counter(), Counter()
    for p in sorted(OUT.glob("*/*/*.json")):
        r = json.loads(p.read_text())
        status[(r["group"], r["status"])] += 1
        if r["status"] != "ok":
            continue
        if "matches_main" in r:
            match[r["matches_main"]] += 1
        m = meta[(r["dataset"], r["net_id"])]
        for name, v in r["variants"].items():
            row = {"dataset": r["dataset"], "net_id": r["net_id"], "topology_id": m.get("topology_id", r["net_id"]),
                   "mu": m.get("mu"), "mu_w": m.get("mu_w"), "overlap": float(m.get("on") or 0) > 0, "variant": name}
            row.update(v["scores"])
            row.update(v["cover_stats"])
            rows.append(row)
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.drop_duplicates(["dataset", "net_id", "variant"])
    return df, status, match


# kiểm định theo cặp; Kiểm tra 1 lấy trung bình theo tô-pô (3 chế độ trọng số của cùng tô-pô không độc lập)
def paired(df, ds, col_a, col_b, metric="onmi_mgh", by="variant"):
    d = df[df.dataset == ds]
    key = "topology_id" if ds == "test1" else "net_id"
    x = d.pivot_table(index=key, columns=by, values=metric, aggfunc="mean")
    if col_a not in x or col_b not in x:
        return None
    x = x[[col_a, col_b]].dropna()
    diff = x[col_a] - x[col_b]
    p = float(wilcoxon(x[col_a], x[col_b]).pvalue) if (diff != 0).any() else 1.0
    return {"n": len(x), "win": int((diff > 0).sum()), "lose": int((diff < 0).sum()), "diff": float(diff.mean()), "p": p}


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out, best = [1.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        best = max(best, min(1.0, (len(ps) - rank) * ps[i]))
        out[i] = best
    return out


def ablation_tables(df, L):
    for ds in ("test1", "test2"):
        d = df[(df.dataset == ds) & df.variant.isin(VARIANTS)]
        if d.empty:
            continue
        L += ["## Bỏ từng thành phần: %s" % NAME[ds], "",
              "| Biến thể | Số mạng | " + " | ".join(n for _, n in METRICS) + " | Chênh ONMI so với đầy đủ | Thắng / thua | p |",
              "|---|:---:|" + "---:|" * len(METRICS) + "---:|:---:|---:|"]
        for v, label in VARIANTS.items():
            x = d[d.variant == v]
            if x.empty:
                continue
            t = paired(df, ds, v, "full") if v != "full" else None
            L.append("| %s | %d | %s | %s | %s | %s |" % (
                label, len(x), " | ".join(_f(x[c].mean()) for c, _ in METRICS),
                _f(t["diff"]) if t else "", "%d / %d" % (t["win"], t["lose"]) if t else "", _p(t["p"]) if t else ""))
        L += ["", "Kiểm định Wilcoxon theo cặp trên ONMI, %s." % (
            "36 tô-pô (trung bình 3 chế độ trọng số)" if ds == "test1" else "50 mạng"), ""]
    d = df[(df.dataset == "test3") & df.variant.isin(VARIANTS)]
    if not d.empty:
        L += ["## Mạng protein (Kiểm tra 3): biến thể cho phép bỏ đỉnh", "",
              "| Biến thể | " + " | ".join(n for _, n in LABELED) + " | Số cộng đồng | Cỡ lớn nhất | Số mức thuộc TB |",
              "|---|" + "---:|" * (len(LABELED) + 3)]
        for v, label in VARIANTS.items():
            x = d[d.variant == v]
            if not x.empty:
                L.append("| %s | %s | %.1f | %.1f | %.2f |" % (label, " | ".join(_f(x[c].mean()) for c, _ in LABELED),
                                                              x.n_communities.mean(), x.max_size.mean(),
                                                              x.mean_memberships.mean()))
        L += ["", "Trung bình trên 4 mạng; không kiểm định vì số mạng quá ít.", ""]


def breakdown_tables(df, L):
    for ds in ("test1", "test2"):
        d = df[(df.dataset == ds) & df.variant.isin(VARIANTS)]
        if d.empty:
            continue
        x = d.pivot_table(index="net_id", columns="variant", values="onmi_mgh")
        info = d.drop_duplicates("net_id").set_index("net_id")
        cols = [("μ = %s" % v, info.index[info.mu == v]) for v in sorted(info.mu.dropna().unique())]
        if ds == "test2":
            cols += [("μ_w = %s" % v, info.index[info.mu_w == v]) for v in sorted(info.mu_w.dropna().unique())]
        cols += [("không chồng lấn", info.index[~info.overlap]), ("có chồng lấn", info.index[info.overlap])]
        L += ["## Chênh ONMI so với bản đầy đủ theo loại mạng: %s" % NAME[ds], "",
              "| Biến thể | " + " | ".join("%s (%d)" % (n, len(ix)) for n, ix in cols) + " |",
              "|---|" + "---:|" * len(cols),
              "| Đầy đủ (ONMI) | " + " | ".join(_f(x.loc[ix, "full"].mean()) for _, ix in cols) + " |"]
        for v, label in VARIANTS.items():
            if v != "full" and v in x:
                L.append("| %s | %s |" % (label, " | ".join(_f((x.loc[ix, v] - x.loc[ix, "full"]).mean())
                                                           for _, ix in cols)))
        L += ["", "Dòng đầu là ONMI của bản đầy đủ; các dòng sau là chênh trung bình so với dòng đầu. "
              "Số trong ngoặc: số mạng của nhóm.", ""]


def slpa_table(df, main, L):
    w = df[df.variant == "slpa_weighted"]
    if w.empty:
        return
    cols = ["dataset", "net_id", "topology_id"] + [c for c, _ in METRICS]
    cols += [c for c, _ in LABELED if c in main.columns and c not in cols]
    s = main[main.method == "slpa"][cols].assign(variant="slpa")
    both = pd.concat([w, s], ignore_index=True)
    L += ["## SLPA có trọng số (phụ lục)", "",
          "Luật nghe cộng trọng số cạnh thay vì cộng 1; mọi phần khác như SLPA của cdlib (t = 21, r = 0.1, hạt giống 42).", "",
          "| Bộ | Biến thể | " + " | ".join(n for _, n in METRICS) + " | Chênh ONMI | Thắng / thua | p |",
          "|---|---|" + "---:|" * len(METRICS) + "---:|:---:|---:|"]
    for ds in ("test1", "test2", "test3"):
        t = paired(both, ds, "slpa_weighted", "slpa") if ds != "test3" else None
        for v, label in (("slpa", "SLPA"), ("slpa_weighted", "SLPA có trọng số")):
            x = both[(both.dataset == ds) & (both.variant == v)]
            last = v == "slpa_weighted" and t
            L.append("| %s | %s | %s | %s | %s | %s |" % (
                NAME[ds], label, " | ".join(_f(x[c].mean()) for c, _ in METRICS), _f(t["diff"]) if last else "",
                "%d / %d" % (t["win"], t["lose"]) if last else "", _p(t["p"]) if last else ""))
    L += [""]


def main_tests(main, L):
    L += ["## Kiểm định Wilcoxon cho bảng chính (ONMI)", "",
          "Phương pháp đề xuất so với từng phương pháp đối chứng; p hai phía, hiệu chỉnh Holm trên 8 so sánh của mỗi bộ.",
          "", "| Bộ | So với | Số cặp | Thắng / thua | Chênh TB | p | p (Holm) |", "|---|---|:---:|:---:|---:|---:|---:|"]
    for ds in ("test1", "test2"):
        tests = [(m, paired(main, ds, "proposed", m, by="method")) for m in S.METHODS if m != "proposed"]
        adj = holm([t["p"] for _, t in tests])
        for (m, t), pa in zip(tests, adj):
            L.append("| %s | %s | %d | %d / %d | %s | %s | %s |" % (NAME[ds], S.METHODS[m], t["n"], t["win"], t["lose"],
                                                                 _f(t["diff"]), _p(t["p"]), _p(pa)))
    L += [""]


def timing_large(L):
    root = S.RESULTS / "timing_n5000"
    rows = [json.loads(p.read_text()) for p in sorted(root.glob("*/*.json"))]
    if not rows:
        return
    L += ["## Thời gian trên bộ N = 5000", "",
          "6 mạng LFR có trọng số (μ_t = μ_w = 0.3; 3 mạng không chồng lấn, 3 mạng có 500 đỉnh chồng lấn, o_m = 2), "
          "cùng quy trình đo với 32 mạng đại diện. Lượt quá giờ được tính là lâu hơn giới hạn khi lấy trung vị. "
          "Cột N = 1000: mạng cùng tham số, không chồng lấn, trong 32 mạng đại diện.", "",
          "| Phương pháp | ok / quá giờ / lỗi | Không chồng lấn: trung vị (s) | Có chồng lấn: trung vị (s) | Lớn nhất (s) "
          "| N = 1000 (s) | Gấp (lần) | Bộ nhớ lớn nhất (GB) |", "|---|:---:|---:|---:|---:|---:|---:|---:|"]

    def secs(r):
        return [x["wall_seconds"] if x["status"] == "ok" else float("inf") for x in r if x["status"] in ("ok", "timeout")]

    def fmt(v, limit):
        return "-" if v is None else "> %d" % limit if v == float("inf") else "%.0f" % v

    for m, name in S.METHODS.items():
        r = [x for x in rows if x["method"] == m]
        if not r:
            continue
        st = Counter(x["status"] for x in r)
        limit = max(x.get("time_limit", S.TIME_LIMIT) for x in r)
        flat = secs([x for x in r if "_on0_" in x["net_id"]])
        over = secs([x for x in r if "_on0_" not in x["net_id"]])
        med_flat = statistics.median(flat) if flat else None
        med_over = statistics.median(over) if over else None
        small = S.RESULTS / "timing" / "test2" / m / "lfrw_n1000_mut0.3_muw0.3_on0_omx_seed1.json"
        n1000 = json.loads(small.read_text()).get("wall_seconds") if small.exists() else None
        ratio = "-" if not n1000 or med_flat is None else "> %.0f" % (limit / n1000) if med_flat == float("inf") \
            else "%.1f" % (med_flat / n1000)
        rss = [x["max_rss_mb"] for x in r if x["status"] == "ok" and x.get("max_rss_mb")]
        L.append("| %s | %d / %d / %d | %s | %s | %s | %s | %s | %s |" % (
            name, st["ok"], st["timeout"], st["error"], fmt(med_flat, limit), fmt(med_over, limit),
            fmt(max(flat + over) if flat + over else None, limit), fmt(n1000, limit), ratio,
            "%.1f" % (max(rss) / 1024) if rss else "-"))
    L += ["", "Gấp: trung vị nhóm không chồng lấn chia cho thời gian ở N = 1000. Bộ nhớ: RSS lớn nhất của lượt chạy, "
          "chỉ có ở các lượt đo sau khi bổ sung trường này.", ""]
    wghac_note(L)


def accuracy_large(df, L):
    path = S.RESULTS / "timing_n5000" / "scores.csv"
    if not path.exists():
        return
    sc = pd.read_csv(path)
    sc["overlap"] = sc["on"] > 0
    rows = [(S.METHODS[m], sc[sc.method == m]) for m in S.METHODS if m in set(sc.method)]
    if not df.empty:
        d = df[df.dataset == datasets.LARGE]
        labels = {"no_phase2": "Đề xuất, bỏ Pha II", "min_edges": "Đề xuất, Pha II cần ít nhất 2 cạnh tới lõi"}
        rows += [(lab, d[d.variant == v]) for v, lab in labels.items() if not d[d.variant == v].empty]
    L += ["## Độ chính xác trên bộ N = 5000", "",
          "| Phương pháp | Số mạng | ONMI không chồng lấn | ONMI có chồng lấn | " + " | ".join(n for _, n in METRICS) +
          " | Số mức thuộc TB |", "|---|:---:|---:|---:|" + "---:|" * len(METRICS) + "---:|"]
    for label, x in rows:
        L.append("| %s | %d | %s | %s | %s | %.2f |" % (
            label, len(x), _f(x[~x.overlap].onmi_mgh.mean()), _f(x[x.overlap].onmi_mgh.mean()),
            " | ".join(_f(x[c].mean()) for c, _ in METRICS), x.mean_memberships.mean()))
    L += ["", "Trung bình trên 6 mạng (3 không chồng lấn, 3 có chồng lấn). Hai dòng cuối: cùng lần chạy của phương pháp "
          "đề xuất, bỏ Pha II hoặc chỉ nhận mức thuộc có ít nhất 2 cạnh tới lõi.", ""]


# wGHAC dựng ma trận khoảng cách dày giữa mọi cặp clique cực đại; ước lượng bộ nhớ và thời gian ở N = 5000
def wghac_note(L):
    import networkx as nx
    ref = S.RESULTS / "timing" / "test2" / "wghac" / "lfrw_n1000_mut0.3_muw0.3_on0_omx_seed1.json"
    if not ref.exists() or any((S.RESULTS / "timing_n5000" / "wghac").glob("*.json")):
        return
    r = json.loads(ref.read_text())
    b0, t0 = r["info"]["n_cliques"], r["wall_seconds"]
    bs = [sum(1 for _ in nx.find_cliques(datasets.load_network(item)[0])) for item in datasets.list_networks(datasets.LARGE)]
    est = [t0 * (b / b0) ** 2 / 3600 for b in bs]
    L += ["wGHAC không đo ở N = 5000. Mỗi mạng có %d–%d clique cực đại; wGHAC dựng ma trận khoảng cách dày giữa mọi cặp "
          "clique (%.1f–%.1f GB mỗi lượt) và tính từng cặp. Ngoại suy theo số cặp clique từ mạng N = 1000 cùng tham số "
          "(%d clique, %.0f s) cho khoảng %.0f–%.0f giờ mỗi mạng, vượt giới hạn %.0f giờ. Lần chạy đầu, 3 lượt wGHAC "
          "chạy cùng lúc làm máy hết bộ nhớ sau 3,3 giờ." % (
              min(bs), max(bs), min(bs) ** 2 * 8 / 1e9, max(bs) ** 2 * 8 / 1e9, b0, t0, min(est), max(est),
              S.TIME_LIMIT / 3600), ""]


def main():
    df, status, match = load()
    main_scores = pd.read_csv(S.RESULTS / "scores_all.csv")
    main_scores = main_scores[main_scores.status == "ok"]
    L = ["# Thực nghiệm bổ sung", "", "Cập nhật %s." % time.strftime("%Y-%m-%d %H:%M"), "",
         "Trạng thái các lượt: " + ", ".join("%s %s: %d" % (g, s, n) for (g, s), n in sorted(status.items())) + ".",
         "Bản đầy đủ chạy lại trùng khít kết quả chính: %d / %d mạng." % (match[True], match[True] + match[False]), ""]
    if not df.empty:
        ablation_tables(df, L)
        breakdown_tables(df, L)
        slpa_table(df, main_scores, L)
    main_tests(main_scores, L)
    timing_large(L)
    accuracy_large(df, L)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SUMMARY.md").write_text("\n".join(L))
    print("Đã ghi %s" % (OUT / "SUMMARY.md"))


if __name__ == "__main__":
    main()
