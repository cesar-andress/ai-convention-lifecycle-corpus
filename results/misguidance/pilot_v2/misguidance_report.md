# Misguidance pilot report

Generated: `2026-06-16T23:25:47.619778+00:00`

Extraction mode: **misguidance extraction (v2)**

**Pilot only — no population claims.** Stale references are *possible instruction–code drift*, not proven errors.

Definitions: `docs/misguidance_definition.md`, `docs/misguidance_extraction_audit.md`

## Pilot v1 vs v2 comparison

| Metric | v1 (scope extraction) | v2 (misguidance extraction) | Δ |
|--------|----------------------:|----------------------------:|--:|
| References extracted | 404 | 736 | +332 |
| Valid | 401 | 401 | +0 |
| Primary stale | 0 | 322 | +322 |
| Ambiguous | 3 | 0 | -3 |
| Unresolved | 0 | 2 | +2 |
| Primary stale rate | 0.0% | 43.8% | — |
| `existed_before` (history) | 0 | 38 | +38 |

## Pilot coverage

- Repositories: **8**
- Instruction files: **15**
- References extracted: **736**

## Headline counts (instruction files)

- Valid at HEAD: **401**
- Primary stale (excludes docs/commands/ambiguous): **322**
- Stale documentation references: **9**
- All stale-type (primary + doc): **331**
- Ambiguous: **0**
- Unresolved: **2**

Primary stale rate (conservative): **43.8%** (322/736)

## Historical existence (stale, doc-stale, ambiguous, unresolved)

- Previously existed (`existed_before`): **38**
- Never existed in git history: **295**

### By detection status

- `doc_reference` + `existed_before`: 3
- `doc_reference` + `never_existed`: 6
- `stale` + `existed_before`: 35
- `stale` + `never_existed`: 287
- `unresolved` + `never_existed`: 2

## Category breakdown

- `existed_before_reference`: 38
- `never_existed_reference`: 295
- `stale_config`: 1
- `stale_directory`: 98
- `stale_doc_reference`: 9
- `stale_path`: 223
- `unresolved_reference`: 2

## Per instruction file

| repo | instruction | n_refs | valid | primary_stale | stale_doc | ambiguous | unresolved | stale_rate |
|------|-------------|--------|-------|---------------|-----------|-----------|------------|------------|
| `BerriAI/litellm` | `CLAUDE.md` | 29 | 12 | 17 | 0 | 0 | 0 | 58.6% |
| `BerriAI/litellm` | `litellm/proxy/_experimental/mcp_server/CLAUDE.md` | 3 | 0 | 3 | 0 | 0 | 0 | 100.0% |
| `apache/airflow` | `CLAUDE.md` | 189 | 96 | 88 | 5 | 0 | 0 | 46.6% |
| `apache/airflow` | `airflow-core/src/airflow/_shared/AGENTS.md` | 2 | 2 | 0 | 0 | 0 | 0 | 0.0% |
| `cheat/cheat` | `CLAUDE.md` | 39 | 29 | 9 | 0 | 0 | 1 | 23.1% |
| `dagster-io/dagster` | `CLAUDE.md` | 48 | 36 | 12 | 0 | 0 | 0 | 25.0% |
| `dagster-io/dagster` | `docs/CLAUDE.md` | 10 | 6 | 4 | 0 | 0 | 0 | 40.0% |
| `electron/electron` | `CLAUDE.md` | 65 | 18 | 45 | 0 | 0 | 1 | 69.2% |
| `electron/electron` | `docs/CLAUDE.md` | 21 | 11 | 7 | 3 | 0 | 0 | 33.3% |
| `grafana/grafana` | `CLAUDE.md` | 106 | 72 | 34 | 0 | 0 | 0 | 32.1% |
| `grafana/grafana` | `docs/AGENTS.md` | 7 | 3 | 4 | 0 | 0 | 0 | 57.1% |
| `payloadcms/payload` | `CLAUDE.md` | 94 | 38 | 56 | 0 | 0 | 0 | 59.6% |
| `payloadcms/payload` | `packages/codemod/CLAUDE.md` | 8 | 3 | 5 | 0 | 0 | 0 | 62.5% |
| `prefecthq/prefect` | `AGENTS.md` | 66 | 45 | 21 | 0 | 0 | 0 | 31.8% |
| `prefecthq/prefect` | `docs/AGENTS.md` | 49 | 30 | 17 | 1 | 0 | 0 | 34.7% |

## Research questions (pilot answers)

1. **How much did extraction volume increase?** v2 extracted **736** refs vs v1 **404** (**+332**, 82.2% relative increase).
2. **How many stale references now appear?** Primary stale **322**, doc-stale **9**, ambiguous **0**, unresolved **2**.
3. **How many previously existed?** `existed_before=38` (stronger drift evidence), `never_existed=295` (possible parser noise or never-valid text).
4. **Is misguidance now measurable?** Yes — non-zero stale or historical drift signal under misguidance extraction.
5. **Enough signal for full-corpus collection?** Promising for a bounded full-corpus *pilot extension* after manual spot-check of `existed_before` examples (38 refs); not ready for population claims.

## Examples — valid references

- `cheat/cheat` / `CLAUDE.md`: `make build` → `Makefile` (valid)
- `cheat/cheat` / `CLAUDE.md`: `make build-release` → `Makefile` (valid)
- `cheat/cheat` / `CLAUDE.md`: `make install` → `Makefile` (valid)
- `cheat/cheat` / `CLAUDE.md`: `make test` → `Makefile` (valid)
- `cheat/cheat` / `CLAUDE.md`: `internal` → `internal/` (valid)
- `cheat/cheat` / `CLAUDE.md`: `make coverage` → `Makefile` (valid)
- `cheat/cheat` / `CLAUDE.md`: `make lint` → `Makefile` (valid)
- `cheat/cheat` / `CLAUDE.md`: `make vet` → `Makefile` (valid)

## Examples — possible drift (stale / existed_before)

- `cheat/cheat` / `CLAUDE.md`: `claude.ai/code` → `claude.ai/code` (stale, `stale_path`, history=`never_existed`)
- `cheat/cheat` / `CLAUDE.md`: `./internal/package_name` → `internal/package_name` (stale, `stale_path`, history=`existed_before`)
- `cheat/cheat` / `CLAUDE.md`: `packages` → `packages/` (stale, `stale_directory`, history=`never_existed`)
- `cheat/cheat` / `CLAUDE.md`: `main.go` → `main.go` (stale, `stale_path`, history=`never_existed`)
- `cheat/cheat` / `CLAUDE.md`: `cmd_*.go` → `cmd_*.go` (stale, `stale_path`, history=`never_existed`)
- `cheat/cheat` / `CLAUDE.md`: `generate.go` → `generate.go` (stale, `stale_path`, history=`never_existed`)
- `cheat/cheat` / `CLAUDE.md`: `conf.yml` → `conf.yml` (stale, `stale_path`, history=`never_existed`)
- `cheat/cheat` / `CLAUDE.md`: `.cheat` → `cheat` (stale, `stale_path`, history=`existed_before`)
- `cheat/cheat` / `CLAUDE.md`: `.git` → `git` (stale, `stale_path`, history=`never_existed`)
- `electron/electron` / `CLAUDE.md`: `packages` → `packages/` (stale, `stale_directory`, history=`never_existed`)
- `electron/electron` / `CLAUDE.md`: `node_modules/.bin/<tool>` → `node_modules/.bin/<tool` (stale, `stale_path`, history=`never_existed`)
- `electron/electron` / `CLAUDE.md`: `node_modules/.bin/` → `node_modules/.bin/` (stale, `stale_directory`, history=`never_existed`)
- `electron/electron` / `CLAUDE.md`: `backend` → `backend/` (stale, `stale_directory`, history=`never_existed`)
- `electron/electron` / `CLAUDE.md`: `API` → `api/` (stale, `stale_directory`, history=`never_existed`)
- `electron/electron` / `CLAUDE.md`: `modules` → `modules/` (stale, `stale_directory`, history=`never_existed`)

## Limitations

- Stale labels indicate *possible* instruction–code drift, not agent harm or author error.
- Commands are not executed; command targets are not auto-stale.
- Documentation references tracked separately from primary misguidance.
- Eight pilot repos — not a population sample.
