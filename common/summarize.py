from __future__ import annotations

import csv
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from common import datasets

SCORE_COLS = ["onmi_mgh", "onmi_lfk", "onf1", "f1", "omega", "P_O", "R_O", "P_mem", "R_mem", "labeled_onmi_mgh",
              "labeled_onmi_lfk", "labeled_onf1", "labeled_f1", "labeled_omega", "labeled_coverage"]
COVER_COLS = ["n_communities", "max_size", "coverage", "mean_memberships"]
COLS = (["dataset", "net_id", "topology_id", "regime", "mu", "mu_w", "on", "om", "replicate", "method", "method_name",
         "status", "seconds"] + COVER_COLS + SCORE_COLS + ["source"])


def label(dataset):
    return S.DATASETS[dataset].split(":")[0]


def mean(values):
    v = [float(x) for x in values if x not in (None, "") and not math.isnan(float(x))]
    return sum(v) / len(v) if v else float("nan")


def fmt(x):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else "%.3f" % x


def load_rows():
    rows = []
    for p in sorted(S.SCORES.glob("*/*/*.json")):
        # bảng chính chỉ gồm 9 phương pháp trên 3 bộ kiểm tra; biến thể và bộ phụ báo riêng
        if p.parent.name not in S.METHODS or p.parent.parent.name not in S.DATASETS:
            continue
        d = json.loads(p.read_text())
        r = {k: d.get(k, "") for k in COLS}
        r.update({k: d.get("cover_stats", {}).get(k, "") for k in COVER_COLS})
        r.update({k: d.get("scores", {}).get(k, "") for k in SCORE_COLS})
        rows.append(r)
    return rows


def completion_table(by, total):
    L = ["## Mức độ hoàn thành", "", "Mỗi ô: ok / quá giờ / lỗi / chưa chạy.", "",
         "| Phương pháp | " + " | ".join(label(ds) for ds in S.DATASETS) + " |", "|---|" + ":---:|" * len(S.DATASETS)]
    for m in S.METHODS:
        cells = []
        for ds in S.DATASETS:
            st = [r["status"] for r in by[(ds, m)]]
            cells.append("%d / %d / %d / %d" % (st.count("ok"), st.count("timeout"), st.count("error"), total[ds] - len(st)))
        L.append("| %s | %s |" % (S.METHODS[m], " | ".join(cells)))
    return L


def dataset_table(ds, by):
    ok = {m: {r["net_id"]: r for r in by[(ds, m)] if r["status"] == "ok"} for m in S.METHODS}
    common = set.intersection(*[set(v) for v in ok.values()]) if all(ok.values()) else set()
    L = ["", "## " + S.DATASETS[ds], "",
         "| Phương pháp | Số mạng ok | ONMI | ONMI-LFK | ONF1 | F1 | Omega | ONMI trên %d mạng mọi phương pháp đều ok |" % len(common),
         "|---|" + ":---:|" * 7]

    def key(m, col="onmi_mgh"):
        v = mean([r[col] for r in ok[m].values()])
        return -v if not math.isnan(v) else 1.0
    for m in sorted(S.METHODS, key=key):
        v = list(ok[m].values())
        L.append("| %s | %d | %s |" % (S.METHODS[m], len(v), " | ".join(
            [fmt(mean([r[c] for r in v])) for c in ("onmi_mgh", "onmi_lfk", "onf1", "f1", "omega")]
            + [fmt(mean([ok[m][n]["onmi_mgh"] for n in common]))])))
    if ds == "test3":
        L += ["", "Trên các đỉnh có nhãn CYC2008:", "",
              "| Phương pháp | Số mạng ok | ONMI | F1 | Omega | Độ phủ đỉnh có nhãn |", "|---|" + ":---:|" * 5]
        for m in sorted(S.METHODS, key=lambda m: key(m, "labeled_onmi_mgh")):
            v = list(ok[m].values())
            L.append("| %s | %d | %s |" % (S.METHODS[m], len(v), " | ".join(
                fmt(mean([r[c] for r in v])) for c in ("labeled_onmi_mgh", "labeled_f1", "labeled_omega", "labeled_coverage"))))
    return L


def main():
    rows = load_rows()
    S.RESULTS.mkdir(parents=True, exist_ok=True)
    with (S.RESULTS / "scores_all.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    total = {ds: len(datasets.list_networks(ds)) for ds in S.DATASETS}
    by = defaultdict(list)
    for r in rows:
        by[(r["dataset"], r["method"])].append(r)
    L = ["# Tổng hợp kết quả", "", "Cập nhật %s, %d tệp điểm." % (time.strftime("%Y-%m-%d %H:%M"), len(rows)), ""]
    L += completion_table(by, total)
    for ds in S.DATASETS:
        L += dataset_table(ds, by)
    (S.RESULTS / "SUMMARY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    from common import excel_report
    xlsx = excel_report.write_workbook(rows)
    print("Đã ghi %s, %s, %s (%d dòng)" % (S.RESULTS / "scores_all.csv", S.RESULTS / "SUMMARY.md", xlsx, len(rows)))


if __name__ == "__main__":
    main()
