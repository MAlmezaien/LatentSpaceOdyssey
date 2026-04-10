# Phase 0 — Repo OS execution log

**Date:** 2026-04-10  
**Branch:** `feat/stage1-5-setup` (create locally if not present)

## Completed

- `.gitignore` at repo root (Python, venvs, Jupyter checkpoints, optional raw data patterns).
- `pyproject.toml` + `environment.yml` — editable install discovers package `src` under `response_latent_space/`. Note: if `pyproject.toml` was saved with a UTF-8 BOM from the editor, `pip install -e .` can fail to parse; save without BOM or strip BOM (first byte sequence `EF BB BF`).
- `README.md`, `Makefile` (`setup`, `install-smoke`), `AGENTS.md`.
- `.cursor/rules/*.mdc`, `.cursor/subagents/*.md`.
- `response_latent_space/src/run_provenance.py` — lightweight `write_run_provenance()` (git commit, command, `pip freeze`, `run_metadata.json`).
- `response_latent_space/run_evaluation.py` — `master_stage1_summary.csv` path columns and `embedding_interpretation_summary.md` key outputs use paths **relative to repo root**.

## Not done in this environment

- **Git:** `git` was not available in the automation shell; run locally:
  - `git init -b main`
  - `git checkout -B feat/stage1-5-setup`
  - commits per sequence below.

## Legacy artifacts

- Existing `master_stage1_summary.csv` (and similar) may still list absolute paths until you re-run `python run_evaluation.py` from `response_latent_space/`. README documents this.

## Suggested commit sequence

1. `chore: initialize gitignore and repo hygiene`
2. `build: add root packaging and environment files`
3. `docs: add README and phase-0 operating docs`
4. `tooling: add cursor rules subagents and agents guide`
5. `feat: add run provenance helper`
6. `fix: make evaluation outputs use repo-relative paths`
7. `docs: update phase-0 status and execution log`
