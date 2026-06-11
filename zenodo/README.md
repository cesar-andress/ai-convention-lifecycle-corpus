# Zenodo deposit

## Record metadata

Upload `metadata.json` fields via the Zenodo web form or REST API when creating the deposit. Replace `PLACEHOLDER` values (DOI, GitHub URL, ORCID, affiliations) before publishing.

## Recommended upload set

Include the repository root **excluding**:

- `.git/`
- `.venv/`
- `data/repos/` (local git clones)
- `__pycache__/`

## Record type

- **Upload type:** Dataset (includes analysis software)
- **License (aggregated data):** CC-BY 4.0
- **License (code):** MIT — documented in root `LICENSE` and deposit description

## Files to highlight

| Path | Role |
|------|------|
| `protocol/*.yaml` | Frozen study protocols |
| `data/lifecycle/*.parquet` | Extracted tables |
| `results/lifecycle/adoption_maintenance_v2.json` | Headline statistics |
| `annotation/annotation_sheet.csv` | Manual validation sample |
| `scripts/lifecycle/` | Pipeline code |
| `docs/reproducibility.md` | Exact reproduction commands |

## Versioning

Tag releases as `v2.0.0` (220 discovered / 209 analyzed cohort). Increment patch for metadata-only fixes; increment minor for protocol-compatible data refreshes.

## Citation

Root `CITATION.cff` and the Zenodo-assigned DOI after publication.
