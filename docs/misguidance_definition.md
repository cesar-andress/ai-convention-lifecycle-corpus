# Misguidance — observable inconsistency between instruction files and repository HEAD

Design note for the misguidance pilot (`scripts/misguidance/`).

**Status:** pilot — conservative lower bound; no population claims.

---

## Research question

Do AI instruction files contain references that are **no longer valid** in the current repository state?

We measure **observable inconsistency** at HEAD. We do not claim causality (e.g., that stale text *caused* agent failure).

---

## Working definition

A reference is **stale** when:

1. it is explicitly referenced by the instruction file (parser v2 extraction);
2. it cannot be resolved in repository HEAD; and
3. the reference previously existed **or** clearly intends to point to repository content.

We report a **conservative lower bound**: ambiguous and unresolved cases are excluded from stale counts.

---

## Term definitions

### Stale path

A reference to a **specific file path** (e.g. `src/foo.py`, `internal/config.yaml`) that does not exist at HEAD and resolution is confident (medium/high parser confidence).

| Example | HEAD | Label |
|---------|------|-------|
| `src/legacy/handler.py` | file removed | **stale path** |
| `src/foo.py` | file present | **currently valid** |
| `maybe/handler.py` (low confidence) | absent | **ambiguous** (not counted stale) |

### Stale directory

A reference to a **directory prefix** (trailing `/` or directory-only token) with no matching files under that prefix at HEAD.

| Example | HEAD | Label |
|---------|------|-------|
| `packages/legacy/` | directory gone | **stale directory** |
| `python_modules/` | tree present | **currently valid** |
| `docs/` in prose metaphor | not a path reference | **ambiguous** / excluded |

### Stale file

Synonym for a stale **path** when the resolved target is a single file (not a directory prefix). Used in examples; primary category label is `stale_path`.

### Stale config reference

A reference to a build/package manifest or lockfile (`Makefile`, `go.mod`, `pyproject.toml`, `Dockerfile`, …) that is absent at HEAD.

| Example | HEAD | Label |
|---------|------|-------|
| `Makefile` via `make test` mapping | Makefile exists | **valid** (file exists; command viability not tested) |
| `tox.ini` mentioned, file absent | missing | **stale config** |
| `uv.lock` (low confidence span) | present | **ambiguous** if resolution uncertain |

### Stale command

A **build or test command** (`make check`, `pytest`, …) that no longer works.

**Pilot policy:** commands are **not** automatically classified as stale. Without execution evidence we use `unknown_command`. Only direct file mappings (e.g. `make foo` → `Makefile` exists) are marked **valid**.

### Unresolved reference

Parser extracted text but **no repository-relative path** could be resolved (empty resolution, external URL stripped, placeholder).

| Example | Label |
|---------|-------|
| `https://example.com/doc` | unresolved (out of scope) |
| `` `GET` `` HTTP verb | unresolved / noise |

### Unknown reference

Extraction is plausible but **governance or target is unclear** — treated as **ambiguous** in the pilot; not counted toward stale rate.

---

## Status labels (pilot detector)

| Status | Meaning |
|--------|---------|
| `valid` | Resolved path or config artifact exists at HEAD |
| `stale` | Confident resolution; target absent at HEAD (non-doc primary misguidance) |
| `ambiguous` | Resolution or reference type uncertain — excluded from stale rate |
| `unresolved` | No usable resolved path |
| `unknown_command` | Command reference; command viability not tested |
| `doc_reference` | Documentation path; tracked separately, not primary misguidance |

---

## Distinguishing stale vs ambiguous vs valid

| Situation | Classification |
|-----------|----------------|
| High/medium confidence path; absent at HEAD | **stale** |
| Low confidence path; absent at HEAD | **ambiguous** |
| Path present at HEAD | **valid** |
| Markdown doc link; absent at HEAD | **doc_reference** + stale subcategory (reported separately) |
| `make test` → Makefile exists | **valid** (mapping only) |
| `make test`; Makefile missing | **stale config** |
| `make test`; Makefile exists; `make test` target unknown | **unknown_command** (not stale) |

---

## Historical existence

For each **stale** reference, git history is queried:

| Value | Meaning |
|-------|---------|
| `existed_before` | Path (or directory prefix) appeared in at least one commit |
| `never_existed` | No historical evidence in git log |
| `unknown` | History check failed or path too ambiguous |

**Interpretation:** `existed_before` is stronger evidence of **drift** (instruction lagging repo evolution). `never_existed` may indicate parser false positive or never-valid instruction text.

---

## Misguidance categories (pilot counts)

| Category | When |
|----------|------|
| `stale_path` | Confident stale file path |
| `stale_directory` | Confident stale directory prefix |
| `stale_config` | Confident stale manifest/config |
| `stale_doc_reference` | Documentation path absent (separate track) |
| `never_existed_reference` | Stale + `historical_existence=never_existed` |
| `unresolved_reference` | Status `unresolved` |

Primary **stale rate** excludes `stale_doc_reference`, `ambiguous`, `unresolved`, and `unknown_command`.

---

## Limitations (pilot)

- Parser v2 coverage is incomplete; false negatives omit stale refs.
- **Parser–detector coupling:** v2 largely skips extracted tokens that do not resolve at HEAD (`low` confidence + absent path). Misguidance measured on v2 output is therefore a **conservative lower bound** and may under-estimate drift.
- Command viability is not executed; commands are not auto-stale.
- Documentation references are not primary misguidance but reported separately.
- Dot-prefix resolution errors (e.g. `.github/` → `github/`) may inflate or deflate stale counts.
- Pilot sample: 8 repos, 15 instruction files — **not** a population estimate.

---

## Outputs

| File | Content |
|------|---------|
| `results/misguidance/pilot/stale_references.csv` | Per-reference detection + history |
| `results/misguidance/pilot/misguidance_summary.csv` | Aggregates per instruction file and repo |
| `results/misguidance/pilot/misguidance_report.md` | Pilot interpretation |

Run: `make pilot-misguidance`
