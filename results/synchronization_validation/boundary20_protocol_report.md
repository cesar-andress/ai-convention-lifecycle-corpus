# Boundary20 protocol report

**Study:** Temporal Co-Update Is a Biased Proxy for Semantic Synchronization  
**Package:** purposive boundary-case validation subsample (n=20)  
**Generated:** see `boundary20_meta.json` after running `make prepare-boundary20-validation`

---

## 1. Why the previous 100-unit validation was circular

The initial construct-validation frame (`sync_construct_validation_sample.csv`, n=100) was stratified from the same operational pipeline that defines sync@N. Annotator A was pre-filled using a mechanical rule aligned with `metric_sync_30`. That design confounds **proxy validity** with **proxy reproduction**:

- High agreement between A and the metric does not validate semantic synchronization; it restates the operational definition.
- Disagreement between A and B (48% raw agreement in the pilot annotation pass) suggests criterion divergence, but the frame still mixes easy metric-positive cases with boundary cases without purposive selection.
- Fields such as `artifact_update_commit`, `artifact_update_date`, and implicit knowledge of the 30-day window leak the proxy into annotator context.

The 100-unit frame remains useful as a **pool** for coverage and calibration. It is not the primary evidentiary package for an EMSE measurement-validity claim.

---

## 2. Why boundary20 is purposive, not prevalence-oriented

The 25-repository synchronization-spectrum cohort is a **purposive measurement cohort**: repositories and artifact families were chosen to probe co-update behavior across instructions, documentation, and configuration—not to estimate population prevalence.

Boundary20 applies the same logic at the **validation-unit** level:

| Design choice | Rationale |
|---------------|-----------|
| n=20, not n=100+ | Depth over breadth; qualitative failure-mode evidence |
| Prioritize A/B disagreements from parent frame | Targets cases where human criteria already diverged |
| Prioritize instruction files, genesis, same-commit, version bumps, boundary lag | Structured bias modes named in the thesis |
| Researcher-only ledger with metric fields | Separates measurement instrument from blinded judgment |
| No scaling to 200+ repos | Stop condition: validity, not prevalence |

We do **not** report boundary20 counts as estimates of how often open-source artifacts are synchronized.

---

## 3. Fields hidden from annotators

Blinded workbooks (`boundary20_annotator_A.csv`, `_B.csv`, `_C.csv`) **exclude**:

- `metric_label`, `metric_sync_30`, `lag_days`
- `artifact_update_commit`, `artifact_update_date`
- Any column that reveals whether sync@30 classified the unit as synchronized
- Selection metadata (`selection_reason`, `expected_failure_mode`, `why_high_information`)

Annotators **receive**:

- Unit identity and artifact location (`unit_id`, `repo_id`, `artifact_family`, `artifact_path`)
- Governed code event context (commit, message, changed paths, diff summary)
- Artifact contents at the governed commit when extractable via `git show`
- `context_availability_notes` documenting missing or partial context

Manual columns follow codebook v3 (`annotation/sync_semantic_codebook_v3.md`).

---

## 4. How the 20 units were selected

Selection script: `scripts/synchronization/prepare_boundary20_validation.py`  
Scoring logic: `scripts/synchronization/boundary20.py`

**Pool:** 100 validation units from `annotation/sync_construct_validation_sample.csv`.

**Priority signals** (non-exhaustive):

1. **A/B disagreement** — units where prior blinded annotators A and B disagreed on semantic synchronization.
2. **Instruction artifacts** — agent-consumed, weakly enforced governance files.
3. **Same-commit co-change** — artifact and code touched in one commit (possible unrelated co-change).
4. **Version bump / release-only edits** — heuristic on commit message and artifact diff text.
5. **Boundary lag (25–30 days)** — sensitivity to the operational window cutoff.
6. **No artifact update** — stale vs no-sync-needed ambiguity, by family.
7. **Nested instruction paths** and **large monorepos** — scope-orthogonality noise.

**Diversification constraints:**

- At least one unit per artifact family (instructions, documentation, configuration).
- Coverage of key selection reasons before filling by priority score.

**Researcher-only ledger:** `results/synchronization_validation/boundary20_selection_ledger.csv` records `metric_label`, `metric_sync_30`, `lag_days`, `selection_reason`, `expected_failure_mode`, and `why_high_information` for each unit.

---

## 5. How the codebook addresses semantic synchronization

Codebook v3 (`annotation/sync_semantic_codebook_v3.md`) defines the construct as maintainer judgment:

> Would a reasonable maintainer conclude that the artifact remained semantically synchronized with the governed code evolution?

Decision rules explicitly reject shortcuts that mirror temporal co-update:

- Absence of update ≠ FALSE; absence of contradiction ≠ TRUE.
- Genesis, version bumps, and same-commit touches are not automatic TRUE.
- Template or generic instruction content may not govern the repository.
- Code-side co-change signals alone are often insufficient.

Reason tags (`substantive_sync`, `no_sync_needed`, `stale_missing_update`, `coincidental_update`, `artifact_genesis_not_resync`, `unrelated_cochange`, etc.) support structured disagreement analysis (RQ2, RQ4).

---

## 6. Annotation and analysis workflow

| Step | Command / artifact |
|------|-------------------|
| Generate package | `make prepare-boundary20-validation` |
| Annotate (3 raters) | `boundary20_annotator_{A,B,C}.csv` |
| Inter-rater agreement | `make summarize-boundary20-agreement` |
| Adjudicate disagreements | `annotation/boundary20_adjudication.csv` |
| Proxy vs human | `make summarize-boundary20-metric-vs-human` |

`summarize_boundary20_agreement.py` reports raw agreement, pairwise Cohen κ, Fleiss κ, Krippendorff α (nominal), AMBIGUOUS rate, agreement by artifact family, and a disagreement table.

`summarize_boundary20_metric_vs_human.py` compares ledger `metric_sync_30` to adjudicated/consensus human labels: confusion matrix, precision, recall, specificity, F1, agreement excluding AMBIGUOUS, AMBIGUOUS sensitivity bounds, and exemplar false-sync / false-desync cases.

---

## 7. Why this supports an EMSE measurement-validity paper

Empirical Software Engineering expects explicit construct definition, transparent measurement threats, and evidence about **what a metric actually measures**. This package delivers:

1. **Construct separation** — semantic synchronization (maintainer judgment) vs temporal co-update (sync@N).
2. **Blinded criterion validation** — annotators cannot see proxy outputs.
3. **Purposive boundary cases** — disagreement modes are diagnosable, not averaged away.
4. **Structured failure taxonomy** — reason tags map to thesis biases (false sync, false desync, scope orthogonality, genesis confusion).
5. **Honest stop condition** — 25 repos, 20 validation units; no prevalence claims.

The contribution is not “X% of repositories are synchronized.” It is: **sync@N is a biased proxy whose errors are structured and predictable**—and therefore unsafe as a direct measure of semantic truth without boundary-aware interpretation.

---

## 8. Related documents

- `paper_sync_validity/research_plan.md` — title, RQs, claims, kill list, threat model
- `annotation/sync_semantic_codebook_v3.md` — annotator instructions
- `docs/synchronization_spectrum_design.md` — purposive 25-repo cohort design
- `results/synchronization_validation/boundary20_selection_ledger.csv` — researcher-only unit metadata
