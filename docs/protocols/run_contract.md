# Stage 1.5 analysis run contract

## Run folder (`results/analysis_runs/<run_id>/`)

- **`tables/`** — CSV and similar tabular outputs  
- **`figures/`** — plots (when produced)  
- **`logs/`** — logs (when produced)  
- **Provenance at run root** (same folder, not only under subdirs):  
  `config_used.yaml`, `git_commit.txt`, `command.txt`, `environment_export.txt`, `run_metadata.json`

`run_metadata.json` includes `schema_version` (currently `"1"`), optional `run_id` and `config_path` (repo-relative).

## Overwrite policy

Creating a run directory uses **fail-if-exists** by default. **`--force`** removes an existing `<run_id>` directory and recreates it (see `prepare_analysis_run_dir`).

## Paths

- Config YAML lists inputs under a **`paths:`** block as **repo-relative** strings.  
- Scripts resolve the repository root via `pyproject.toml` (`ppi-network-approaches`) or `.git` (`src.repo_paths.find_repo_root`).  
- Downstream CSVs must not embed machine-specific absolute paths; use `src.repo_paths.as_repo_relative` where paths are emitted.

## Commands

- **Smoke:** `make stage1-5-smoke` or `python scripts/analysis/smoke_analysis_run.py`  
- **Biovalidation:** `python scripts/analysis/run_biovalidate.py --config configs/stage1_5/biovalidation_nmf_k8_c3.yaml`  
- **Contract output location:** add `--run-id <slug>` to write under `results/analysis_runs/<run_id>/` with full provenance.

Legacy biovalidation outputs remain under `response_latent_space/results/biovalidation/<run_tag>/` when `outputs.target: legacy` in the YAML.
