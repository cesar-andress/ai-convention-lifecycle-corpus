#!/usr/bin/env python3
"""Clone repositories and extract per-artifact git touch history."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lifecycle.detection import artifact_type, is_bot, is_ci_path, is_lifecycle_artifact, load_config
from lifecycle.git_utils import (
    GIT_ENV,
    clone_repo,
    count_repo_commits,
    fetch_stars,
    list_head_files,
    repo_last_commit_ts,
    run_git,
)

DEFAULT_CONFIG = ROOT / "protocol" / "lifecycle_v1.yaml"


def discover_artifact_paths(repo_dir: Path, cfg: dict) -> set[str]:
    """Paths matching lifecycle scope seen anywhere in git history."""
    proc = run_git(
        ["git", "log", "--all", "--pretty=format:", "--name-only", "--diff-filter=AMR"],
        cwd=repo_dir,
    )
    paths: set[str] = set()
    if proc.returncode == 0:
        for line in proc.stdout.splitlines():
            p = line.strip().replace("\\", "/").lstrip("./")
            if p and is_lifecycle_artifact(p, cfg):
                paths.add(p)
    for p in list_head_files(repo_dir):
        if is_lifecycle_artifact(p, cfg):
            paths.add(p)
    return paths


def touch_history_for_path(repo_dir: Path, path: str) -> list[dict]:
    proc = run_git(
        ["git", "log", "--all", "--follow", "--format=%H|%at|%an|%ae", "--", path],
        cwd=repo_dir,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return []

    rows: list[dict] = []
    seen_shas: set[str] = set()
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        sha, ts, author, email = line.split("|", 3)
        if sha in seen_shas:
            continue
        seen_shas.add(sha)
        rows.append(
            {
                "commit": sha,
                "committed_at": datetime.fromtimestamp(int(ts), tz=timezone.utc),
                "author": author,
                "email": email,
            }
        )
    rows.sort(key=lambda r: r["committed_at"])
    return rows


def repo_commit_stats(repo_dir: Path, cfg: dict) -> dict:
    n_commits = count_repo_commits(repo_dir)

    proc_auth = run_git(
        ["git", "log", "--all", "--no-merges", "--pretty=format:%an|%ae"],
        cwd=repo_dir,
    )
    n_auth = 0
    n_bot = 0
    if proc_auth.returncode == 0:
        for line in proc_auth.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("|", 1)
            author = parts[0]
            email = parts[1] if len(parts) > 1 else ""
            n_auth += 1
            if is_bot(author, email, cfg):
                n_bot += 1

    proc_ci = run_git(
        ["git", "log", "--all", "--no-merges", "--pretty=format:@@", "--name-only"],
        cwd=repo_dir,
    )
    n_ci_commits = 0
    n_valid_commits = 0
    if proc_ci.returncode == 0:
        files: list[str] = []
        for raw in proc_ci.stdout.splitlines():
            if raw == "@@":
                if files:
                    n_valid_commits += 1
                    if any(is_ci_path(f, cfg) for f in files):
                        n_ci_commits += 1
                files = []
            elif raw.strip():
                files.append(raw.strip().replace("\\", "/").lstrip("./"))
        if files:
            n_valid_commits += 1
            if any(is_ci_path(f, cfg) for f in files):
                n_ci_commits += 1

    denom = n_auth if n_auth else n_commits
    ci_denom = n_valid_commits if n_valid_commits else n_commits
    return {
        "n_commits": n_commits,
        "bot_rate": n_bot / denom if denom else 0.0,
        "ci_rate": n_ci_commits / ci_denom if ci_denom else 0.0,
    }


def extract_repo(
    repo_url: str,
    repo_id: str,
    owner: str,
    repo: str,
    repos_dir: Path,
    cfg: dict,
    timeout: int,
    min_commits: int,
) -> tuple[list[dict], dict | None, str | None]:
    repo_dir = repos_dir / owner / repo
    if not clone_repo(repo_url, repo_dir, timeout=timeout, shallow=False):
        return [], None, "clone_fail"

    if count_repo_commits(repo_dir) < min_commits:
        return [], None, "low_commits"

    observation_end = repo_last_commit_ts(repo_dir)
    if observation_end is None:
        return [], None, "no_commits"

    artifact_paths = discover_artifact_paths(repo_dir, cfg)
    if not artifact_paths:
        return [], None, "no_artifacts"

    touch_rows: list[dict] = []
    for path in sorted(artifact_paths):
        history = touch_history_for_path(repo_dir, path)
        if not history:
            continue
        atype = artifact_type(path, cfg)
        for i, touch in enumerate(history):
            touch_rows.append(
                {
                    "repo_id": repo_id,
                    "artifact_type": atype,
                    "artifact_path": path,
                    "touch_index": i,
                    "commit": touch["commit"],
                    "committed_at": touch["committed_at"],
                    "observation_end": observation_end,
                }
            )

    n_files = len(list_head_files(repo_dir))
    stats = repo_commit_stats(repo_dir, cfg)
    stars = fetch_stars(owner, repo)

    covariates = {
        "repo_id": repo_id,
        "repo_url": repo_url,
        "observation_end": observation_end,
        "n_repo_files": n_files,
        "log_repo_files": __import__("math").log10(max(n_files, 1)),
        "commit_volume": stats["n_commits"],
        "log_commit_volume": __import__("math").log10(max(stats["n_commits"], 1)),
        "stars": stars if stars is not None else float("nan"),
        "log_stars": __import__("math").log10(max(stars, 1)) if stars else float("nan"),
        "bot_rate": stats["bot_rate"],
        "ci_rate": stats["ci_rate"],
        "n_artifacts": len(artifact_paths),
    }
    return touch_rows, covariates, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--discovered", type=Path, default=None)
    parser.add_argument("--repos-dir", type=Path, default=None)
    parser.add_argument("--touch-out", type=Path, default=None)
    parser.add_argument("--covariates-out", type=Path, default=None)
    parser.add_argument("--attrition-out", type=Path, default=None)
    parser.add_argument("--meta-out", type=Path, default=None)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Keep existing touch/cov parquets and skip repos already extracted ok.",
    )
    args = parser.parse_args()

    cfg = load_config(str(args.config))
    discovered_path = args.discovered or ROOT / cfg["outputs"]["discovered"]
    repos_dir = args.repos_dir or ROOT / cfg["extraction"]["repos_dir"]
    touch_out = args.touch_out or ROOT / cfg["outputs"]["touch_history"]
    cov_out = args.covariates_out or ROOT / cfg["outputs"]["repo_covariates"]
    attrition_out = args.attrition_out or ROOT / "results/lifecycle/extract_attrition.csv"
    meta_out = args.meta_out or touch_out.with_name("extract_meta.json")
    timeout = int(cfg["extraction"]["clone_timeout_seconds"])
    min_commits = int(cfg["extraction"]["min_repo_commits"])

    if not discovered_path.exists():
        print(f"missing discovered file: {discovered_path}", file=sys.stderr)
        return 1

    discovered_rows = list(csv.DictReader(discovered_path.open()))
    n_discovered = len(discovered_rows)
    print(f"extract: {n_discovered} repos from {discovered_path}", file=sys.stderr)

    touch_rows: list[dict] = []
    cov_rows: list[dict] = []
    attrition: list[dict] = []
    done_ids: set[str] = set()

    if args.resume and touch_out.exists() and cov_out.exists():
        touch_df = pd.read_parquet(touch_out)
        cov_df = pd.read_parquet(cov_out)
        touch_rows = touch_df.to_dict(orient="records")
        cov_rows = cov_df.to_dict(orient="records")
        if attrition_out.exists():
            attrition = pd.read_csv(attrition_out).to_dict(orient="records")
            done_ids = {a["repo_id"] for a in attrition if a.get("status") == "ok"}
        else:
            done_ids = set(touch_df["repo_id"].unique())
        print(
            f"resume: {len(done_ids)} repos already extracted, {len(touch_rows)} touch rows loaded",
            file=sys.stderr,
        )
    elif not args.resume:
        # Prevent downstream reads of stale parquets while a fresh extract runs.
        for stale in (touch_out, cov_out, meta_out):
            if stale.exists():
                stale.unlink()
                print(f"removed stale output: {stale}", file=sys.stderr)

    for row in discovered_rows:
        if row["repo_id"] in done_ids:
            continue
        try:
            touches, cov, reason = extract_repo(
                row["repo_url"],
                row["repo_id"],
                row["owner"],
                row["repo"],
                repos_dir,
                cfg,
                timeout,
                min_commits,
            )
        except Exception as exc:
            attrition.append(
                {
                    "repo_id": row["repo_id"],
                    "seed_pool": row.get("seed_pool", ""),
                    "status": "skipped",
                    "reason": f"extract_error:{exc.__class__.__name__}",
                    "n_touch_rows": 0,
                }
            )
            print(f"skip {row['repo_id']}: extract_error:{exc}", file=sys.stderr)
            continue
        if reason:
            attrition.append(
                {
                    "repo_id": row["repo_id"],
                    "seed_pool": row.get("seed_pool", ""),
                    "status": "skipped",
                    "reason": reason,
                    "n_touch_rows": 0,
                }
            )
            print(f"skip {row['repo_id']}: {reason}", file=sys.stderr)
            continue

        if not touches:
            attrition.append(
                {
                    "repo_id": row["repo_id"],
                    "seed_pool": row.get("seed_pool", ""),
                    "status": "skipped",
                    "reason": "no_touch_rows",
                    "n_touch_rows": 0,
                }
            )
            print(f"skip {row['repo_id']}: no_touch_rows", file=sys.stderr)
            continue

        touch_rows.extend(touches)
        if cov:
            cov_rows.append(cov)
        attrition.append(
            {
                "repo_id": row["repo_id"],
                "seed_pool": row.get("seed_pool", ""),
                "status": "ok",
                "reason": "",
                "n_touch_rows": len(touches),
            }
        )
        print(f"ok: {row['repo_id']} ({len(touches)} touch rows)", file=sys.stderr)

    if not touch_rows:
        print("no touch history extracted", file=sys.stderr)
        return 1

    touch_out.parent.mkdir(parents=True, exist_ok=True)
    attrition_out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(touch_rows).to_parquet(touch_out, index=False)
    pd.DataFrame(cov_rows).to_parquet(cov_out, index=False)
    attrition_df = pd.DataFrame(attrition).drop_duplicates(subset=["repo_id"], keep="last")
    attrition_df.to_csv(attrition_out, index=False)
    attrition = attrition_df.to_dict(orient="records")

    n_ok = sum(1 for a in attrition if a["status"] == "ok")
    n_skipped = len(attrition) - n_ok
    n_repos_touch = pd.DataFrame(touch_rows)["repo_id"].nunique()
    meta = {
        "discovered_path": str(discovered_path),
        "n_discovered": n_discovered,
        "n_extract_ok": n_ok,
        "n_extract_skipped": n_skipped,
        "n_repos_in_touch_history": int(n_repos_touch),
        "n_touch_rows": len(touch_rows),
        "attrition_out": str(attrition_out),
        "complete": len(attrition) == n_discovered,
    }
    meta_out.write_text(json.dumps(meta, indent=2) + "\n")

    print(f"touch history -> {touch_out} ({len(touch_rows)} rows, {n_repos_touch} repos)")
    print(f"repo covariates -> {cov_out} ({len(cov_rows)} repos)")
    print(f"extract meta -> {meta_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
