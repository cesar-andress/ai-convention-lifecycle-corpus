# Repository migration report

Migration from internal study workspace (`../` relative to this corpus) to public Zenodo corpus layout.

**Policy:** files were **copied**; nothing was deleted from the source workspace.

**Date:** 2026-06-11  
**Study:** Adoption Is Not Maintenance (adoption_maintenance v2)

---

## Summary

| Category | Files in corpus | Notes |
|----------|-----------------|-------|
| Protocol | 3 | Frozen YAML |
| Scripts | 10 | v2 pipeline only (see `docs/legacy_removal_log.md`) |
| Data (aggregates) | 8 | Parquet/CSV/JSON for v2 cohort |
| Results | 8 | v2 headline outputs only |
| Annotation | 1 | 40-row validation sheet |
| Seeds | 7 | URL lists referenced by v2 protocol |
| Metadata / docs | 5 | Manifest, README, migration, legacy log, CITATION |

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
| `lifecycle/build_dataset.py` | `scripts/lifecycle/build_dataset.py` | Touch history → artifact parquet; `load_artifact_frame` |
| `lifecycle/detection.py` | `scripts/lifecycle/detection.py` | Shared path-pattern matching |
| `lifecycle/discover_v2.py` | `scripts/lifecycle/discover_v2.py` | v2 discovery and funnel |
| `lifecycle/extract_history.py` | `scripts/lifecycle/extract_history.py` | Git clone and per-path touch extraction |
| `lifecycle/fill_annotation.py` | `scripts/lifecycle/fill_annotation.py` | Annotation sheet label helper |
| `lifecycle/git_utils.py` | `scripts/lifecycle/git_utils.py` | Git subprocess helpers |
| `lifecycle/run_v2.py` | `scripts/lifecycle/run_v2.py` | v2 end-to-end pipeline entry point |

**Removed after copy (corpus only):** `analyze.py`, `discover.py`, `run_pilot.py`, `robustness.py` — see `docs/legacy_removal_log.md`.

**Compatibility:** symlink `lifecycle → scripts/lifecycle` at corpus root so `ROOT/lifecycle/` paths in scripts resolve without modification.

---

## Data (`data/lifecycle/`)

| Source path | Destination path | Reason |
|-------------|------------------|--------|
| `data/lifecycle/discovered_v2.csv` | `data/lifecycle/discovered_v2.csv` | v2 adopted repository list (220 rows) |
| `data/lifecycle/touch_history.parquet` | `data/lifecycle/touch_history.parquet` | Per-commit touch rows (86{,}845 rows) |
| `data/lifecycle/artifacts.parquet` | `data/lifecycle/artifacts.parquet` | Artifact-level build table |
| `data/lifecycle/artifacts_full.parquet` | `data/lifecycle/artifacts_full.parquet` | Extended artifact fields |
| `data/lifecycle/repo_covariates.parquet` | `data/lifecycle/repo_covariates.parquet` | Repository covariates at extraction |
| `data/lifecycle/artifact_states_v2.parquet` | `data/lifecycle/artifact_states_v2.parquet` | v2 state-enriched artifact table |
| `data/lifecycle/extract_meta.json` | `data/lifecycle/extract_meta.json` | Extraction scale metadata (209 ok / 11 skipped) |
| `data/lifecycle/artifacts_build_meta.json` | `data/lifecycle/artifacts_build_meta.json` | Build-step provenance |

**Removed after copy:** `discovered.csv`, `artifact_states.parquet` (v1 tables).

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

**Removed after copy:** v1 JSON/CSV results (`adoption_maintenance.json`, `analysis.json`, `robustness.json`, funnel and table CSVs). See `docs/legacy_removal_log.md`.

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
