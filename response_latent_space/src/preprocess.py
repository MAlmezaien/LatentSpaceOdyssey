from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def log_transform_ic50(df: pd.DataFrame) -> pd.DataFrame:
    x = df.astype(float).copy()
    x = x.where(np.isfinite(x), np.nan)
    x = x.where(x > 0, np.nan)
    return np.log10(x)


def convert_to_sensitivity(df_ic50_linear: pd.DataFrame) -> pd.DataFrame:
    """
    Convert IC50 in linear space to sensitivity as -log10(IC50).
    """
    x = df_ic50_linear.astype(float).copy()
    x = x.where(np.isfinite(x), np.nan)
    x = x.where(x > 0, np.nan)
    return -np.log10(x)


def filter_missing(
    df: pd.DataFrame, max_drug_missing: float, max_cell_missing: float
) -> Tuple[pd.DataFrame, pd.Series, pd.Series, Dict[str, int]]:
    if not (0 <= max_drug_missing <= 1 and 0 <= max_cell_missing <= 1):
        raise ValueError("Missingness thresholds must be in [0, 1].")

    drug_missing_frac = df.isna().mean(axis=1)
    cell_missing_frac = df.isna().mean(axis=0)

    keep_drugs = drug_missing_frac <= max_drug_missing
    keep_cells = cell_missing_frac <= max_cell_missing

    out = df.loc[keep_drugs, keep_cells].copy()
    summary = {
        "n_drugs_before": int(df.shape[0]),
        "n_cells_before": int(df.shape[1]),
        "n_drugs_after": int(out.shape[0]),
        "n_cells_after": int(out.shape[1]),
        "n_drugs_removed": int((~keep_drugs).sum()),
        "n_cells_removed": int((~keep_cells).sum()),
    }
    return out, keep_drugs, keep_cells, summary


def impute_missing(df: pd.DataFrame, method: str = "drug_median") -> pd.DataFrame:
    x = df.astype(float).copy()
    if method == "drug_median":
        fill = x.median(axis=1, skipna=True)
        return x.T.fillna(fill).T
    if method == "drug_mean":
        fill = x.mean(axis=1, skipna=True)
        return x.T.fillna(fill).T
    if method == "zero":
        return x.fillna(0.0)
    raise ValueError(f"Unknown impute method: {method}")


def zscore_per_drug(df: pd.DataFrame) -> pd.DataFrame:
    x = df.astype(float)
    mu = x.mean(axis=1)
    sd = x.std(axis=1, ddof=0).replace(0.0, np.nan)
    z = x.sub(mu, axis=0).div(sd, axis=0)
    return z.fillna(0.0)


def filter_low_variance_drugs(df: pd.DataFrame, threshold: float) -> Tuple[pd.DataFrame, Dict[str, int]]:
    if threshold < 0:
        raise ValueError("Variance threshold must be >= 0.")
    var = df.astype(float).var(axis=1, ddof=0)
    keep = var >= threshold
    out = df.loc[keep].copy()
    summary = {
        "n_drugs_before": int(df.shape[0]),
        "n_drugs_after": int(out.shape[0]),
        "n_drugs_removed": int((~keep).sum()),
    }
    return out, summary


@dataclass
class PreprocessArtifacts:
    raw: pd.DataFrame
    log_ic50: pd.DataFrame | None
    sensitivity: pd.DataFrame | None
    filtered: pd.DataFrame
    imputed: pd.DataFrame
    scaled: pd.DataFrame
    summary: Dict[str, object]
    kept_drug_ids: List[str]
    kept_cell_ids: List[str]
    removed_drug_ids: List[str]
    removed_cell_ids: List[str]


def run_preprocess_pipeline(
    response: pd.DataFrame,
    *,
    do_log_transform: bool,
    convert_to_sensitivity_flag: bool,
    max_missing_drug: float,
    max_missing_cell: float,
    impute_method: str,
    low_variance_threshold: float,
    do_zscore_per_drug: bool,
) -> PreprocessArtifacts:
    raw = response.copy()
    log_ic50 = None
    sens = None

    working = raw.astype(float).where(np.isfinite(raw.astype(float)), np.nan)

    if do_log_transform:
        log_ic50 = log_transform_ic50(working)
        working = log_ic50

    if convert_to_sensitivity_flag:
        # If we already logged IC50, sensitivity is simply -log10(IC50) = -(log10(IC50)).
        if do_log_transform:
            sens = -working
        else:
            sens = convert_to_sensitivity(working)
        working = sens

    # Summary stats before filtering (for QC plots)
    miss_drug_before = working.isna().mean(axis=1)
    miss_cell_before = working.isna().mean(axis=0)
    var_drug_before = working.astype(float).var(axis=1, ddof=0)

    filtered, keep_drugs_mask, keep_cells_mask, miss_summary = filter_missing(
        working, max_missing_drug, max_missing_cell
    )
    filtered_lv, lv_summary = filter_low_variance_drugs(filtered, low_variance_threshold)
    imputed = impute_missing(filtered_lv, method=impute_method)

    if do_zscore_per_drug:
        scaled = zscore_per_drug(imputed)
    else:
        scaled = imputed.copy()

    # Summary stats after filtering
    miss_drug_after = filtered_lv.isna().mean(axis=1)
    miss_cell_after = filtered_lv.isna().mean(axis=0)
    var_drug_after = filtered_lv.astype(float).var(axis=1, ddof=0)

    summary: Dict[str, object] = {}
    summary.update({f"missing_{k}": v for k, v in miss_summary.items()})
    summary.update({f"low_variance_{k}": v for k, v in lv_summary.items()})
    summary["impute_method"] = impute_method
    summary["do_log_transform"] = do_log_transform
    summary["convert_to_sensitivity"] = convert_to_sensitivity_flag
    summary["zscore_per_drug"] = do_zscore_per_drug
    summary["max_missing_drug"] = float(max_missing_drug)
    summary["max_missing_cell"] = float(max_missing_cell)
    summary["low_variance_threshold"] = float(low_variance_threshold)

    # Compact numeric QC summaries (avoid dumping whole series into JSON unless needed elsewhere)
    def _qc_series_stats(s: pd.Series) -> Dict[str, float]:
        s2 = s.astype(float).replace([np.inf, -np.inf], np.nan).dropna()
        if s2.empty:
            return {"min": float("nan"), "p50": float("nan"), "p95": float("nan"), "max": float("nan"), "mean": float("nan")}
        return {
            "min": float(s2.min()),
            "p50": float(s2.quantile(0.50)),
            "p95": float(s2.quantile(0.95)),
            "max": float(s2.max()),
            "mean": float(s2.mean()),
        }

    summary["qc_missing_per_drug_before"] = _qc_series_stats(miss_drug_before)
    summary["qc_missing_per_cell_before"] = _qc_series_stats(miss_cell_before)
    summary["qc_missing_per_drug_after"] = _qc_series_stats(miss_drug_after)
    summary["qc_missing_per_cell_after"] = _qc_series_stats(miss_cell_after)
    summary["qc_variance_per_drug_before"] = _qc_series_stats(var_drug_before)
    summary["qc_variance_per_drug_after"] = _qc_series_stats(var_drug_after)

    kept_drugs = filtered_lv.index.astype(str).tolist()
    kept_cells = filtered_lv.columns.astype(str).tolist()
    removed_drugs = working.index.astype(str)[~keep_drugs_mask].tolist()
    removed_cells = working.columns.astype(str)[~keep_cells_mask].tolist()

    return PreprocessArtifacts(
        raw=raw,
        log_ic50=log_ic50,
        sensitivity=sens,
        filtered=filtered_lv,
        imputed=imputed,
        scaled=scaled,
        summary=summary,
        kept_drug_ids=kept_drugs,
        kept_cell_ids=kept_cells,
        removed_drug_ids=removed_drugs,
        removed_cell_ids=removed_cells,
    )

