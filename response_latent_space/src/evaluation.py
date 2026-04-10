from __future__ import annotations

from typing import Callable, Dict, Iterable, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score
from sklearn.metrics import adjusted_rand_score


def compute_reconstruction_error(original: pd.DataFrame, reconstructed: pd.DataFrame) -> float:
    a = original.to_numpy(dtype=float)
    b = reconstructed.to_numpy(dtype=float)
    return float(np.sqrt(np.mean((a - b) ** 2)))


def compute_silhouette_score(embedding: pd.DataFrame, labels: pd.Series) -> float:
    x = embedding.to_numpy(dtype=float)
    y = labels.to_numpy()
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(silhouette_score(x, y))


def nearest_neighbor_table(
    embedding: pd.DataFrame, ids: Optional[Iterable[str]] = None, n_neighbors: int = 10
) -> pd.DataFrame:
    from sklearn.neighbors import NearestNeighbors

    if ids is None:
        ids = embedding.index.astype(str)
    ids = list(map(str, ids))

    x = embedding.loc[ids].to_numpy(dtype=float)
    nn = NearestNeighbors(n_neighbors=min(n_neighbors + 1, len(ids)))
    nn.fit(x)
    dists, idx = nn.kneighbors(x)

    rows = []
    for i, q in enumerate(ids):
        for rank, (j, dist) in enumerate(zip(idx[i, 1:], dists[i, 1:]), start=1):
            rows.append(
                {
                    "query_id": q,
                    "neighbor_rank": rank,
                    "neighbor_id": ids[int(j)],
                    "distance": float(dist),
                }
            )
    return pd.DataFrame(rows)


def bootstrap_cluster_stability(
    embedding: pd.DataFrame,
    cluster_fn: Callable[[pd.DataFrame], pd.Series],
    *,
    n_bootstrap: int = 50,
    sample_frac: float = 0.8,
    random_state: int = 1337,
) -> pd.DataFrame:
    """
    Generic bootstrap stability stub.
    Returns the fraction of times each pair co-clusters (for sampled items).

    cluster_fn signature: (embedding_subset: pd.DataFrame) -> pd.Series labels indexed by ids
    """
    rng = np.random.default_rng(random_state)
    ids = embedding.index.astype(str).to_numpy()
    n = len(ids)
    if n < 2:
        return pd.DataFrame(columns=["id_i", "id_j", "co_cluster_prob"])

    pair_counts: Dict[Tuple[str, str], int] = {}
    sample_counts: Dict[Tuple[str, str], int] = {}

    for _ in range(n_bootstrap):
        take = rng.choice(ids, size=max(2, int(np.ceil(sample_frac * n))), replace=False)
        sub = embedding.loc[take]
        labels = cluster_fn(sub).astype(int)
        lab = labels.to_dict()
        take_list = list(map(str, take))

        for a_i in range(len(take_list)):
            for b_i in range(a_i + 1, len(take_list)):
                a = take_list[a_i]
                b = take_list[b_i]
                key = (a, b) if a < b else (b, a)
                sample_counts[key] = sample_counts.get(key, 0) + 1
                if lab[a] == lab[b]:
                    pair_counts[key] = pair_counts.get(key, 0) + 1

    rows = []
    for (a, b), denom in sample_counts.items():
        numer = pair_counts.get((a, b), 0)
        rows.append({"id_i": a, "id_j": b, "co_cluster_prob": numer / denom})
    return pd.DataFrame(rows)


def bootstrap_against_reference_labels(
    embedding: pd.DataFrame,
    cluster_fn: Callable[[pd.DataFrame], pd.Series],
    reference_labels: pd.Series,
    *,
    n_bootstrap: int = 50,
    sample_frac: float = 0.8,
    random_state: int = 1337,
) -> pd.DataFrame:
    """
    Stability summary: repeatedly recluster a random subset of items and compare to a
    reference clustering using Adjusted Rand Index (ARI).

    - embedding: items×k
    - reference_labels: labels indexed by item id
    - cluster_fn: (embedding_subset) -> labels indexed by item id
    """
    rng = np.random.default_rng(random_state)
    ids_all = embedding.index.astype(str)
    ref = reference_labels.copy()
    ref.index = ref.index.astype(str)

    common = ids_all.intersection(ref.index)
    if len(common) < 3:
        return pd.DataFrame(columns=["bootstrap", "n_items", "ari"])

    ids = common.to_numpy()
    n = len(ids)
    take_n = max(3, int(np.ceil(sample_frac * n)))

    rows = []
    for b in range(int(n_bootstrap)):
        take = rng.choice(ids, size=min(take_n, n), replace=False)
        sub = embedding.loc[take]
        pred = cluster_fn(sub)
        pred = pred.loc[take].astype(int)
        y_true = ref.loc[take].astype(int)
        ari = float(adjusted_rand_score(y_true.to_numpy(), pred.to_numpy()))
        rows.append({"bootstrap": b, "n_items": int(len(take)), "ari": ari})
    return pd.DataFrame(rows)


def neighbor_label_enrichment(
    neighbor_table: pd.DataFrame,
    metadata: pd.DataFrame,
    *,
    id_col: str = "drug_id",
    label_col: str,
    n_permutations: int = 1000,
    random_state: int = 1337,
) -> pd.DataFrame:
    """
    Compute label agreement enrichment in a nearest-neighbor table vs a shuffled-label baseline.

    Expects neighbor_table columns (as produced by nearest_neighbor_table):
      - query_id, neighbor_id, neighbor_rank, distance

    Returns a one-row DataFrame with observed match rate, permutation mean/std, and p-value.
    """
    if neighbor_table.empty:
        return pd.DataFrame(
            [
                {
                    "label_col": label_col,
                    "n_pairs": 0,
                    "observed_match_rate": np.nan,
                    "perm_mean": np.nan,
                    "perm_std": np.nan,
                    "p_value": np.nan,
                }
            ]
        )

    md = metadata.copy()
    if id_col not in md.columns or label_col not in md.columns:
        raise ValueError(f"metadata must contain columns: {id_col!r}, {label_col!r}")

    md[id_col] = md[id_col].astype(str)
    md[label_col] = md[label_col].astype(str)
    label_map = md.set_index(id_col)[label_col]

    df = neighbor_table.copy()
    df["query_id"] = df["query_id"].astype(str)
    df["neighbor_id"] = df["neighbor_id"].astype(str)
    df["query_label"] = df["query_id"].map(label_map)
    df["neighbor_label"] = df["neighbor_id"].map(label_map)
    df = df.dropna(subset=["query_label", "neighbor_label"])
    df = df[(df["query_label"] != "nan") & (df["neighbor_label"] != "nan")]

    if df.empty:
        return pd.DataFrame(
            [
                {
                    "label_col": label_col,
                    "n_pairs": 0,
                    "observed_match_rate": np.nan,
                    "perm_mean": np.nan,
                    "perm_std": np.nan,
                    "p_value": np.nan,
                }
            ]
        )

    obs = float((df["query_label"] == df["neighbor_label"]).mean())
    n_pairs = int(len(df))

    # Permutation baseline: shuffle labels across ids (keeps neighbor graph fixed)
    rng = np.random.default_rng(random_state)
    ids = label_map.index.to_numpy()
    labels = label_map.to_numpy()

    # Precompute indexers for fast remapping (-1 means missing)
    idx = pd.Index(ids.astype(str))
    q_pos = idx.get_indexer(df["query_id"].astype(str))
    n_pos = idx.get_indexer(df["neighbor_id"].astype(str))
    mask = (q_pos >= 0) & (n_pos >= 0)
    q_pos = q_pos[mask].astype(int, copy=False)
    n_pos = n_pos[mask].astype(int, copy=False)

    if len(q_pos) == 0:
        return pd.DataFrame(
            [
                {
                    "label_col": label_col,
                    "n_pairs": 0,
                    "observed_match_rate": np.nan,
                    "perm_mean": np.nan,
                    "perm_std": np.nan,
                    "p_value": np.nan,
                }
            ]
        )

    perm_scores = np.empty(int(n_permutations), dtype=float)
    for i in range(int(n_permutations)):
        perm = rng.permutation(labels)
        perm_scores[i] = float(np.mean(perm[q_pos] == perm[n_pos]))

    perm_mean = float(np.mean(perm_scores))
    perm_std = float(np.std(perm_scores, ddof=0))
    # one-sided: enrichment means observed > permuted
    p_value = float((np.sum(perm_scores >= obs) + 1.0) / (len(perm_scores) + 1.0))

    return pd.DataFrame(
        [
            {
                "label_col": label_col,
                "n_pairs": n_pairs,
                "observed_match_rate": obs,
                "perm_mean": perm_mean,
                "perm_std": perm_std,
                "p_value": p_value,
                "n_permutations": int(n_permutations),
            }
        ]
    )

