import cdlib  # nạp libgomp của hệ thống trước
import numpy as np
from scipy.optimize import linear_sum_assignment

from metrics.scoring import score
from cdlib import evaluation, NodeClustering


def match(cover, gt, restricted=None):
    a = [set(c) if restricted is None else set(c) & restricted for c in cover]
    b = [set(c) if restricted is None else set(c) & restricted for c in gt]
    matrix = np.array([[2*len(c & d)/max(len(c)+len(d), 1) for d in b] for c in a])
    if not a or not b:
        return {}, np.zeros((len(a), len(b)))
    rows, cols = linear_sum_assignment(-matrix)
    return {int(i): int(j) for i, j in zip(rows, cols) if matrix[i, j] > 0}, matrix


def membership_map(nodes, cover):
    mapping = {u: set() for u in nodes}
    for i, community in enumerate(cover):
        for u in community:
            if u in mapping:
                mapping[u].add(i)
    return mapping


def node_metrics(graph, cover, gt):
    nodes = sorted(graph)
    pred = membership_map(nodes, cover)
    true = membership_map(nodes, gt)
    alignment, _ = match(cover, gt)
    records = []
    tp = fp = fn = 0
    for u in nodes:
        p, t = len(pred[u]) > 1, len(true[u]) > 1
        tp += int(p and t)
        fp += int(p and not t)
        fn += int(t and not p)
        recovered = {alignment.get(i, -1-i) for i in pred[u]}
        correct = len(recovered & true[u])
        precision = correct/max(len(recovered), 1)
        recall = correct/max(len(true[u]), 1)
        records.append({'node': u, 'degree': graph.degree(u), 'strength': graph.degree(u, weight='weight'),
                        'true_memberships': len(true[u]), 'predicted_memberships': len(pred[u]),
                        'membership_precision': precision, 'membership_recall': recall,
                        'membership_f1': 2*correct/max(len(recovered)+len(true[u]), 1),
                        'mean_true_community_size': np.mean([len(gt[i]) for i in true[u]]) if true[u] else 0,
                        'homeless': int(not pred[u])})
    precision, recall = tp/max(tp+fp, 1), tp/max(tp+fn, 1)
    return {'overlap_precision': precision, 'overlap_recall': recall,
            'overlap_f1': 2*tp/max(2*tp+fp+fn, 1), 'overlap_tp': tp, 'overlap_fp': fp, 'overlap_fn': fn,
            'membership_count_mae': float(np.mean([abs(len(pred[u])-len(true[u])) for u in nodes])),
            'homeless_count': sum(not pred[u] for u in nodes),
            'predicted_memberships_all_nodes': sum(map(len, pred.values()))/max(len(nodes), 1)}, records
