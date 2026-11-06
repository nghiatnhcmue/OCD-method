# 32 mạng đại diện để đo thời gian: Kiểm tra 1 mọi ô mu x mức chồng lấn (INJ, lần lặp 1), Kiểm tra 2
# mọi cặp (mu_t, mu_w) với on = 0 và on = 300, om = 4 (lần lặp 1), Kiểm tra 3 cả 4 mạng.

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
