from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_k] = "1"
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
LIB = ROOT / "lib"
for _p in (str(ROOT), str(LIB)):
    while _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

DATA = ROOT / "data"
RESULTS = ROOT / "results"
RAW = RESULTS / "raw"
SCORES = RESULTS / "scores"
LOGS = RESULTS / "logs"
TMP = RESULTS / "tmp"

TOOLS = ROOT / "tools"
CT_BINARY_DIR = TOOLS / "closed_trail_distance_binary"
JAVA = TOOLS / "java" / "jre" / "bin" / "java"
if not JAVA.exists():
    JAVA = Path(shutil.which("java") or "java")
CL1_JAR = TOOLS / "clusterone" / "cluster_one-1.0.jar"

METHODS = {
    "proposed": "Phương pháp đề xuất",
    "wghac": "wGHAC",
    "oslom": "OSLOM",
    "slpa": "SLPA",
    "infomap": "Infomap",
    "bigclam": "BigCLAM",
    "danmf": "DANMF",
    "clusterone": "ClusterONE",
    "aslpaw": "ASLPAw",
}
# Biến thể chạy riêng, không nằm trong bảng 9 phương pháp
EXTRA_METHODS = {
    "bigclam_k": "BigCLAM (K thật)",
    "danmf_k": "DANMF (K thật)",
    "aslpaw_seeded": "ASLPAw (có seed)",
}
ALL_METHODS = {**METHODS, **EXTRA_METHODS}
DATASETS = {
    "test1": "Kiểm tra 1: 108 mạng LFR (N = 1000), 36 cấu trúc x 3 chế độ trọng số INJ/FLAT/PERM",
    "test2": "Kiểm tra 2: 50 mạng LFR có trọng số của Lancichinetti-Fortunato (N = 1000)",
    "test3": "Kiểm tra 3: 4 mạng tương tác protein của nấm men, nhãn phức hợp CYC2008",
}
TIME_LIMIT = 21600
WORKERS = 4


def preload_native_libs():
    import cdlib  # libgomp của hệ thống phải nạp trước bản đi kèm torch/POT


def _local_module_names():
    names = set()
    for d in (LIB, ROOT):
        for p in d.iterdir():
            if p.suffix == ".py":
                names.add(p.stem)
            elif p.is_dir() and (p / "__init__.py").exists():
                names.add(p.name)
    return names


def foreign_modules():
    names = _local_module_names()
    in_repo = (REPO / "src" / "wghac").is_dir()
    found = []
    for name, module in list(sys.modules.items()):
        f = getattr(module, "__file__", None)
        if not f:
            continue
        p = Path(f).resolve()
        if ROOT in p.parents:
            continue
        installed = bool({"site-packages", "dist-packages"} & set(p.parts))
        if name.split(".")[0] in names or (in_repo and REPO in p.parents and not installed):
            found.append("%s (%s)" % (name, p))
    return sorted(found)
