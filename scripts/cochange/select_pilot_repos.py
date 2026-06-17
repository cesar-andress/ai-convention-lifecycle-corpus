#!/usr/bin/env python3
"""Select repositories for the co-change scope-sensitivity pilot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cochange.repo_utils import repo_dir_from_id
from lifecycle.corpus_paths import configure

ROOT = configure()

PILOT_SELECTION = [
    {
        "repo_id": "cheat/cheat",
        "reason_selected": "small single-root CLAUDE.md; code-heavy CLI tool",
    },
    {
        "repo_id": "electron/electron",
        "reason_selected": "small repo with root and nested docs/CLAUDE.md",
    },
    {
        "repo_id": "dagster-io/dagster",
        "reason_selected": "medium artifact count but large monorepo history; root+nested CLAUDE.md",
    },
    {
        "repo_id": "apache/airflow",
        "reason_selected": "monorepo with multiple AGENTS/CLAUDE paths; code-heavy OSS",
    },
    {
        "repo_id": "BerriAI/litellm",
        "reason_selected": "medium repo with multiple root and nested instruction files",
    },
    {
        "repo_id": "payloadcms/payload",
        "reason_selected": "documentation- and package-heavy monorepo",
    },
    {
        "repo_id": "prefecthq/prefect",
        "reason_selected": "medium-large Python monorepo with multiple instruction paths",
    },
    {
        "repo_id": "grafana/grafana",
        "reason_selected": "large code-heavy frontend/backend monorepo",
    },
]

ROOT_PRIORITY = ["CLAUDE.md", "AGENTS.md", ".github/copilot-instructions.md", "SKILL.md"]


def instruction_files_for_repo(states: pd.DataFrame, repo_id: str, max_files: int = 2) -> list[str]:
    present = states[(states.repo_id == repo_id) & (states.present_in_head == True)]
    root_types = {"agents_md", "claude_md", "copilot_instructions", "skill_md"}
    roots = present[present.artifact_type.isin(root_types) & ~present.artifact_path.str.contains("/")]
    nested = present[
        (~present.artifact_path.str.contains("^[^/]+$", regex=True))
        & present.artifact_type.isin(root_types)
    ]

    selected: list[str] = []
    for pref in ROOT_PRIORITY:
        match = roots[roots.artifact_path == pref]
        if not match.empty:
            selected.append(pref)
            break
    if not selected and not roots.empty:
        selected.append(sorted(roots.artifact_path)[0])

    nested_pref = ["docs/CLAUDE.md", "docs/AGENTS.md"]
    for pref in nested_pref:
        if pref in nested.artifact_path.values and pref not in selected:
            selected.append(pref)
            break
    if len(selected) < max_files and not nested.empty:
        for path in sorted(nested.artifact_path):
            if path not in selected:
                selected.append(path)
                break

    return selected[:max_files]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results/cochange/pilot/pilot_repos.csv",
    )
    args = parser.parse_args()

    states = pd.read_parquet(ROOT / "data/lifecycle/artifact_states_v2.parquet")
    repos_dir = ROOT / "data/repos"

    rows = []
    for item in PILOT_SELECTION:
        repo_id = item["repo_id"]
        present = states[(states.repo_id == repo_id) & (states.present_in_head == True)]
        roots = present[
            present.artifact_type.isin({"agents_md", "claude_md", "copilot_instructions", "skill_md"})
            & ~present.artifact_path.str.contains("/")
        ]
        nested = present[
            present.artifact_path.str.contains("/")
            & present.artifact_type.isin({"agents_md", "claude_md", "copilot_instructions", "skill_md", "cursor_rules", "prompts"})
        ]
        clone = repo_dir_from_id(repo_id, repos_dir)
        clone_ok = clone.exists() and (clone / ".git").exists()
        if clone_ok:
            try:
                from lifecycle.git_utils import count_repo_commits

                clone_ok = count_repo_commits(clone) > 0
            except Exception:
                clone_ok = False
        rows.append(
            {
                "repo_id": repo_id,
                "reason_selected": item["reason_selected"],
                "n_instruction_files_known": len(present),
                "has_root_instruction": len(roots) > 0,
                "has_nested_instruction": len(nested) > 0,
                "local_clone_available": clone_ok,
                "pilot_instruction_files": ";".join(instruction_files_for_repo(states, repo_id)),
            }
        )

    out_df = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args.out, index=False)
    print(f"wrote {args.out} ({len(out_df)} repos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
