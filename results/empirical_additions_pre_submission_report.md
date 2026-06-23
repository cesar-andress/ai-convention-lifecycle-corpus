# Empirical additions pre-submission decision report

Generated: 2026-06-18T05:34:54.332145+00:00

## 1. GitHub Actions headline table

| Metric | Value |
|--------|------:|
| family | GitHub Actions (root .github/workflows/) |
| repos_adopted | 186 |
| repos_mature_present | 155 |
| mature_present_paths | 2175 |
| median_paths | 10.5 |
| max_paths | 335 |
| artifact_gap | 7.6% [4.8, 11.5] |
| restricted_gap | 2.6% [1.0, 4.3] |
| unguarded_gap | 1.6% [0.0, 2.7] |
| maturity_matched_gap | 18.8% |
| loo_artifact | 0.01267676862275001 |
| loo_restricted | 0.006325932132383746 |
| loo_unguarded | 0.005318221447253704 |

## 2. AI full detector vs AI without prompts/

| Variant | Mature paths | Artifact gap | Restricted repo gap | Unguarded repo gap | Maturity-matched |
|---------|-------------:|-------------|--------------------:|-------------------:|-----------------:|
| AI conventions (full detector) | 577 | 56.0% | 21.4% | 7.2% | 68.4% |
| AI conventions (no prompts/) | 323 | 28.5% [13.8, 48.3] | 17.3% [10.4, 23.8] | 5.0% [2.4, 7.1] | 69.3% |

## 3. GitHub Actions gate

- **Passed:** True
- **Recommendation:** PROCEED
- adopted_repos_ge_80: PASS
- restricted_repos_ge_40: PASS
- mature_present_paths_ge_150: PASS
- concentration_below_50pct: PASS
- artifact_bootstrap_present: PASS
- restricted_bootstrap_present: PASS
- unguarded_bootstrap_present: PASS

## 4. Integrate GitHub Actions?

Yes — gate passed; second family exercises the protocol on configuration artifacts without altering AI headline values.

## 5. Integrate prompts/ ablation?

INTEGRATE_WITH_CAVEAT: artifact–restricted spread 11.1 pp (32.3% of full 34.6 pp retained).

## 6. Risks

- GitHub Actions: high per-repo workflow multiplicity may widen artifact CIs and increase runtime.
- GitHub Actions: cohort was selected for AI conventions, not CI prevalence.
- Prompts ablation: skill_md concentration remains even after prompts/ removal.
- Either addition increases Results/Discussion length and reviewer surface area.

## 7. Estimated manuscript page impact

GitHub Actions subsection + comparison table: ~0.5–0.75 pages. Prompts ablation robustness row: ~0.15–0.25 pages. Combined upper bound ~1 page.

## 8. Final recommendation

**integrate_both**
