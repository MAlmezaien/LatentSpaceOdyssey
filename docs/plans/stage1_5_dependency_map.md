# Stage 1.5 — Dependency map

**Parent index:** [stage1_5_master.md](stage1_5_master.md)

---

## Ordering (hard)

1. **Phase 0 must merge before Phase 1.**  
   Phase 1 assumes git, packaging, baseline provenance helper, and path-hygiene direction exist.

2. **Phase 1 must merge before Phase 2.**  
   Phase 2 analysis scripts must write under `results/analysis_runs/<run_id>/` with the provenance bundle and **relative-path** policy defined in phase 1.

3. **Phase 3 only starts after Phase 2 outputs are frozen enough for writing.**  
   “Frozen enough” means: the tables/figures you will cite are produced by merged code, stored under concrete `run_id` folders, and are not expected to change without a new run and explicit doc revision.

---

## Merge gates (see also [master — Merge policy](stage1_5_master.md#merge-policy))

- Phase 2 branches do not merge until **provenance + relative paths** work on `main`.
- Phase 3 does not merge until cited **`run_id`s exist** and **pass QA**.

---

## Strategic intent

This ordering prevents the common failure mode: **biological conclusions committed before the repository and run contract are stable**, which invalidates both reproducibility and trust in the narrative.
