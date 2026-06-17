# Content-reference parser manual validation summary

Generated: `2026-06-16T23:14:44.321384+00:00`

Source: `annotation/cochange_reference_validation_sample2.csv`

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
| `manual_resolved_path_correct` | 80.0% | 95.0% | yes |
| `manual_should_be_used_for_scope` | 75.0% | 71.1% | no |

## Boolean precision (TRUE / (TRUE + FALSE))

- `manual_is_reference_correct`: precision=100.0%, true=50, false=0, ambiguous=0, annotated=50
- `manual_resolved_path_correct`: precision=95.0%, true=38, false=2, ambiguous=10, annotated=50
- `manual_should_be_used_for_scope`: precision=71.1%, true=32, false=13, ambiguous=5, annotated=50

## Counts by `manual_reference_category`

- `build_command`: 6
- `config_file`: 6
- `directory`: 26
- `documentation_reference`: 7
- `include_pointer`: 2
- `path`: 3

## Precision by extraction rule

- `code_span` (n=18): reference=100.0%, scope=87.5%
- `common_directory_name` (n=2): reference=100.0%, scope=100.0%
- `explicit_path` (n=15): reference=100.0%, scope=92.9%
- `known_config_filename` (n=1): reference=100.0%, scope=100.0%
- `make_command_to_makefile` (n=6): reference=100.0%, scope=0.0%
- `markdown_link` (n=6): reference=100.0%, scope=0.0%
- `scope_section:code_span` (n=2): reference=100.0%, scope=100.0%

## Precision by confidence

- `high` (n=18): reference=100.0%, scope=94.1%
- `low` (n=4): reference=100.0%, scope=33.3%
- `medium` (n=28): reference=100.0%, scope=60.0%

## False positives

_None labeled yet._

## Ambiguous cases

- `dagster-io/dagster` / `CLAUDE.md`: `make ruff` → `Makefile` (category=`build_command`)
- `grafana/grafana` / `CLAUDE.md`: `apps/folder/` → `apps/folder/` (category=`directory`)
- `electron/electron` / `CLAUDE.md`: `filenames.gni` → `filenames.gni` (category=`config_file`)
- `grafana/grafana` / `CLAUDE.md`: `docs/` → `docs/` (category=`directory`)
- `prefecthq/prefect` / `AGENTS.md`: `docs/AGENTS.md` → `docs/AGENTS.md` (category=`include_pointer`)
- `apache/airflow` / `CLAUDE.md`: `[`.apache-magpie.lock`](.apache-magpie.lock)` → `apache-magpie.lock` (category=`config_file`)
- `grafana/grafana` / `CLAUDE.md`: `make devenv` → `Makefile` (category=`build_command`)
- `cheat/cheat` / `CLAUDE.md`: `make check` → `Makefile` (category=`build_command`)
- `cheat/cheat` / `CLAUDE.md`: `make build` → `Makefile` (category=`build_command`)
- `payloadcms/payload` / `packages/codemod/CLAUDE.md`: `README.md` → `README.md` (category=`documentation_reference`)
- `grafana/grafana` / `CLAUDE.md`: `make update-workspace` → `Makefile` (category=`build_command`)
- `dagster-io/dagster` / `CLAUDE.md`: `make sanity_check` → `Makefile` (category=`build_command`)
- `prefecthq/prefect` / `docs/AGENTS.md`: `[flows documentation](/v3/concepts/flows)` → `v3/concepts/flows` (category=`documentation_reference`)
- `apache/airflow` / `CLAUDE.md`: `uv.lock` → `uv.lock` (category=`config_file`)
- `apache/airflow` / `CLAUDE.md`: `[`.github/instructions/code-review.instructions.md`](.github/instructions/code-review.instructions.md)` → `github/instructions/code-review.instructions.md` (category=`include_pointer`)

## Interpretation

If any threshold fails, content-referenced scope remains **exploratory only** in the paper until parser rules or annotation sample issues are resolved.
