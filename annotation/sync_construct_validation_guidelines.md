# Synchronization construct validation — annotation guidelines

Manual construct validation for the operational **sync@30** metric used in the synchronization-spectrum pilot.

**Goal:** determine whether a metric-defined synchronization event corresponds to human judgment that the artifact was plausibly synchronized with the governed code change.

This is **not** stale-reference auditing and **not** parser validation.

---

## 1. Validation unit

Each row is one **governed-code change event** paired with the nearest artifact update within **W=30 days** (if any).

| Field | Meaning |
|-------|---------|
| `governed_code_commit` | Commit that changed ≥1 repo-wide governed code path (excluding the artifact itself) |
| `artifact_path` | Anchor file for the artifact family in this repository |
| `artifact_update_commit` | Nearest commit touching `artifact_path` within 30 days after the code event (empty if none) |
| `metric_sync_30` | Operational label: `True` if an in-window artifact update exists, else `False` |
| `metric_label` | `synchronized` or `not_synchronized` (same as `metric_sync_30`) |
| `scope_mode` | Always `repo_wide` for this validation package |

Review question:

> **Was the artifact plausibly synchronized with the code change?**

Use commit messages, changed-file lists, and diff summaries provided in the row. Inspect the repository locally if needed (`data/repos/<owner>/<repo>`).

---

## 2. Manual fields

Fill only these columns in `annotation/sync_construct_validation_sample.csv`:

### `manual_is_semantically_synchronized`

| Value | Use when |
|-------|----------|
| `TRUE` | The artifact update (or justified absence) plausibly reflects the code change |
| `FALSE` | The metric and human judgment disagree on synchronization |
| `AMBIGUOUS` | Insufficient context, mixed signals, or domain expertise required |

### `manual_confidence`

| Value | Use when |
|-------|----------|
| `high` | Clear evidence from messages/diffs |
| `medium` | Reasonable inference with some uncertainty |
| `low` | Thin evidence; label is tentative |

### `manual_sync_type`

| Value | Definition |
|-------|------------|
| `substantive_sync` | Artifact content meaningfully updated to match the code change |
| `cosmetic_sync` | Artifact touched but change is formatting, metadata, or non-substantive |
| `unrelated_cochange` | Artifact updated in window but change unrelated to the code event |
| `stale_no_update` | Code change required artifact update; none occurred (or update missed the point) |
| `no_sync_needed` | Code change did not require artifact update; absence is correct |
| `ambiguous` | Cannot classify sync type confidently |

### `manual_reason`

Free-text justification (1–3 sentences). Cite specific paths, message phrases, or diff evidence.

### `annotator` / `annotated_at`

Your identifier and ISO date (`YYYY-MM-DD`).

---

## 3. Decision rules

### When `metric_sync_30 = True` (synchronized)

The metric found an artifact update within 30 days.

- Label `TRUE` + `substantive_sync` when the update plausibly addresses the code change.
- Label `TRUE` + `cosmetic_sync` when the artifact was touched but only cosmetically.
- Label `FALSE` + `unrelated_cochange` when the artifact changed but not because of this code event.
- Label `FALSE` + `stale_no_update` when the update exists but misses required content (e.g., paths still wrong).

### When `metric_sync_30 = False` (not_synchronized)

No artifact update within 30 days.

- Label `TRUE` + `no_sync_needed` when the code change clearly did not require artifact maintenance.
- Label `FALSE` + `stale_no_update` when the artifact should have been updated but was not.
- Label `AMBIGUOUS` when you cannot tell whether an update was needed.

---

## 4. Examples (illustrative)

### Example A — TRUE substantive sync

- Code commit adds `src/payments/` module; `CLAUDE.md` updated within 5 days adding payment development instructions.
- `manual_is_semantically_synchronized`: `TRUE`
- `manual_sync_type`: `substantive_sync`

### Example B — FALSE unrelated cochange

- Code commit refactors internal tests; `package.json` version bump in same week unrelated to dependency structure.
- Metric: synchronized (`metric_sync_30=True`)
- `manual_is_semantically_synchronized`: `FALSE`
- `manual_sync_type`: `unrelated_cochange`

### Example C — FALSE stale no update

- Code commit removes `docs/api/` tree; `AGENTS.md` still references removed paths; no artifact update within 30 days.
- Metric: not synchronized
- `manual_is_semantically_synchronized`: `FALSE`
- `manual_sync_type`: `stale_no_update`

### Example D — TRUE no sync needed

- Code commit fixes typo in unit test; no instruction-file update.
- Metric: not synchronized
- `manual_is_semantically_synchronized`: `TRUE`
- `manual_sync_type`: `no_sync_needed`

---

## 5. Workflow

1. Run `make prepare-sync-validation` (once) to generate the sample.
2. Annotate `annotation/sync_construct_validation_sample.csv`.
3. Run `make summarize-sync-validation` after annotation batches.
4. Do **not** auto-fill manual labels; do **not** edit generated review columns.

---

## 6. Inter-rater note

If multiple annotators participate, use separate workbook copies or add an `annotator` column consistently. Summaries aggregate all filled rows.
