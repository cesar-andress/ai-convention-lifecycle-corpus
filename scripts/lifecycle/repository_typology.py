#!/usr/bin/env python3
"""Conservative repository typology for lifecycle sensitivity analysis."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.corpus_paths import configure
from lifecycle.git_utils import list_head_files

ROOT = configure()

KNOWN_COLLECTION_OR_LIST = {
    "sickn33/antigravity-awesome-skills",
    "ComposioHQ/awesome-claude-skills",
    "thedaviddias/Front-End-Checklist",
    "f/prompts.chat",
    "mattpocock/skills",
}

NAME_PATTERNS = [
    re.compile(r"awesome", re.I),
    re.compile(r"checklist", re.I),
    re.compile(r"curated", re.I),
    re.compile(r"catalog", re.I),
    re.compile(r"prompts\.chat", re.I),
]

SOURCE_EXT = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".c",
    ".cpp",
    ".h",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".scala",
    ".vue",
    ".sql",
    ".sh",
}
MD_PROMPT_EXT = {".md", ".mdc", ".txt", ".yaml", ".yml"}


def head_file_counts(repo_dir: Path) -> tuple[int, int, int]:
    """Return (n_source_files, n_markdown_or_prompt_files, prompts_path_count)."""
    if not repo_dir.exists():
        return 0, 0, 0
    n_src = n_md = n_prompts = 0
    for rel in list_head_files(repo_dir):
        p = Path(rel)
        ext = p.suffix.lower()
        if ext in SOURCE_EXT:
            n_src += 1
        if ext in MD_PROMPT_EXT:
            n_md += 1
        if rel.startswith("prompts/") or "/prompts/" in rel:
            n_prompts += 1
    return n_src, n_md, n_prompts


def classify_repo(
    repo_id: str,
    *,
    n_ever: int,
    n_present: int,
    n_mature: int,
    n_skill_md: int,
    n_prompts_paths: int,
    n_src: int,
    n_md: int,
    prompts_head: int,
) -> tuple[str, str, str]:
    """Return (repo_type, typology_reason, confidence)."""
    owner, repo = repo_id.split("/", 1)
    reasons: list[str] = []

    if repo_id in KNOWN_COLLECTION_OR_LIST:
        reasons.append("known_curated_list_repository")
        return "collection_or_list", "; ".join(reasons), "high"

    name_hits = [pat.pattern for pat in NAME_PATTERNS if pat.search(repo)]
    skill_share = n_skill_md / n_ever if n_ever else 0.0
    md_share = n_md / (n_md + n_src) if (n_md + n_src) else 0.0

    structural_collection = False
    if n_skill_md >= 200 and skill_share >= 0.75 and n_src < 600:
        structural_collection = True
        reasons.append("high_skill_md_dominance_with_modest_source_footprint")
    if n_prompts_paths >= 100 and n_src < 120:
        structural_collection = True
        reasons.append("large_prompts_tree_low_source_footprint")
    if n_ever >= 80 and n_src < 30 and md_share >= 0.85:
        structural_collection = True
        reasons.append("markdown_heavy_low_source_footprint")

    if name_hits and structural_collection:
        reasons.append(f"name_pattern({','.join(name_hits)})")
        return "collection_or_list", "; ".join(reasons), "medium"

    if name_hits and repo_id.endswith("-skills") and n_skill_md >= 50:
        reasons.append(f"name_pattern({','.join(name_hits)})")
        reasons.append("skills_suffix_with_many_skill_md_paths")
        return "collection_or_list", "; ".join(name_hits), "medium"

    if structural_collection and skill_share >= 0.9 and n_ever >= 300:
        return "collection_or_list", "; ".join(reasons), "medium"

    codebase_reasons: list[str] = []
    if n_src >= 200:
        codebase_reasons.append("substantial_source_code_footprint_at_head")
    elif n_src >= 80 and n_src > n_skill_md:
        codebase_reasons.append("source_files_exceed_skill_md_paths")
    elif n_ever <= 20 and n_src >= 30:
        codebase_reasons.append("low_path_multiplicity_with_source_code")

    if codebase_reasons and not name_hits:
        return "codebase", "; ".join(codebase_reasons), "medium"

    if n_src >= 500:
        return "codebase", "large_source_code_footprint_at_head", "high"

    return "unclear", "insufficient_confidence_for_codebase_or_collection_label", "low"


def build_typology(states_path: Path, repos_dir: Path) -> pd.DataFrame:
    df = pd.read_parquet(states_path)
    rows = []
    for repo_id, grp in df.groupby("repo_id", sort=True):
        owner, repo = repo_id.split("/", 1)
        repo_dir = repos_dir / owner / repo
        n_src, n_md, prompts_head = head_file_counts(repo_dir)
        n_ever = len(grp)
        n_present = int(grp["present_in_head"].sum())
        n_mature = int(grp["mature_present_180"].sum())
        n_skill_md = int((grp["artifact_type"] == "skill_md").sum())
        n_prompts_paths = int((grp["artifact_type"] == "prompts").sum())

        repo_type, reason, confidence = classify_repo(
            repo_id,
            n_ever=n_ever,
            n_present=n_present,
            n_mature=n_mature,
            n_skill_md=n_skill_md,
            n_prompts_paths=n_prompts_paths,
            n_src=n_src,
            n_md=n_md,
            prompts_head=prompts_head,
        )
        rows.append(
            {
                "repo_id": repo_id,
                "repo_type": repo_type,
                "typology_reason": reason,
                "n_ever_introduced_paths": n_ever,
                "n_present_paths": n_present,
                "n_mature_present_paths": n_mature,
                "n_source_files_head": n_src,
                "n_markdown_or_prompt_files_head": n_md,
                "prompts_path_count": max(n_prompts_paths, prompts_head),
                "confidence": confidence,
            }
        )
    return pd.DataFrame(rows)


def render_report(summary: dict, df: pd.DataFrame) -> str:
    lines = [
        "# Repository typology report",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "Conservative heuristic typology for sensitivity stratification (not corpus exclusion).",
        "",
        "## Counts by type",
        "",
    ]
    for k, v in summary["counts_by_type"].items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("## Collection/list repositories (high/medium confidence)")
    lines.append("")
    coll = df[df.repo_type == "collection_or_list"].sort_values("n_ever_introduced_paths", ascending=False)
    for _, row in coll.iterrows():
        lines.append(
            f"- `{row.repo_id}` ({row.confidence}): {row.n_ever_introduced_paths} paths; {row.typology_reason}"
        )
    lines.append("")
    lines.append("## Unclear repositories")
    lines.append("")
    lines.append(f"{summary['counts_by_type'].get('unclear', 0)} repositories left as `unclear` to avoid over-classification.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--states",
        type=Path,
        default=ROOT / "data/lifecycle/artifact_states_v2.parquet",
    )
    parser.add_argument("--repos-dir", type=Path, default=ROOT / "data/repos")
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=ROOT / "results/lifecycle/repository_typology.csv",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=ROOT / "results/lifecycle/repository_typology_summary.json",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=ROOT / "results/lifecycle/repository_typology_report.md",
    )
    args = parser.parse_args()

    if not args.states.exists():
        raise SystemExit(f"missing states parquet: {args.states}")

    df = build_typology(args.states, args.repos_dir)
    counts = Counter(df.repo_type)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_repos": len(df),
        "counts_by_type": dict(counts),
        "confidence_counts": dict(Counter(df.confidence)),
        "known_collection_repos_present": sorted(
            r for r in KNOWN_COLLECTION_OR_LIST if r in set(df.repo_id)
        ),
        "collection_or_list_repo_ids": sorted(df.loc[df.repo_type == "collection_or_list", "repo_id"]),
    }

    args.csv_out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.csv_out, index=False)
    args.json_out.write_text(json.dumps(summary, indent=2) + "\n")
    args.md_out.write_text(render_report(summary, df))

    print(f"wrote {args.csv_out}")
    print(f"wrote {args.json_out}")
    print(f"wrote {args.md_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
