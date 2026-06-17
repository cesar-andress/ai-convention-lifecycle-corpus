#!/usr/bin/env python3
"""Extract commit-level changed-file manifests for an arbitrary repository."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cochange.changed_files import extract_changed_files, manifest_output_path
from cochange.repo_utils import ensure_repo, repo_dir_from_id, repo_url_from_discovered
from lifecycle.corpus_paths import configure

ROOT = configure()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-id", required=True, help="owner/name")
    parser.add_argument("--clone-path", type=Path, default=None)
    parser.add_argument("--repo-url", default=None)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/cochange/pilot")
    parser.add_argument("--out", type=Path, default=None, help="Override manifest output path")
    parser.add_argument("--csv", action="store_true")
    parser.add_argument("--clone-timeout", type=int, default=600)
    args = parser.parse_args()

    repo_dir = args.clone_path or repo_dir_from_id(args.repo_id, ROOT / "data/repos")
    repo_url = args.repo_url or repo_url_from_discovered(
        args.repo_id, ROOT / "data/lifecycle/discovered_v2.csv"
    )
    out = args.out or manifest_output_path(args.output_dir, args.repo_id)

    ensure_repo(args.repo_id, repo_dir, repo_url, timeout=args.clone_timeout)
    df, n_commits = extract_changed_files(repo_dir, args.repo_id)

    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"commits parsed: {n_commits}")
    print(f"changed-file rows: {len(df)}")
    print(f"wrote {out}")

    if args.csv:
        csv_path = out.with_suffix(".csv")
        df.to_csv(csv_path, index=False)
        print(f"wrote {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
