# PPI Network Approaches

Response-defined latent space analyses (stage 1 pipeline under `response_latent_space/`).

## Setup

From the **repository root** (this directory):

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -U pip
pip install -e .
```

Or with Conda:

```bash
conda env create -f environment.yml
conda activate ppi-network-approaches
```

**Install smoke (provenance helper):**

```bash
python -c "from src.run_provenance import write_run_provenance; print('ok')"
```

Run this from repo root after `pip install -e .`. The import name `src` matches the existing package layout under `response_latent_space/src` (not renamed in Phase 0).

If `pip install -e .` fails parsing `pyproject.toml`, ensure the file is UTF-8 **without** a BOM (some Windows editors add a BOM).

## Running stage-1 scripts

Scripts expect to be run with working directory `response_latent_space/` (paths in `configs/default.yaml` are relative to that folder):

```bash
cd response_latent_space
python run_preprocess.py
python run_embedding.py
python run_evaluation.py
```

## Data

Large raw matrices (e.g. IC50) are **not** committed by default (see `.gitignore`). Place inputs under `response_latent_space/data/` as required by your config.

## Legacy result paths

CSV files generated **before** the repo-relative path fix may still contain absolute paths. Re-run `python run_evaluation.py` from `response_latent_space/` to regenerate `master_stage1_summary.csv` with portable paths when convenient.

## Documentation

Stage 1.5 plans (canonical): `docs/plans/`.
