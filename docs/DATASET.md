# AI Convention Lifecycle Corpus — dataset landing page

**Version:** 2.0.0  
**Primary maintenance window:** *T* = 180 days  
**Citation:** [`CITATION.cff`](../CITATION.cff) · [`docs/CITING.md`](CITING.md)

This page introduces the corpus for researchers who encounter the dataset **without** any companion publication. Operational details are frozen in `protocol/*.yaml`; full field definitions and funnels are in [`docs/dataset_description.md`](dataset_description.md).

---

## What this dataset is

The **AI Convention Lifecycle Corpus** is a mining-software-repositories (MSR) replication package. It links public GitHub repositories to **version-controlled files that instruct AI coding agents and assistants**—then measures whether those files are only *present* or also *maintained* in git history.

**Bundled v2 cohort (headline release):**

| Quantity | Value |
|----------|------:|
| Discovered adopted repositories | 220 |
| Successfully extracted & analyzed | 209 |
| Ever-introduced artifact instances | 13,988 |
| Mature-present artifacts at *T* = 180 d | 577 |
| Artifact-level mature-present gap | **56.0%** |
| Repository-level gap | **7.2%** |

**Included:** seed URL lists, Python pipeline, aggregated Parquet/CSV/JSON tables, bootstrap and sensitivity outputs, and a 40-row manual-validation sample.

**Not included:** full git clones (`data/repos/`). Re-extraction clones public URLs from `data/lifecycle/discovered_v2.csv`.

---

## What an AI convention is

An **AI convention** (in this corpus) is a **repository path whose primary role is to give instructions to AI tools**—not general project documentation.

Examples of in-scope conventions:

| Type | Example paths |
|------|----------------|
| Open agent context | `AGENTS.md` |
| Vendor agent memory | `CLAUDE.md` |
| Copilot repository instructions | `.github/copilot-instructions.md` |
| Editor rule trees | `.cursor/rules/*.md`, `.mdc` |
| Windsurf rules | `.windsurf/*.{md,mdc,yaml,yml}` |
| Agent skill descriptors | `SKILL.md`, `.agents/*.{md,yaml,yml}` |
| Prompt libraries | `prompts/*.{md,txt,yaml,yml}` |

**Out of scope** by design: generic docs such as `README.md`, `CONTRIBUTING.md`, `LICENSE`, and paths under build/vendor trees. Classification uses **location and filename patterns** (regex in `protocol/lifecycle_v1.yaml`), not manual content coding at scale.

**Important distinction:** A convention file may be *adopted* (still present in the repository snapshot at observation end) while being *git-dormant* (no qualifying commit touching that path within the last *T* days). The corpus quantifies that gap.

---

## Corpus construction

Construction follows four stages, orchestrated by `scripts/lifecycle/run_v2.py`:

```text
Seeds → Discovery → Extraction → Build → Adoption–maintenance analysis
```

| Stage | Input | Output |
|-------|--------|--------|
| **Seeds** | Curated GitHub URL lists in `seeds/` | Candidate repository pool |
| **Discovery** | Shallow git clone + HEAD scan | `data/lifecycle/discovered_v2.csv` (220 adopted repos) |
| **Extraction** | Full clone + git log | Touch history, covariates, artifact tables |
| **Build** | Touch history + protocols | Parquet artifact tables with temporal fields |
| **Analysis** | Frozen parquets | Gap statistics, bootstrap CIs, funnels, annotation sample |

**Sampling design:** seed-driven and opportunistic—not a random sample of all GitHub. Pools include AI-adjacent repositories (`seeds/seeds.txt`, `seeds/seeds_stratified.txt`) and broader open-source expansions (`seeds/wave2_*.txt`, search-derived lists). Each repository retains a `seed_pool` label.

**Observation end:** the timestamp of the **last commit in each repository at extraction time** (not a single fixed calendar date across the corpus).

**Unit of analysis:**

- **Primary:** artifact instance = `(repo_id, artifact_type, artifact_path)`  
- **Secondary:** repository = `owner/repo`  
- **Exploratory strata:** artifact type, introduction quarter (where cell sizes permit)

Machine-readable summary: [`metadata/study_manifest.json`](../metadata/study_manifest.json).

---

## Discovery process

**Goal:** find repositories that **already adopt** at least one in-scope convention path in `HEAD`.

Implemented in `scripts/lifecycle/discover_v2.py` using rules from `protocol/lifecycle_v1.yaml` and scale parameters from `protocol/adoption_maintenance_v2.yaml`.

**Procedure (per candidate URL):**

1. Parse `owner/repo` from the seed URL.  
2. Shallow clone (`--depth 1`, timeout 120 s) or reuse an existing clone under `data/repos/`.  
3. Scan `HEAD` for paths matching artifact regex patterns.  
4. **Retain** the repository if ≥1 in-scope path is present; otherwise discard.

**Attrition stages** (logged in `results/lifecycle/discovery_funnel_v2.csv`):

| Stage | Meaning |
|-------|---------|
| `candidates_processed` | Seed URLs attempted |
| `duplicate_skip` | Already in the working adopted set |
| `parse_fail` | URL not parseable |
| `clone_fail` | Shallow clone failed or timed out |
| `no_artifacts` | Clone OK but no in-scope paths in HEAD |
| `adopted` | Repository retained |

Discovery targets **220** adopted repositories (v2). The authoritative list is `data/lifecycle/discovered_v2.csv`.

---

## Extraction process

**Goal:** for each discovered repository, recover **full git history** of every in-scope artifact path and compute temporal fields.

Implemented in `scripts/lifecycle/extract_history.py` and `scripts/lifecycle/build_dataset.py`.

**Procedure (per discovered repository):**

1. **Full clone** into `data/repos/{owner}/{repo}` (timeout 180 s).  
2. **Skip** if total commit count &lt; 20 (`low_commits`).  
3. Enumerate all in-scope paths ever seen (HEAD scan + history).  
4. For each path, extract commit-level **touches** via `git log --all --follow -- <path>`.  
5. **Skip** repository if no touch rows are produced (`no_touch_rows`).  
6. Record repository covariates (stars, commit volume, bot/CI rates).

**Key per-artifact fields:**

| Field | Meaning |
|-------|---------|
| `introduced_at` | First commit touching the path |
| `last_touch_at` | Most recent commit touching the path |
| `touch_count` | Distinct commit SHAs touching the path |
| `observation_end` | Last commit timestamp at extraction |
| `follow_up_days` | Days from introduction to observation end |
| `days_since_last_touch` | Days from last touch to observation end |
| `present_in_head` | Path exists in `HEAD` at observation end |

**Bundled extraction attrition** (220 discovered):

| Outcome | Count |
|---------|------:|
| `ok` | 209 |
| `no_touch_rows` | 7 |
| `low_commits` | 4 |

Skip log: `results/lifecycle/extract_attrition_v2.csv`. Build metadata: `data/lifecycle/extract_meta.json`, `data/lifecycle/artifacts_build_meta.json`.

**Outputs:** `touch_history.parquet`, `artifacts.parquet`, `artifacts_full.parquet`, `repo_covariates.parquet`.

---

## Adoption–maintenance analysis

**Definitions** (`protocol/adoption_maintenance_v1.yaml`):

| Concept | Operational rule |
|---------|------------------|
| **Adoption (artifact)** | Path present in `HEAD` at observation end (`present_in_head`) |
| **Adoption (repository)** | ≥1 adopted artifact in `HEAD` |
| **Maintenance (artifact) at *T*** | Adopted AND `days_since_last_touch < T` |
| **Maintenance (repository) at *T*** | ≥1 maintained artifact at *T* |

Primary window **T = 180 days**; sensitivity at 90 and 365 days.

### State machine

Each artifact instance receives **exactly one** state at threshold *T* (priority: DELETED → TOO_YOUNG → ACTIVE → DORMANT):

| State | Condition |
|-------|-----------|
| **DELETED** | Not in `HEAD` (ever introduced, then removed) |
| **TOO_YOUNG** | In `HEAD` but `follow_up_days < T` |
| **ACTIVE** | In `HEAD`, mature, touched within last *T* days |
| **DORMANT** | In `HEAD`, mature, **no** touch within last *T* days |

**Git-dormant** ≠ semantically obsolete. It means only that git history shows no recent commits on that path.

### Gap metrics

**Artifact-level gap (mature-present denominator):**

```text
gap_rate = count(DORMANT at T) / count(present_in_head AND follow_up_days ≥ T)
```

**Repository-level gap:**

```text
gap_rate = (adopted_repos − maintained_repos) / adopted_repos
```

Implemented in `scripts/lifecycle/adoption_maintenance_v2.py`. Primary results: `results/lifecycle/adoption_maintenance_v2.json`. State-enriched table: `data/lifecycle/artifact_states_v2.parquet`.

### Uncertainty and validation

| Method | Output |
|--------|--------|
| Cluster bootstrap (5,000 replicates, cluster = repository) | `results/lifecycle/bootstrap_v2.json` |
| Leave-one-repository-out | `results/lifecycle/loo_v2.csv` |
| Stratified manual sample (20 dormant + 20 active at *T* = 180) | `annotation/annotation_sheet.csv` |

Type and cohort breakdowns (`type_gap_age_adjusted.csv`, `cohort_gap_v2.csv`) apply minimum cell-size guards defined in the v2 protocol.

---

## Limitations

Read these before generalizing findings beyond the bundled cohort.

### Construct validity

- **Adoption ≠ use.** `HEAD` presence does not show whether developers or agents read or follow the file.  
- **Maintenance ≠ semantic freshness.** Git touches may be trivial edits, renames, or bulk formatting.  
- **Dormant ≠ obsolete.** A git-dormant convention may still be accurate and relied upon off-git.  
- **Pattern matching ≠ intent.** Paths are classified by location/name, not by human content review.

### Sampling and external validity

- **Non-random, seed-driven sample** over-represents AI-adjacent and actively maintained OSS; estimates are **not** global GitHub prevalence.  
- **Observation end varies by repository** (last commit at extraction), so calendar-time alignment across repos is approximate.  
- **Platform drift:** AI convention filenames and tooling evolve quickly; the v2 snapshot is time-bound.

### Measurement

- **`git log --follow`** may miss or merge history across renames; touch counts can be incomplete.  
- **Prompt-heavy repositories** dominate instance counts; interpret type-stratified tables with composition in mind.  
- **Bot commits** are recorded but not excluded from touches; high bot rates may inflate “maintenance” for some paths.

### Redistribution

- **No bundled clones:** re-extraction requires network access and respects per-repository licenses.  
- Repositories may become private, renamed, or deleted after the snapshot was taken.

### Manual validation

- The **40-row annotation sample** supports sanity checks, not population inference.  
- Heuristic pre-fills in `scripts/lifecycle/fill_annotation.py` are starting points, not expert adjudication.

Full validity discussion: [`docs/dataset_description.md`](dataset_description.md) §11.

---

## Get started

| Task | Command / file |
|------|----------------|
| Verify bundled headline stats | `make verify-headline` |
| Recompute analysis (offline) | `make analyze` |
| Full pipeline from GitHub | `make lifecycle-v2` |
| Step-by-step reproduction | [`docs/reproducibility.md`](reproducibility.md) |
| File inventory | [`metadata/replication_package.md`](../metadata/replication_package.md) |
| How to cite | [`docs/CITING.md`](CITING.md) |
| Zenodo release procedure | [`docs/ZENODO_RELEASE_CHECKLIST.md`](ZENODO_RELEASE_CHECKLIST.md) |

**Quick verification** (from corpus root):

```bash
python3 -m venv .venv && source .venv/bin/activate
make install && make verify-headline
```

Expected: `OK: n_repos=209 artifact_gap= 0.56`

---

## Primary data files

| File | Role |
|------|------|
| `data/lifecycle/discovered_v2.csv` | Adopted repository registry (220 rows) |
| `data/lifecycle/artifacts_full.parquet` | Artifact table for analysis |
| `data/lifecycle/artifact_states_v2.parquet` | Per-artifact states at 90/180/365 d |
| `results/lifecycle/adoption_maintenance_v2.json` | Headline gap statistics |
| `protocol/*.yaml` | Frozen detection and analysis rules |

---

## License

| Component | License |
|-----------|---------|
| Source code | MIT ([`LICENSE`](../LICENSE)) |
| Aggregated data & seeds | CC-BY 4.0 |

Third-party git content is not redistributed; clone from GitHub at reproduction time under each repository’s license.
