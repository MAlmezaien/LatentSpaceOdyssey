"""
Backward-compatible entry: loads ``configs/stage1_5/biovalidation_nmf_k8_c3.yaml`` and runs biovalidation.

Prefer: ``python scripts/analysis/run_biovalidate.py --config configs/stage1_5/biovalidation_nmf_k8_c3.yaml``
"""

from __future__ import annotations

import sys
from pathlib import Path

_RLS = Path(__file__).resolve().parent.parent
if str(_RLS) not in sys.path:
    sys.path.insert(0, str(_RLS))

from src.biovalidate_cell_clusters import load_yaml_config, run_biovalidation_from_config
from src.repo_paths import find_repo_root


def main() -> None:
    repo_root = find_repo_root(Path(__file__))
    config_path = repo_root / "configs" / "stage1_5" / "biovalidation_nmf_k8_c3.yaml"
    cfg = load_yaml_config(config_path)
    run_biovalidation_from_config(
        repo_root,
        cfg,
        config_path=config_path,
        argv=sys.argv,
    )


if __name__ == "__main__":
    main()
