#!/usr/bin/env python3
"""Select 25 repositories for the synchronization spectrum pilot."""

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

COCHANGE_PILOT = [
    "cheat/cheat",
    "electron/electron",
    "dagster-io/dagster",
    "apache/airflow",
    "BerriAI/litellm",
    "payloadcms/payload",
    "prefecthq/prefect",
    "grafana/grafana",
]

INSTRUCTION_TYPES = {
    "claude_md",
    "agents_md",
    "cursor_rules",
    "copilot_instructions",
    "skill_md",
}

TARGET_N = 25


def repos_with_instructions(states: pd.DataFrame) -> pd.DataFrame:
    present = states[states.present_in_head == True]
    inst = present[present.artifact_type.isin(INSTRUCTION_TYPES)]
    summary = (
        inst.groupby("repo_id")
        .agg(
            n_instruction_files=("artifact_path", "count"),
            has_root_instruction=(
                "artifact_path",
                lambda s: any("/" not in p for p in s),
            ),
            seed_pool=("seed_pool", "first"),
        )
        .reset_index()
    )
    return summary


def select_additional(
    candidates: pd.DataFrame,
    already: set[str],
    n_needed: int,
) -> list[str]:
    remaining = candidates[~candidates.repo_id.isin(already)].copy()
    remaining = remaining.sort_values(["seed_pool", "repo_id"])

    selected: list[str] = []
    pools = list(remaining["seed_pool"].drop_duplicates())
    idx = 0
    while len(selected) < n_needed and not remaining.empty:
        made_progress = False
        for pool in pools:
            if len(selected) >= n_needed:
                break
            pool_rows = remaining[remaining.seed_pool == pool]
            if pool_rows.empty:
                continue
            pick = pool_rows.iloc[idx % len(pool_rows)]
            repo_id = pick["repo_id"]
            if repo_id in already or repo_id in selected:
                continue
            selected.append(repo_id)
            remaining = remaining[remaining.repo_id != repo_id]
            made_progress = True
        if not made_progress:
            break
        idx += 1

    if len(selected) < n_needed:
        for repo_id in remaining.repo_id:
            if repo_id in already or repo_id in selected:
                continue
            selected.append(repo_id)
            if len(selected) >= n_needed:
                break
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results/synchronization_spectrum/pilot_repos.csv",
    )
    parser.add_argument("--target-n", type=int, default=TARGET_N)
    args = parser.parse_args()

    states = pd.read_parquet(ROOT / "data/lifecycle/artifact_states_v2.parquet")
    discovered = pd.read_csv(ROOT / "data/lifecycle/discovered_v2.csv")
    repos_dir = ROOT / "data/repos"

    inst_summary = repos_with_instructions(states)
    discovered_ids = set(discovered.repo_id)
    inst_summary = inst_summary[inst_summary.repo_id.isin(discovered_ids)]

    rows: list[dict] = []
    selected: list[str] = []

    for repo_id in COCHANGE_PILOT:
        if repo_id not in inst_summary.repo_id.values:
            continue
        selected.append(repo_id)

    n_needed = max(0, args.target_n - len(selected))
    extra = select_additional(inst_summary, set(selected), n_needed)
    selected.extend(extra)

    cochange_reasons = {
        "cheat/cheat": "small single-root CLAUDE.md; code-heavy CLI tool",
        "electron/electron": "small repo with root and nested docs/CLAUDE.md",
        "dagster-io/dagster": "medium artifact count but large monorepo history; root+nested CLAUDE.md",
        "apache/airflow": "monorepo with multiple AGENTS/CLAUDE paths; code-heavy OSS",
        "BerriAI/litellm": "medium repo with multiple root and nested instruction files",
        "payloadcms/payload": "documentation- and package-heavy monorepo",
        "prefecthq/prefect": "medium-large Python monorepo with multiple instruction paths",
        "grafana/grafana": "large code-heavy frontend/backend monorepo",
    }

    for repo_id in selected:
        meta = inst_summary[inst_summary.repo_id == repo_id].iloc[0]
        clone = repo_dir_from_id(repo_id, repos_dir)
        clone_ok = clone.exists() and (clone / ".git").exists()
        reason = cochange_reasons.get(repo_id, f"stratified expansion ({meta['seed_pool']})")
        cohort = "cochange_pilot" if repo_id in COCHANGE_PILOT else "lifecycle_expansion"
        rows.append(
            {
                "repo_id": repo_id,
                "cohort": cohort,
                "seed_pool": meta["seed_pool"],
                "reason_selected": reason,
                "n_instruction_files_head": int(meta["n_instruction_files"]),
                "has_root_instruction": bool(meta["has_root_instruction"]),
                "local_clone_available": clone_ok,
            }
        )

    out_df = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args.out, index=False)
    print(f"wrote {args.out} ({len(out_df)} repos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
