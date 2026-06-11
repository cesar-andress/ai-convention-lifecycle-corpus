---
# Dataset card metadata (informational; not consumed by tooling)
title: AI Convention Lifecycle Corpus
version: 2.0.0
study_id: adoption-maintenance-v2
license_code: MIT
license_data: CC-BY-4.0
language: en
homepage: https://github.com/cesar-andress/ai-convention-lifecycle-corpus
doi: 10.5281/zenodo.20637986
tags:
  - mining-software-repositories
  - github
  - ai-assisted-development
  - software-maintenance
  - replication-package
---

# Dataset card: AI Convention Lifecycle Corpus

| Field | Value |
|-------|-------|
| **Version** | 2.0.0 |
| **Study ID** | `adoption-maintenance-v2` |
| **Primary window** | *T* = 180 days |
| **Languages** | English (documentation); repository file content multilingual |
| **License (code)** | MIT |
| **License (aggregated data)** | CC-BY 4.0 |
| **Citation** | [`CITATION.cff`](../CITATION.cff) · [`docs/CITING.md`](../docs/CITING.md) |
| **DOI** | `10.5281/zenodo.20637986` |

This card describes the corpus as a **standalone research artifact**. No companion publication is required to understand scope, provenance, or appropriate use.

Extended documentation: [`docs/DATASET.md`](../docs/DATASET.md) · [`docs/dataset_description.md`](../docs/dataset_description.md) · [`metadata/replication_package.md`](replication_package.md).

---

## Dataset Summary

The **AI Convention Lifecycle Corpus** is a mining-software-repositories (MSR) dataset and replication package. It connects public GitHub repositories to **AI instructional artifact paths**—version-controlled files that tell coding agents and assistants how to behave in a project—and measures the gap between **adoption** (path present in `git` HEAD at observation end) and **maintenance** (qualifying git commit touching the path within the last *T* days).

**Headline v2 release:**

| Metric | Value |
|--------|------:|
| Discovered adopted repositories | 220 |
| Successfully extracted & analyzed | 209 |
| Ever-introduced artifact instances | 13,988 |
| Mature-present artifacts (*T* = 180 d) | 577 |
| Artifact-level mature-present gap | 56.0% |
| Repository-level gap | 7.2% |

The deposit bundles frozen YAML protocols, seed URL lists, Python pipeline code, aggregated Parquet/CSV/JSON tables, uncertainty quantification outputs, and a stratified manual-validation sample. Full git clones are **not** redistributed.

---

## Motivation

Teams increasingly store AI-facing instructions in git-tracked paths (`AGENTS.md`, `CLAUDE.md`, Copilot/Cursor rule trees, `prompts/` directories). MSR studies often infer technology **adoption** from snapshot presence of configuration or documentation files. For AI conventions, presence at `HEAD` may overstate ongoing **maintenance** if paths are introduced once and rarely touched again.

This corpus enables researchers to:

1. **Measure** adoption vs. git-based maintenance on the same path granularity.  
2. **Reproduce** discovery, extraction, and gap statistics from frozen protocols.  
3. **Extend** the pipeline to new seed pools, thresholds, or artifact patterns without re-deriving definitions from prose.

The central empirical quantity is the **adoption–maintenance gap**: adopted paths that are mature-present yet git-dormant at threshold *T*.

---

## Composition

### Instances and units

| Unit | Definition | Count (v2) |
|------|------------|----------:|
| **Repository** | Public GitHub slug `owner/repo` in the analyzed cohort | 209 |
| **Artifact instance** | Tuple `(repo_id, artifact_type, artifact_path)` with ≥1 historical touch | 13,988 |
| **Touch event** | One commit SHA touching an artifact path | 86,845 rows |

### Artifact types (pattern-defined)

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

Patterns and exclusions: `protocol/lifecycle_v1.yaml`.

### Bundled files

| Category | Paths |
|----------|-------|
| **Registry** | `data/lifecycle/discovered_v2.csv` |
| **Core tables** | `touch_history.parquet`, `artifacts.parquet`, `artifacts_full.parquet`, `artifact_states_v2.parquet`, `repo_covariates.parquet` |
| **Results** | `results/lifecycle/adoption_maintenance_v2.json`, `bootstrap_v2.json`, funnel/LOO/cohort/type CSVs |
| **Validation** | `annotation/annotation_sheet.csv` (40 rows) |
| **Protocols** | `protocol/lifecycle_v1.yaml`, `adoption_maintenance_v1.yaml`, `adoption_maintenance_v2.yaml` |
| **Seeds** | `seeds/*.txt` (7 pools) |
| **Code** | `scripts/lifecycle/*.py`, `Makefile`, `requirements.txt` |

Complete inventory: [`metadata/replication_package.md`](replication_package.md).

### What is not included

- Full git clones (`data/repos/`) — third-party content under per-repository licenses.  
- Raw GitHub API dumps beyond seed lists.  
- Manuscript text, figures, or paper-specific claim guardrails.

---

## Collection Process

### Sampling frame

**Seed-driven, opportunistic sample** — not a probability sample of all GitHub or all open source.

| Seed pool label | Source files | Intent |
|-----------------|--------------|--------|
| `ai_adopter` | `seeds/seeds.txt`, `seeds/seeds_stratified.txt` | AI tooling, agents, AI-adjacent ecosystems |
| `general_oss` | `seeds/wave2_*.txt`, `seeds/lifecycle_*.txt` | Broader OSS and search-derived candidates |

URLs are deduplicated; each repository retains `seed_pool` in `discovered_v2.csv`.

### Discovery (repository inclusion)

Tool: `scripts/lifecycle/discover_v2.py`

1. Parse candidate URL → `owner/repo`.  
2. Shallow clone (`--depth 1`, 120 s timeout) or reuse local clone.  
3. Scan `HEAD` for in-scope artifact paths.  
4. Retain if ≥1 path matches; stop at **220** adopted repositories (v2 target).

Attrition log: `results/lifecycle/discovery_funnel_v2.csv`.

### Extraction (history and covariates)

Tool: `scripts/lifecycle/extract_history.py`

1. Full clone (180 s timeout).  
2. Skip if commit count &lt; 20.  
3. Enumerate in-scope paths in history; extract `git log --follow` per path.  
4. Skip repository if zero touch rows.

**Bundled attrition:** 209 ok · 7 `no_touch_rows` · 4 `low_commits` (of 220 discovered).

Log: `results/lifecycle/extract_attrition_v2.csv`.

### Observation time

**Observation end** = timestamp of the last commit in each repository **at extraction time**. There is no single calendar cutoff shared across all repositories.

### Annotators

Automated pipeline only at scale. A **40-row stratified sample** (20 git-dormant + 20 active at *T* = 180) supports manual or heuristic validation; it is not a second ground-truth layer for the full corpus.

---

## Preprocessing

### Path detection and filtering

- **Inclusion:** regex patterns per `artifact_type` (`protocol/lifecycle_v1.yaml`).  
- **Exclusion:** vendor/build prefixes (`node_modules/`, `dist/`, …), generic doc basenames (`README.md`, `CONTRIBUTING.md`, …), and docs-subtree regex blocklist.

Classification is **path-based**, not content-based, at corpus scale.

### Temporal feature construction

Built by `scripts/lifecycle/build_dataset.py` from touch history:

| Field | Definition |
|-------|------------|
| `introduced_at` | First commit touching the path |
| `last_touch_at` | Most recent commit touching the path |
| `touch_count` | Distinct commit SHAs |
| `follow_up_days` | Days from introduction to observation end |
| `days_since_last_touch` | Days from last touch to observation end |
| `present_in_head` | Path exists in `HEAD` at observation end |

### State assignment and gap computation

Tool: `scripts/lifecycle/adoption_maintenance_v2.py`  
Rules: `protocol/adoption_maintenance_v1.yaml`

At each *T* ∈ {90, 180, 365}, assign one state per artifact: **DELETED**, **TOO_YOUNG**, **ACTIVE**, **DORMANT** (mutually exclusive; fixed priority order).

**Mature-present gap rate** at artifact level:

```text
count(DORMANT at T) / count(present_in_head AND follow_up_days ≥ T)
```

Cluster bootstrap (5,000 replicates, cluster = repository) and leave-one-repository-out sensitivity included in results.

### Annotation pre-fill (optional)

`scripts/lifecycle/fill_annotation.py` may populate heuristic columns in `annotation/annotation_sheet.csv` when local clones exist; human review is expected for rigorous reuse.

---

## Uses

### Intended uses

- Empirical MSR research on **AI governance files**, agent instructions, and prompt libraries in OSS.  
- Teaching and benchmarking **reproducible mining pipelines** (protocol-driven discovery → extraction → analysis).  
- **Sensitivity analysis** over maintenance windows (90 / 180 / 365 days), aggregation level (artifact vs. repository), and seed pools.  
- **Method comparison** for adoption vs. activity proxies on git-hosted configuration artifacts.

### Out-of-scope uses

- Estimating **global prevalence** of AI conventions on all of GitHub (non-random sample).  
- Inferring **semantic quality**, agent compliance, or developer intent from path presence alone.  
- **Identifying individuals** or attributing authorship beyond public git metadata already in upstream repositories.  
- Training LLMs on bundled file **content** at scale without re-cloning and respecting upstream licenses (clones not shipped).

### Reproduction entry points

| Goal | Command |
|------|---------|
| Verify bundled headline stats | `make verify-headline` |
| Recompute analysis offline | `make analyze` |
| Full pipeline from GitHub | `make lifecycle-v2` |

Details: [`docs/reproducibility.md`](../docs/reproducibility.md).

---

## Limitations

### Construct validity

- **Adoption ≠ use** — `HEAD` presence does not measure reading or following instructions.  
- **Maintenance ≠ semantic freshness** — git touches may be trivial or unrelated to instruction content.  
- **Git-dormant ≠ obsolete** — dormant paths may remain functionally current.  
- **Pattern matching ≠ intent** — filenames/locations proxy for “AI convention” without manual coding.

### Statistical generalization

- Seed pools overweight AI-adjacent and actively maintained repositories.  
- Composition is **prompt-heavy** in instance counts; type-stratified tables require care.  
- Observation end varies by repository; cross-repo calendar comparisons are approximate.

### Technical measurement

- `git log --follow` may miss or merge rename history.  
- Discovery used shallow clones; extraction used full history — rare edge-case divergence possible.  
- Bot commits are included in touches; high `bot_rate` covariates may affect interpretation.

### Validation sample

- **n = 40** annotation rows — illustrative, not powered for population inference.  
- Heuristic pre-fills are not expert adjudication.

Full discussion: [`docs/dataset_description.md`](../docs/dataset_description.md) §11.

---

## Ethical Considerations

### Public data and identifiers

- All repository identifiers are **public GitHub slugs** already visible on the platform.  
- No private repositories, credentials, or personal data beyond what appears in public git history and metadata.

### Redistribution

- **Aggregated tables** (this deposit) are released under **CC-BY 4.0**.  
- **Source code** is **MIT**.  
- **Upstream repository content** is not redistributed; users who re-clone must comply with each project’s license and GitHub Terms of Service.

### Dual use

The dataset describes where projects publish AI instructions. It does **not** endorse scraping beyond normal git clone for research reproduction. Users should avoid harassment, deanonymization attempts, or contact with maintainers based solely on dormant-path labels.

### Environmental impact

Full re-extraction clones ~220 repositories and is network- and disk-intensive. Prefer bundled parquets for analysis-only reuse.

---

## Maintenance

### Versioning

Semantic versioning on git tags (e.g. `v2.0.0`). Record each release on Zenodo with a version-specific DOI under the same concept DOI prefix.

| Version | Date | Notes |
|---------|------|-------|
| v2.0.0 | 2026-06-11 | Initial public v2 cohort (209 analyzed repos) |

Release procedure: [`docs/ZENODO_RELEASE_CHECKLIST.md`](../docs/ZENODO_RELEASE_CHECKLIST.md).

### Issue reporting

- **Code and metadata bugs:** GitHub Issues on `cesar-andress/ai-convention-lifecycle-corpus`.  
- **Protocol change requests:** open an issue describing the proposed YAML diff; breaking changes require a **major** version bump.

### Contact and authorship

Author metadata: [`CITATION.cff`](../CITATION.cff) (César Andrés; ORCID 0009-0001-8968-3404).

### Update policy

| Change | Version bump |
|--------|--------------|
| Protocol-compatible data refresh | minor |
| Docs/metadata only | patch |
| Breaking protocol or cohort redefinition | major |

When updating, refresh `metadata/study_manifest.json`, this card, [`docs/DATASET.md`](../docs/DATASET.md), and Zenodo metadata together.

### Machine-readable manifest

[`metadata/study_manifest.json`](study_manifest.json) — sample counts, protocol paths, headline checksums.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-11 | Initial dataset card for v2.0.0 release |
