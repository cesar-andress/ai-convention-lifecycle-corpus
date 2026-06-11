# Paper / corpus separation audit

**Date:** 2026-06-10  
**Workspace root:** `../` (internal study monorepo)  
**Manuscript tree:** `../paper/`  
**Public corpus tree:** `.` (this repository)

This audit documents the final boundary between the LaTeX manuscript and the Zenodo replication corpus.

---

## 1. Target layout

```text
ai-artifact-cochange/
├── paper/                          # Manuscript-only (private/submission)
│   ├── main.tex
│   ├── sections/
│   ├── tables/
│   ├── examples/
│   ├── figures/
│   ├── submission/
│   │   ├── response-to-reviewers/
│   │   ├── writing/
│   │   └── manuscript-protocol-extensions.yaml
│   ├── camera-ready/
│   └── README.md
│
└── ai-convention-lifecycle-corpus/ # Reproducibility-only (public/Zenodo)
    ├── protocol/
    ├── data/lifecycle/
    ├── results/lifecycle/
    ├── scripts/lifecycle/
    ├── annotation/
    ├── seeds/
    ├── docs/
    ├── metadata/
    └── zenodo/
```

The internal workspace root (`../`) may still hold working copies of pipeline code and clones for active development. Those assets are **not** part of either release tree and are documented in `docs/repository_migration.md`.

---

## 2. Paper-only assets (`../paper/`)

| Path | Role |
|------|------|
| `main.tex` | ACM root document |
| `sections/*.tex` | Manuscript sections (abstract through conclusion) |
| `tables/*.tex` | Static LaTeX tables (numbers transcribed from corpus outputs) |
| `examples/repox-*.tex` | RepoX running-example fragments |
| `examples/repox-macros.tex` | Shared example macros |
| `figures/` | Manuscript figures (empty placeholder; no figure files in corpus) |
| `submission/response-to-reviewers/reviewer2.md` | Threats / validity response draft |
| `submission/response-to-reviewers/reviewer2_round1.md` | Round-1 response notes |
| `submission/writing/roadmap.md` | Internal writing roadmap |
| `submission/writing/writing-style.md` | Style constraints |
| `submission/manuscript-protocol-extensions.yaml` | Table/figure plan and claim guardrails (moved out of corpus protocol) |
| `camera-ready/main.pdf` | Built PDF |
| `Makefile` | LaTeX build (`make` → `camera-ready/main.pdf`) |
| `README.md` | Manuscript layout and build instructions |
| `main.{aux,bbl,blg,log,out}` | Ephemeral LaTeX intermediates (gitignored) |

**Bibliography:** `../../bibliography.bib` (shared at papers repo root; not duplicated in corpus).

---

## 3. Corpus-only assets (this repository)

### Protocols

| Path | Role |
|------|------|
| `protocol/lifecycle_v1.yaml` | Artifact patterns, extraction, build outputs |
| `protocol/adoption_maintenance_v1.yaml` | Adoption, maintenance, states, gap definitions |
| `protocol/adoption_maintenance_v2.yaml` | v2 scale, seeds, outputs, reproduction checks |

Manuscript-only protocol blocks (`deliverables`, `claims_allowed`, `claims_forbidden`, pilot submission notes) were **removed** from corpus protocols and relocated to `../paper/submission/manuscript-protocol-extensions.yaml`.

### Data

| Path | Role |
|------|------|
| `data/lifecycle/discovered_v2.csv` | Adopted repository registry (220 rows) |
| `data/lifecycle/touch_history.parquet` | Commit-level touch events |
| `data/lifecycle/artifacts.parquet` | Compact artifact table |
| `data/lifecycle/artifacts_full.parquet` | Extended artifact fields |
| `data/lifecycle/artifact_states_v2.parquet` | State-enriched artifacts |
| `data/lifecycle/repo_covariates.parquet` | Repository covariates |
| `data/lifecycle/extract_meta.json` | Extraction scale metadata |
| `data/lifecycle/artifacts_build_meta.json` | Build provenance |

### Results

| Path | Role |
|------|------|
| `results/lifecycle/adoption_maintenance_v2.json` | Primary summary (headline gaps, bootstrap, annotation metadata) |
| `results/lifecycle/bootstrap_v2.json` | Cluster-bootstrap intervals |
| `results/lifecycle/loo_v2.csv` | Leave-one-repository-out sensitivity |
| `results/lifecycle/funnel_v2.csv` | Analysis funnel by threshold |
| `results/lifecycle/discovery_funnel_v2.csv` | Discovery attrition |
| `results/lifecycle/extract_attrition_v2.csv` | Extraction skip log |
| `results/lifecycle/cohort_gap_v2.csv` | Cohort-stratified gaps |
| `results/lifecycle/type_gap_age_adjusted.csv` | Age-adjusted type comparison |

### Code and seeds

| Path | Role |
|------|------|
| `scripts/lifecycle/*.py` | v2 pipeline and analysis |
| `lifecycle` → `scripts/lifecycle` | Import-path symlink |
| `seeds.txt`, `seeds_stratified.txt`, `seeds/*` | Discovery URL pools |
| `annotation/annotation_sheet.csv` | Stratified validation sample (40 rows) |

### Documentation and release metadata

| Path | Role |
|------|------|
| `README.md` | Dataset overview and reproduction entry point |
| `CITATION.cff` | Corpus citation metadata |
| `LICENSE` | MIT (code) |
| `Makefile` | `install`, `analyze`, `lifecycle-v2`, `verify-headline` |
| `requirements.txt` | Python dependencies |
| `metadata/study_manifest.json` | Sample counts and headline checksums |
| `docs/reproducibility.md` | Exact reproduction commands |
| `docs/dataset_description.md` | Standalone dataset reference |
| `docs/repository_migration.md` | Internal → corpus copy map |
| `docs/legacy_removal_log.md` | Removed pilot artifacts |
| `docs/separation_audit.md` | This file |
| `zenodo/metadata.json` | Zenodo deposit metadata |
| `zenodo/README.md` | Deposit checklist |

---

## 4. Moves performed in this separation pass

| From | To | Reason |
|------|-----|--------|
| `paper/notes/reviewer2*.md` | `paper/submission/response-to-reviewers/` | Response-to-reviewers drafts belong with manuscript |
| `paper/notes/roadmap.md`, `writing-style.md` | `paper/submission/writing/` | Internal writing notes |
| `paper/main.pdf` | `paper/camera-ready/main.pdf` | Camera-ready output separated from source |
| Protocol `deliverables` / `claims_*` / pilot notes | `paper/submission/manuscript-protocol-extensions.yaml` | Manuscript planning, not replication logic |
| JSON `paper_title`, `claims_*`, `submission_readiness` | Removed or renamed in corpus outputs | Manuscript metadata stripped from corpus |

---

## 5. Corpus de-manuscripting (in-place edits)

| Location | Change |
|----------|--------|
| `protocol/adoption_maintenance_v2.yaml` | `submission_readiness` → `reproduction_checks`; removed submission header comment |
| `protocol/adoption_maintenance_v1.yaml` | Removed deliverables, claims, pilot submission blocks |
| `scripts/lifecycle/adoption_maintenance_v2.py` | Summary emits `study_id`, `reproduction_checks`; no claim lists |
| `results/lifecycle/adoption_maintenance_v2.json` | Aligned with script output schema |
| `metadata/study_manifest.json` | Removed `paper_title` field |

---

## 6. Verification

### 6.1 No manuscript text in corpus

Checks run on 2026-06-10:

| Check | Result |
|-------|--------|
| `*.tex` under corpus root | **0 files** |
| `\documentclass`, `\begin{document}` in corpus | **No matches** |
| `submission_readiness`, `claims_allowed`, `paper_title` in corpus | **No matches** (after cleanup) |
| Reviewer response drafts in corpus | **None** |

Corpus markdown may cite the study **title** as bibliographic context (`CITATION.cff`, `README.md`); this is dataset metadata, not manuscript prose.

### 6.2 No exclusive corpus data in `paper/`

| Check | Result |
|-------|--------|
| `*.parquet`, `*.csv` data files under `paper/` | **0 files** |
| `protocol/*.yaml` under `paper/` | **0 files** (extensions YAML is manuscript-only) |
| Pipeline scripts under `paper/` | **0 files** |

Paper `tables/*.tex` contain **transcribed statistics only**; canonical numeric outputs remain in `results/lifecycle/` here.

### 6.3 Cross-reference integrity

| Reference | Status |
|-----------|--------|
| Paper `Makefile` → `../../bibliography.bib` | Valid (shared bib at monorepo root) |
| Paper `README.md` → `../ai-convention-lifecycle-corpus/` | Valid sibling path |
| Corpus `README.md` → `../paper/` | Valid sibling path |
| Paper methodology cites corpus paths (`protocol/…`, `data/lifecycle/…`) | Paths resolve in **corpus**, not in `paper/` (by design) |

### 6.4 Headline checksum

```bash
make verify-headline
# Expected: OK: n_repos=209 artifact_gap= 0.56
```

---

## 7. Final audit verdict

| Criterion | Status |
|-----------|--------|
| Manuscript sources confined to `../paper/` | **PASS** |
| Replication assets confined to corpus | **PASS** |
| No LaTeX manuscript in corpus | **PASS** |
| No corpus datasets exclusively under `paper/` | **PASS** |
| Manuscript metadata stripped from corpus JSON/protocols | **PASS** |
| Sibling cross-links documented | **PASS** |

**Outcome:** The paper and corpus are separable for independent citation. Researchers may cite `CITATION.cff` / Zenodo DOI without accessing `../paper/`. Authors may compile the manuscript without copying parquets into `paper/`.

---

## 8. Internal workspace note

The parent directory `../` (outside this git repository) still contains development artifacts: full `lifecycle/` scripts, legacy `v4/` experiments, co-change pilots, `data/repos/` clones, and duplicate aggregates. Those paths are **intentionally excluded** from both release trees. See `docs/repository_migration.md` §Explicitly excluded.
