from __future__ import annotations

import shutil
from pathlib import Path


def prepare_analysis_run_dir(repo_root: Path, run_id: str, *, force: bool = False) -> Path:
    """
    Create ``results/analysis_runs/<run_id>/`` with ``tables/``, ``figures/``, ``logs/``.

    Default: fail if the run directory already exists. With ``force``, remove it first.
    """
    root = repo_root / "results" / "analysis_runs" / run_id
    if root.exists():
        if not force:
            raise FileExistsError(
                f"Analysis run directory already exists: {root}. "
                "Use --force to replace it, or choose a new --run-id."
            )
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    for sub in ("tables", "figures", "logs"):
        (root / sub).mkdir(exist_ok=True)
    return root
