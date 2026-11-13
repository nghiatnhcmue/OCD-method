import itertools
import numpy as np
import networkx as nx
import cdlib
from wghac import cdlib_quality_measures_weighted

import nf1.NF1_class as _nf1_mod
import scipy.stats


# nf1 gọi scipy.stats.mode(...)[0][0], lỗi với scipy >= 1.11
def _patched_get_f1(self):
    f1_list = np.array(self._NF1__communities_f1())
    mode_result = scipy.stats.mode(f1_list)
    mode_val = mode_result[0]
    if hasattr(mode_val, '__len__'):
        mode_val = mode_val[0]
    return (
        np.mean(f1_list),
        np.std(f1_list),
        np.max(f1_list),
        np.min(f1_list),
        mode_val,
    )


_nf1_mod.NF1.get_f1 = _patched_get_f1


def merge_bases_into_nodes(communities_list):
    merged_communities = []
    seen = set()
    for community_containing_base in communities_list:
        merged_nodes = set()
        for base in community_containing_base:
            merged_nodes |= set(base)
        if len(merged_nodes) <= 1:
            continue
        key = tuple(sorted(merged_nodes))
        if key in seen:
            continue
        seen.add(key)
        merged_communities.append(set(key))
    return merged_communities


def get_clustering_comm_list(clustering_result, nodelist_labels):
    comm_list = list()
    for i in range(max(clustering_result) + 1):
        comm_list.append(list())
    for node_id, cluster_id in zip(nodelist_labels, clustering_result):
        comm_list[cluster_id].append(node_id)
    return [com for com in comm_list if len(com) > 0]


def modularity_eq(graph, communities, weight=None):
    q = 0.0
    degrees = dict(graph.degree(weight=weight))
    O = np.zeros((graph.number_of_nodes(), len(communities)))

    for k, nds in enumerate(communities):
        O[[int(n) for n in nds], k] = 1
    O = O.sum(1, keepdims=True)
    m = np.sum([v for k, v in degrees.items()]) / 2
    for community_nodes in communities:
        for nd1, nd2 in itertools.combinations(community_nodes, 2):
            if nd1 == nd2:
                continue
            if graph.has_edge(nd1, nd2):
                e = graph[nd1][nd2]
                wt = e[weight] if weight is not None else 1
            else:
                wt = 0
            q += (
                (wt - degrees[nd1] * degrees[nd2] / (2 * m))
                * (1 / (O[int(nd1), 0] * O[int(nd2), 0]))
            )
    return q / (2 * m)


def get_overlapping_ratio_coef(graph_relabeled, comm_list):
    return sum([len(x) for x in comm_list]) / nx.number_of_nodes(graph_relabeled)


def calculate_weighted_conductance(G, communities_list, weight_param):
    if not isinstance(G, nx.Graph):
        raise ValueError('G must be a networkx Graph.')
    if not isinstance(communities_list, list) or not all(isinstance(c, set) for c in communities_list):
        raise ValueError('communities_list must be a list of sets of nodes.')

    conductance_list = []
    for community in communities_list:
        intra_community_weight = sum(G[u][v][weight_param] for u, v in G.subgraph(community).edges())
        inter_community_weight = sum(
            G[u][v][weight_param]
            for u in community
            for v in G.neighbors(u)
            if v not in community
        )

        try:
            weighted_conductance = inter_community_weight / (2 * intra_community_weight + inter_community_weight)
            conductance_list.append(weighted_conductance)
        except Exception:
            conductance_list.append(0)

    return np.mean(conductance_list)


def _communities_to_object(communities):
    if hasattr(communities, 'communities'):
        return communities
    return type('obj', (object,), {'communities': communities})


def _set_metric_error(results, metric_status, metric_name, exc):
    results[metric_name] = np.nan
    metric_status[metric_name] = f'error:{type(exc).__name__}:{exc}'


def _set_metric_not_applicable(results, metric_status, metric_name, reason):
    results[metric_name] = np.nan
    metric_status[metric_name] = f'not_applicable:{reason}'


def _safe_metric(results, metric_status, metric_name, metric_fn):
    try:
        value = metric_fn()
        if hasattr(value, 'score'):
            value = value.score
        results[metric_name] = value
        metric_status[metric_name] = 'ok'
    except Exception as exc:
        _set_metric_error(results, metric_status, metric_name, exc)


def _nf1_score_compat(partition_obj, gt_obj):
    summary = _nf1_mod.NF1(partition_obj.communities, gt_obj.communities).summary()
    return float(summary["scores"].loc["NF1"].iloc[0])


def _nf1_with_full_cover_fallback(raw_obj, full_cover_obj, gt_obj, gt_full_cover_obj):
    try:
        return _nf1_score_compat(raw_obj, gt_obj)
    except (KeyError, IndexError):
        return _nf1_score_compat(full_cover_obj, gt_full_cover_obj)


def cdlib_communities_quality_check(graph, communities, weight_param, metric_status=None):
    communities_cdlib_object = _communities_to_object(communities)
    evaluation_dict = dict()
    metric_status = metric_status if metric_status is not None else {}

    metric_specs = [
        ('conductance', lambda: cdlib.evaluation.conductance(graph, communities_cdlib_object)),
        ('expansion', lambda: cdlib.evaluation.expansion(graph, communities_cdlib_object)),
        ('internal_edge_density', lambda: cdlib.evaluation.internal_edge_density(graph, communities_cdlib_object)),
        ('cut_ratio', lambda: cdlib.evaluation.cut_ratio(graph, communities_cdlib_object)),
        ('normalized_cut', lambda: cdlib.evaluation.normalized_cut(graph, communities_cdlib_object)),
        ('flake_odf', lambda: cdlib.evaluation.flake_odf(graph, communities_cdlib_object)),
        ('avg_odf', lambda: cdlib.evaluation.avg_odf(graph, communities_cdlib_object)),
        ('scaled_density', lambda: cdlib.evaluation.scaled_density(graph, communities_cdlib_object)),
        ('avg_transitivity', lambda: cdlib.evaluation.avg_transitivity(graph, communities_cdlib_object)),
        ('expansion_uniform', lambda: cdlib_quality_measures_weighted.expansion(graph, communities_cdlib_object, weight='weight_uniform')),
        ('internal_edge_density_uniform', lambda: cdlib_quality_measures_weighted.internal_edge_density(graph, communities_cdlib_object, weight='weight_uniform')),
        ('cut_ratio_uniform', lambda: cdlib_quality_measures_weighted.cut_ratio(graph, communities_cdlib_object, weight='weight_uniform')),
        ('normalized_cut_uniform', lambda: cdlib_quality_measures_weighted.normalized_cut(graph, communities_cdlib_object, weight='weight_uniform')),
        ('flake_odf_uniform', lambda: cdlib_quality_measures_weighted.flake_odf(graph, communities_cdlib_object, weight='weight_uniform')),
        ('avg_odf_uniform', lambda: cdlib_quality_measures_weighted.avg_odf(graph, communities_cdlib_object, weight='weight_uniform')),
        ('expansion_weight', lambda: cdlib_quality_measures_weighted.expansion(graph, communities_cdlib_object, weight=weight_param)),
        ('internal_edge_density_weight', lambda: cdlib_quality_measures_weighted.internal_edge_density(graph, communities_cdlib_object, weight=weight_param)),
        ('cut_ratio_weight', lambda: cdlib_quality_measures_weighted.cut_ratio(graph, communities_cdlib_object, weight=weight_param)),
        ('normalized_cut_weight', lambda: cdlib_quality_measures_weighted.normalized_cut(graph, communities_cdlib_object, weight=weight_param)),
        ('flake_odf_weight', lambda: cdlib_quality_measures_weighted.flake_odf(graph, communities_cdlib_object, weight=weight_param)),
        ('avg_odf_weight', lambda: cdlib_quality_measures_weighted.avg_odf(graph, communities_cdlib_object, weight=weight_param)),
    ]

    for metric_name, metric_fn in metric_specs:
        _safe_metric(evaluation_dict, metric_status, metric_name, metric_fn)

    return evaluation_dict


def get_overlapping_evaluation_dict(
        graph,
        communities,
        weight_param,
        gt_communities=None,
        full_cover_communities=None,
        use_full_cover_for_metrics: bool = True,
):
    results = dict()
    metric_status = dict()
    raw_communities = [set(comm) for comm in communities]
    if full_cover_communities is None:
        full_cover_communities = get_full_cover_for_communities(raw_communities, graph.nodes())
    else:
        full_cover_communities = [set(comm) for comm in full_cover_communities]

    metric_communities = (
        full_cover_communities
        if use_full_cover_for_metrics
        else raw_communities
    )
    cdlib_communitites_obj = _communities_to_object(metric_communities)
    cdlib_communitites_complete_obj = _communities_to_object(full_cover_communities)

    results['comms_len'] = len(raw_communities)
    results['comms_len_full_cover'] = len(full_cover_communities)
    results['metric_status'] = metric_status
    metric_status['evaluation_cover_policy'] = (
        'full_cover' if use_full_cover_for_metrics else 'raw_cover'
    )

    if metric_communities:
        results['ratio_overlapping'] = get_overlapping_ratio_coef(
            graph, metric_communities)
        metric_status['ratio_overlapping'] = 'ok'
    else:
        _set_metric_not_applicable(results, metric_status, 'ratio_overlapping', 'no_communities')

    _safe_metric(results, metric_status, 'modularity_eq', lambda: modularity_eq(graph, metric_communities, weight=weight_param))
    _safe_metric(results, metric_status, 'modularity_eq_uniform', lambda: modularity_eq(graph, metric_communities, weight='weight_uniform'))
    _safe_metric(results, metric_status, 'conductance_weighted', lambda: calculate_weighted_conductance(graph, full_cover_communities, weight_param))
    _safe_metric(results, metric_status, 'conductance_weighted_uniform', lambda: calculate_weighted_conductance(graph, full_cover_communities, 'weight_uniform'))
    _safe_metric(results, metric_status, 'modularity_overlap', lambda: cdlib.evaluation.modularity_overlap(graph, cdlib_communitites_obj, weight_param))
    _safe_metric(results, metric_status, 'modularity_overlap_uniform', lambda: cdlib.evaluation.modularity_overlap(graph, cdlib_communitites_obj, 'weight_uniform'))

    if gt_communities is not None:
        gt_communities_obj = _communities_to_object(list(gt_communities))
        gt_full_cover_obj = _communities_to_object(
            get_full_cover_for_communities(list(gt_communities), graph.nodes()))
        _safe_metric(results, metric_status, 'onmi_1', lambda: cdlib.evaluation.overlapping_normalized_mutual_information_LFK(cdlib_communitites_obj, gt_communities_obj))
        _safe_metric(results, metric_status, 'onmi_2', lambda: cdlib.evaluation.overlapping_normalized_mutual_information_MGH(cdlib_communitites_obj, gt_communities_obj))
        _safe_metric(results, metric_status, 'f1', lambda: cdlib.evaluation.f1(cdlib_communitites_obj, gt_communities_obj))
        _safe_metric(
            results, metric_status, 'nf1',
            lambda: _nf1_with_full_cover_fallback(
                cdlib_communitites_obj, cdlib_communitites_complete_obj,
                gt_communities_obj, gt_full_cover_obj))
        _safe_metric(results, metric_status, 'omega', lambda: cdlib.evaluation.omega(cdlib_communitites_complete_obj, gt_full_cover_obj))

        on_ratio, om_ratio, f1_nodes = calculate_overlapping_quality(
            graph, metric_communities, gt_communities)
        if np.isnan(on_ratio):
            for metric_name in ['on_ratio', 'om_ratio', 'on_ratio_1_diff', 'om_ratio_1_diff', 'f1_nodes']:
                _set_metric_not_applicable(results, metric_status, metric_name, 'ground_truth_has_no_overlap')
        else:
            results['on_ratio'] = on_ratio
            results['om_ratio'] = om_ratio
            results['on_ratio_1_diff'] = np.abs(1 - on_ratio)
            results['om_ratio_1_diff'] = np.abs(1 - om_ratio)
            results['f1_nodes'] = f1_nodes
            for metric_name in ['on_ratio', 'om_ratio', 'on_ratio_1_diff', 'om_ratio_1_diff']:
                metric_status[metric_name] = 'ok'
            if f1_nodes == 0 and on_ratio == 0:
                metric_status['f1_nodes'] = 'valid_zero:no_detected_overlap_nodes'
            elif f1_nodes == 0:
                metric_status['f1_nodes'] = 'valid_zero:no_true_positive_overlap_nodes'
            else:
                metric_status['f1_nodes'] = 'ok'
    else:
        for metric_name in ['onmi_1', 'onmi_2', 'f1', 'nf1', 'omega', 'on_ratio', 'om_ratio', 'on_ratio_1_diff', 'om_ratio_1_diff', 'f1_nodes']:
            _set_metric_not_applicable(results, metric_status, metric_name, 'no_ground_truth')

    cdlib_results_dict = cdlib_communities_quality_check(
        graph, metric_communities, weight_param, metric_status)
    results.update(cdlib_results_dict)

    return results


def calculate_overlapping_quality(graph, communities, gt_communities):
    nodes = list(graph.nodes())
    detected_node_assigment_counts = {node: 0 for node in nodes}
    gt_node_assigment_counts = {node: 0 for node in nodes}
    for comm in communities:
        for node in comm:
            if node in detected_node_assigment_counts:
                detected_node_assigment_counts[node] += 1
    for comm in gt_communities:
        for node in comm:
            if node in gt_node_assigment_counts:
                gt_node_assigment_counts[node] += 1

    detected_counts = np.array(list(detected_node_assigment_counts.values()), dtype=np.float64)
    gt_counts = np.array(list(gt_node_assigment_counts.values()), dtype=np.float64)

    gt_overlap_nodes = np.sum(gt_counts > 1)
    if gt_overlap_nodes == 0:
        return np.nan, np.nan, np.nan

    detected_overlap_nodes = np.sum(detected_counts > 1)
    on_ratio = detected_overlap_nodes / gt_overlap_nodes
    gt_mean_assignment = np.mean(gt_counts)
    om_ratio = np.mean(detected_counts) / gt_mean_assignment if gt_mean_assignment > 0 else np.nan
    tp = np.sum((detected_counts > 1) & (gt_counts > 1))
    if tp == 0:
        f1 = 0
    else:
        precision = tp / detected_overlap_nodes
        recall = tp / gt_overlap_nodes
        f1 = 2 * (precision * recall) / (precision + recall)
    return on_ratio, om_ratio, f1


def drop_small_communities(communities: list, min_size=3):
    filtered_communities = list()
    for community in communities:
        if len(community) >= min_size:
            filtered_communities.append(set(community))
    return filtered_communities


def get_full_cover_for_communities(communities: list, nodes: list):
    communities_copy = [set(community) for community in communities]
    nodes_set = set(nodes)
    for community in communities_copy:
        for node in community:
            if node in nodes_set:
                nodes_set.remove(node)
    for node in nodes_set:
        communities_copy.append(set([node]))
    return communities_copy


def postprocess_for_full_cover(communities: list, nodes: list, graph: nx.Graph):
    communities_copy = [set(community) for community in communities]
    nodes_set = set(nodes)
    for community in communities_copy:
        for node in community:
            if node in nodes_set:
                nodes_set.remove(node)
    missing_node_community_assigment = dict()
    for node in nodes_set:
        neighbours = set(graph.neighbors(node))
        neighbours_communities = [len(comm & neighbours) for comm in communities_copy]
        if any([c > 1 for c in neighbours_communities]):
            comm_id_max = np.argmax(neighbours_communities)
            missing_node_community_assigment[node] = comm_id_max
        else:
            missing_node_community_assigment[node] = -1
    for node in nodes_set:
        if missing_node_community_assigment[node] != -1:
            communities_copy[missing_node_community_assigment[node]].add(node)
        else:
            communities_copy.append(set([node]))
    return communities_copy


def get_communities_ct_diameter(communities, ct_distance_matrix):
    communities_diameter = list()
    for community in communities:
        communities_diameter.append(np.max(ct_distance_matrix[np.ix_(list(community), list(community))]))
    return communities_diameter


def silhouette_score_for_overlapping_communities(communities, ct_distance_matrix):
    if ct_distance_matrix is None or len(communities) == 0:
        return np.nan, np.nan

    normalized_communities = [sorted(set(community)) for community in communities if len(community) > 0]
    if not normalized_communities:
        return np.nan, np.nan

    node_communities_belonging = dict()
    node_silhouette_scores = dict()
    mean_distances = []

    for i, community in enumerate(normalized_communities):
        for node in community:
            if node not in node_communities_belonging:
                node_communities_belonging[node] = []
            node_communities_belonging[node].append(i)

    for community in normalized_communities:
        mean_distances.append(np.mean(ct_distance_matrix[:, community], axis=1))

    for node, communities_belonging in node_communities_belonging.items():
        node_silhouette_scores[node] = []
        outer_candidates = [
            mean_distances[e][node]
            for e, outer_community in enumerate(normalized_communities)
            if e not in communities_belonging and len(outer_community) > 0
        ]
        b = np.min(outer_candidates) if outer_candidates else 0.0

        for community_belonging in communities_belonging:
            community_nodes = normalized_communities[community_belonging]
            if len(community_nodes) == 1:
                node_silhouette_scores[node].append(0.0)
                continue

            a = np.sum(ct_distance_matrix[node, community_nodes]) / max(len(community_nodes) - 1, 1)
            denominator = max(a, b)
            s = 0.0 if denominator <= 0 else (b - a) / denominator
            node_silhouette_scores[node].append(s)

    mean_silhouette_scores = np.mean([np.mean(v) for v in node_silhouette_scores.values()]) if node_silhouette_scores else np.nan
    max_silhouette_scores = np.mean([np.max(v) for v in node_silhouette_scores.values()]) if node_silhouette_scores else np.nan
    return mean_silhouette_scores, max_silhouette_scores


def estimate_structural_community_count(graph_gcc: nx.Graph) -> int:
    counts = []
    for resolution in (3.0, 3.5, 4.0):
        try:
            comms = nx.algorithms.community.greedy_modularity_communities(
                graph_gcc,
                weight='weight_normalized',
                resolution=resolution,
            )
        except TypeError:
            comms = nx.algorithms.community.greedy_modularity_communities(
                graph_gcc,
                weight='weight_normalized',
            )
        except Exception:
            continue
        counts.append(len([c for c in comms if len(c) >= 3]))
    if not counts:
        return max(2, int(round(np.sqrt(max(graph_gcc.number_of_nodes(), 1)))))

    avg_clustering = float(nx.average_clustering(graph_gcc))
    transitivity = float(nx.transitivity(graph_gcc))
    boundary_pressure = float(np.clip(
        0.55 * ((0.42 - avg_clustering) / 0.30)
        + 0.45 * ((0.28 - transitivity) / 0.22),
        0.0,
        1.0,
    ))
    base = max(counts)
    expanded = int(round(base * (1.0 + 0.12 * boundary_pressure)))
    return max(2, expanded)
