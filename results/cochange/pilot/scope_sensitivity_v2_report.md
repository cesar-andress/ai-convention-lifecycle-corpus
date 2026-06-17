# Scope sensitivity pilot report (v2 parser)

**Parser version:** v2  
Methodological pilot only — do not generalize to a population.

## Sync@30 by scope mode (v2)

| repo | instruction | repo_wide | subtree | content_referenced | refs_used |
|------|-------------|-----------|---------|-------------------|-----------|
| `BerriAI/litellm` | `CLAUDE.md` | 27.0% | 27.0% | 27.3% | 12 |
| `BerriAI/litellm` | `litellm/proxy/_experimental/mcp_server/CLAUDE.md` | 2.7% | 9.7% | n/a | 0 |
| `apache/airflow` | `CLAUDE.md` | 1.6% | 1.6% | 3.0% | 86 |
| `apache/airflow` | `airflow-core/src/airflow/_shared/AGENTS.md` | 4.2% | 7.1% | 18.4% | 2 |
| `cheat/cheat` | `CLAUDE.md` | 2.7% | 2.7% | 15.0% | 28 |
| `dagster-io/dagster` | `CLAUDE.md` | 4.9% | 4.9% | 4.6% | 36 |
| `dagster-io/dagster` | `docs/CLAUDE.md` | 4.6% | 3.8% | 3.8% | 5 |
| `electron/electron` | `CLAUDE.md` | 1.8% | 1.8% | 2.3% | 15 |
| `electron/electron` | `docs/CLAUDE.md` | 0.6% | 0.7% | 0.7% | 11 |
| `grafana/grafana` | `CLAUDE.md` | 1.8% | 1.8% | 2.0% | 69 |
| `grafana/grafana` | `docs/AGENTS.md` | 1.5% | 1.1% | 1.1% | 3 |
| `payloadcms/payload` | `CLAUDE.md` | 8.8% | 8.8% | 12.6% | 34 |
| `payloadcms/payload` | `packages/codemod/CLAUDE.md` | 2.6% | 86.4% | 1.2% | 2 |
| `prefecthq/prefect` | `AGENTS.md` | 9.0% | 9.0% | 10.8% | 44 |
| `prefecthq/prefect` | `docs/AGENTS.md` | 7.1% | 5.6% | 5.6% | 30 |

## v1 vs v2 content-referenced comparison

| repo | instruction | v1 refs | v1 used | v2 refs | v2 used | v1 sync@30 | v2 sync@30 | Δ sync@30 |
|------|-------------|---------|---------|---------|---------|------------|------------|-----------|
| `BerriAI/litellm` | `CLAUDE.md` | 52 | 4 | 12 | 12 | 29.4% | 27.3% | -2.1% |
| `BerriAI/litellm` | `litellm/proxy/_experimental/mcp_server/CLAUDE.md` | 4 | 0 | 0 | 0 | n/a | n/a | n/a |
| `apache/airflow` | `CLAUDE.md` | 1 | 0 | 98 | 86 | n/a | 3.0% | n/a |
| `apache/airflow` | `airflow-core/src/airflow/_shared/AGENTS.md` | 6 | 0 | 2 | 2 | n/a | 18.4% | n/a |
| `cheat/cheat` | `CLAUDE.md` | 39 | 1 | 29 | 28 | 17.1% | 15.0% | -2.1% |
| `dagster-io/dagster` | `CLAUDE.md` | 68 | 6 | 36 | 36 | 4.6% | 4.6% | -0.0% |
| `dagster-io/dagster` | `docs/CLAUDE.md` | 20 | 3 | 6 | 5 | 4.4% | 3.8% | -0.6% |
| `electron/electron` | `CLAUDE.md` | 125 | 11 | 18 | 15 | 2.8% | 2.3% | -0.5% |
| `electron/electron` | `docs/CLAUDE.md` | 44 | 1 | 11 | 11 | 0.7% | 0.7% | 0.0% |
| `grafana/grafana` | `CLAUDE.md` | 1 | 0 | 72 | 69 | n/a | 2.0% | n/a |
| `grafana/grafana` | `docs/AGENTS.md` | 36 | 1 | 3 | 3 | 1.1% | 1.1% | 0.0% |
| `payloadcms/payload` | `CLAUDE.md` | 222 | 6 | 38 | 34 | 12.6% | 12.6% | -0.0% |
| `payloadcms/payload` | `packages/codemod/CLAUDE.md` | 25 | 2 | 3 | 2 | 1.2% | 1.2% | 0.0% |
| `prefecthq/prefect` | `AGENTS.md` | 110 | 16 | 45 | 44 | 10.9% | 10.8% | -0.1% |
| `prefecthq/prefect` | `docs/AGENTS.md` | 85 | 2 | 31 | 30 | 5.6% | 5.6% | 0.0% |

## Zero usable references (v2)

- `BerriAI/litellm` / `litellm/proxy/_experimental/mcp_server/CLAUDE.md`

## Interpretation guardrail

Optimize for scope validity, not recall.
