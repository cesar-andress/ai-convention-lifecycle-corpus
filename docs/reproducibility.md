# Reproducibility guide

All commands assume the **corpus root** as the working directory. Paths are relative. Set `PYTHONPATH=.` (the `Makefile` does this automatically).

## 0. Environment

```bash
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
make install
```

Dependencies: `requirements.txt` (`pyyaml`, `pandas`, `pyarrow`, `numpy`).

Confirm the import symlink exists:

```bash
test -L lifecycle && test lifecycle -ef scripts/lifecycle && echo "OK: lifecycle symlink"
```

## 1. Full end-to-end pipeline

Requires **network access**, **`git`**, and disk space for clones under `data/repos/`:

```bash
make lifecycle-v2
```

This executes, in order:

1. Discovery (append mode on bundled `data/lifecycle/discovered_v2.csv`)
2. Git extraction with resume
3. Artifact build
4. Adoption–maintenance v2 analysis

Equivalent manual invocation:

```bash
export PYTHONPATH=.

python lifecycle/run_v2.py
```

## 2. Step-by-step regeneration

Use these commands to regenerate each output class independently. Skip §2.1 if you keep the bundled `data/lifecycle/discovered_v2.csv`.

### 2.1 Discovery

Discover adopted repositories from all seed pools defined in `protocol/adoption_maintenance_v2.yaml`:

```bash
export PYTHONPATH=.

python lifecycle/discover_v2.py \
  --v2-config protocol/adoption_maintenance_v2.yaml \
  --lifecycle-config protocol/lifecycle_v1.yaml \
  --out data/lifecycle/discovered_v2.csv \
  --funnel-out results/lifecycle/discovery_funnel_v2.csv \
  --local-repos-dir data/repos
```

**Produces:**

- `data/lifecycle/discovered_v2.csv`
- `results/lifecycle/discovery_funnel_v2.csv`

To append additional candidates while preserving existing rows (as `run_v2.py` does):

```bash
python lifecycle/discover_v2.py \
  --append \
  --v2-config protocol/adoption_maintenance_v2.yaml \
  --lifecycle-config protocol/lifecycle_v1.yaml \
  --out data/lifecycle/discovered_v2.csv \
  --funnel-out results/lifecycle/discovery_funnel_v2.csv \
  --local-repos-dir data/repos \
  --only-seed-files \
    seeds/wave2_s0_candidates.txt \
    seeds/lifecycle_cached_clones.txt \
    seeds/lifecycle_gh_repo_search.txt
```

### 2.2 Extraction (touch history + covariates)

Clone each discovered repository and extract per-path git touch history.

**Fresh extract** (deletes stale parquets first):

```bash
python lifecycle/extract_history.py \
  --config protocol/lifecycle_v1.yaml \
  --discovered data/lifecycle/discovered_v2.csv \
  --repos-dir data/repos \
  --touch-out data/lifecycle/touch_history.parquet \
  --covariates-out data/lifecycle/repo_covariates.parquet \
  --attrition-out results/lifecycle/extract_attrition_v2.csv \
  --meta-out data/lifecycle/extract_meta.json
```

**Incremental extract** (resume after interruption; used by `make lifecycle-v2`):

```bash
python lifecycle/extract_history.py \
  --config protocol/lifecycle_v1.yaml \
  --discovered data/lifecycle/discovered_v2.csv \
  --repos-dir data/repos \
  --touch-out data/lifecycle/touch_history.parquet \
  --covariates-out data/lifecycle/repo_covariates.parquet \
  --attrition-out results/lifecycle/extract_attrition_v2.csv \
  --meta-out data/lifecycle/extract_meta.json \
  --resume
```

**Produces:**

- `data/lifecycle/touch_history.parquet`
- `data/lifecycle/repo_covariates.parquet`
- `results/lifecycle/extract_attrition_v2.csv`
- `data/lifecycle/extract_meta.json`

### 2.3 Artifact build

Aggregate touch rows into artifact-level tables:

```bash
python lifecycle/build_dataset.py \
  --config protocol/lifecycle_v1.yaml \
  --touch-history data/lifecycle/touch_history.parquet \
  --out data/lifecycle/artifacts.parquet
```

**Produces:**

- `data/lifecycle/artifacts.parquet`
- `data/lifecycle/artifacts_full.parquet`
- `data/lifecycle/artifacts_build_meta.json`

### 2.4 Adoption–maintenance v2 analysis

Single step that regenerates **artifact states**, **bootstrap**, **leave-one-out**, **annotation sheet**, and **final JSON/CSV outputs**:

```bash
python lifecycle/adoption_maintenance_v2.py \
  --v2-config protocol/adoption_maintenance_v2.yaml \
  --lifecycle-config protocol/lifecycle_v1.yaml \
  --discovered data/lifecycle/discovered_v2.csv \
  --repos-dir data/repos
```

Or via Makefile (same script, default arguments):

```bash
make analyze
```

**Produces:**

| Path | Content |
|------|---------|
| `data/lifecycle/artifact_states_v2.parquet` | State-enriched artifact table |
| `results/lifecycle/bootstrap_v2.json` | Cluster-bootstrap intervals |
| `results/lifecycle/loo_v2.csv` | Leave-one-repository-out table |
| `annotation/annotation_sheet.csv` | Stratified validation sample (40 rows) |
| `results/lifecycle/adoption_maintenance_v2.json` | Primary summary JSON |
| `results/lifecycle/funnel_v2.csv` | Threshold funnel |
| `results/lifecycle/cohort_gap_v2.csv` | Cohort-stratified gaps |
| `results/lifecycle/type_gap_age_adjusted.csv` | Age-adjusted type comparison |

The summary JSON embeds bootstrap statistics and annotation metadata; `bootstrap_v2.json` holds the full bootstrap object also written separately.

### 2.5 Annotation sheet refresh (optional)

After local clones exist under `data/repos/`, refresh heuristic label columns on an existing sheet:

```bash
python lifecycle/fill_annotation.py \
  --sheet annotation/annotation_sheet.csv
```

To overwrite existing label cells:

```bash
python lifecycle/fill_annotation.py \
  --sheet annotation/annotation_sheet.csv \
  --overwrite
```

Note: row selection (20 git-dormant + 20 active) occurs inside `adoption_maintenance_v2.py` (`build_annotation_sheet`). Re-run §2.4 to regenerate the sheet from scratch.

## 3. Offline reproduction (bundled parquets)

If `data/lifecycle/artifacts_full.parquet` and `data/lifecycle/touch_history.parquet` are present, skip §2.1–2.3 and run:

```bash
make analyze
```

No network or `data/repos/` clones are required. HEAD-presence flags fall back to values computed during the bundled extraction when clones are absent.

## 4. Verify headline statistics

```bash
make verify-headline
```

Expected console output:

```
OK: n_repos=209 artifact_gap= 0.56
```

## 5. Protocol cross-reference

Output paths are declared in `protocol/adoption_maintenance_v2.yaml` under `discovery.outputs` and `outputs`. Extraction paths follow `protocol/lifecycle_v1.yaml` (`outputs.touch_history`, `outputs.artifacts`, etc.).

## 6. Clean bytecode cache

```bash
make clean
```
