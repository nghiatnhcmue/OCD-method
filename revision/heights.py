from __future__ import annotations

import csv
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S

TREES = S.RESULTS / "revision" / "trees"
OUT = S.RESULTS / "revision" / "heights"
TOL = 1e-12


def envelope(n, merges):
    H = [0.0] * n
    for a, b, h in merges:
        H.append(max(h, H[a], H[b]))
    return H


def inversion_stats(rec):
    n, merges = len(rec["leaves"]), rec["merges"]
    m = len(merges)
    birth = [0.0] * n + [h for _, _, h in merges]
    death = [None] * (n + m)
    for a, b, h in merges:
        death[a] = death[b] = h
    inverted = [i for i in range(n, n + m) if death[i] is not None and death[i] < birth[i] - TOL]
    H = envelope(n, merges)
    inv_merges = [k for k, (a, b, h) in enumerate(merges) if h < max(H[a], H[b]) - TOL]
    double = [k for k, (a, b, h) in enumerate(merges) if h < min(H[a], H[b]) - TOL]
    mags = [(birth[i] - death[i]) / birth[i] for i in inverted if birth[i] > 0]
    return {"n_internal": m, "n_roots": sum(1 for i in range(n, n + m) if death[i] is None),
            "n_inverted": len(inverted), "share_inverted": len(inverted) / m if m else 0.0,
            "n_inverted_merges": len(inv_merges), "n_double": len(double),
            "magnitude_median": statistics.median(mags) if mags else 0.0, "magnitude_max": max(mags, default=0.0),
            "n_decreasing_steps": sum(1 for k in range(m - 1) if merges[k + 1][2] < merges[k][2] - TOL),
            "inverted_sizes_median": statistics.median(len_members(n, merges, i) for i in inverted) if inverted else 0}


def len_members(n, merges, i):
    stack, size = [i], 0
    while stack:
        j = stack.pop()
        if j < n:
            size += 1
        else:
            a, b, _ = merges[j - n]
            stack += [a, b]
    return size


def compare_row(rec):
    off, on = rec["variants"]["off"], rec["variants"]["on"]
    row = {"n_rho_changed": rec["n_rho_changed"], "n_psi_changed": rec["n_psi_changed"],
           "selected_same": rec["selected_same"], "n_selected_off": len(off["selected"]),
           "n_selected_on": len(on["selected"]), "n_comm_off": len(off["final"]), "n_comm_on": len(on["final"]),
           "onmi_on_off_pre": rec["onmi_on_off_pre_cover"], "onmi_on_off_final": rec["onmi_on_off_final"],
           "added_off": off["added"], "added_on": on["added"], "matches_main": rec["matches_main"]}
    keys = ["onmi_mgh", "onf1"] + (["labeled_onmi_mgh"] if rec["dataset"] == "test3" else [])
    for k in keys:
        if "scores_final" in off:
            a, b = off["scores_final"].get(k), on["scores_final"].get(k)
            row[k + "_off"], row[k + "_on"] = a, b
            row["d_" + k] = b - a if a is not None and b is not None else None
            row["pre_" + k + "_off"] = off["scores_pre"].get(k)
            row["pre_" + k + "_on"] = on["scores_pre"].get(k)
    return row


def write_csv(path, rows):
    cols = []
    for r in rows:
        cols += [k for k in r if k not in cols]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


NAMES = (("test1", "Kiểm tra 1"), ("test2", "Kiểm tra 2"), ("test3", "Mạng protein"), ("test2_n5000", "N = 5000"),
         ("applications", "Mạng ứng dụng"))


def _num(x):
    return None if x is None or x == "" or (isinstance(x, float) and x != x) else float(x)


def summary(inv, cmp_rows):
    L = ["# Bao đơn điệu: thống kê đảo độ cao và tác động", "",
         "Nút đảo (định nghĩa cũ): độ cao thô của nút lớn hơn độ cao gộp với cha. Lần gộp bị đảo: d(A,B) < max H của hai "
         "con; đảo kép: d(A,B) < min H của hai con. Độ lớn: (h(C) − h(cha))/h(C).", "",
         "| Bộ | Số mạng | Nút trong | Nút đảo | Tỉ lệ (gộp) | Tỉ lệ, trung vị theo mạng | Tỉ lệ lớn nhất | Mạng có đảo "
         "| Lần gộp bị đảo | Đảo kép | Độ lớn trung vị | Độ lớn lớn nhất | Bước giảm độ cao |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for ds, name in NAMES:
        rs = [r for r in inv if r["dataset"] == ds]
        if not rs:
            continue
        n_int, n_inv = sum(r["n_internal"] for r in rs), sum(r["n_inverted"] for r in rs)
        mags = [r["magnitude_median"] for r in rs if r["n_inverted"]]
        L.append("| %s | %d | %d | %d | %.1f%% | %.1f%% | %.1f%% | %d | %d | %d | %.3f | %.3f | %d |" % (
            name, len(rs), n_int, n_inv, 100 * n_inv / max(n_int, 1),
            100 * statistics.median(r["share_inverted"] for r in rs), 100 * max(r["share_inverted"] for r in rs),
            sum(1 for r in rs if r["n_inverted"]), sum(r["n_inverted_merges"] for r in rs), sum(r["n_double"] for r in rs),
            statistics.median(mags) if mags else 0.0, max((r["magnitude_max"] for r in rs), default=0.0),
            sum(r["n_decreasing_steps"] for r in rs)))
    L += ["", "| Bộ | Số mạng | Ψ đổi (nút, trung vị) | Tập chọn đổi | Phủ Pha I đổi | Phủ cuối đổi | ONMI(bật, tắt) "
          "phủ cuối, nhỏ nhất | ΔONMI TB | Thắng / thua ONMI | ΔONF1 TB | Thắng / thua ONF1 |",
          "|---|---:|---:|---:|---:|---:|---:|---:|:---:|---:|:---:|"]
    for ds, name in NAMES:
        rs = [r for r in cmp_rows if r["dataset"] == ds]
        if not rs:
            continue
        key = "labeled_onmi_mgh" if ds == "test3" else "onmi_mgh"
        d_onmi = [_num(r.get("d_" + key)) for r in rs]
        d_onf1 = [_num(r.get("d_onf1")) for r in rs]
        d_onmi, d_onf1 = [x for x in d_onmi if x is not None], [x for x in d_onf1 if x is not None]
        L.append("| %s | %d | %d | %d | %d | %d | %.3f | %s | %s | %s | %s |" % (
            name, len(rs), statistics.median(r["n_psi_changed"] for r in rs), sum(1 for r in rs if not r["selected_same"]),
            sum(1 for r in rs if r["onmi_on_off_pre"] < 1), sum(1 for r in rs if r["onmi_on_off_final"] < 1),
            min(r["onmi_on_off_final"] for r in rs),
            "%+.4f" % statistics.mean(d_onmi) if d_onmi else "-",
            "%d / %d" % (sum(x > 1e-12 for x in d_onmi), sum(x < -1e-12 for x in d_onmi)) if d_onmi else "-",
            "%+.4f" % statistics.mean(d_onf1) if d_onf1 else "-",
            "%d / %d" % (sum(x > 1e-12 for x in d_onf1), sum(x < -1e-12 for x in d_onf1)) if d_onf1 else "-"))
    L += ["", "Δ = bật cờ trừ tắt cờ, trên phủ cuối (Pha II cũ). Mạng protein dùng ONMI có nhãn. ONF1 chỉ tính trên "
          "mạng có nhãn chồng lấn.", ""]
    return L


def main():
    inv, cmp_rows, bad = [], [], []
    for p in sorted(TREES.glob("*/*.json")):
        rec = json.loads(p.read_text())
        if rec.get("status") != "ok":
            bad.append((p.parent.name, p.stem, rec.get("status")))
            continue
        head = {"dataset": rec["dataset"], "net_id": rec["net_id"], "n_nodes": rec["n_nodes"]}
        inv.append({**head, **inversion_stats(rec)})
        cmp_rows.append({**head, **compare_row(rec)})
    write_csv(OUT / "inversions.csv", inv)
    write_csv(OUT / "compare.csv", cmp_rows)
    (OUT / "SUMMARY.md").write_text("\n".join(summary(inv, cmp_rows)))
    print("Mạng: %d ok, %d chưa ok %s" % (len(inv), len(bad), bad[:5]))
    for r in inv:
        if r["net_id"] in ("celegans_varshney", "netscience"):
            print("%s: %d/%d nút đảo (%.1f%%)" % (r["net_id"], r["n_inverted"], r["n_internal"], 100 * r["share_inverted"]))
    print("Không trùng kết quả cũ:", [(r["dataset"], r["net_id"]) for r in cmp_rows if not r["matches_main"]])


if __name__ == "__main__":
    main()
