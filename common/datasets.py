# Danh sách mạng của ba bộ kiểm tra và hàm đọc một mạng (đồ thị có trọng số, nhãn chuẩn).

from __future__ import annotations

import json

import networkx as nx

import settings as S

DATA_DIRS = {"test1": "kiem_tra_1", "test2": "kiem_tra_2", "test3": "kiem_tra_3"}


def _data_path(p):
    return S.DATA / p.split("data/kiem_tra_luan_van/", 1)[-1]


def _manifest(dataset):
    return json.loads((S.DATA / DATA_DIRS[dataset] / "MANIFEST.json").read_text())


def list_networks(dataset=None):
    nets = []
    for t in _manifest("test1")["topologies"]:
        for regime in ("INJ", "FLAT", "PERM"):
            nets.append({"dataset": "test1", "net_id": "%s_%s" % (t["topology_id"], regime), "topology_id": t["topology_id"],
                         "regime": regime, "edges": _data_path(t["edge_files"][regime]), "truth": _data_path(t["gt"]),
                         "mu": t["mu"], "mu_w": "", "on": t["on"], "om": t["om"], "replicate": t["replicate"]})
    d2 = S.DATA / DATA_DIRS["test2"]
    for n in _manifest("test2")["networks"]:
        s = n["stem"]
        nets.append({"dataset": "test2", "net_id": s, "topology_id": s, "regime": "original",
                     "edges": d2 / ("%s.tsv" % s), "truth": d2 / ("%s_gt.json" % s),
                     "mu": n["mu_t"], "mu_w": n["mu_w"], "on": n["on"], "om": n["om"] or "", "replicate": n["replicate"]})
    for m in _manifest("test3")["mang"]:
        nets.append({"dataset": "test3", "net_id": m["ten"], "topology_id": m["ten"], "regime": "ppi",
                     "edges": _data_path(m["graph"]), "truth": _data_path(m["phuc_hop"]["cyc2008"]["tep"]),
                     "mu": "", "mu_w": "", "on": "", "om": "", "replicate": ""})
    return [d for d in nets if dataset is None or d["dataset"] == dataset]


def find_network(dataset, net_id):
    for d in list_networks(dataset):
        if d["net_id"] == net_id:
            return d
    raise ValueError("Không có mạng %s trong %s" % (net_id, dataset))


def load_network(item):
    g = nx.Graph()
    for line in item["edges"].read_text().splitlines():
        f = line.split()
        if len(f) >= 3:
            g.add_edge(int(f[0]), int(f[1]), weight=float(f[2]))
    truth = []
    for c in json.loads(item["truth"].read_text()):
        truth.append(set(int(x) for x in (c.get("dinh", []) if isinstance(c, dict) else c)))
    g.add_nodes_from(u for c in truth for u in c)
    return g, truth
