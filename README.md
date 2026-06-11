# AI Convention Lifecycle Corpus

**Replication package (v2.0.0)** for measuring the adoption–maintenance gap in AI instructional artifacts on public GitHub repositories.

This deposit is **self-contained**: a researcher can understand, cite, and reproduce the empirical study from this README and the bundled files alone. Start with **[`docs/DATASET.md`](docs/DATASET.md)** for a standalone introduction. The companion LaTeX manuscript lives in a separate repository/directory and is **not** included here.

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

**Not included:** full git clones (`data/repos/`). Re-extraction clones public URLs listed in `data/lifecycle/discovered_v2.csv`.

---

## 2. Research objective

**Central question:** To what extent does snapshot presence of AI instructional artifacts on GitHub reflect ongoing git-based maintenance of those same paths?

**Operational contrast:**

- **Adoption** — artifact path present in `HEAD` at observation end.
- **Maintenance** — at least one qualifying commit touching the path within the last *T* days (primary *T* = 180).

**Secondary objectives** (frozen in protocols; see `metadata/replication_package.md`):

1. Quantify the adoption–maintenance gap at *T* ∈ {90, 180, 365} days.
2. Compare artifact-level vs. repository-level aggregation.
3. Report heterogeneity by artifact type and introduction cohort where cell sizes permit.
4. Distinguish **deletion** (path removed from `HEAD`) from **git dormancy** (present but untouched).

Definitions, detection patterns, maturity rules, and state machine are specified in `protocol/` and documented in `docs/dataset_description.md`.

---

## 3. Corpus contents

| Category | Location | Description |
|----------|----------|-------------|
| **Protocols** | `protocol/*.yaml` | Frozen detection, extraction, and analysis specifications |
| **Seeds** | `seeds/*.txt` | Curated GitHub URL pools used for discovery |
| **Scripts** | `scripts/lifecycle/` | Discovery, extraction, build, and analysis pipeline |
| **Datasets** | `data/lifecycle/` | Discovery list, touch history, artifact tables, covariates, metadata |
| **Results** | `results/lifecycle/` | Headline statistics, funnels, bootstrap CIs, sensitivity tables |
| **Annotation** | `annotation/` | Stratified 40-row manual-validation sheet |
| **Metadata** | `metadata/` | Study manifest, Zenodo deposit template, package inventory |
| **Documentation** | `docs/` | Reproducibility, dataset description, release audits |

Full file-level inventory: **`metadata/replication_package.md`**.

---

## 4. Directory structure

```
.
├── README.md                    # This file
├── CITATION.cff                 # Machine-readable citation metadata
├── LICENSE                      # MIT (source code)
├── Makefile                     # install | analyze | lifecycle-v2 | verify-headline
├── requirements.txt
├── protocol/                    # Frozen YAML protocols
├── seeds/                       # GitHub URL seed pools
├── scripts/lifecycle/           # Python pipeline (set PYTHONPATH=scripts)
├── data/lifecycle/              # Aggregated tabular datasets + build/extract metadata
├── results/lifecycle/           # Analysis outputs (JSON/CSV)
├── annotation/                  # Manual-validation sample
├── metadata/                    # study_manifest.json, zenodo.json, replication_package.md
├── docs/                        # Supporting technical documentation
└── zenodo/                      # Deposit checklist (points to metadata/zenodo.json)
```

---

## 5. Reproduction workflow

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

Requires `data/lifecycle/artifacts_full.parquet` (bundled):

```bash
make analyze
```

Runs `scripts/lifecycle/adoption_maintenance_v2.py` and refreshes `results/lifecycle/*`.

### C. Full pipeline from GitHub (network + git)

Clones repositories into `data/repos/` and reruns discovery → extraction → build → analysis:

```bash
make lifecycle-v2
```

Equivalent: `python scripts/lifecycle/run_v2.py` with `PYTHONPATH=./scripts`.

**Step-by-step commands, flags, and output paths:** `docs/reproducibility.md`.

### Hardware (full re-extraction)

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8–16 GB |
| Disk (aggregates only) | 2 GB | — |
| Disk (with clones) | — | 50–100 GB |
| Software | Python ≥ 3.10, git | Linux or macOS tested |

---

## 6. Citation

**Full guide:** [`docs/CITING.md`](docs/CITING.md) — BibTeX examples for Zenodo, GitHub, and versioned dataset releases.

| Use case | Cite |
|----------|------|
| Data, seeds, headline statistics, bundled outputs | **Zenodo** (preferred) |
| Pipeline code or repository history | **GitHub** + version tag |
| Reproducible numbers | **Version `v2.0.0`** + Zenodo DOI |

### Zenodo (preferred)

```bibtex
@dataset{ai_convention_lifecycle_corpus_v2,
  author       = {Andr{\'e}s, C\'esar},
  title        = {{AI Convention Lifecycle Corpus} --- Adoption Is Not Maintenance (v2)},
  year         = {2026},
  publisher    = {Zenodo},
  version      = {2.0.0},
  doi          = {10.5281/zenodo.20637986},
  url          = {https://doi.org/10.5281/zenodo.20637986}
}
```

### GitHub (code)

Repository: `https://github.com/cesar-andress/ai-convention-lifecycle-corpus` — see [`docs/CITING.md`](docs/CITING.md) for a `@software` BibTeX block.

### Dataset version

Always report **`v2.0.0`** when citing headline values (209 repos, 13,988 artifacts, 56.0% artifact-level gap at *T* = 180 d).

Machine-readable metadata: **`CITATION.cff`**.

---

## 7. License

| Component | License | Notes |
|-----------|---------|-------|
| **Source code** (`scripts/`, `Makefile`, etc.) | [MIT](LICENSE) | See root `LICENSE` |
| **Aggregated data** (`data/lifecycle/*`, `results/lifecycle/*`, `annotation/*`, `seeds/*`) | **CC-BY 4.0** | Redistributable study outputs |
| **Third-party git content** | Per-repository | Not redistributed; clone from GitHub at reproduction time |

When in doubt, treat **tabular outputs and seed lists as CC-BY 4.0** and **code as MIT**.

---

## 8. Zenodo DOI

| Field | Value |
|-------|-------|
| **DOI** | `10.5281/zenodo.20637986` |
| **URL** | `https://doi.org/10.5281/zenodo.20637986` |
| **Version** | 2.0.0 |
| **Upload metadata template** | `metadata/zenodo.json` |
| **Deposit checklist** | `zenodo/README.md` |

---

## Further reading (optional)

| Document | Purpose |
|----------|---------|
| `docs/DATASET.md` | **Dataset landing page** — standalone introduction for new researchers |
| `metadata/dataset_card.md` | Academic dataset card (standard sections) |
| `docs/CITING.md` | How to cite Zenodo, GitHub, and dataset version (BibTeX) |
| `docs/ZENODO_RELEASE_CHECKLIST.md` | Step-by-step Zenodo release procedure |
| `metadata/replication_package.md` | Complete file inventory |
| `docs/reproducibility.md` | Exact reproduction commands |
| `docs/dataset_description.md` | Sampling, definitions, validity threats |
| `docs/public_release_audit.md` | Leakage audit for public release |
| `metadata/study_manifest.json` | Machine-readable sample summary |
