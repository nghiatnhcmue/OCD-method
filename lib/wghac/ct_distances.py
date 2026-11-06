# Khoảng cách CT có trọng số, tính bằng tệp nhị phân trong tools/closed_trail_distance_binary/.

import os
import subprocess
import time
from pathlib import Path

import networkx as nx
import numpy as np

from settings import CT_BINARY_DIR
DEFAULT_BINARY_PATH = CT_BINARY_DIR / 'efficient_suurballe_weighted'
DEFAULT_NETWORKIT_LIB_DIR = CT_BINARY_DIR


def sanitize_matrix(matrix: np.ndarray) -> np.ndarray:
    m = np.asarray(matrix, dtype=np.float64)
    m = np.nan_to_num(m, nan=0.0, posinf=0.0, neginf=0.0)
    m = np.maximum(m, 0.0)
    m = (m + m.T) / 2.0
    np.fill_diagonal(m, 0.0)
    max_val = m.max() if m.size else 0.0
    if max_val > 996:
        m = m * (996.0 / max_val)
    np.fill_diagonal(m, 0.0)
    return m.astype(np.float32)


def compute_ct_binary(graph_gcc: nx.Graph, temp_prefix: str = 'ct') -> np.ndarray:
    binary_path = Path(os.environ.get('WGHAC_CT_BINARY', DEFAULT_BINARY_PATH))
    if not binary_path.is_file():
        raise RuntimeError(
            f'Missing Snasel_4 weighted CT executable: {binary_path}. '
            'Set WGHAC_CT_BINARY to the official four-argument binary.'
        )
    if graph_gcc.is_multigraph():
        raise ValueError('Snasel_4 weighted CT expects a simple undirected graph.')
    bridges = list(nx.bridges(graph_gcc))
    if bridges:
        raise ValueError(
            'Snasel_4 weighted CT requires a graph without bridges; '
            f'found {len(bridges)} bridge edge(s).'
        )
    os.makedirs('tmp_files', exist_ok=True)
    stamp = f'{temp_prefix}_{os.getpid()}_{time.time_ns()}'
    edge_path = os.path.join('tmp_files', f'{stamp}.edgelist')
    out_path = os.path.join('tmp_files', f'{stamp}_dist.csv')
    try:
        try:
            nodes = sorted(graph_gcc.nodes())
        except TypeError:
            nodes = sorted(graph_gcc.nodes(), key=lambda node: (type(node).__name__, repr(node)))
        node_index = {node: index for index, node in enumerate(nodes)}
        edges = list(graph_gcc.edges(data=True))
        with open(edge_path, 'w', encoding='utf-8', newline='\n') as stream:
            for u, v, data in edges:
                if 'cost' in data:
                    cost = float(data['cost'])
                else:
                    affinity = float(data.get('weight_normalized', data.get('weight', 1.0)))
                    cost = 1.0 / max(affinity, 1e-10)
                if not np.isfinite(cost) or cost <= 0.0:
                    raise ValueError(f'CT edge cost must be finite and positive: {(u, v)}={cost}')
                stream.write(f'{node_index[u]} {node_index[v]} {cost:.17g}\n')
        child_env = os.environ.copy()
        lib_dir = os.environ.get(
            'WGHAC_NETWORKIT_LIB_DIR', str(DEFAULT_NETWORKIT_LIB_DIR)
        )
        previous_lib_path = child_env.get('LD_LIBRARY_PATH', '')
        child_env['LD_LIBRARY_PATH'] = (
            lib_dir if not previous_lib_path else f'{lib_dir}{os.pathsep}{previous_lib_path}'
        )
        res = subprocess.run(
            [str(binary_path), edge_path, 'edgelist', 'full', out_path],
            capture_output=True,
            text=True,
            check=False,
            env=child_env,
        )
        if res.returncode != 0:
            detail = res.stderr.strip() or res.stdout.strip()
            raise RuntimeError(f'efficient_suurballe_weighted failed: {detail}')
        matrix = np.atleast_2d(np.loadtxt(out_path, dtype=np.float64, delimiter='\t'))
        expected = (len(nodes), len(nodes))
        if matrix.shape != expected:
            raise RuntimeError(f'weighted_closed_trail returned {matrix.shape}, expected {expected}')
        return sanitize_matrix(matrix)
    finally:
        for p in [edge_path, out_path]:
            if os.path.exists(p):
                os.remove(p)
