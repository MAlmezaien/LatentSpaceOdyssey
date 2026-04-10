---
doc_type: execution-plan
stage1_5_phase: 2
title: "Scientific analyses"
branch: "feat/k8-c2-vs-c3 | feat/within-cluster-personalization | …"
status: not started
owner: ""
last_updated: "2026-04-10"
depends_on:
  - "Phase 1 merged to main (provenance + relative paths)"
links:
  master: stage1_5_master.md
  dependency_map: stage1_5_dependency_map.md
  merge_policy: stage1_5_master.md#merge-policy
---

# Phase 2 — Scientific analyses

> **Plan mode.** Evidence generation under the phase 1 contract; 2A = measurement plumbing, 2B = interpretation-ready tables.  
> **Index:** [stage1_5_master.md](stage1_5_master.md) · **Dependencies:** [stage1_5_dependency_map.md](stage1_5_dependency_map.md) · **Merge policy:** [master § Merge policy](stage1_5_master.md#merge-policy)

## Plan snapshot

| Field | Value |
|-------|--------|
| Status | not started · in progress · blocked · done |
| Owner | |
| Last updated | 2026-04-10 |
| Depends on | Phase 1 merged to `main` (provenance + relative paths required before phase 2 branches merge) |
| Branches | See § Execution — optional parallel branches |
| Worktree | Recommended for parallel streams |

---

## 1. Objective

Produce **reproducible scientific outputs** for stage 1.5: embedding comparison (NMF k=3 vs k=8), partition comparison on k=8 (c=2 vs c=3), within-cluster personalization, latent factor interpretation (k=8), and drug local-neighborhood reporting—each emitted under `results/analysis_runs/<run_id>/` using the phase 1 contract.

---

## 2. Scope

### Phase 2A — Pipeline-facing (measurement plumbing)

- **`compare_embeddings_nmf.py`** — NMF k=3 vs k=8: reconstruction, cell stability, cell silhouette, drug silhouette (explicit handling of label-dependent metrics), interpretability notes table.
- **`compare_partition_k8_c2_c3.py`** — Cluster sizes, silhouette, bootstrap ARI, marker–drug coherence, robustness to marker cutoff, **singleton handling** section.
- **Generalized biovalidation wrapper** — phase 1 refactor exercised for k8 c2 and k8 c3 (and comparator configs as needed), not only c3.

### Phase 2B — Biology-facing (interpretation starts here)

- **`within_cluster_personalization.py`** — NN structure among cell lines; variance of factor loadings within clusters; overlap of top sensitive drugs; exemplar pairs (same cluster, different drug rankings).
- **`interpret_factors_nmf_k8.py`** — Top-loading cells and drugs per factor; factor interpretation tables; coherence assessment.
- **`drug_neighborhood_report.py`** — Nearest-neighbor consistency; MoA/target enrichment in **local** neighborhoods; representative neighborhoods; **no** overclaim from global hard drug clusters.

### Excluded

Final decision memos and polished narrative (phase 3); repo bootstrap (phase 0); run contract definition (phase 1).

---

## 3. Prerequisites & inputs

- Phase 1 merged: configs, provenance contract, generalized biovalidation.
- Data: processed response matrix, `response_latent_space/results/embeddings/nmf_k3`, `nmf_k8`, cluster assignments, drug/cell metadata as required per script.

---

## 4. Deliverables

- One or more `run_id` folders per analysis family, each with tables/figures + provenance.
- Intermediate summary CSVs suitable for phase 3 writing (no manual editing).

---

## 5. File changes

| Area | Files (illustrative) |
|------|----------------------|
| Configs | `configs/stage1_5/embedding_compare_*.yaml`, `partition_k8_*.yaml`, `personalization_*.yaml`, `factors_nmf_k8.yaml`, `drug_neighborhoods.yaml` |
| Scripts | `scripts/analysis/compare_embeddings_nmf.py`, `compare_partition_k8_c2_c3.py`, `within_cluster_personalization.py`, `interpret_factors_nmf_k8.py`, `drug_neighborhood_report.py` |
| Package | Extend [`response_latent_space/src/`](../../response_latent_space/src/) only where shared logic is reused (avoid duplication). |
| Tests | Minimal tests for critical metrics (optional but encouraged for bootstrap/ARI aggregation). |

---

## 6. Execution

### Branch options

**Option A — one branch per major analysis (parallel review):**

| Work | Branch |
|------|--------|
| k8 c2 vs c3 + embedding compare glue | `feat/k8-c2-vs-c3` (may include 2A compare scripts) |
| Within-cluster personalization | `feat/within-cluster-personalization` |
| Factor interpretation | `feat/factor-interpretation` |
| Drug neighborhoods | `feat/drug-neighborhood-report` |

**Option B:** sequential features on one branch after phase 1 merges.

Use **git worktrees** when running parallel streams (e.g. `../repo-wt-k8`).

### Tasks — 2A

- [ ] Implement `compare_embeddings_nmf.py` + config; write run outputs + provenance.
- [ ] Implement `compare_partition_k8_c2_c3.py` + config; include singleton audit and bootstrap ARI summary.
- [ ] Wire Makefile targets; run regression vs `master_stage1_summary.csv` where metrics should align.

### Tasks — 2B

- [ ] Implement `within_cluster_personalization.py` with configurable k-NN and ranking depth.
- [ ] Implement `interpret_factors_nmf_k8.py` (tables + optional auto-summary JSON for writers).
- [ ] Implement `drug_neighborhood_report.py` using local enrichment only.
- [ ] Tag checkpoints as appropriate (e.g. `v0.2-stage1-5-partition-review`, `v0.3-stage1-5-personalization-check`) when milestones are real.

---

## 7. Exit criteria (definition of done)

- Each script runs with **only** config + env; outputs land under `results/analysis_runs/<run_id>/` with full provenance.
- Metrics and definitions are documented in run metadata or companion `metrics_used.json` (lightweight) so phase 3 cannot misquote numbers.
- **2A vs 2B:** 2A outputs are measurement-heavy; 2B outputs include interpretation-ready tables with caveats fields where needed.
- Singleton behavior for k8 c=3 is **flagged**, not hidden.

---

## 8. Risks & caveats

- **Silhouette** depends on chosen partition—do not compare k=3 vs k=8 partitions without stating label source.
- **Bootstrap ARI** near 1.0 with tiny subsamples can be misleading; report n, seed, and distribution.
- **Biological judgment** belongs in phase 3 prose; phase 2 should output evidence tables and short neutral notes only.
