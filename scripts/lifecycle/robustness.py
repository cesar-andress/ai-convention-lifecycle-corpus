#!/usr/bin/env python3
"""Cluster bootstrap, leave-one-repo-out, funnel, and type table for lifecycle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lifecycle.analyze import _median_from_step, load_artifact_frame, pooled_median_survival
from lifecycle.detection import load_config

DEFAULT_CONFIG = ROOT / "protocol" / "lifecycle_v1.yaml"
PRIMARY = 180
BOOTSTRAP_REPLICATES = 5000
MIN_ELIGIBLE_TYPE = 30
RESULTS_DIR = ROOT / "results" / "lifecycle"


def metric_columns(threshold: int = PRIMARY) -> tuple[str, str, str]:
    return f"eligible_{threshold}", f"event_stasis_{threshold}", f"survival_days_{threshold}"


def stasis_rate_eligible(df: pd.DataFrame, threshold: int = PRIMARY) -> float | None:
    elig_col, event_col, _ = metric_columns(threshold)
    elig = df[df[elig_col]]
    if elig.empty:
        return None
    return float(elig[event_col].mean())


def median_survival_eligible(df: pd.DataFrame, threshold: int = PRIMARY) -> float | None:
    elig_col, event_col, duration_col = metric_columns(threshold)
    return pooled_median_survival(df, duration_col, event_col, elig_col)


def cluster_bootstrap(
    df: pd.DataFrame,
    *,
    n_replicates: int = BOOTSTRAP_REPLICATES,
    seed: int = 42,
    threshold: int = PRIMARY,
) -> dict:
    elig_col, event_col, duration_col = metric_columns(threshold)
    repo_ids = df["repo_id"].unique()
    groups = {rid: df[df["repo_id"] == rid] for rid in repo_ids}

    rng = np.random.default_rng(seed)
    rate_samples: list[float] = []
    median_samples: list[float] = []

    for _ in range(n_replicates):
        sampled = rng.choice(repo_ids, size=len(repo_ids), replace=True)
        boot = pd.concat([groups[r] for r in sampled], ignore_index=True)
        elig = boot[boot[elig_col]]
        if elig.empty:
            continue
        rate_samples.append(float(elig[event_col].mean()))
        med = pooled_median_survival(boot, duration_col, event_col, elig_col)
        if med is not None:
            median_samples.append(float(med))

    rate_arr = np.array(rate_samples)
    median_arr = np.array(median_samples)

    def ci(arr: np.ndarray) -> dict:
        if len(arr) == 0:
            return {"point": None, "ci_low": None, "ci_high": None, "n_replicates": 0}
        return {
            "point": float(np.mean(arr)),
            "ci_low": float(np.percentile(arr, 2.5)),
            "ci_high": float(np.percentile(arr, 97.5)),
            "n_replicates": int(len(arr)),
        }

    full_rate = stasis_rate_eligible(df, threshold)
    full_median = median_survival_eligible(df, threshold)

    return {
        "method": "cluster_bootstrap_by_repo_id",
        "n_replicates_requested": n_replicates,
        "n_repos": int(len(repo_ids)),
        "threshold_days": threshold,
        "stasis_rate_eligible": {
            "observed": full_rate,
            "bootstrap_mean": ci(rate_arr)["point"],
            "ci_95": {
                "low": ci(rate_arr)["ci_low"],
                "high": ci(rate_arr)["ci_high"],
            },
            "n_successful_replicates": ci(rate_arr)["n_replicates"],
        },
        "median_survival_pooled": {
            "observed": full_median,
            "bootstrap_mean": ci(median_arr)["point"],
            "ci_95": {
                "low": ci(median_arr)["ci_low"],
                "high": ci(median_arr)["ci_high"],
            },
            "n_successful_replicates": ci(median_arr)["n_replicates"],
        },
    }


def leave_one_repo_out(df: pd.DataFrame, threshold: int = PRIMARY) -> dict:
    full_rate = stasis_rate_eligible(df, threshold)
    full_median = median_survival_eligible(df, threshold)
    rows: list[dict] = []

    for repo_id in sorted(df["repo_id"].unique()):
        subset = df[df["repo_id"] != repo_id]
        rate = stasis_rate_eligible(subset, threshold)
        median = median_survival_eligible(subset, threshold)
        elig_col, event_col, _ = metric_columns(threshold)
        n_removed = int((df["repo_id"] == repo_id).sum())
        n_elig_removed = int(df.loc[df["repo_id"] == repo_id, elig_col].sum())

        rows.append(
            {
                "repo_id": repo_id,
                "n_artifacts_removed": n_removed,
                "n_eligible_180_removed": n_elig_removed,
                "stasis_180_rate_eligible": rate,
                "delta_rate_vs_full": (rate - full_rate) if rate is not None and full_rate is not None else None,
                "median_survival_pooled": median,
                "delta_median_vs_full": (median - full_median)
                if median is not None and full_median is not None
                else None,
            }
        )

    loo_df = pd.DataFrame(rows)
    influential_rate = loo_df.reindex(
        loo_df["delta_rate_vs_full"].abs().sort_values(ascending=False).index
    ).head(5)
    influential_median = loo_df.reindex(
        loo_df["delta_median_vs_full"].abs().sort_values(ascending=False).index
    ).head(5)

    return {
        "threshold_days": threshold,
        "full_sample": {
            "stasis_180_rate_eligible": full_rate,
            "median_survival_pooled": full_median,
        },
        "by_repo": rows,
        "influential_by_rate": influential_rate.to_dict(orient="records"),
        "influential_by_median": influential_median.to_dict(orient="records"),
    }


def build_funnel(df: pd.DataFrame, thresholds: list[int]) -> pd.DataFrame:
    rows = [{"stage": "total_artifacts", "threshold_days": "all", "count": len(df)}]
    for th in thresholds:
        elig_col = f"eligible_{th}"
        event_col = f"event_stasis_{th}"
        rows.append({"stage": "eligible", "threshold_days": th, "count": int(df[elig_col].sum())})
        rows.append({"stage": "stasis_events", "threshold_days": th, "count": int(df[event_col].sum())})
    return pd.DataFrame(rows)


def build_type_table(df: pd.DataFrame, threshold: int = PRIMARY, min_eligible: int = MIN_ELIGIBLE_TYPE) -> pd.DataFrame:
    elig_col, event_col, duration_col = metric_columns(threshold)
    rows: list[dict] = []

    for atype, grp in df.groupby("artifact_type", sort=True):
        elig = grp[grp[elig_col]]
        n_elig = len(elig)
        if n_elig < min_eligible:
            continue
        rate = float(elig[event_col].mean()) if n_elig else float("nan")
        median = pooled_median_survival(grp, duration_col, event_col, elig_col)
        rows.append(
            {
                "artifact_type": atype,
                "n_total": len(grp),
                "n_eligible_180": n_elig,
                "n_stasis_events_180": int(elig[event_col].sum()),
                "stasis_180_rate_eligible": rate,
                "median_survival_days": median,
            }
        )

    return pd.DataFrame(rows).sort_values("n_eligible_180", ascending=False)


def run_robustness(
    df: pd.DataFrame,
    *,
    thresholds: list[int],
    n_bootstrap: int = BOOTSTRAP_REPLICATES,
) -> dict:
    elig_col, event_col, _ = metric_columns(PRIMARY)
    eligible = df[df[elig_col]]

    return {
        "n_repositories": int(df["repo_id"].nunique()),
        "n_artifacts": len(df),
        "n_eligible_180": int(eligible.shape[0]),
        "n_stasis_events_180": int(eligible[event_col].sum()),
        "primary_threshold_days": PRIMARY,
        "cluster_bootstrap": cluster_bootstrap(df, n_replicates=n_bootstrap, threshold=PRIMARY),
        "leave_one_repo_out": leave_one_repo_out(df, threshold=PRIMARY),
        "eligibility_funnel": build_funnel(df, thresholds).to_dict(orient="records"),
        "artifact_types_included_min_eligible_30": build_type_table(df).to_dict(orient="records"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--artifacts", type=Path, default=None)
    parser.add_argument("--touch-history", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--bootstrap", type=int, default=BOOTSTRAP_REPLICATES)
    args = parser.parse_args()

    cfg = load_config(str(args.config))
    artifacts_path = args.artifacts or ROOT / cfg["outputs"]["artifacts"]
    touch_path = args.touch_history or ROOT / cfg["outputs"]["touch_history"]
    thresholds = sorted({90, 180, 365})

    try:
        df = load_artifact_frame(artifacts_path, touch_path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    robustness = run_robustness(df, thresholds=thresholds, n_bootstrap=args.bootstrap)
    funnel_df = build_funnel(df, thresholds)
    type_df = build_type_table(df)

    robustness_path = out_dir / "robustness.json"
    funnel_path = out_dir / "funnel.csv"
    type_path = out_dir / "table_stasis_by_type.csv"

    robustness_path.write_text(json.dumps(robustness, indent=2, default=str) + "\n")
    funnel_df.to_csv(funnel_path, index=False)
    type_df.to_csv(type_path, index=False)

    print(json.dumps(robustness, indent=2, default=str))
    print(f"wrote {robustness_path}", file=sys.stderr)
    print(f"wrote {funnel_path}", file=sys.stderr)
    print(f"wrote {type_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
