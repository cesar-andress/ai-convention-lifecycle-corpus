# Validated drift — decision support (preliminary)

Generated: `2026-06-16T23:31:11.453077+00:00`

**Not ground truth yet** — manual labels in `validated_drift_ground_truth.csv` are empty.

## Stage 5 — Evidence strength estimate (automatic, not manual)

- **Strong:** 2 candidates
- **Moderate:** 13 candidates
- **Weak:** 23 candidates

### Strong candidates

- `DC006` `dagster-io/dagster`: `setup.py` (deleted 2018-07-19)
- `DC005` `dagster-io/dagster`: `examples/docs_snippets/docs_snippets/intro_tutorial/basics/connecting_ops/` (deleted 2026-04-23)

### Moderate candidates

- `DC011` `apache/airflow`: `airflow/cli/cli_parser.py`
- `DC012` `apache/airflow`: `tests/cli/test_cli_parser.py`
- `DC013` `apache/airflow`: `airflow/cli/cli_parser.py`
- `DC014` `apache/airflow`: `tests/cli/test_cli_parser.py`
- `DC029` `payloadcms/payload`: `src/`
- `DC030` `payloadcms/payload`: `src`
- `DC031` `payloadcms/payload`: `dev`
- `DC035` `payloadcms/payload`: `Dev`
- `DC015` `apache/airflow`: `newsfragments/`
- `DC009` `apache/airflow`: `src`
- `DC010` `apache/airflow`: `tests/`
- `DC002` `cheat/cheat`: `.cheat`
- `DC032` `payloadcms/payload`: `.scss`

### Weak candidates

23 candidates — review last or mark as parser artifacts.

## Stage 6 — Decision support

### 1. If only **strong** candidates are accepted, how many remain?

**2** (automatic pre-filter; manual review may accept fewer).

### 2. If **strong + moderate** are accepted, how many remain?

**15** (upper bound before manual pruning).

### 3. Is the resulting phenomenon large enough for a dedicated paper?

A **focused qualitative / case-study paper** is more defensible than a prevalence paper; the core phenomenon appears real but narrow.

### 4. Recommended next study design

**Focused qualitative study** first; defer full-corpus measurement until ground-truth labels confirm ≥5 real drift cases.

## Objective reminder

Maximizing drift counts is not the goal. The defensible core is the manually validated subset of strong/moderate cases with reliable deletion history and literal instruction references.
