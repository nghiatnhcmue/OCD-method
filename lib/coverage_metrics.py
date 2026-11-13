from __future__ import annotations

from collections import Counter

import numpy as np
from scipy.optimize import linear_sum_assignment


def overlapping_nodes(cover):
    count = Counter(v for c in cover for v in c)
    return {v for v, m in count.items() if m > 1}


def overlap_pr(truth, pred):
    Vt, Vp = overlapping_nodes(truth), overlapping_nodes(pred)
    if not Vt and not Vp:
        return {"ONF1": float("nan"), "P_O": float("nan"), "R_O": float("nan")}
    hit = len(Vt & Vp)
    P = hit / len(Vp) if Vp else 0.0
    R = hit / len(Vt) if Vt else 0.0
    F = 2 * P * R / (P + R) if P + R > 0 else 0.0
    return {"ONF1": F, "P_O": P, "R_O": R}


def dice_matching(truth, pred):
    t = [set(c) for c in truth]
    p = [set(c) for c in pred]
    D = np.zeros((len(p), len(t)))
    for j, P in enumerate(p):
        for i, T in enumerate(t):
            common = len(P & T)
            if common:
                D[j, i] = 2 * common / (len(P) + len(T))
    rows, cols = linear_sum_assignment(-D)
    return [(int(j), int(i)) for j, i in zip(rows, cols) if D[j, i] > 0]


def membership_pr(truth, pred):
    t = [set(c) for c in truth]
    p = [set(c) for c in pred]
    c = sum(len(p[j] & t[i]) for j, i in dice_matching(t, p))
    n_pred = sum(len(P) for P in p)
    n_true = sum(len(T) for T in t)
    return {"P_mem": c / n_pred if n_pred else float("nan"), "R_mem": c / n_true if n_true else float("nan")}
