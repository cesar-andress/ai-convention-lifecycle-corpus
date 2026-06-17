# Drift candidate audit report (qualitative)

Generated: `2026-06-16T23:29:13.987507+00:00`

**Pilot subset only — no population claims.**

Candidates (historical_existence=`existed_before`): **38**

## 1. Which repositories contribute most candidates?

- `payloadcms/payload`: **17**
- `apache/airflow`: **11**
- `cheat/cheat`: **2**
- `electron/electron`: **2**
- `dagster-io/dagster`: **2**
- `grafana/grafana`: **2**
- `BerriAI/litellm`: **1**
- `prefecthq/prefect`: **1**

## 2. Which categories dominate?

- `unknown`: 17
- `deleted_directory`: 8
- `source_code_reference`: 6
- `config_reference`: 4
- `documentation_reference`: 3

## 3. How many appear likely to be real drift? (heuristic pre-assessment only)

Manual columns in `drift_candidate_review.csv` are empty — these are **not** validated labels.

- heuristic `no`: 23
- heuristic `yes`: 15

## 4. How many appear to be parser artifacts? (heuristic pre-assessment only)

- heuristic `no`: 23
- heuristic `yes`: 12
- heuristic `maybe`: 3

## 5. Strong enough for a full-corpus study?

- Reliable git history rows: **15/38**
- Heuristic `yes` drift: **15**
- Heuristic `yes` artifact: **12**

Qualitative conclusion: complete manual review of `drift_candidate_review.csv` before deciding on full-corpus collection. If manual review confirms even a modest subset of the **38** candidates as plausible drift, the phenomenon warrants a bounded scale-up; otherwise refine extraction/history rules first.

## Historical context summary

- Median path lifetime (days, where computed): 8

## Next steps

1. Fill `drift_candidate_review.csv` (`appears_to_be_real_drift`, `appears_to_be_false_positive`, `reference_still_meaningful`, `notes`).
2. Re-run summarizer after review (future target).
3. Only then decide on full-corpus misguidance collection.
