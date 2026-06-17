# Co-change reference validation schema

Machine-checkable values for `annotation/cochange_reference_validation_sample.csv`.

Guidelines (human-readable): `annotation/cochange_reference_validation_guidelines.md`

---

## Boolean columns

Use uppercase strings exactly as written.

| Column | Accepted values |
|--------|-----------------|
| `manual_is_reference_correct` | `TRUE`, `FALSE`, `AMBIGUOUS` |
| `manual_resolved_path_correct` | `TRUE`, `FALSE`, `AMBIGUOUS` |
| `manual_should_be_used_for_scope` | `TRUE`, `FALSE`, `AMBIGUOUS` |

### Semantics

- **TRUE** — annotator agrees with the positive interpretation described in the guidelines.
- **FALSE** — annotator rejects the positive interpretation.
- **AMBIGUOUS** — genuine extraction but judgment cannot be made confidently; excluded from precision numerator/denominator (reported separately).

Leave blank only while a row is not yet annotated.

---

## `manual_reference_category`

Exactly one lowercase label per annotated row:

| Value | Meaning |
|-------|---------|
| `path` | Specific file or subdirectory path |
| `directory` | Directory prefix (`src/`, `packages/`, …) |
| `config_file` | Build/package manifest (`pyproject.toml`, `go.mod`, …) |
| `build_command` | Build invocation mapped to a repo artifact (e.g. `make build` → `Makefile`) |
| `test_command` | Test invocation mapped to a repo artifact |
| `documentation_reference` | Doc paths, ADRs, contributing guides |
| `include_pointer` | `@AGENTS.md`, bare instruction-file pointer |
| `false_positive` | Extractor error; not a real reference |
| `ambiguous` | Real text but unclear governance or resolution |

---

## Metadata columns

| Column | Format |
|--------|--------|
| `manual_notes` | Free text; required when any boolean is `AMBIGUOUS` or category is `ambiguous` |
| `annotator` | Name or initials |
| `annotated_at` | ISO 8601 date, e.g. `2026-06-17` |

---

## Provisional acceptance thresholds

Computed by `make summarize-reference-validation` over decisive (`TRUE`/`FALSE`) rows:

| Metric | Minimum precision |
|--------|-------------------|
| `manual_is_reference_correct` | ≥ 85% |
| `manual_resolved_path_correct` | ≥ 80% |
| `manual_should_be_used_for_scope` | ≥ 75% |

If any threshold fails, content-referenced scope stays **exploratory only** in the paper.
