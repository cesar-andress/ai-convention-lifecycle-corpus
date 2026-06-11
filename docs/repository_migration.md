# Repository migration report

Migration from internal study workspace (`../` relative to this corpus) to public Zenodo corpus layout.

**Policy:** files were **copied**; nothing was deleted from the source workspace.

**Date:** 2026-06-11  
**Study:** Adoption Is Not Maintenance (adoption_maintenance v2)

---

## Summary

| Category | Files copied | Notes |
|----------|-------------|-------|
| Protocol | 3 | Frozen YAML |
| Scripts | 14 | `lifecycle/*.py` → `scripts/lifecycle/` |
| Data (aggregates) | 10 | Parquet/CSV/JSON only |
| Results | 17 | v2 headline + v1 legacy outputs |
| Annotation | 1 | 40-row validation sheet |
| Seeds | 8 | URL lists for discovery |
| Metadata / docs | 4 | Manifest, README, CITATION, this file |

**Excluded (documented):** `data/repos/` (full git clones), `paper/`, root-level legacy scripts (`discover.py`, `v4/`), non-headline protocol YAML.

---

## Protocol

| Source path | Destination path | Reason |
|-------------|------------------|--------|
| `protocol/lifecycle_v1.yaml` | `protocol/lifecycle_v1.yaml` | Frozen artifact detection, extraction, and build rules |
| `protocol/adoption_maintenance_v1.yaml` | `protocol/adoption_maintenance_v1.yaml` | Base adoption/maintenance state model and gap definitions |
| `protocol/adoption_maintenance_v2.yaml` | `protocol/adoption_maintenance_v2.yaml` | v2 scale, seeds, bootstrap, and headline output paths |

---

## Scripts (`lifecycle/` → `scripts/lifecycle/`)

| Source path | Destination path | Reason |
|-------------|------------------|--------|
| `lifecycle/__init__.py` | `scripts/lifecycle/__init__.py` | Package marker |
| `lifecycle/adoption_maintenance.py` | `scripts/lifecycle/adoption_maintenance.py` | v1 gap metrics and state assignment |
| `lifecycle/adoption_maintenance_v2.py` | `scripts/lifecycle/adoption_maintenance_v2.py` | v2 headline analysis, bootstrap, LOO |
| `lifecycle/analyze.py` | `scripts/lifecycle/analyze.py` | Legacy survival-style analysis (v1 outputs) |
| `lifecycle/build_dataset.py` | `scripts/lifecycle/build_dataset.py` | Touch history → artifact parquet |
| `lifecycle/detection.py` | `scripts/lifecycle/detection.py` | Shared path-pattern matching |
| `lifecycle/discover.py` | `scripts/lifecycle/discover.py` | v1 discovery (referenced by pilot tooling) |
| `lifecycle/discover_v2.py` | `scripts/lifecycle/discover_v2.py` | v2 discovery and funnel |
| `lifecycle/extract_history.py` | `scripts/lifecycle/extract_history.py` | Git clone and per-path touch extraction |
| `lifecycle/fill_annotation.py` | `scripts/lifecycle/fill_annotation.py` | Annotation sheet label helper |
| `lifecycle/git_utils.py` | `scripts/lifecycle/git_utils.py` | Git subprocess helpers |
| `lifecycle/robustness.py` | `scripts/lifecycle/robustness.py` | v1 cluster bootstrap / LOO |
| `lifecycle/run_pilot.py` | `scripts/lifecycle/run_pilot.py` | Pilot orchestration (historical) |
| `lifecycle/run_v2.py` | `scripts/lifecycle/run_v2.py` | v2 end-to-end pipeline entry point |

**Compatibility:** symlink `lifecycle → scripts/lifecycle` at corpus root so `ROOT/lifecycle/` paths in scripts resolve without modification.

---

## Data (`data/lifecycle/`)

| Source path | Destination path | Reason |
|-------------|------------------|--------|
| `data/lifecycle/discovered_v2.csv` | `data/lifecycle/discovered_v2.csv` | v2 adopted repository list (220 rows) |
| `data/lifecycle/discovered.csv` | `data/lifecycle/discovered.csv` | Earlier discovery pass (cross-check) |
| `data/lifecycle/touch_history.parquet` | `data/lifecycle/touch_history.parquet` | Per-commit touch rows (86{,}845 rows) |
| `data/lifecycle/artifacts.parquet` | `data/lifecycle/artifacts.parquet` | Artifact-level build table |
| `data/lifecycle/artifacts_full.parquet` | `data/lifecycle/artifacts_full.parquet` | Extended artifact fields |
| `data/lifecycle/repo_covariates.parquet` | `data/lifecycle/repo_covariates.parquet` | Repository covariates at extraction |
| `data/lifecycle/artifact_states_v2.parquet` | `data/lifecycle/artifact_states_v2.parquet` | v2 state-enriched artifact table |
| `data/lifecycle/artifact_states.parquet` | `data/lifecycle/artifact_states.parquet` | v1 state table (legacy) |
| `data/lifecycle/extract_meta.json` | `data/lifecycle/extract_meta.json` | Extraction scale metadata (209 ok / 11 skipped) |
| `data/lifecycle/artifacts_build_meta.json` | `data/lifecycle/artifacts_build_meta.json` | Build-step provenance |

---

## Results (`results/lifecycle/`)

| Source path | Destination path | Reason |
|-------------|------------------|--------|
| `results/lifecycle/adoption_maintenance_v2.json` | `results/lifecycle/adoption_maintenance_v2.json` | **Primary headline summary** for MSR paper |
| `results/lifecycle/bootstrap_v2.json` | `results/lifecycle/bootstrap_v2.json` | Cluster-bootstrap intervals |
| `results/lifecycle/loo_v2.csv` | `results/lifecycle/loo_v2.csv` | Leave-one-repository-out sensitivity |
| `results/lifecycle/funnel_v2.csv` | `results/lifecycle/funnel_v2.csv` | Analysis funnel by threshold |
| `results/lifecycle/discovery_funnel_v2.csv` | `results/lifecycle/discovery_funnel_v2.csv` | Discovery attrition funnel |
| `results/lifecycle/extract_attrition_v2.csv` | `results/lifecycle/extract_attrition_v2.csv` | Extraction skip log |
| `results/lifecycle/cohort_gap_v2.csv` | `results/lifecycle/cohort_gap_v2.csv` | Gap by introduction quarter |
| `results/lifecycle/type_gap_age_adjusted.csv` | `results/lifecycle/type_gap_age_adjusted.csv` | Age-adjusted type comparison |
| `results/lifecycle/adoption_maintenance.json` | `results/lifecycle/adoption_maintenance.json` | v1 gap summary (legacy) |
| `results/lifecycle/analysis.json` | `results/lifecycle/analysis.json` | v1 survival-style outputs |
| `results/lifecycle/robustness.json` | `results/lifecycle/robustness.json` | v1 robustness outputs |
| `results/lifecycle/funnel.csv` | `results/lifecycle/funnel.csv` | v1 funnel |
| `results/lifecycle/funnel_adoption_maintenance.csv` | `results/lifecycle/funnel_adoption_maintenance.csv` | v1 adoption funnel |
| `results/lifecycle/table_gap_by_type.csv` | `results/lifecycle/table_gap_by_type.csv` | Stratified gap by artifact type |
| `results/lifecycle/table_gap_by_cohort.csv` | `results/lifecycle/table_gap_by_cohort.csv` | Stratified gap by cohort |
| `results/lifecycle/table_repo_summary.csv` | `results/lifecycle/table_repo_summary.csv` | Per-repository summary |
| `results/lifecycle/table_stasis_by_type.csv` | `results/lifecycle/table_stasis_by_type.csv` | v1 stasis by type |

---

## Annotation

| Source path | Destination path | Reason |
|-------------|------------------|--------|
| `annotation/annotation_sheet.csv` | `annotation/annotation_sheet.csv` | Stratified manual validation (20 git-dormant + 20 active) |

---

## Seeds

| Source path | Destination path | Reason |
|-------------|------------------|--------|
| `seeds.txt` | `seeds.txt` | AI-adopter seed pool (protocol reference) |
| `seeds_stratified.txt` | `seeds_stratified.txt` | Stratified AI-adopter seeds |
| `seeds/lifecycle_gh_repo_search.txt` | `seeds/lifecycle_gh_repo_search.txt` | GitHub repo search expansion seeds |
| `seeds/lifecycle_gh_search.txt` | `seeds/lifecycle_gh_search.txt` | GitHub code search seeds |
| `seeds/lifecycle_cached_clones.txt` | `seeds/lifecycle_cached_clones.txt` | Cached clone fast-path list |
| `seeds/wave2_general_oss.txt` | `seeds/wave2_general_oss.txt` | General-OSS seed pool |
| `seeds/wave2_s2_priority.txt` | `seeds/wave2_s2_priority.txt` | Priority general-OSS seeds |
| `seeds/wave2_s0_candidates.txt` | `seeds/wave2_s0_candidates.txt` | Additional general-OSS candidates |

---

## Root / metadata / build

| Source path | Destination path | Reason |
|-------------|------------------|--------|
| `requirements.txt` | `requirements.txt` | Python dependencies for pipeline |
| — | `metadata/study_manifest.json` | Generated corpus manifest (headline counts) |
| — | `Makefile` | Corpus reproduction targets |
| — | `README.md`, `LICENSE`, `CITATION.cff` | Public release documentation |
| — | `zenodo/README.md` | Zenodo deposit checklist |

---

## Explicitly excluded

| Source path | Reason not copied |
|-------------|-------------------|
| `data/repos/**` | Full git clones; large; per-repository licenses; users re-clone from `discovered_v2.csv` |
| `paper/**` | LaTeX paper; separate submission artifact |
| `protocol/instructional_detection.yaml` | Out of scope for adoption_maintenance v2 headline |
| `protocol/stratified_validation.yaml` | Separate validation wave |
| `protocol/wave2_collection.yaml` | Collection metadata only |
| `discover.py`, `extract.py`, `metrics.py`, `v4/**` | Legacy / parallel studies |
| `lifecycle/__pycache__/**` | Bytecode cache |

---

## Verification

From corpus root:

```bash
make verify-headline
# Expected: OK: n_repos=209 artifact_gap= 0.56
```
