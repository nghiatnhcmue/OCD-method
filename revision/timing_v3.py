from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from common.datasets import LARGE

# So thời gian v3 (results/round_c/timing*, đo lại theo timing/run_timing.py) với v2 đã lưu (results/timing*)
OLD, NEW = S.RESULTS, S.RESULTS / "round_c"
ROWS = [("Kiểm tra 1 (18 mạng)", "test1", None), ("Kiểm tra 2 (10 mạng)", "test2", None),
        ("Collins 2007", "test3", "collins2007"), ("Gavin 2006", "test3", "gavin2006"),
        ("Krogan Core", "test3", "krogan2006_core"), ("Krogan Ext", "test3", "krogan2006_extended")]


def runs(root, ds, m):
    base = root / "timing_n5000" / m if ds == LARGE else root / "timing" / ds / m
    out = {}
    for p in base.glob("*.json"):
        x = json.loads(p.read_text())
        if x.get("status") == "ok":
            out[x["net_id"]] = x
    return out


def med(v):
    return statistics.median(v) if v else None


def f(x, nd=0):
    return "-" if x is None else "{:,.{}f}".format(x, nd)


def step(x, k):
    return (x.get("info") or {}).get("step_seconds", {}).get(k)


def main():
    L = ["# Thời gian DOT-CCM v3 theo quy trình đo", "",
         "Cập nhật %s. v3: `results/round_c/timing*` (đo lại, `RUN_TAG=round_c python3 timing/run_timing.py --set all "
         "--methods proposed`). v2 và wGHAC: số đã lưu trong `results/timing*`. Cùng quy trình: cặp nhân gắn bằng "
         "`taskset`, 5 tiến trình, `CLOCK_MONOTONIC_RAW`, mỗi lượt đo một lần." % time.strftime("%Y-%m-%d %H:%M"), "",
         "| Bộ | v2 (s) | v3 (s) | v3 / v2 | wGHAC (s) | wGHAC / v3 | Pha II v2 (s) | Pha II v3 (s) | Số mạng v3 |",
         "|---|---:|---:|---:|---:|---:|---:|---:|:---:|"]
    for label, ds, net in ROWS:
        a, b, w = runs(OLD, ds, "proposed"), runs(NEW, ds, "proposed"), runs(OLD, ds, "wghac")
        if net:
            a, b, w = ({k: v for k, v in d.items() if k == net} for d in (a, b, w))
        both = sorted(set(a) & set(b))
        ta, tb = med([a[k]["wall_seconds"] for k in both]), med([b[k]["wall_seconds"] for k in both])
        tw = med([w[k]["wall_seconds"] for k in w])
        pa, pb = med([step(a[k], "F_phase2") for k in both if step(a[k], "F_phase2") is not None]), \
            med([step(b[k], "F_phase2") for k in both if step(b[k], "F_phase2") is not None])
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %d |" % (
            label, f(ta), f(tb), f(tb / ta, 2) if ta and tb else "-", f(tw), f(tw / tb, 2) if tw and tb else "-",
            f(pa, 1), f(pb, 1), len(b)))
    L += ["", "Trung vị trên các mạng của bộ (chỉ mạng có cả hai lượt v2 và v3). Pha II: `info.step_seconds.F_phase2`.", ""]
    a, b = runs(OLD, LARGE, "proposed"), runs(NEW, LARGE, "proposed")
    L += ["## N = 5000", "", "| Mạng | v2 (s) | v3 (s) | v3 / v2 | Pha II v2 (s) | Pha II v3 (s) | RSS v3 (GB) |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k), b.get(k)
        L.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            k.replace("lfrw_n5000_mut0.3_muw0.3_", ""), f(x and x["wall_seconds"]), f(y and y["wall_seconds"]),
            f(y["wall_seconds"] / x["wall_seconds"], 2) if x and y else "-", f(x and step(x, "F_phase2"), 1),
            f(y and step(y, "F_phase2"), 1), f(y["max_rss_mb"] / 1024, 2) if y and y.get("max_rss_mb") else "-"))
    for name, sel in (("không chồng lấn", "_on0_"), ("có chồng lấn", "_on500_")):
        ks = [k for k in set(a) & set(b) if sel in k]
        L.append("| Trung vị, %s | %s | %s | | | | |" % (
            name, f(med([a[k]["wall_seconds"] for k in ks])), f(med([b[k]["wall_seconds"] for k in ks]))))
    allk = []
    for ds in ("test1", "test2", "test3", LARGE):
        a, b = runs(OLD, ds, "proposed"), runs(NEW, ds, "proposed")
        allk += [b[k]["wall_seconds"] / a[k]["wall_seconds"] for k in set(a) & set(b)]
    if allk:
        L += ["", "Tỉ số v3 / v2 theo từng mạng trên %d mạng: trung vị %.3f, nhỏ nhất %.3f, lớn nhất %.3f. Pha I của "
              "hai bản giống nhau, nên phần chênh ngoài Pha II là dao động giữa hai lần đo." % (
                  len(allk), med(allk), min(allk), max(allk)), ""]
    out = NEW / "timing_v3.md"
    out.write_text("\n".join(L))
    print("Đã ghi %s" % out)


if __name__ == "__main__":
    main()
