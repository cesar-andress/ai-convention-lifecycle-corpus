# Legacy removal log

**Date:** 2026-06-10  
**Scope:** `ai-convention-lifecycle-corpus/` only (internal study workspace unchanged).  
**Goal:** retain assets required to reproduce the final **Adoption Is Not Maintenance** study (`adoption_maintenance_v2`).

---

## Scripts removed

| Removed path | Reason removed | Replacement |
|--------------|----------------|-------------|
| `scripts/lifecycle/analyze.py` | v1 survival / Cox-style exploratory analysis; not part of v2 headline pipeline | `load_artifact_frame()` moved to `scripts/lifecycle/build_dataset.py`; gap metrics in `adoption_maintenance.py` / `adoption_maintenance_v2.py` |
| `scripts/lifecycle/discover.py` | v1 repository discovery (pilot scale) | `scripts/lifecycle/discover_v2.py` |
| `scripts/lifecycle/run_pilot.py` | Pilot orchestration chaining v1 discover → extract → analyze | `scripts/lifecycle/run_v2.py` |
| `scripts/lifecycle/robustness.py` | v1 cluster-bootstrap / LOO (separate from v2 outputs) | Bootstrap and LOO in `scripts/lifecycle/adoption_maintenance_v2.py` → `bootstrap_v2.json`, `loo_v2.csv` |

## Script edits (not removed)

| Path | Change | Reason |
|------|--------|--------|
| `scripts/lifecycle/adoption_maintenance.py` | Removed v1 CLI (`main`); library-only | v1 standalone runner produced deprecated outputs |
| `scripts/lifecycle/discover_v2.py` | Removed `--also-write-legacy-discovered` | Avoid regenerating v1 `discovered.csv` |
| `scripts/lifecycle/run_v2.py` | Dropped legacy discover flag from default step | Align with v2-only corpus |
| `scripts/lifecycle/build_dataset.py` | Added `load_artifact_frame()` | Decouple analysis from deleted `analyze.py` |
| `requirements.txt` | Removed `statsmodels`, `scipy`, `scikit-learn` | Only needed by deleted v1 survival / robustness code |

---

## Data removed

| Removed path | Reason removed | Replacement |
|--------------|----------------|-------------|
| `data/lifecycle/discovered.csv` | v1 discovery list (duplicate of v2 cohort) | `data/lifecycle/discovered_v2.csv` |
| `data/lifecycle/artifact_states.parquet` | v1 state-enriched artifact table | `data/lifecycle/artifact_states_v2.parquet` |

---

## Results removed

| Removed path | Reason removed | Replacement |
|--------------|----------------|-------------|
| `results/lifecycle/adoption_maintenance.json` | v1 gap summary | `results/lifecycle/adoption_maintenance_v2.json` |
| `results/lifecycle/analysis.json` | v1 survival-style outputs | Headline gap in `adoption_maintenance_v2.json` |
| `results/lifecycle/robustness.json` | v1 bootstrap / LOO | `bootstrap_v2.json`, `loo_v2.csv` |
| `results/lifecycle/funnel.csv` | v1 lifecycle funnel | `funnel_v2.csv`, `discovery_funnel_v2.csv` |
| `results/lifecycle/funnel_adoption_maintenance.csv` | v1 adoption funnel | `funnel_v2.csv` |
| `results/lifecycle/table_gap_by_type.csv` | v1 type table (unadjusted) | `type_gap_age_adjusted.csv` |
| `results/lifecycle/table_gap_by_cohort.csv` | v1 cohort table | `cohort_gap_v2.csv` |
| `results/lifecycle/table_repo_summary.csv` | v1 per-repo summary | `loo_v2.csv` (sensitivity) + `adoption_maintenance_v2.json` |
| `results/lifecycle/table_stasis_by_type.csv` | v1 stasis exploratory table | Threshold breakdown in `adoption_maintenance_v2.json` |

---

## Seeds removed

| Removed path | Reason removed | Replacement |
|--------------|----------------|-------------|
| `seeds/lifecycle_gh_search.txt` | GitHub **code** search pilot pool; not referenced in `adoption_maintenance_v2.yaml` | `seeds/lifecycle_gh_repo_search.txt` |

---

## Retained (final study assets)

**Protocols:** `protocol/lifecycle_v1.yaml`, `protocol/adoption_maintenance_v1.yaml`, `protocol/adoption_maintenance_v2.yaml` (v2 extends v1; v1 extends lifecycle detection spec).

**Pipeline:** `run_v2.py` → `discover_v2.py` → `extract_history.py` → `build_dataset.py` → `adoption_maintenance_v2.py` (+ shared `detection.py`, `git_utils.py`, `fill_annotation.py`, `adoption_maintenance.py`).

**Data:** `discovered_v2.csv`, `touch_history.parquet`, `artifacts.parquet`, `artifacts_full.parquet`, `repo_covariates.parquet`, `artifact_states_v2.parquet`, `extract_meta.json`, `artifacts_build_meta.json`.

**Results:** all `*_v2.*` outputs plus `type_gap_age_adjusted.csv`, `extract_attrition_v2.csv`.

**Annotation:** `annotation/annotation_sheet.csv`.

**Seeds:** `seeds/seeds.txt`, `seeds/seeds_stratified.txt`, and all wave-2 / cached-clone / repo-search pools listed in `adoption_maintenance_v2.yaml`.

---

## Never copied / already excluded

These legacy artifacts remain only in the internal workspace (see `docs/repository_migration.md`):

- Co-change study scripts and data (`v4/`, root-level co-change pipelines)
- `protocol/stratified_validation.yaml`, `protocol/wave2_collection.yaml`, `protocol/instructional_detection.yaml`
- Exploratory notebooks and intermediate pilot outputs under the private repo
- Full git clones (`data/repos/`)
