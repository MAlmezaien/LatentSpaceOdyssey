# Stage 1.5 — Master roadmap (index)

| | |
|--|--|
| **Status** | in progress |
| **Owner** | |
| **Last updated** | 2026-04-10 |
| **Depends on** | — (index); see [stage1_5_dependency_map.md](stage1_5_dependency_map.md) for phase order |

This document is the single index for stage 1.5. Execution detail lives in linked plans. Dependency order is explicit in [stage1_5_dependency_map.md](stage1_5_dependency_map.md).

**Execution plan format:** Each phase file is a **plan-mode** document: YAML frontmatter (`doc_type: execution-plan`, phase, branch, status, `depends_on`), a one-line **Plan snapshot** table (editable while work progresses), numbered sections (Objective → Scope → Inputs → Deliverables → Files → Execution → Exit criteria → Risks), and **checkbox tasks** where applicable.

| Phase | Document | Branch (primary) |
|-------|----------|------------------|
| 0 — Repo OS | [stage1_5_phase0_repo_os.md](stage1_5_phase0_repo_os.md) | `feat/stage1-5-setup` |
| 1 — Pipeline contract | [stage1_5_phase1_pipeline_contract.md](stage1_5_phase1_pipeline_contract.md) | `feat/stage1-5-pipeline-contract` |
| 2 — Scientific analyses | [stage1_5_phase2_analysis.md](stage1_5_phase2_analysis.md) | see plan |
| 3 — Reporting & release | [stage1_5_phase3_reporting_release.md](stage1_5_phase3_reporting_release.md) | `feat/stage1-5-reporting` |
| Dependencies | [stage1_5_dependency_map.md](stage1_5_dependency_map.md) | |

---

## Cursor Plan sync policy

- Canonical plans live in `docs/plans/`.
- Cursor-native Plans are optional execution mirrors for the currently active phase only.
- Update `docs/plans/` first.
- When beginning a phase, create or refresh a single Cursor Plan from the canonical phase doc.
- Do not maintain inactive phases as Cursor-native Plans unless needed.

---

## Merge policy

These rules reduce a common failure mode: **biological conclusions written before the repo and run contract are stable.**

- **Phase 2 analysis branches** (`feat/k8-c2-vs-c3`, `feat/within-cluster-personalization`, etc.) **do not merge** to `main` unless **provenance** (phase 1 bundle) and **relative paths** for pipeline I/O are already working on `main` (i.e. phases 0–1 merged and verified).
- **Phase 3 reporting** (`feat/stage1-5-reporting`) **does not merge** unless every cited **`run_id`** under `results/analysis_runs/` **exists**, is **complete**, and **passes QA** (checklist in phase 3 plan).

---

## Project objective

Build a rigorous, version-controlled, transferable analysis pipeline for **stage 1.5**: separate embedding choice from clustering choice; compare NMF **k=8** cell partitions **c=2** vs **c=3**; quantify within-cluster personalization capacity; interpret latent factors and drug-side local neighborhoods; produce decision-ready documents on whether stage 1 already supports personalization and whether stage 2 priors are justified.

**Working assumptions:** primary embedding candidate NMF **k=8**; comparator NMF **k=3**; **c=3** on k=8 is provisional if a singleton appears; continuous coordinates and factor loadings matter more than hard clusters alone; drug story emphasizes local neighborhoods, not global cluster purity.

---

## Current repo ground truth

- **Analysis code and data paths** live under [`response_latent_space/`](../../response_latent_space/): `run_preprocess.py`, `run_evaluation.py`, `src/` (`evaluation`, `clustering`, `interpret`), `configs/default.yaml`.
- **Embeddings** exist under `response_latent_space/results/embeddings/` (e.g. `nmf_k3`, `nmf_k8`).
- **Stage-1 style outputs** include `results/clustering/`, `results/interpretation/`, and `master_stage1_summary.csv` with metrics across models and cluster counts. Some CSV columns have stored **absolute paths** (portability issue).
- **Biovalidation** for NMF k8 c3 is implemented in a **hardcoded** script under `response_latent_space/scripts/` targeting a fixed run tag.
- **Workspace** may not yet be a git repository; root-level `docs/`, `pyproject.toml`, and `environment.yml` as specified in the roadmap are not assumed present until phase 0 completes.

---

## Architecture choice

- **Keep** `response_latent_space/` as the Python package and anchor for existing relative paths (preprocess, embeddings, legacy results).
- **Add** project-root `docs/`, `configs/stage1_5/`, `reports/`, `scripts/analysis/`, and **`results/analysis_runs/`** for timestamped, provenance-backed runs.
- **Configs** reference inputs via **stable relative paths** from repo root (e.g. explicit `response_latent_space/...` where needed). No hidden “only works on this machine” assumptions.

---

## Phase overview

| Phase | Intent | Merge point |
|-------|--------|-------------|
| **0** | Git, packaging, docs, provenance helper, path hygiene | Repo professionally organized |
| **1** | Run contract: YAMLs, run folder schema, CLI + provenance bundle, generalize biovalidation | Runs reproducible and portable |
| **2** | Scientific scripts: embedding/partition comparisons, personalization, factors, drug neighborhoods | Science outputs in `analysis_runs` |
| **3** | Decision memos, summary report, QA, tags, optional hooks | Conclusions audited and released |

Internal split for phase 2 (see linked plan): **2A** = pipeline-facing measurement scripts; **2B** = biology-facing interpretation scripts.

---

## Branch strategy

- **`main`**: stable, reproducible states only.
- **Phase 0:** `feat/stage1-5-setup` → merge after acceptance.
- **Phase 1:** `feat/stage1-5-pipeline-contract` → merge after acceptance.
- **Phase 2:** optional focused branches, e.g. `feat/k8-c2-vs-c3`, `feat/within-cluster-personalization`, `feat/factor-interpretation`, `feat/drug-neighborhood-report`, or fewer branches if workload is sequential—see [stage1_5_phase2_analysis.md](stage1_5_phase2_analysis.md).
- **Phase 3:** `feat/stage1-5-reporting` (writing and QA after outputs stabilize).
- **Git worktrees** encouraged for parallel work without cross-branch interference.

Suggested checkpoint tags (apply when criteria met): `v0.1-stage1-baseline`, `v0.2-stage1-5-partition-review`, `v0.3-stage1-5-personalization-check` (exact mapping to merges is flexible; tag when the corresponding milestone is real).

---

## Run ID convention

- **`results/analysis_runs/<run_id>/`** where `run_id` is **`YYYY-MM-DD_<short_slug>`** (e.g. `2026-04-10_embedding_compare_nmf_k3_k8`).
- Every run directory must include the **provenance bundle** defined in phase 1 (config snapshot, git commit, command, environment export, `run_metadata.json`).
- **No manual edits** to generated artifacts inside run folders.

---

## Final deliverables

- `docs/project_brief.md`
- `docs/current_state/stage1_status_2026-04-10.md` (or latest dated snapshot)
- `docs/decisions/representation_decision.md`
- `docs/decisions/cell_partition_decision.md`
- `docs/decisions/stage1_personalization_assessment.md`
- `configs/stage1_5/*.yaml`
- `scripts/analysis/*.py`
- `results/analysis_runs/<run_id>/*` (per analysis family)
- `reports/stage1_5_summary.md`
- `reports/stage1_5_summary.html` (and PDF if toolchain allows)

---

## Merge bar / acceptance criteria

**Global**

- Fresh **clone + environment setup** can rerun at least one full analysis path end-to-end into a new `run_id` with complete provenance.
- Generated figures and tables are **reproducible from code**; no manual edits to outputs.
- **Relative paths** in new artifacts; no reliance on machine-local absolute paths for pipeline I/O.

**Per-phase bars** are stated in each linked execution plan; phase 3 adds **QA sign-off** before declaring release-ready.

**No merge to `main`** unless: scripts run end-to-end where applicable, outputs live under `analysis_runs` with provenance, docs updated as required by that phase, and (for phase 3) QA checklist satisfied.

See **Merge policy** above for phase 2 and phase 3 branch gates.
