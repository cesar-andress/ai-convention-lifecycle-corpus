#!/usr/bin/env python3
"""Extract commit-level changed-file manifests for co-change feasibility (prototype)."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.corpus_paths import configure
from lifecycle.git_utils import clone_repo, count_repo_commits, run_git

ROOT = configure()

DEFAULT_REPO_ID = "dagster-io/dagster"
DEFAULT_REPO_URL = "https://github.com/dagster-io/dagster"
DEFAULT_REPO_DIR = ROOT / "data" / "repos" / "dagster-io" / "dagster"
DEFAULT_OUT = ROOT / "results" / "cochange" / "prototype" / "dagster_changed_files.parquet"

# git name-status codes we retain (exclude pure deletes from sync prototype for now).
TRACKED_STATUSES = frozenset({"A", "M", "D", "R", "C", "T"})


def ensure_repo(repo_url: str, repo_dir: Path, timeout: int) -> None:
    """Clone or refresh repo_dir if missing or empty."""
    if repo_dir.exists() and count_repo_commits(repo_dir) > 0:
        return
    if repo_dir.exists():
        print(f"removing empty or broken clone: {repo_dir}", file=sys.stderr)
        shutil.rmtree(repo_dir)
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    ok = clone_repo(repo_url, repo_dir, timeout=timeout, shallow=False)
    if not ok or count_repo_commits(repo_dir) == 0:
        raise SystemExit(f"failed to clone {repo_url} into {repo_dir}")


def parse_name_status_log(text: str, repo_id: str) -> tuple[list[dict], int]:
    rows: list[dict] = []
    commit_sha: str | None = None
    author_ts: int | None = None
    n_commits = 0

    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if not line:
            continue
        if line.startswith("COMMIT|"):
            parts = line.split("|", 2)
            if len(parts) == 3:
                commit_sha = parts[1]
                author_ts = int(parts[2])
                n_commits += 1
            continue
        if commit_sha is None or author_ts is None:
            continue
        if "\t" not in line:
            continue
        status, path = line.split("\t", 1)
        status = status.strip()
        path = path.strip().replace("\\", "/").lstrip("./")
        if not path:
            continue
        # Rename/copy lines may be `R100\told\tnew`; keep final path.
        if "\t" in path:
            path = path.split("\t")[-1].strip()
        base_status = status[0] if status else status
        if base_status not in TRACKED_STATUSES:
            continue
        rows.append(
            {
                "repo_id": repo_id,
                "commit": commit_sha,
                "author_date": datetime.fromtimestamp(author_ts, tz=timezone.utc),
                "changed_path": path,
                "change_status": base_status,
            }
        )
    return rows, n_commits


def extract_changed_files(repo_dir: Path, repo_id: str) -> tuple[pd.DataFrame, int]:
    proc = run_git(
        [
            "git",
            "log",
            "HEAD",
            "--no-merges",
            "--name-status",
            "--no-renames",
            "--format=COMMIT|%H|%at",
        ],
        cwd=repo_dir,
    )
    if proc.returncode != 0:
        raise SystemExit(f"git log failed in {repo_dir}: {proc.stderr.strip()}")

    rows, n_commits = parse_name_status_log(proc.stdout, repo_id)
    if not rows:
        raise SystemExit(f"no changed-file rows parsed from {repo_dir}")
    df = pd.DataFrame(rows).sort_values(["author_date", "commit", "changed_path"]).reset_index(drop=True)
    return df, n_commits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID)
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL)
    parser.add_argument("--repo-path", type=Path, default=DEFAULT_REPO_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--csv", action="store_true", help="Also write a CSV alongside parquet")
    parser.add_argument("--clone-timeout", type=int, default=600)
    args = parser.parse_args()

    ensure_repo(args.repo_url, args.repo_path, timeout=args.clone_timeout)
    df, n_commits = extract_changed_files(args.repo_path, args.repo_id)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out, index=False)
    print(f"commits parsed: {n_commits}")
    print(f"changed-file rows: {len(df)}")
    print(f"wrote {args.out}")

    if args.csv:
        csv_path = args.out.with_suffix(".csv")
        df.to_csv(csv_path, index=False)
        print(f"wrote {csv_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
