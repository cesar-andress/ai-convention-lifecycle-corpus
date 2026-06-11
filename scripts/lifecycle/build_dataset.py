#!/usr/bin/env python3
"""Aggregate touch history into artifact-level lifecycle metrics."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lifecycle.detection import load_config

DEFAULT_CONFIG = ROOT / "protocol" / "lifecycle_v1.yaml"

STASIS_THRESHOLDS = [90, 180, 365]


def follow_up_days(introduced_at: pd.Timestamp, observation_end: pd.Timestamp) -> int:
    return max(0, (observation_end - introduced_at).days)


def silence_days(last_touch_at: pd.Timestamp, observation_end: pd.Timestamp) -> int:
    return max(0, (observation_end - last_touch_at).days)


def threshold_metrics(
    introduced_at: pd.Timestamp,
    last_touch_at: pd.Timestamp,
    observation_end: pd.Timestamp,
    threshold: int,
) -> dict:
    follow_up = follow_up_days(introduced_at, observation_end)
    silence = silence_days(last_touch_at, observation_end)
    eligible = follow_up >= threshold
    raw_stasis = silence >= threshold
    event_stasis = eligible and raw_stasis
    censored = not event_stasis
    return {
        f"eligible_{threshold}": eligible,
        f"stasis_{threshold}": raw_stasis,
        f"event_stasis_{threshold}": event_stasis,
        f"censored_{threshold}": censored,
    }


def survival_time_days(
    introduced: pd.Timestamp,
    last_touch: pd.Timestamp,
    observation_end: pd.Timestamp,
    threshold: int,
) -> tuple[int, bool]:
    """Duration/event for eligible artifacts; ineligible rows get event=False."""
    metrics = threshold_metrics(introduced, last_touch, observation_end, threshold)
    if not metrics[f"eligible_{threshold}"]:
        return follow_up_days(introduced, observation_end), False
    if metrics[f"event_stasis_{threshold}"]:
        stasis_start = last_touch + timedelta(days=threshold)
        return int((stasis_start - introduced).days), True
    return follow_up_days(introduced, observation_end), False


def build_artifacts(touch_df: pd.DataFrame, thresholds: list[int]) -> pd.DataFrame:
    rows: list[dict] = []
    grouped = touch_df.groupby(["repo_id", "artifact_type", "artifact_path"], sort=True)

    for (repo_id, artifact_type, artifact_path), grp in grouped:
        grp = grp.sort_values("committed_at")
        introduced_at = grp["committed_at"].iloc[0]
        last_touch_at = grp["committed_at"].iloc[-1]
        observation_end = grp["observation_end"].iloc[-1]
        touch_count = len(grp)

        active_days = max(0, (last_touch_at - introduced_at).days)
        obs_end = observation_end

        row = {
            "repo_id": repo_id,
            "artifact_type": artifact_type,
            "artifact_path": artifact_path,
            "introduced_at": introduced_at,
            "last_touch_at": last_touch_at,
            "observation_end": obs_end,
            "follow_up_days": follow_up_days(introduced_at, obs_end),
            "touch_count": touch_count,
            "active_days": active_days,
        }

        first_after = grp["committed_at"].iloc[1] if touch_count > 1 else pd.NaT
        row["first_touch_after_intro"] = first_after

        for th in thresholds:
            row.update(threshold_metrics(introduced_at, last_touch_at, obs_end, th))
            dur, event = survival_time_days(introduced_at, last_touch_at, obs_end, th)
            row[f"survival_days_{th}"] = dur
            row[f"survival_event_{th}"] = event

        rows.append(row)

    return pd.DataFrame(rows)


def eligibility_summary(df: pd.DataFrame, thresholds: list[int]) -> dict:
    n_all = len(df)
    out: dict = {}
    for th in thresholds:
        event_col = f"event_stasis_{th}"
        elig_col = f"eligible_{th}"
        n_events = int(df[event_col].sum()) if event_col in df.columns else 0
        n_elig = int(df[elig_col].sum()) if elig_col in df.columns else 0
        rate_all = n_events / n_all if n_all else 0.0
        rate_elig = n_events / n_elig if n_elig else 0.0
        out[str(th)] = {
            "stasis_T_rate_all": float(rate_all),
            "stasis_T_rate_eligible": float(rate_elig),
            "n_eligible_T": n_elig,
            "n_event_stasis_T": n_events,
            "censoring_rate_T": float(1.0 - rate_elig) if n_elig else 0.0,
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--touch-history", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    cfg = load_config(str(args.config))
    touch_path = args.touch_history or ROOT / cfg["outputs"]["touch_history"]
    out_path = args.out or ROOT / cfg["outputs"]["artifacts"]

    if not touch_path.exists():
        print(f"missing touch history: {touch_path}", file=sys.stderr)
        return 1

    meta_path = touch_path.with_name("extract_meta.json")
    if meta_path.exists():
        extract_meta = json.loads(meta_path.read_text())
    else:
        extract_meta = None

    touch_df = pd.read_parquet(touch_path)
    for col in ("committed_at", "observation_end"):
        touch_df[col] = pd.to_datetime(touch_df[col], utc=True)

    thresholds = [cfg["stasis_thresholds_days"]["primary"]] + list(
        cfg["stasis_thresholds_days"]["sensitivity"]
    )
    thresholds = sorted(set(int(t) for t in thresholds))

    artifacts = build_artifacts(touch_df, thresholds)

    export_cols = [
        "repo_id",
        "artifact_type",
        "artifact_path",
        "introduced_at",
        "last_touch_at",
        "touch_count",
        "active_days",
        "stasis_90",
        "stasis_180",
        "stasis_365",
    ]
    missing = [c for c in export_cols if c not in artifacts.columns]
    if missing:
        print(f"missing columns: {missing}", file=sys.stderr)
        return 1

    out_df = artifacts[export_cols].copy()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(out_path, index=False)

    full_path = out_path.with_name("artifacts_full.parquet")
    artifacts.to_parquet(full_path, index=False)

    eligibility = eligibility_summary(artifacts, thresholds)

    meta = {
        "n_artifacts": len(out_df),
        "n_repos": out_df["repo_id"].nunique(),
        "by_type": out_df["artifact_type"].value_counts().to_dict(),
        "stasis_180_rate_all": eligibility["180"]["stasis_T_rate_all"],
        "stasis_180_rate_eligible": eligibility["180"]["stasis_T_rate_eligible"],
        "n_eligible_180": eligibility["180"]["n_eligible_T"],
        "eligibility_by_threshold": eligibility,
    }
    if extract_meta is not None:
        meta["extract_meta"] = extract_meta
        n_touch = int(extract_meta.get("n_repos_in_touch_history", 0))
        if n_touch and meta["n_repos"] != n_touch:
            print(
                f"warning: artifact repos ({meta['n_repos']}) != extract touch repos ({n_touch})",
                file=sys.stderr,
            )
    (out_path.parent / "artifacts_build_meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))
    print(f"artifacts -> {out_path}")
    return 0


def load_artifact_frame(artifacts_path: Path, touch_path: Path) -> pd.DataFrame:
    """Load artifact table for adoption--maintenance analysis."""
    full_path = artifacts_path.with_name("artifacts_full.parquet")
    if full_path.exists():
        df = pd.read_parquet(full_path)
    elif artifacts_path.exists() and touch_path.exists():
        touch_df = pd.read_parquet(touch_path)
        for col in ("committed_at", "observation_end"):
            if col in touch_df.columns:
                touch_df[col] = pd.to_datetime(touch_df[col], utc=True)
        df = build_artifacts(touch_df, STASIS_THRESHOLDS)
    else:
        raise FileNotFoundError(f"missing artifacts: {artifacts_path}")

    for col in ("introduced_at", "last_touch_at", "observation_end", "first_touch_after_intro"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True)
    return df


if __name__ == "__main__":
    sys.exit(main())
