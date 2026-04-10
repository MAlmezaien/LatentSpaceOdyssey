# AGENTS.md

## Project mission

This repository studies response-defined latent spaces for personalised drug combinations.
The response matrix is the anchor. Pretrained cell/drug models are future priors, not the primary source of truth.

## Scientific guardrails

- Do not overclaim from hard clusters alone.
- Distinguish embedding quality from clustering quality.
- Treat singleton clusters as warning signals.
- Prioritize within-cluster heterogeneity and continuous factor structure.
- Local drug neighborhoods are more important than hard global drug cluster purity.

## Engineering guardrails

- Everything must be reproducible from code.
- Never manually edit generated results.
- Write outputs only inside `results/analysis_runs/<run_id>/` once that pipeline exists.
- Every run must record config, git commit --trailer "Made-with: Cursor", command, and metadata.
- Prefer scripts and config files over notebook-only logic.
- Keep `docs/decisions/` updated when scientific choices change.

## Directory expectations

- `configs/` — parameterization
- `scripts/` — executable logic
- `docs/current_state/` — latest factual state
- `docs/decisions/` — signed-off reasoning
- `docs/logs/` — work logs and plans
- `results/analysis_runs/` — run outputs (stage 1.5+)
- `reports/` — presentation-ready summaries

## Current phase

See `docs/plans/stage1_5_master.md`. Phase 0 establishes repo OS; later phases add stage 1.5 analysis contracts and reporting.

## Writing standards

- Be concise, evidence-based, and explicit about caveats.
- Do not describe a solution as "best" unless the metric and scope are stated.
- Prefer "primary working embedding" over "global optimum" when appropriate.

## Merge standard

No branch is ready to merge unless:

- Scripts run end-to-end where applicable
- Outputs are saved with provenance where required
- Docs are updated
- A QA review has been done when reporting science
