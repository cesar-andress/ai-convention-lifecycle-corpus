# Research plan — temporal co-update as biased proxy for semantic synchronization

## Final title

**Temporal Co-Update Is a Biased Proxy for Semantic Synchronization: A Validated Measurement Study of Code-Governing Artifacts**

## Target journal

- **Primary:** Empirical Software Engineering (EMSE)
- **Fallback:** Information and Software Technology (IST)

## Core claim

Temporal co-update metrics (e.g., sync@N) are **operationally useful but construct-invalid** as direct measures of semantic synchronization between governing artifacts and repository evolution. The bias is **structured and diagnosable**: proxy agreement with maintainer judgment depends on case difficulty, scope orthogonality, and artifact family—not on a single prevalence rate in a convenience sample.

## Non-claims

- We do **not** claim population prevalence of synchronization or drift across open source.
- We do **not** claim sync@N measures semantic truth.
- We do **not** claim AI instruction files are universally stale or synchronized.
- We do **not** claim the 25-repository cohort is representative of all repositories with AI conventions.
- We do **not** optimize the proxy (sync@30) for higher agreement.
- We do **not** claim instruction-file path-reference drift as the headline contribution.

## Research questions

**RQ1.** To what extent does temporal co-update (sync@N) agree with maintainer-judged semantic synchronization, and how does agreement differ between boundary cases and easy cases?

**RQ2.** Is disagreement between proxy and human judgment structured by change-scope orthogonality?

**RQ3.** What information is required to determine semantic synchronization, and are code-side co-change signals alone sufficient?

**RQ4.** What recurring modes of synchronization and desynchronization arise between governing artifacts and repository evolution?

## Contribution statement

We provide a **validated measurement study** showing that sync@N is a biased proxy for semantic synchronization among code-governing artifacts (AI instructions, configuration, documentation). Using a purposive 25-repository measurement cohort and a blinded boundary-case validation subsample, we:

1. Specify semantic synchronization as a maintainer-judgment construct distinct from temporal co-update.
2. Demonstrate structured proxy–human disagreement modes (false sync, false desync, genesis confusion, scope orthogonality).
3. Show that code-side co-change signals alone are often insufficient for semantic judgment.
4. Explain why instruction artifacts expose proxy weakness sharply (agent-consumed, weakly enforced).

The contribution is **measurement validity**, not prevalence estimation.

## Minimal viable acceptance package (EMSE)

| Component | Status / deliverable |
|-----------|---------------------|
| Construct definition + codebook v3 | `annotation/sync_semantic_codebook_v3.md` |
| Purposive cohort description (n=25) | Spectrum pilot + design docs |
| Boundary validation subsample (n=20) | `boundary20_*` annotation package |
| ≥2 independent annotators + adjudication | A/B/C workbooks + adjudication sheet |
| Proxy–human confusion analysis | `summarize_boundary20_metric_vs_human.py` |
| Structured failure-mode taxonomy | Reason tags + qualitative examples |
| Threat model + limitations | This document |

## Ideal acceptance package

| Component | Enhancement |
|-----------|-------------|
| Third annotator + adjudicator | Reduces dyadic bias |
| Artifact content at governed commit | Reduces insufficient-context rate |
| Scope-orthogonality coding on boundary20 | Direct RQ2 evidence |
| Negative examples with screenshots/diffs | Reviewer-facing appendix |
| Replication note on one alternate window (sync@7) | Sensitivity without new metric family |
| Qualitative synthesis of disagreement modes | Thematic table for RQ4 |

## Kill list (out of scope for this paper)

- Scaling to 200+ repositories for prevalence claims
- New parsers, scope modes, or extraction rules
- Improving sync@30 to maximize human agreement
- Headline stale-reference counts or misguidance rates
- Population inference from stratified pilot samples
- Competing sync metric leaderboard
- LLM-as-judge ground truth
- Framing instruction files as “worse README” without validity argument

## Threat model

| Threat | Mitigation |
|--------|------------|
| **Construct under-specification** | Codebook v3 with explicit TRUE/FALSE/AMBIGUOUS rules; boundary-case purposive sample |
| **Circular validation** | Blinded workbooks; ledger with metric labels researcher-only; reject preannotation mirroring metric |
| **Annotator blindness failure** | Remove lag, metric label, artifact-update commits from annotator CSVs |
| **Low inter-rater agreement** | Expected on boundary cases; adjudication; report κ and failure modes, not only accuracy |
| **Convenience cohort** | Frame as purposive measurement cohort; no prevalence claims |
| **Repo-wide scope inflation** | Discuss scope orthogonality as structured false-desync source (RQ2) |
| **Insufficient context** | Artifact contents at governed commit; AMBIGUOUS rate reported |
| **Single-window arbitrariness** | Acknowledge N=30 as operational; boundary lag cases included |
| **Instruction-file salience** | Treat as sharp probe of proxy limits, not universal law |
| **Genesis mistaken for resync** | Explicit codebook rule; select genesis/boundary units |
| **Same-commit unrelated co-change** | Explicit codebook rule; select same-commit units |
| **Version-bump false sync** | Explicit codebook rule; select release/version units |

## Stop condition

The paper is complete when we can answer RQ1–RQ4 with **validated boundary-case evidence** and a clear statement of **where and why** sync@N fails as a semantic proxy—without scaling the corpus for prevalence.
