from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _ensure_out(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def savefig(fig: plt.Figure, path: str | Path, *, dpi: int = 150) -> Path:
    """
    Save a matplotlib figure, creating parent dirs, and close it.
    Returns the saved path.
    """
    p = _ensure_out(path)
    fig.savefig(p, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return p


def _to_frame(x: pd.DataFrame | np.ndarray, *, index: Optional[Iterable[str]] = None) -> pd.DataFrame:
    if isinstance(x, pd.DataFrame):
        return x
    arr = np.asarray(x, dtype=float)
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D array, got shape {arr.shape}")
    if index is None:
        index = [str(i) for i in range(arr.shape[0])]
    return pd.DataFrame(arr, index=pd.Index(list(index), dtype=str))


def _aligned_labels(embedding_index: pd.Index, labels: Optional[pd.Series]) -> Optional[pd.Series]:
    if labels is None:
        return None
    if not isinstance(labels, pd.Series):
        labels = pd.Series(labels)  # type: ignore[arg-type]
    return labels.reindex(embedding_index)


def plot_umap(
    embedding: pd.DataFrame | np.ndarray,
    labels: Optional[pd.Series] = None,
    title: Optional[str] = None,
    *,
    out_path: str | Path | None = None,
    random_state: int = 1337,
    n_neighbors: int = 15,
    min_dist: float = 0.1,
    point_size: float = 10.0,
    alpha: float = 0.8,
    dpi: int = 150,
) -> plt.Figure:
    """
    UMAP projection of an embedding table (rows = items).
    If labels are provided, points are colored and a legend is shown.
    """
    try:
        import umap  # type: ignore
    except Exception as e:  # pragma: no cover
        raise ImportError("UMAP requires `umap-learn` to be installed.") from e

    emb = _to_frame(embedding)
    if emb.shape[0] < 2:
        raise ValueError("Need at least 2 rows to plot.")

    reducer = umap.UMAP(
        random_state=random_state,
        n_neighbors=min(int(n_neighbors), max(2, emb.shape[0] - 1)),
        min_dist=float(min_dist),
    )
    coords = reducer.fit_transform(emb.to_numpy(dtype=float, copy=False))

    fig, ax = plt.subplots(figsize=(6, 5), dpi=dpi)
    lab = _aligned_labels(emb.index, labels)
    if lab is None:
        ax.scatter(coords[:, 0], coords[:, 1], s=point_size, alpha=alpha)
    else:
        lab_str = lab.astype("string").fillna("NA")
        uniq = list(pd.unique(lab_str))
        cmap = plt.get_cmap("tab20", max(1, len(uniq)))
        for i, k in enumerate(uniq):
            mask = (lab_str == k).to_numpy()
            ax.scatter(
                coords[mask, 0],
                coords[mask, 1],
                s=point_size,
                alpha=alpha,
                label=str(k),
                color=cmap(i),
            )
        ax.legend(markerscale=2, fontsize=8, frameon=False, ncol=1)
    ax.set_xlabel("UMAP1")
    ax.set_ylabel("UMAP2")
    if title:
        ax.set_title(title)
    fig.tight_layout()
    if out_path is not None:
        savefig(fig, out_path, dpi=dpi)
    return fig


def plot_pca_scatter(
    embedding: pd.DataFrame | np.ndarray,
    labels: Optional[pd.Series] = None,
    title: Optional[str] = None,
    *,
    out_path: str | Path | None = None,
    random_state: int = 1337,
    point_size: float = 10.0,
    alpha: float = 0.8,
    dpi: int = 150,
) -> plt.Figure:
    from sklearn.decomposition import PCA

    emb = _to_frame(embedding)
    if emb.shape[0] < 2:
        raise ValueError("Need at least 2 rows to plot.")

    coords = PCA(n_components=2, random_state=random_state).fit_transform(emb.to_numpy(dtype=float, copy=False))
    fig, ax = plt.subplots(figsize=(6, 5), dpi=dpi)

    lab = _aligned_labels(emb.index, labels)
    if lab is None:
        ax.scatter(coords[:, 0], coords[:, 1], s=point_size, alpha=alpha)
    else:
        lab_str = lab.astype("string").fillna("NA")
        uniq = list(pd.unique(lab_str))
        cmap = plt.get_cmap("tab20", max(1, len(uniq)))
        for i, k in enumerate(uniq):
            mask = (lab_str == k).to_numpy()
            ax.scatter(
                coords[mask, 0],
                coords[mask, 1],
                s=point_size,
                alpha=alpha,
                label=str(k),
                color=cmap(i),
            )
        ax.legend(markerscale=2, fontsize=8, frameon=False, ncol=1)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    if title:
        ax.set_title(title)
    fig.tight_layout()
    if out_path is not None:
        savefig(fig, out_path, dpi=dpi)
    return fig


def plot_reconstruction_curve(
    summary_df: pd.DataFrame,
    title: str = "Reconstruction error vs k",
    *,
    out_path: str | Path | None = None,
    dpi: int = 150,
    show_explained_variance: bool = True,
) -> plt.Figure:
    """
    Plot reconstruction error vs k, grouped by model.
    If `explained_variance` exists (SVD), can also overlay it on a secondary axis.
    """
    need = {"model", "k", "reconstruction_error"}
    missing = need - set(summary_df.columns)
    if missing:
        raise ValueError(f"summary_df missing columns: {sorted(missing)}")

    fig, ax = plt.subplots(figsize=(6, 4), dpi=dpi)
    for model, dfm in summary_df.groupby("model", sort=True):
        dfm = dfm.sort_values("k")
        ax.plot(dfm["k"], dfm["reconstruction_error"], marker="o", label=str(model))
    ax.set_xlabel("k")
    ax.set_ylabel("RMSE")
    ax.set_title(title)
    ax.legend(frameon=False)

    if show_explained_variance and "explained_variance" in summary_df.columns:
        df_ev = summary_df.copy()
        df_ev = df_ev[df_ev["explained_variance"].notna()]
        if len(df_ev):
            ax2 = ax.twinx()
            for model, dfm in df_ev.groupby("model", sort=True):
                dfm = dfm.sort_values("k")
                ax2.plot(
                    dfm["k"],
                    dfm["explained_variance"],
                    marker="s",
                    linestyle="--",
                    alpha=0.7,
                    label=f"{model} explained var",
                )
            ax2.set_ylabel("Explained variance (sum)")
    fig.tight_layout()
    if out_path is not None:
        savefig(fig, out_path, dpi=dpi)
    return fig


def plot_heatmap_reordered(
    matrix: pd.DataFrame,
    row_order: Sequence[str],
    col_order: Sequence[str],
    title: Optional[str] = None,
    *,
    out_path: str | Path | None = None,
    cmap: str = "coolwarm",
    robust: bool = True,
    vmin: float | None = None,
    vmax: float | None = None,
    show_ticks: bool = False,
    dpi: int = 150,
) -> plt.Figure:
    """
    Heatmap of matrix reordered by provided row/col lists.
    Designed for large matrices (ticks off by default).
    """
    mat_df = matrix.loc[list(row_order), list(col_order)]
    mat = mat_df.to_numpy(dtype=float, copy=False)
    fig, ax = plt.subplots(figsize=(8, 6), dpi=dpi)

    vvmin = vmin
    vvmax = vmax
    if robust and (vvmin is None or vvmax is None):
        finite = mat[np.isfinite(mat)]
        if finite.size:
            lo, hi = np.percentile(finite, [2, 98])
            vvmin = lo if vvmin is None else vvmin
            vvmax = hi if vvmax is None else vvmax

    im = ax.imshow(mat, aspect="auto", interpolation="nearest", cmap=cmap, vmin=vvmin, vmax=vvmax)
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.ax.set_ylabel("value", rotation=90)

    ax.set_xlabel("Cells")
    ax.set_ylabel("Drugs")
    if title:
        ax.set_title(title)

    if show_ticks:
        ax.set_xticks(np.arange(len(mat_df.columns)))
        ax.set_xticklabels(mat_df.columns.astype(str), rotation=90, fontsize=6)
        ax.set_yticks(np.arange(len(mat_df.index)))
        ax.set_yticklabels(mat_df.index.astype(str), fontsize=6)
    else:
        ax.set_xticks([])
        ax.set_yticks([])

    fig.tight_layout()
    if out_path is not None:
        savefig(fig, out_path, dpi=dpi)
    return fig


def plot_latent_factor_loadings(
    loadings: pd.DataFrame,
    title: Optional[str] = None,
    *,
    factor: str | None = None,
    top_n: int = 20,
    out_path: str | Path | None = None,
    dpi: int = 150,
) -> plt.Figure:
    """
    Visualize latent factor loadings.

    Expected shapes:
    - features×factors: index are features (e.g. drugs), columns are factors
    - OR factors×features (will be auto-transposed if it looks that way)
    """
    df = loadings.copy()
    if df.shape[0] < df.shape[1] and all(str(c).lower().startswith(("svd_", "nmf_")) for c in df.index.astype(str)):
        df = df.T

    if factor is None:
        # Summary: mean absolute loading per factor
        fig, ax = plt.subplots(figsize=(7, 4), dpi=dpi)
        df.abs().mean(axis=0).sort_values(ascending=False).plot(kind="bar", ax=ax)
        ax.set_ylabel("Mean |loading|")
        if title:
            ax.set_title(title)
        fig.tight_layout()
        if out_path is not None:
            savefig(fig, out_path, dpi=dpi)
        return fig

    if factor not in df.columns:
        raise ValueError(f"factor '{factor}' not found in columns.")

    s = df[factor].astype(float)
    s = s.reindex(s.abs().sort_values(ascending=False).head(int(top_n)).index)
    fig, ax = plt.subplots(figsize=(7, max(3.5, 0.22 * len(s))), dpi=dpi)
    s.iloc[::-1].plot(kind="barh", ax=ax)
    ax.set_xlabel("loading")
    ax.set_ylabel("feature")
    ax.axvline(0.0, color="k", linewidth=0.8, alpha=0.6)
    ax.set_title(title or f"Top loadings: {factor}")
    fig.tight_layout()
    if out_path is not None:
        savefig(fig, out_path, dpi=dpi)
    return fig

