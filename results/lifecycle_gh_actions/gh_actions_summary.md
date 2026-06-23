# GitHub Actions family summary (gh_actions_v1)

Generated: 2026-06-18T05:26:53.876020+00:00

## Primary panel (root `.github/workflows/`, example paths excluded)

- Repos adopted (HEAD): **186**
- Repos with ≥1 mature-present workflow: **155**
- Mature-present workflow paths: **2175**
- Median workflows per adopted repo: **10.5**
- Artifact gap @ T=180: **7.6%** CI [4.8, 11.5]
- Restricted repo gap: **2.6%** CI [1.0, 4.3]
- Unguarded repo gap: **1.6%** CI [0.0, 2.7]
- Maturity-matched unrestricted repo gap: **18.8%**
- LOO max |Δ| artifact / unguarded / restricted: **0.013 / 0.005 / 0.006**

## Gate decision

- **PROCEED**

- adopted_repos_ge_80: PASS
- restricted_repos_ge_40: PASS
- mature_present_paths_ge_150: PASS
- concentration_below_50pct: PASS
- artifact_bootstrap_present: PASS
- restricted_bootstrap_present: PASS
- unguarded_bootstrap_present: PASS
- Top-repo concentration: `apache/beam` (15.4% of mature-present paths)
