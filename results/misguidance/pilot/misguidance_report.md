# Misguidance pilot report

Generated: `2026-06-16T23:14:19.102256+00:00`

**Pilot only — no population claims.**

Definition: `docs/misguidance_definition.md`

## Pilot coverage

- Repositories: **8**
- Instruction files: **15**
- References extracted (parser v2): **404**

## Headline counts (instruction files)

- Valid at HEAD: **401**
- Primary stale (excludes docs/commands/ambiguous): **0**
- Stale documentation references: **0**
- All stale-type (primary + doc): **0**
- Ambiguous: **3**
- Unresolved: **0**
- Unknown command: **0**

Primary stale rate (conservative): **0.0%** (0/404)

## Historical existence (stale + doc stale)

- Previously existed (`existed_before`): **0**
- Never existed in git history: **0**

## Category breakdown


## Per instruction file

| repo | instruction | n_refs | valid | primary_stale | stale_doc | ambiguous | stale_rate |
|------|-------------|--------|-------|---------------|-----------|-----------|------------|
| `BerriAI/litellm` | `CLAUDE.md` | 12 | 12 | 0 | 0 | 0 | 0.0% |
| `BerriAI/litellm` | `litellm/proxy/_experimental/mcp_server/CLAUDE.md` | 0 | 0 | 0 | 0 | 0 | n/a |
| `apache/airflow` | `CLAUDE.md` | 98 | 96 | 0 | 0 | 2 | 0.0% |
| `apache/airflow` | `airflow-core/src/airflow/_shared/AGENTS.md` | 2 | 2 | 0 | 0 | 0 | 0.0% |
| `cheat/cheat` | `CLAUDE.md` | 29 | 29 | 0 | 0 | 0 | 0.0% |
| `dagster-io/dagster` | `CLAUDE.md` | 36 | 36 | 0 | 0 | 0 | 0.0% |
| `dagster-io/dagster` | `docs/CLAUDE.md` | 6 | 6 | 0 | 0 | 0 | 0.0% |
| `electron/electron` | `CLAUDE.md` | 18 | 18 | 0 | 0 | 0 | 0.0% |
| `electron/electron` | `docs/CLAUDE.md` | 11 | 11 | 0 | 0 | 0 | 0.0% |
| `grafana/grafana` | `CLAUDE.md` | 72 | 72 | 0 | 0 | 0 | 0.0% |
| `grafana/grafana` | `docs/AGENTS.md` | 3 | 3 | 0 | 0 | 0 | 0.0% |
| `payloadcms/payload` | `CLAUDE.md` | 38 | 38 | 0 | 0 | 0 | 0.0% |
| `payloadcms/payload` | `packages/codemod/CLAUDE.md` | 3 | 3 | 0 | 0 | 0 | 0.0% |
| `prefecthq/prefect` | `AGENTS.md` | 45 | 45 | 0 | 0 | 0 | 0.0% |
| `prefecthq/prefect` | `docs/AGENTS.md` | 31 | 30 | 0 | 0 | 1 | 0.0% |

## Per repository (aggregated)

| repo | n_refs | primary_stale | stale_doc | stale_rate | existed_before | never_existed |
|------|--------|---------------|-----------|------------|----------------|---------------|
| `BerriAI/litellm` | 12 | 0 | 0 | 0.0% | 0 | 0 |
| `apache/airflow` | 100 | 0 | 0 | 0.0% | 0 | 0 |
| `cheat/cheat` | 29 | 0 | 0 | 0.0% | 0 | 0 |
| `dagster-io/dagster` | 42 | 0 | 0 | 0.0% | 0 | 0 |
| `electron/electron` | 29 | 0 | 0 | 0.0% | 0 | 0 |
| `grafana/grafana` | 75 | 0 | 0 | 0.0% | 0 | 0 |
| `payloadcms/payload` | 41 | 0 | 0 | 0.0% | 0 | 0 |
| `prefecthq/prefect` | 76 | 0 | 0 | 0.0% | 0 | 0 |

## Research questions (pilot answers)

1. **Do stale references exist?** No primary-stale references detected under conservative rules.
2. **Are they common?** Primary stale rate 0.0% across 404 extracted refs in 15 instruction files (pilot only).
3. **Which categories dominate?** None
4. **How many previously existed?** `existed_before=0`, `never_existed=0`.
5. **Strong enough to scale?** Observable primary-stale signal is near zero on parser-v2 output in this pilot, likely due to extractor selection bias (non-resolving tokens are mostly dropped). Before scaling, add a misguidance-oriented extraction mode that retains unresolved medium/high-confidence references and re-run the pilot.

## Examples — valid references

- `cheat/cheat` / `CLAUDE.md`: `make build` → `Makefile` (valid)
- `cheat/cheat` / `CLAUDE.md`: `make build-release` → `Makefile` (valid)
- `cheat/cheat` / `CLAUDE.md`: `make install` → `Makefile` (valid)
- `cheat/cheat` / `CLAUDE.md`: `make test` → `Makefile` (valid)
- `cheat/cheat` / `CLAUDE.md`: `internal` → `internal/` (valid)
- `cheat/cheat` / `CLAUDE.md`: `make coverage` → `Makefile` (valid)
- `cheat/cheat` / `CLAUDE.md`: `make lint` → `Makefile` (valid)
- `cheat/cheat` / `CLAUDE.md`: `make vet` → `Makefile` (valid)

## Examples — stale references

_None under conservative rules._

## Limitations

- Parser v2 incomplete coverage; stale rate is a lower bound on inconsistency, not an upper bound.
- **Selection bias:** parser v2 mostly omits tokens that fail HEAD resolution; primary stale rate 0% may reflect pipeline design, not absence of drift.
- Commands are not executed; `unknown_command` is not misguidance.
- Documentation staleness is reported separately from primary misguidance.
- Eight pilot repos / fifteen instruction files — not representative of all OSS.
