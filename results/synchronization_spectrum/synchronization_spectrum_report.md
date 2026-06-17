# Synchronization spectrum pilot report

**Generated:** 2026-06-16 23:39 UTC  
**Repositories:** 25  
**Metric rows:** 140 `(repo × family)`  

Design: `docs/synchronization_spectrum_design.md`.
Cross-family scope: **repo-wide** (`ScopeMode.REPO_WIDE`).

## Stage 1 — Families and inclusion

| Spectrum group | Families |
|----------------|----------|
| instructions | claude_md, agents_md, cursor_rules |
| configuration | github_workflows, package_json, pyproject_toml, go_mod |
| documentation | readme, contributing, docs_index |

Inclusion criteria documented in the design note; anchors selected per family from HEAD/history.

## Stage 2 — Group-level medians

| spectrum_group | family_id | n_repo_rows | median_update_frequency_per_year | median_co_change_rate | median_sync_7 | median_sync_30 | median_median_update_lag_days_30 | median_lifecycle_persistence_rate |
|---|---|---|---|---|---|---|---|---|
| configuration | github_workflows | 5 | 0.613 | 0.0% | 1.1% | 5.5% | 13.802534722222223 | 100.0% |
| configuration | go_mod | 6 | 2.242 | 0.2% | 6.3% | 18.4% | 10.687065972222221 | 100.0% |
| configuration | package_json | 20 | 30.006 | 1.7% | 34.4% | 61.5% | 5.513237847222222 | 100.0% |
| configuration | pyproject_toml | 13 | 84.930 | 1.7% | 58.1% | 68.0% | 1.3222800925925926 | 100.0% |
| documentation | contributing | 22 | 4.702 | 0.1% | 6.7% | 22.1% | 10.830630787037038 | 100.0% |
| documentation | docs_index | 13 | 2.991 | 0.0% | 4.9% | 16.6% | 11.171435185185185 | 50.0% |
| documentation | readme | 25 | 70.125 | 1.1% | 65.5% | 92.0% | 3.7268171296296297 | 100.0% |
| instructions | agents_md | 18 | 3.147 | 0.1% | 4.8% | 13.0% | 9.718457754629629 | 100.0% |
| instructions | claude_md | 16 | 1.806 | 0.1% | 2.4% | 4.9% | 9.205127314814815 | 100.0% |
| instructions | cursor_rules | 2 | 0.245 | 0.0% | 0.6% | 2.0% | 14.547609953703702 | 0.0% |

## Stage 3 — Calibration index

| Spectrum group | Synchronization index (0≈docs, 1≈config) | Metrics |
|----------------|---------------------------------------------|---------|
| configuration | 0.917 | 6 |
| instructions | 0.151 | 6 |
| documentation | 0.253 | 6 |

Empirical ordering (composite index, 0=documentation … 1=configuration): instructions (0.151) < documentation (0.253) < configuration (0.917).
Median sync@30 by group (repo-wide scope): instructions 4.9%; documentation 22.1%; configuration 40.0%. README excluded from documentation group interpretation (release churn outlier).

## Stage 6 — Decision questions

### 1. Do instruction files behave more like configuration or documentation?

On the composite synchronization index, instruction files fall **closer to documentation** (index=0.151 vs configuration=0.917, documentation=0.253).

On sync@30 under repo-wide scope, instruction families (median 4.9–13.0%) lag both manifest configuration (18–68% by family) and narrative documentation (CONTRIBUTING/docs-index ~17–22%; root README is an outlier at 92% due to release churn).

### 2. Is synchronization measurably different?

Yes at pilot scale: group-level median sync@30 ranges from 4.9% (instructions) to 40.0% (configuration), Δ=35.1%.

### 3. Is drift merely anecdotal or part of a broader synchronization pattern?

Validated drift candidates (misguidance v2) show **real but narrow** path-level drift. This pilot links drift to **systematically low instruction–code synchronization**: instruction files update in response to repo-wide code changes less often than dependency manifests and less often than CONTRIBUTING-style documentation, so stale path references are a predictable consequence rather than isolated anecdotes.

### 4. Is this sufficient for a dedicated EMSE/IST paper?

**Pilot evidence supports a positioning paper** whose contribution is evolutionary behavior of AI instruction files relative to configuration and documentation — not stale reference counts. Requirements before submission: scale beyond 25 repos with pre-registered family detectors, report sensitivity to scope mode, and pair quantitative spectrum positioning with qualitative drift audit (ground-truth sample).

## Interpretation guardrails

- Pilot sample is not population-representative.
- Repo-wide scope may under-estimate instruction sync vs content-referenced scope.
- Configuration families include bot-driven manifest touches; interpret co-change accordingly.
- Do not extrapolate headline lifecycle gaps (209 repos) to this 25-repo pilot.
