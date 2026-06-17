# Synchronization spectrum pilot — design

**Status:** pilot specification for empirical positioning of AI instruction files between enforced configuration and traditional documentation.

**Scope:** 20–30 repositories with local clones; no new extraction rules, parsers, or lifecycle pipeline changes.

---

## 1. Research question

Where do AI instruction files sit on the synchronization spectrum?

| Pole | Example | Stale artifact consequence |
|------|---------|----------------------------|
| Enforced configuration | `.github/workflows/ci.yml`, `package.json` | Build or dependency resolution may break |
| AI instruction files | `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/*` | Unclear — intermediate enforcement |
| Traditional documentation | `README.md`, `CONTRIBUTING.md` | Usually non-blocking |

---

## 2. Stage 1 — Family selection

Families are matched **at analysis time** from git history and HEAD file lists. This reuses existing changed-file manifests and lifecycle parquet rows; it does **not** extend `protocol/lifecycle_v1.yaml` or add detector families.

### Spectrum groups and families

| Spectrum group | `family_id` | Inclusion pattern (repo-relative path) | Anchor selection |
|----------------|-------------|----------------------------------------|------------------|
| **instructions** | `claude_md` | `(^|/)CLAUDE\.md$` | Prefer repository root; else deepest path with most touches |
| **instructions** | `agents_md` | `(^|/)AGENTS\.md$` | Same as above |
| **instructions** | `cursor_rules` | `(^|/)\.cursor/rules/.*\.(md\|mdc)$` | Prefer `.cursor/rules/` file with most touches |
| **configuration** | `github_workflows` | `(^|/)\.github/workflows/.*\.ya?ml$` | Workflow with most historical touches |
| **configuration** | `package_json` | `(^|/)package\.json$` | Prefer repository root |
| **configuration** | `pyproject_toml` | `(^|/)pyproject\.toml$` | Prefer repository root |
| **configuration** | `go_mod` | `(^|/)go\.mod$` | Prefer repository root |
| **documentation** | `readme` | `(^|/)README\.md$` | Prefer repository root |
| **documentation** | `contributing` | `(^|/)CONTRIBUTING\.md$` | Prefer repository root |
| **documentation** | `docs_index` | `^docs/(README\.md\|index\.md\|index\.html)$` | First match in priority order |

### Repository inclusion criteria (pilot sample)

1. Listed in `data/lifecycle/discovered_v2.csv` with a local clone under `data/repos/`.
2. At least one AI instruction artifact present in HEAD (`artifact_states_v2.parquet`, types in `{claude_md, agents_md, cursor_rules, copilot_instructions, skill_md}`).
3. Stratified expansion beyond the eight co-change pilot repos: round-robin across `seed_pool` values to reach **25 repositories** total.
4. Fixed inclusion of the eight co-change scope pilot repos for continuity with prior co-change analyses.

### Per-family inclusion criteria

A `(repo, family)` row is emitted only when:

- An anchor path matching the family pattern appears in the changed-file manifest **or** in HEAD; and
- The anchor is not under excluded vendor/build prefixes (`cochange.scope.EXCLUDED_PREFIXES`).

Families with no qualifying anchor in a repository are omitted (not imputed).

---

## 3. Stage 2 — Synchronization metrics

All cross-family comparisons use **repo-wide governed scope** (`ScopeMode.REPO_WIDE` in `sync_engine.py`) so configuration, instructions, and documentation are measured against the same code-change event definition.

| Metric | Operational definition | Source |
|--------|------------------------|--------|
| **update frequency** | Anchor-touch commits / repository observation span (years) | Changed-file manifest |
| **update lag** | Median days from repo-wide code event to next anchor update within W=30 | `sync_engine.compute_scope_metrics` |
| **co-change rate** | Share of repo-wide code events with anchor update in the same commit (W=0) | `sync_0` |
| **sync@7** | Share of repo-wide code events followed by anchor update within 7 days | `sync_7` |
| **sync@30** | Share of repo-wide code events followed by anchor update within 30 days | `sync_30` |
| **lifecycle persistence** | `maintained_180 / mature_present_180` at primary 180-day window | Lifecycle parquet for instruction paths; git-derived analogue for config/docs |

**Governed-code event:** commit modifying ≥1 non-excluded, non-anchor path under repo-wide scope, with ≥1 path other than the anchor (mirrors co-change prototype assumptions).

---

## 4. Stage 3 — Calibration

For each metric, compute group-level medians across `(repo, family)` rows within:

- `configuration`
- `instructions`
- `documentation`

Normalize metrics to a **0–1 synchronization index** per metric (min–max across the three group medians), then average across metrics with defined values. Lower index → documentation-like; higher index → configuration-like.

This is a descriptive pilot index — not a population estimand.

---

## 5. Stage 4 — Pilot execution

- Target: **25 repositories** (`results/synchronization_spectrum/pilot_repos.csv`).
- Changed-file manifests cached under `results/synchronization_spectrum/manifests/`.
- Driver: `scripts/spectrum/run_pilot.py` (`make synchronization-spectrum-pilot`).

---

## 6. Stage 5 — Outputs

| File | Content |
|------|---------|
| `family_metrics.csv` | One row per `(repo_id, family_id)` with all metrics |
| `family_comparison.csv` | Aggregated medians/IQR by `spectrum_group` and `family_id` |
| `synchronization_spectrum_report.md` | Methods summary, calibration table, Stage 6 decision answers |

---

## 7. Interpretation guardrails

- Pilot sample is **not** representative of all open-source repositories.
- Cross-family comparison holds scope mode constant (repo-wide); instruction-specific content-referenced scope is **not** used here.
- Drift/stale-reference findings from misguidance pilots inform qualitative discussion but are not the headline contribution.
- Numeric claims are limited to this pilot until scaled replication is pre-registered.
