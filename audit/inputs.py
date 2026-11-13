from __future__ import annotations

import csv
import inspect
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S

S.preload_native_libs()
import networkx as nx

from common import datasets

OUT = S.RESULTS / "audit"


def graph_rows():
    rows = []
    for ds in ("test1", "test2", "test3", datasets.LARGE):
        for item in datasets.list_networks(ds):
            g, truth = datasets.load_network(item)
            w = [float(d["weight"]) for _, _, d in g.edges(data=True)]
            gcc = max(nx.connected_components(g), key=len)
            bridges = sum(1 for _ in nx.bridges(g))
            core = g.copy()
            while True:
                b = list(nx.bridges(core))
                if not b:
                    break
                core.remove_edges_from(b)
                core = core.subgraph(max(nx.connected_components(core), key=len)).copy()
            labeled = set().union(*truth) if truth else set()
            rows.append({"dataset": ds, "net_id": item["net_id"], "n": g.number_of_nodes(), "m": g.number_of_edges(),
                         "w_min": min(w), "w_max": max(w), "w_below_1": sum(x < 1 for x in w),
                         "components": nx.number_connected_components(g), "gcc": len(gcc), "bridges": bridges,
                         "core_2ec": core.number_of_nodes(), "labeled_nodes": len(labeled & set(g)),
                         "truth_overlap_nodes": sum(1 for u in labeled if sum(u in t for t in truth) > 1)})
    return rows


def backends():
    seen = defaultdict(Counter)
    for p in S.RAW.glob("*/*/*.json"):
        r = json.loads(p.read_text())
        info = r.get("info") or {}
        tag = info.get("implementation") or info.get("status") or ""
        tag = tag.split(":")[0] + (":" + tag.split(":")[2] if tag.startswith("oslom_binary") else "")
        seen[r["method"]][(r["dataset"], tag)] += 1
    return seen


def coverage():
    out = defaultdict(list)
    for p in S.SCORES.glob("*/*/*.json"):
        r = json.loads(p.read_text())
        if r.get("status") == "ok":
            out[(r["method"], r["dataset"])].append(r["cover_stats"]["coverage"])
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = graph_rows()
    with (OUT / "graphs.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for ds in ("test1", "test2", "test3", datasets.LARGE):
        r = [x for x in rows if x["dataset"] == ds]
        print("%s n=%d w=[%.4g, %.4g] nets_with_w<1=%d bridges[min,max]=[%d,%d] nets_with_bridges=%d "
              "multi_component=%d core2ec_frac_min=%.3f overlap_truth_nets=%d labeled_frac=[%.2f,%.2f]" % (
                  ds, len(r), min(x["w_min"] for x in r), max(x["w_max"] for x in r),
                  sum(1 for x in r if x["w_below_1"]), min(x["bridges"] for x in r), max(x["bridges"] for x in r),
                  sum(1 for x in r if x["bridges"]), sum(1 for x in r if x["components"] > 1),
                  min(x["core_2ec"] / x["n"] for x in r), sum(1 for x in r if x["truth_overlap_nodes"]),
                  min(x["labeled_nodes"] / x["n"] for x in r), max(x["labeled_nodes"] / x["n"] for x in r)))
    for m, c in sorted(backends().items()):
        print("backend", m, dict(c))
    for (m, ds), v in sorted(coverage().items()):
        print("coverage %-10s %-12s min=%.3f median=%.3f" % (m, ds, min(v), statistics.median(v)))
    import cdlib.algorithms as A
    for name in ("aslpaw", "infomap"):
        src = inspect.getsource(getattr(A, name))
        print("==", name, "mentions weight:", "weight" in src)
        print("\n".join(l for l in src.splitlines() if "weight" in l or "Infomap(" in l or "trials" in l)[:1500])


if __name__ == "__main__":
    main()
