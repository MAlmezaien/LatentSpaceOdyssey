"""
Verify biovalidation is deterministic: two consecutive runs produce identical CSVs.

Usage:
  python scripts/analysis/regression_biovalidate_k8_c3.py

Requires inputs referenced in ``configs/stage1_5/biovalidation_nmf_k8_c3.yaml``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

_REPO = Path(__file__).resolve().parents[2]
_RLS = _REPO / "response_latent_space"
if str(_RLS) not in sys.path:
    sys.path.insert(0, str(_RLS))

from src.biovalidate_cell_clusters import (  # noqa: E402
    load_yaml_config,
    run_biovalidation_from_config,
)
from src.repo_paths import find_repo_root  # noqa: E402

REF_SUFFIX = "nmf_k8_c3"
REF_CSV_NAMES = [
    f"cluster_size_audit_{REF_SUFFIX}.csv",
    f"cell_cluster_metadata_join_{REF_SUFFIX}.csv",
    f"cluster_cell_metadata_summary_{REF_SUFFIX}.csv",
    f"cluster_marker_enrichment_moa_{REF_SUFFIX}.csv",
    f"cluster_marker_enrichment_target_{REF_SUFFIX}.csv",
    f"cluster_robustness_top10_vs_top20_{REF_SUFFIX}.csv",
]


def _canonicalize(df: pd.DataFrame) -> pd.DataFrame:
    cols = list(df.columns)
    return df.sort_values(by=cols, kind="mergesort").reset_index(drop=True)


def _frames_close(a: pd.DataFrame, b: pd.DataFrame, rtol: float = 1e-9, atol: float = 1e-12) -> bool:
    a, b = _canonicalize(a), _canonicalize(b)
    try:
        assert_frame_equal(a, b, rtol=rtol, atol=atol, check_dtype=False, check_exact=False)
    except AssertionError:
        return False
    return True


def main() -> int:
    repo = find_repo_root()
    cfg_path = repo / "configs" / "stage1_5" / "biovalidation_nmf_k8_c3.yaml"
    cfg = load_yaml_config(cfg_path)

    out_dir = _RLS / "results" / "biovalidation" / REF_SUFFIX

    run_biovalidation_from_config(repo, cfg, config_path=cfg_path, argv=[sys.argv[0], "regression_pass1"])
    first = {name: pd.read_csv(out_dir / name) for name in REF_CSV_NAMES}

    run_biovalidation_from_config(repo, cfg, config_path=cfg_path, argv=[sys.argv[0], "regression_pass2"])
    second = {name: pd.read_csv(out_dir / name) for name in REF_CSV_NAMES}

    for name in REF_CSV_NAMES:
        if not _frames_close(first[name], second[name]):
            print(f"FAIL: non-deterministic or mismatch in {name}")
            return 1

    print("OK: two consecutive biovalidation runs match within tolerance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
