"""Độ đo cho phức hợp protein theo Nepusz, Yu và Paccanaro (2012, Online Methods): MMR chia cho số phức hợp chuẩn,
Frac là tỉ lệ phức hợp chuẩn có một cụm dự đoán với ω > 0,25; Sn, PPV (mẫu số là tổng biên của bảng tiếp liên), Acc theo Brohée và van Helden (2006)."""
from __future__ import annotations

import math

import numpy as np

MIN_PRED = 3
FRAC_THRESHOLD = 0.25


def overlap_score(a, b):
    i = len(a & b)
    return i * i / (len(a) * len(b))


def restrict(cover, reference):
    """Chiếu phủ dự đoán lên tập protein có nhãn, bỏ cụm còn dưới MIN_PRED protein."""
    labeled = set().union(*reference)
    return [c for c in (set(c) & labeled for c in cover) if len(c) >= MIN_PRED]


def complex_scores(pred, reference):
    from scipy.optimize import linear_sum_assignment
    ref = [set(r) for r in reference]
    out = {"n_pred": len(pred), "n_ref": len(ref)}
    if not pred:
        return dict(out, mmr=0.0, sn=0.0, ppv=0.0, acc=0.0, frac=0.0)
    W = np.array([[overlap_score(r, p) for p in pred] for r in ref])
    rows, cols = linear_sum_assignment(-W)
    T = np.array([[len(r & p) for p in pred] for r in ref], dtype=float)
    sn = T.max(axis=1).sum() / sum(len(r) for r in ref)
    ppv = T.max(axis=0).sum() / T.sum() if T.sum() > 0 else 0.0
    return dict(out, mmr=float(W[rows, cols].sum() / len(ref)), sn=float(sn), ppv=float(ppv),
                acc=math.sqrt(sn * ppv), frac=float((W.max(axis=1) > FRAC_THRESHOLD).mean()))
