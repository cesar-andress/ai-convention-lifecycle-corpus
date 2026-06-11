# Zenodo deposit notes

This folder holds metadata for the public Zenodo release of the **AI Convention Lifecycle Corpus**.

## Recommended deposit structure

Upload the repository root (excluding `.git/`, `.venv/`, and any local `data/repos/` clones).

## Record type

- **Resource type:** Dataset (with optional Software)
- **License (code):** MIT (see root `LICENSE`)
- **License (aggregated data files):** CC-BY 4.0 (see root `README.md`)

## Files to highlight in the Zenodo description

| Path | Role |
|------|------|
| `protocol/*.yaml` | Frozen study protocols |
| `data/lifecycle/*.parquet` | Extracted artifact and touch-history tables |
| `results/lifecycle/adoption_maintenance_v2.json` | Headline statistics (MSR paper) |
| `annotation/annotation_sheet.csv` | Manual validation sample (n=40) |
| `scripts/lifecycle/` | Analysis and pipeline code |

## Citation

Use `CITATION.cff` at the repository root. Link to the MSR paper when published.

## Versioning

Tag releases as `v2.0.0` (220 discovered / 209 analyzed cohort). Increment patch for metadata-only fixes; increment minor for protocol-compatible data refreshes.
