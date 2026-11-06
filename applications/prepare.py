# Chuyển tệp gốc của ba mạng ứng dụng trong applications/data/ thành danh sách cạnh vô hướng có trọng số
# (<mạng>.tsv: u v w) và bảng đỉnh (<mạng>_nodes.tsv), rồi ghi sha256 của mọi tệp vào checksums.csv.
#   python3 applications/prepare.py

from __future__ import annotations

import csv
import hashlib
import io
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from applications.networks import D

NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _zip_csv(path, name):
    with zipfile.ZipFile(path) as z:
        rows = list(csv.reader(io.StringIO(z.read(name).decode("utf-8"))))
    return [[c.strip() for c in r] for r in rows[1:]]


def _add(edges, u, v, w):
    if u == v:
        return False
    edges[(min(u, v), max(u, v))] += w
    return True


def _write(net, edges, nodes, cols):
    out = D / net
    with (out / ("%s.tsv" % net)).open("w") as f:
        for (u, v), w in sorted(edges.items()):
            f.write("%d\t%d\t%r\n" % (u, v, w))
    with (out / ("%s_nodes.tsv" % net)).open("w", newline="") as f:
        wr = csv.writer(f, delimiter="\t", lineterminator="\n")
        wr.writerow(["id"] + cols)
        for i in sorted(nodes):
            wr.writerow([i] + nodes[i])
    import networkx as nx
    g = nx.Graph(list(edges))
    cc = sorted((len(c) for c in nx.connected_components(g)), reverse=True)
    lcc = g.subgraph(max(nx.connected_components(g), key=len))
    ws = list(edges.values())
    print("%s: %d đỉnh trong bảng, %d đỉnh có cạnh, %d cạnh, trọng số %g-%g; %d thành phần, lớn nhất %d đỉnh / %d cạnh"
          % (net, len(nodes), g.number_of_nodes(), len(edges), min(ws), max(ws), len(cc), cc[0], lcc.number_of_edges()))


def netscience():
    z = D / "netscience" / "netscience.csv.zip"
    nodes = {int(r[0]): [r[1]] for r in _zip_csv(z, "nodes.csv")}
    edges, loops = defaultdict(float), 0
    for s, t, w in (r[:3] for r in _zip_csv(z, "edges.csv")):
        loops += not _add(edges, int(s), int(t), float(w))
    print("netscience: %d dòng cạnh, %d khuyên bỏ qua" % (sum(1 for _ in _zip_csv(z, "edges.csv")), loops))
    _write("netscience", edges, nodes, ["name"])


def brain_coactivation():
    z = D / "brain_coactivation" / "coactivation.csv.zip"
    nodes = {}
    for r in _zip_csv(z, "nodes.csv"):
        xyz = NUMBER.findall(r[1])
        if len(xyz) != 3:
            raise ValueError("Tọa độ không đủ 3 số: %r" % r[1])
        nodes[int(r[0])] = xyz
    edges, loops = defaultdict(float), 0
    for s, t, w in (r[:3] for r in _zip_csv(z, "edges.csv")):
        loops += not _add(edges, int(s), int(t), float(w))
    print("brain_coactivation: %d khuyên bỏ qua" % loops)
    _write("brain_coactivation", edges, nodes, ["x", "y", "z"])


# khớp hóa học: bản ghi S, Sp (Neuron 1 gửi sang Neuron 2); R, Rp là cùng các khớp ghi ở phía nhận.
# khớp điện EJ ghi cả hai chiều. NMJ là khớp thần kinh - cơ, không thuộc mạng nơ-ron - nơ-ron.
# một bản ghi trong NeuronConnect.xls viết tên bằng chữ thường (avfl, avfr), nên tên được viết hoa trước khi tra.
def celegans_varshney():
    import pandas as pd
    d = D / "celegans_varshney"
    con = pd.read_excel(d / "NeuronConnect.xls")
    typ = pd.read_excel(d / "NeuronType.xls")
    con.columns = [c.strip() for c in con.columns]
    typ.columns = [c.strip() for c in typ.columns]
    names = sorted(str(x).strip() for x in typ["Neuron"])
    idx = {n: i for i, n in enumerate(names)}
    send, recv, gap = defaultdict(int), defaultdict(int), defaultdict(int)
    kinds, lower = defaultdict(int), 0
    for a, b, t, n in con[["Neuron 1", "Neuron 2", "Type", "Nbr"]].itertuples(index=False):
        a, b, t, n = str(a).strip(), str(b).strip(), str(t).strip(), int(n)
        lower += a != a.upper() or b != b.upper()
        a, b = a.upper(), b.upper()
        kinds[t] += n
        if t == "NMJ":
            continue
        if a not in idx or b not in idx:
            raise ValueError("Nơ-ron không có trong NeuronType.xls: %s %s" % (a, b))
        if t in ("S", "Sp"):
            send[(a, b)] += n
        elif t in ("R", "Rp"):
            recv[(b, a)] += n
        elif t == "EJ":
            gap[(a, b)] += n
        else:
            raise ValueError("Loại khớp lạ: %s" % t)
    print("celegans_varshney: tổng Nbr theo loại %s; %d bản ghi có tên chữ thường" % (dict(sorted(kinds.items())), lower))
    diff = sorted(k for k in set(send) | set(recv) if send.get(k, 0) != recv.get(k, 0))
    print("  khớp hóa học phía gửi %d, phía nhận %d; %d cặp có hướng lệch giữa hai phía (dùng phía gửi):"
          % (sum(send.values()), sum(recv.values()), len(diff)))
    for k in diff:
        print("    %s -> %s: gửi %d, nhận %d" % (k[0], k[1], send.get(k, 0), recv.get(k, 0)))
    asym = sorted(k for k in gap if gap[k] != gap.get((k[1], k[0]), 0))
    if asym:
        raise ValueError("Khớp điện ghi không đối xứng: %s" % asym[:10])
    edges, loops = defaultdict(int), 0
    for (a, b), n in send.items():
        loops += not _add(edges, idx[a], idx[b], n)
    for (a, b), n in gap.items():
        if a < b:
            _add(edges, idx[a], idx[b], n)
        elif a == b:
            loops += 1
    print("  khớp điện %d (đếm một lần mỗi cặp), %d cặp; %d bản ghi khuyên bỏ qua"
          % (sum(n for (a, b), n in gap.items() if a < b), sum(1 for a, b in gap if a < b), loops))
    t = typ.set_index(typ["Neuron"].astype(str).str.strip())
    nodes = {idx[n]: [n, str(t.at[n, "Soma Region"]).strip(), "%g" % float(t.at[n, "Soma Position"]),
                      str(t.at[n, "AY Ganglion Designation"]).strip()] for n in names}
    _write("celegans_varshney", edges, nodes, ["name", "soma_region", "soma_position", "ganglion"])


def checksums():
    rows = []
    for p in sorted(D.rglob("*")):
        if p.is_file() and p.name != "checksums.csv":
            rows.append([p.relative_to(D).as_posix(), p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest()])
    with (D / "checksums.csv").open("w", newline="") as f:
        wr = csv.writer(f, lineterminator="\n")
        wr.writerow(["path", "size", "sha256"])
        wr.writerows(rows)
    print("checksums.csv: %d tệp" % len(rows))


if __name__ == "__main__":
    netscience()
    brain_coactivation()
    celegans_varshney()
    checksums()
