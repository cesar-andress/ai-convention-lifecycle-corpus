# Blinded synchronization construct validation protocol

Generated: 2026-06-17T07:15:54.190522+00:00

## Annotator workbooks (fill these)

- `annotation/sync_construct_validation_blinded_annotator_A.csv`
- `annotation/sync_construct_validation_blinded_annotator_B.csv`

Codebook: `annotation/sync_construct_validation_codebook.md`

## Calibration first

- `annotation/sync_construct_validation_calibration_units.csv` (14 units)
- Same columns as main workbooks; subset of unit IDs also present in A/B files.

## Workflow

1. Both annotators code calibration units independently.
2. Compare labels, discuss disagreements, refine codebook.
3. Both annotators code full blinded workbooks (100 units each).
4. Run `make summarize-sync-agreement` to populate adjudication sheet.
5. Adjudicator fills `annotation/sync_construct_validation_adjudication.csv`.
6. Run `make summarize-sync-metric-vs-human`.

## Blinding

Annotator files exclude metric-derived fields (`metric_sync_30`, `lag_days`, `metric_label`, stratum/size fields).

**Calibration unit IDs:** 4f004fee3aad, 7fda69f5754d, 9404c9bd7fb2, c620114d8f4c, cc69217b9807, e63c6e231ac3, 05e811636411, 21e176064439, 79cc1712d62d, d28f0628a182, 81fd6f0fd73f, 984b7775755f, f141d2679668, fcb9a141ef05
