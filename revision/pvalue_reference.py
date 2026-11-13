from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binom, gamma, poisson

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings as S

S.preload_native_libs()
import ccm_tail as C
from wom_v1 import pvalue

OUT = S.RESULTS / "revision" / "pvalues" / "reference.csv"
# N = 5000, mọi đỉnh bậc 20, trọng số trung bình 1, lõi 15 đỉnh
N, DEG, CORE = 5000, 20, 15
P_EDGE = DEG * DEG / (N * DEG)


def main():
    rng = np.random.default_rng(42)
    n = 10_000_000
    rows = []
    for kappa in (0.25, 1.0):
        k = rng.binomial(CORE, P_EDGE, size=n)
        T = np.zeros(n)
        hit = k > 0
        T[hit] = rng.gamma(k[hit] / kappa, kappa)
        lam = -CORE * np.log1p(-P_EDGE)
        m = np.arange(1, 80)
        mu, var = CORE * P_EDGE, CORE * P_EDGE * (1 - P_EDGE + kappa)
        for t in (1.0, 1.5, 2.0, 3.0, 4.0):
            mc = (T >= t).mean()
            rows.append({"kappa": kappa, "t": t, "monte_carlo": mc, "mc_se": np.sqrt(mc * (1 - mc) / n),
                         "exact": float(np.sum(binom.pmf(m[:CORE], CORE, P_EDGE) * gamma.sf(t, m[:CORE] / kappa, scale=kappa))),
                         "cp_closed": float(np.sum(poisson.pmf(m, lam) * gamma.sf(t, m / kappa, scale=kappa))),
                         "cp_grid": C.cp_tails([t], [np.full(CORE, P_EDGE)], [np.ones(CORE)], C.XiLaw(kappa))[0],
                         "normal": pvalue(t, mu, var)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print("kappa=%.2f t=%.1f MC=%.3g exact=%.3g cp_grid=%.3g (x%.3f) normal=%.2g" % (
            r["kappa"], r["t"], r["monte_carlo"], r["exact"], r["cp_grid"], r["cp_grid"] / r["exact"], r["normal"]))


if __name__ == "__main__":
    main()
