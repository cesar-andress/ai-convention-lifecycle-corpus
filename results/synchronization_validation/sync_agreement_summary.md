# Synchronization construct validation — inter-annotator agreement

Generated: 2026-06-17T07:37:01.120312+00:00

## Coverage

- Total units in workbooks: **100**
- Paired annotated units: **100**
- Disagreements: **52**
- Units with low confidence (either annotator): **27**

## Agreement

- Raw agreement: **0.480**
- Cohen's κ (TRUE/FALSE/AMBIGUOUS): **0.065**
- Decisive raw agreement: **0.629**
- Cohen's κ (TRUE/FALSE only): **0.000**

## Disagreement table

| A label | B label | count |
|---------|---------|-------|
| AMBIGUOUS | AMBIGUOUS | 4 |
| AMBIGUOUS | TRUE | 13 |
| False | AMBIGUOUS | 7 |
| False | TRUE | 26 |
| True | AMBIGUOUS | 6 |
| True | TRUE | 44 |

## By artifact family

- **configuration**: n=34, agreement=0.618, κ=0.235
- **documentation**: n=35, agreement=0.457, κ=0.023
- **instructions**: n=31, agreement=0.355, κ=0.008

## By repository size

- **large**: n=37, agreement=0.459
- **medium**: n=32, agreement=0.531
- **small**: n=31, agreement=0.452

## Adjudication

Disagreements exported to `annotation/sync_construct_validation_adjudication.csv`.
Fill adjudicated_label, adjudicated_confidence, adjudication_notes, then run `make summarize-sync-metric-vs-human`.
