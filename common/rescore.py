# Chấm lại từ results/raw/ mà không chạy lại phương pháp.
#   python3 common/rescore.py [--workers 4] [--dataset test1 ...] [--method wghac ...] [--missing-only]

from __future__ import annotations

import argparse
import json
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S


def _rescore(f):
    try:
        S.preload_native_libs()
        from common import datasets, runner
        raw = json.loads(Path(f).read_text())
        dataset, method = Path(f).parent.parent.name, Path(f).parent.name
        runner.score_and_write(datasets.find_network(dataset, raw["net_id"]), method, raw)
        return f, None
    except Exception as e:
        return f, "%s: %s" % (type(e).__name__, e)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=S.WORKERS)
    ap.add_argument("--dataset", nargs="*")
    ap.add_argument("--method", nargs="*")
    ap.add_argument("--missing-only", action="store_true")
    a = ap.parse_args()
    files = []
    for f in sorted(S.RAW.glob("*/*/*.json")):
        dataset, method = f.parent.parent.name, f.parent.name
        if (a.dataset and dataset not in a.dataset) or (a.method and method not in a.method):
            continue
        s = S.SCORES / dataset / method / f.name
        if a.missing_only and s.exists() and s.stat().st_mtime >= f.stat().st_mtime:
            continue
        files.append(str(f))
    print("Chấm lại %d lượt, %d tiến trình" % (len(files), a.workers), flush=True)
    errors = []
    with Pool(a.workers) as pool:
        for i, (f, e) in enumerate(pool.imap_unordered(_rescore, files), 1):
            if e:
                errors.append((f, e))
            if i % 100 == 0 or i == len(files):
                print("  %d/%d" % (i, len(files)), flush=True)
    for f, e in errors:
        print("  LỖI %s: %s" % (f, e), flush=True)
    if errors:
        sys.exit("Chấm lại: %d tệp lỗi" % len(errors))
