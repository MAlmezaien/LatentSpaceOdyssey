---
doc_type: execution-plan
stage1_5_phase: 3
title: "Decisions, report, QA, release"
branch: feat/stage1-5-reporting
status: not started
owner: ""
last_updated: "2026-04-10"
depends_on:
  - "Phase 2 outputs frozen enough to cite"
  - "Cited run_ids exist and pass QA before merge"
links:
  master: stage1_5_master.md
  dependency_map: stage1_5_dependency_map.md
  merge_policy: stage1_5_master.md#merge-policy
---

# Phase 3 — Decisions, report, QA, release

> **Plan mode.** Writing and audit **after** evidence is stable; no new science unless QA forces a fix.  
> **Index:** [stage1_5_master.md](stage1_5_master.md) · **Dependencies:** [stage1_5_dependency_map.md](stage1_5_dependency_map.md) · **Merge policy:** [master § Merge policy](stage1_5_master.md#merge-policy)

## Plan snapshot

| Field | Value |
|-------|--------|
| Status | not started · in progress · blocked · done |
| Owner | |
| Last updated | 2026-04-10 |
| Depends on | Phase 2 outputs **frozen enough to cite**; cited `run_id`s must exist and pass QA before merge |
| Branch | `feat/stage1-5-reporting` |
| Worktree | Optional |

---

## 1. Objective

Turn **stable** phase 2 outputs into signed-off **decision documents**, a **summary report**, **QA audit**, **release tags**, and **optional** Cursor hooks—without premature conclusions before evidence is fixed.

---

## 2. Scope

### Included

- **Decision memos** (evidence-linked, uncertainty-aware):
  - `docs/decisions/representation_decision.md`
  - `docs/decisions/cell_partition_decision.md`
  - `docs/decisions/stage1_personalization_assessment.md`
- **Project docs:** `docs/project_brief.md`; `docs/current_state/stage1_status_<date>.md` refresh.
- **Final summary:** `reports/stage1_5_summary.md`; `reports/stage1_5_summary.html` (PDF optional if pandoc/wkhtmltopdf available).
- **QA checklist:** reproducibility, path correctness, config/output consistency, claim vs evidence, provenance completeness, figure/table numbering match prose.
- **Release tags:** e.g. `v1.0-stage1-5-complete` or aligned team tag scheme after QA pass.
- **Optional hooks:** e.g. warn on writes outside `results/analysis_runs/`, require provenance files post-run, stale `docs/decisions` vs code (implement only if low friction).

### Excluded

New scientific metrics or reruns except to fix blocking errors found in QA.

---

## 3. Prerequisites & inputs

- Phase 2 merged; frozen `run_id`(s) referenced as canonical evidence.
- Phase 1 contract for what “complete run” means.

---

## 4. Deliverables

- Decision and report markdown/HTML (and PDF if agreed).
- QA log or punch list in `docs/logs/` with severity and resolution.
- Git tag(s) on validated commit.
- Optional `.cursor/hooks` configuration documented in README.

---

## 5. File changes

| Path | Action |
|------|--------|
| `docs/decisions/*.md` | Create/update |
| `docs/project_brief.md` | Create |
| `docs/current_state/stage1_status_*.md` | Create/update |
| `reports/stage1_5_summary.md` | Create |
| `reports/stage1_5_summary.html` | Generate |
| `reports/figures/`, `reports/tables/` | Populate by copy or relative links to `analysis_runs` |
| `docs/logs/*_qa.md` | Create |
| `docs/protocols/qa_checklist.md` | Create (optional) |
| `.cursor/hooks.json` + scripts | Optional |

---

## 6. Execution

### Tasks

- [ ] **Freeze evidence:** list canonical `run_id` folders and commit hashes in a short index (e.g. `docs/current_state/` or report front matter).
- [ ] Draft decision memos using **only** referenced tables/figures; add “what this does not justify” sections.
- [ ] Assemble `stage1_5_summary.md` (executive summary, methods pointer, links to runs).
- [ ] Generate HTML (and PDF if toolchain present); ensure assets use relative paths.
- [ ] Run **QA checklist**; file punch list; fix doc/code mismatches (minimal code fixes only).
- [ ] Tag release; optional hooks last.

---

## 7. Exit criteria (definition of done)

- Every numeric claim in decision docs maps to a **specific artifact** under `results/analysis_runs/`.
- Summary report builds without manual patching of generated numbers.
- QA produces **merge/no-merge** style outcome for the reporting branch.
- No overselling of hard clusters; singleton issue and local-vs-global drug framing are explicit.

---

## 8. Risks & caveats

- **Premature writing:** do not start this phase until phase 2 outputs are stable enough to cite.
- **Scope creep:** resist adding new analyses here; send feedback to a new ticket or phase 2 patch.
- **Hooks:** optional; do not block release on hook polish.
