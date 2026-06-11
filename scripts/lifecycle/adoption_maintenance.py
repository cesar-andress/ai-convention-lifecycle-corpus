#!/usr/bin/env python3
"""Compute adoption, maintenance, gap, and state machine metrics."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lifecycle.analyze import load_artifact_frame
from lifecycle.detection import load_config
from lifecycle.git_utils import GIT_ENV, list_head_files

DEFAULT_PROTOCOL = ROOT / "protocol" / "adoption_maintenance_v1.yaml"
DEFAULT_LIFECYCLE = ROOT / "protocol" / "lifecycle_v1.yaml"
THRESHOLDS = [90, 180, 365]
BOOTSTRAP_N = 5000


def load_am_config(path: Path) -> dict:
    import yaml

    with path.open() as f:
        return yaml.safe_load(f)


def enrich_present_in_head(df: pd.DataFrame, repos_dir: Path) -> pd.DataFrame:
    out = df.copy()
    head_cache: dict[str, set[str]] = {}

    def head_paths(repo_id: str) -> set[str] | None:
        if repo_id in head_cache:
            return head_cache[repo_id]
        owner, repo = repo_id.split("/", 1)
        repo_dir = repos_dir / owner / repo
        if not repo_dir.exists():
            head_cache[repo_id] = set()
            return None
        paths = set(list_head_files(repo_dir))
        head_cache[repo_id] = paths
        return paths

    present_flags: list[bool] = []
    for _, row in out.iterrows():
        paths = head_paths(row["repo_id"])
        if paths is None:
            present_flags.append(True)
        else:
            present_flags.append(row["artifact_path"] in paths)

    out["present_in_head"] = present_flags
    out["deleted"] = ~out["present_in_head"]
    return out


def days_since_last_touch(df: pd.DataFrame) -> pd.Series:
    return (df["observation_end"] - df["last_touch_at"]).dt.days.clip(lower=0)


def assign_state(row: pd.Series, t: int) -> str:
    if not row["present_in_head"]:
        return "DELETED"
    if row["follow_up_days"] < t:
        return "TOO_YOUNG"
    if row["days_since_last_touch"] < t:
        return "ACTIVE"
    return "DORMANT"


def add_states_and_flags(df: pd.DataFrame, thresholds: list[int]) -> pd.DataFrame:
    out = df.copy()
    out["days_since_last_touch"] = days_since_last_touch(out)
    ts = out["introduced_at"].dt.tz_convert("UTC").dt.tz_localize(None)
    out["introduced_at_quarter"] = ts.dt.to_period("Q").astype(str)

    for t in thresholds:
        out[f"state_{t}"] = out.apply(lambda r: assign_state(r, t), axis=1)
        out[f"mature_present_{t}"] = out["present_in_head"] & (out["follow_up_days"] >= t)
        out[f"maintained_{t}"] = out["present_in_head"] & (out["days_since_last_touch"] < t)
        out[f"adopted_{t}"] = out["present_in_head"]  # adoption = presence
    return out


def gap_artifact_mature(df: pd.DataFrame, t: int) -> dict:
    mature = df[df[f"mature_present_{t}"]]
    n = len(mature)
    if n == 0:
        return {"n_mature_present": 0, "n_active": 0, "n_dormant": 0, "gap_rate": None, "maintenance_rate": None}
    n_active = int((mature[f"state_{t}"] == "ACTIVE").sum())
    n_dormant = int((mature[f"state_{t}"] == "DORMANT").sum())
    return {
        "n_mature_present": n,
        "n_active": n_active,
        "n_dormant": n_dormant,
        "gap_rate": n_dormant / n,
        "maintenance_rate": n_active / n,
    }


def gap_repo_level(df: pd.DataFrame, t: int) -> dict:
    adopted_repos = df.groupby("repo_id")["present_in_head"].any()
    n_adopted = int(adopted_repos.sum())

    maintained = df.groupby("repo_id")[f"maintained_{t}"].any()
    n_maintained = int(maintained.sum())

    dormant_only = []
    for repo_id, grp in df.groupby("repo_id"):
        if not grp["present_in_head"].any():
            continue
        if grp[f"maintained_{t}"].any():
            continue
        if (grp[f"mature_present_{t}"] & (grp[f"state_{t}"] == "DORMANT")).any():
            dormant_only.append(repo_id)

    return {
        "n_repos_adopted": n_adopted,
        "n_repos_maintained": n_maintained,
        "n_repos_dormant_only": len(dormant_only),
        "gap_rate": (n_adopted - n_maintained) / n_adopted if n_adopted else None,
        "dormant_only_rate": len(dormant_only) / n_adopted if n_adopted else None,
    }


def table_by_type(df: pd.DataFrame, t: int, min_mature: int = 30) -> pd.DataFrame:
    rows = []
    for atype, grp in df.groupby("artifact_type", sort=True):
        g = gap_artifact_mature(grp, t)
        if g["n_mature_present"] < min_mature:
            continue
        rows.append(
            {
                "artifact_type": atype,
                "n_total": len(grp),
                "n_present": int(grp["present_in_head"].sum()),
                "n_deleted": int(grp["deleted"].sum()),
                f"n_mature_present_{t}": g["n_mature_present"],
                f"n_active_{t}": g["n_active"],
                f"n_dormant_{t}": g["n_dormant"],
                f"gap_rate_mature_{t}": g["gap_rate"],
                f"maintenance_rate_mature_{t}": g["maintenance_rate"],
            }
        )
    return pd.DataFrame(rows)


def table_by_cohort(df: pd.DataFrame, t: int) -> pd.DataFrame:
    rows = []
    for cohort, grp in df.groupby("introduced_at_quarter", sort=True):
        g = gap_artifact_mature(grp, t)
        rows.append(
            {
                "introduced_at_quarter": cohort,
                "n_total": len(grp),
                "n_present": int(grp["present_in_head"].sum()),
                f"n_mature_present_{t}": g["n_mature_present"],
                f"n_active_{t}": g["n_active"],
                f"n_dormant_{t}": g["n_dormant"],
                f"gap_rate_mature_{t}": g["gap_rate"],
                f"maintenance_rate_mature_{t}": g["maintenance_rate"],
            }
        )
    return pd.DataFrame(rows)


def table_repo_summary(df: pd.DataFrame, t: int) -> pd.DataFrame:
    rows = []
    for repo_id, grp in df.groupby("repo_id", sort=True):
        g = gap_artifact_mature(grp, t)
        rows.append(
            {
                "repo_id": repo_id,
                "n_artifacts": len(grp),
                "n_present": int(grp["present_in_head"].sum()),
                "n_deleted": int(grp["deleted"].sum()),
                f"n_mature_present_{t}": g["n_mature_present"],
                f"n_active_{t}": g["n_active"],
                f"n_dormant_{t}": g["n_dormant"],
                "repo_maintained": bool(grp[f"maintained_{t}"].any()),
                "repo_adopted": bool(grp["present_in_head"].any()),
            }
        )
    return pd.DataFrame(rows)


def build_funnel(df: pd.DataFrame, thresholds: list[int]) -> pd.DataFrame:
    rows = [
        {"stage": "ever_introduced", "threshold_days": "all", "count": len(df)},
        {"stage": "present_in_head", "threshold_days": "all", "count": int(df["present_in_head"].sum())},
        {"stage": "deleted", "threshold_days": "all", "count": int(df["deleted"].sum())},
    ]
    for t in thresholds:
        mature = df[df[f"mature_present_{t}"]]
        rows.append({"stage": "mature_present", "threshold_days": t, "count": len(mature)})
        rows.append({"stage": "active", "threshold_days": t, "count": int((mature[f"state_{t}"] == "ACTIVE").sum())})
        rows.append({"stage": "dormant", "threshold_days": t, "count": int((mature[f"state_{t}"] == "DORMANT").sum())})
        rows.append({"stage": "too_young", "threshold_days": t, "count": int((df[f"state_{t}"] == "TOO_YOUNG").sum())})
    return pd.DataFrame(rows)


def cluster_bootstrap_gap(df: pd.DataFrame, t: int, n: int = BOOTSTRAP_N, seed: int = 42) -> dict:
    repos = df["repo_id"].unique()
    groups = {r: df[df["repo_id"] == r] for r in repos}
    rng = np.random.default_rng(seed)

    gap_samples = []
    maint_samples = []
    for _ in range(n):
        sampled = rng.choice(repos, size=len(repos), replace=True)
        boot = pd.concat([groups[r] for r in sampled], ignore_index=True)
        g = gap_artifact_mature(boot, t)
        if g["gap_rate"] is not None:
            gap_samples.append(g["gap_rate"])
            maint_samples.append(g["maintenance_rate"])

    def ci(arr):
        if not arr:
            return None, None
        return float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))

    obs = gap_artifact_mature(df, t)
    lo, hi = ci(gap_samples)
    mlo, mhi = ci(maint_samples)
    return {
        "threshold_days": t,
        "observed_gap_rate_mature": obs["gap_rate"],
        "observed_maintenance_rate_mature": obs["maintenance_rate"],
        "gap_rate_ci_95": {"low": lo, "high": hi},
        "maintenance_rate_ci_95": {"low": mlo, "high": mhi},
        "n_bootstrap": len(gap_samples),
    }


def leave_one_repo_out(df: pd.DataFrame, t: int) -> list[dict]:
    full = gap_artifact_mature(df, t)
    rows = []
    for repo_id in sorted(df["repo_id"].unique()):
        sub = df[df["repo_id"] != repo_id]
        g = gap_artifact_mature(sub, t)
        rows.append(
            {
                "repo_id": repo_id,
                "gap_rate_mature": g["gap_rate"],
                "delta_gap_vs_full": (g["gap_rate"] - full["gap_rate"]) if g["gap_rate"] is not None else None,
                "maintenance_rate_mature": g["maintenance_rate"],
            }
        )
    return rows


def compute_all(
    df: pd.DataFrame,
    thresholds: list[int],
    primary: int = 180,
    min_type: int = 30,
) -> dict:
    df = add_states_and_flags(df, thresholds)

    by_threshold = {str(t): {"artifact": gap_artifact_mature(df, t), "repo": gap_repo_level(df, t)} for t in thresholds}
    bootstrap = {str(t): cluster_bootstrap_gap(df, t) for t in thresholds}

    primary_states = df[f"state_{primary}"].value_counts().to_dict()
    ever = len(df)
    present = int(df["present_in_head"].sum())

    return {
        "n_repos": int(df["repo_id"].nunique()),
        "n_artifacts_ever_introduced": ever,
        "n_artifacts_present_in_head": present,
        "n_artifacts_deleted": int(df["deleted"].sum()),
        "primary_threshold_days": primary,
        f"state_counts_{primary}": primary_states,
        "by_threshold": by_threshold,
        "cluster_bootstrap": bootstrap,
        "leave_one_repo_out_gap_mature": leave_one_repo_out(df, primary),
        "adoption_repo_rate": float(df.groupby("repo_id")["present_in_head"].any().mean()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--lifecycle-config", type=Path, default=DEFAULT_LIFECYCLE)
    parser.add_argument("--repos-dir", type=Path, default=ROOT / "data" / "repos")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "lifecycle")
    args = parser.parse_args()

    am_cfg = load_am_config(args.protocol)
    lc_cfg = load_config(str(args.lifecycle_config))
    primary = int(am_cfg["maintenance_windows_days"]["primary"])
    min_type = int(am_cfg["gap"]["by_artifact_type"]["min_mature_present_T"])

    artifacts_path = ROOT / lc_cfg["outputs"]["artifacts"]
    touch_path = ROOT / lc_cfg["outputs"]["touch_history"]
    df = load_artifact_frame(artifacts_path, touch_path)
    df = enrich_present_in_head(df, args.repos_dir)

    results = compute_all(df, THRESHOLDS, primary=primary, min_type=min_type)
    df_out = add_states_and_flags(df, THRESHOLDS)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    states_path = ROOT / am_cfg["outputs"]["artifact_states"]
    states_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_parquet(states_path, index=False)

    (out_dir / "adoption_maintenance.json").write_text(json.dumps(results, indent=2, default=str) + "\n")
    table_by_type(df_out, primary, min_type).to_csv(out_dir / "table_gap_by_type.csv", index=False)
    table_by_cohort(df_out, primary).to_csv(out_dir / "table_gap_by_cohort.csv", index=False)
    table_repo_summary(df_out, primary).to_csv(out_dir / "table_repo_summary.csv", index=False)
    build_funnel(df_out, THRESHOLDS).to_csv(out_dir / "funnel_adoption_maintenance.csv", index=False)

    print(json.dumps(results, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
