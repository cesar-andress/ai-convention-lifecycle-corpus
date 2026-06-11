# AI Convention Lifecycle Corpus

Replication package for the empirical study **Adoption Is Not Maintenance: The Adoption–Maintenance Gap in AI Instructional Artifacts on GitHub**.

The corpus bundles frozen protocols, seed lists, extraction and analysis code, aggregated tabular datasets, headline statistics, and a manual-validation sample for the v2 cohort: **220** adopted repositories discovered, **209** successfully extracted and analyzed, **13,988** ever-introduced artifact instances.

The companion LaTeX manuscript is in **`../paper/`** (sibling directory) and is not part of this deposit.

## 1. Dataset overview

This deposit supports reproduction of a mining-software-repositories study that measures the gap between **adoption** (an AI instructional artifact path present in `git` HEAD at observation time) and **maintenance** (at least one qualifying git touch within the last *T* days before observation end).

**Primary analysis window:** *T* = 180 days.

**Artifact scope** (frozen in `protocol/lifecycle_v1.yaml`): paths matching AI agent-governance conventions such as `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `.cursor/rules/*`, prompt directories, and related patterns. Generic documentation files (for example `README.md`, `CONTRIBUTING.md`) are excluded.

**Units of analysis:** artifact instance (primary), repository (secondary), artifact type and introduction cohort (exploratory strata where sample size permits).

**Bundled aggregates** (CC-BY 4.0): discovery list, per-commit touch history, artifact-level tables, covariates, state-enriched artifacts, JSON/CSV results, and a 40-row annotation sheet.

**Not bundled:** full git clones under `data/repos/` (large; per-repository licenses). Re-extraction clones public URLs from `data/lifecycle/discovered_v2.csv`.

**Code license:** MIT (`LICENSE`).

## 2. Research questions

1. **Adoption vs. maintenance:** To what extent does HEAD presence of AI instructional artifacts reflect git-based maintenance of those same paths?
2. **Magnitude of the gap:** How large is the adoption–maintenance gap among mature-present artifacts at *T* ∈ {90, 180, 365} days, and at the primary window (*T* = 180)?
3. **Level aggregation:** Does repository-level maintenance mask artifact-level git dormancy?
4. **Heterogeneity:** How does gap magnitude vary by artifact type and introduction cohort when denominators are sufficient?
5. **Outcome distinction:** How do deletion (path removed from HEAD) and git dormancy (present but untouchéd) compare among ever-introduced artifacts?

Operational definitions and state machine rules are frozen in `protocol/adoption_maintenance_v1.yaml` and scale parameters in `protocol/adoption_maintenance_v2.yaml`.

## 3. Repository structure

```
.
├── protocol/                    # Frozen YAML protocols (detection, extraction, analysis)
├── data/lifecycle/              # Discovery CSV, parquets, extraction/build metadata
├── results/lifecycle/           # Headline JSON/CSV outputs
├── scripts/lifecycle/           # Python pipeline (import path: lifecycle/)
├── lifecycle -> scripts/lifecycle   # Symlink for PYTHONPATH compatibility
├── annotation/                  # Manual-validation sheet (40 rows)
├── seeds/                       # GitHub URL seed pools
├── seeds.txt                    # AI-adopter seed pool
├── seeds_stratified.txt         # Stratified AI-adopter seed pool
├── metadata/study_manifest.json # Sample counts and headline checksums
├── docs/                        # Reproduction, migration, and legacy-removal notes
├── zenodo/                      # Zenodo deposit metadata
├── Makefile                     # install, analyze, lifecycle-v2, verify-headline
├── requirements.txt             # Python dependencies
├── CITATION.cff                 # Citation metadata
└── LICENSE                      # MIT (code)
```

| Path | Role |
|------|------|
| `protocol/lifecycle_v1.yaml` | Artifact patterns, extraction outputs, build rules |
| `protocol/adoption_maintenance_v1.yaml` | Adoption, maintenance, maturity, gap definitions |
| `protocol/adoption_maintenance_v2.yaml` | v2 scale, seeds, bootstrap, output paths |
| `data/lifecycle/discovered_v2.csv` | Adopted repository list (220 rows) |
| `data/lifecycle/touch_history.parquet` | Per-commit touch events |
| `data/lifecycle/artifacts.parquet` | Artifact-level export table |
| `data/lifecycle/artifacts_full.parquet` | Extended artifact fields for analysis |
| `data/lifecycle/artifact_states_v2.parquet` | State-enriched artifact table |
| `results/lifecycle/adoption_maintenance_v2.json` | Primary summary statistics |
| `annotation/annotation_sheet.csv` | Stratified manual validation sample |

See `docs/reproducibility.md` for step-by-step commands.

## 4. Reproduction instructions

### Quick verification (offline, bundled data)

From the corpus root:

```bash
python3 -m venv .venv
source .venv/bin/activate
make install
make verify-headline
```

`make verify-headline` checks that `results/lifecycle/adoption_maintenance_v2.json` reports **209** analyzed repositories and artifact-level mature-present gap ≈ **56.0%** at *T* = 180.

### Recompute analysis from frozen parquets (offline)

Requires no network or local clones if `artifacts_full.parquet` is present:

```bash
make analyze
```

### Full pipeline from GitHub (network + git required)

Clone repositories into `data/repos/` and rerun discovery → extraction → build → analysis:

```bash
make lifecycle-v2
```

Detailed commands, flags, and output paths: **`docs/reproducibility.md`**.

## 5. Expected outputs

After a successful full run (`make lifecycle-v2`) or offline analysis (`make analyze`), the following v2 outputs should exist:

| Output | Description |
|--------|-------------|
| `data/lifecycle/artifact_states_v2.parquet` | Per-artifact states (DELETED, TOO_YOUNG, ACTIVE, DORMANT) at 90/180/365 days |
| `results/lifecycle/bootstrap_v2.json` | Cluster-bootstrap confidence intervals (5,000 replicates) |
| `results/lifecycle/loo_v2.csv` | Leave-one-repository-out sensitivity |
| `annotation/annotation_sheet.csv` | Stratified validation sample (20 git-dormant + 20 active at *T* = 180) |
| `results/lifecycle/adoption_maintenance_v2.json` | Headline gaps, bootstrap summary, annotation metadata, threshold breakdown |
| `results/lifecycle/funnel_v2.csv` | Analysis funnel by maintenance window |
| `results/lifecycle/discovery_funnel_v2.csv` | Discovery attrition (after discovery step) |
| `results/lifecycle/extract_attrition_v2.csv` | Extraction skip log (after extraction step) |
| `results/lifecycle/cohort_gap_v2.csv` | Gap by introduction quarter |
| `results/lifecycle/type_gap_age_adjusted.csv` | Age-adjusted gap comparison by artifact type |

**Headline values** (primary, *T* = 180, bundled release):

| Metric | Value |
|--------|-------|
| Analyzed repositories | 209 |
| Ever-introduced artifacts | 13,988 |
| Mature-present artifacts | 577 |
| Artifact-level mature-present gap | 56.0% |
| Repository-level gap | 7.2% |

## 6. Hardware requirements

| Resource | Minimum | Recommended (full re-extraction) |
|----------|---------|--------------------------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8–16 GB |
| Disk | 2 GB (bundled aggregates only) | 50–100 GB free (`data/repos/` clones for ~220 repositories) |
| Network | Not required for `make analyze` | Stable broadband for `make lifecycle-v2` |
| Software | Python ≥ 3.10, `git` | Same; Linux or macOS tested |

Bootstrap analysis (5,000 cluster replicates) is CPU-bound; expect several minutes on a laptop. Full git extraction time depends on clone sizes and GitHub rate limits; resume mode (`--resume` on extraction) supports interrupted runs.

## 7. Limitations

- **Observation end is extraction-time HEAD:** Metrics describe git history up to each repository’s last commit at extraction, not a fixed calendar date across repos.
- **Git touches only:** Maintenance is operationalized as qualifying commits touching the artifact path; semantic relevance, reading, or out-of-band edits are not observed.
- **Seed-driven sample:** Repositories enter via curated GitHub URL seeds (AI-adopter and general-OSS pools), not a random sample of all open-source projects.
- **HEAD presence as adoption:** A path present at observation end counts as adopted even if content is stale or placeholder text.
- **No bundled clones:** Re-extraction requires cloning public repositories; some URLs may become unavailable, private, or renamed over time.
- **Manual validation is partial:** The annotation sheet covers 40 stratified artifact instances; automated label columns are heuristic pre-fills (`lifecycle/fill_annotation.py`) and do not replace human adjudication for new runs.
- **Non-comparable strata:** Type and cohort breakdowns are reported only where minimum cell sizes in the protocol are met.

## Citation

Cite this corpus via `CITATION.cff`. After Zenodo registration, use the assigned DOI.

## Further documentation

- `docs/reproducibility.md` — exact reproduction commands
- `docs/dataset_description.md` — sampling, definitions, funnels, validity (standalone reference)
- `docs/repository_migration.md` — layout mapping from the internal study workspace
- `docs/separation_audit.md` — paper/corpus boundary and verification
- `docs/legacy_removal_log.md` — removed pilot artifacts (corpus copy only)
- `docs/commit_policy.md` — required git commit workflow for this repository
- `metadata/study_manifest.json` — machine-readable sample summary
