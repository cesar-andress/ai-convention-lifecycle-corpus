# Scope sensitivity pilot report

Methodological pilot only — do not generalize to a population.

**Repositories:** 8  
**Instruction files analyzed:** 7  
**Metric rows:** 45 (3 scope modes per instruction file)  

## Pilot repositories

| repo_id | reason | instruction files |
|---------|--------|-------------------|
| `cheat/cheat` | small single-root CLAUDE.md; code-heavy CLI tool | `CLAUDE.md` |
| `electron/electron` | small repo with root and nested docs/CLAUDE.md | `CLAUDE.md;docs/CLAUDE.md` |
| `dagster-io/dagster` | medium artifact count but large monorepo history; root+nested CLAUDE.md | `CLAUDE.md;docs/CLAUDE.md` |
| `apache/airflow` | monorepo with multiple AGENTS/CLAUDE paths; code-heavy OSS | `CLAUDE.md;airflow-core/src/airflow/_shared/AGENTS.md` |
| `BerriAI/litellm` | medium repo with multiple root and nested instruction files | `CLAUDE.md;litellm/proxy/_experimental/mcp_server/CLAUDE.md` |
| `payloadcms/payload` | documentation- and package-heavy monorepo | `CLAUDE.md;packages/codemod/CLAUDE.md` |
| `prefecthq/prefect` | medium-large Python monorepo with multiple instruction paths | `AGENTS.md;docs/AGENTS.md` |
| `grafana/grafana` | large code-heavy frontend/backend monorepo | `CLAUDE.md;docs/AGENTS.md` |

## Sync@30 by scope mode

| repo | instruction | repo_wide | subtree | content_referenced |
|------|-------------|-----------|---------|-------------------|
| `BerriAI/litellm` | `CLAUDE.md` | 27.0% | 27.0% | 29.4% |
| `BerriAI/litellm` | `litellm/proxy/_experimental/mcp_server/CLAUDE.md` | 2.7% | 9.7% | n/a |
| `apache/airflow` | `CLAUDE.md` | 1.6% | 1.6% | n/a |
| `apache/airflow` | `airflow-core/src/airflow/_shared/AGENTS.md` | 4.2% | 7.1% | n/a |
| `cheat/cheat` | `CLAUDE.md` | 2.7% | 2.7% | 17.1% |
| `dagster-io/dagster` | `CLAUDE.md` | 4.9% | 4.9% | 4.6% |
| `dagster-io/dagster` | `docs/CLAUDE.md` | 4.6% | 3.8% | 4.4% |
| `electron/electron` | `CLAUDE.md` | 1.8% | 1.8% | 2.8% |
| `electron/electron` | `docs/CLAUDE.md` | 0.6% | 0.7% | 0.7% |
| `grafana/grafana` | `CLAUDE.md` | 1.8% | 1.8% | n/a |
| `grafana/grafana` | `docs/AGENTS.md` | 1.5% | 1.1% | 1.1% |
| `payloadcms/payload` | `CLAUDE.md` | 8.8% | 8.8% | 12.6% |
| `payloadcms/payload` | `packages/codemod/CLAUDE.md` | 2.6% | 86.4% | 1.2% |
| `prefecthq/prefect` | `AGENTS.md` | 9.0% | 9.0% | 10.9% |
| `prefecthq/prefect` | `docs/AGENTS.md` | 7.1% | 5.6% | 5.6% |

## Strong repo-wide vs content-referenced divergence (sync@30)

- `cheat/cheat` / `CLAUDE.md`: repo-wide 2.7% vs content 17.1% (Δ=14.4%; refs_used=1; events_repo_wide=859)
- `payloadcms/payload` / `CLAUDE.md`: repo-wide 8.8% vs content 12.6% (Δ=3.9%; refs_used=6; events_repo_wide=13756)
- `BerriAI/litellm` / `CLAUDE.md`: repo-wide 27.0% vs content 29.4% (Δ=2.3%; refs_used=4; events_repo_wide=33078)

## Interpretation prompts

- If repo-wide sync@30 is near zero but content-referenced sync@30 is materially higher, repo-wide scope may be too broad.
- If content-referenced scope has zero resolved references, treat that mode as inconclusive rather than as high synchronization.
- For root instruction files, subtree and repo-wide modes are equivalent by design in this pilot.
