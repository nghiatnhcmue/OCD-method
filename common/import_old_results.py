from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S

OLD = S.REPO / "results" / "kiem_tra_luan_van" / "raw"
OLD_DATASET = {"kiem_tra_1": "test1", "kiem_tra_2": "test2", "kiem_tra_3": "test3"}
OLD_METHOD = {"proposed": "phien_ban_2"}
UNCHANGED = ("oslom", "slpa", "infomap", "bigclam", "clusterone", "aslpaw", "wghac")
CHANGED = ("proposed", "danmf")


def copy_old(method, dest_root, source):
    n = 0
    for f in sorted(OLD.glob("*/%s/*.json" % OLD_METHOD.get(method, method))):
        dataset = OLD_DATASET[f.parent.parent.name]
        dest = dest_root / dataset / method / f.name
        if dest.exists():
            continue
        r = json.loads(f.read_text())
        if r.get("trang_thai", "ok") != "ok" or not r.get("cover"):
            continue
        info = {("status" if k == "trang_thai" else k): v for k, v in (r.get("info") or {}).items()}
        rec = {"dataset": dataset, "net_id": r["net_id"], "method": method, "seconds": r.get("giay"), "status": "ok",
               "info": info, "cover": r["cover"], "source": source}
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(rec, indent=1, ensure_ascii=False))
        n += 1
    return n


if __name__ == "__main__":
    methods = sys.argv[1:] or UNCHANGED
    for m in methods:
        if m not in UNCHANGED:
            raise SystemExit("%s đã sửa mã: phải chạy lại, không nhập kết quả cũ" % m)
        print(m, "chép", copy_old(m, S.RAW, "imported: results/kiem_tra_luan_van/raw (earlier run, unchanged method code)"))
    if not sys.argv[1:]:
        for m in CHANGED:
            print(m, "lưu đối chiếu", copy_old(m, S.RESULTS / "before_fix" / "raw", "earlier run, before fix"))
