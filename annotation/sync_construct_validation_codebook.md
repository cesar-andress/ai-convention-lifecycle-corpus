# Synchronization construct validation — annotation codebook

Codebook for blinded dual-annotator validation of the operational **sync@30** synchronization metric.

**Version:** blinded protocol v1  
**Workbooks:** `sync_construct_validation_blinded_annotator_A.csv`, `sync_construct_validation_blinded_annotator_B.csv`  
**Calibration:** `sync_construct_validation_calibration_units.csv`

---

## 1. Purpose

Determine whether a repository artifact was **semantically synchronized** with a governed code change, independent of the operational metric.

Annotators must **not** inspect metric-derived fields. Those fields are removed from your workbook. Do not open the unblinded source sample (`sync_construct_validation_sample.csv`) during annotation.

The stratified sample balances artifact families and apparent update patterns for **construct coverage**, not population estimation.

---

## 2. Validation unit

Each row is one **governed-code change event** paired with contextual evidence about the anchor artifact (`artifact_path`):

| Field | Meaning |
|-------|---------|
| `governed_code_commit` | Commit that changed governed code paths (repo-wide scope) |
| `artifact_update_commit` | A later commit touching the artifact, if present in the provided context (may be empty) |
| `changed_paths_in_code_commit` | Governed paths changed in the code event |
| `commit_message_*`, `diff_summary_*` | Review aids — inspect local clone if needed |

**Review question:**

> Given the code change and the artifact evidence shown, was the artifact plausibly **semantically synchronized** with that code change?

Semantic synchronization means the artifact content (or justified absence of update) **plausibly reflects** the code change — not merely that files changed in a similar time window.

---

## 3. Primary label — `manual_is_semantically_synchronized`

| Value | Definition |
|-------|------------|
| `TRUE` | The artifact was plausibly synchronized with the code change |
| `FALSE` | The artifact was not plausibly synchronized (stale, unrelated update, or missed required update) |
| `AMBIGUOUS` | Insufficient evidence or genuine expert disagreement after review |

### Positive examples (`TRUE`)

**Substantive sync.** Code commit introduces `src/payments/`; `CLAUDE.md` updated within the shown artifact commit adds payment workflow instructions aligned with the change.

**No sync needed.** Code commit fixes an internal test typo; no artifact update is shown; artifact content clearly unaffected.

**Correct absence.** Code change is purely cosmetic refactoring with no bearing on artifact scope; leaving the artifact unchanged is appropriate.

### Negative examples (`FALSE`)

**Stale, no update.** Code commit removes a documented directory; artifact still references removed paths; no artifact update shown.

**Missed required update.** Public API surface changes; `CONTRIBUTING.md` still describes old contribution flow; no artifact update shown.

**Unrelated co-change.** Artifact commit shown updates unrelated sections (version bump, formatting) while code change requires different content maintenance.

### Boundary cases (`AMBIGUOUS` or split labels)

**Cosmetic artifact update.** Artifact commit only reformats headings while code change altered governed behavior — use `AMBIGUOUS` unless you can confidently judge substantive vs cosmetic.

**Same-commit co-change.** Code and artifact change in the same commit but messages/diffs suggest unrelated edits — often `FALSE` + `unrelated_cochange`, unless content clearly aligns.

**Sparse context.** Commit messages and diff summaries too thin to judge — `AMBIGUOUS` + `insufficient_context`.

---

## 4. Confidence — `manual_confidence`

| Value | When to use |
|-------|-------------|
| `high` | Clear messages/diffs or local inspection confirms judgment |
| `medium` | Reasonable inference with residual uncertainty |
| `low` | Thin evidence; label is tentative |

---

## 5. Reason tag — `manual_reason_tag`

Single best-fit category:

| Tag | Meaning |
|-----|---------|
| `substantive_sync` | Artifact meaningfully updated to reflect the code change |
| `cosmetic_sync` | Artifact touched but change is non-substantive |
| `unrelated_cochange` | Artifact updated but not because of this code event |
| `stale_no_update` | Required update missing or update fails to address the code change |
| `no_sync_needed` | Code change did not require artifact maintenance |
| `insufficient_context` | Cannot judge from provided material |
| `ambiguous` | Mixed signals; see free text |

Use `manual_reason_free_text` for brief evidence (paths, phrases, diff lines).

---

## 6. Decision rules

### No artifact update commit shown

- If code change clearly did **not** require artifact maintenance → `TRUE` + `no_sync_needed`
- If code change **did** require maintenance → `FALSE` + `stale_no_update`
- If unclear → `AMBIGUOUS` + `insufficient_context`

### Artifact update commit shown

- Content plausibly addresses code change → `TRUE` + `substantive_sync`
- Touch is formatting/metadata only → often `FALSE` + `cosmetic_sync` (cosmetic co-change ≠ semantic sync)
- Update exists but unrelated → `FALSE` + `unrelated_cochange`
- Update shown but still stale relative to code change → `FALSE` + `stale_no_update`

### Cosmetic artifact update

Co-change or same-commit touch **does not automatically** imply semantic synchronization. Judge whether content meaningfully reflects the governed code change.

### Same-commit unrelated co-change

When `governed_code_commit` equals `artifact_update_commit` but diffs/messages indicate unrelated edits, prefer `FALSE` + `unrelated_cochange` unless content clearly aligns.

### Insufficient context

Use `AMBIGUOUS` + `insufficient_context` when commit messages and summaries are too sparse. Optionally inspect `data/repos/<owner>/<repo>` locally — do **not** consult metric labels.

---

## 7. Blinding and independence

- Workbooks exclude `metric_sync_30`, `lag_days`, `metric_label`, and stratum fields.
- The presence or absence of `artifact_update_commit` is **observational context**, not a metric label.
- Annotators A and B code **independently** before adjudication.
- Do not use LLM-generated labels as ground truth.

---

## 8. Workflow

1. **Calibration (12–15 units):** Both annotators code `sync_construct_validation_calibration_units.csv`.
2. **Discussion:** Compare disagreements; refine this codebook.
3. **Full annotation:** Code respective blinded workbooks (100 units each).
4. **Agreement:** Facilitator runs `make summarize-sync-agreement`.
5. **Adjudication:** Third reviewer fills `sync_construct_validation_adjudication.csv` for disagreements.
6. **Metric validation:** Run `make summarize-sync-metric-vs-human` (facilitator only; uses unblinded metric column).

---

## 9. Annotator metadata

- `annotator`: pre-filled (`annotator_A` / `annotator_B`) — do not change.
- `annotated_at`: ISO date (`YYYY-MM-DD`) when row completed.
