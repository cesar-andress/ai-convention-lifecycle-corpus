#!/usr/bin/env python3
"""Build stratified construct-validation sample for synchronization metric."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.corpus_paths import configure
from synchronization.units import MANUAL_COLUMNS, REVIEW_CONTEXT_COLUMNS, prepare_sample

ROOT = configure()


def render_readme(meta: dict, sample_path: Path, annotation_path: Path) -> str:
    lines = [
        "# Synchronization construct validation sample",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"- Review context: `{sample_path}`",
        f"- Annotation workbook: `{annotation_path}`",
        "- Guidelines: `annotation/sync_construct_validation_guidelines.md`",
        "",
        f"**Sampled units:** {meta.get('sampled_n', 0)} (target {meta.get('target_n', 100)})",
        f"**Pool before sampling:** {meta.get('pool_size_before_sample', 0)}",
        "",
        "## Stratum balance",
        "",
        "| artifact_family | metric_label | repo_size_class | count |",
        "|-----------------|--------------|-----------------|-------|",
    ]
    for row in meta.get("balance", []):
        lines.append(
            f"| {row['artifact_family']} | {row['metric_label']} | "
            f"{row['repo_size_class']} | {row['count']} |"
        )

    shortages = meta.get("stratum_shortages") or {}
    lines.extend(["", "## Shortages", ""])
    if not shortages:
        lines.append("None — all strata filled to target per-stratum quota.")
    else:
        for key, short in sorted(shortages.items()):
            lines.append(f"- `{key}`: short by {short} units")

    lines.extend(
        [
            "",
            "## Manual annotation",
            "",
            "Fill `annotation/sync_construct_validation_sample.csv` only.",
            "Do not edit manual columns in the results copy.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pilot-repos",
        type=Path,
        default=ROOT / "results/synchronization_spectrum/pilot_repos.csv",
    )
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=ROOT / "results/synchronization_spectrum/manifests",
    )
    parser.add_argument(
        "--sample-out",
        type=Path,
        default=ROOT / "results/synchronization_validation/sync_validation_sample.csv",
    )
    parser.add_argument(
        "--annotation-out",
        type=Path,
        default=ROOT / "annotation/sync_construct_validation_sample.csv",
    )
    parser.add_argument("--target-n", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    import pandas as pd

    if not args.pilot_repos.exists():
        raise SystemExit(f"missing pilot repos: {args.pilot_repos}")

    pilot_df = pd.read_csv(args.pilot_repos)
    repos_dir = ROOT / "data/repos"

    sample_df, annotation_df, meta = prepare_sample(
        pilot_df,
        args.manifest_dir,
        repos_dir,
        target_n=args.target_n,
        seed=args.seed,
    )

    args.sample_out.parent.mkdir(parents=True, exist_ok=True)
    sample_df.to_csv(args.sample_out, index=False)
    print(f"wrote {args.sample_out} ({len(sample_df)} units)")

    args.annotation_out.parent.mkdir(parents=True, exist_ok=True)
    annotation_cols = REVIEW_CONTEXT_COLUMNS + MANUAL_COLUMNS
    annotation_df[annotation_cols].to_csv(args.annotation_out, index=False)
    print(f"wrote {args.annotation_out}")

    meta_path = args.sample_out.parent / "sync_validation_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, default=str) + "\n")
    print(f"wrote {meta_path}")

    readme_path = args.sample_out.parent / "sync_validation_sample_readme.md"
    readme_path.write_text(
        render_readme(meta, args.sample_out, args.annotation_out)
    )
    print(f"wrote {readme_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
