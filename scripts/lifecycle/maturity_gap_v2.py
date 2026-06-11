#!/usr/bin/env python3
"""Exploratory adoption-maintenance gap by repository maturity tier (v2 corpus)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.adoption_maintenance import gap_artifact_mature, gap_repo_level
from lifecycle.corpus_paths import configure

ROOT = configure()

DEFAULT_STATES = ROOT / "data" / "lifecycle" / "artifact_states_v2.parquet"
DEFAULT_COV = ROOT / "data" / "lifecycle" / "repo_covariates.parquet"
DEFAULT_TOUCH = ROOT / "data" / "lifecycle" / "touch_history.parquet"
DEFAULT_OUT_JSON = ROOT / "results" / "lifecycle" / "maturity_gap_v2.json"
DEFAULT_OUT_CSV = ROOT / "results" / "lifecycle" / "maturity_gap_v2.csv"

THRESHOLD = 180
BOOTSTRAP_N = 5000
BOOTSTRAP_SEED = 42
MIN_REPOS_TIER = 20
MIN_MATURE_TIER = 30


def touch_repo_features(touch: pd.DataFrame) -> pd.DataFrame:
    """Per-repo activity breadth from AI-artifact touch history."""
    g = touch.groupby("repo_id", sort=True)
    return pd.DataFrame(
        {
            "repo_id": g.size().index,
            "n_ai_touch_commits": g["commit"].nunique().values,
            "ai_touch_span_days": (
                g["committed_at"].max().values - g["committed_at"].min().values
            ).astype("timedelta64[D]").astype(int),
        }
    )


def build_maturity_frame(
    cov: pd.DataFrame,
    touch: pd.DataFrame,
    states: pd.DataFrame,
) -> pd.DataFrame:
    """Composite maturity score from frozen extract covariates + touch breadth."""
    touch_feat = touch_repo_features(touch)

    # Repository-age proxy: span from earliest artifact introduction to observation end.
    intro = (
        states.groupby("repo_id")["introduced_at"]
        .min()
        .rename("first_artifact_intro")
    )
    obs = cov.set_index("repo_id")["observation_end"]
    age = (
        obs.reindex(intro.index)
        - intro.reindex(obs.index)
    ).dt.days.rename("repo_age_proxy_days")

    frame = cov.merge(touch_feat, on="repo_id", how="left").set_index("repo_id")
    frame["repo_age_proxy_days"] = age.reindex(frame.index)
    frame["ci_present"] = (frame["ci_rate"].fillna(0) > 0).astype(float)
    frame["log_commit_volume"] = frame["log_commit_volume"].fillna(0)
    frame["log_repo_files"] = frame["log_repo_files"].fillna(0)
    frame["n_ai_touch_commits"] = frame["n_ai_touch_commits"].fillna(0)
    frame["ai_touch_span_days"] = frame["ai_touch_span_days"].fillna(0).clip(lower=0)

    components = {
        "commit_volume": frame["commit_volume"],
        "repo_files": frame["n_repo_files"],
        "ci_present": frame["ci_present"],
    }
    ranks = {k: s.rank(pct=True, method="average") for k, s in components.items()}
    # Equal-weight composite over full-repository covariates available offline.
    frame["maturity_score"] = pd.DataFrame(ranks).mean(axis=1)
    frame["maturity_tier"] = pd.qcut(
        frame["maturity_score"],
        q=3,
        labels=["Low", "Medium", "High"],
    )
    return frame.reset_index()


def tier_bootstrap(
    df: pd.DataFrame,
    repo_ids: np.ndarray,
    t: int,
    n: int,
    seed: int,
) -> dict:
    rng = np.random.default_rng(seed)
    groups = {r: df[df["repo_id"] == r] for r in repo_ids}
    art_samples: list[float] = []
    repo_samples: list[float] = []
    for _ in range(n):
        picked = rng.choice(repo_ids, size=len(repo_ids), replace=True)
        boot = pd.concat([groups[r] for r in picked], ignore_index=True)
        ag = gap_artifact_mature(boot, t)
        rg = gap_repo_level(boot, t)
        if ag["gap_rate"] is not None:
            art_samples.append(ag["gap_rate"])
        if rg["gap_rate"] is not None:
            repo_samples.append(rg["gap_rate"])

    def ci(samples: list[float], obs: float | None) -> dict:
        if not samples:
            return {"observed": obs, "ci_95": {"low": None, "high": None}, "n_bootstrap": 0}
        arr = np.array(samples)
        return {
            "observed": obs,
            "ci_95": {"low": float(np.percentile(arr, 2.5)), "high": float(np.percentile(arr, 97.5))},
            "n_bootstrap": len(samples),
        }

    obs_art = gap_artifact_mature(df[df["repo_id"].isin(repo_ids)], t)["gap_rate"]
    obs_repo = gap_repo_level(df[df["repo_id"].isin(repo_ids)], t)["gap_rate"]
    return {
        "artifact_gap_mature": ci(art_samples, obs_art),
        "repo_gap": ci(repo_samples, obs_repo),
    }


def analyze_tiers(df: pd.DataFrame, maturity: pd.DataFrame, t: int) -> dict:
    merged = maturity[["repo_id", "maturity_score", "maturity_tier"]].merge(
        df[["repo_id"]].drop_duplicates(),
        on="repo_id",
        how="inner",
    )
    out: dict = {
        "threshold_days": t,
        "score_components": [
            "commit_volume (full extracted history)",
            "n_repo_files at HEAD at extract",
            "ci_present (ci_rate > 0 from full-repo commit file touches)",
        ],
        "omitted_components": [
            "repository_age (first-commit date not retained in frozen extract)",
            "contributor_count",
            "release_activity",
            "governance_files (CONTRIBUTING, CODEOWNERS, SECURITY)",
        ],
        "omitted_reason": "Not retained in frozen v2 extract; composite uses offline covariates only.",
        "tiers": {},
        "stability": {},
    }

    tier_rows = []
    stable = True
    for tier in ["Low", "Medium", "High"]:
        repos = merged.loc[merged["maturity_tier"] == tier, "repo_id"].values
        sub = df[df["repo_id"].isin(repos)]
        art = gap_artifact_mature(sub, t)
        repo = gap_repo_level(sub, t)
        boot = tier_bootstrap(sub, repos, t, BOOTSTRAP_N, BOOTSTRAP_SEED + hash(tier) % 1000)

        tier_ok = len(repos) >= MIN_REPOS_TIER and art["n_mature_present"] >= MIN_MATURE_TIER
        if not tier_ok:
            stable = False

        row = {
            "maturity_tier": tier,
            "n_repos": int(len(repos)),
            "n_mature_present": art["n_mature_present"],
            "n_active": art["n_active"],
            "n_dormant": art["n_dormant"],
            "artifact_gap_mature": art["gap_rate"],
            "repo_gap": repo["gap_rate"],
            "artifact_gap_ci_95_low": boot["artifact_gap_mature"]["ci_95"]["low"],
            "artifact_gap_ci_95_high": boot["artifact_gap_mature"]["ci_95"]["high"],
            "repo_gap_ci_95_low": boot["repo_gap"]["ci_95"]["low"],
            "repo_gap_ci_95_high": boot["repo_gap"]["ci_95"]["high"],
            "tier_stable": tier_ok,
        }
        tier_rows.append(row)
        out["tiers"][tier] = {
            "n_repos": row["n_repos"],
            "artifact": art,
            "repo": repo,
            "bootstrap": boot,
            "tier_stable": tier_ok,
        }

    out["tier_table"] = tier_rows
    out["stability"] = {
        "all_tiers_meet_minima": stable,
        "min_repos_per_tier": MIN_REPOS_TIER,
        "min_mature_present_per_tier": MIN_MATURE_TIER,
        "artifact_gap_range_pp": _pp_range([r["artifact_gap_mature"] for r in tier_rows]),
        "repo_gap_range_pp": _pp_range([r["repo_gap"] for r in tier_rows]),
    }
    return out


def _pp_range(rates: list[float | None]) -> float | None:
    vals = [r for r in rates if r is not None]
    if len(vals) < 2:
        return None
    return round(100 * (max(vals) - min(vals)), 1)


def loo_max_shift(df: pd.DataFrame, maturity: pd.DataFrame, t: int) -> dict:
    """Leave-one-repo-out max shift within each tier (artifact gap)."""
    shifts: dict[str, float] = {}
    for tier in ["Low", "Medium", "High"]:
        repos = maturity.loc[maturity["maturity_tier"] == tier, "repo_id"].tolist()
        if len(repos) < 3:
            shifts[tier] = float("nan")
            continue
        base = gap_artifact_mature(df[df["repo_id"].isin(repos)], t)["gap_rate"]
        max_delta = 0.0
        for rid in repos:
            sub = df[(df["repo_id"].isin(repos)) & (df["repo_id"] != rid)]
            g = gap_artifact_mature(sub, t)["gap_rate"]
            if base is not None and g is not None:
                max_delta = max(max_delta, abs(g - base))
        shifts[tier] = round(100 * max_delta, 1)
    return shifts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--states", type=Path, default=DEFAULT_STATES)
    parser.add_argument("--covariates", type=Path, default=DEFAULT_COV)
    parser.add_argument("--touch", type=Path, default=DEFAULT_TOUCH)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--threshold", type=int, default=THRESHOLD)
    args = parser.parse_args()

    states = pd.read_parquet(args.states)
    cov = pd.read_parquet(args.covariates)
    touch = pd.read_parquet(args.touch)

    maturity = build_maturity_frame(cov, touch, states)
    result = analyze_tiers(states, maturity, args.threshold)
    result["loo_max_artifact_gap_shift_pp"] = loo_max_shift(states, maturity, args.threshold)
    result["maturity_score_summary"] = {
        "mean": float(maturity["maturity_score"].mean()),
        "min": float(maturity["maturity_score"].min()),
        "max": float(maturity["maturity_score"].max()),
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2, default=str) + "\n")

    tier_df = pd.DataFrame(result["tier_table"])
    maturity_out = maturity[
        [
            "repo_id",
            "commit_volume",
            "n_repo_files",
            "repo_age_proxy_days",
            "n_ai_touch_commits",
            "ci_present",
            "maturity_score",
            "maturity_tier",
        ]
    ]
    tier_df.to_csv(args.out_csv, index=False)
    maturity_out.to_csv(args.out_csv.with_name("maturity_scores_v2.csv"), index=False)

    print(json.dumps(result["stability"], indent=2))
    print(json.dumps(result["tier_table"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
