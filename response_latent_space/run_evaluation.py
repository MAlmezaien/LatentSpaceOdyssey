from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import yaml

from src.clustering import run_kmeans
from src.evaluation import (
    bootstrap_against_reference_labels,
    compute_silhouette_score,
    neighbor_label_enrichment,
    nearest_neighbor_table,
)
from src.interpret import (
    cluster_level_sensitivity_summary,
    find_marker_drugs_for_cell_clusters,
    rank_drug_associations_with_cell_factor,
    summarize_drug_neighbors,
    top_associations_per_factor,
)
from src.io_utils import load_cell_metadata, load_drug_metadata, load_response_matrix, save_dataframe
from src.plotting import plot_pca_scatter, plot_reconstruction_curve, plot_umap
from src.repo_paths import as_repo_relative


def load_config(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _list_embedding_runs(embeddings_root: Path) -> List[Tuple[str, int, Path]]:
    runs: List[Tuple[str, int, Path]] = []
    for child in embeddings_root.iterdir():
        if not child.is_dir():
            continue
        name = child.name.lower()
        if name.startswith("svd_k"):
            runs.append(("SVD", int(name.replace("svd_k", "")), child))
        elif name.startswith("nmf_k"):
            runs.append(("NMF", int(name.replace("nmf_k", "")), child))
    return sorted(runs, key=lambda x: (x[0], x[1]))


def main() -> None:
    base = Path(__file__).resolve().parent
    repo_root = base.parent
    cfg = load_config(base / "configs" / "default.yaml")

    paths = cfg["paths"]
    preprocess_cfg = cfg.get("preprocess", {})
    clustering_cfg = cfg.get("clustering", {})
    plotting_cfg = cfg.get("plotting", {})

    random_state = int(preprocess_cfg.get("random_seed", 1337))
    n_clusters_list = list(map(int, clustering_cfg.get("n_clusters", [2, 3, 4, 5, 6, 7, 8])))
    kmeans_cfg = clustering_cfg.get("kmeans", {})
    stability_cfg = clustering_cfg.get("stability", {})
    enrichment_cfg = clustering_cfg.get("enrichment", {})
    umap_cfg = plotting_cfg.get("umap", {})

    proc_path = base / paths["out_processed_dir"] / "processed_response_matrix.csv"
    response = load_response_matrix(proc_path, index_col=0)  # drugs×cells

    embeddings_root = base / paths["out_embeddings_dir"]
    runs = _list_embedding_runs(embeddings_root)
    if not runs:
        raise FileNotFoundError(f"No embedding runs found under: {embeddings_root}")

    out_cluster = base / paths["out_clustering_dir"]
    out_interp = base / paths["out_interpretation_dir"]
    out_fig = base / paths["out_figures_dir"]
    out_cluster.mkdir(parents=True, exist_ok=True)
    out_interp.mkdir(parents=True, exist_ok=True)
    out_fig.mkdir(parents=True, exist_ok=True)

    drug_md = None
    drug_md_path = base / paths["drug_metadata"]
    if drug_md_path.exists():
        drug_md = load_drug_metadata(drug_md_path)

    cell_md = None
    cell_md_path = base / paths.get("cell_metadata", "")
    if cell_md_path and cell_md_path.exists():
        cell_md = load_cell_metadata(cell_md_path)

    # Figures: reconstruction curve (if embedding summary exists)
    emb_summary_path = embeddings_root / "embedding_summary.csv"
    if emb_summary_path.exists():
        try:
            emb_summary = pd.read_csv(emb_summary_path)
            plot_reconstruction_curve(
                emb_summary,
                out_path=out_fig / "reconstruction_curve.png",
            )
        except Exception:
            # non-fatal: keep runner robust even if summary format changed
            pass

    master_rows: List[Dict[str, Any]] = []
    combined_cell_assign_rows: List[Dict[str, Any]] = []
    combined_drug_assign_rows: List[Dict[str, Any]] = []
    combined_marker_rows: List[pd.DataFrame] = []
    combined_cell_stab_rows: List[pd.DataFrame] = []
    combined_cluster_summ_rows: List[pd.DataFrame] = []

    for model, k, run_dir in runs:
        cell_emb = load_response_matrix(run_dir / "cell_embedding.csv", index_col=0)  # cells×k
        drug_emb = load_response_matrix(run_dir / "drug_embedding.csv", index_col=0)  # drugs×k

        # Embedding figures (unlabeled)
        try:
            plot_umap(
                cell_emb,
                title=f"Cells UMAP ({model} k={k})",
                out_path=out_fig / f"umap_cells_{model.lower()}_k{k}.png",
                random_state=random_state,
                n_neighbors=int(umap_cfg.get("n_neighbors", 15)),
                min_dist=float(umap_cfg.get("min_dist", 0.1)),
            )
            plot_umap(
                drug_emb,
                title=f"Drugs UMAP ({model} k={k})",
                out_path=out_fig / f"umap_drugs_{model.lower()}_k{k}.png",
                random_state=random_state,
                n_neighbors=int(umap_cfg.get("n_neighbors", 15)),
                min_dist=float(umap_cfg.get("min_dist", 0.1)),
            )
            plot_pca_scatter(
                cell_emb,
                title=f"Cells PCA ({model} k={k})",
                out_path=out_fig / f"pca_cells_{model.lower()}_k{k}.png",
                random_state=random_state,
            )
            plot_pca_scatter(
                drug_emb,
                title=f"Drugs PCA ({model} k={k})",
                out_path=out_fig / f"pca_drugs_{model.lower()}_k{k}.png",
                random_state=random_state,
            )
        except Exception:
            # plotting should not break the evaluation tables
            pass

        for n_clusters in n_clusters_list:
            # Cells
            cell_labels = run_kmeans(
                cell_emb,
                n_clusters=n_clusters,
                random_state=random_state,
                n_init=int(kmeans_cfg.get("n_init", 20)),
            )
            cell_sil = compute_silhouette_score(cell_emb, cell_labels)
            cell_assign_path = out_cluster / f"cell_clusters_{model.lower()}_k{k}_c{n_clusters}.csv"
            save_dataframe(cell_labels.to_frame("cluster"), cell_assign_path, index=True)
            for cell_id, cl in cell_labels.astype(int).items():
                combined_cell_assign_rows.append(
                    {
                        "model": model,
                        "k": int(k),
                        "n_clusters": int(n_clusters),
                        "cell_id": str(cell_id),
                        "cluster": int(cl),
                    }
                )

            # Cell cluster stability: bootstrap-recluster subsets and compare to full labels (ARI)
            stability = bootstrap_against_reference_labels(
                cell_emb,
                cluster_fn=lambda sub: run_kmeans(
                    sub,
                    n_clusters=n_clusters,
                    random_state=random_state,
                    n_init=int(kmeans_cfg.get("n_init", 20)),
                ),
                reference_labels=cell_labels,
                n_bootstrap=int(stability_cfg.get("n_bootstrap", 50)),
                sample_frac=float(stability_cfg.get("sample_frac", 0.8)),
                random_state=random_state,
            )
            stab_path = out_cluster / f"cell_cluster_stability_{model.lower()}_k{k}_c{n_clusters}.csv"
            save_dataframe(stability, stab_path, index=False)
            if len(stability):
                stab2 = stability.copy()
                stab2.insert(0, "n_clusters", int(n_clusters))
                stab2.insert(0, "k", int(k))
                stab2.insert(0, "model", model)
                combined_cell_stab_rows.append(stab2)

            # Drugs
            drug_labels = run_kmeans(
                drug_emb,
                n_clusters=n_clusters,
                random_state=random_state,
                n_init=int(kmeans_cfg.get("n_init", 20)),
            )
            drug_sil = compute_silhouette_score(drug_emb, drug_labels)
            drug_assign_path = out_cluster / f"drug_clusters_{model.lower()}_k{k}_c{n_clusters}.csv"
            save_dataframe(drug_labels.to_frame("cluster"), drug_assign_path, index=True)
            for drug_id, cl in drug_labels.astype(int).items():
                combined_drug_assign_rows.append(
                    {
                        "model": model,
                        "k": int(k),
                        "n_clusters": int(n_clusters),
                        "drug_id": str(drug_id),
                        "cluster": int(cl),
                    }
                )

            # Interpretation artifacts (cells)
            markers = find_marker_drugs_for_cell_clusters(response, cell_labels, top_n=20)
            markers2 = markers.copy()
            markers2.insert(0, "n_clusters", int(n_clusters))
            markers2.insert(0, "k", int(k))
            markers2.insert(0, "model", model)
            combined_marker_rows.append(markers2)
            marker_path = out_interp / f"cell_cluster_marker_drugs_{model.lower()}_k{k}_c{n_clusters}.csv"
            save_dataframe(markers, marker_path, index=False)

            # Cluster-level sensitivity summaries
            cl_summ = cluster_level_sensitivity_summary(response, cell_labels)
            cl_summ.insert(0, "n_clusters", int(n_clusters))
            cl_summ.insert(0, "k", int(k))
            cl_summ.insert(0, "model", model)
            combined_cluster_summ_rows.append(cl_summ)
            save_dataframe(
                cl_summ,
                out_interp / f"cell_cluster_sensitivity_summary_{model.lower()}_k{k}_c{n_clusters}.csv",
                index=False,
            )

            # Cluster-labeled UMAPs (optional, non-fatal)
            try:
                plot_umap(
                    cell_emb,
                    labels=cell_labels.astype(str),
                    title=f"Cells UMAP ({model} k={k}, c={n_clusters})",
                    out_path=out_fig / f"umap_cells_{model.lower()}_k{k}_c{n_clusters}.png",
                    random_state=random_state,
                    n_neighbors=int(umap_cfg.get("n_neighbors", 15)),
                    min_dist=float(umap_cfg.get("min_dist", 0.1)),
                )
                plot_umap(
                    drug_emb,
                    labels=drug_labels.astype(str),
                    title=f"Drugs UMAP ({model} k={k}, c={n_clusters})",
                    out_path=out_fig / f"umap_drugs_{model.lower()}_k{k}_c{n_clusters}.png",
                    random_state=random_state,
                    n_neighbors=int(umap_cfg.get("n_neighbors", 15)),
                    min_dist=float(umap_cfg.get("min_dist", 0.1)),
                )
            except Exception:
                pass

            master_rows.append(
                {
                    "model": model,
                    "k": k,
                    "n_clusters": n_clusters,
                    "cell_silhouette": cell_sil,
                    "drug_silhouette": drug_sil,
                    "cell_stability_ari_mean": float(stability["ari"].mean()) if len(stability) else float("nan"),
                    "cell_stability_ari_median": float(stability["ari"].median()) if len(stability) else float("nan"),
                    "cell_clusters_path": as_repo_relative(cell_assign_path, repo_root),
                    "drug_clusters_path": as_repo_relative(drug_assign_path, repo_root),
                    "cell_stability_path": as_repo_relative(stab_path, repo_root),
                    "marker_drugs_path": as_repo_relative(marker_path, repo_root),
                }
            )

        # Drug nearest-neighbors (per run, independent of n_clusters)
        nn = nearest_neighbor_table(drug_emb, n_neighbors=10)
        if drug_md is not None:
            nn = summarize_drug_neighbors(nn, drug_md)
        nn_path = out_interp / f"drug_nearest_neighbors_{model.lower()}_k{k}.csv"
        save_dataframe(nn, nn_path, index=False)

        # Cell-factor associations (per run)
        assoc = rank_drug_associations_with_cell_factor(cell_emb, response)
        assoc_top = top_associations_per_factor(assoc, top_n=200)
        save_dataframe(assoc_top, out_interp / f"cell_factor_drug_associations_{model.lower()}_k{k}_top200.csv", index=False)

        # Neighbor-label enrichment (if metadata available)
        if drug_md is not None and "drug_id" in drug_md.columns:
            for label_col in ["moa", "target", "moal_community"]:
                if label_col not in drug_md.columns:
                    continue
                enr = neighbor_label_enrichment(
                    neighbor_table=nearest_neighbor_table(drug_emb, n_neighbors=10),
                    metadata=drug_md,
                    id_col="drug_id",
                    label_col=label_col,
                    n_permutations=int(enrichment_cfg.get("n_permutations", 1000)),
                    random_state=random_state,
                )
                enr_path = out_interp / f"drug_neighbor_enrichment_{label_col}_{model.lower()}_k{k}.csv"
                save_dataframe(enr, enr_path, index=False)

    master = pd.DataFrame(master_rows)
    master_path = out_interp / "master_stage1_summary.csv"
    save_dataframe(master, master_path, index=False)

    # Consolidated deliverables (single-file outputs)
    if combined_cell_assign_rows:
        cell_assign_all = pd.DataFrame(combined_cell_assign_rows)
        save_dataframe(cell_assign_all, out_cluster / "cell_cluster_assignments.csv", index=False)
    if combined_drug_assign_rows:
        drug_assign_all = pd.DataFrame(combined_drug_assign_rows)
        save_dataframe(drug_assign_all, out_cluster / "drug_cluster_assignments.csv", index=False)
    if combined_marker_rows:
        save_dataframe(pd.concat(combined_marker_rows, ignore_index=True), out_interp / "cell_cluster_marker_drugs.csv", index=False)
    if combined_cell_stab_rows:
        save_dataframe(
            pd.concat(combined_cell_stab_rows, ignore_index=True),
            out_cluster / "cell_cluster_stability_all.csv",
            index=False,
        )
    if combined_cluster_summ_rows:
        save_dataframe(
            pd.concat(combined_cluster_summ_rows, ignore_index=True),
            out_interp / "cell_cluster_sensitivity_summary_all.csv",
            index=False,
        )

    # Write a lightweight interpretation summary markdown
    try:
        best_rmse_row = None
        if emb_summary_path.exists():
            emb_summary = pd.read_csv(emb_summary_path)
            emb_summary["reconstruction_error"] = pd.to_numeric(emb_summary["reconstruction_error"], errors="coerce")
            if emb_summary["reconstruction_error"].notna().any():
                best_rmse_row = emb_summary.sort_values("reconstruction_error").iloc[0].to_dict()

        best_stab_row = None
        if len(master):
            best_stab = master.copy()
            best_stab["cell_stability_ari_mean"] = pd.to_numeric(best_stab["cell_stability_ari_mean"], errors="coerce")
            if best_stab["cell_stability_ari_mean"].notna().any():
                best_stab_row = best_stab.sort_values("cell_stability_ari_mean", ascending=False).iloc[0].to_dict()

        lines: List[str] = []
        lines.append("# Stage-1 embedding interpretation summary\n")
        lines.append("## Preprocessing\n")
        lines.append(f"- Random seed: `{random_state}`\n")
        lines.append("\n## Embedding quality\n")
        if best_rmse_row is not None:
            lines.append(
                f"- Best reconstruction error (RMSE): **{best_rmse_row['reconstruction_error']:.4f}** "
                f"({best_rmse_row.get('model')} k={best_rmse_row.get('k')})\n"
            )
        else:
            lines.append("- Best reconstruction error (RMSE): (not available)\n")

        lines.append("\n## Clustering stability (cells)\n")
        if best_stab_row is not None:
            lines.append(
                f"- Best mean ARI vs bootstrap subsets: **{float(best_stab_row['cell_stability_ari_mean']):.3f}** "
                f"({best_stab_row.get('model')} k={best_stab_row.get('k')}, c={best_stab_row.get('n_clusters')})\n"
            )
        else:
            lines.append("- Best mean ARI: (not available)\n")

        lines.append("\n## Key outputs\n")
        lines.append(f"- Master summary: `{as_repo_relative(master_path, repo_root)}`\n")
        lines.append(
            f"- Cell cluster assignments: `{as_repo_relative(out_cluster / 'cell_cluster_assignments.csv', repo_root)}`\n"
        )
        lines.append(
            f"- Drug cluster assignments: `{as_repo_relative(out_cluster / 'drug_cluster_assignments.csv', repo_root)}`\n"
        )
        lines.append(
            f"- Marker drugs: `{as_repo_relative(out_interp / 'cell_cluster_marker_drugs.csv', repo_root)}`\n"
        )
        lines.append(f"- Drug neighbors: `{as_repo_relative(out_interp, repo_root)}` (see `drug_nearest_neighbors_*`)\n")
        lines.append(f"- Figures: `{as_repo_relative(out_fig, repo_root)}`\n")

        (out_interp / "embedding_interpretation_summary.md").write_text("".join(lines), encoding="utf-8")
    except Exception:
        pass

    print("Evaluation complete.")
    print(f"Wrote clustering to: {out_cluster}")
    print(f"Wrote interpretation to: {out_interp}")
    print(f"Wrote master summary: {master_path}")


if __name__ == "__main__":
    main()
