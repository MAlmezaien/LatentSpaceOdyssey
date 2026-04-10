from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.cluster import AgglomerativeClustering


def run_kmeans(embedding: pd.DataFrame, n_clusters: int, random_state: int, *, n_init: int = 20) -> pd.Series:
    x = embedding.to_numpy(dtype=float)
    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=n_init)
    labels = km.fit_predict(x)
    return pd.Series(labels, index=embedding.index, name="cluster")


def run_hierarchical(
    embedding: pd.DataFrame,
    n_clusters: int,
    *,
    linkage: str = "ward",
    metric: Optional[str] = None,
) -> pd.Series:
    x = embedding.to_numpy(dtype=float)
    # sklearn: for linkage='ward', metric must be euclidean (metric arg is ignored/unsupported in older versions)
    if linkage == "ward":
        model = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage)
    else:
        # Newer sklearn uses `metric=...`; older uses `affinity=...`. We try metric first, then fallback.
        if metric is None:
            metric = "euclidean"
        try:
            model = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage, metric=metric)
        except TypeError:
            model = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage, affinity=metric)  # type: ignore[arg-type]
    labels = model.fit_predict(x)
    return pd.Series(labels, index=embedding.index, name="cluster")


def build_knn_graph(embedding: pd.DataFrame, n_neighbors: int) -> pd.DataFrame:
    """
    Placeholder for stage-2/Leiden: returns kNN edges (i, j, dist).
    """
    from sklearn.neighbors import NearestNeighbors

    x = embedding.to_numpy(dtype=float)
    nn = NearestNeighbors(n_neighbors=min(n_neighbors + 1, x.shape[0]), metric="euclidean")
    nn.fit(x)
    dists, idx = nn.kneighbors(x)

    edges = []
    ids = embedding.index.astype(str).to_list()
    for row_i, (nbrs, ds) in enumerate(zip(idx, dists)):
        for j, dist in zip(nbrs[1:], ds[1:]):  # skip self
            edges.append((ids[row_i], ids[int(j)], float(dist)))
    return pd.DataFrame(edges, columns=["i", "j", "dist"])

