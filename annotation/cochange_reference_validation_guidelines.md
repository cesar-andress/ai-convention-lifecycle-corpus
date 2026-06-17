# Co-change reference validation guidelines

Manual annotation template: `annotation/cochange_reference_validation_sample.csv`

Sample source: `results/cochange/reference_validation_sample.csv` (parser v2, seed 42).

---

## Fields

| Column | Values | Description |
|--------|--------|-------------|
| `manual_is_reference_correct` | `true` / `false` | Is the extracted text a genuine repository reference? |
| `manual_resolved_path_correct` | `true` / `false` | Does `resolved_path` match the intended HEAD path? |
| `manual_should_be_used_for_scope` | `true` / `false` | Should this reference govern co-change scope for the instruction file? |
| `manual_reference_category` | see below | Fine-grained label |
| `manual_notes` | free text | Rationale, edge cases |
| `annotator` | name / initials | Who annotated |
| `annotated_at` | ISO date | When annotated |

---

## manual_is_reference_correct

**True** if the raw extracted text is genuinely a repository reference or command/config reference relevant to project structure, build, test, documentation layout, or source layout.

**False** if the extractor captured prose, HTTP URLs, metaphorical slashes, HTTP verbs, or placeholder tokens unrelated to repository paths.

### Examples

| raw_reference | correct? | Why |
|---------------|----------|-----|
| `python_modules/dagster/dagster_tests/` | **true** | Explicit directory path in repo |
| `Makefile` via `make test` | **true** | Build entry point mapped to root Makefile |
| `allowlist/blocklist` | **false** | Metaphor, not a path |
| `GET` | **false** | HTTP verb in backticks |
| `[ADR 0017](dev/breeze/doc/adr/0017-....md)` | **true** | Markdown link to repo file |
| `@AGENTS.md` | **true** | Include pointer to another instruction file |
| `claude.ai/code` | **false** | External URL fragment |

---

## manual_resolved_path_correct

**True** if `resolved_path` is the intended repository-relative path visible in HEAD (file or directory prefix).

**False** if resolution dropped a prefix, failed on relative paths, or mapped to the wrong directory.

### Examples

| raw | resolved_path | correct? | Why |
|-----|---------------|----------|-----|
| `internal/config/` | `internal/config/` | **true** | Directory prefix matches HEAD |
| `../shared` from nested AGENTS | `shared/` or intended shared module path | **false** if wrong | Relative resolution error |
| `scripts/tools/setup_breeze` | `scripts/tools/setup_breeze` | **true** | File path matches |
| `.github/workflows/ci.yml` | `github/workflows/ci.yml` | **false** | Leading dot stripped incorrectly |

---

## manual_should_be_used_for_scope

**True** if the reference plausibly indicates code or project areas **governed** by the instruction file (areas the brief is meant to guide work on).

**False** if the reference is real but outside plausible governance (e.g., unrelated docs, CI-only paths not mentioned as in-scope, generic `README.md`).

Prefer **precision over recall**: when unsure, mark **false** and note `ambiguous` category.

### Examples

| instruction | reference | use for scope? | Why |
|-------------|-----------|----------------|-----|
| root `CLAUDE.md` | `internal/` in architecture section | **true** | Describes code layout |
| root `CLAUDE.md` | root `Makefile` via `make check` | **true** | Build/test commands in brief |
| root `CLAUDE.md` | `docs/` only in style guide | **false** | Docs not governed by code brief |
| `docs/CLAUDE.md` | `docs/api-history.schema.json` | **true** | Within docs subtree |
| root `CLAUDE.md` | `@AGENTS.md` include pointer | **false** for path scope | Pointer metadata, not governed code (included separately) |

---

## manual_reference_category

Use exactly one:

| Category | When to use |
|----------|-------------|
| `path` | Specific file or subdirectory path |
| `directory` | Directory prefix (`src/`, `packages/`) |
| `config_file` | Build/package manifest (`pyproject.toml`, `go.mod`, …) |
| `build_command` | `make build`, `npm run build`, … |
| `test_command` | `pytest`, `make test`, `go test`, … |
| `documentation_reference` | Markdown doc paths, ADRs, contributing docs |
| `include_pointer` | `@AGENTS.md`, bare `AGENTS.md` pointer line |
| `false_positive` | Extractor error; not a real reference |
| `ambiguous` | Genuine text but unclear governance or resolution |

### Examples

| raw_reference | category |
|---------------|----------|
| `python_modules/libraries/` | `directory` |
| `pyproject.toml` | `config_file` |
| `make ruff` → `Makefile` | `build_command` |
| `go test ./...` | `test_command` |
| `contributing-docs/05_pull_requests.rst` | `documentation_reference` |
| `@AGENTS.md` | `include_pointer` |
| `primary/secondary` | `false_positive` |

---

## Annotation workflow

1. Open the instruction file at `HEAD` in the repository clone (`data/repos/owner/repo`).
2. Read `raw_reference` in context (search surrounding lines in the file or included AGENTS content).
3. Fill the four manual judgment columns.
4. Add brief `manual_notes` when marking `ambiguous` or overriding parser `confidence`.
5. Record `annotator` and `annotated_at` when the row is complete.

---

## Using results

After annotation, compute:

- **Precision@scope** = fraction of `manual_should_be_used_for_scope=true` among rows where annotator agrees reference is correct.
- **False-positive rate** = rows labeled `false_positive` / total.

Do not expand corpus until precision on this sample is acceptable (target: ≥80% precision on `manual_should_be_used_for_scope=true` rows).
