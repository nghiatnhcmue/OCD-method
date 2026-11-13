from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S


def merge_share():
    print("Tỉ lệ thời gian bước gộp (C_merge / total) của DOT-CCM trong lượt đo thời gian")
    for ds in ("test1", "test2", "test3"):
        v = []
        for p in sorted((S.RESULTS / "timing" / ds / "proposed").glob("*.json")):
            r = json.loads(p.read_text())
            st = (r.get("info") or {}).get("step_seconds") or {}
            if r.get("status") == "ok" and st.get("total"):
                v.append(st["C_merge"] / st["total"])
        print("  %s: %d mạng, trung vị %.3f, nhỏ nhất %.3f, lớn nhất %.3f" % (
            ds, len(v), statistics.median(v), min(v), max(v)))


def wghac_largest():
    print("Cỡ cụm lớn nhất của wGHAC")
    root = S.RESULTS / "scores"
    for muw in ("0.1", "0.3", "0.5"):
        v = [json.loads(p.read_text())["cover_stats"]["max_size"]
             for p in sorted((root / "test2" / "wghac").glob("lfrw_n1000_mut0.5_muw%s_*.json" % muw))]
        print("  KT2 mu_t = 0.5, mu_w = %s: %d mạng, trung vị %.0f, trung bình %.1f" % (
            muw, len(v), statistics.median(v), statistics.mean(v)))
    for p in sorted((root / "test3" / "wghac").glob("*.json")):
        r = json.loads(p.read_text())
        c = r["cover_stats"]
        print("  %s: %d cụm, lớn nhất %d / %d đỉnh" % (r["net_id"], c["n_communities"], c["max_size"], r["n_nodes"]))


def phase2_singles():
    d = S.RESULTS / "audit" / "phase2_diag"
    print("Kết nạp của Pha II theo số cạnh nối vào lõi (từ %s)" % d.relative_to(S.ROOT))
    single_total = single_correct = 0
    for p in sorted(d.glob("*.json")):
        r = json.loads(p.read_text())
        a = r["adds"]
        one = [x for x in a if x["k"] == 1]
        many = [x for x in a if x["k"] >= 2]
        single_total += len(one)
        single_correct += sum(x["correct"] for x in one)
        print("  %s: %d kết nạp, một cạnh %.1f%%, đúng khi >= 2 cạnh %s" % (
            r["net_id"], len(a), 100 * len(one) / len(a) if a else float("nan"),
            "%.1f%%" % (100 * sum(x["correct"] for x in many) / len(many)) if many else "-"))
    print("  tổng kết nạp một cạnh: %d, trong đó đúng: %d" % (single_total, single_correct))


if __name__ == "__main__":
    merge_share()
    wghac_largest()
    phase2_singles()
