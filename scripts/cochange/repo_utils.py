"""Repository path and clone helpers for co-change pilots."""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

from lifecycle.git_utils import clone_repo, count_repo_commits

ROOT_INSTRUCTION_BASENAMES = frozenset(
    {
        "AGENTS.md",
        "CLAUDE.md",
        "SKILL.md",
        "copilot-instructions.md",
    }
)


def repo_dir_from_id(repo_id: str, repos_root: Path) -> Path:
    owner, repo = repo_id.split("/", 1)
    return repos_root / owner / repo


def safe_repo_dirname(repo_id: str) -> str:
    return repo_id.replace("/", "__")


def repo_url_from_discovered(repo_id: str, discovered_csv: Path) -> str | None:
    with discovered_csv.open() as f:
        for row in csv.DictReader(f):
            if row["repo_id"] == repo_id:
                return row["repo_url"]
    return f"https://github.com/{repo_id}"


def ensure_repo(
    repo_id: str,
    repo_dir: Path,
    repo_url: str,
    *,
    timeout: int = 600,
) -> None:
    """Clone repo_dir if missing or empty."""
    if repo_dir.exists() and count_repo_commits(repo_dir) > 0:
        return
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    ok = clone_repo(repo_url, repo_dir, timeout=timeout, shallow=False)
    if not ok or count_repo_commits(repo_dir) == 0:
        raise RuntimeError(f"failed to clone {repo_url} into {repo_dir}")
