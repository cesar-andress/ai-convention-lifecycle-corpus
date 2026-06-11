# Zenodo deposit checklist

**Full procedure:** [`docs/ZENODO_RELEASE_CHECKLIST.md`](../docs/ZENODO_RELEASE_CHECKLIST.md) — version bump through DOI verification (use this for every release).

Use **`metadata/zenodo.json`** as the canonical upload metadata template (copy fields into the Zenodo web form or REST API).

**Canonical v2.0.0 release title:** AI Convention Lifecycle Corpus v2.0.0 — Expanded 209-Repository Dataset and Adoption–Maintenance Framework

## Before uploading

1. Confirm DOI `10.5281/zenodo.20637986` in `CITATION.cff`, `metadata/zenodo.json`, and `README.md` matches the Zenodo record for this release.
2. Confirm author metadata in `CITATION.cff` and `metadata/zenodo.json` matches the release tag.
3. Tag the GitHub release as **`v2.0.0`**.

## Upload set

Include the repository root **excluding**:

- `.git/`
- `.venv/`
- `data/repos/`
- `__pycache__/`

## Record type

| Field | Value |
|-------|-------|
| Upload type | Dataset (includes analysis software) |
| License (Zenodo field) | CC-BY 4.0 (aggregated data) |
| Code license | MIT — document in description and `LICENSE` |

## Key files to highlight in deposit notes

| Path | Role |
|------|------|
| `README.md` | Standalone package guide |
| `metadata/replication_package.md` | Complete file inventory |
| `protocol/*.yaml` | Frozen study protocols |
| `data/lifecycle/*.parquet` | Extracted tables |
| `results/lifecycle/adoption_maintenance_v2.json` | Headline statistics |
| `annotation/annotation_sheet.csv` | Manual validation sample |
| `scripts/lifecycle/` | Pipeline code |

## Verification after upload

Share the DOI link and run offline:

```bash
make verify-headline
```

Expected: `OK: n_repos=209 artifact_gap= 0.56`
