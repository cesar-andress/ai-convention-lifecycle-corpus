#!/usr/bin/env python3
"""Combine GitHub Actions and prompts/ ablation into pre-submission decision report."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GH_SUMMARY = ROOT / "results/lifecycle_gh_actions/adoption_maintenance_gh_actions.json"
GH_GATE = ROOT / "results/lifecycle_gh_actions/gh_actions_gate_report.json"
PROMPTS_SUMMARY = ROOT / "results/lifecycle_ablation_no_prompts/adoption_maintenance_no_prompts.json"
OUT_MD = ROOT / "results/empirical_additions_pre_submission_report.md"
OUT_JSON = ROOT / "results/empirical_additions_pre_submission_report.json"

CANONICAL_AI = {
    "artifact_gap_pct": 56.0,
    "restricted_repo_gap_pct": 21.4,
    "unguarded_repo_gap_pct": 7.2,
    "maturity_matched_repo_gap_pct": 68.4,
}


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def fmt_ci(point: float | None, lo: float | None, hi: float | None) -> str:
    if point is None:
        return "n/a"
    if lo is None or hi is None:
        return f"{point:.1f}%"
    return f"{point:.1f}% [{lo:.1f}, {hi:.1f}]"


def gh_table_row(summary: dict) -> dict:
    h = summary["headline_primary_180"]
    b = summary["bootstrap"]["180"]
    art = b["artifact_gap_mature"]
    rest = b["repo_gap_restricted"]
    repo = b["repo_gap"]
    return {
        "family": "GitHub Actions (root .github/workflows/)",
        "repos_adopted": h["n_repos_adopted_head"],
        "repos_mature_present": h["n_repos_with_mature_present"],
        "mature_present_paths": h["n_mature_present_paths"],
        "median_paths": h["median_paths_per_adopted_repo"],
        "max_paths": h.get("max_paths_per_adopted_repo"),
        "artifact_gap": fmt_ci(
            art["observed"] * 100,
            art["gap_ci_95"]["low"] * 100,
            art["gap_ci_95"]["high"] * 100,
        ),
        "restricted_gap": fmt_ci(
            rest["observed"] * 100,
            rest["ci_95"]["low"] * 100,
            rest["ci_95"]["high"] * 100,
        ),
        "unguarded_gap": fmt_ci(
            repo["observed"] * 100,
            repo["ci_95"]["low"] * 100,
            repo["ci_95"]["high"] * 100,
        ),
        "maturity_matched_gap": f"{h['repo_gap_maturity_matched_unrestricted']*100:.1f}%",
        "loo_artifact": summary.get("loo_max_abs_delta_artifact_gap"),
        "loo_restricted": summary.get("loo_max_abs_delta_repo_gap_restricted"),
        "loo_unguarded": summary.get("loo_max_abs_delta_repo_gap_unguarded"),
    }


def ai_row(label: str, h: dict, boot: dict | None) -> dict:
    row = {
        "family": label,
        "repos_adopted": h["n_repos_adopted_head"],
        "repos_mature_present": h["n_repos_with_mature_present"],
        "mature_present_paths": h["n_mature_present_paths"],
        "median_paths": h.get("median_paths_per_adopted_repo"),
        "max_paths": h.get("max_paths_per_adopted_repo"),
        "artifact_gap": f"{h['artifact_gap_mature']*100:.1f}%",
        "restricted_gap": f"{h['repo_gap_restricted']*100:.1f}%",
        "unguarded_gap": f"{h['repo_gap_unguarded']*100:.1f}%",
        "maturity_matched_gap": f"{h['repo_gap_maturity_matched_unrestricted']*100:.1f}%",
        "loo_artifact": None,
        "loo_restricted": None,
        "loo_unguarded": None,
    }
    if boot:
        b = boot["180"]
        art = b["artifact_gap_mature"]
        rest = b["repo_gap_restricted"]
        repo = b["repo_gap"]
        row["artifact_gap"] = fmt_ci(
            art["observed"] * 100, art["gap_ci_95"]["low"] * 100, art["gap_ci_95"]["high"] * 100
        )
        row["restricted_gap"] = fmt_ci(
            rest["observed"] * 100, rest["ci_95"]["low"] * 100, rest["ci_95"]["high"] * 100
        )
        row["unguarded_gap"] = fmt_ci(
            repo["observed"] * 100, repo["ci_95"]["low"] * 100, repo["ci_95"]["high"] * 100
        )
    return row


def final_recommendation(gh_gate: dict | None, prompts_decision: dict | None) -> str:
    gh_ok = gh_gate and gh_gate.get("passed")
    prompts_ok = prompts_decision and prompts_decision.get("recommendation") in (
        "INTEGRATE_AS_ROBUSTNESS_ROW",
        "INTEGRATE_WITH_CAVEAT",
    )
    if gh_ok and prompts_ok:
        return "integrate_both"
    if gh_ok:
        return "integrate_only_github_actions"
    if prompts_ok:
        return "integrate_only_prompts_ablation"
    return "integrate_neither_submit_current_manuscript"


def render_md(payload: dict) -> str:
    lines = [
        "# Empirical additions pre-submission decision report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## 1. GitHub Actions headline table",
        "",
        "| Metric | Value |",
        "|--------|------:|",
    ]
    if payload.get("github_actions"):
        g = payload["github_actions"]
        for k, v in g.items():
            lines.append(f"| {k} | {v} |")
    else:
        lines.append("| status | **PENDING — pipeline incomplete** |")

    lines.extend(
        [
            "",
            "## 2. AI full detector vs AI without prompts/",
            "",
            "| Variant | Mature paths | Artifact gap | Restricted repo gap | Unguarded repo gap | Maturity-matched |",
            "|---------|-------------:|-------------|--------------------:|-------------------:|-----------------:|",
        ]
    )
    for row in payload.get("ai_comparison_rows", []):
        lines.append(
            f"| {row['family']} | {row['mature_present_paths']} | {row['artifact_gap']} | "
            f"{row['restricted_gap']} | {row['unguarded_gap']} | {row['maturity_matched_gap']} |"
        )

    lines.extend(["", "## 3. GitHub Actions gate", ""])
    if payload.get("github_actions_gate"):
        gate = payload["github_actions_gate"]
        lines.append(f"- **Passed:** {gate['passed']}")
        lines.append(f"- **Recommendation:** {gate['recommendation']}")
        for k, v in gate.get("checks", {}).items():
            lines.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    else:
        lines.append("- **Status:** not yet evaluated")

    lines.extend(["", "## 4. Integrate GitHub Actions?", ""])
    lines.append(payload.get("integrate_github_actions_rationale", "Pending."))

    lines.extend(["", "## 5. Integrate prompts/ ablation?", ""])
    lines.append(payload.get("integrate_prompts_rationale", "Pending."))

    lines.extend(["", "## 6. Risks", ""])
    for r in payload.get("risks", []):
        lines.append(f"- {r}")

    lines.extend(
        [
            "",
            "## 7. Estimated manuscript page impact",
            "",
            payload.get("page_impact", "TBD"),
            "",
            "## 8. Final recommendation",
            "",
            f"**{payload['final_recommendation']}**",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    gh = load_json(GH_SUMMARY)
    gh_gate = load_json(GH_GATE)
    prompts = load_json(PROMPTS_SUMMARY)

    missing = []
    if not gh:
        missing.append("GitHub Actions summary")
    if not gh_gate:
        missing.append("GitHub Actions gate")
    if not prompts:
        missing.append("prompts ablation summary")

    ai_rows = []
    if prompts:
        ai_rows.append(
            ai_row(
                "AI conventions (full detector)",
                prompts["headline_full_detector_reference"],
                None,
            )
        )
        ai_rows.append(
            ai_row(
                "AI conventions (no prompts/)",
                prompts["headline_primary_180"],
                prompts.get("bootstrap"),
            )
        )
        for k, v in prompts["loo"].items() if False else []:
            pass
        ai_rows[-1]["loo_artifact"] = prompts.get("loo_max_abs_delta_artifact_gap")
        ai_rows[-1]["loo_restricted"] = prompts.get("loo_max_abs_delta_repo_gap_restricted")
        ai_rows[-1]["loo_unguarded"] = prompts.get("loo_max_abs_delta_repo_gap_unguarded")

    gh_row = gh_table_row(gh) if gh else None

    integrate_gh = (
        "Yes — gate passed; second family exercises the protocol on configuration artifacts "
        "without altering AI headline values."
        if gh_gate and gh_gate.get("passed")
        else "No — gate failed or pipeline incomplete; keep as future work."
    )
    prompts_dec = prompts.get("decision") if prompts else None
    integrate_prompts = (
        f"{prompts_dec['recommendation']}: artifact–restricted spread "
        f"{prompts_dec['ablated_artifact_minus_restricted_pp']} pp "
        f"({prompts_dec['spread_retained_pct']}% of full {prompts_dec['full_artifact_minus_restricted_pp']} pp retained)."
        if prompts_dec
        else "Pending ablation run."
    )

    risks = [
        "GitHub Actions: high per-repo workflow multiplicity may widen artifact CIs and increase runtime.",
        "GitHub Actions: cohort was selected for AI conventions, not CI prevalence.",
        "Prompts ablation: skill_md concentration remains even after prompts/ removal.",
        "Either addition increases Results/Discussion length and reviewer surface area.",
    ]

    page_impact = (
        "GitHub Actions subsection + comparison table: ~0.5–0.75 pages. "
        "Prompts ablation robustness row: ~0.15–0.25 pages. "
        "Combined upper bound ~1 page."
    )

    rec = final_recommendation(gh_gate, prompts_dec)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "canonical_ai_headlines_unchanged": CANONICAL_AI,
        "missing_artifacts": missing,
        "github_actions": gh_row,
        "github_actions_gate": gh_gate,
        "ai_comparison_rows": ai_rows,
        "integrate_github_actions_rationale": integrate_gh,
        "integrate_prompts_rationale": integrate_prompts,
        "prompts_ablation_decision": prompts_dec,
        "risks": risks,
        "page_impact": page_impact,
        "final_recommendation": rec,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    OUT_MD.write_text(render_md(payload))
    print(f"Wrote {OUT_MD}")
    if missing:
        print(f"WARNING: missing {missing}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
