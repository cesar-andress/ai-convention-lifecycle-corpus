# Dataset description

**Corpus:** AI Convention Lifecycle Corpus (v2)  
**Version:** 2.0.0  
**Primary maintenance window:** *T* = 180 days  
**Citation:** see root `CITATION.cff` and Zenodo DOI (when assigned)

This document describes the corpus as a **standalone research artifact**. A researcher can understand what was collected, how it was operationalized, and what limitations apply without consulting any companion publication.

Frozen operational rules live in:

- `protocol/lifecycle_v1.yaml` — artifact scope, git extraction, build metrics  
- `protocol/adoption_maintenance_v1.yaml` — adoption, maintenance, states, gap formulas  
- `protocol/adoption_maintenance_v2.yaml` — sample scale, seed pools, analysis outputs  

Reproduction commands: `docs/reproducibility.md`.

---

## 1. Purpose

The corpus supports empirical measurement of the **adoption–maintenance gap** for AI instructional and agent-governance files in open-source GitHub repositories.

- **Adoption** is operationalized as path presence in `git` HEAD at repository observation end.  
- **Maintenance** is operationalized as at least one qualifying git **touch** of that path within the last *T* days before observation end.  

The deposit includes seed lists, pipeline code, aggregated tables, headline statistics, bootstrap intervals, leave-one-out sensitivity tables, and a stratified manual-validation sample.

---

## 2. Sampling strategy

### 2.1 Design

This is a **seed-driven, opportunistic sample**, not a probability sample of all open-source software or all GitHub repositories.

Repositories enter the study through **curated URL seed pools** declared in `protocol/adoption_maintenance_v2.yaml`:

| Seed pool | Source files | Intent |
|-----------|--------------|--------|
| `ai_adopter` | `seeds/seeds_stratified.txt`, `seeds/seeds.txt` | Repositories associated with AI tooling, agents, or AI-adjacent ecosystems |
| `general_oss` | `seeds/wave2_general_oss.txt`, `seeds/wave2_s2_priority.txt`, `seeds/wave2_s0_candidates.txt`, `seeds/lifecycle_cached_clones.txt`, `seeds/lifecycle_gh_repo_search.txt` | Broader open-source candidates, including repository-search expansions |

URLs are deduplicated across pools. Each adopted repository retains its originating `seed_pool` label in `data/lifecycle/discovered_v2.csv`.

### 2.2 Inclusion at discovery

A repository is **discovered adopted** when a shallow `git` clone (or an existing local clone under `data/repos/`) reveals **at least one in-scope artifact path in HEAD** matching the pattern rules in `protocol/lifecycle_v1.yaml`.

Scale parameters (v2):

| Parameter | Value |
|-----------|-------|
| Target adopted repositories | 220 |
| Maximum candidate URLs processed per discovery run | 1,500 |
| Discovery clone timeout | 120 s |
| Discovery clone depth | shallow (`--depth 1`) |

Discovery stops when the target number of adopted repositories is reached or the candidate budget is exhausted.

### 2.3 Inclusion at extraction

Discovered repositories proceed to **full clone extraction**. A repository contributes to analysis tables when extraction succeeds and yields at least one touch-history row for an in-scope artifact path.

Extraction filters (`protocol/lifecycle_v1.yaml`):

| Rule | Value |
|------|-------|
| Minimum commit count | 20 |
| Extraction clone timeout | 180 s |
| Extraction clone depth | full history |

### 2.4 Released sample (bundled v2)

| Stage | Count |
|-------|-------|
| Discovered adopted repositories | 220 |
| Successfully extracted repositories | 209 |
| Skipped at extraction | 11 |
| Ever-introduced artifact instances | 13,988 |
| Present in HEAD at observation end | 9,994 |
| Mature-present at *T* = 180 | 577 |
| Touch-history rows | 86,845 |

Machine-readable summary: `metadata/study_manifest.json`.

---

## 3. Discovery funnel

Discovery attrition is recorded in `results/lifecycle/discovery_funnel_v2.csv`. Stages are emitted by `scripts/lifecycle/discover_v2.py`:

| Stage | Meaning |
|-------|---------|
| `candidates_processed` | Unique seed URLs attempted in the run |
| `duplicate_skip` | URL already seen in the working adopted set |
| `parse_fail` | URL could not be parsed as `owner/repo` |
| `clone_fail` | Shallow clone timed out or failed |
| `no_artifacts` | Clone succeeded but no in-scope paths in HEAD |
| `adopted` | Repository retained (≥1 in-scope path in HEAD) |

**Bundled release counts** (cumulative adopted set):

| Metric | Count |
|--------|-------|
| Adopted repositories (all pools) | 220 |
| Adopted — `ai_adopter` | 57 |
| Adopted — `general_oss` | 163 |

The funnel CSV may reflect an incremental discovery pass; the authoritative adopted list is `data/lifecycle/discovered_v2.csv` (220 rows).

---

## 4. Extraction funnel

Extraction attrition is recorded per repository in `results/lifecycle/extract_attrition_v2.csv` and summarized in `data/lifecycle/extract_meta.json`.

### 4.1 Pipeline

For each row in `discovered_v2.csv`:

1. Full clone into `data/repos/{owner}/{repo}` (not redistributed).  
2. Skip if commit count `< 20` (`low_commits`).  
3. Enumerate in-scope artifact paths ever seen in history (git log name-only + HEAD scan).  
4. For each path, extract commit-level touch history (`git log --follow`).  
5. Skip repository if no touch rows are produced (`no_touch_rows`).

### 4.2 Bundled attrition

| Outcome | Count |
|---------|-------|
| `ok` | 209 |
| `no_touch_rows` | 7 |
| `low_commits` | 4 |
| **Total discovered** | **220** |

Skip reasons are mutually exclusive per final row in the attrition log (last status kept on resume).

### 4.3 Analysis funnel

After build and state assignment, artifact counts by stage appear in `results/lifecycle/funnel_v2.csv`:

| Stage (*T* = 180) | Count |
|-------------------|-------|
| Ever introduced | 13,988 |
| Present in HEAD | 9,994 |
| Deleted (ever introduced, not in HEAD) | 3,994 |
| Mature-present | 577 |
| Active | 254 |
| Git-dormant | 323 |
| Too young | 9,417 |

Sensitivity windows *T* ∈ {90, 365} are reported in the same file.

---

## 5. Artifact definitions

### 5.1 Unit of analysis

An **artifact instance** is the tuple `(repo_id, artifact_type, artifact_path)` where the path matched an in-scope pattern at least once in the repository’s git history.

`repo_id` is `owner/repo` (GitHub slug). Multiple paths of the same type in one repository are separate instances.

### 5.2 In-scope path patterns

Patterns are regex-defined in `protocol/lifecycle_v1.yaml`:

| `artifact_type` | Example paths |
|-----------------|---------------|
| `agents_md` | `AGENTS.md` |
| `claude_md` | `CLAUDE.md` |
| `copilot_instructions` | `.github/copilot-instructions.md` |
| `cursor_rules` | `.cursor/rules/*.md`, `.mdc` |
| `windsurf_rules` | `.windsurf/*.{md,mdc,yaml,yml}` |
| `agents_dir` | `.agents/*.{md,yaml,yml}` |
| `skill_md` | `SKILL.md` |
| `prompts` | `prompts/*.{md,txt,yaml,yml}` |

### 5.3 Exclusions

Paths are excluded if they match:

- **Prefix blocklist:** `node_modules/`, `vendor/`, `dist/`, `build/`, `target/`, `coverage/`, `.git/`  
- **Basename blocklist:** `README.md`, `CHANGELOG.md`, `LICENSE`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`  
- **Regex blocklist:** e.g. `docs/api/`, `docs/reference/`, `docs/*/prompts/`  

Generic contribution or documentation files are intentionally out of scope.

### 5.4 Temporal fields

| Field | Definition |
|-------|------------|
| `introduced_at` | Timestamp of the **first** commit in the extracted touch history for the path |
| `last_touch_at` | Timestamp of the **most recent** commit in the touch history |
| `touch_count` | Number of distinct commits touching the path |
| `observation_end` | Timestamp of the repository’s last commit at extraction time |
| `follow_up_days` | `(observation_end − introduced_at).days` |
| `days_since_last_touch` | `(observation_end − last_touch_at).days`, floored at 0 |

### 5.5 Touch

A **touch** is a commit returned by:

```text
git log --all --follow -- <artifact_path>
```

Each distinct commit SHA counts once. Author metadata is stored but does not gate maintenance classification. Bot authorship is recorded in repository covariates (`bot_rate`) but is not excluded from touches.

---

## 6. Adoption definition

Adoption measures **HEAD presence** at observation end.

| Level | Definition | Operational rule |
|-------|------------|------------------|
| **Artifact adopted** | Path exists in `git` HEAD | `present_in_head == true` |
| **Repository adopted** | ≥1 adopted artifact in HEAD | `any(present_in_head)` per `repo_id` |

**Ever introduced** includes paths seen in history that were later deleted (`present_in_head == false`). Deletion is an outcome distinct from git dormancy.

At discovery time, “adopted repository” uses the same HEAD rule on a shallow clone. At analysis time, HEAD is re-checked against local full clones when available (`scripts/lifecycle/adoption_maintenance.py`); otherwise bundled `present_in_head` values from extraction are used.

---

## 7. Maintenance definition

Maintenance measures **recent git activity** on an adopted path.

| Level | Definition | Operational rule |
|-------|------------|------------------|
| **Artifact maintained at *T*** | Adopted path touched within *T* days of observation end | `present_in_head` AND `days_since_last_touch < T` |
| **Repository maintained at *T*** | ≥1 artifact maintained at *T* | `any(artifact_maintained_T)` per `repo_id` |

Primary *T* = **180 days**. Sensitivity windows: **90** and **365** days.

Maintenance is **git-based only**. Reads, local edits without commit, fork usage, or runtime consumption of instructions are not observed.

---

## 8. State machine definition

At each threshold *T*, every artifact instance is assigned **exactly one** state. Priority order: `DELETED` → `TOO_YOUNG` → `ACTIVE` → `DORMANT` (`protocol/adoption_maintenance_v1.yaml`).

| State | Condition |
|-------|-----------|
| **DELETED** | `present_in_head == false` |
| **TOO_YOUNG** | Present AND `follow_up_days < T` |
| **ACTIVE** | Present AND `follow_up_days ≥ T` AND `days_since_last_touch < T` |
| **DORMANT** | Present AND `follow_up_days ≥ T` AND `days_since_last_touch ≥ T` |

**Git-dormant** means the path remains in HEAD but has no qualifying touch in the last *T* days. It does **not** imply semantic obsolescence, developer abandonment, or agent non-use.

### 8.1 Maturity guards

Gap rates at artifact level use the **mature-present** denominator:

```text
artifact_mature_present_T = present_in_head AND follow_up_days ≥ T
```

**Artifact-level gap rate (mature-present):**

```text
count(DORMANT at T) / count(mature_present at T)
```

**Repository-level gap rate:**

```text
(adopted_repos − maintained_repos) / adopted_repos
```

Equivalently: repositories that are adopted but have no maintained artifact at *T*, with at least one mature-present dormant artifact.

State-enriched tables: `data/lifecycle/artifact_states_v2.parquet`.

---

## 9. Annotation protocol

### 9.1 Purpose

Automated git states are validated on a **small stratified sample** of artifact instances. The sample supports sanity checks on state assignment and coarse content relevance; it is not a second ground-truth layer for maintenance.

### 9.2 Selection

Implemented in `scripts/lifecycle/adoption_maintenance_v2.py` (`build_annotation_sheet`):

| Parameter | Value |
|-----------|-------|
| Random seed | 42 |
| Git-dormant rows (`state_180 == DORMANT`, mature-present) | 20 |
| Active rows (`state_180 == ACTIVE`, mature-present) | 20 |
| **Total** | **40** |

Sampling is without replacement within each stratum; if a stratum has fewer than 20 eligible rows, all eligible rows are taken.

Output: `annotation/annotation_sheet.csv`.

### 9.3 Columns

| Column | Role |
|--------|------|
| `repo_id`, `artifact_type`, `artifact_path` | Instance identifier |
| `state_180`, `introduced_at`, `last_touch_at`, `days_since_last_touch`, `touch_count`, `present_in_head` | Automated fields copied at selection time |
| `git_state_correct` | Manual/heuristic: does git evidence support the assigned state? |
| `substantial_last_touch` | Was the last touch more than a trivial/format-only change? |
| `apparent_semantic_relevance` | Does file content appear instruction-like for AI tooling? |
| `ambiguous` | Case flagged as hard to adjudicate |
| `annotator_notes` | Free text |

### 9.4 Labeling workflow

1. **Sheet generation** — stratified sample written by the v2 analysis step.  
2. **Heuristic pre-fill** — `scripts/lifecycle/fill_annotation.py` populates label columns from local clone content and git metadata when `data/repos/` is available; existing non-empty cells are preserved.  
3. **Human review** — expected for rigorous reuse; bundled labels mix heuristic pre-fills and empty cells.

Pre-fill rules (abbreviated):

- `git_state_correct`: cross-checks `days_since_last_touch` against `state_180`.  
- `substantial_last_touch`: `yes` if `touch_count ≥ 2`, or single touch on recently active path.  
- `apparent_semantic_relevance`: based on UTF-8 file length thresholds at annotation time.  
- `ambiguous`: set when clone missing, very short content, vendored paths, or near-threshold dormancy.

Annotation summary statistics are embedded in `results/lifecycle/adoption_maintenance_v2.json` under `annotation_summary`.

---

## 10. Uncertainty quantification

Reported alongside point estimates in `results/lifecycle/adoption_maintenance_v2.json` and `results/lifecycle/bootstrap_v2.json`:

| Method | Setting |
|--------|---------|
| Cluster bootstrap | 5,000 replicates, clusters = `repo_id`, seed = 42 |
| Leave-one-repository-out | Drop each repository once; report Δ gap for artifact- and repo-level metrics |

Stratified tables (`cohort_gap_v2.csv`, `type_gap_age_adjusted.csv`) apply minimum cell-size guards (`min_mature_present_type = 30`, `min_cohort_type_per_quarter = 10`).

---

## 11. Threats to validity

### 11.1 Construct validity

- **Adoption ≠ use.** HEAD presence does not measure whether developers or agents read or follow instructions.  
- **Maintenance ≠ semantic freshness.** Git touches may be formatting, renames, or tangential edits.  
- **Dormant ≠ obsolete.** A git-dormant file may remain functionally current.  
- **Pattern matching ≠ intent.** Paths are classified by location and filename patterns, not by manual content coding at scale.

### 11.2 Internal validity

- **Observation end varies by repository** (last commit at extraction), so calendar-time comparisons across repos are approximate.  
- **Discovery used shallow clones; extraction used full history.** Rare edge cases may differ between stages.  
- **HEAD re-check** depends on local clones at analysis time; offline re-runs may retain extraction-time presence flags.

### 11.3 External validity

- **Non-random sample.** Seed pools over-represent AI-adjacent and popular OSS repositories; findings do not estimate global prevalence on GitHub.  
- **Temporal drift.** The bundled snapshot reflects extraction dates in the v2 cohort; platform and convention norms evolve quickly.  
- **Survivorship.** Repositories that became private, deleted, or unreachable after extraction are not re-fetched in the static deposit.

### 11.4 Measurement validity

- **`git log --follow`** may miss or merge history across renames; touch counts can be incomplete.  
- **Prompt directories** dominate instance counts (`skill_md` and `prompts` families); type-stratified summaries should be read with composition in mind.  
- **Large prompt repositories** (e.g. high `touch_count` outliers) skew touch-volume covariates; sensitivity analysis excluding top prompt repositories is reported in `adoption_maintenance_v2.json` under `sensitivity_exclude_top_prompt_repos`.

### 11.5 Annotation validity

- **n = 40** manual sample is illustrative, not powered for population inference.  
- **Heuristic pre-fills** are not a substitute for blinded expert annotation on new extractions.

### 11.6 Re-identification and licensing

- Repository identifiers are public GitHub slugs.  
- Full clones are **not** redistributed; users must respect per-repository licenses when re-cloning from `discovered_v2.csv`.

---

## 12. Primary headline statistics (*T* = 180)

From `results/lifecycle/adoption_maintenance_v2.json` (209 analyzed repositories):

| Metric | Value |
|--------|-------|
| Artifact-level mature-present gap | 56.0% |
| Artifact-level mature-present maintenance rate | 44.0% |
| Repository-level gap | 7.2% |
| Deleted (ever introduced) | 28.6% |
| Git-dormant among mature-present | 56.0% |

Bootstrap 95% intervals and leave-one-out ranges: `results/lifecycle/bootstrap_v2.json`, `results/lifecycle/loo_v2.csv`.

---

## 13. File index

| File | Description |
|------|-------------|
| `data/lifecycle/discovered_v2.csv` | Adopted repository registry |
| `data/lifecycle/touch_history.parquet` | Commit-level touches |
| `data/lifecycle/artifacts.parquet` | Compact artifact table |
| `data/lifecycle/artifacts_full.parquet` | Full build columns for analysis |
| `data/lifecycle/artifact_states_v2.parquet` | States and gap flags |
| `data/lifecycle/repo_covariates.parquet` | Stars, commits, bot/CI rates |
| `results/lifecycle/adoption_maintenance_v2.json` | Primary summary |
| `annotation/annotation_sheet.csv` | Validation sample |
| `protocol/*.yaml` | Frozen definitions |

---

## 14. How to cite

```text
César Andrés. (2026). AI Convention Lifecycle Corpus — Adoption Is Not Maintenance (v2) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.20637986
```

Update author names and DOI after deposit. Full metadata: `CITATION.cff`.
