# Reference validation pre-annotation draft

**Not final validation.** Human review required before running acceptance thresholds.

- Source: `annotation/cochange_reference_validation_sample.csv`
- Draft output: `annotation/cochange_reference_validation_preannotated.csv`
- Annotator tag: `PREANNOTATION`
- Date: `2026-06-17`

## Summary counts

- Total rows: **50**
- Scope TRUE: **29**
- Scope FALSE: **18**
- Category `ambiguous`: **3**

### By category

- `ambiguous`: 3
- `build_command`: 4
- `config_file`: 3
- `directory`: 22
- `documentation_reference`: 12
- `include_pointer`: 1
- `path`: 3
- `test_command`: 2

### Boolean labels

- `manual_is_reference_correct`: AMBIGUOUS=3, TRUE=47
- `manual_resolved_path_correct`: AMBIGUOUS=5, TRUE=45
- `manual_should_be_used_for_scope`: AMBIGUOUS=3, FALSE=18, TRUE=29

## Rows still requiring human review

**6** rows flagged (ambiguous labels, low confidence, or resolution risk).

- Row **6** `electron/electron` / `CLAUDE.md`: `filenames.gni` → `filenames.gni` (low, `code_span`, draft=`ambiguous`) — low parser confidence
- Row **18** `apache/airflow` / `CLAUDE.md`: `[`.apache-magpie.lock`](.apache-magpie.lock)` → `apache-magpie.lock` (medium, `markdown_link`, draft=`config_file`) — markdown link resolution; possible dot-prefix resolution error
- Row **36** `payloadcms/payload` / `packages/codemod/CLAUDE.md`: `README.md` → `README.md` (low, `code_span`, draft=`documentation_reference`) — low parser confidence
- Row **43** `prefecthq/prefect` / `docs/AGENTS.md`: `[flows documentation](/v3/concepts/flows)` → `v3/concepts/flows` (low, `markdown_link`, draft=`ambiguous`) — low parser confidence; markdown link resolution; relative or docs-path resolution suspect
- Row **45** `apache/airflow` / `CLAUDE.md`: `uv.lock` → `uv.lock` (low, `code_span`, draft=`ambiguous`) — low parser confidence
- Row **50** `apache/airflow` / `CLAUDE.md`: `[`.github/instructions/code-review.instructions.md`](.github/instructions/code-review.instructions.md)` → `github/instructions/code-review.instructions.md` (medium, `markdown_link`, draft=`documentation_reference`) — markdown link resolution; possible dot-prefix resolution error

## Next steps

1. Review flagged rows first, then spot-check high-confidence directory/path labels.
2. Copy accepted rows into `annotation/cochange_reference_validation_sample.csv` with your annotator id.
3. Run `make summarize-reference-validation` only on the human-validated CSV.

