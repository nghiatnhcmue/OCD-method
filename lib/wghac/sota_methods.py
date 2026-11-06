# Trình bao các phương pháp đối chứng: OSLOM, SLPA, ASLPAw, DANMF, BigCLAM, Infomap.

import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import tempfile
import time

import cdlib
import cdlib.algorithms
import networkx as nx
import numpy as np

from wghac import functions
import settings


def _set_reproducible_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def _find_oslom_binary(directed: bool = False) -> str | None:
    env_names = (
        ('OSLOM_DIR_PATH', 'OSLOM_PATH') if directed
        else ('OSLOM_UNDIR_PATH', 'OSLOM_PATH')
    )
    for env_name in env_names:
        path = os.environ.get(env_name)
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    binary_name = 'oslom_dir' if directed else 'oslom_undir'
    path = shutil.which(binary_name)
    if path:
        return path

    local_path = settings.TOOLS / 'oslom' / 'OSLOM2' / binary_name
    if local_path.is_file() and os.access(local_path, os.X_OK):
        return str(local_path)
    return None


def _unc_wsl_parts(path: str | Path) -> tuple[str, str] | None:
    value = str(path).replace('/', '\\')
    prefix = '\\\\wsl.localhost\\'
    if not value.lower().startswith(prefix.lower()):
        return None
    parts = value[len(prefix):].split('\\')
    if len(parts) < 2:
        return None
    distro = parts[0]
    linux_path = '/' + '/'.join(part for part in parts[1:] if part)
    return distro, linux_path


def _communities_from_result(result) -> list:
    return [set(c) for c in result.communities if len(c) >= 2]


def _predicted_overlap_node_count(communities: list) -> int:
    counts = {}
    for community in communities:
        for node in community:
            counts[node] = counts.get(node, 0) + 1
    return sum(1 for count in counts.values() if count > 1)


def _pyoslom_base_communities(model) -> list:
    clusters = model.cluster_.get('clusters', {}) if model.cluster_ else {}
    base_clusters = clusters.get(0, {})
    if not base_clusters:
        return []
    return [set(nlist) for nlist in base_clusters.values() if nlist]


def _pyoslom_weighted_graph(graph_gcc: nx.Graph) -> nx.Graph:
    return _graph_with_standard_weight(graph_gcc)


def _graph_with_standard_weight(graph_gcc: nx.Graph) -> nx.Graph:
    graph = graph_gcc.copy()
    for _, _, data in graph.edges(data=True):
        data['weight'] = float(data.get('weight_normalized', data.get('weight', 1.0)))
    return graph


def _run_pyoslom_fallback(graph_gcc: nx.Graph) -> tuple[list, str]:
    from pyoslom import OSLOM as _PyOSLOM

    model = _PyOSLOM(directed=False, random_state=42)
    model.fit(_pyoslom_weighted_graph(graph_gcc))
    communities = _pyoslom_base_communities(model)
    return communities, 'pyoslom_level0_fallback'


def _parse_oslom_tp_file(tp_path: Path, id_to_node: dict[int, object]) -> list:
    zero_id_to_node = {idx - 1: node for idx, node in id_to_node.items()}
    communities = []

    with tp_path.open('r', encoding='utf-8', errors='ignore') as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            ids = [int(x) for x in re.findall(r'-?\d+', line)]
            if not ids:
                continue

            nodes = []
            for raw_id in ids:
                if raw_id in id_to_node:
                    nodes.append(id_to_node[raw_id])
                elif raw_id in zero_id_to_node:
                    nodes.append(zero_id_to_node[raw_id])
            community = set(nodes)
            if len(community) >= 2:
                communities.append(community)

    unique = []
    seen = set()
    for community in communities:
        key = frozenset(community)
        if key not in seen:
            seen.add(key)
            unique.append(community)
    return unique


def _run_original_oslom_binary(
        graph_gcc: nx.Graph,
        config: dict | None = None,
) -> tuple[list, str]:
    config = dict(config or {})
    binary = _find_oslom_binary(directed=False)
    if not binary:
        raise FileNotFoundError('oslom_undir binary not found')

    nodes = list(graph_gcc.nodes())
    node_to_id = {node: idx + 1 for idx, node in enumerate(nodes)}
    id_to_node = {idx + 1: node for idx, node in enumerate(nodes)}

    tmp_root = settings.TMP / 'oslom'
    tmp_root.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix='oslom_run_', dir=tmp_root))
    edge_path = run_dir / 'network.dat'

    try:
        with edge_path.open('w', encoding='utf-8') as fh:
            for u, v, data in graph_gcc.edges(data=True):
                weight = data.get('weight_normalized', data.get('weight', 1.0))
                try:
                    weight = float(weight)
                except (TypeError, ValueError):
                    weight = 1.0
                if not np.isfinite(weight) or weight <= 0:
                    weight = 1.0
                fh.write(f'{node_to_id[u]} {node_to_id[v]} {weight:.12g}\n')

        timeout = int(config.get(
            'timeout_sec', os.environ.get('OSLOM_TIMEOUT_SEC', '3600')))
        seed = str(config.get('seed', os.environ.get('OSLOM_SEED', '42')))
        runs = str(config.get('runs', os.environ.get('OSLOM_RUNS', '10')))
        hier_runs = str(config.get(
            'hier_runs', os.environ.get('OSLOM_HIER_RUNS', '50')))
        threshold = str(config.get(
            'threshold', os.environ.get('OSLOM_T', '0.1')))
        coverage = str(config.get(
            'coverage', os.environ.get('OSLOM_CP', '0.5')))
        oslom_args = [
            '-f', edge_path.name,
            '-w',
            '-seed', seed,
            '-r', runs,
            '-hr', hier_runs,
            '-t', threshold,
            '-cp', coverage,
        ]
        if config.get('fast'):
            oslom_args.append('-fast')
        binary_wsl = _unc_wsl_parts(binary)
        run_dir_wsl = _unc_wsl_parts(run_dir)
        if os.name == 'nt' and binary_wsl and run_dir_wsl:
            binary_distro, binary_linux_path = binary_wsl
            run_dir_distro, run_dir_linux_path = run_dir_wsl
            if binary_distro != run_dir_distro:
                raise RuntimeError(
                    f'OSLOM binary and run directory use different WSL distros: '
                    f'{binary_distro} != {run_dir_distro}')
            cmd = [
                'wsl.exe', '-d', binary_distro,
                '--cd', run_dir_linux_path,
                '--', binary_linux_path,
                *oslom_args,
            ]
            proc_cwd = None
        else:
            cmd = [binary, *oslom_args]
            proc_cwd = run_dir
        proc = subprocess.run(
            cmd,
            cwd=proc_cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
        if proc.returncode != 0:
            tail = proc.stdout[-600:].replace('\n', ' | ') if proc.stdout else ''
            raise RuntimeError(f'oslom_undir failed with code {proc.returncode}: {tail}')

        output_dir = run_dir / f'{edge_path.name}_oslo_files'
        candidates = [
            output_dir / 'tp',
            output_dir / 'tp_without_singletons',
            run_dir / 'tp',
        ]
        for tp_path in candidates:
            if tp_path.is_file():
                communities = _parse_oslom_tp_file(tp_path, id_to_node)
                if communities:
                    overlap_nodes = _predicted_overlap_node_count(communities)
                    return communities, (
                        f'oslom_binary:{Path(binary).name}:{tp_path.name}:'
                        f'r={runs}:hr={hier_runs}:t={threshold}:cp={coverage}:'
                        f'seed={seed}:communities={len(communities)}:'
                        f'overlap_nodes={overlap_nodes}'
                    )

        raise ValueError('oslom_undir completed but no non-empty tp communities were parsed')
    finally:
        resolved_run_dir = run_dir.resolve()
        resolved_tmp_root = tmp_root.resolve()
        if resolved_run_dir.parent == resolved_tmp_root and resolved_run_dir.name.startswith('oslom_run_'):
            shutil.rmtree(resolved_run_dir, ignore_errors=True)


def _evaluate_communities(graph_gcc: nx.Graph, communities: list, gt_communities) -> dict:
    weight = str(graph_gcc.graph.get(
        'analysis_weight',
        'weight_normalized'
        if any('weight_normalized' in data for _, _, data in graph_gcc.edges(data=True))
        else 'weight_uniform',
    ))
    raw = [set(community) for community in communities if community]
    full_cover = functions.postprocess_for_full_cover(
        raw, graph_gcc.nodes(), graph_gcc)
    ev = functions.get_overlapping_evaluation_dict(
        graph_gcc,
        raw,
        weight,
        gt_communities,
        full_cover_communities=full_cover,
    )
    ev['selection_metric'] = 'direct_result'
    ev['selection_value'] = np.nan
    return ev


def _patch_danmf(cls, sp):
    if getattr(cls, '_wghac_sparse_patch', False):
        return
    orig = cls._setup_target_matrices

    def patched(self, g):
        orig(self, g)
        self._A = sp.csr_matrix(self._A)
        self._L = sp.csr_matrix(self._L)
        self._D = sp.csr_matrix(self._D)

    cls._setup_target_matrices = patched
    cls._wghac_sparse_patch = True


def _run_danmf(
        graph_gcc: nx.Graph,
        gt_communities,
        config: dict | None = None,
) -> dict:
    config = dict(config or {})
    import scipy.sparse as _sp
    from karateclub import DANMF

    _patch_danmf(DANMF, _sp)

    if 'layers' in config:
        layers = [int(value) for value in config['layers']]
    else:
        last = max(4, functions.estimate_structural_community_count(graph_gcc))
        first = max(last * 2, last + 16)
        layers = [first, last]
    pre_iterations = int(config.get('pre_iterations', 100))
    iterations = int(config.get('iterations', 100))
    seed = int(config.get('seed', 42))
    lamb = float(config.get('lamb', 0.1))
    col_threshold = float(config.get('col_threshold', 0.1))
    model = DANMF(
        layers=layers,
        pre_iterations=pre_iterations,
        iterations=iterations,
        seed=seed,
        lamb=lamb,
    )
    model.fit(graph_gcc.copy())

    communities = []
    if hasattr(model, '_P'):
        P = np.asarray(model._P)
        if P.ndim == 2 and P.shape[0] > 0:
            for k in range(P.shape[1]):
                col = P[:, k]
                col_max = col.max()
                if col_max <= 0 or not np.isfinite(col_max):
                    continue
                members = set(int(i) for i in np.where(col > col_threshold * col_max)[0])
                if len(members) >= 2:
                    communities.append(members)

    if not communities:
        memberships = model.get_memberships()
        comm_map: dict = {}
        for node, cid in memberships.items():
            comm_map.setdefault(int(cid), set()).add(int(node))
        communities = [c for c in comm_map.values() if len(c) >= 2]

    if not communities:
        raise ValueError('DANMF returned no communities')

    ev = _evaluate_communities(graph_gcc, communities, gt_communities)
    overlap_nodes = _predicted_overlap_node_count(communities)
    ev.setdefault('metric_status', {})['sota_output'] = (
        f'karateclub.DANMF:layers={layers}:pre_iterations={pre_iterations}:'
        f'iterations={iterations}:lambda={lamb}:seed={seed}:'
        f'col_threshold={col_threshold}:overlap_nodes={overlap_nodes}:'
        'protocol=snasel4_column_soft_membership'
    )
    return ev


def _find_bigclam_binary() -> str | None:
    env_path = os.environ.get('BIGCLAM_PATH')
    if env_path and os.path.exists(env_path):
        return env_path
    local_path = settings.TOOLS / 'bigclam' / 'bigclam'
    if local_path.exists():
        return str(local_path)
    tmp_path = Path('/tmp/snap/examples/bigclam/bigclam')
    if tmp_path.exists():
        return str(tmp_path)
    return shutil.which('bigclam')


def _run_bigclam(
        graph_gcc: nx.Graph,
        gt_communities,
        config: dict | None = None,
) -> dict:
    config = dict(config or {})
    bin_path = _find_bigclam_binary()

    if 'dimensions' in config:
        dimensions = int(config['dimensions'])
    else:
        dimensions = max(4, functions.estimate_structural_community_count(graph_gcc))

    if bin_path:
        with tempfile.TemporaryDirectory(prefix="snap_bc_") as tmpdir:
            tmp = Path(tmpdir)
            edge_file = tmp / "edges.txt"
            with open(edge_file, "w") as f:
                for u, v in sorted(graph_gcc.edges()):
                    f.write(f"{u}\t{v}\n")
            out_prefix = str(tmp / "bc_")
            cmd = [str(bin_path), f"-i:{edge_file}", f"-o:{out_prefix}", f"-c:{dimensions}", "-nt:1"]
            cp = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tmp), timeout=1800)
            cmty_file = tmp / "bc_cmtyvv.txt"
            if cp.returncode == 0 and cmty_file.exists():
                communities = []
                for line in cmty_file.read_text().splitlines():
                    line = line.strip()
                    if line:
                        members = set(int(x) for x in line.split() if x.strip())
                        if len(members) >= 2:
                            communities.append(members)
                if communities:
                    ev = _evaluate_communities(graph_gcc, communities, gt_communities)
                    overlap_nodes = _predicted_overlap_node_count(communities)
                    ev.setdefault('metric_status', {})['sota_output'] = (
                        f'snap.BigClam:dimensions={dimensions}:overlap_nodes={overlap_nodes}:'
                        'binary=official_snap_cpp'
                    )
                    return ev

    from karateclub import BigClam

    iterations = int(config.get('iterations', 50))
    learning_rate = float(config.get('learning_rate', 0.005))
    seed = int(config.get('seed', 42))

    nodes = list(graph_gcc.nodes())
    relabelled = nx.convert_node_labels_to_integers(graph_gcc, ordering='default')
    model = BigClam(
        dimensions=dimensions,
        iterations=iterations,
        learning_rate=learning_rate,
        seed=seed,
    )
    model.fit(relabelled)
    F = np.asarray(model.get_embedding(), dtype=float)

    n = relabelled.number_of_nodes()
    m = relabelled.number_of_edges()
    epsilon = (2.0 * m) / (n * (n - 1)) if n > 1 else 0.0
    epsilon = min(max(epsilon, 1e-12), 1.0 - 1e-12)
    delta = float(np.sqrt(-np.log(1.0 - epsilon)))

    communities = []
    for k in range(F.shape[1]):
        members = set(nodes[i] for i in np.where(F[:, k] >= delta)[0])
        if len(members) >= 2:
            communities.append(members)

    if not communities:
        comm_map: dict = {}
        for idx, cid in model.get_memberships().items():
            comm_map.setdefault(int(cid), set()).add(nodes[int(idx)])
        communities = [c for c in comm_map.values() if len(c) >= 2]

    if not communities:
        raise ValueError('BigCLAM returned no communities')

    ev = _evaluate_communities(graph_gcc, communities, gt_communities)
    overlap_nodes = _predicted_overlap_node_count(communities)
    ev.setdefault('metric_status', {})['sota_output'] = (
        f'karateclub.BigClam:dimensions={dimensions}:iterations={iterations}:'
        f'learning_rate={learning_rate}:seed={seed}:delta={delta:.6g}:'
        f'overlap_nodes={overlap_nodes}:protocol=de_cuong_wsdm13_delta_threshold'
    )
    return ev


def run_sota_method(
        method_name: str,
        graph_gcc: nx.Graph,
        gt_communities,
        config: dict | None = None,
) -> tuple:
    t0 = time.time()
    config = dict(config or {})
    seed = int(config.get('seed', 42))
    _set_reproducible_seed(seed)

    oslom_source = None

    if method_name == 'OSLOM':
        if _find_oslom_binary(directed=False):
            try:
                communities, oslom_source = _run_original_oslom_binary(
                    graph_gcc, config=config)
            except Exception as binary_exc:
                if config.get('require_original'):
                    raise
                try:
                    communities, fallback_source = _run_pyoslom_fallback(graph_gcc)
                except Exception as fallback_exc:
                    raise RuntimeError(
                        f'OSLOM binary failed: {binary_exc}; '
                        f'pyoslom fallback failed: {fallback_exc}') from binary_exc
                msg = str(binary_exc).replace('\n', ' ')[:220]
                oslom_source = f'oslom_binary_failed:{msg};fallback={fallback_source}'
        else:
            if config.get('require_original'):
                raise FileNotFoundError(
                    'Original OSLOM binary required by this protocol but not found.')
            communities, oslom_source = _run_pyoslom_fallback(graph_gcc)

    elif method_name == 'ASLPAW':
        n_restarts = int(config.get('n_restarts', 5))
        restart_seeds = [seed + i * 37 for i in range(n_restarts)]
        best_communities = None
        for rs in restart_seeds:
            _set_reproducible_seed(rs)
            try:
                result = cdlib.algorithms.aslpaw(graph_gcc)
                cands = _communities_from_result(result)
            except Exception:
                continue
            if best_communities is None or len(cands) > len(best_communities):
                best_communities = cands
        communities = best_communities or []

    elif method_name == 'SLPA':
        t = int(config.get('t', 21))
        r = float(config.get('r', 0.1))
        result = cdlib.algorithms.slpa(graph_gcc, t=t, r=r)
        communities = _communities_from_result(result)

    elif method_name == 'DANMF':
        evaluation = _run_danmf(graph_gcc, gt_communities, config=config)
        return evaluation, time.time() - t0

    elif method_name == 'BigCLAM':
        evaluation = _run_bigclam(graph_gcc, gt_communities, config=config)
        return evaluation, time.time() - t0

    else:
        raise ValueError(f'Unknown SOTA method: {method_name}')

    if not communities:
        raise ValueError(f'{method_name} returned no communities')

    evaluation = _evaluate_communities(graph_gcc, communities, gt_communities)
    if method_name == 'OSLOM':
        overlap_nodes = _predicted_overlap_node_count(communities)
        status = oslom_source or 'unknown_oslom_backend'
        if overlap_nodes == 0:
            status = f'{status}:no_predicted_overlap_nodes'
        evaluation.setdefault('metric_status', {})['sota_output'] = status
        if 'fallback' in status:
            evaluation['runtime_note_type'] = 'fallback'
            evaluation['runtime_note_message'] = status
    elif method_name == 'ASLPAW':
        evaluation.setdefault('metric_status', {})['sota_output'] = (
            'cdlib.aslpaw:reference_wrapper:unweighted:'
            f'seed={seed}:protocol=snasel4_default_configuration'
        )
    elif method_name == 'SLPA':
        t = int(config.get('t', 21))
        r = float(config.get('r', 0.1))
        overlap_nodes = _predicted_overlap_node_count(communities)
        evaluation.setdefault('metric_status', {})['sota_output'] = (
            f'cdlib.slpa:reference_wrapper:unweighted:t={t}:r={r}:'
            f'seed={seed}:overlap_nodes={overlap_nodes}:'
            'protocol=de_cuong_baseline_configuration'
        )
    return evaluation, time.time() - t0


def run_infomap(graph: nx.Graph, directed: bool = False, seed: int = 42) -> list:
    _set_reproducible_seed(seed)
    g = _graph_with_standard_weight(graph)
    if directed:
        if not g.is_directed():
            g = g.to_directed()
        flags = f'-d --seed {int(seed)} --silent'
    else:
        if g.is_directed():
            g = nx.Graph(g)
        flags = f'--seed {int(seed)} --silent'
    result = cdlib.algorithms.infomap(g, flags=flags)
    return _communities_from_result(result)
