#!/usr/bin/env python3
"""Recompute headline gaps by repository typology and restricted repository estimand."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.adoption_maintenance import gap_artifact_mature, gap_repo_level, gap_repo_restricted
from lifecycle.corpus_paths import configure

ROOT = configure()

T_PRIMARY = 180

GROUP_SPECS = [
    ("all_repositories", lambda t: t["repo_id"].notna()),
    ("codebase_only", lambda t: t["repo_type"] == "codebase"),
    ("collection_or_list_only", lambda t: t["repo_type"] == "collection_or_list"),
    ("excluding_collection_or_list", lambda t: t["repo_type"] != "collection_or_list"),
    ("unclear_only", lambda t: t["repo_type"] == "unclear"),
]


def compute_group_gaps(df: pd.DataFrame, repo_ids: set[str], t: int) -> dict:
    sub = df[df["repo_id"].isin(repo_ids)]
    art = gap_artifact_mature(sub, t)
    repo = gap_repo_level(sub, t)
    restricted = gap_repo_restricted(sub, t)
    n_repos_analyzed = sub["repo_id"].nunique()
    return {
        "T": t,
        "n_repos_analyzed": int(n_repos_analyzed),
        "n_ever_introduced_paths": int(len(sub)),
        "artifact_gap": art["gap_rate"],
        "artifact_gap_pct": round(art["gap_rate"] * 100, 1) if art["gap_rate"] is not None else None,
        "n_mature_present_artifacts": art["n_mature_present"],
        "repository_gap_original": repo["gap_rate"],
        "repository_gap_original_pct": round(repo["gap_rate"] * 100, 1) if repo["gap_rate"] is not None else None,
        "n_repos_adopted_denominator": repo["n_repos_adopted"],
        "repository_gap_restricted": restricted["gap_rate"],
        "repository_gap_restricted_pct": round(restricted["gap_rate"] * 100, 1)
        if restricted["gap_rate"] is not None
        else None,
        "n_repos_with_mature_present_denominator": restricted["n_repos_with_mature_present"],
        "n_repos_with_active_mature_present": restricted["n_repos_with_active_mature_present"],
    }


def render_gaps_report(rows: list[dict], restricted_json: dict) -> str:
    lines = [
        "# Gaps by repository typology (T=180 days)",
        "",
        f"Generated: {restricted_json['generated_at']}",
        "",
        "Typology is heuristic and used for sensitivity stratification; the full analyzed sample remains reported.",
        "",
        "## Restricted repository estimand (all repositories)",
        "",
        f"- Original repository gap: **{restricted_json['original_repository_gap_pct']}%** "
        f"(denominator: {restricted_json['n_repos_analyzed']} adopted repositories)",
        f"- Restricted repository gap: **{restricted_json['restricted_repository_gap_pct']}%** "
        f"(denominator: {restricted_json['n_repos_with_mature_present']} repositories with ≥1 mature-present path)",
        f"- Artifact gap (mature-present): **{round(restricted_json['artifact_gap'] * 100, 1)}%** "
        f"(denominator: {restricted_json['n_mature_present_artifacts']} paths)",
        "",
        "## By typology group",
        "",
        "| Group | Repos | Artifact gap | Repo gap (original) | Repo gap (restricted) | Mature paths |",
        "|-------|------:|-------------:|--------------------:|----------------------:|-------------:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['group']} | {row['n_repos_analyzed']} | "
            f"{row['artifact_gap_pct']}% | {row['repository_gap_original_pct']}% | "
            f"{row['repository_gap_restricted_pct']}% | {row['n_mature_present_artifacts']} |"
        )
    lines.append("")
    coll = next(r for r in rows if r["group"] == "collection_or_list_only")
    codebase = next(r for r in rows if r["group"] == "codebase_only")
    all_r = next(r for r in rows if r["group"] == "all_repositories")
    lines.extend(
        [
            "## Interpretation notes",
            "",
            f"- Collection/list repositories ({coll['n_repos_analyzed']} repos) contribute "
            f"{coll['n_mature_present_artifacts']} mature-present paths "
            f"({coll['n_mature_present_artifacts'] / all_r['n_mature_present_artifacts'] * 100:.1f}% of the mature-present denominator).",
            f"- Codebase repositories ({codebase['n_repos_analyzed']} repos): artifact gap "
            f"{codebase['artifact_gap_pct']}% vs repository gap {codebase['repository_gap_original_pct']}% (original) / "
            f"{codebase['repository_gap_restricted_pct']}% (restricted).",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--states",
        type=Path,
        default=ROOT / "data/lifecycle/artifact_states_v2.parquet",
    )
    parser.add_argument(
        "--typology",
        type=Path,
        default=ROOT / "results/lifecycle/repository_typology.csv",
    )
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=ROOT / "results/lifecycle/gaps_by_repository_typology.csv",
    )
    parser.add_argument(
        "--restricted-json-out",
        type=Path,
        default=ROOT / "results/lifecycle/restricted_repository_gap_v2.json",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=ROOT / "results/lifecycle/gaps_by_repository_typology_report.md",
    )
    parser.add_argument("--t", type=int, default=T_PRIMARY)
    args = parser.parse_args()

    if not args.states.exists():
        raise SystemExit(f"missing states: {args.states}")
    if not args.typology.exists():
        raise SystemExit(f"missing typology (run repository_typology.py first): {args.typology}")

    states = pd.read_parquet(args.states)
    typology = pd.read_csv(args.typology)
    merged = states.merge(typology[["repo_id", "repo_type"]], on="repo_id", how="left")

    rows = []
    for group_name, mask_fn in GROUP_SPECS:
        repo_ids = set(typology.loc[mask_fn(typology), "repo_id"])
        stats = compute_group_gaps(merged, repo_ids, args.t)
        stats["group"] = group_name
        rows.append(stats)

    csv_df = pd.DataFrame(rows)
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    csv_df.to_csv(args.csv_out, index=False)

    all_stats = rows[0]
    restricted = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "T": args.t,
        "n_repos_analyzed": all_stats["n_repos_analyzed"],
        "n_repos_with_mature_present": all_stats["n_repos_with_mature_present_denominator"],
        "n_repos_with_active_mature_present": all_stats["n_repos_with_active_mature_present"],
        "original_repository_gap": all_stats["repository_gap_original"],
        "original_repository_gap_pct": all_stats["repository_gap_original_pct"],
        "restricted_repository_gap": all_stats["repository_gap_restricted"],
        "restricted_repository_gap_pct": all_stats["repository_gap_restricted_pct"],
        "artifact_gap": all_stats["artifact_gap"],
        "n_mature_present_artifacts": all_stats["n_mature_present_artifacts"],
        "typology_counts": typology.repo_type.value_counts().to_dict(),
    }
    args.restricted_json_out.write_text(json.dumps(restricted, indent=2) + "\n")
    args.md_out.write_text(render_gaps_report(rows, restricted))

    print(f"wrote {args.csv_out}")
    print(f"wrote {args.restricted_json_out}")
    print(f"wrote {args.md_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
