# Gộp phân cấp theo khoảng cách CT (wGHAC).

import networkx as nx
import numpy as np
import enum
from scipy.sparse import csr_matrix

class GHACLinkageMethod(enum.Enum):
    SINGLE = 1
    COMPLETE = 2
    AVERAGE = 3
    POWER_AVERAGE = 4

class GraphAgglomerativeClusteringClosedTrail():
    def __init__(self, graph: nx.Graph, ct_linkage_method: GHACLinkageMethod, ct_distance_matrix: np.ndarray, bases: list, weight_attribute=None, al_paper_denominator: bool = False,
                 overlap_reward_mode: str = 'paper', overlap_alpha: float = 1.0, overlap_beta: float = 3.0, overlap_lambda: float = 0.65,
                 ppr_mode: bool = False, ppr_gamma: float = 1.0, ppr_alpha: float = 0.15, ppr_eps: float = 1e-4,
                 cpm_mode: bool = False, cpm_gamma: float = 1.0, cpm_gamma_res_mult: float = 1.0,
                 cg_mode: bool = False, cg_gamma: float = 1.0,
                 hrg_mode: bool = False, hrg_gamma: float = 1.0,
                 gcd_mode: bool = False, gcd_gamma: float = 1.0,
                 om_mode: bool = False,
                 mrc_lite_mode: bool = False,
                 wbmf_lite_mode: bool = False,
                 ncbmf_mode: bool = False):
        self.graph = graph
        self.m = nx.number_of_edges(self.graph)
        self.degrees = dict(nx.degree(self.graph))
        self.ct_linkage_method = ct_linkage_method
        self.ct_distance_matrix = ct_distance_matrix
        self.bases = bases
        self.weight_attribute = weight_attribute
        self.al_paper_denominator = al_paper_denominator
        self.overlap_reward_mode = overlap_reward_mode
        self.overlap_alpha = overlap_alpha
        self.overlap_beta = overlap_beta
        self.overlap_lambda = overlap_lambda
        self.ppr_mode = ppr_mode
        self.ppr_gamma = ppr_gamma
        self.ppr_alpha = ppr_alpha
        self.ppr_eps = ppr_eps
        self.cpm_mode = cpm_mode
        self.cpm_gamma = cpm_gamma
        self.cpm_gamma_res_mult = cpm_gamma_res_mult
        self.wt = None
        self._edge_weight = {}
        if weight_attribute is not None:
            self._edge_weight = {
                (min(u, v), max(u, v)): float(w)
                for u, v, w in self.graph.edges(data=weight_attribute)
            }
            self.wt = sum(self._edge_weight.values())
        self._strength = {}
        self._ppr_push_cache = {}
        if ppr_mode:
            self._strength = {
                v: sum(self._edge_weight.get((min(v, u), max(v, u)), 1.0)
                       for u in self.graph.neighbors(v))
                for v in self.graph.nodes()
            }
        self._cpm_gamma_res = 0.0
        if cpm_mode:
            n_nodes = self.graph.number_of_nodes()
            total_w = self.wt if self.wt is not None else self.m
            self._cpm_gamma_res = cpm_gamma_res_mult * (
                2.0 * total_w / (n_nodes * (n_nodes - 1)) if n_nodes > 1 else 0.0
            )
        self.cg_mode = cg_mode
        self.cg_gamma = cg_gamma
        self._cg_node_to_bases = {}
        self._cg_inv_km1 = {}
        if cg_mode:
            for qi, base in enumerate(self.bases):
                for v in base:
                    self._cg_node_to_bases.setdefault(v, []).append(qi)
            self._cg_inv_km1 = {
                v: (1.0 / (len(qs) - 1) if len(qs) > 1 else 0.0)
                for v, qs in self._cg_node_to_bases.items()
            }
            self._cg_base_sets = [set(b) for b in self.bases]
        self.hrg_mode = hrg_mode
        self.hrg_gamma = hrg_gamma
        self.gcd_mode = gcd_mode
        self.gcd_gamma = gcd_gamma
        self._gcd_sig = {}
        if gcd_mode:
            for v in self.graph.nodes():
                neighbors = set(self.graph.neighbors(v))
                deg = len(neighbors)
                tri = 0
                for u in neighbors:
                    tri += len(neighbors & set(self.graph.neighbors(u)))
                tri //= 2
                wedges = deg * (deg - 1) // 2 - tri
                self._gcd_sig[v] = (float(deg), float(tri), float(wedges))
        self.om_mode = om_mode
        self.mrc_lite_mode = mrc_lite_mode
        self._mrc_dmin = 0.0
        self._mrc_dmax = 1.0
        if mrc_lite_mode:
            finite = self.ct_distance_matrix[~np.eye(self.ct_distance_matrix.shape[0], dtype=bool)]
            self._mrc_dmin = float(finite.min())
            self._mrc_dmax = float(finite.max())
        self.wbmf_lite_mode = wbmf_lite_mode
        self._wbmf_K = None
        self._wbmf_r = None
        if wbmf_lite_mode:
            self._wbmf_K, self._wbmf_r = self._wbmf_precompute()
        self.ncbmf_mode = ncbmf_mode
        self._ncbmf_K = None
        self._ncbmf_r = None
        self._ncbmf_pi = None
        if ncbmf_mode:
            self._ncbmf_K, self._ncbmf_r, self._ncbmf_pi = self._ncbmf_precompute()
        self._overlap_denominator_cache = {}
        self._overlap_cache_limit = 50000
        self.reset()
        self.linkage_matrix = None

    def reset(self):
        self.clusters_map_of_sets = dict()
        self.clusters_map_of_edges_sets = dict()
        self.clusters_map_of_leaf_counts = dict()
        for i, base in enumerate(self.bases):
            self.clusters_map_of_sets[i] = set(base)
            self.clusters_map_of_leaf_counts[i] = 1
            graph_overlap = nx.subgraph(self.graph, base)
            self.clusters_map_of_edges_sets[i] = set()
            for u,v in nx.edges(graph_overlap):
                self.clusters_map_of_edges_sets[i].add((min(u,v), max(u,v)))

    def run(self):
        bases_count = len(self.bases)
        print('Start pairwise distance matrix calculation.')
        distance_matrix = self.calculate_pairwise_distance_matrix()
        print('Calculation finished.')
        linkage_matrix = np.empty((bases_count - 1, 4))
        linkage_clusters_reuse_translation = list(range(bases_count))
        np.fill_diagonal(distance_matrix, 999)
        i = 0
        while i < bases_count - 1:
            if i % 100 == 0:
                print('Agglomeration', i, bases_count - 1)
            tmp = np.unravel_index(np.argmin(distance_matrix, axis=None), distance_matrix.shape)
            m1, m2 = tmp

            linkage_matrix[i, 0] = linkage_clusters_reuse_translation[m1]
            linkage_matrix[i, 1] = linkage_clusters_reuse_translation[m2]
            linkage_matrix[i, 2] = distance_matrix[m1, m2]
            linkage_clusters_reuse_translation[m1] = bases_count + i

            self.clusters_map_of_sets[m1] = self.clusters_map_of_sets[m1] | self.clusters_map_of_sets[m2]
            self.clusters_map_of_sets[m2] = None
            self.clusters_map_of_edges_sets[m1] = self.clusters_map_of_edges_sets[m1] | self.clusters_map_of_edges_sets[m2]
            self.clusters_map_of_edges_sets[m2] = None
            linkage_matrix[i, 3] = self._merge_leaf_counts(m1, m2)

            for idx in range(bases_count):
                if self.clusters_map_of_sets[idx] is not None and idx != m1:
                    d = self.calculate_ct_method_between_clusters(self.clusters_map_of_sets[m1], self.clusters_map_of_sets[idx], self.clusters_map_of_edges_sets[m1], self.clusters_map_of_edges_sets[idx])
                    if d>0 and distance_matrix[m1, idx] == 997:
                        continue
                    distance_matrix[m1, idx] = d
                    distance_matrix[idx, m1] = d

            distance_matrix[m2, :] = 999
            distance_matrix[:, m2] = 999
            i += 1
        print('Agglomeration finished.')
        self.linkage_matrix = linkage_matrix
        return self.linkage_matrix

    def _merge_leaf_counts(self, target_idx: int, removed_idx: int) -> int:
        count = (
            self.clusters_map_of_leaf_counts.get(target_idx, 0)
            + self.clusters_map_of_leaf_counts.get(removed_idx, 0)
        )
        self.clusters_map_of_leaf_counts[target_idx] = count
        self.clusters_map_of_leaf_counts[removed_idx] = 0
        return count

    def calculate_pairwise_distance_matrix(self):
        bases_count = len(self.bases)
        clusters_distance_matrix = np.zeros((bases_count, bases_count))
        for i in range(bases_count):
            for j in range(i+1, bases_count):
                d = self.calculate_ct_method_between_clusters(self.clusters_map_of_sets[i], self.clusters_map_of_sets[j], self.clusters_map_of_edges_sets[i], self.clusters_map_of_edges_sets[j])
                clusters_distance_matrix[i, j] = d
                clusters_distance_matrix[j, i] = d
        return clusters_distance_matrix

    def calculate_ct_method_between_clusters(self, cluster1, cluster2, edges_list1, edges_list2):
        if self.om_mode:
            return self._om_distance(cluster1, cluster2)

        if self.mrc_lite_mode:
            return self._mrc_lite_distance(cluster1, cluster2, edges_list1, edges_list2)

        if self.wbmf_lite_mode:
            return self._wbmf_lite_distance(cluster1, cluster2)

        if self.ncbmf_mode:
            return self._ncbmf_distance(cluster1, cluster2)

        intersect = cluster1 & cluster2
        submatrix_indices = np.ix_(list(cluster1 - intersect), list(cluster2 - intersect))
        submatrix = self.ct_distance_matrix[submatrix_indices]
        if submatrix.size == 0:
            return 0
        d = None
        if self.ct_linkage_method == GHACLinkageMethod.SINGLE:
            d = np.min(submatrix)
        elif self.ct_linkage_method == GHACLinkageMethod.COMPLETE:
            d = np.max(submatrix)
        elif self.ct_linkage_method == GHACLinkageMethod.AVERAGE:
            if self.al_paper_denominator:
                d = float(np.sum(submatrix)) / (submatrix.shape[0] + submatrix.shape[1])
            else:
                d = np.average(submatrix)
        elif self.ct_linkage_method == GHACLinkageMethod.POWER_AVERAGE:
            d = self._power_average_distance(submatrix)

        if intersect:
            if self.overlap_reward_mode == 'normalized':
                d /= self._normalized_overlap_reward(
                    cluster1, cluster2, intersect, edges_list1 & edges_list2)
            elif self.overlap_reward_mode == 'directed':
                d /= self._directed_overlap_reward(cluster1, cluster2)
            elif self.overlap_reward_mode == 'relative':
                d /= self._relative_overlap_reward(cluster1, cluster2)
            else:
                d /= self._overlap_denominator(
                    intersect, edges_list1 & edges_list2)

        if self.ppr_mode and d > 0:
            lam = self._ppr_lambda(cluster1, cluster2)
            d *= (1.0 + self.ppr_gamma * max(0.0, 1.0 - lam))

        if self.cpm_mode and d > 0:
            eta = self._cpm_eta(cluster1, cluster2)
            d *= (1.0 + self.cpm_gamma * max(0.0, 1.0 - eta))

        if self.cg_mode and d > 0:
            phi = self._cg_phi(cluster1, cluster2)
            d /= (1.0 + self.cg_gamma * phi)

        if self.hrg_mode and d > 0:
            h_b = self._hrg_entropy(cluster1, cluster2)
            d *= (1.0 + self.hrg_gamma * h_b)

        if self.gcd_mode and d > 0:
            s_bar = self._gcd_similarity(cluster1, cluster2)
            d /= (1.0 + self.gcd_gamma * s_bar)
        return d

    def _gcd_node_similarity(self, u, v) -> float:
        su, sv = self._gcd_sig[u], self._gcd_sig[v]
        total = 0.0
        for a, b in zip(su, sv):
            denom = np.log(max(a, b) + 2.0)
            total += abs(np.log(a + 1.0) - np.log(b + 1.0)) / denom
        d_dist = total / len(su)
        return 1.0 - d_dist

    def _gcd_similarity(self, cluster1, cluster2) -> float:
        total = 0.0
        count = 0
        for u in cluster1:
            for v in cluster2:
                total += self._gcd_node_similarity(u, v)
                count += 1
        return total / count if count > 0 else 0.0

    def _om_edge_weight_sum(self, X, Y) -> float:
        total = 0.0
        smaller, larger = (X, Y) if len(X) <= len(Y) else (Y, X)
        for u in smaller:
            for v in self.graph.neighbors(u):
                if v in larger:
                    total += self._edge_weight.get((min(u, v), max(u, v)), 1.0)
        return total

    def _om_distance(self, cluster1, cluster2) -> float:
        O = cluster1 & cluster2
        A = cluster1 - cluster2
        B = cluster2 - cluster1
        if not A or not B:
            return 0.0

        w_ab = self._om_edge_weight_sum(A, B)
        m_sum = 0.0
        for o in O:
            a_o = sum(self._edge_weight.get((min(u, o), max(u, o)), 1.0)
                      for u in A if o in self.graph[u])
            b_o = sum(self._edge_weight.get((min(u, o), max(u, o)), 1.0)
                      for u in B if o in self.graph[u])
            m_sum += min(a_o, b_o)

        e_ij = w_ab + m_sum
        w_ao = self._om_edge_weight_sum(A, O) if O else 0.0
        w_bo = self._om_edge_weight_sum(B, O) if O else 0.0
        t_a = w_ab + w_ao
        t_b = w_ab + w_bo
        m_ij = e_ij / (min(t_a, t_b) + 1e-9)
        m_ij = min(max(m_ij, 0.0), 1.0)
        return 1.0 - m_ij

    def _mrc_lite_distance(self, cluster1, cluster2, edges_list1, edges_list2) -> float:
        intersect = cluster1 & cluster2
        only1 = list(cluster1 - intersect)
        only2 = list(cluster2 - intersect)
        if not only1 or not only2:
            return 0.0

        submatrix_indices = np.ix_(only1, only2)
        submatrix = self.ct_distance_matrix[submatrix_indices]
        z = (submatrix.astype(np.float64) - self._mrc_dmin) / (self._mrc_dmax - self._mrc_dmin + 1e-9)
        z = np.clip(z, 0.0, 1.0)
        flat = z.flatten()
        if flat.size == 1:
            w_ab = float(flat[0])
        else:
            q25, q75 = np.percentile(flat, [25, 75])
            clipped = np.clip(flat, q25, q75)
            w_ab = float(clipped.mean())

        if intersect:
            denom = self._overlap_denominator(intersect, edges_list1 & edges_list2)
            omega_star = denom - 1.0
            h = 1.0 + omega_star / (1.0 + omega_star)
        else:
            h = 1.0
        return w_ab / h

    def _wbmf_precompute(self):
        nodes = sorted(self.graph.nodes())
        idx = {v: i for i, v in enumerate(nodes)}
        n = len(nodes)

        edges = list(self.graph.edges(data=True))
        weight_attr = self.weight_attribute
        weights = np.array([float(d.get(weight_attr, 1.0)) for _, _, d in edges]) if edges else np.array([])
        if len(weights) == 0:
            return np.zeros((n, n)), np.zeros(n)
        order = np.argsort(weights)
        sorted_w = weights[order]
        rank_val = np.empty(len(weights))
        i = 0
        while i < len(sorted_w):
            j = i
            while j < len(sorted_w) and sorted_w[j] == sorted_w[i]:
                j += 1
            rank_val[i:j] = (i + 1 + j) / 2.0
            i = j
        ranks = np.empty(len(weights))
        ranks[order] = rank_val
        m = len(weights)
        a_vals = (ranks - 0.5) / m

        A = np.zeros((n, n))
        for (u, v, _), a in zip(edges, a_vals):
            A[idx[u], idx[v]] = a
            A[idx[v], idx[u]] = a

        s = A.sum(axis=1)
        s_safe = np.where(s > 0, s, 1e-9)
        sqrtA = np.sqrt(A)
        tau = (sqrtA / s_safe[None, :]) @ sqrtA.T
        np.fill_diagonal(tau, 0.0)

        b = (A * (1.0 + tau)) / (1.0 + A * (1.0 + tau))
        b = np.where(A > 0, b, 0.0)
        np.fill_diagonal(b, 0.0)

        row_sum = b.sum(axis=1)
        row_sum_safe = np.where(row_sum > 0, row_sum, 1e-9)
        P = b / row_sum_safe[:, None]
        K = 0.5 * (P + P @ P)

        r = b.sum(axis=1)
        K_full = np.zeros((n, n))
        r_full = np.zeros(n)
        for v in nodes:
            r_full[v] = r[idx[v]]
            for u in nodes:
                K_full[v, u] = K[idx[v], idx[u]]
        return K_full, r_full

    def _wbmf_lite_distance(self, cluster1, cluster2) -> float:
        X = cluster1 - cluster2
        Y = cluster2 - cluster1
        I = cluster1 & cluster2
        if not X or not Y:
            return 0.0

        K = self._wbmf_K
        YI = list(Y | I)
        XI = list(X | I)
        f_ab = sum(K[u, v] for u in X for v in YI) / len(X)
        f_ba = sum(K[v, u] for v in Y for u in XI) / len(Y)
        F = (2.0 * f_ab * f_ba) / (f_ab + f_ba + 1e-9)
        F = min(max(F, 0.0), 1.0)

        r = self._wbmf_r
        r_union = sum(r[u] for u in (cluster1 | cluster2))
        r_inter = sum(r[u] for u in I) if I else 0.0
        O = r_inter / (r_union + 1e-9)
        O = min(max(O, 0.0), 1.0)

        return (1.0 - F) * np.sqrt(max(1.0 - O, 0.0))

    def _ncbmf_precompute(self):
        nodes = sorted(self.graph.nodes())
        idx = {v: i for i, v in enumerate(nodes)}
        n = len(nodes)

        edges = list(self.graph.edges(data=True))
        weight_attr = self.weight_attribute
        weights = np.array([float(d.get(weight_attr, 1.0)) for _, _, d in edges]) if edges else np.array([])
        if len(weights) == 0:
            zeros_n = np.zeros(n)
            return np.zeros((n, n)), zeros_n, zeros_n
        order = np.argsort(weights)
        sorted_w = weights[order]
        rank_val = np.empty(len(weights))
        i = 0
        while i < len(sorted_w):
            j = i
            while j < len(sorted_w) and sorted_w[j] == sorted_w[i]:
                j += 1
            rank_val[i:j] = (i + 1 + j) / 2.0
            i = j
        ranks = np.empty(len(weights))
        ranks[order] = rank_val
        m = len(weights)
        a_vals = (ranks - 0.5) / m

        A = np.zeros((n, n))
        for (u, v, _), a in zip(edges, a_vals):
            A[idx[u], idx[v]] = a
            A[idx[v], idx[u]] = a

        s = A.sum(axis=1)
        s_safe = np.where(s > 0, s, 1e-9)
        sqrtA = np.sqrt(A)
        T3 = (sqrtA / s_safe[None, :]) @ sqrtA.T
        np.fill_diagonal(T3, 0.0)
        T3_hat = T3 / (1.0 + T3)

        adj = {v: set(self.graph.neighbors(v)) for v in nodes}
        T4 = np.zeros((n, n))
        for u, v, _ in edges:
            total = 0.0
            for x in adj[u]:
                if x == v:
                    continue
                for y in adj[v]:
                    if y == u or y == x:
                        continue
                    if y in adj.get(x, ()):
                        num = (A[idx[u], idx[x]] * A[idx[x], idx[y]] * A[idx[y], idx[v]]) ** (1.0 / 3.0)
                        den = np.sqrt(s_safe[idx[x]] * s_safe[idx[y]])
                        total += num / (den + 1e-9)
            T4[idx[u], idx[v]] = total
            T4[idx[v], idx[u]] = total
        T4_hat = T4 / (1.0 + T4)

        b = A * (1.0 + T3_hat + 0.5 * T4_hat)
        b = np.where(A > 0, b, 0.0)
        np.fill_diagonal(b, 0.0)

        row_sum = b.sum(axis=1)
        row_sum_safe = np.where(row_sum > 0, row_sum, 1e-9)
        P = b / row_sum_safe[:, None]
        P2 = P @ P
        P3 = P2 @ P
        K = 0.6 * P + 0.3 * P2 + 0.1 * P3

        r = b.sum(axis=1)
        r_total = r.sum()
        pi = r / r_total if r_total > 0 else np.ones(n) / n

        K_full = np.zeros((n, n))
        r_full = np.zeros(n)
        pi_full = np.zeros(n)
        for v in nodes:
            r_full[v] = r[idx[v]]
            pi_full[v] = pi[idx[v]]
            for u in nodes:
                K_full[v, u] = K[idx[v], idx[u]]
        return K_full, r_full, pi_full

    def _ncbmf_directional_support(self, X, target_set):
        K = self._ncbmf_K
        pi = self._ncbmf_pi
        X_list = list(X)
        target_list = list(target_set)
        pi_target = sum(pi[v] for v in target_list)
        pi_X = sum(pi[u] for u in X_list)
        p0 = pi_target / (1.0 - pi_X + 1e-9)

        e_vals = []
        for u in X_list:
            k_u_X = sum(K[u, v] for v in X_list)
            k_u_target = sum(K[u, v] for v in target_list)
            p_u = k_u_target / (1.0 - k_u_X + 1e-9)
            denom = p_u + p0 - 2.0 * p_u * p0 + 1e-9
            e_u = max(0.0, (p_u - p0) / denom) if denom > 0 else 0.0
            e_vals.append(min(e_u, 1.0))

        mean_e = sum(e_vals) / len(e_vals)
        e_vals_sorted = sorted(e_vals)
        h = -(-len(e_vals) // 2)
        lower_half_mean = sum(e_vals_sorted[:h]) / h
        return np.sqrt(max(mean_e, 0.0) * max(lower_half_mean, 0.0))

    def _ncbmf_distance(self, cluster1, cluster2) -> float:
        X = cluster1 - cluster2
        Y = cluster2 - cluster1
        I = cluster1 & cluster2
        if not X or not Y:
            return 0.0

        YI = Y | I
        XI = X | I
        G_XY = self._ncbmf_directional_support(X, YI)
        G_YX = self._ncbmf_directional_support(Y, XI)
        G_bi = (2.0 * G_XY * G_YX) / (G_XY + G_YX + 1e-9)
        G_bi = min(max(G_bi, 0.0), 1.0)

        O_bal = 0.0
        if I:
            K = self._ncbmf_K
            r = self._ncbmf_r
            all_nodes_set = set(self.graph.nodes())
            outside = all_nodes_set - (cluster1 | cluster2)
            q_vals = []
            for i_node in I:
                x_i = sum(K[i_node, u] for u in X)
                y_i = sum(K[i_node, v] for v in Y)
                o_i = sum(K[i_node, o] for o in outside) if outside else 0.0
                B_i = (4.0 * x_i * y_i) / ((x_i + y_i) ** 2 + 1e-9)
                R_i = (x_i + y_i) / (x_i + y_i + o_i + 1e-9)
                q_vals.append(np.sqrt(max(B_i, 0.0) * max(R_i, 0.0)))
            r_A = sum(r[u] for u in cluster1)
            r_B = sum(r[v] for v in cluster2)
            r_I = sum(r[i_node] for i_node in I)
            eta_I = r_I / (min(r_A, r_B) + 1e-9)
            O_bal = eta_I * (sum(q_vals) / len(q_vals))
            O_bal = min(max(O_bal, 0.0), 1.0)

        S = G_bi * (1.0 + O_bal * (1.0 - G_bi))
        S = min(max(S, 0.0), 1.0)
        return 1.0 - S

    def _hrg_entropy(self, cluster1, cluster2) -> float:
        e_cross = 0
        smaller, larger = (cluster1, cluster2) if len(cluster1) <= len(cluster2) else (cluster2, cluster1)
        for u in smaller:
            for v in self.graph.neighbors(u):
                if v in larger:
                    e_cross += 1
        denom = len(cluster1) * len(cluster2)
        if denom <= 0:
            return 0.0
        theta = e_cross / denom
        if theta <= 0.0 or theta >= 1.0:
            return 0.0
        return -theta * np.log(theta) - (1.0 - theta) * np.log(1.0 - theta)

    def _cg_touching_bases(self, cluster) -> set:
        qs = set()
        for v in cluster:
            qs.update(self._cg_node_to_bases.get(v, ()))
        return qs

    def _cg_phi(self, cluster1, cluster2) -> float:
        Qi = self._cg_touching_bases(cluster1)
        Qj = self._cg_touching_bases(cluster2)
        if not Qi or not Qj:
            return 0.0
        total = 0.0
        for qa in Qi:
            set_a = self._cg_base_sets[qa]
            for qb in Qj:
                if qb == qa:
                    continue
                shared = set_a & self._cg_base_sets[qb]
                if shared:
                    total += sum(self._cg_inv_km1.get(v, 0.0) for v in shared)
        denom = len(Qi) * len(Qj)
        return total / denom if denom > 0 else 0.0

    def _w_cross(self, cluster1, cluster2) -> float:
        smaller, larger = (cluster1, cluster2) if len(cluster1) <= len(cluster2) else (cluster2, cluster1)
        total = 0.0
        for u in smaller:
            for v in self.graph.neighbors(u):
                if v in larger:
                    total += self._edge_weight.get((min(u, v), max(u, v)), 1.0)
        return total

    def _cpm_eta(self, cluster1, cluster2) -> float:
        if self._cpm_gamma_res <= 0:
            return 1.0
        wc = self._w_cross(cluster1, cluster2)
        denom = self._cpm_gamma_res * len(cluster1) * len(cluster2)
        return wc / denom if denom > 0 else 1.0

    def _push_ppr(self, seed_dist: dict, max_iterations: int = 20000) -> dict:
        alpha, eps = self.ppr_alpha, self.ppr_eps
        p: dict = {}
        r = dict(seed_dist)
        queue = [u for u, mass in r.items() if mass >= eps * self._strength.get(u, 1.0)]
        queue_set = set(queue)
        iterations = 0
        while queue and iterations < max_iterations:
            u = queue.pop()
            queue_set.discard(u)
            iterations += 1
            ru = r.get(u, 0.0)
            du = self._strength.get(u, 0.0)
            if du <= 0 or ru < eps * du:
                continue
            p[u] = p.get(u, 0.0) + alpha * ru
            mass = (1.0 - alpha) * ru
            r[u] = 0.0
            for v in self.graph.neighbors(u):
                w = self._edge_weight.get((min(u, v), max(u, v)), 1.0)
                r[v] = r.get(v, 0.0) + mass * w / du
                dv = self._strength.get(v, 1.0)
                if r[v] >= eps * dv and v not in queue_set:
                    queue.append(v)
                    queue_set.add(v)
        return p

    def _cached_push(self, cluster) -> dict:
        key = frozenset(cluster)
        cached = self._ppr_push_cache.get(key)
        if cached is not None:
            return cached
        seed = {v: 1.0 / len(cluster) for v in cluster}
        p = self._push_ppr(seed)
        self._ppr_push_cache[key] = p
        return p

    def _ppr_lambda(self, cluster1, cluster2) -> float:
        if not self.wt:
            return 1.0
        p1 = self._cached_push(cluster1)
        p2 = self._cached_push(cluster2)
        flow_12 = sum(p1.get(v, 0.0) for v in cluster2)
        flow_21 = sum(p2.get(v, 0.0) for v in cluster1)
        rho = 0.5 * (flow_12 + flow_21)
        vol1 = sum(self._strength.get(u, 0.0) for u in cluster1)
        vol2 = sum(self._strength.get(u, 0.0) for u in cluster2)
        null = (vol1 + vol2) / (4.0 * self.wt)
        if null <= 0:
            return 1.0
        return rho / null

    def _normalized_overlap_reward(self, cluster1, cluster2, intersect, common_edges) -> float:
        union_size = len(cluster1 | cluster2)
        jaccard = len(intersect) / union_size if union_size > 0 else 0.0

        n_overlap = len(intersect)
        max_possible_edges = n_overlap * (n_overlap - 1) / 2.0
        if max_possible_edges > 0 and common_edges:
            edge_weight_sum = sum(
                self._edge_weight.get(edge, 1.0) if self.weight_attribute is not None else 1.0
                for edge in common_edges
            )
            density = edge_weight_sum / max_possible_edges
        else:
            density = 0.0

        o = self.overlap_lambda * jaccard + (1.0 - self.overlap_lambda) * min(density, 1.0)
        return 1.0 + self.overlap_alpha * np.tanh(self.overlap_beta * o)

    def _vertex_attachment_prob(self, u, target: set) -> float:
        total = 0.0
        attached = 0.0
        for v in self.graph.neighbors(u):
            w = self._edge_weight.get((min(u, v), max(u, v)), 1.0)
            total += w
            if v in target:
                attached += w
        return attached / total if total > 0 else 0.0

    def _directed_support(self, source: set, target: set) -> float:
        if not source:
            return 0.0
        containment = len(source & target) / len(source)
        boundary = source - target
        if not boundary:
            return containment
        miss_prob = 1.0
        for u in boundary:
            miss_prob *= (1.0 - self._vertex_attachment_prob(u, target))
        attachment = 1.0 - miss_prob
        return containment * attachment

    def _directed_overlap_reward(self, cluster1, cluster2) -> float:
        s_12 = self._directed_support(cluster1, cluster2)
        s_21 = self._directed_support(cluster2, cluster1)
        o = max(s_12, s_21)
        return 1.0 + self.overlap_alpha * np.tanh(self.overlap_beta * o)

    def _power_average_distance(self, submatrix: np.ndarray) -> float:
        maximum = float(np.max(submatrix))
        if maximum == 0.0:
            return 0.0
        scaled = submatrix / maximum
        return maximum * float(np.sqrt(np.mean(np.square(scaled))))

    def _relative_overlap_reward(self, cluster1, cluster2) -> float:
        smaller_size = min(len(cluster1), len(cluster2))
        rho = len(cluster1 & cluster2) / smaller_size
        return 1.0 + rho

    def _overlap_denominator(self, intersect, common_edges) -> float:
        if len(intersect) == 1:
            return 2.0

        intersect_key = frozenset(intersect)
        edges_key = frozenset(common_edges)
        cache_key = (intersect_key, edges_key, self.weight_attribute)
        cached = self._overlap_denominator_cache.get(cache_key)
        if cached is not None:
            return cached

        if not edges_key:
            denominator = 2.0
        else:
            graph_overlap = nx.edge_subgraph(self.graph, edges_key).copy()
            graph_overlap.add_nodes_from(intersect_key)
            cliques = list(nx.find_cliques(graph_overlap))
            max_size = max((len(clique) for clique in cliques), default=1)
            denominator = 1.0 + max_size

            if self.weight_attribute is not None and self.wt:
                max_weight = 0.0
                for clique in cliques:
                    if len(clique) != max_size:
                        continue
                    clique_nodes = set(clique)
                    clique_weight = sum(
                        self._edge_weight.get(edge, 0.0)
                        for edge in edges_key
                        if edge[0] in clique_nodes and edge[1] in clique_nodes
                    )
                    max_weight = max(max_weight, clique_weight / self.wt)
                denominator += max_weight

        if len(self._overlap_denominator_cache) < self._overlap_cache_limit:
            self._overlap_denominator_cache[cache_key] = denominator
        return denominator
