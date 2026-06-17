# Content-reference parser manual validation summary

Generated: `2026-06-16T23:09:17.420757+00:00`

Source: `annotation/cochange_reference_validation_sample.csv`

## Status: **exploratory_only**

Content-ref acceptable for paper sensitivity analysis: **False**

## Coverage

- Total rows: **50**
- Annotated rows (any manual field): **50**
- Fully annotated rows (all booleans + category): **50**
- Unannotated rows: **0**

## Provisional thresholds

| Metric | Threshold | Observed | Pass |
|--------|-----------|----------|------|
| `manual_is_reference_correct` | 85.0% | 100.0% | yes |
| `manual_resolved_path_correct` | 80.0% | 100.0% | yes |
| `manual_should_be_used_for_scope` | 75.0% | 69.6% | no |

## Boolean precision (TRUE / (TRUE + FALSE))

- `manual_is_reference_correct`: precision=100.0%, true=47, false=0, ambiguous=3, annotated=50
- `manual_resolved_path_correct`: precision=100.0%, true=45, false=0, ambiguous=5, annotated=50
- `manual_should_be_used_for_scope`: precision=69.6%, true=32, false=14, ambiguous=4, annotated=50

## Counts by `manual_reference_category`

- `ambiguous`: 3
- `build_command`: 4
- `config_file`: 3
- `directory`: 25
- `documentation_reference`: 9
- `include_pointer`: 1
- `path`: 3
- `test_command`: 2

## Precision by extraction rule

- `code_span` (n=18): reference=100.0%, scope=87.5%
- `common_directory_name` (n=2): reference=100.0%, scope=100.0%
- `explicit_path` (n=15): reference=100.0%, scope=85.7%
- `known_config_filename` (n=1): reference=100.0%, scope=100.0%
- `make_command_to_makefile` (n=6): reference=100.0%, scope=0.0%
- `markdown_link` (n=6): reference=100.0%, scope=20.0%
- `scope_section:code_span` (n=2): reference=100.0%, scope=100.0%

## Precision by confidence

- `high` (n=18): reference=100.0%, scope=88.2%
- `low` (n=4): reference=100.0%, scope=0.0%
- `medium` (n=28): reference=100.0%, scope=60.7%

## False positives

_None labeled yet._

## Ambiguous cases

- `electron/electron` / `CLAUDE.md`: `filenames.gni` → `filenames.gni` (category=`ambiguous`)
- `apache/airflow` / `CLAUDE.md`: `[`.apache-magpie.lock`](.apache-magpie.lock)` → `apache-magpie.lock` (category=`config_file`)
- `prefecthq/prefect` / `docs/AGENTS.md`: `v3/api-ref/rest-api/` → `docs/v3/api-ref/rest-api/` (category=`documentation_reference`)
- `prefecthq/prefect` / `docs/AGENTS.md`: `[flows documentation](/v3/concepts/flows)` → `v3/concepts/flows` (category=`ambiguous`)
- `apache/airflow` / `CLAUDE.md`: `uv.lock` → `uv.lock` (category=`ambiguous`)
- `apache/airflow` / `CLAUDE.md`: `[`.github/instructions/code-review.instructions.md`](.github/instructions/code-review.instructions.md)` → `github/instructions/code-review.instructions.md` (category=`documentation_reference`)

## Interpretation

If any threshold fails, content-referenced scope remains **exploratory only** in the paper until parser rules or annotation sample issues are resolved.
