---
doc_type: execution-plan
stage1_5_phase: 0
title: "Repo operating system"
branch: feat/stage1-5-setup
status: done
owner: ""
last_updated: "2026-04-10"
depends_on: []
links:
  master: stage1_5_master.md
  dependency_map: stage1_5_dependency_map.md
---

# Phase 0 — Repo operating system

> **Plan mode.** Engineering infrastructure only; mergeable before any new scientific analysis.  
> **Index:** [stage1_5_master.md](stage1_5_master.md) · **Dependencies:** [stage1_5_dependency_map.md](stage1_5_dependency_map.md)

## Plan snapshot

| Field | Value |
|-------|--------|
| Status | done |
| Owner | |
| Last updated | 2026-04-10 |
| Depends on | Nothing precedes phase 0 |
| Branch | `feat/stage1-5-setup` |
| Worktree | Optional |

---

## 1. Objective

Establish git, packaging, documentation, and shared engineering utilities so the repository is professionally organized and mergeable **before** any new scientific analysis logic lands.

---

## 2. Scope

### Included

- `git init` (if not already a repo)
- `.gitignore` (Python, venvs, OS noise; policy for large `data/raw`)
- `README.md` (clone, env, install, high-level commands)
- `Makefile` (at least: setup, placeholder or smoke targets for later phases)
- `AGENTS.md` (project mission, guardrails, directory expectations — per team template)
- `.cursor/rules/` (e.g. scope, reproducibility, outputs, no manual result edits)
- `.cursor/subagents/` (planner, pipeline engineer, stats analyst, QA reviewer, scientific writer)
- Root `pyproject.toml` (package layout for `response_latent_space` or documented install path)
- Root `environment.yml` (conda/mamba; aligned with `pyproject` dependencies)
- **Provenance helper** module (write `git_commit.txt`, `command.txt`, `environment_export.txt`, `run_metadata.json` — full contract finalized in phase 1)
- **Path hygiene:** identify and plan fixes for absolute paths emitted in existing evaluation outputs (implementation may complete in phase 0 or hand off to phase 1 with tickets)

### Excluded

Stage 1.5 YAML run configs, analysis scripts beyond a provenance smoke test, decision memos, final reports.

---

## 3. Prerequisites & inputs

- Existing tree under [`response_latent_space/`](../../response_latent_space/).
- Team templates for `AGENTS.md`, Cursor rules, and subagent prompts (if already drafted elsewhere).

---

## 4. Deliverables

- Git repository with initial commit(s) on a feature branch.
- Documented one-command setup in `README.md`.
- Installable Python package from repo root (`pip install -e .`).
- Provenance helper callable from future scripts.
- `.gitignore` and policy note for data that must not be committed blindly.

---

## 5. File changes

| Path | Action |
|------|--------|
| `.gitignore` | Create |
| `README.md` | Create |
| `Makefile` | Create |
| `AGENTS.md` | Create |
| `pyproject.toml` | Create |
| `environment.yml` | Create |
| `.cursor/rules/*.mdc` | Create |
| `.cursor/subagents/*.md` | Create |
| `response_latent_space/src/run_provenance.py` (or `scripts/utils/provenance.py`) | Create |
| `run_evaluation.py` / writers of `master_stage1_summary.csv` | Change (path hygiene; may be partial in phase 0) |

---

## 6. Execution

### Tasks

- [x] Initialize git; add `.gitignore`; document data policy in `README`.
- [x] Add `pyproject.toml` and `environment.yml`; verify editable install.
- [x] Add `AGENTS.md`, Cursor rules, subagent markdown files.
- [x] Add `Makefile` with `setup` (and stubs for later targets if useful).
- [x] Implement minimal **provenance helper** (write core files; JSON schema can tighten in phase 1).
- [x] Audit `run_evaluation.py` and related saves for **absolute paths**; implement relative-path emission or document required follow-up in phase 1.
- [ ] Open PR → review → merge to `main`.

---

## 7. Exit criteria (definition of done)

- `git status` clean on merge; no secrets or giant binaries committed.
- `pip install -e .` from repo root succeeds; import of package works.
- `README.md` describes clone + env + install in one place.
- Provenance helper runs in isolation and writes expected files to a test directory.
- Path hygiene either **fixed** for new runs or **explicitly ticketed** with owner for phase 1.

---

## 8. Risks & caveats

- **Large raw data:** do not commit by default; use `.gitignore` + documented acquisition.
- **Dual venvs** (`response_latent_space/.venv` vs root): document which env is canonical after phase 0.
- Moving all path fixes into phase 1 is acceptable only if phase 0 documents the debt clearly.
