# F1 hai phía theo Yang và Leskovec.

from __future__ import annotations


import numpy as np


def f1_matrix(pred, gt):
    a = [set(c) for c in pred]
    b = [set(c) for c in gt]
    m = np.zeros((len(a), len(b)))
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            inter = len(x & y)
            if inter:
                m[i, j] = 2.0 * inter / (len(x) + len(y))
    return m


def yl_scores(pred, gt):
    m = f1_matrix(pred, gt)
    if m.size == 0:
        return {"f1_gt": 0.0, "f1_pred": 0.0, "f1_yl": 0.0}
    f1_gt = float(m.max(axis=0).mean())
    f1_pred = float(m.max(axis=1).mean())
    return {"f1_gt": f1_gt, "f1_pred": f1_pred, "f1_yl": 0.5 * (f1_gt + f1_pred)}
