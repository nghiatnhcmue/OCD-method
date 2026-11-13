import networkx as nx
import matplotlib.pyplot as plt
import scipy.sparse
import pandas as pd
import numpy as np
import os
import scipy.cluster.hierarchy
import scipy.spatial.distance
import cdlib
import cdlib.algorithms

from wghac import functions


def _community_count_bounds(
        ground_truth_communities,
        use_ground_truth_count_window: bool = False,
) -> tuple[int, int]:
    if use_ground_truth_count_window and ground_truth_communities is not None:
        return (
            max(1, len(ground_truth_communities) // 2),
            max(2, len(ground_truth_communities) * 2),
        )
    return 2, 100


def evaluate_hierarchy(
    graph: nx.Graph,
    linkage_matrix: np.ndarray,
    bases: list,
    weight_param: str = None,
    min_distance_in_modularity_calculation: float = 0.000,
    xlim: tuple[int, int] = None,
    figsize: tuple[int, int] = (12, 12),
    ground_truth_communities: list | None = None,
    plot_dendrograms: bool = True,
    ct_distance_matrix: np.ndarray = None,
    compute_silhouette: bool = True,
    max_eval_levels: int | None = None,
    use_ground_truth_count_window: bool = False,
    min_community_size: int = 5,
):
    dendrogram_modularity_info = dict()
    levels_for_calculation = list()
    linkage_matrix_for_eval = linkage_matrix.copy()
    distance_vector = linkage_matrix_for_eval[:, 2].copy()
    linkage_matrix_for_eval[:, 2] = range(1, linkage_matrix_for_eval.shape[0] + 1)

    for level in np.unique(linkage_matrix_for_eval[:, 2]):
        if distance_vector[int(level - 1)] < min_distance_in_modularity_calculation or distance_vector[int(level - 1)] < 0:
            continue
        levels_for_calculation.append(level)

    total_eval_levels = len(levels_for_calculation)

    communities_count_hint_min, communities_count_hint_max = (
        _community_count_bounds(
            ground_truth_communities,
            use_ground_truth_count_window=use_ground_truth_count_window,
        )
    )

    eligible_levels = []
    for level in levels_for_calculation:
        clustering = scipy.cluster.hierarchy.fcluster(
            linkage_matrix_for_eval,
            t=level,
            criterion='distance',
        )
        comm_list = functions.get_clustering_comm_list(clustering, bases)
        raw_communities = functions.merge_bases_into_nodes(comm_list)
        raw_communities = functions.drop_small_communities(raw_communities, min_size=min_community_size)
        if len(raw_communities) > communities_count_hint_max or len(raw_communities) < communities_count_hint_min:
            continue
        eligible_levels.append((level, raw_communities))

    eligible_eval_levels = len(eligible_levels)
    _auto_limit = 200
    if max_eval_levels is None and eligible_eval_levels > _auto_limit:
        max_eval_levels = _auto_limit
    if max_eval_levels is not None and eligible_eval_levels > max_eval_levels:
        selected_indices = np.linspace(
            0,
            eligible_eval_levels - 1,
            num=max_eval_levels,
            dtype=int,
        )
        eligible_levels = [
            eligible_levels[idx] for idx in np.unique(selected_indices)
        ]

    for level, raw_communities in eligible_levels:
        distance = distance_vector[int(level - 1)]
        full_cover_communities = functions.postprocess_for_full_cover(raw_communities, graph.nodes(), graph)

        cd_evaluation = functions.get_overlapping_evaluation_dict(
            graph,
            raw_communities,
            weight_param,
            ground_truth_communities,
            full_cover_communities=full_cover_communities,
        )
        cd_evaluation['distance'] = distance
        cd_evaluation['level'] = int(level)
        cd_evaluation['communities'] = raw_communities
        cd_evaluation['communities_full_cover'] = full_cover_communities
        cd_evaluation['hierarchy_eval_levels_total'] = total_eval_levels
        cd_evaluation['hierarchy_eval_levels_eligible'] = eligible_eval_levels
        cd_evaluation['hierarchy_eval_levels_used'] = len(eligible_levels)
        cd_evaluation['hierarchy_eval_policy'] = (
            'deterministic_even_grid'
            if len(eligible_levels) < eligible_eval_levels
            else 'all_eligible_levels'
        )

        metric_status = cd_evaluation.setdefault('metric_status', {})
        metric_status['candidate_level_count_policy'] = (
            'ground_truth_oracle_window'
            if use_ground_truth_count_window
            else 'fixed_unsupervised_2_100'
        )

        if ct_distance_matrix is None or len(full_cover_communities) == 0:
            cd_evaluation['max_ct_diameter'] = np.nan
            cd_evaluation['next_linkage_distance'] = np.nan
            cd_evaluation['dunn_index'] = np.nan
            metric_status['max_ct_diameter'] = 'not_applicable:no_ct_distance_matrix'
            metric_status['next_linkage_distance'] = 'not_applicable:no_ct_distance_matrix'
            metric_status['dunn_index'] = 'not_applicable:no_ct_distance_matrix'
        else:
            try:
                max_ct_diameter = max(functions.get_communities_ct_diameter(full_cover_communities, ct_distance_matrix))
                cd_evaluation['max_ct_diameter'] = max_ct_diameter
                metric_status['max_ct_diameter'] = 'ok'
            except Exception as exc:
                cd_evaluation['max_ct_diameter'] = np.nan
                metric_status['max_ct_diameter'] = f'error:{type(exc).__name__}:{exc}'
                max_ct_diameter = np.nan

            next_linkage_distance = np.nan
            for i in range(int(level), len(distance_vector)):
                if distance_vector[i] > 0:
                    next_linkage_distance = distance_vector[i]
                    break
            cd_evaluation['next_linkage_distance'] = next_linkage_distance
            metric_status['next_linkage_distance'] = 'ok' if not np.isnan(next_linkage_distance) else 'not_applicable:no_next_linkage_distance'

            if np.isnan(max_ct_diameter) or max_ct_diameter <= 0 or np.isnan(next_linkage_distance):
                cd_evaluation['dunn_index'] = np.nan
                metric_status['dunn_index'] = 'not_applicable:invalid_diameter_or_linkage_distance'
            else:
                cd_evaluation['dunn_index'] = next_linkage_distance / max_ct_diameter
                metric_status['dunn_index'] = 'ok'

        if not compute_silhouette:
            cd_evaluation['silhouette'] = np.nan
            cd_evaluation['silhouette_maxsi'] = np.nan
            metric_status['silhouette'] = 'disabled'
            metric_status['silhouette_maxsi'] = 'disabled'
        elif ct_distance_matrix is None or len(full_cover_communities) == 0:
            cd_evaluation['silhouette'] = np.nan
            cd_evaluation['silhouette_maxsi'] = np.nan
            metric_status['silhouette'] = 'not_applicable:no_ct_distance_matrix'
            metric_status['silhouette_maxsi'] = 'not_applicable:no_ct_distance_matrix'
        else:
            try:
                mean_silhouette_scores, max_silhouette_scores = functions.silhouette_score_for_overlapping_communities(
                    full_cover_communities,
                    ct_distance_matrix,
                )
                cd_evaluation['silhouette'] = mean_silhouette_scores
                cd_evaluation['silhouette_maxsi'] = max_silhouette_scores
                metric_status['silhouette'] = 'ok' if not np.isnan(mean_silhouette_scores) else 'not_applicable:no_silhouette_values'
                metric_status['silhouette_maxsi'] = 'ok' if not np.isnan(max_silhouette_scores) else 'not_applicable:no_silhouette_values'
            except Exception as exc:
                cd_evaluation['silhouette'] = np.nan
                cd_evaluation['silhouette_maxsi'] = np.nan
                metric_status['silhouette'] = f'error:{type(exc).__name__}:{exc}'
                metric_status['silhouette_maxsi'] = f'error:{type(exc).__name__}:{exc}'

        dendrogram_modularity_info[level] = cd_evaluation

    if len(dendrogram_modularity_info) == 0:
        return None

    df = pd.DataFrame(dendrogram_modularity_info).T.reset_index(drop=True)

    if plot_dendrograms:
        best_step = max(
            dendrogram_modularity_info,
            key=lambda k: dendrogram_modularity_info[k].get('modularity_eq', float('-inf')),
        )
        plot_hierarchy_quality(
            df,
            linkage_matrix_for_eval,
            bases,
            graph,
            save_path='output_dendrogram.png',
            highlight_steps=[best_step],
            title='Network covers internal quality evaluation',
        )

    return df


_PLOT_METRICS = [
    ('silhouette',           'SI',      'max'),
    ('modularity_overlap',   'Mᵒᵛ',    'max'),
    ('conductance_weighted', 'Condᵥᵥ', 'min'),
    ('modularity_eq',        'Mᵉ',     'max'),
    ('dunn_index',           'DI',      'max'),
    ('overlap_silhouette',   'OSI',     'max'),
]

_METRIC_LABEL = {m: lbl for m, lbl, _ in _PLOT_METRICS}
_METRIC_DIR   = {m: d   for m, _, d in _PLOT_METRICS}


def plot_hierarchy_quality(
    df_results: pd.DataFrame,
    linkage_matrix_step: np.ndarray,
    bases: list,
    graph: 'nx.Graph | None' = None,
    save_path: str = 'output_dendrogram.png',
    highlight_steps: 'list[float] | None' = None,
    metrics: 'list[str] | None' = None,
    title: str = 'Network covers internal quality evaluation',
    figsize: 'tuple | None' = None,
):
    if metrics is None:
        metrics = [m for m, _, _ in _PLOT_METRICS if m in df_results.columns]

    n_metrics  = len(metrics)
    n_bases    = len(bases)
    dend_rows  = max(6, min(20, n_bases // 30))
    h_ratios   = [1] * n_metrics + [dend_rows]
    fig_h      = n_metrics * 1.4 + dend_rows * 0.5
    fig_w      = figsize[0] if figsize else 14
    fig_h      = figsize[1] if figsize else fig_h

    fig, axs = plt.subplots(
        n_metrics + 1, 1, sharex=True,
        figsize=(fig_w, fig_h),
        gridspec_kw={'height_ratios': h_ratios},
    )
    if n_metrics + 1 == 1:
        axs = [axs]

    steps = df_results['level'].tolist() if 'level' in df_results.columns else list(range(len(df_results)))

    for i, metric in enumerate(metrics):
        ax = axs[i]
        vals = pd.to_numeric(df_results[metric], errors='coerce').tolist() if metric in df_results.columns else [float('nan')] * len(steps)
        ax.plot(steps, vals, 'x-', markersize=3, linewidth=0.8, color='steelblue')
        ax.set_ylabel(_METRIC_LABEL.get(metric, metric), fontsize=8, labelpad=2)
        ax.yaxis.set_major_formatter(plt.FormatStrFormatter('%.3f'))
        ax.tick_params(labelsize=7)
        ax.grid(True, axis='both', alpha=0.3)
        if highlight_steps:
            for s in highlight_steps:
                ax.axvline(x=s, color='red', linestyle='--', linewidth=1.0, alpha=0.85)

    ax_dend = axs[-1]

    color_thresh = 0.5
    if highlight_steps:
        color_thresh = float(highlight_steps[0]) + 0.001

    show_labels = n_bases <= 150
    truncate = n_bases > 500
    node_labels = None
    if show_labels:
        labels_map = nx.get_node_attributes(graph, 'original_label') if graph is not None else {}
        if labels_map:
            node_labels = [
                ', '.join(sorted(str(labels_map.get(n, n)) for n in b))
                for b in bases
            ]
        else:
            node_labels = [str(i) for i in range(n_bases)]

    dend_kwargs = dict(
        orientation='right',
        ax=ax_dend,
        color_threshold=color_thresh,
        no_labels=(not show_labels),
        leaf_font_size=6 if show_labels else None,
    )
    if not truncate:
        dend_kwargs['labels'] = node_labels
    else:
        dend_kwargs['truncate_mode'] = 'lastp'
        dend_kwargs['p'] = 60

    scipy.cluster.hierarchy.dendrogram(linkage_matrix_step, **dend_kwargs)
    ax_dend.set_title('Dendrogram', fontsize=9)
    ax_dend.grid(True, axis='x', alpha=0.3)
    ax_dend.tick_params(axis='x', labelsize=7)
    if highlight_steps:
        for s in highlight_steps:
            ax_dend.axvline(x=s, color='red', linestyle='--', linewidth=1.0, alpha=0.85)

    axs[-1].set_xlabel('Agglomeration step', fontsize=8)

    if title:
        fig.suptitle(title, fontsize=10, y=1.002)

    plt.tight_layout()

    os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
    plt.savefig(save_path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    print(f'Dendrogram saved: {save_path}')
