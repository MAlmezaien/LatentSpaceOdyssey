from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd


def _as_path(path: str | Path) -> Path:
    return path if isinstance(path, Path) else Path(path)


def load_response_matrix(path: str | Path, index_col: int | None = 0) -> pd.DataFrame:
    """
    Load a drug×cell response matrix from CSV/TSV/Parquet.

    Conventions:
      - rows: drugs
      - cols: cells
      - index: drug IDs (strings)
      - columns: cell IDs (strings)
    """
    p = _as_path(path)
    if not p.exists():
        raise FileNotFoundError(f"Response matrix not found: {p}")

    if p.suffix.lower() in {".parquet"}:
        df = pd.read_parquet(p)
    elif p.suffix.lower() in {".tsv", ".txt"}:
        df = pd.read_csv(p, sep="\t", index_col=index_col)
    else:
        df = pd.read_csv(p, index_col=index_col)

    df.index = df.index.astype(str)
    df.columns = df.columns.astype(str)
    return df


def load_drug_metadata(path: str | Path) -> pd.DataFrame:
    p = _as_path(path)
    if not p.exists():
        raise FileNotFoundError(f"Drug metadata not found: {p}")
    df = pd.read_csv(p)
    return df


def load_cell_metadata(path: str | Path) -> pd.DataFrame:
    p = _as_path(path)
    if not p.exists():
        raise FileNotFoundError(f"Cell metadata not found: {p}")
    df = pd.read_csv(p)
    return df


def save_dataframe(df: pd.DataFrame, path: str | Path, index: bool = True) -> None:
    p = _as_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix.lower() == ".parquet":
        df.to_parquet(p, index=index)
    else:
        df.to_csv(p, index=index)


def save_numpy(array: np.ndarray, path: str | Path) -> None:
    p = _as_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    np.save(p, array)


@dataclass(frozen=True)
class AlignmentReport:
    n_drugs_matrix: int
    n_cells_matrix: int
    n_duplicate_drugs: int
    n_duplicate_cells: int
    n_drugs_in_metadata: Optional[int]
    n_cells_in_metadata: Optional[int]
    n_drugs_missing_metadata: Optional[int]
    n_cells_missing_metadata: Optional[int]


def validate_matrix_and_metadata(
    response: pd.DataFrame,
    drug_metadata: Optional[pd.DataFrame] = None,
    cell_metadata: Optional[pd.DataFrame] = None,
    drug_id_col: str = "drug_id",
    cell_id_col: str = "cell_line_id",
) -> AlignmentReport:
    drug_ids = response.index.astype(str)
    cell_ids = response.columns.astype(str)

    n_dup_drugs = int(pd.Index(drug_ids).duplicated().sum())
    n_dup_cells = int(pd.Index(cell_ids).duplicated().sum())

    n_drugs_in_md = None
    n_cells_in_md = None
    n_drugs_missing = None
    n_cells_missing = None

    if drug_metadata is not None and drug_id_col in drug_metadata.columns:
        md_drugs = set(drug_metadata[drug_id_col].astype(str))
        n_drugs_in_md = len(md_drugs)
        n_drugs_missing = len([d for d in drug_ids if d not in md_drugs])

    if cell_metadata is not None and cell_id_col in cell_metadata.columns:
        md_cells = set(cell_metadata[cell_id_col].astype(str))
        n_cells_in_md = len(md_cells)
        n_cells_missing = len([c for c in cell_ids if c not in md_cells])

    return AlignmentReport(
        n_drugs_matrix=response.shape[0],
        n_cells_matrix=response.shape[1],
        n_duplicate_drugs=n_dup_drugs,
        n_duplicate_cells=n_dup_cells,
        n_drugs_in_metadata=n_drugs_in_md,
        n_cells_in_metadata=n_cells_in_md,
        n_drugs_missing_metadata=n_drugs_missing,
        n_cells_missing_metadata=n_cells_missing,
    )

