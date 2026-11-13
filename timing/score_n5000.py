from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S
from common import datasets, evaluate

OUT = S.RESULTS / "timing_n5000"


def main():
    rows = []
    for item in datasets.list_networks(datasets.LARGE):
        g, truth = datasets.load_network(item)
        for f in sorted(OUT.glob("*/%s.json" % item["net_id"])):
            r = json.loads(f.read_text())
            if r.get("status") != "ok":
                continue
            cover = [set(c) for c in r["cover"] if c]
            row = {"dataset": datasets.LARGE, "net_id": item["net_id"], "on": item["on"], "method": r["method"]}
            row.update(evaluate.cover_stats(g, cover))
            row.update(evaluate.evaluate(datasets.LARGE, g, cover, truth))
            row["added_memberships"] = (r.get("info") or {}).get("added_memberships")
            rows.append(row)
            print("%s %s ONMI %.3f" % (r["method"], item["net_id"], row["onmi_mgh"]), flush=True)
    pd.DataFrame(rows).to_csv(OUT / "scores.csv", index=False)
    print("Đã ghi %s" % (OUT / "scores.csv"))


if __name__ == "__main__":
    main()
