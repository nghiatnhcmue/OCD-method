from __future__ import annotations

import settings

NAN = float("nan")


def _metrics(g, cover, truth):
    import coverage_metrics as CM
    from campaign_metrics import yl_scores
    from diagnostics import node_metrics
    from metrics.scoring import score
    cov = [set(c) for c in cover if c]
    m = score(g, [sorted(c) for c in cov], truth)
    f1 = yl_scores([sorted(c) for c in cov], [sorted(c) for c in truth])["f1_yl"]
    onf1 = node_metrics(g, cov, truth)[0]["overlap_f1"]
    T = [set(str(x) for x in c) for c in truth]
    P = [set(str(x) for x in c) for c in cov]
    o, pm = CM.overlap_pr(T, P), CM.membership_pr(T, P)
    return {"onmi_mgh": m["onmi_mgh"], "onmi_lfk": m["onmi_lfk"], "omega": m["omega"], "f1": f1, "onf1": onf1,
            "P_O": o["P_O"], "R_O": o["R_O"], "P_mem": pm["P_mem"], "R_mem": pm["R_mem"]}


def evaluate(dataset, g, cover, truth):
    scores = _metrics(g, cover, truth)
    count = {}
    for c in truth:
        for u in c:
            count[u] = count.get(u, 0) + 1
    # nhãn chuẩn không có đỉnh chồng lấn: ONF1 và R_O không xác định
    if not any(k > 1 for k in count.values()):
        scores["onf1"] = NAN
        scores["R_O"] = NAN
    # Kiểm tra 3: chấm thêm trên đồ thị con gồm các đỉnh có nhãn CYC2008
    if dataset == "test3":
        labeled = set(count)
        projected = [c for c in (set(c) & labeled for c in cover) if len(c) >= 2]
        if projected:
            m = _metrics(g.subgraph(labeled).copy(), projected, truth)
            for k in ("onmi_mgh", "onmi_lfk", "omega", "f1", "onf1"):
                scores["labeled_" + k] = m[k]
            scores["labeled_coverage"] = len(set().union(*projected)) / len(labeled)
    return scores


def cover_stats(g, cover):
    V = set(g.nodes())
    members = [u for c in cover for u in c]
    return {"n_communities": len(cover), "coverage": len(set(members) & V) / len(V), "mean_memberships": len(members) / len(V),
            "max_size": max((len(c) for c in cover), default=0), "nodes_outside_graph": len(set(members) - V)}
