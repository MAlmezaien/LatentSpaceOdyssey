---
doc_type: execution-plan
stage1_5_phase: 1
title: "Run contract + reusable analysis plumbing"
branch: feat/stage1-5-pipeline-contract
status: done
owner: ""
last_updated: "2026-04-13"
depends_on:
  - "Phase 0 merged to main"
links:
  master: stage1_5_master.md
  dependency_map: stage1_5_dependency_map.md
---

# Phase 1 — Run contract + reusable analysis plumbing

> **Plan mode.** Defines how every analysis run is parameterized, where outputs live, and what provenance must contain—no biology interpretation here.  
> **Index:** [stage1_5_master.md](stage1_5_master.md) · **Dependencies:** [stage1_5_dependency_map.md](stage1_5_dependency_map.md)

## Plan snapshot

| Field | Value |
|-------|--------|
| Status | done |
| Owner | |
| Last updated | 2026-04-10 |
| Depends on | Phase 0 merged to `main` |
| Branch | `feat/stage1-5-pipeline-contract` |
| Worktree | Optional |

---

## 1. Objective

Define and implement the **contract** that every stage 1.5 analysis run must satisfy: configs, CLI, output layout, provenance bundle, and relative-path policy—plus **generalize** the hardcoded NMF k8 c3 biovalidation so any embedding/partition tag can be run the same way.

---

## 2. Scope

### Included

- `configs/stage1_5/*.yaml` — base schemas for run families (embedding compare, partition compare, personalization, factors, drug neighborhoods); may start minimal and extend in phase 2.
- **Run folder schema** under `results/analysis_runs/<run_id>/` (subdirs e.g. `tables/`, `figures/`, `logs/` as needed).
- **CLI conventions:** `--config`, `--run-id` (or auto-generated `YYYY-MM-DD_slug`), mandatory failure on missing inputs.
- **Script I/O contract:** inputs listed in config; outputs only under the run folder; no silent overwrites of prior runs (fail or require `--force` policy).
- **Provenance bundle contract** (finalize contents of phase 0 helper): `config_used.yaml`, `git_commit.txt`, `command.txt`, `environment_export.txt`, `run_metadata.json`.
- **Relative-path policy:** all paths in configs and emitted metadata are repo-relative; CSV columns that reference files use relative paths.
- **Generalize biovalidation:** refactor [`response_latent_space/scripts/interpret_cell_clusters_nmf_k8_c3.py`](../../response_latent_space/scripts/interpret_cell_clusters_nmf_k8_c3.py) into config-driven entry (new module + thin wrapper or CLI), preserving behavior for k8 c3 as one preset.

### Excluded

Writing decision memos; full scientific interpretation; final HTML/PDF report (phase 3).

---

## 3. Prerequisites & inputs

- Phase 0 merged (`pyproject`, provenance helper baseline, README).
- Existing assets: `response_latent_space/results/embeddings/`, clustering CSVs, metadata, processed matrix paths from [`configs/default.yaml`](../../response_latent_space/configs/default.yaml).

---

## 4. Deliverables

- Documented run folder layout and provenance checklist.
- `configs/stage1_5/*.yaml` templates with comments.
- At least one **smoke** analysis command that writes a complete `run_id` folder using the contract.
- Generalized biovalidation/biovalidation-equivalent pipeline callable by config (k8 c3 regression test: outputs match prior logic within tolerance).

---

## 5. File changes

| Path | Action |
|------|--------|
| `configs/stage1_5/*.yaml` | Create |
| `docs/protocols/` (optional) | `run_contract.md` describing schema |
| `response_latent_space/src/run_provenance.py` (or equivalent) | Extend to full bundle contract |
| `scripts/analysis/` | Stub or `smoke_run.py` proving contract |
| Biovalidation script(s) | Refactor; deprecate hardcoded `RUN_TAG` |

---

## 6. Execution

### Tasks

- [x] Freeze provenance bundle file list and `run_metadata.json` schema (minimal JSON is fine).
- [x] Add `configs/stage1_5/` YAMLs with explicit `paths:` block pointing at `response_latent_space/...`.
- [x] Implement path resolution helper (repo root discovery) shared by scripts.
- [x] Refactor biovalidation logic to parameterized functions + CLI; keep old script as wrapper if needed.
- [x] Fix **all** remaining absolute-path emissions from evaluation/summary pipelines touched by stage 1.5 (`as_repo_relative` consolidated in `src/repo_paths.py`; evaluation already emitted repo-relative paths).
- [x] Add smoke script + Makefile target `stage1-5-smoke` (name flexible).
- [ ] PR → merge.

---

## 7. Exit criteria (definition of done)

- Any script adhering to the contract can be rerun on a fresh clone using only config + documented env.
- A single `run_id` directory contains **all** required provenance files plus outputs.
- No output CSV/JSON from new pipeline code contains machine-specific absolute paths.
- k8 c3 biovalidation path is **config-driven**; regression check passes.

---

## 8. Risks & caveats

- **Backward compatibility:** existing notebooks may reference old paths; document migration or symlink strategy briefly in README.
- **Schema churn:** keep `run_metadata.json` minimal to avoid blocking merges; extend with version field when needed.
