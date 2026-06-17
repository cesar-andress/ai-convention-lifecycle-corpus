#!/usr/bin/env python3
"""Feasibility pilot: GitHub Actions workflows on the fixed 209-repo cohort."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import numpy as np
import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.corpus_paths import configure

ROOT = configure()

from lifecycle.git_utils import repo_last_commit_ts, run_git

WORKFLOW_RE = re.compile(r"(^|/)\.github/workflows/.*\.ya?ml$")
T_PRIMARY = 180
PILOT_N = 20
PILOT_SEED = 42

FALSE_POSITIVE_HINTS = (
    "/examples/",
    "/example/",
    "/demo/",
    "/demos/",
    "/test/",
    "/tests/",
    "/fixtures/",
    "/vendor/",
    "/third_party/",
    "/node_modules/",
)


def list_workflow_head_files(repo_dir: Path) -> list[str]:
    """HEAD paths preserving leading dot on .github/ (list_head_files strips it)."""
    proc = run_git(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=repo_dir)
    if proc.returncode != 0:
        return []
    out: list[str] = []
    for raw in proc.stdout.splitlines():
        p = raw.strip().replace("\\", "/")
        if not p:
            continue
        if p.startswith("./"):
            p = p[2:]
        out.append(p)
    return out


def normalize_path(path: str) -> str:
    p = path.replace("\\", "/").strip()
    if p.startswith("./"):
        p = p[2:]
    return p


def is_workflow_path(path: str) -> bool:
    path = normalize_path(path)
    return bool(WORKFLOW_RE.search(path))


def false_positive_flags(path: str) -> list[str]:
    path = normalize_path(path)
    flags: list[str] = []
    if not path.startswith(".github/workflows/"):
        flags.append("nested_subtree")
    for hint in FALSE_POSITIVE_HINTS:
        if hint in f"/{path}":
            flags.append(f"under_{hint.strip('/')}")
    if path.count(".github/workflows/") > 1:
        flags.append("nested_workflows_dir")
    return flags


def discover_workflow_paths(repo_dir: Path) -> set[str]:
    paths: set[str] = set()
    for p in list_workflow_head_files(repo_dir):
        if is_workflow_path(p):
            paths.add(normalize_path(p))
    try:
        proc = run_git(
            [
                "git",
                "log",
                "--all",
                "--pretty=format:",
                "--name-only",
                "--diff-filter=AMR",
                "--",
                ".github/workflows",
            ],
            cwd=repo_dir,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        proc = None
    if proc and proc.returncode == 0:
        for line in proc.stdout.splitlines():
            p = normalize_path(line.strip())
            if p and is_workflow_path(p):
                paths.add(p)
    return paths


def path_touch_bounds(repo_dir: Path, path: str) -> tuple[datetime | None, datetime | None]:
    try:
        proc = run_git(
            ["git", "log", "--all", "--follow", "--format=%at", "--", path],
            cwd=repo_dir,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return None, None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None, None
    stamps = [int(x) for x in proc.stdout.splitlines() if x.strip().isdigit()]
    if not stamps:
        return None, None
    return (
        datetime.fromtimestamp(min(stamps), tz=timezone.utc),
        datetime.fromtimestamp(max(stamps), tz=timezone.utc),
    )


def analyze_repo(repo_id: str, repos_dir: Path, observation_end: datetime | None) -> dict:
    owner, repo = repo_id.split("/", 1)
    repo_dir = repos_dir / owner / repo
    if not (repo_dir / ".git").exists():
        return {"repo_id": repo_id, "status": "no_clone"}

    head_files = {normalize_path(p) for p in list_workflow_head_files(repo_dir)}
    obs_end = observation_end or repo_last_commit_ts(repo_dir)
    if obs_end is None:
        return {"repo_id": repo_id, "status": "no_observation_end"}

    paths = discover_workflow_paths(repo_dir)
    path_rows = []
    for path in sorted(paths):
        introduced_at, last_touch_at = path_touch_bounds(repo_dir, path)
        present = path in head_files
        follow_up = None
        mature_present = False
        if introduced_at is not None:
            follow_up = max(0, (obs_end - introduced_at).days)
            mature_present = present and follow_up >= T_PRIMARY
        fp_flags = false_positive_flags(path)
        path_rows.append(
            {
                "artifact_path": path,
                "present_in_head": present,
                "introduced_at": introduced_at.isoformat() if introduced_at else None,
                "last_touch_at": last_touch_at.isoformat() if last_touch_at else None,
                "follow_up_days": follow_up,
                f"mature_present_{T_PRIMARY}": mature_present,
                "false_positive_flags": fp_flags,
            }
        )

    n_head = sum(1 for r in path_rows if r["present_in_head"])
    n_mature = sum(1 for r in path_rows if r[f"mature_present_{T_PRIMARY}"])
    return {
        "repo_id": repo_id,
        "status": "ok",
        "observation_end": obs_end.isoformat(),
        "n_workflow_paths_ever": len(path_rows),
        "n_workflow_paths_head": n_head,
        "n_mature_present_paths": n_mature,
        "has_workflows_head": n_head > 0,
        "has_mature_present": n_mature > 0,
        "paths": path_rows,
    }


def cohort_ok() -> pd.DataFrame:
    attr = pd.read_csv(ROOT / "results/lifecycle/extract_attrition_v2.csv")
    ok = attr[attr["status"] == "ok"].copy()
    disc = pd.read_csv(ROOT / "data/lifecycle/discovered_v2.csv")
    pool = disc.set_index("repo_id")["seed_pool"].to_dict()
    ok["seed_pool"] = ok["repo_id"].map(pool).fillna("unknown")
    return ok


def select_pilot_repos(ok: pd.DataFrame, n: int, seed: int) -> list[str]:
    rng = np.random.default_rng(seed)
    chosen: list[str] = []
    pools = sorted(ok["seed_pool"].unique())
    per_pool = max(1, n // len(pools))
    for pool in pools:
        pool_ids = ok.loc[ok["seed_pool"] == pool, "repo_id"].tolist()
        k = min(per_pool, len(pool_ids))
        pick = rng.choice(pool_ids, size=k, replace=False).tolist()
        chosen.extend(pick)
    if len(chosen) < n:
        remaining = [r for r in ok["repo_id"].tolist() if r not in chosen]
        extra = rng.choice(remaining, size=min(n - len(chosen), len(remaining)), replace=False).tolist()
        chosen.extend(extra)
    return sorted(chosen[:n])


def aggregate_metrics(rows: list[dict]) -> dict:
    ok_rows = [r for r in rows if r.get("status") == "ok"]
    n_repos = len(ok_rows)
    adopted = [r for r in ok_rows if r["has_workflows_head"]]
    restricted = [r for r in ok_rows if r["has_mature_present"]]
    paths_per_repo = [r["n_workflow_paths_head"] for r in adopted]
    ever_per_repo = [r["n_workflow_paths_ever"] for r in ok_rows if r["n_workflow_paths_ever"] > 0]
    mature_paths = sum(r["n_mature_present_paths"] for r in ok_rows)
    all_paths = []
    fp_paths = []
    for r in ok_rows:
        for p in r["paths"]:
            all_paths.append(p)
            if p["false_positive_flags"]:
                fp_paths.append(p)
    head_counts = paths_per_repo or [0]
    return {
        "n_repos_analyzed": n_repos,
        "n_repos_with_workflows_head": len(adopted),
        "n_repos_with_mature_present": len(restricted),
        "n_mature_present_paths": mature_paths,
        "n_workflow_paths_head_total": sum(paths_per_repo),
        "median_workflow_paths_head_per_adopted_repo": float(median(paths_per_repo)) if paths_per_repo else 0.0,
        "median_workflow_paths_ever_per_repo_with_any": float(median(ever_per_repo)) if ever_per_repo else 0.0,
        "max_workflow_paths_head": max(head_counts),
        "max_workflow_paths_ever": max((r["n_workflow_paths_ever"] for r in ok_rows), default=0),
        "false_positive_path_count": len(fp_paths),
        "false_positive_examples": fp_paths[:15],
    }


def extrapolate(pilot: dict, full: dict, pilot_n: int, full_n: int) -> dict:
    scale = full_n / pilot_n if pilot_n else 1.0
    return {
        "scale_factor": scale,
        "from_pilot_linear": {
            "n_repos_with_workflows_head": round(pilot["n_repos_with_workflows_head"] * scale),
            "n_repos_with_mature_present": round(pilot["n_repos_with_mature_present"] * scale),
            "n_mature_present_paths": round(pilot["n_mature_present_paths"] * scale),
        },
        "from_full_cohort_direct": {
            "n_repos_with_workflows_head": full["n_repos_with_workflows_head"],
            "n_repos_with_mature_present": full["n_repos_with_mature_present"],
            "n_mature_present_paths": full["n_mature_present_paths"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-n", type=int, default=PILOT_N)
    parser.add_argument("--seed", type=int, default=PILOT_SEED)
    parser.add_argument("--full-cohort", action="store_true", help="Scan all 209 repos (default).")
    parser.add_argument("--pilot-only", action="store_true", help="Scan pilot sample only.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "gh_actions_pilot")
    args = parser.parse_args()

    ok = cohort_ok()
    pilot_ids = select_pilot_repos(ok, args.pilot_n, args.seed)
    repos_dir = ROOT / "data" / "repos"
    cov = pd.read_parquet(ROOT / "data" / "lifecycle" / "repo_covariates.parquet")
    obs_map = {
        rid: pd.Timestamp(row.observation_end).to_pydatetime().replace(tzinfo=timezone.utc)
        for rid, row in cov.set_index("repo_id").iterrows()
    }

    target_ids = pilot_ids if args.pilot_only else ok["repo_id"].tolist()
    rows: list[dict] = []
    for i, repo_id in enumerate(target_ids, 1):
        print(f"[{i}/{len(target_ids)}] {repo_id}", flush=True)
        try:
            rows.append(analyze_repo(repo_id, repos_dir, obs_map.get(repo_id)))
        except Exception as exc:  # noqa: BLE001
            rows.append({"repo_id": repo_id, "status": "error", "error": str(exc)})

    pilot_set = set(pilot_ids)
    pilot_rows = [r for r in rows if r.get("repo_id") in pilot_set]
    pilot_metrics = aggregate_metrics(pilot_rows)

    if args.pilot_only:
        full_metrics = None
        extrap = None
    else:
        full_metrics = aggregate_metrics(rows)
        extrap = extrapolate(pilot_metrics, full_metrics, len(pilot_ids), len(ok))

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pilot_repos.csv").write_text("repo_id\n" + "\n".join(pilot_ids) + "\n")
    (out_dir / "repo_metrics.json").write_text(json.dumps(rows, indent=2, default=str) + "\n")
    summary = {
        "family_regex": WORKFLOW_RE.pattern,
        "t_primary_days": T_PRIMARY,
        "pilot_n": len(pilot_ids),
        "pilot_repo_ids": pilot_ids,
        "pilot_metrics": pilot_metrics,
        "full_cohort_n": len(ok),
        "full_cohort_metrics": full_metrics,
        "extrapolation": extrap,
        "decision_thresholds": {
            "min_adopted_repos": 80,
            "min_restricted_repos": 40,
            "min_mature_present_paths": 150,
        },
    }
    (out_dir / "feasibility_summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
