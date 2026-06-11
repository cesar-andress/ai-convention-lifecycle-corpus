# Replication package inventory

**Release title:** AI Convention Lifecycle Corpus v2.0.0 — Expanded 209-Repository Dataset and Adoption–Maintenance Framework  
**DOI:** [https://doi.org/10.5281/zenodo.20637986](https://doi.org/10.5281/zenodo.20637986)

This document describes **data, code, and protocols only**. It does not reproduce manuscript text, figures, or paper-specific claims.

Machine-readable summary: `metadata/study_manifest.json`.

---

## Repository structure

Top-level layout for Zenodo users and replicators. Detailed file lists follow in later sections.

| Component | Path | Purpose |
|-----------|------|---------|
| Protocol specifications | `protocol/` | Frozen detection rules, extraction settings, and measurement thresholds |
| Seed pools | `seeds/` | Curated GitHub URL pools used for repository discovery |
| Analysis scripts | `scripts/lifecycle/` | Discovery, extraction, dataset build, and gap analyses |
| Build automation | `Makefile` | Package-level reproduction targets |
| Processed data | `data/lifecycle/` | Discovery tables, touch history, and extracted parquet datasets |
| Results | `results/lifecycle/` | Headline gaps, bootstrap intervals, LOO sensitivity, and robustness outputs |
| Headline gap bundle | `results/lifecycle/adoption_maintenance_v2.json` | Offline verification of reported headline statistics |
| Annotation sample | `annotation/annotation_sheet.csv` | Stratified 40-row manual-validation sample |
| Package metadata | `metadata/` | Study manifest, Zenodo deposit template, and this inventory |
| Documentation | `docs/` | Reproducibility guide, dataset description, and release audits |
| Citation metadata | `CITATION.cff` | Dataset version and preferred citation string |
| Root overview | `README.md` | Standalone package overview and reproduction guide |
| Zenodo checklist | `zenodo/` | Deposit checklist (see `metadata/zenodo.json`) |

**Not bundled:** full git clones under `data/repos/` (per-repository licenses; clone at reproduction time).

---

## Protocols

Location: `protocol/`

Frozen YAML specifications. Do not edit for reproduction; copy and version if extending the study.

| File | Role |
|------|------|
| `lifecycle_v1.yaml` | Artifact path patterns, extraction outputs, dataset build rules |
| `adoption_maintenance_v1.yaml` | Adoption, maintenance, maturity, gap, and state-machine definitions |
| `adoption_maintenance_v2.yaml` | v2 scale parameters, seed file references, bootstrap settings, output paths |

---

## Scripts

Location: `scripts/lifecycle/`

Python pipeline. Run with `PYTHONPATH=./scripts` (set automatically by `Makefile`).

| Script | Role |
|--------|------|
| `run_v2.py` | End-to-end orchestrator: discover → extract → build → analyze |
| `discover_v2.py` | Repository discovery from seed pools; writes discovery CSV and funnel |
| `extract_history.py` | Git log extraction per repository; touch events and covariates |
| `build_dataset.py` | Builds artifact-level Parquet tables from touch history |
| `adoption_maintenance_v2.py` | Primary v2 analysis: gaps, bootstrap, LOO, cohort/type breakdowns |
| `adoption_maintenance.py` | v1 analysis module (legacy; retained for protocol compatibility) |
| `detection.py` | Path-pattern matching against protocol rules |
| `fill_annotation.py` | Heuristic pre-fill for manual validation sheet |
| `corpus_paths.py` | Root-relative path constants |
| `git_utils.py` | Git subprocess helpers |
| `__init__.py` | Package marker |

### Build targets

Defined in `Makefile`:

| Target | Command | Network | Produces |
|--------|---------|---------|----------|
| `install` | `pip install -r requirements.txt` | optional | Python deps |
| `verify-headline` | checks bundled JSON | no | stdout OK line |
| `analyze` | `adoption_maintenance_v2.py` | no | refreshed results under `results/lifecycle/` |
| `lifecycle-v2` | `run_v2.py` | yes | full data + results refresh |

Dependencies: `requirements.txt` (`pyyaml`, `pandas`, `pyarrow`, `numpy`).

---

## Seed lists

Location: `seeds/`

Curated GitHub URL pools referenced by `protocol/adoption_maintenance_v2.yaml`.

| File | Role |
|------|------|
| `seeds.txt` | Primary seed pool |
| `seeds_stratified.txt` | Stratified seed pool |
| `wave2_s0_candidates.txt` | Wave-2 candidate URLs |
| `wave2_s2_priority.txt` | Wave-2 priority URLs |
| `wave2_general_oss.txt` | General open-source expansion pool |
| `lifecycle_cached_clones.txt` | Previously cloned repository URLs |
| `lifecycle_gh_repo_search.txt` | GitHub search-derived candidates |

---

## Datasets

Location: `data/lifecycle/`

Aggregated tabular outputs (CC-BY 4.0). Git clones are **not** included.

| File | Format | Description |
|------|--------|-------------|
| `discovered_v2.csv` | CSV | 220-row adopted repository list (owner, repo, URL, discovery metadata) |
| `touch_history.parquet` | Parquet | Per-commit touch events on matched artifact paths |
| `artifacts.parquet` | Parquet | Artifact-level export table |
| `artifacts_full.parquet` | Parquet | Extended artifact fields for analysis (input to `make analyze`) |
| `artifact_states_v2.parquet` | Parquet | State-enriched artifacts (DELETED, TOO_YOUNG, ACTIVE, DORMANT) at 90/180/365 d |
| `repo_covariates.parquet` | Parquet | Repository-level covariates at extraction |
| `extract_meta.json` | JSON | Extraction run metadata (timestamps, skip counts) |
| `artifacts_build_meta.json` | JSON | Dataset build metadata |

---

## Analysis outputs

Location: `results/lifecycle/`

| File | Format | Description |
|------|--------|-------------|
| `adoption_maintenance_v2.json` | JSON | **Primary headline statistics**, bootstrap summary, annotation metadata |
| `bootstrap_v2.json` | JSON | Cluster-bootstrap CIs (5,000 replicates) |
| `loo_v2.csv` | CSV | Leave-one-repository-out sensitivity |
| `funnel_v2.csv` | CSV | Analysis funnel by maintenance window |
| `discovery_funnel_v2.csv` | CSV | Discovery attrition |
| `extract_attrition_v2.csv` | CSV | Extraction skip log |
| `cohort_gap_v2.csv` | CSV | Gap by introduction quarter |
| `type_gap_age_adjusted.csv` | CSV | Age-adjusted gap by artifact type |

### Headline values

Source: `adoption_maintenance_v2.json` at *T* = 180 d.

| Metric | Value |
|--------|------:|
| Analyzed repositories | 209 |
| Ever-introduced artifacts | 13,988 |
| Mature-present artifacts | 577 |
| Artifact-level mature-present gap | 56.0% |
| Repository-level gap | 7.2% |

---

## Annotation

Location: `annotation/`

| File | Format | Description |
|------|--------|-------------|
| `annotation_sheet.csv` | CSV | 40-row stratified sample (20 git-dormant + 20 active at *T* = 180 d) |

---

## Package metadata

Location: `metadata/`

| File | Description |
|------|-------------|
| `study_manifest.json` | Sample counts, protocol paths, headline checksums |
| `dataset_card.md` | Academic dataset card (summary, motivation, limitations, ethics) |
| `zenodo.json` | Zenodo deposit field template |
| `replication_package.md` | This inventory |

---

## Root files

| File | Description |
|------|-------------|
| `README.md` | Standalone package overview and reproduction guide |
| `CITATION.cff` | Citation metadata (dataset + companion paper reference) |
| `LICENSE` | MIT license for source code |
| `Makefile` | Reproduction targets |
| `requirements.txt` | Python dependencies |

---

## Supporting documentation

Location: `docs/`

Technical notes for reproduction and release auditing. **No manuscript content.**

| File | Purpose |
|------|---------|
| `DATASET.md` | Standalone dataset landing page for independent discovery |
| `reproducibility.md` | Step-by-step commands and flags |
| `dataset_description.md` | Sampling frame, definitions, funnels |
| `separation_audit.md` | Boundary between corpus and paper repository |
| `public_release_audit.md` | Leakage audit for Zenodo release |
| `repository_migration.md` | Layout mapping from internal workspace |
| `legacy_removal_log.md` | Removed pilot artifacts |
| `commit_policy.md` | Git commit workflow for this repository |

---

## Explicitly excluded from deposit

| Path | Reason |
|------|--------|
| `.git/` | Version control metadata |
| `.venv/` | Local Python environment |
| `data/repos/` | Large third-party git clones (per-repo licenses) |
| `__pycache__/` | Python bytecode |

---

## Citation

**Release title:** AI Convention Lifecycle Corpus v2.0.0 — Expanded 209-Repository Dataset and Adoption–Maintenance Framework  
**Dataset DOI:** [https://doi.org/10.5281/zenodo.20637986](https://doi.org/10.5281/zenodo.20637986)

See also `CITATION.cff` and `README.md` (Citation section).
