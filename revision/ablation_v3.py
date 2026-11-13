from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
from collections import Counter, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from common import runner

# Bóc tách cho cấu hình v3 (methods/proposed/config.json). Nhóm base dựng lại cây từ bộ đệm Pha I
# (results/revision/trees); no_log và no_ot dựng cây mới như ablation/variants.py, rồi chọn tập và Pha II theo v3.
OUT = S.RESULTS / "round_c" / "ablation"
LOGS = S.LOGS / "round_c" / "ablation"
TREES = S.RESULTS / "revision" / "trees"
PHASE2 = S.RESULTS / "revision" / "phase2"
V3_NAME = "cp_node_0.05"
VARIANTS = {"full": "Đầy đủ (v3)", "no_phase2": "Bỏ Pha II", "density": "Chọn tập theo mật độ thay cho Ψ",
            "no_log": "Bỏ nén log", "no_ot": "Bỏ vận tải tối ưu", "min_edges": "Pha II cần ít nhất 2 cạnh tới lõi"}


def groups():
    from common import datasets
    return {"base": ("test1", "test2", "test3", datasets.LARGE), "no_log": ("test1", "test2"),
            "no_ot": ("test1", "test2")}


def out_path(group, dataset, net_id):
    return OUT / group / dataset / ("%s.json" % net_id)


def _is_ok(path):
    try:
        return json.loads(path.read_text()).get("status") == "ok"
    except (OSError, ValueError):
        return False


def finish(A, g, ctx, dendrogram, cfg, mode="psi"):
    import wom_dot
    selected = A._select_sets(dendrogram, g, mode, cfg["monotone_heights"])
    cover = A._cover_from_sets(ctx.nodes, ctx.signatures, selected, cfg["tau_m"], cfg["min_comm_size"])
    cores = wom_dot.extract_cores([set(c) for c in cover], [set(s) for s in selected])
    final, _, _, _ = A._phase_two_v3(g, cover, cores, cfg)
    return cover, cores, final


def run_one(group, dataset, net_id):
    S.preload_native_libs()
    import wom_dot
    from ablation import variants as V
    from common import datasets, evaluate
    from methods.common import Dendrogram
    A = runner.load_method("proposed").algorithm
    cfg = A.load_config()
    if cfg.get("version") != 3 or cfg.get("q_bh") != 0.05 or cfg.get("phase2_family") != "node":
        raise RuntimeError("config.json không phải cấu hình v3 đã khóa")
    g0, truth = datasets.load_network(datasets.find_network(dataset, net_id))
    g = wom_dot.canonical_graph(g0)
    t0 = time.clock_gettime(time.CLOCK_MONOTONIC_RAW)
    rec = {"group": group, "dataset": dataset, "net_id": net_id, "status": "ok", "config": cfg, "variants": {}}
    if group == "base":
        tree = json.loads((TREES / dataset / ("%s.json" % net_id)).read_text())
        ctx = A._signatures(g, cfg)
        if [int(x) for x in ctx.nodes] != tree["leaves"]:
            raise RuntimeError("thứ tự lá khác bộ đệm")
        dendrogram = Dendrogram(leaves=[[x] for x in ctx.nodes], merges=[(a, b, h) for a, b, h in tree["merges"]])
        cover, cores, final = finish(A, g, ctx, dendrogram, cfg)
        floor, _, _, _ = A._phase_two_v3(g, cover, cores, dict(cfg, phase2_min_core_edges=2))
        covers = {"full": final, "no_phase2": cover, "min_edges": floor,
                  "density": finish(A, g, ctx, dendrogram, cfg, "density")[2]}
        ref = json.loads((PHASE2 / dataset / ("%s.json" % net_id)).read_text())["configs"][V3_NAME]["cover"]
        rec["matches_v3"] = sorted(sorted(int(x) for x in c) for c in final if c) == sorted(ref)
    else:
        g1, ctx, dendrogram = V.tree(g0, cfg, log_weights=group != "no_log", transport=group != "no_ot")
        covers = {group: finish(A, g1, ctx, dendrogram, cfg)[2]}
    rec["seconds"] = time.clock_gettime(time.CLOCK_MONOTONIC_RAW) - t0
    for name, cover in covers.items():
        cover = [sorted(int(x) for x in c) for c in cover if c]
        sets = [set(c) for c in cover]
        rec["variants"][name] = {"cover": cover, "cover_stats": evaluate.cover_stats(g, sets),
                                 "scores": evaluate.evaluate(dataset, g, sets, truth) if sets else {}}
    foreign = S.foreign_modules()
    if foreign:
        raise RuntimeError("Có module nạp từ ngoài thư mục thực nghiệm: %s" % ", ".join(foreign))
    runner.write_json(out_path(group, dataset, net_id), rec)
    print("[DONE] %s %s %s %.1fs matches_v3=%s" % (group, dataset, net_id, rec["seconds"], rec.get("matches_v3")))


def _run_job(job, time_limit):
    group, dataset, net_id = job
    log = LOGS / group / dataset / ("%s.log" % net_id)
    log.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with log.open("w") as fh:
        p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "one", group, dataset, net_id],
                             stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = p.wait(timeout=time_limit)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait()
            rc = 124
    f = out_path(group, dataset, net_id)
    if rc != 0 and not _is_ok(f):
        runner.write_json(f, {"group": group, "dataset": dataset, "net_id": net_id,
                              "status": "timeout" if rc == 124 else "error", "exit_code": rc,
                              "time_limit": time_limit, "seconds": time.time() - t0})
    with (S.LOGS / "round_c" / "ablation.txt").open("a") as fh:
        fh.write("%s rc=%d s=%d %s %s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), rc, time.time() - t0, group, dataset,
                                              net_id))
    return rc


def main(argv=None):
    from common import datasets
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", nargs="*", default=["base", "no_ot", "no_log"])
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--large-workers", type=int, default=2)
    ap.add_argument("--time-limit", type=int, default=S.TIME_LIMIT)
    ap.add_argument("--only", nargs="*", default=[], help="nhóm:bộ:mạng")
    ap.add_argument("--rerun", action="store_true")
    a = ap.parse_args(argv)
    G = groups()
    jobs = [(grp, d["dataset"], d["net_id"], d.get("replicate", 1)) for grp in a.groups for ds in G[grp]
            for d in datasets.list_networks(ds)]
    if a.only:
        wanted = {tuple(x.split(":")) for x in a.only}
        jobs = [j for j in jobs if j[:3] in wanted]
    jobs = [j for j in jobs if a.rerun or not _is_ok(out_path(*j[:3]))]
    # base trước (nhanh), rồi no_ot, rồi no_log lặp 1 trước lặp 2: lô bị dừng giữa chừng vẫn có tập con cân đối
    order = {g: i for i, g in enumerate(a.groups)}
    jobs.sort(key=lambda j: (order[j[0]], j[3] if isinstance(j[3], int) else 1, j[1], j[2]))
    heavy_sets = (datasets.LARGE, "test3")
    heavy = deque(j[:3] for j in jobs if j[1] in heavy_sets)
    light = deque(j[:3] for j in jobs if j[1] not in heavy_sets)
    n_heavy = max(1, min(a.large_workers, a.workers))
    lock = threading.Lock()
    rcs = []

    def worker(takes_heavy):
        while True:
            with lock:
                if takes_heavy and heavy:
                    job = heavy.popleft()
                elif light:
                    job = light.popleft()
                else:
                    return
            rc = _run_job(job, a.time_limit)
            with lock:
                rcs.append(rc)
    (S.LOGS / "round_c").mkdir(parents=True, exist_ok=True)
    with (S.LOGS / "round_c" / "ablation.txt").open("a") as fh:
        fh.write("%s START jobs=%d workers=%d time_limit=%d\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), len(jobs),
                                                                  a.workers, a.time_limit))
    print("Bóc tách v3: %d lượt, %d tiến trình" % (len(jobs), a.workers), flush=True)
    threads = [threading.Thread(target=worker, args=(i < n_heavy,)) for i in range(a.workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("Xong: %d ok, %d quá giờ, %d lỗi" % (rcs.count(0), rcs.count(124), len(rcs) - rcs.count(0) - rcs.count(124)))


def summarize():
    import pandas as pd
    from scipy.stats import wilcoxon
    from ablation.summarize import METRICS, LABELED, _f, _p, holm
    from common import datasets
    meta = {(d["dataset"], d["net_id"]): d for ds in groups()["base"] for d in datasets.list_networks(ds)}
    rows, status, match = [], Counter(), Counter()
    for p in sorted(OUT.glob("*/*/*.json")):
        r = json.loads(p.read_text())
        status[(r["group"], r["status"])] += 1
        if r["status"] != "ok":
            continue
        if "matches_v3" in r:
            match[r["matches_v3"]] += 1
        m = meta[(r["dataset"], r["net_id"])]
        for name, v in r["variants"].items():
            row = {"dataset": r["dataset"], "net_id": r["net_id"], "topology_id": m.get("topology_id", r["net_id"]),
                   "replicate": m.get("replicate"), "variant": name}
            row.update(v["scores"])
            row.update(v["cover_stats"])
            rows.append(row)
    df = pd.DataFrame(rows)
    L = ["# Bóc tách DOT-CCM v3", "", "Cập nhật %s. Cấu hình: `methods/proposed/config.json` (v3, họ theo đỉnh, "
         "q = 0,05). Kết quả: `results/round_c/ablation/`; mã: `revision/ablation_v3.py`." % time.strftime("%Y-%m-%d %H:%M"),
         "", "Trạng thái: " + ", ".join("%s %s: %d" % (g, s, n) for (g, s), n in sorted(status.items())) + ".",
         "Bản đầy đủ dựng lại từ bộ đệm trùng khít phủ v3 của đợt C: %d / %d mạng." % (match[True], sum(match.values())),
         ""]
    name = {"test1": "Kiểm tra 1", "test2": "Kiểm tra 2", "test3": "Kiểm tra 3", datasets.LARGE: "N = 5000"}
    for ds in ("test1", "test2"):
        d = df[df.dataset == ds]
        if d.empty:
            continue
        key = "topology_id" if ds == "test1" else "net_id"
        x = d.pivot_table(index=key, columns="variant", values="onmi_mgh", aggfunc="mean")
        L += ["## %s" % name[ds], "",
              "Mỗi dòng so với bản đầy đủ trên đúng các mạng mà biến thể đã chạy xong.", "",
              "| Biến thể | Số mạng | " + " | ".join(n for _, n in METRICS) + " | ONMI đầy đủ cùng mạng | Chênh ONMI "
              "| Thắng / thua | p | p (Holm) |", "|---|:---:|" + "---:|" * len(METRICS) + "---:|---:|:---:|---:|---:|"]
        tests, lines = [], []
        for v, label in VARIANTS.items():
            xv = d[d.variant == v]
            if xv.empty:
                continue
            if v == "full":
                lines.append(("| %s | %d | %s | | | | | |" % (label, len(xv), " | ".join(
                    _f(xv[c].mean()) for c, _ in METRICS)), None))
                continue
            nets = set(xv.net_id)
            full = d[(d.variant == "full") & d.net_id.isin(nets)]
            pair = x[[v, "full"]].dropna()
            diff = pair[v] - pair["full"]
            p = float(wilcoxon(pair[v], pair["full"]).pvalue) if (diff != 0).any() else 1.0
            tests.append(p)
            lines.append(("| %s | %d | %s | %s | %s | %d / %d | %s | %%s |" % (
                label, len(xv), " | ".join(_f(xv[c].mean()) for c, _ in METRICS), _f(full.onmi_mgh.mean()),
                _f(diff.mean()), (diff > 0).sum(), (diff < 0).sum(), _p(p)), len(tests) - 1))
        adj = holm(tests) if tests else []
        for text, i in lines:
            L.append(text if i is None else text % _p(adj[i]))
        L += ["", "Wilcoxon theo cặp trên ONMI%s; Holm trên các biến thể của bộ này." % (
            ", theo tô-pô (trung bình các chế độ trọng số đã có)" if ds == "test1" else ", theo mạng"), ""]
    for ds in ("test3", datasets.LARGE):
        d = df[df.dataset == ds]
        if d.empty:
            continue
        cols = LABELED if ds == "test3" else [(c, n) for c, n in METRICS]
        L += ["## %s" % name[ds], "", "| Biến thể | Số mạng | " + " | ".join(n for _, n in cols) +
              " | Số cộng đồng | Số mức thuộc TB |", "|---|:---:|" + "---:|" * (len(cols) + 2)]
        for v, label in VARIANTS.items():
            xv = d[d.variant == v]
            if not xv.empty:
                L.append("| %s | %d | %s | %.1f | %.2f |" % (label, len(xv), " | ".join(_f(xv[c].mean()) for c, _ in cols),
                                                            xv.n_communities.mean(), xv.mean_memberships.mean()))
        L += ["", "Trung bình; không kiểm định vì số mạng ít.", ""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "SUMMARY.md").write_text("\n".join(L))
    print("Đã ghi %s" % (OUT / "SUMMARY.md"))


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "one":
        run_one(*sys.argv[2:])
    elif len(sys.argv) == 2 and sys.argv[1] == "summary":
        summarize()
    else:
        main()
