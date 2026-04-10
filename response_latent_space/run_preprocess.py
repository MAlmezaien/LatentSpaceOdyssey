from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from src.io_utils import (
    load_cell_metadata,
    load_drug_metadata,
    load_response_matrix,
    save_dataframe,
    validate_matrix_and_metadata,
)
from src.preprocess import run_preprocess_pipeline


def load_config(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    base = Path(__file__).resolve().parent
    cfg = load_config(base / "configs" / "default.yaml")

    paths = cfg["paths"]
    matrix_cfg = cfg.get("matrix", {})
    preprocess_cfg = cfg.get("preprocess", {})

    response_path = base / paths["response_matrix"]
    response = load_response_matrix(response_path, index_col=matrix_cfg.get("index_col", 0))
    if matrix_cfg.get("transpose", False):
        response = response.T

    drug_md = None
    cell_md = None
    if (base / paths["drug_metadata"]).exists():
        drug_md = load_drug_metadata(base / paths["drug_metadata"])
    if (base / paths["cell_metadata"]).exists():
        cell_md = load_cell_metadata(base / paths["cell_metadata"])

    report = validate_matrix_and_metadata(response, drug_md, cell_md)

    artifacts = run_preprocess_pipeline(
        response,
        do_log_transform=bool(preprocess_cfg.get("do_log_transform", True)),
        convert_to_sensitivity_flag=bool(preprocess_cfg.get("convert_to_sensitivity", True)),
        max_missing_drug=float(preprocess_cfg.get("max_missing_drug", 0.2)),
        max_missing_cell=float(preprocess_cfg.get("max_missing_cell", 0.2)),
        impute_method=str(preprocess_cfg.get("impute_method", "drug_median")),
        low_variance_threshold=float(preprocess_cfg.get("low_variance_threshold", 1e-8)),
        do_zscore_per_drug=bool(preprocess_cfg.get("zscore_per_drug", True)),
    )

    out_proc = base / paths["out_processed_dir"]
    out_proc.mkdir(parents=True, exist_ok=True)

    save_dataframe(artifacts.raw, out_proc / "raw_response_matrix.csv", index=True)
    if artifacts.log_ic50 is not None:
        save_dataframe(artifacts.log_ic50, out_proc / "log_ic50_matrix.csv", index=True)
    if artifacts.sensitivity is not None:
        save_dataframe(artifacts.sensitivity, out_proc / "sensitivity_matrix.csv", index=True)

    save_dataframe(artifacts.filtered, out_proc / "filtered_matrix.csv", index=True)
    save_dataframe(artifacts.imputed, out_proc / "imputed_matrix.csv", index=True)
    save_dataframe(artifacts.scaled, out_proc / "scaled_matrix.csv", index=True)
    save_dataframe(pd.DataFrame({"drug_id": artifacts.kept_drug_ids}), out_proc / "kept_drugs.csv", index=False)
    save_dataframe(pd.DataFrame({"cell_id": artifacts.kept_cell_ids}), out_proc / "kept_cells.csv", index=False)
    save_dataframe(pd.DataFrame({"drug_id": artifacts.removed_drug_ids}), out_proc / "removed_drugs.csv", index=False)
    save_dataframe(pd.DataFrame({"cell_id": artifacts.removed_cell_ids}), out_proc / "removed_cells.csv", index=False)

    summary = {
        "alignment_report": report.__dict__,
        "preprocess_summary": artifacts.summary,
        "shapes": {
            "raw": list(artifacts.raw.shape),
            "filtered": list(artifacts.filtered.shape),
            "scaled": list(artifacts.scaled.shape),
        },
    }

    out_qc = base / paths["out_qc_dir"]
    out_qc.mkdir(parents=True, exist_ok=True)

    # QC figures
    def _savefig(fig, name: str) -> None:
        p = out_qc / name
        fig.savefig(p, bbox_inches="tight")
        plt.close(fig)

    def _plot_missingness_bars(df: pd.DataFrame, title: str):
        miss_drug = df.isna().mean(axis=1).to_numpy(dtype=float)
        miss_cell = df.isna().mean(axis=0).to_numpy(dtype=float)
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), dpi=150)
        axes[0].hist(miss_drug[np.isfinite(miss_drug)], bins=40, color="#4C78A8", alpha=0.9)
        axes[0].set_title("Per-drug missingness")
        axes[0].set_xlabel("Fraction missing")
        axes[0].set_ylabel("Count")
        axes[1].hist(miss_cell[np.isfinite(miss_cell)], bins=40, color="#F58518", alpha=0.9)
        axes[1].set_title("Per-cell missingness")
        axes[1].set_xlabel("Fraction missing")
        fig.suptitle(title)
        fig.tight_layout()
        return fig

    def _plot_variance_hist(df: pd.DataFrame, title: str):
        var = df.astype(float).var(axis=1, ddof=0).to_numpy(dtype=float)
        var = var[np.isfinite(var)]
        fig, ax = plt.subplots(figsize=(6, 3.5), dpi=150)
        if var.size:
            # Log-ish view when dynamic range is huge, but keep it safe for zeros.
            ax.hist(np.log10(np.maximum(var, 1e-16)), bins=50, color="#54A24B", alpha=0.9)
            ax.set_xlabel("log10(variance per drug)")
        ax.set_ylabel("Count")
        ax.set_title(title)
        fig.tight_layout()
        return fig

    # Use the matrix space used for filtering (sensitivity/log space depending on config)
    working_for_qc = artifacts.sensitivity if artifacts.sensitivity is not None else (artifacts.log_ic50 if artifacts.log_ic50 is not None else artifacts.raw)
    _savefig(_plot_missingness_bars(working_for_qc, "Missingness (before filtering)"), "missingness_before.png")
    _savefig(_plot_missingness_bars(artifacts.filtered, "Missingness (after filtering)"), "missingness_after.png")
    _savefig(_plot_variance_hist(working_for_qc, "Per-drug variance (before filtering)"), "variance_before.png")
    _savefig(_plot_variance_hist(artifacts.filtered, "Per-drug variance (after filtering)"), "variance_after.png")

    with (out_qc / "preprocess_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Also write the primary deliverable name from the checklist.
    save_dataframe(artifacts.scaled, out_proc / "processed_response_matrix.csv", index=True)

    print("Preprocess complete.")
    print(f"Wrote processed matrices to: {out_proc}")
    print(f"Wrote QC summary to: {base / paths['out_qc_dir'] / 'preprocess_summary.json'}")


if __name__ == "__main__":
    main()
