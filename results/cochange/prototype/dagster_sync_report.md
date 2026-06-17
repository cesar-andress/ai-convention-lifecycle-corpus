# Dagster co-change synchronization prototype

**Repository:** `dagster-io/dagster`  
**Changed-file manifest:** `/home/cesar/papers/ai-artifact-cochange/ai-convention-lifecycle-corpus/results/cochange/prototype/dagster_changed_files.parquet`  
**Commits parsed:** 27595  
**Changed-file rows:** 274498  

Provisional scope rules: `docs/cochange_scope_rules.md`.

## `CLAUDE.md`

- **Governed scope:** repository-wide (excluding vendor/build/binary paths)
- **Instruction file found in history:** True
- **Instruction-update commits:** 20
- **Governed-code events:** 27406

| Window | Sync rate | Median lag (days) |
|--------|-----------|-------------------|
| W=0 | 0.1% | 0.00 |
| W=7 | 2.0% | 1.06 |
| W=30 | 4.9% | 11.13 |

## `docs/CLAUDE.md`

- **Governed scope:** subtree `docs/` (excluding vendor/build/binary paths)
- **Instruction file found in history:** True
- **Instruction-update commits:** 4
- **Governed-code events:** 5089

| Window | Sync rate | Median lag (days) |
|--------|-----------|-------------------|
| W=0 | 0.1% | 0.00 |
| W=7 | 1.3% | 1.82 |
| W=30 | 3.8% | 10.03 |

## Interpretation guardrail

This report describes one repository under provisional path-based scope rules.
Do not generalize to cross-family claims without replication and sensitivity analyses.
