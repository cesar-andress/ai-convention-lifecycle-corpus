# AI Convention Lifecycle Corpus

Public reproduction package for the MSR study **Adoption Is Not Maintenance: The Adoption--Maintenance Gap in AI Instructional Artifacts on GitHub**.

This repository contains frozen protocols, aggregated datasets, analysis scripts, headline results, and manual-validation labels for the v2 cohort (**220** discovered adopted repositories, **209** analyzed, **13{,}988** ever-introduced artifact instances).

The LaTeX paper lives in a separate private/submission repository and is **not** included here.

## What is included

| Directory | Contents |
|-----------|----------|
| `protocol/` | Frozen YAML protocols (`lifecycle_v1`, `adoption_maintenance_v1/v2`) |
| `data/lifecycle/` | Redistributable parquets, discovery CSVs, extraction metadata |
| `results/lifecycle/` | Headline JSON/CSV outputs (gaps, bootstrap, LOO, funnels) |
| `scripts/lifecycle/` | Python pipeline and analysis code |
| `annotation/` | Stratified manual-validation sheet (40 rows) |
| `seeds/`, `seeds*.txt` | GitHub URL seed pools used by discovery |
| `metadata/` | Study manifest with sample counts |
| `docs/` | Migration and reproduction notes |
| `zenodo/` | Deposit guidance |

A symlink `lifecycle → scripts/lifecycle` preserves import paths expected by the pipeline.

## What is not included

- **`data/repos/`** — full git clones of analyzed GitHub repositories (large; per-repo licenses). Re-extraction requires cloning URLs from `data/lifecycle/discovered_v2.csv`.
- **Paper sources** — `paper/` LaTeX project.
- **Local venv**, caches, and pilot-only artifacts outside the v2 headline path.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
make install
make verify-headline   # checks frozen adoption_maintenance_v2.json
make analyze           # re-run analysis from parquets (offline)
```

Full re-extraction from GitHub (network + git required):

```bash
make lifecycle-v2
```

## Data license

Aggregated tabular files under `data/lifecycle/` and `results/lifecycle/` are released under **CC-BY 4.0** (cite this corpus and the MSR paper). Source code is **MIT** (see `LICENSE`).

## Headline statistics (primary, T=180 days)

From `results/lifecycle/adoption_maintenance_v2.json`:

- Artifact-level mature-present gap: **56.0%**
- Repository-level gap: **7.2%**
- Analyzed repositories: **209**

See `metadata/study_manifest.json` for additional fields.

## Citation

Use `CITATION.cff`. After Zenodo deposit, replace placeholder DOI and repository URL.

## Migration

See `docs/repository_migration.md` for the mapping from the internal study workspace to this public corpus layout.
