from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from revision.phase2 import CONFIGS, OUT, TREES, first_batch

GROUPS = (("test1", "Kiểm tra 1"), ("test2", "Kiểm tra 2"), ("test3", "Mạng protein"), ("test2_n5000", "N = 5000"),
          ("applications", "Mạng ứng dụng"))
LABELS = {"v2": "v2 (kết quả cũ)", "on_none": "Pha I mới, bỏ Pha II", "old": "Pha I mới + Pha II cũ"}
LABELS.update({name: "%s, họ %s, q = %s" % ("Compound Poisson" if m == "cpoisson" else "Số cạnh", f, q)
               for name, m, f, q in CONFIGS if name != "old"})


def rows_for(dataset, net_id):
    rec = json.loads((OUT / dataset / ("%s.json" % net_id)).read_text())
    tree = json.loads((TREES / dataset / ("%s.json" % net_id)).read_text())
    off, on = tree["variants"]["off"], tree["variants"]["on"]
    base = {"dataset": dataset, "net_id": net_id, "overlap_truth": rec["overlap_truth"]}
    out = [dict(base, row="v2", added=off["added"], false_added=rec["v2_false_added"], **off.get("scores_final", {})),
           dict(base, row="on_none", added=0, false_added=0, **on.get("scores_pre", {}))]
    for name, v in rec["configs"].items():
        out.append(dict(base, row=name, added=v["added"], false_added=v.get("false_added"),
                        nodes_with_adds=v["nodes_with_adds"], phase2_seconds=v["phase2_seconds"],
                        **v.get("scores", {})))
    out[0]["phase2_seconds"] = rec["configs"]["old"]["phase2_seconds"]
    return out


def _mean(xs):
    xs = [x for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return statistics.mean(xs) if xs else None


def _f(x, nd=3):
    return "-" if x is None else "%.*f" % (nd, x)


def table(rows, title, L, metric="onmi_mgh"):
    order = ["v2", "on_none", "old"] + [n for n, *_ in CONFIGS if n != "old"]
    nets = sorted({(r["dataset"], r["net_id"]) for r in rows})
    by = {(r["dataset"], r["net_id"], r["row"]): r for r in rows}
    L += ["### %s (%d mạng)" % (title, len(nets)), "",
          "| Cấu hình | %s | ONF1 | R_O |" % ("ONMI" if metric == "onmi_mgh" else "ONMI có nhãn") +
          " Mức thuộc thêm (TB) | Sai (TB) | Tỉ lệ đúng | Sai trên mạng không chồng lấn (TB) "
          "| Thắng / thua ONMI so với v2 | Thời gian Pha II, trung vị (s) |",
          "|---|---:|---:|---:|---:|---:|---:|---:|:---:|---:|"]
    for name in order:
        rs = [by[(d, n, name)] for d, n in nets if (d, n, name) in by]
        if not rs:
            continue
        added = sum(r["added"] for r in rs)
        false = [r.get("false_added") for r in rs]
        prec = None if not added or any(x is None for x in false) else 1 - sum(false) / added
        flat = [r for r in rs if not r["overlap_truth"]]
        win = lose = 0
        for d, n in nets:
            a, b = by.get((d, n, name), {}).get(metric), by.get((d, n, "v2"), {}).get(metric)
            if a is not None and b is not None and name != "v2":
                win += a > b + 1e-12
                lose += a < b - 1e-12
        secs = [r.get("phase2_seconds") for r in rs if r.get("phase2_seconds") is not None]
        L.append("| %s | %s | %s | %s | %.1f | %s | %s | %s | %s | %s |" % (
            LABELS[name], _f(_mean([r.get(metric) for r in rs])), _f(_mean([r.get("onf1") for r in rs])),
            _f(_mean([r.get("R_O") for r in rs])), added / len(rs), _f(_mean(false), 1), _f(prec),
            _f(_mean([r["added"] for r in flat]), 1) if flat else "-", "" if name == "v2" else "%d / %d" % (win, lose),
            _f(statistics.median(secs), 1) if secs else "-"))
    L.append("")


def main():
    rows, missing = [], []
    for p in sorted(TREES.glob("*/*.json")):
        q = OUT / p.parent.name / p.name
        if q.exists():
            rows += rows_for(p.parent.name, p.stem)
        else:
            missing.append((p.parent.name, p.stem))
    cols = []
    for r in rows:
        cols += [k for k in r if k not in cols]
    with (OUT / "summary.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    first = set(first_batch())
    L = ["# Pha II: trước và sau", "",
         "Pha I mới (bao đơn điệu) cho mọi dòng trừ v2. Thời gian Pha II đo bằng CLOCK_MONOTONIC_RAW trong lô song song, "
         "không theo quy trình đo thời gian; chỉ dùng để so tương đối. Mạng chưa có kết quả: %d." % len(missing), ""]
    table([r for r in rows if (r["dataset"], r["net_id"]) in first], "35 mạng mà Pha II cũ làm giảm ONMI", L)
    for ds, name in GROUPS:
        rs = [r for r in rows if r["dataset"] == ds]
        if rs:
            table(rs, name, L, "labeled_onmi_mgh" if ds == "test3" else "onmi_mgh")
    (OUT / "SUMMARY.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
