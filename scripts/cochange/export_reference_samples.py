#!/usr/bin/env python3
"""Export illustrative reference extraction examples and validation sample."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cochange.content_refs import extract_content_references
from cochange.repo_utils import repo_dir_from_id, safe_repo_dirname
from lifecycle.corpus_paths import configure
from lifecycle.git_utils import list_head_files

ROOT = configure()


def collect_all_v2_refs(pilot_csv: Path, manifest_dir: Path) -> pd.DataFrame:
    pilot = pd.read_csv(pilot_csv)
    rows: list[dict] = []
    for _, pr in pilot.iterrows():
        repo_id = pr["repo_id"]
        repo_dir = repo_dir_from_id(repo_id, ROOT / "data/repos")
        head_files = set(list_head_files(repo_dir))
        for instr in str(pr["pilot_instruction_files"]).split(";"):
            if not instr:
                continue
            rows.extend(extract_content_references(repo_id, repo_dir, instr, head_files))
    return pd.DataFrame(rows)


def build_examples(df: pd.DataFrame, out: Path) -> None:
    """Pick diverse high/medium examples per repo (used and unused)."""
    picks: list[pd.Series] = []
    for repo_id in df["repo_id"].unique():
        sub = df[df.repo_id == repo_id]
        for used in (True, False):
            pool = sub[sub.used_for_scope == used]
            if pool.empty:
                continue
            for conf in ("high", "medium", "low"):
                conf_pool = pool[pool.confidence == conf]
                if not conf_pool.empty:
                    picks.append(conf_pool.iloc[0])
                    break
    examples = pd.DataFrame(picks).drop_duplicates()
    examples = examples[
        [
            "repo_id",
            "instruction_file",
            "raw_text",
            "resolved_path",
            "extraction_rule",
            "confidence",
            "exists_in_head",
            "used_for_scope",
        ]
    ]
    examples.to_csv(out, index=False)
    print(f"wrote {out} ({len(examples)} examples)")


def build_validation_sample(df: pd.DataFrame, out: Path, n: int = 50, seed: int = 42) -> None:
    sample = df.sample(n=min(n, len(df)), random_state=seed)
    sample = sample[
        [
            "repo_id",
            "instruction_file",
            "raw_reference",
            "resolved_path",
            "extraction_rule",
            "confidence",
        ]
    ].rename(columns={"raw_reference": "raw_reference"})
    sample.to_csv(out, index=False)
    print(f"wrote {out} ({len(sample)} rows)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-repos", type=Path, default=ROOT / "results/cochange/pilot/pilot_repos.csv")
    parser.add_argument("--examples-out", type=Path, default=ROOT / "results/cochange/reference_extraction_examples.csv")
    parser.add_argument("--validation-out", type=Path, default=ROOT / "results/cochange/reference_validation_sample.csv")
    args = parser.parse_args()

    df = collect_all_v2_refs(args.pilot_repos, ROOT / "results/cochange/pilot")
    args.examples_out.parent.mkdir(parents=True, exist_ok=True)
    build_examples(df, args.examples_out)
    build_validation_sample(df, args.validation_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
