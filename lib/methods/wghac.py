from __future__ import annotations


import networkx as nx
import numpy as np
from scipy.cluster.hierarchy import fcluster

from wghac import ct_distances, functions
from wghac.graph_hierarchical_agglomerative_clustering import (
    GHACLinkageMethod,
    GraphAgglomerativeClusteringClosedTrail,
)
from wghac.run_ghac_community_detection import evaluate_hierarchy

from methods.common import largest_2ec_core, reattach_removed

_SI_METRIC = "silhouette"


def _prepare(graph: nx.Graph) -> nx.Graph:
    prepared = nx.Graph()
    for u, v, data in graph.edges(data=True):
        weight = float(data.get("weight", data.get("weight_normalized", 1.0)))
        prepared.add_edge(u, v, weight=weight, weight_normalized=weight,
                          cost=1.0 / max(weight, 1e-12))
    return prepared


def run_wghac(graph: nx.Graph, *, linkage: str = "AL",
              min_comm_size: int = 5,
              al_paper_denominator: bool = True,
              temp_prefix: str = "ocd") -> dict:
    prepared = _prepare(graph)
    core, removed = largest_2ec_core(prepared)
    if core.number_of_nodes() < 5:
        return {"cover": [set(graph.nodes())], "status": "degenerate_core"}
    core = nx.convert_node_labels_to_integers(
        core, ordering="sorted", label_attribute="original_label")
    back = {n: core.nodes[n]["original_label"] for n in core.nodes()}

    distance = ct_distances.compute_ct_binary(core, temp_prefix=temp_prefix)
    cliques = [tuple(sorted(c)) for c in nx.find_cliques(core)]
    cliques = sorted(cliques)
    if len(cliques) < 2:
        return {"cover": [set(graph.nodes())], "status": "single_clique"}
    method = (GHACLinkageMethod.AVERAGE if linkage == "AL"
              else GHACLinkageMethod.COMPLETE)
    engine = GraphAgglomerativeClusteringClosedTrail(
        core, method, np.asarray(distance, dtype=np.float64).copy(),
        [list(c) for c in cliques], "weight_normalized",
        al_paper_denominator=al_paper_denominator,
        overlap_reward_mode="paper")
    linkage_matrix = engine.run()
    levels = evaluate_hierarchy(
        core, linkage_matrix, [list(c) for c in cliques],
        weight_param="weight_normalized",
        ground_truth_communities=None,
        ct_distance_matrix=np.asarray(distance),
        plot_dendrograms=False, compute_silhouette=True,
        use_ground_truth_count_window=False)
    if levels is None or levels.empty:
        return {"cover": [set(graph.nodes())], "status": "no_levels"}
    finite = levels[np.isfinite(
        levels[_SI_METRIC].astype(float))]
    if finite.empty:
        return {"cover": [set(graph.nodes())], "status": "no_finite_si"}
    best = finite.loc[finite[_SI_METRIC].astype(float).idxmax()]
    selected_level = int(best["level"])

    matrix = np.asarray(linkage_matrix, dtype=np.float64).copy()
    matrix[:, 2] = np.arange(1, matrix.shape[0] + 1, dtype=np.float64)
    clustering = fcluster(matrix, t=selected_level, criterion="distance")
    comm_list = functions.get_clustering_comm_list(
        clustering, [list(c) for c in cliques])
    raw = functions.merge_bases_into_nodes(comm_list)
    raw = functions.drop_small_communities(raw, min_size=min_comm_size)
    full = functions.postprocess_for_full_cover(raw, core.nodes(), core)
    cover = [{back[n] for n in community} for community in full]
    cover = reattach_removed(cover, removed, prepared)
    return {
        "cover": cover,
        "status": "ok",
        "selected_level": selected_level,
        "si": float(best[_SI_METRIC]),
        "n_cliques": len(cliques),
        "core_nodes": core.number_of_nodes(),
        "removed_nodes": len(removed),
    }
