# Multi-family replication design

Design note for extending the adoption--maintenance measurement protocol beyond the bundled AI-convention detector family.

**Status:** specification only; no additional artifact families are extracted in release v2.0.0.

---

## 1. Goal

Enable independent replications that apply the **same gap machinery** to different artifact families without conflating:

- detector coverage (what paths enter the panel),
- measurement definitions (adoption, maintenance, maturity, states),
- aggregation level (equal-weight path vs existential repository estimands),
- sample design (seed pools, discovery quotas).

Generality claims require **paired results per family**, not pooled headline numbers.

---

## 2. Detector family abstraction

Each artifact family is a self-contained configuration with the following fields.

| Field | Required | Description |
|-------|----------|-------------|
| `family_id` | yes | Stable identifier (e.g., `ai_conventions_v1`, `gh_actions_v1`) |
| `family_label` | yes | Human-readable name for papers and dataset cards |
| `extends` | no | Base protocol YAML (typically `protocol/adoption_maintenance_v1.yaml`) |
| `artifact_patterns` | yes | List of `{id, regex}` inclusion rules |
| `exclude_path_prefixes` | yes | Vendor/build directory prefixes |
| `exclude_basenames` | recommended | Generic documentation filenames |
| `exclude_path_regex` | optional | Family-specific false-positive filters |
| `seed_pools` | yes | Discovery seed file lists |
| `discovery` | yes | Quotas, timeouts, output paths |
| `maintenance_windows_days` | yes | Primary and sensitivity *T* values |
| `analysis` | yes | Bootstrap, LOO, concentration exclusions |

Reference implementation: `protocol/lifecycle_v1.yaml` (current AI family) and `scripts/lifecycle/detection.py`.

Template file (non-executing): `protocol/detector_family_template.yaml`.

---

## 3. Inclusion and exclusion patterns

**Inclusion** defines which repository-relative paths become artifact instances.

**Exclusion** is evaluated **before** inclusion in `detection.py`:

1. Prefix match (`exclude_path_prefixes`)
2. Basename match (`exclude_basenames`)
3. Regex match (`exclude_path_regex`)

Document exclusions in prose separately from inclusion rules so reviewers cannot confuse `README.md` or `node_modules/` with analyzed artifacts.

Each family should record:

- expected multiplicity (median instances per repo),
- known false-positive classes,
- rationale for family-specific exclusions.

---

## 4. Required pipeline outputs per family

For each `{family_id}` run, freeze:

| Output | Purpose |
|--------|---------|
| `discovered_{family}.csv` | Discovery funnel |
| `artifacts_{family}.parquet` | Path panel |
| `adoption_maintenance_{family}.json` | Headline + sensitivity bundle |
| `bootstrap_{family}.json` | Cluster CIs at each *T* |
| `loo_{family}.csv` | Leave-one-repo-out |
| `funnel_{family}.csv` | Lifecycle counts by *T* |

Gap computation reuses `adoption_maintenance.py` functions:

- `gap_artifact_mature(df, T)`
- `gap_repo_level(df, T)`

No changes to gap formulas are required when swapping detectors.

---

## 5. Paired gaps per family

For each threshold *T* in `{90, 180, 365}` (or family-specific sensitivity set), report:

| Estimand | Denominator | Numerator (gap) |
|----------|-------------|-----------------|
| Artifact gap | mature-present paths | share DORMANT |
| Repository gap | adopted repos | repos with no maintained mature-present path |

Always report **both** on the same extracted panel, plus:

- instance concentration (mean, median, top-*k* repos),
- bootstrap CIs,
- LOO max |Δ|,
- pre-specified concentration exclusion (if any).

---

## 6. Comparing families

Cross-family synthesis is **descriptive**, not pooled:

| Comparison dimension | Report |
|---------------------|--------|
| Multiplicity | median/mean instances per repo |
| Headline spread | artifact gap − repository gap at primary *T* |
| Sensitivity ratio | LOO max |Δ| artifact / LOO max |Δ| repo |
| CI width | artifact CI width / repo CI width |
| Concentration | gap with and without top-*k* repos |

Do **not** average gap rates across families without explicit weighting and justification.

---

## 7. Responsible generality claims

| Claim level | Evidence bar |
|-------------|--------------|
| Protocol reusable | One family implemented + docs + frozen YAML |
| Paired estimands diverge when multiplicity high | Demonstrated in ≥1 family with concentration stats |
| Pattern generalizes across repository artifacts | ≥2 families, same protocol, separate headline tables |
| Numeric gaps generalize | Not supported without representative sampling per family |

Until multi-family tables exist, manuscripts should state:

> "The protocol is family-parameterized; numeric results describe `{family_label}` under `{seed/design}` only."

---

## 8. Planned families (not yet implemented)

| Family | Inclusion sketch | Multiplicity expectation |
|--------|------------------|------------------------|
| GitHub Actions workflows | `(^|/)\.github/workflows/.*\.ya?ml$` | High in CI-heavy repos |
| Dependency manifests | `package.json`, `requirements*.txt`, `go.mod`, … | Medium; bot-driven touches |
| Dockerfiles | `(^|/)Dockerfile$`, `docker-compose*.yml` | Low–medium |
| CI config (legacy) | `.travis.yml`, `Jenkinsfile`, `.circleci/` | Low |
| Doc conventions | `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` | Low (often one per repo) |
| Issue/PR templates | `.github/ISSUE_TEMPLATE/`, `PULL_REQUEST_TEMPLATE.md` | Low–medium |

Each requires its own seed strategy and exclusion rules (e.g., vendored workflows under `node_modules/`).

---

## 9. Implementation steps for a new family

1. Copy `protocol/detector_family_template.yaml` → `protocol/{family_id}.yaml`.
2. Define inclusion/exclusion patterns; review false positives on a pilot of ~20 repos.
3. Add seed pool files under `seeds/{family_id}/`.
4. Wire discovery script or parameterize `discover_v2.py` with `--config`.
5. Run extraction → build → `adoption_maintenance_v2.py` (or family-specific driver).
6. Verify headline JSON against manuscript tables.
7. Add family row to cross-family comparison table (future paper section).

---

## 10. Code touch points

| Module | Role |
|--------|------|
| `scripts/lifecycle/detection.py` | Load YAML; `artifact_type()`, `is_excluded()` |
| `scripts/lifecycle/discover_v2.py` | Shallow discovery against detector |
| `scripts/lifecycle/extract_history.py` | Full clone + touch extraction |
| `scripts/lifecycle/build_dataset.py` | Artifact parquet build |
| `scripts/lifecycle/adoption_maintenance_v2.py` | Gaps, bootstrap, LOO, JSON bundle |
| `protocol/adoption_maintenance_v1.yaml` | Measurement definitions (family-agnostic) |

**Non-breaking extension:** pass `config=` path into `load_config()` (already supported); add CLI `--detector-config` to pipeline entry points without changing default `lifecycle_v1.yaml`.
