from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yaml

from src.embedding import run_nmf_embedding, run_svd_embedding
from src.io_utils import load_response_matrix, save_dataframe


def load_config(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def main() -> None:
    base = Path(__file__).resolve().parent
    cfg = load_config(base / "configs" / "default.yaml")

    paths = cfg["paths"]
    preprocess_cfg = cfg.get("preprocess", {})
    embed_cfg = cfg.get("embedding", {})

    random_state = int(preprocess_cfg.get("random_seed", 1337))
    latent_dims = list(map(int, embed_cfg.get("latent_dims", [3, 5, 8, 10, 15])))
    models = list(embed_cfg.get("models", ["SVD", "NMF"]))

    proc_path = base / paths["out_processed_dir"] / "processed_response_matrix.csv"
    matrix = load_response_matrix(proc_path, index_col=0)

    out_root = base / paths["out_embeddings_dir"]
    _ensure_dir(out_root)

    summary_rows: List[Dict[str, Any]] = []

    for model in models:
        model_upper = str(model).upper()
        for k in latent_dims:
            if model_upper == "SVD":
                drug_emb, cell_emb, ev, recon, rmse = run_svd_embedding(matrix, n_components=k, random_state=random_state)
                out_dir = out_root / f"svd_k{k}"
                _ensure_dir(out_dir)
                save_dataframe(drug_emb, out_dir / "drug_embedding.csv", index=True)
                save_dataframe(cell_emb, out_dir / "cell_embedding.csv", index=True)
                save_dataframe(recon, out_dir / "reconstructed_matrix.csv", index=True)
                summary_rows.append(
                    {
                        "model": "SVD",
                        "k": k,
                        "reconstruction_error": rmse,
                        "explained_variance": ev,
                        "notes": "",
                    }
                )
            elif model_upper == "NMF":
                nmf_cfg = embed_cfg.get("nmf", {})
                drug_emb, cell_emb, recon, rmse, notes = run_nmf_embedding(
                    matrix,
                    n_components=k,
                    random_state=random_state,
                    max_iter=int(nmf_cfg.get("max_iter", 2000)),
                    tol=float(nmf_cfg.get("tol", 1e-4)),
                )
                out_dir = out_root / f"nmf_k{k}"
                _ensure_dir(out_dir)
                save_dataframe(drug_emb, out_dir / "drug_embedding.csv", index=True)
                save_dataframe(cell_emb, out_dir / "cell_embedding.csv", index=True)
                save_dataframe(recon, out_dir / "reconstructed_matrix.csv", index=True)
                (out_dir / "notes.json").write_text(json.dumps(notes, indent=2), encoding="utf-8")
                summary_rows.append(
                    {
                        "model": "NMF",
                        "k": k,
                        "reconstruction_error": rmse,
                        "explained_variance": "",
                        "notes": json.dumps(notes),
                    }
                )
            else:
                raise ValueError(f"Unknown embedding model: {model}")

    summary_df = pd.DataFrame(summary_rows)
    save_dataframe(summary_df, out_root / "embedding_summary.csv", index=False)

    print("Embedding complete.")
    print(f"Wrote embeddings to: {out_root}")
    print(f"Wrote summary to: {out_root / 'embedding_summary.csv'}")


if __name__ == "__main__":
    main()
