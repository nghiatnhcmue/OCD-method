from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import datasets


def timing_subset():
    nets = [d for d in datasets.list_networks("test1") if d["replicate"] == 1 and d["regime"] == "INJ"]
    nets += [d for d in datasets.list_networks("test2")
             if d["replicate"] == 1 and (d["on"] == 0 or (d["on"] == 300 and d["om"] == 4))]
    return nets + datasets.list_networks("test3")


if __name__ == "__main__":
    nets = timing_subset()
    for d in nets:
        print(d["dataset"], d["net_id"], d["mu"], d["mu_w"], d["on"], d["om"])
    print(len(nets), "mạng")
