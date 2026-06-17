# Semantic synchronization — annotation codebook v3

**Version:** v3 (boundary20 / EMSE measurement-validity study)  
**Workbooks:** `boundary20_annotator_A.csv`, `boundary20_annotator_B.csv`, `boundary20_annotator_C.csv`  
**Researcher ledger (do not use during annotation):** `results/synchronization_validation/boundary20_selection_ledger.csv`

---

## 1. Purpose

This codebook defines **semantic synchronization** as a maintainer-judgment construct, distinct from temporal co-update (sync@N). Annotators judge whether an artifact remained aligned with a **specific governed code change**, using only the evidence provided in the blinded workbook.

**Do not** consult metric labels, lag values, artifact-update commits/dates, or any field indicating whether sync@30 classified the unit as synchronized. Do not open the selection ledger during annotation.

---

## 2. Construct

> **Would a reasonable maintainer conclude that the artifact remained semantically synchronized with the governed code evolution?**

Semantic synchronization means the artifact’s guidance, configuration, or documentation **still correctly reflects** the repository state **relevant to the governed change**—not merely that the artifact file was touched near the code change in time.

Each row is one **validation unit**: a governed code commit paired with artifact context at that commit (and review aids). You judge alignment **at the time of the governed change**, not future fixes.

---

## 3. Primary label — `manual_is_semantically_synchronized`

| Value | Decision rule |
|-------|----------------|
| `TRUE` | **Positive evidence** that the artifact remains aligned with the governed code change. |
| `FALSE` | **Positive evidence** that the artifact is outdated, contradicted, or missing guidance that should have changed. |
| `AMBIGUOUS` | **Insufficient evidence.** Neither absence of update alone nor absence of visible contradiction alone is enough. |

### Critical non-rules

- **No artifact update alone is not `FALSE`.** A missing update is not automatic desynchronization.
- **No visible contradiction alone is not `TRUE`.** Lack of an obvious stale passage does not prove alignment.
- **Artifact creation inside the observation window is not automatically synchronization.** Genesis may be initial placement, not resync with the governed change.
- **Version bumps are not automatically synchronization.** Lockfile or version churn may be release hygiene unrelated to the governed code change.
- **Same-commit co-change can be unrelated.** Touching the artifact in the same commit as code does not imply semantic alignment.
- **Template files may not govern the repository itself.** Generic boilerplate may not encode project-specific truth.
- **Code-side co-change signals alone are often insufficient.** You may need artifact content, commit messages, and changed paths together.

---

## 4. Confidence — `manual_confidence`

| Value | When to use |
|-------|-------------|
| `high` | Clear positive or negative evidence after review. |
| `medium` | Reasonable judgment with some residual uncertainty. |
| `low` | Thin context; label is best guess rather than firm conclusion. |

Prefer `AMBIGUOUS` over a low-confidence decisive label when evidence is genuinely inadequate.

---

## 5. Reason tags — `manual_reason_tag`

| Tag | Meaning |
|-----|---------|
| `substantive_sync` | Artifact content aligns with or appropriately reflects the governed change. |
| `no_sync_needed` | Governed change does not require artifact update; artifact still valid. |
| `stale_missing_update` | Artifact should have been updated but was not (or update not shown). |
| `stale_contradiction` | Artifact content contradicts the post-change repository state. |
| `coincidental_update` | Artifact was updated, but not in semantic response to the governed change. |
| `artifact_genesis_not_resync` | Artifact appeared recently but this is not evidence of resynchronization with this code change. |
| `unrelated_cochange` | Co-temporal or same-commit artifact touch is unrelated to governed code semantics. |
| `insufficient_context` | Cannot judge; missing artifact body, paths, or scope information. |
| `ambiguous` | Genuine expert uncertainty after review. |

Use exactly one primary tag. Add nuance in `manual_reason_free_text` if needed.

---

## 6. Annotation workflow

1. Read `governed_code_commit_message`, `changed_paths_in_governed_commit`, and `governed_commit_diff_summary`.
2. Read `artifact_contents_at_governed_commit` or `artifact_excerpt` when present.
3. Note `context_availability_notes` for missing content.
4. Apply the construct question and decision rules above.
5. Set label, confidence, reason tag, and brief free-text justification.
6. Fill `annotator` and `annotated_at` (ISO-8601).

If local clone review is needed, use only information that would be available to a maintainer at the governed commit—**not** subsequent artifact history or metric outputs.

---

## 7. Adjudication

When annotators A, B, and C disagree, an adjudicator resolves the unit using the same construct and codebook. Adjudicated labels feed proxy–human comparison; unresolved disagreements are reported separately.

---

## 8. What this study does not claim

- Population prevalence of synchronization or drift.
- That sync@30 measures semantic truth.
- That higher inter-annotator agreement is the success criterion.

The goal is to document **where** temporal co-update agrees and disagrees with maintainer-judged semantic synchronization on **high-information boundary cases**.
