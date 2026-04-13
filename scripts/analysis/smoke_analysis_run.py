"""
Create a minimal analysis run under ``results/analysis_runs/<run_id>/`` with full provenance.

Usage (from repo root, after ``pip install -e .`` or with PYTHONPATH as in run_biovalidate).
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_RLS = _REPO / "response_latent_space"
if str(_RLS) not in sys.path:
    sys.path.insert(0, str(_RLS))

from src.analysis_runs import prepare_analysis_run_dir  # noqa: E402
from src.repo_paths import as_repo_relative, find_repo_root  # noqa: E402
from src.run_provenance import write_run_provenance  # noqa: E402


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Smoke test for stage 1.5 analysis run layout + provenance.")
    ap.add_argument(
        "--run-id",
        default=None,
        help="Run folder name (default: UTC timestamp slug smoke_YYYY-MM-DDTHHMMSSZ).",
    )
    ap.add_argument("--force", action="store_true", help="Replace existing run directory if present.")
    ap.add_argument("--repo-root", type=Path, default=None, help="Repository root (default: auto-detect).")
    args = ap.parse_args(argv)

    repo_root = args.repo_root.resolve() if args.repo_root else find_repo_root()
    run_id = args.run_id or f"smoke_{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}"

    run_root = prepare_analysis_run_dir(repo_root, run_id, force=args.force)

    stub_config = repo_root / "configs" / "stage1_5" / "_template.yaml"
    if not stub_config.is_file():
        shutil.rmtree(run_root)
        raise FileNotFoundError(f"Expected stub config at {stub_config}")

    write_run_provenance(
        run_root,
        argv=sys.argv if argv is None else [sys.argv[0], *argv],
        config_source=stub_config,
        run_id=run_id,
        config_path_repo_relative=as_repo_relative(stub_config, repo_root),
    )

    (run_root / "tables" / "smoke.txt").write_text(
        "stage1_5 smoke run ok\n",
        encoding="utf-8",
    )
    print(run_root)


if __name__ == "__main__":
    main()
