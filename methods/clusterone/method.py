# ClusterONE 1.0, tham số mặc định, đầu vào là danh sách cạnh có trọng số.

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import settings as S

USES_WEIGHTS = True


def run(g):
    S.TMP.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cl1_", dir=str(S.TMP)) as tmp:
        edges = Path(tmp) / "edges.txt"
        edges.write_text("".join("%d\t%d\t%r\n" % (u, v, float(d["weight"])) for u, v, d in sorted(g.edges(data=True))))
        cp = subprocess.run([str(S.JAVA), "-jar", str(S.CL1_JAR), "-f", "edge_list", "-F", "plain", str(edges)],
                            capture_output=True, text=True, timeout=7200, cwd=tmp)
        if cp.returncode != 0:
            raise RuntimeError("ClusterONE lỗi: %s" % cp.stderr[-500:])
        cover = [set(int(x) for x in line.split()) for line in cp.stdout.splitlines() if line.strip()]
    return cover, {}
