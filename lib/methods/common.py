from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx


def largest_2ec_core(graph: nx.Graph) -> tuple[nx.Graph, list]:
    core = graph.copy()
    while True:
        if core.number_of_nodes() == 0:
            break
        bridges = list(nx.bridges(core))
        if not bridges:
            break
        core.remove_edges_from(bridges)
        components = list(nx.connected_components(core))
        giant = max(components, key=len)
        core = core.subgraph(giant).copy()
    removed = [n for n in graph.nodes() if n not in core]
    return core, removed


def reattach_removed(cover: list[set], removed: list,
                     graph: nx.Graph) -> list[set]:
    cover = [set(c) for c in cover]
    for node in removed:
        best, best_weight = None, 0.0
        for idx, community in enumerate(cover):
            weight = sum(
                float(graph[node][nbr].get("weight", 1.0))
                for nbr in graph.neighbors(node) if nbr in community)
            if weight > best_weight:
                best, best_weight = idx, weight
        if best is not None:
            cover[best].add(node)
        elif cover:
            for nbr in graph.neighbors(node):
                homes = [i for i, c in enumerate(cover) if nbr in c]
                if homes:
                    cover[homes[0]].add(node)
                    break
    return cover


@dataclass
class TreeNode:
    members: set
    h_birth: float
    h_death: float | None = None
    children: list = field(default_factory=list)


@dataclass
class Dendrogram:
    leaves: list
    merges: list = field(default_factory=list)

    def tree_nodes(self, root_death_factor: float = 1.05, monotone: bool = False) -> list[TreeNode]:
        nodes = [TreeNode(set(leaf), 0.0) for leaf in self.leaves]
        for left, right, height in self.merges:
            # bao đơn điệu: H(cha) = max(d, H(con trái), H(con phải)), H(lá) = 0
            if monotone:
                height = max(height, nodes[left].h_birth, nodes[right].h_birth)
            nodes[left].h_death = height
            nodes[right].h_death = height
            parent = TreeNode(
                nodes[left].members | nodes[right].members, height)
            parent.children = [left, right]
            nodes.append(parent)
        max_height = max((h for _, _, h in self.merges), default=1.0)
        for node in nodes:
            if node.h_death is None:
                node.h_death = root_death_factor * max_height
        return nodes
