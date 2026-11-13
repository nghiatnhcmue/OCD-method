from __future__ import annotations

import json
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from timing.run_timing import SEED
from applications import networks
from applications.run import OUT, _rel, out_path

TITLE = {"celegans_varshney": "Nơ-ron C. elegans (Varshney et al. 2011)",
         "netscience": "Đồng tác giả khoa học mạng (Newman 2006), thành phần liên thông lớn nhất",
         "brain_coactivation": "Vùng não người, mạng đồng kích hoạt (Crossley et al. 2013)"}
SHORT = {"celegans_varshney": "C. elegans", "netscience": "Đồng tác giả", "brain_coactivation": "Não người"}
METHOD = {"proposed": "Phương pháp đề xuất", "wghac": "wGHAC"}
GANGLIA = {"A": "hạch trước", "B": "hạch lưng", "C": "hạch bên", "D": "hạch bụng", "E": "hạch retrovesicular",
           "F": "nhóm thân bên", "G": "dây thần kinh bụng", "H": "hạch trước hậu môn", "J": "hạch lưng trực tràng",
           "K": "hạch thắt lưng"}
REGION = {"H": "đầu", "M": "thân", "T": "đuôi"}
PERM = 100
LIST_MAX = 60


def _read(net, method, r=0):
    p = out_path(net, method, r)
    return json.loads(p.read_text()) if p.exists() else None


def _ok(d):
    return bool(d) and d.get("status") == "ok"


def _status(net, method, d, r=0):
    if not d:
        return "chưa chạy"
    if d["status"] != "error":
        return d["status"]
    lines = (S.LOGS / "applications" / _rel(net, method, r).with_suffix(".log")).read_text().strip().splitlines()
    last = lines[-1] if lines else "?"
    mem = re.search(r"Unable to allocate ([\d.]+ \w+) for an array with shape \((\d+), (\d+)\)", last)
    if mem:
        return "thiếu bộ nhớ: cần mảng %s x %s (%s)" % (mem.group(2), mem.group(3), mem.group(1))
    return "lỗi: %s" % last


def _cover(d):
    return sorted((set(c) for c in d["cover"]), key=lambda c: (-len(c), min(c)))


def _member(cover):
    m = defaultdict(list)
    for i, c in enumerate(cover):
        for u in c:
            m[u].append(i)
    return m


def _permute(cover, nodes, rng):
    m = dict(zip(nodes, (int(x) for x in rng.permutation(nodes))))
    return [{m[u] for u in c} for c in cover]


def _onmi(g, a, b):
    from metrics.scoring import score
    s = score(g, [sorted(c) for c in a], [sorted(c) for c in b])
    return s["onmi_mgh"], s["omega"]


def _strength(g, c, u):
    return sum(d["weight"] for v, d in g[u].items() if v in c)


def _top(g, c, label, k=8):
    return ", ".join(label(u) for u in sorted(c, key=lambda u: (-_strength(g, c, u), u))[:k])


def _f(x, nd=3):
    return "-" if x is None or x != x else "%.*f" % (nd, x)


def _pct(x):
    return "-" if x is None or x != x else "%.1f%%" % (100 * x)


def _stats(g, d):
    from common.evaluate import cover_stats
    from methods.dothac import _weighted_conductance
    cover = _cover(d)
    total = g.size(weight="weight")
    final = Counter(u for c in cover for u in c)
    pre = Counter(u for c in d.get("pre_cover", []) for u in c)
    steps = d["info"].get("step_seconds") or {}
    st = cover_stats(g, cover)
    sizes = [len(c) for c in cover]
    rank = {tuple(sorted(c)): i for i, c in enumerate(cover)}
    number = [rank[tuple(sorted(c))] + 1 for c in d["cover"]]
    return {"cover": cover, "number": number, "k": len(cover), "size_median": statistics.median(sizes), "size_max": max(sizes),
            "coverage": st["coverage"], "mean_memberships": st["mean_memberships"],
            "overlap_final": sum(1 for x in final.values() if x > 1), "overlap_pre": sum(1 for x in pre.values() if x > 1),
            "adds": d.get("adds", []), "phi": [_weighted_conductance(g, c, total) for c in cover],
            "wall": d["wall_seconds"], "merge": steps["C_merge"] / steps["total"] if steps.get("total") else None}


def _overlap_rows(g, cover, label, extra=lambda u: [], key=None):
    m = _member(cover)
    over = sorted((u for u, cs in m.items() if len(cs) > 1), key=key or label)
    rows = []
    for u in over[:LIST_MAX]:
        links = "; ".join("%d: %s" % (i + 1, _f(_strength(g, cover[i], u), 2)) for i in m[u])
        rows.append("| %s | %s |" % (" | ".join([label(u)] + extra(u)), links))
    more = len(over) - len(rows)
    return over, rows, more


def celegans(g, s, L):
    t = networks.node_table("celegans_varshney")
    name = {i: r["name"] for i, r in t.items()}
    idx = {n: i for i, n in name.items()}
    pairs = [(idx[n], idx[n[:-1] + "R"]) for n in sorted(idx) if n.endswith("L") and n[:-1] + "R" in idx]
    cover, nodes, rng = s["cover"], sorted(g), np.random.default_rng(SEED)

    def together(cv):
        m = _member(cv)
        return sum(1 for a, b in pairs if set(m[a]) & set(m[b])) / len(pairs)

    pair_obs = together(cover)
    pair_null = [together(_permute(cover, nodes, rng)) for _ in range(PERM)]
    gang = defaultdict(set)
    for i, r in t.items():
        gang[r["ganglion"]].add(i)
    truth = [gang[k] for k in sorted(gang)]
    g_obs = _onmi(g, cover, truth)[0]
    g_null = [_onmi(g, _permute(cover, nodes, rng), truth)[0] for _ in range(PERM)]
    L += ["## %s" % TITLE["celegans_varshney"], "",
          "- Cặp nơ-ron trái/phải cùng ít nhất một cộng đồng: %d/%d cặp (%s). Mốc hoán vị nhãn đỉnh (%d lần): trung bình %s, "
          "lớn nhất %s." % (round(pair_obs * len(pairs)), len(pairs), _pct(pair_obs), PERM, _pct(statistics.mean(pair_null)),
                            _pct(max(pair_null))),
          "- ONMI giữa tập bao phủ và 10 hạch giải phẫu: %s. Mốc hoán vị nhãn đỉnh: trung vị %s, lớn nhất %s."
          % (_f(g_obs), _f(statistics.median(g_null)), _f(max(g_null))),
          "- Ký hiệu hạch (Achacoso và Yamamoto 1992, cột AY Ganglion Designation): "
          + ", ".join("%s %s" % kv for kv in GANGLIA.items()) + ".", "",
          "| # | Cỡ | Đầu / thân / đuôi | Hạch (số nơ-ron) | Độ dẫn | Nơ-ron có trọng số nội bộ lớn nhất |",
          "|---:|---:|:---:|---|---:|---|"]
    for i, c in enumerate(cover):
        reg = Counter(t[u]["soma_region"] for u in c)
        gan = Counter(t[u]["ganglion"] for u in c)
        L.append("| %d | %d | %d / %d / %d | %s | %s | %s |" % (
            i + 1, len(c), reg["H"], reg["M"], reg["T"], ", ".join("%s %d" % kv for kv in sorted(gan.items())),
            _f(s["phi"][i]), _top(g, c, name.get)))
    over, rows, more = _overlap_rows(g, cover, name.get, lambda u: [REGION[t[u]["soma_region"]], t[u]["ganglion"]])
    L += ["", "Nơ-ron thuộc nhiều cộng đồng: %d." % len(over)]
    if rows:
        L += ["", "| Nơ-ron | Vùng | Hạch | Cộng đồng: trọng số nối vào |", "|---|---|:---:|---|"] + rows
        if more:
            L.append("| ... còn %d nơ-ron | | | |" % more)
    L.append("")


def brain(g, s, L):
    from scipy.spatial.distance import pdist
    t = networks.node_table("brain_coactivation")
    nodes = sorted(g)
    X = np.array([[float(t[u][k]) for k in ("x", "y", "z")] for u in nodes])
    pos = {u: i for i, u in enumerate(nodes)}
    cover, rng = s["cover"], np.random.default_rng(SEED)
    rows, ratios, one_side = [], [], 0
    for i, c in enumerate(cover):
        ids = np.array(sorted(pos[u] for u in c))
        left, right = int((X[ids, 0] < 0).sum()), int((X[ids, 0] > 0).sum())
        one_side += max(left, right) >= 0.9 * len(c)
        obs = float(pdist(X[ids]).mean()) if len(ids) > 1 else 0.0
        null = statistics.mean(float(pdist(X[rng.choice(len(nodes), len(ids), replace=False)]).mean()) for _ in range(PERM))
        ratios.append(obs / null)
        cx, cy, cz = X[ids].mean(axis=0)
        rows.append("| %d | %d | %d / %d | %.0f, %.0f, %.0f | %.1f | %.1f | %s |"
                    % (i + 1, len(c), left, right, cx, cy, cz, obs, null, _f(s["phi"][i])))
    L += ["## %s" % TITLE["brain_coactivation"], "",
          "- Cộng đồng có ít nhất 90%% số vùng cùng một bán cầu (x < 0 là bán cầu trái): %d/%d." % (one_side, len(cover)),
          "- Khoảng cách trung bình giữa hai vùng trong cùng cộng đồng, chia cho giá trị đó của tập vùng ngẫu nhiên cùng cỡ "
          "(%d lần chọn): trung vị %s, từ %s đến %s." % (PERM, _f(statistics.median(ratios), 2), _f(min(ratios), 2),
                                                        _f(max(ratios), 2)),
          "- Tọa độ tính bằng mm trong không gian chuẩn; y > 0 là phía trước (thùy trán), z > 0 là phía trên.", "",
          "| # | Cỡ | Trái / phải | Tâm (x, y, z) | Khoảng cách TB (mm) | Tập ngẫu nhiên (mm) | Độ dẫn |",
          "|---:|---:|:---:|:---:|---:|---:|---:|"] + rows

    def label(u):
        return "vùng %d (%s)" % (u, ", ".join("%.0f" % v for v in X[pos[u]]))

    over, rows, more = _overlap_rows(g, cover, label, key=int)
    L += ["", "Vùng thuộc nhiều cộng đồng: %d." % len(over)]
    if rows:
        L += ["", "| Vùng (x, y, z) | Cộng đồng: trọng số nối vào |", "|---|---|"] + rows
        if more:
            L.append("| ... còn %d vùng | |" % more)
    L.append("")


def netscience(g, s, L):
    t = networks.node_table("netscience")
    name = {i: r["name"] for i, r in t.items()}
    cover = s["cover"]
    L += ["## %s" % TITLE["netscience"], "", "| # | Cỡ | Độ dẫn | Tác giả có trọng số nội bộ lớn nhất |", "|---:|---:|---:|---|"]
    for i, c in enumerate(cover):
        L.append("| %d | %d | %s | %s |" % (i + 1, len(c), _f(s["phi"][i]), _top(g, c, name.get)))
    over, rows, more = _overlap_rows(g, cover, name.get)
    L += ["", "Tác giả thuộc nhiều cộng đồng: %d." % len(over)]
    if rows:
        L += ["", "| Tác giả | Cộng đồng: trọng số nối vào |", "|---|---|"] + rows
        if more:
            L.append("| ... còn %d tác giả | |" % more)
    L.append("")


def phase_two(stats, L):
    L += ["## Mức thuộc do Pha II thêm", ""]
    rows = []
    for net, s in stats.items():
        label = _labeler(net)
        for u, c, w, mu, var, p in s["adds"][:LIST_MAX]:
            rows.append("| %s | %s | %d | %s | %s | %.2g |" % (SHORT[net], label(u), s["number"][c], _f(w, 2), _f(mu, 2), p))
        if len(s["adds"]) > LIST_MAX:
            rows.append("| %s | ... còn %d mức thuộc | | | | |" % (SHORT[net], len(s["adds"]) - LIST_MAX))
    if not rows:
        L += ["Pha II không thêm mức thuộc nào trên ba mạng.", ""]
        return
    L += ["Kỳ vọng và p theo mô hình CCM của Pha II; p chưa hiệu chỉnh, BH mức q = 0.001 theo từng đỉnh.", "",
          "| Mạng | Đỉnh | Cộng đồng | Trọng số nối vào lõi | Kỳ vọng | p |", "|---|---|---:|---:|---:|---:|"] + rows + [""]


def _labeler(net):
    t = networks.node_table(net)
    if net == "brain_coactivation":
        return lambda u: "vùng %d" % u
    return lambda u: t[u]["name"]


def stability(L):
    L += ["## Độ ổn định khi bỏ 5% cạnh", "",
          "Mỗi bản nhiễu bỏ ngẫu nhiên 5%% số cạnh (hạt giống %d + r), không để đỉnh nào mất hết cạnh. ONMI và Omega so với "
          "tập bao phủ trên mạng gốc; mốc ngẫu nhiên: tập bao phủ gốc với nhãn đỉnh bị xáo (10 lần)." % SEED, "",
          "| Mạng | Phương pháp | Cộng đồng (gốc) | Cỡ lớn nhất (gốc) | Bản nhiễu ok | ONMI: trung vị (min-max) | Omega trung vị "
          "| ONMI mốc ngẫu nhiên | Cộng đồng sau nhiễu (min-max) |", "|---|---|---:|---:|:---:|:---:|---:|---:|:---:|"]
    for net in networks.NETS:
        g = networks.load(net)
        nodes = sorted(g)
        for m in ("proposed", "wghac"):
            d0 = _read(net, m)
            if not _ok(d0):
                L.append("| %s | %s | %s | | | | | | |" % (SHORT[net], METHOD[m], _status(net, m, d0)))
                continue
            c0 = _cover(d0)
            files = sorted((OUT / "stability" / net / m).glob("r*.json"))
            runs = [json.loads(p.read_text()) for p in files]
            ok = [d for d in runs if _ok(d)]
            sc = [_onmi(g, c0, _cover(d)) for d in ok]
            rng = np.random.default_rng(SEED)
            base = [_onmi(g, c0, _permute(c0, nodes, rng))[0] for _ in range(10)]
            on = [x[0] for x in sc]
            ks = [len(d["cover"]) for d in ok]
            L.append("| %s | %s | %d | %d/%d | %d/%d | %s | %s | %s | %s |" % (
                SHORT[net], METHOD[m], len(c0), max(len(c) for c in c0), len(nodes), len(ok), len(runs),
                "%s (%s-%s)" % (_f(statistics.median(on)), _f(min(on)), _f(max(on))) if on else "-",
                _f(statistics.median(x[1] for x in sc)) if sc else "-", _f(statistics.median(base)),
                "%d-%d" % (min(ks), max(ks)) if ks else "-"))
    L.append("")


def main():
    S.preload_native_libs()
    stats, L = {}, []
    for net in networks.NETS:
        d = _read(net, "proposed")
        if _ok(d):
            stats[net] = _stats(networks.load(net), d)
    L += ["# Mạng ứng dụng: kết quả của phương pháp đề xuất", "",
          "Cập nhật %s. Tham số như trong `methods/proposed/config.json`." % time.strftime("%Y-%m-%d %H:%M"), "",
          "## Tổng quan", "",
          "| Mạng | Đỉnh | Cạnh | Cộng đồng | Cỡ trung vị / lớn nhất | Độ phủ | Mức thuộc TB | Đỉnh chồng lấn: Pha I / cuối "
          "| Mức thuộc Pha II thêm | Độ dẫn trung vị | Thời gian (s) | Bước gộp |",
          "|---|---:|---:|---:|:---:|---:|---:|:---:|---:|---:|---:|---:|"]
    for net in networks.NETS:
        g = networks.load(net)
        if net not in stats:
            L.append("| %s | %d | %d | %s | | | | | | | | |" % (SHORT[net], g.number_of_nodes(), g.number_of_edges(),
                                                              _status(net, "proposed", _read(net, "proposed"))))
            continue
        s = stats[net]
        L.append("| %s | %d | %d | %d | %s / %d | %s | %s | %d / %d | %d | %s | %.0f | %s |" % (
            SHORT[net], g.number_of_nodes(), g.number_of_edges(), s["k"], "%g" % s["size_median"], s["size_max"],
            _pct(s["coverage"]), _f(s["mean_memberships"], 2), s["overlap_pre"], s["overlap_final"], len(s["adds"]),
            _f(statistics.median(s["phi"])), s["wall"], _pct(s["merge"])))
    L += ["", "Độ dẫn: độ dẫn có trọng số của từng cộng đồng. Bước gộp: phần của bước gộp cụm trong tổng thời gian các "
          "bước. Thời gian đo cùng điều kiện với timing/run_timing.py.", ""]
    for net, fn in (("celegans_varshney", celegans), ("brain_coactivation", brain), ("netscience", netscience)):
        if net in stats:
            fn(networks.load(net), stats[net], L)
    if stats:
        phase_two(stats, L)
    stability(L)
    L += ["## Thời gian chạy trên mạng gốc", "", "| Mạng | Phương pháp đề xuất (s) | wGHAC (s) |", "|---|---:|---:|"]
    for net in networks.NETS:
        cells = []
        for m in ("proposed", "wghac"):
            d = _read(net, m)
            cells.append("%.0f" % d["wall_seconds"] if _ok(d) else _status(net, m, d))
        L.append("| %s | %s | %s |" % (SHORT[net], cells[0], cells[1]))
    L.append("")
    (OUT / "SUMMARY.md").write_text("\n".join(L))
    print("Đã ghi %s" % (OUT / "SUMMARY.md"))


if __name__ == "__main__":
    main()
