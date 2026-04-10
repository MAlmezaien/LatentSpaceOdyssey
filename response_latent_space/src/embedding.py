from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.decomposition import NMF, TruncatedSVD


@dataclass
class EmbeddingResult:
    model: str
    k: int
    drug_embedding: pd.DataFrame
    cell_embedding: pd.DataFrame
    reconstructed: pd.DataFrame
    reconstruction_error: float
    explained_variance_ratio_sum: Optional[float]
    notes: str = ""


def _to_matrix(df: pd.DataFrame) -> np.ndarray:
    x = df.astype(float).to_numpy()
    if not np.isfinite(x).all():
        raise ValueError("Embedding input contains NaN/Inf; impute before embedding.")
    return x


def run_svd_embedding(
    matrix: pd.DataFrame, n_components: int, random_state: int
) -> Tuple[pd.DataFrame, pd.DataFrame, float, pd.DataFrame, float]:
    """
    SVD via TruncatedSVD.

    Returns:
      - drug_embedding (rows=drugs)
      - cell_embedding (rows=cells)
      - explained_variance_ratio_sum
      - reconstructed (drug×cell)
      - reconstruction_error (RMSE)
    """
    X = _to_matrix(matrix)
    svd = TruncatedSVD(n_components=n_components, random_state=random_state)
    U_S = svd.fit_transform(X)  # (n_drugs, k) corresponds to U @ S
    V = svd.components_.T  # (n_cells, k)
    S = np.diag(svd.singular_values_)
    V_S = V @ S  # (n_cells, k) corresponds to V @ S

    X_hat = svd.inverse_transform(U_S)
    rmse = float(np.sqrt(np.mean((X - X_hat) ** 2)))

    drug_emb = pd.DataFrame(U_S, index=matrix.index, columns=[f"svd_{i+1}" for i in range(n_components)])
    cell_emb = pd.DataFrame(V_S, index=matrix.columns, columns=[f"svd_{i+1}" for i in range(n_components)])
    recon = pd.DataFrame(X_hat, index=matrix.index, columns=matrix.columns)
    ev = float(np.sum(svd.explained_variance_ratio_))
    return drug_emb, cell_emb, ev, recon, rmse


def run_nmf_embedding(
    matrix: pd.DataFrame, n_components: int, random_state: int, *, max_iter: int = 2000, tol: float = 1e-4
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, float, Dict[str, float]]:
    """
    NMF (non-negative). If input has negatives, we shift it to be non-negative.

    Returns:
      - drug_embedding W (rows=drugs)
      - cell_embedding H^T (rows=cells)
      - reconstructed W @ H
      - reconstruction_error (RMSE)
      - notes dict (e.g. shift applied)
    """
    X = _to_matrix(matrix)
    notes: Dict[str, float] = {}
    min_val = float(X.min())
    shift = 0.0
    if min_val < 0:
        shift = -min_val
        X = X + shift
        notes["shift_applied"] = shift

    nmf = NMF(
        n_components=n_components,
        init="nndsvda",
        random_state=random_state,
        max_iter=max_iter,
        tol=tol,
    )
    W = nmf.fit_transform(X)  # (n_drugs, k)
    H = nmf.components_  # (k, n_cells)
    X_hat = W @ H
    rmse = float(np.sqrt(np.mean((X - X_hat) ** 2)))

    drug_emb = pd.DataFrame(W, index=matrix.index, columns=[f"nmf_{i+1}" for i in range(n_components)])
    cell_emb = pd.DataFrame(H.T, index=matrix.columns, columns=[f"nmf_{i+1}" for i in range(n_components)])
    recon = pd.DataFrame(X_hat - shift, index=matrix.index, columns=matrix.columns) if shift != 0 else pd.DataFrame(
        X_hat, index=matrix.index, columns=matrix.columns
    )
    return drug_emb, cell_emb, recon, rmse, notes

