"""Shared git helpers for instruction-lifecycle."""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"}


def run_git(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run git; tolerate non-UTF8 bytes in log output (author names, paths)."""
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=GIT_ENV,
    )


def parse_github_url(url: str) -> tuple[str, str] | None:
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", url.strip())
    return (m.group(1), m.group(2)) if m else None


def clone_repo(url: str, dest: Path, timeout: int = 180, shallow: bool = False) -> bool:
    if dest.exists():
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone", "--single-branch", "--quiet", url, str(dest)]
    if shallow:
        cmd[2:2] = ["--depth", "1", "--filter=blob:none"]
    try:
        proc = run_git(cmd, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False
    return proc.returncode == 0


def normalize_repo_relative_path(path: str) -> str:
    """Normalize a repository-relative path; strip only a literal leading './'."""
    p = path.replace("\\", "/").strip()
    if p.startswith("./"):
        p = p[2:]
    return p


def list_head_files(repo_dir: Path) -> list[str]:
    proc = run_git(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=repo_dir)
    if proc.returncode != 0:
        return []
    return [normalize_repo_relative_path(p) for p in proc.stdout.splitlines() if p.strip()]


def repo_last_commit_ts(repo_dir: Path) -> datetime | None:
    proc = run_git(["git", "log", "-1", "--format=%at"], cwd=repo_dir)
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    return datetime.fromtimestamp(int(proc.stdout.strip()), tz=timezone.utc)


def count_repo_commits(repo_dir: Path) -> int:
    proc = run_git(["git", "rev-list", "--count", "HEAD"], cwd=repo_dir)
    if proc.returncode != 0:
        return 0
    try:
        return int(proc.stdout.strip())
    except ValueError:
        return 0


def fetch_stars(owner: str, repo: str) -> int | None:
    try:
        proc = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}", "--jq", ".stargazers_count"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if proc.returncode != 0:
        return None
    try:
        return int(proc.stdout.strip())
    except ValueError:
        return None
