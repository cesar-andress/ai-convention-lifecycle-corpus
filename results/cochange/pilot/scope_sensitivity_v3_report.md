# Scope sensitivity pilot report (v3 — package-subtree)

**Parser version:** v2  
Methodological pilot — do not generalize to a population.

## Sync@30 by scope mode

| repo | instruction | repo_wide | subtree | content_ref | package_subtree | pkg status |
|------|-------------|-----------|---------|-------------|-----------------|------------|
| `BerriAI/litellm` | `CLAUDE.md` | 27.0% | 27.0% | 27.3% | n/a | inconclusive_no_package_roots |
| `BerriAI/litellm` | `litellm/proxy/_experimental/mcp_server/CLAUDE.md` | 2.7% | 9.7% | n/a | 9.7% | fallback_subtree_nested |
| `apache/airflow` | `CLAUDE.md` | 1.6% | 1.6% | 3.0% | 3.7% | usable |
| `apache/airflow` | `airflow-core/src/airflow/_shared/AGENTS.md` | 4.2% | 7.1% | 18.4% | 13.7% | usable |
| `cheat/cheat` | `CLAUDE.md` | 2.7% | 2.7% | 15.0% | n/a | inconclusive_no_package_roots |
| `dagster-io/dagster` | `CLAUDE.md` | 4.9% | 4.9% | 4.6% | 4.6% | usable |
| `dagster-io/dagster` | `docs/CLAUDE.md` | 4.6% | 3.8% | 3.8% | 3.8% | usable |
| `electron/electron` | `CLAUDE.md` | 1.8% | 1.8% | 2.3% | 4.9% | usable |
| `electron/electron` | `docs/CLAUDE.md` | 0.6% | 0.7% | 0.7% | 0.7% | fallback_subtree_nested |
| `grafana/grafana` | `CLAUDE.md` | 1.8% | 1.8% | 2.0% | 2.8% | usable |
| `grafana/grafana` | `docs/AGENTS.md` | 1.5% | 1.1% | 1.1% | 1.1% | fallback_subtree_nested |
| `payloadcms/payload` | `CLAUDE.md` | 8.8% | 8.8% | 12.6% | 13.1% | usable |
| `payloadcms/payload` | `packages/codemod/CLAUDE.md` | 2.6% | 86.4% | 1.2% | 86.4% | usable |
| `prefecthq/prefect` | `AGENTS.md` | 9.0% | 9.0% | 10.8% | 11.8% | usable |
| `prefecthq/prefect` | `docs/AGENTS.md` | 7.1% | 5.6% | 5.6% | 5.6% | fallback_subtree_nested |

## Package-subtree vs repo-wide (sync@30 delta)

- `payloadcms/payload` / `packages/codemod/CLAUDE.md`: repo-wide 2.6% → package-subtree 86.4% (Δ=83.7%; roots=packages/codemod/)
- `apache/airflow` / `airflow-core/src/airflow/_shared/AGENTS.md`: repo-wide 4.2% → package-subtree 13.7% (Δ=9.4%; roots=airflow-core/)
- `payloadcms/payload` / `CLAUDE.md`: repo-wide 8.8% → package-subtree 13.1% (Δ=4.4%; roots=packages/;packages/drizzle/;packages/graphql/;packages/kv-redis/;packages/next/;packages/payload/;packages/richtext-lexical/;packages/translations/;packages/ui/;test/)
- `electron/electron` / `CLAUDE.md`: repo-wide 1.8% → package-subtree 4.9% (Δ=3.1%; roots=github/workflows/;spec/)
- `prefecthq/prefect` / `AGENTS.md`: repo-wide 9.0% → package-subtree 11.8% (Δ=2.8%; roots=client/;src/;ui-v2/;ui/)
- `apache/airflow` / `CLAUDE.md`: repo-wide 1.6% → package-subtree 3.7% (Δ=2.1%; roots=airflow-core/;airflow-ctl/;chart/;dev/;dev/breeze/;dev/mypy/;devel-common/;providers/amazon/;scripts/;task-sdk/)
- `grafana/grafana` / `CLAUDE.md`: repo-wide 1.8% → package-subtree 2.8% (Δ=1.0%; roots=apps/;apps/dashboard/;apps/folder/;packages/;pkg/plugins/)
- `dagster-io/dagster` / `docs/CLAUDE.md`: repo-wide 4.6% → package-subtree 3.8% (Δ=-0.8%; roots=docs/)
- `dagster-io/dagster` / `CLAUDE.md`: repo-wide 4.9% → package-subtree 4.6% (Δ=-0.3%; roots=docs/;examples/;js_modules/;python_modules/;python_modules/dagster/)

## Package-subtree vs content-referenced agreement

**Within 5 pp (usable package-subtree):**
- `apache/airflow` / `CLAUDE.md`: content 3.0% vs package 3.7%
- `apache/airflow` / `airflow-core/src/airflow/_shared/AGENTS.md`: content 18.4% vs package 13.7%
- `dagster-io/dagster` / `CLAUDE.md`: content 4.6% vs package 4.6%
- `dagster-io/dagster` / `docs/CLAUDE.md`: content 3.8% vs package 3.8%
- `electron/electron` / `CLAUDE.md`: content 2.3% vs package 4.9%
- `grafana/grafana` / `CLAUDE.md`: content 2.0% vs package 2.8%
- `payloadcms/payload` / `CLAUDE.md`: content 12.6% vs package 13.1%
- `prefecthq/prefect` / `AGENTS.md`: content 10.8% vs package 11.8%

**Differ by >5 pp (usable package-subtree):**
- `payloadcms/payload` / `packages/codemod/CLAUDE.md`: content 1.2% vs package 86.4%

## Inconclusive package-subtree cases

- `cheat/cheat` / `CLAUDE.md`: **inconclusive_no_package_roots** (detected roots=2)
- `BerriAI/litellm` / `CLAUDE.md`: **inconclusive_no_package_roots** (detected roots=15)

## Nested fallback to subtree

- `electron/electron` / `docs/CLAUDE.md`: sync@30=0.7% (roots `docs/`)
- `BerriAI/litellm` / `litellm/proxy/_experimental/mcp_server/CLAUDE.md`: sync@30=9.7% (roots `litellm/proxy/_experimental/mcp_server/`)
- `prefecthq/prefect` / `docs/AGENTS.md`: sync@30=5.6% (roots `docs/`)
- `grafana/grafana` / `docs/AGENTS.md`: sync@30=1.1% (roots `docs/`)

## Interpretation guardrail

Optimize validity over recall.
