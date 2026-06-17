"""Commit-level changed-file manifest extraction."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from lifecycle.git_utils import run_git

TRACKED_STATUSES = frozenset({"A", "M", "D", "R", "C", "T"})


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
        raise RuntimeError(f"git log failed in {repo_dir}: {proc.stderr.strip()}")

    rows, n_commits = parse_name_status_log(proc.stdout, repo_id)
    if not rows:
        raise RuntimeError(f"no changed-file rows parsed from {repo_dir}")
    df = pd.DataFrame(rows).sort_values(["author_date", "commit", "changed_path"]).reset_index(drop=True)
    return df, n_commits


def manifest_output_path(output_dir: Path, repo_id: str) -> Path:
    return output_dir / f"{repo_id.replace('/', '__')}_changed_files.parquet"
