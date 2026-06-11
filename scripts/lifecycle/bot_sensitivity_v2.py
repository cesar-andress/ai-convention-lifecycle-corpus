#!/usr/bin/env python3
"""Bot-touch sensitivity: recompute headline gaps after excluding automation commits."""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.adoption_maintenance import (
    add_states_and_flags,
    gap_artifact_mature,
    gap_repo_level,
)
from lifecycle.adoption_maintenance_v2 import headline_metrics
from lifecycle.build_dataset import (
    follow_up_days,
    survival_time_days,
    threshold_metrics,
)
from lifecycle.corpus_paths import configure
from lifecycle.detection import is_conservative_automation_bot
from lifecycle.git_utils import run_git

ROOT = configure()
DEFAULT_DISCOVERED = ROOT / "data" / "lifecycle" / "discovered_v2.csv"
DEFAULT_TOUCH = ROOT / "data" / "lifecycle" / "touch_history.parquet"
DEFAULT_ARTIFACTS = ROOT / "data" / "lifecycle" / "artifacts_full.parquet"
DEFAULT_STATES = ROOT / "data" / "lifecycle" / "artifact_states_v2.parquet"
DEFAULT_REPOS = ROOT / "data" / "repos"
DEFAULT_CACHE = ROOT / "data" / "lifecycle" / "commit_authors.parquet"
DEFAULT_OUT = ROOT / "results" / "lifecycle" / "bot_sensitivity_v2.json"
THRESHOLDS = [90, 180, 365]
PRIMARY_T = 180
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")


def clone_repo_history(url: str, dest: Path, timeout: int = 300) -> bool:
    if dest.exists():
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone", "--filter=blob:none", "--quiet", url, str(dest)]
    try:
        proc = run_git(cmd, timeout=timeout)
    except Exception:
        return False
    return proc.returncode == 0


def commit_authors_for_commits(repo_dir: Path, commits: set[str]) -> pd.DataFrame:
    rows: list[dict] = []
    for sha in sorted(commits):
        proc = run_git(
            ["git", "show", "-s", "--format=%H|%an|%ae", sha],
            cwd=repo_dir,
            timeout=60,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            continue
        parts = proc.stdout.strip().split("|", 2)
        if len(parts) != 3:
            continue
        rows.append({"commit": parts[0], "author": parts[1], "email": parts[2]})
    return pd.DataFrame(rows)


def commit_authors_for_repo(repo_dir: Path) -> pd.DataFrame:
    proc = run_git(
        ["git", "log", "--all", "--pretty=format:%H|%an|%ae"],
        cwd=repo_dir,
        timeout=300,
    )
    rows: list[dict] = []
    if proc.returncode != 0:
        return pd.DataFrame(columns=["commit", "author", "email"])
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        rows.append({"commit": parts[0], "author": parts[1], "email": parts[2]})
    return pd.DataFrame(rows)


def repo_author_rows(
    repo_id: str,
    repo_dir: Path,
    commits: set[str],
) -> pd.DataFrame:
    authors = commit_authors_for_commits(repo_dir, commits)
    if authors.empty:
        return pd.DataFrame(columns=["repo_id", "commit", "author", "email"])
    sub = authors.copy()
    sub["repo_id"] = repo_id
    return sub


def build_author_cache(
    touch_df: pd.DataFrame,
    discovered: pd.DataFrame,
    repos_dir: Path,
    cache_path: Path,
    *,
    clone_timeout: int = 180,
    workers: int = 6,
) -> pd.DataFrame:
    if cache_path.exists():
        cache = pd.read_parquet(cache_path)
    else:
        cache = pd.DataFrame(columns=["repo_id", "commit", "author", "email"])

    url_map = discovered.set_index("repo_id")["repo_url"].to_dict()
    commits_by_repo = {
        repo_id: set(touch_df.loc[touch_df["repo_id"] == repo_id, "commit"].unique())
        for repo_id in touch_df["repo_id"].unique()
    }
    cached_pairs = set(zip(cache["repo_id"], cache["commit"])) if len(cache) else set()
    needed_repos = [
        repo_id
        for repo_id, commits in commits_by_repo.items()
        if not all((repo_id, c) in cached_pairs for c in commits)
    ]

    def missing_commits(repo_id: str) -> set[str]:
        commits = commits_by_repo[repo_id]
        if not cached_pairs:
            return commits
        return {c for c in commits if (repo_id, c) not in cached_pairs}

    def process_repo(repo_id: str) -> pd.DataFrame:
        owner, repo = repo_id.split("/", 1)
        repo_dir = repos_dir / owner / repo
        if not repo_dir.exists():
            url = url_map.get(repo_id)
            if not url or not clone_repo_history(url, repo_dir, timeout=clone_timeout):
                print(f"warning: could not clone {repo_id}", file=sys.stderr)
                return pd.DataFrame(columns=["repo_id", "commit", "author", "email"])
        return repo_author_rows(repo_id, repo_dir, missing_commits(repo_id))

    frames = [cache] if len(cache) else []
    if needed_repos:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(process_repo, repo_id): repo_id for repo_id in needed_repos}
            for fut in as_completed(futures):
                repo_id = futures[fut]
                try:
                    sub = fut.result()
                except Exception as exc:  # pragma: no cover - network/git failures
                    print(f"warning: author lookup failed for {repo_id}: {exc}", file=sys.stderr)
                    continue
                if not sub.empty:
                    frames.append(sub)
                    partial = pd.concat(frames, ignore_index=True).drop_duplicates(["repo_id", "commit"])
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    partial.to_parquet(cache_path, index=False)
                    frames = [partial]

    if not frames:
        cache = pd.DataFrame(columns=["repo_id", "commit", "author", "email"])
        return cache

    return pd.concat(frames, ignore_index=True).drop_duplicates(["repo_id", "commit"])


def fetch_commit_author_api(owner: str, repo: str, sha: str) -> tuple[str, str] | None:
    import subprocess

    try:
        proc = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{owner}/{repo}/commits/{sha}",
                "--jq",
                '.commit.author.name + "|" + (.commit.author.email // "")',
            ],
            capture_output=True,
            text=True,
            timeout=45,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if proc.returncode != 0 or "|" not in proc.stdout.strip():
        return None
    author, email = proc.stdout.strip().split("|", 1)
    return author, email


def enrich_missing_authors_api(
    touch_df: pd.DataFrame,
    cache: pd.DataFrame,
    *,
    cache_path: Path,
) -> pd.DataFrame:
    known = set(zip(cache["repo_id"], cache["commit"]))
    need = touch_df[["repo_id", "commit"]].drop_duplicates()
    need = need[
        ~need.apply(lambda r: (r["repo_id"], r["commit"]) in known, axis=1)
    ]
    if need.empty:
        return cache

    rows: list[dict] = []
    for i, row in enumerate(need.itertuples(index=False), start=1):
        owner, repo = row.repo_id.split("/", 1)
        got = fetch_commit_author_api(owner, repo, row.commit)
        if got:
            author, email = got
            rows.append(
                {
                    "repo_id": row.repo_id,
                    "commit": row.commit,
                    "author": author,
                    "email": email,
                }
            )
        if i % 100 == 0 and rows:
            partial = pd.concat([cache, pd.DataFrame(rows)], ignore_index=True).drop_duplicates(
                ["repo_id", "commit"]
            )
            partial.to_parquet(cache_path, index=False)
            cache = partial
            rows = []

    if rows:
        cache = pd.concat([cache, pd.DataFrame(rows)], ignore_index=True).drop_duplicates(
            ["repo_id", "commit"]
        )
        cache.to_parquet(cache_path, index=False)
    return cache


def attach_authors(touch_df: pd.DataFrame, cache: pd.DataFrame) -> pd.DataFrame:
    out = touch_df.merge(cache, on=["repo_id", "commit"], how="left")
    out["author"] = out["author"].fillna("")
    out["email"] = out["email"].fillna("")
    return out


def build_artifacts_bot_filtered(touch_df: pd.DataFrame, thresholds: list[int]) -> pd.DataFrame:
    rows: list[dict] = []
    grouped = touch_df.groupby(["repo_id", "artifact_type", "artifact_path"], sort=True)

    for (repo_id, artifact_type, artifact_path), grp in grouped:
        grp = grp.sort_values("committed_at")
        introduced_at = grp["committed_at"].iloc[0]
        observation_end = grp["observation_end"].iloc[-1]
        obs_end = observation_end

        bot_mask = grp.apply(
            lambda r: is_conservative_automation_bot(str(r["author"]), str(r["email"])),
            axis=1,
        )
        human = grp[~bot_mask]

        if human.empty:
            last_touch_at = EPOCH
            touch_count = 0
            first_after = pd.NaT
        else:
            last_touch_at = human["committed_at"].iloc[-1]
            touch_count = len(human)
            first_after = human["committed_at"].iloc[1] if touch_count > 1 else pd.NaT

        row = {
            "repo_id": repo_id,
            "artifact_type": artifact_type,
            "artifact_path": artifact_path,
            "introduced_at": introduced_at,
            "last_touch_at": last_touch_at,
            "observation_end": obs_end,
            "follow_up_days": follow_up_days(introduced_at, obs_end),
            "touch_count": touch_count,
            "active_days": max(0, (last_touch_at - introduced_at).days) if touch_count else 0,
            "first_touch_after_intro": first_after,
        }

        for th in thresholds:
            row.update(threshold_metrics(introduced_at, last_touch_at, obs_end, th))
            dur, event = survival_time_days(introduced_at, last_touch_at, obs_end, th)
            row[f"survival_days_{th}"] = dur
            row[f"survival_event_{th}"] = event

        rows.append(row)

    return pd.DataFrame(rows)


def merge_present_in_head(df: pd.DataFrame, artifact_states: pd.DataFrame) -> pd.DataFrame:
    keys = artifact_states[["repo_id", "artifact_path", "present_in_head"]].drop_duplicates()
    out = df.merge(keys, on=["repo_id", "artifact_path"], how="left")
    out["present_in_head"] = out["present_in_head"].fillna(True)
    out["deleted"] = ~out["present_in_head"]
    return out


def bot_touch_stats(touch_df: pd.DataFrame) -> dict:
    known = touch_df["author"].astype(str).str.len().gt(0)
    scoped = touch_df[known]
    bot_mask = scoped.apply(
        lambda r: is_conservative_automation_bot(str(r["author"]), str(r["email"])),
        axis=1,
    )
    return {
        "n_touch_rows": int(len(touch_df)),
        "n_touch_rows_with_author": int(len(scoped)),
        "author_lookup_coverage": float(len(scoped) / len(touch_df)) if len(touch_df) else 0.0,
        "n_bot_touch_rows": int(bot_mask.sum()),
        "bot_touch_share_among_known": float(bot_mask.mean()) if len(scoped) else 0.0,
    }


def compute_bot_filtered_gaps(
    touch_df: pd.DataFrame,
    artifact_states: pd.DataFrame,
    *,
    t: int = PRIMARY_T,
) -> dict:
    df = build_artifacts_bot_filtered(touch_df, THRESHOLDS)
    df = merge_present_in_head(df, artifact_states)
    df = add_states_and_flags(df, THRESHOLDS)
    return headline_metrics(df, t)


def sensitivity_summary(original: dict, filtered: dict, stats: dict) -> dict:
    orig_art = float(original["artifact_gap_mature"]) * 100
    orig_repo = float(original["repo_gap"]) * 100
    filt_art = float(filtered["artifact_gap_mature"]) * 100
    filt_repo = float(filtered["repo_gap"]) * 100
    return {
        "threshold_days": PRIMARY_T,
        "bot_filter_rules": [
            "dependabot",
            "renovate",
            "github-actions",
            "pre-commit-ci",
            "bot[bot]",
            "bot@",
        ],
        "touch_stats": stats,
        "original": {
            "artifact_gap_pct": round(orig_art, 1),
            "repo_gap_pct": round(orig_repo, 1),
        },
        "bot_filtered": {
            "artifact_gap_pct": round(filt_art, 1),
            "repo_gap_pct": round(filt_repo, 1),
        },
        "absolute_difference_pp": {
            "artifact_gap": round(abs(filt_art - orig_art), 1),
            "repo_gap": round(abs(filt_repo - orig_repo), 1),
        },
        "headline_180_original": original,
        "headline_180_bot_filtered": filtered,
        "substantively_unchanged": (
            abs(filt_art - orig_art) < 5.0 and abs(filt_repo - orig_repo) < 5.0
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--discovered", type=Path, default=DEFAULT_DISCOVERED)
    parser.add_argument("--touch-history", type=Path, default=DEFAULT_TOUCH)
    parser.add_argument("--artifacts-full", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--artifact-states", type=Path, default=DEFAULT_STATES)
    parser.add_argument("--repos-dir", type=Path, default=DEFAULT_REPOS)
    parser.add_argument("--author-cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--summary-json", type=Path, default=ROOT / "results/lifecycle/adoption_maintenance_v2.json")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--skip-api-enrichment", action="store_true")
    args = parser.parse_args()

    touch_df = pd.read_parquet(args.touch_history)
    for col in ("committed_at", "observation_end"):
        touch_df[col] = pd.to_datetime(touch_df[col], utc=True)

    if "author" not in touch_df.columns or "email" not in touch_df.columns:
        discovered = pd.read_csv(args.discovered)
        cache = build_author_cache(touch_df, discovered, args.repos_dir, args.author_cache)
        if not args.skip_api_enrichment:
            cache = enrich_missing_authors_api(touch_df, cache, cache_path=args.author_cache)
        touch_df = attach_authors(touch_df, cache)
    else:
        touch_df["author"] = touch_df["author"].fillna("")
        touch_df["email"] = touch_df["email"].fillna("")

    artifacts_full = pd.read_parquet(args.artifacts_full)
    artifact_states = pd.read_parquet(args.artifact_states)
    for col in ("introduced_at", "last_touch_at", "observation_end"):
        if col in artifacts_full.columns:
            artifacts_full[col] = pd.to_datetime(artifacts_full[col], utc=True)

    summary_src = json.loads(args.summary_json.read_text())
    original = summary_src["headline_primary_180"]
    filtered = compute_bot_filtered_gaps(touch_df, artifact_states, t=PRIMARY_T)
    stats = bot_touch_stats(touch_df)
    out = sensitivity_summary(original, filtered, stats)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
