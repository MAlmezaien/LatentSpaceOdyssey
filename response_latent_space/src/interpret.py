from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd


def find_marker_drugs_for_cell_clusters(
    response_matrix: pd.DataFrame, cell_clusters: pd.Series, top_n: int = 20
) -> pd.DataFrame:
    """
    Simple marker-drug heuristic: for each cell cluster, rank drugs by mean sensitivity in that cluster.

    response_matrix: drugs×cells
    cell_clusters: cluster label per cell (index must match response_matrix columns)
    """
    clusters = cell_clusters.loc[response_matrix.columns].astype(str)
    rows = []
    for clust, cells in clusters.groupby(clusters).groups.items():
        sub = response_matrix.loc[:, list(cells)]
        scores = sub.mean(axis=1).sort_values(ascending=False)
        for rank, (drug, score) in enumerate(scores.head(top_n).items(), start=1):
            rows.append({"cluster": clust, "rank": rank, "drug_id": str(drug), "mean_score": float(score)})
    return pd.DataFrame(rows)


def rank_drug_associations_with_cell_factor(
    cell_embedding: pd.DataFrame, response_matrix: pd.DataFrame, *, min_cells: int = 3
) -> pd.DataFrame:
    """
    Rank drugs by correlation with each cell latent factor.

    cell_embedding: cells×k
    response_matrix: drugs×cells
    """
    emb = cell_embedding.loc[response_matrix.columns].astype(float)
    y = response_matrix.astype(float)

    rows: List[Dict[str, object]] = []
    for factor in emb.columns:
        v = emb[factor].to_numpy()
        v = (v - v.mean()) / (v.std(ddof=0) + 1e-12)

        for drug in y.index.astype(str):
            r = y.loc[drug].to_numpy()
            r = (r - np.nanmean(r)) / (np.nanstd(r) + 1e-12)
            mask = np.isfinite(r)
            if int(mask.sum()) < int(min_cells):
                corr = np.nan
            else:
                corr = float(np.corrcoef(v[mask], r[mask])[0, 1])
            rows.append({"factor": str(factor), "drug_id": str(drug), "corr": corr})

    out = pd.DataFrame(rows)
    return out.sort_values(["factor", "corr"], ascending=[True, False])


def top_associations_per_factor(
    associations: pd.DataFrame, *, top_n: int = 200, factor_col: str = "factor", score_col: str = "corr"
) -> pd.DataFrame:
    """
    Convenience helper to keep files small: keep the top-N rows per factor by |score|.
    """
    if associations.empty:
        return associations
    df = associations.copy()
    if factor_col not in df.columns or score_col not in df.columns:
        raise ValueError(f"associations must contain columns: {factor_col!r}, {score_col!r}")
    df[score_col] = pd.to_numeric(df[score_col], errors="coerce")
    df["_abs_score"] = df[score_col].abs()
    df = df.sort_values([factor_col, "_abs_score"], ascending=[True, False])
    df = df.groupby(factor_col, sort=False, as_index=False).head(int(top_n))
    return df.drop(columns=["_abs_score"])


def summarize_drug_neighbors(drug_neighbors: pd.DataFrame, drug_metadata: pd.DataFrame) -> pd.DataFrame:
    """
    Join neighbor table with metadata for query + neighbor.
    Expects columns: query_id, neighbor_id, neighbor_rank, distance
    """
    md = drug_metadata.copy()
    if "drug_id" not in md.columns:
        return drug_neighbors

    md["drug_id"] = md["drug_id"].astype(str)
    q = md.add_prefix("query_")
    n = md.add_prefix("neighbor_")

    out = drug_neighbors.copy()
    out["query_id"] = out["query_id"].astype(str)
    out["neighbor_id"] = out["neighbor_id"].astype(str)
    out = out.merge(q, left_on="query_id", right_on="query_drug_id", how="left")
    out = out.merge(n, left_on="neighbor_id", right_on="neighbor_drug_id", how="left")
    return out


def cluster_level_sensitivity_summary(
    response_matrix: pd.DataFrame, cell_clusters: pd.Series
) -> pd.DataFrame:
    clusters = cell_clusters.loc[response_matrix.columns].astype(str)
    rows = []
    for clust, cells in clusters.groupby(clusters).groups.items():
        sub = response_matrix.loc[:, list(cells)]
        rows.append(
            {
                "cluster": clust,
                "n_cells": int(len(cells)),
                "mean_sensitivity_overall": float(sub.to_numpy(dtype=float).mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("cluster")

