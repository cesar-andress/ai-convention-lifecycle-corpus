# AI Convention Lifecycle Corpus

**Release title:** AI Convention Lifecycle Corpus v2.0.0 — Expanded 209-Repository Dataset and Adoption–Maintenance Framework  
**DOI:** [https://doi.org/10.5281/zenodo.20637986](https://doi.org/10.5281/zenodo.20637986)

Replication package for measuring the adoption–maintenance gap in AI instructional artifacts on public GitHub repositories.

This deposit is **self-contained**: a researcher can understand, cite, and reproduce the empirical study from this README and the bundled files alone. Start with the [dataset landing page](docs/DATASET.md) for a standalone introduction. The companion LaTeX manuscript lives in a separate repository and is **not** included here.

---

## Repository structure

| Component | Path | Purpose |
|-----------|------|---------|
| Protocol specifications | `protocol/` | Frozen detection rules, extraction settings, and measurement thresholds |
| Seed pools | `seeds/` | Curated GitHub URL pools used for repository discovery |
| Analysis scripts | `scripts/lifecycle/` | Discovery, extraction, dataset build, and gap analyses |
| Build automation | `Makefile` | Package-level reproduction targets (`install`, `verify-headline`, `analyze`, `lifecycle-v2`) |
| Processed data | `data/lifecycle/` | Discovery tables, touch history, and extracted parquet datasets |
| Results | `results/lifecycle/` | Headline gaps, bootstrap intervals, LOO sensitivity, and robustness outputs |
| Headline gap bundle | `results/lifecycle/adoption_maintenance_v2.json` | Offline verification of reported headline statistics |
| Annotation sample | `annotation/annotation_sheet.csv` | Stratified 40-row manual-validation sample |
| Package metadata | `metadata/` | Study manifest, Zenodo deposit template, and file inventory |
| Replication inventory | `metadata/replication_package.md` | Complete file-level manifest with checksums |
| Documentation | `docs/` | Reproducibility guide, dataset description, and release audits |
| Citation metadata | `CITATION.cff` | Dataset version and preferred citation string |
| Zenodo checklist | `zenodo/` | Deposit checklist (see `metadata/zenodo.json`) |

**Not bundled:** full git clones under `data/repos/`. Full re-extraction clones public URLs listed in the discovery table.

**File-level detail:** see [metadata/replication_package.md](metadata/replication_package.md).

---

## 1. What this dataset is

The **AI Convention Lifecycle Corpus** is a frozen mining-software-repositories (MSR) dataset and analysis pipeline. It captures:

- Which open-source repositories **adopt** AI-facing instruction paths at observation-time `HEAD` (e.g. `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `.cursor/rules/*`, `prompts/` trees).
- Whether those paths show **maintenance**—qualifying git commits touching the path within a lookback window *T* days before observation end.

**Bundled release (v2 cohort):**

| Quantity | Value |
|----------|------:|
| Discovered adopted repositories | 220 |
| Successfully extracted & analyzed | 209 |
| Ever-introduced artifact instances | 13,988 |
| Mature-present artifacts (*T* = 180 d) | 577 |
| Primary maintenance window | 180 days |

**Headline gap at *T* = 180 days (mature-present artifacts):** **56.0%** artifact-level; **7.2%** repository-level.

**Included:** YAML protocols, GitHub URL seed pools, Python extraction/analysis code, aggregated Parquet/CSV/JSON tables, bootstrap and sensitivity outputs, and a 40-row manual-validation sample.

---

## 2. Research objective

**Central question:** To what extent does snapshot presence of AI instructional artifacts on GitHub reflect ongoing git-based maintenance of those same paths?

**Operational contrast:**

- **Adoption** — artifact path present in `HEAD` at observation end.
- **Maintenance** — at least one qualifying commit touching the path within the last *T* days (primary *T* = 180).

**Secondary objectives** (frozen in protocols; see the replication inventory):

1. Quantify the adoption–maintenance gap at *T* ∈ {90, 180, 365} days.
2. Compare artifact-level vs. repository-level aggregation.
3. Report heterogeneity by artifact type and introduction cohort where cell sizes permit.
4. Distinguish **deletion** (path removed from `HEAD`) from **git dormancy** (present but untouched).

Definitions, detection patterns, maturity rules, and state machine are specified in the protocol directory and documented in [docs/dataset_description.md](docs/dataset_description.md).

---

## 3. Reproduction workflow

### A. Quick verification (offline, ~1 min)

Confirms bundled headline statistics without network access:

```bash
python3 -m venv .venv
source .venv/bin/activate
make install
make verify-headline
```

Expected output: `OK: n_repos=209 artifact_gap= 0.56`

### B. Recompute analysis from frozen parquets (offline)

Requires the bundled artifact parquet table (see **Processed data** in the repository structure table):

```bash
make analyze
```

Runs the primary v2 analysis script and refreshes outputs under the results directory.

### C. Full pipeline from GitHub (network + git)

Clones repositories into `data/repos/` and reruns discovery → extraction → build → analysis:

```bash
make lifecycle-v2
```

Equivalent: `python scripts/lifecycle/run_v2.py` with `PYTHONPATH=./scripts`.

**Step-by-step commands, flags, and output paths:** [docs/reproducibility.md](docs/reproducibility.md).

### Hardware (full re-extraction)

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8–16 GB |
| Disk (aggregates only) | 2 GB | — |
| Disk (with clones) | — | 50–100 GB |
| Software | Python ≥ 3.10, git | Linux or macOS tested |

---

## 4. Citation

**Full guide:** [docs/CITING.md](docs/CITING.md) — BibTeX examples for Zenodo, GitHub, and versioned dataset releases.

| Use case | Cite |
|----------|------|
| Data, seeds, headline statistics, bundled outputs | **Zenodo** (preferred) |
| Pipeline code or repository history | **GitHub** + version tag |
| Reproducible numbers | **Version `v2.0.0`** + Zenodo DOI |

### Zenodo (preferred)

```bibtex
@dataset{ai_convention_lifecycle_corpus_v2,
  author       = {Andr{\'e}s, C\'esar and Moncunilla, David Mart{\'i}n},
  title        = {{AI Convention Lifecycle Corpus v2.0.0 --- Expanded 209-Repository Dataset and Adoption--Maintenance Framework}},
  year         = {2026},
  publisher    = {Zenodo},
  version      = {2.0.0},
  doi          = {10.5281/zenodo.20637986},
  url          = {https://doi.org/10.5281/zenodo.20637986}
}
```

### GitHub (code)

Repository: `https://github.com/cesar-andress/ai-convention-lifecycle-corpus` — see [docs/CITING.md](docs/CITING.md) for a `@software` BibTeX block.

### Dataset version

Always report **`v2.0.0`** when citing headline values (209 repos, 13,988 artifacts, 56.0% artifact-level gap at *T* = 180 d).

Machine-readable metadata: **`CITATION.cff`**.

---

## 5. License

| Component | License | Notes |
|-----------|---------|-------|
| **Source code** (`scripts/`, `Makefile`, etc.) | [MIT](LICENSE) | See root `LICENSE` |
| **Aggregated data** (processed data, results, annotation, seeds) | **CC-BY 4.0** | Redistributable study outputs |
| **Third-party git content** | Per-repository | Not redistributed; clone from GitHub at reproduction time |

When in doubt, treat **tabular outputs and seed lists as CC-BY 4.0** and **code as MIT**.

---

## 6. Zenodo release

| Field | Value |
|-------|-------|
| **Release title** | AI Convention Lifecycle Corpus v2.0.0 — Expanded 209-Repository Dataset and Adoption–Maintenance Framework |
| **DOI** | `10.5281/zenodo.20637986` |
| **URL** | `https://doi.org/10.5281/zenodo.20637986` |
| **Version** | 2.0.0 |
| **Upload metadata template** | `metadata/zenodo.json` |
| **Deposit checklist** | `zenodo/README.md` |

---

## Further reading

| Document | Purpose |
|----------|---------|
| [docs/DATASET.md](docs/DATASET.md) | Standalone dataset landing page for new researchers |
| [metadata/dataset_card.md](metadata/dataset_card.md) | Academic dataset card |
| [docs/CITING.md](docs/CITING.md) | How to cite Zenodo, GitHub, and dataset version (BibTeX) |
| [docs/ZENODO_RELEASE_CHECKLIST.md](docs/ZENODO_RELEASE_CHECKLIST.md) | Step-by-step Zenodo release procedure |
| [metadata/replication_package.md](metadata/replication_package.md) | Complete file inventory |
| [docs/reproducibility.md](docs/reproducibility.md) | Exact reproduction commands |
| [docs/dataset_description.md](docs/dataset_description.md) | Sampling, definitions, validity threats |
| [docs/public_release_audit.md](docs/public_release_audit.md) | Leakage audit for public release |
| [metadata/study_manifest.json](metadata/study_manifest.json) | Machine-readable sample summary |
