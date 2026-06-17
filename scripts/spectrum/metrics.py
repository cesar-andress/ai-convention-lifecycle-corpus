"""Metric computation for synchronization spectrum pilot."""

from __future__ import annotations

from statistics import median

import pandas as pd

from cochange.scope import normalize_path
from cochange.scope_modes import ScopeMode
from cochange.sync_engine import build_commit_index, compute_scope_metrics
from spectrum.families import FamilyDef


def observation_span_years(manifest: pd.DataFrame) -> float:
    if manifest.empty:
        return 0.0
    start = manifest["author_date"].min()
    end = manifest["author_date"].max()
    days = max(1.0, (end - start).total_seconds() / 86400.0)
    return days / 365.25


def git_persistence_metrics(
    anchor_path: str,
    manifest: pd.DataFrame,
    present_in_head: bool,
    threshold_days: int = 180,
) -> dict:
    anchor_path = normalize_path(anchor_path)
    sub = manifest[manifest["changed_path"].map(normalize_path) == anchor_path]
    if sub.empty:
        return {
            "present_in_head": present_in_head,
            "mature_present_180": False,
            "maintained_180": False,
            "lifecycle_persistence_rate": None,
            "follow_up_days": None,
            "days_since_last_touch": None,
        }

    introduced_at = sub["author_date"].min()
    last_touch_at = sub["author_date"].max()
    observation_end = manifest["author_date"].max()
    follow_up_days = int((observation_end - introduced_at).days)
    days_since_last_touch = int((observation_end - last_touch_at).days)

    mature = present_in_head and follow_up_days >= threshold_days
    maintained = present_in_head and days_since_last_touch < threshold_days
    rate = (1.0 if maintained else 0.0) if mature else None

    return {
        "present_in_head": present_in_head,
        "mature_present_180": mature,
        "maintained_180": maintained,
        "lifecycle_persistence_rate": rate,
        "follow_up_days": follow_up_days,
        "days_since_last_touch": days_since_last_touch,
    }


def lifecycle_persistence_row(states: pd.DataFrame, repo_id: str, anchor_path: str) -> dict | None:
    sub = states[
        (states.repo_id == repo_id)
        & (states.artifact_path.map(normalize_path) == normalize_path(anchor_path))
    ]
    if sub.empty:
        return None
    row = sub.iloc[0]
    mature = bool(row.get("mature_present_180", False))
    maintained = bool(row.get("maintained_180", False))
    rate = (1.0 if maintained else 0.0) if mature else None
    return {
        "present_in_head": bool(row.get("present_in_head", False)),
        "mature_present_180": mature,
        "maintained_180": maintained,
        "lifecycle_persistence_rate": rate,
        "follow_up_days": int(row.get("follow_up_days", 0)) if pd.notna(row.get("follow_up_days")) else None,
        "days_since_last_touch": int(row.get("days_since_last_touch", 0))
        if pd.notna(row.get("days_since_last_touch"))
        else None,
    }


def compute_family_row(
    repo_id: str,
    family: FamilyDef,
    anchor_path: str,
    manifest: pd.DataFrame,
    head_files: set[str],
    states: pd.DataFrame | None = None,
) -> dict:
    anchor_path = normalize_path(anchor_path)
    by_commit = build_commit_index(manifest)
    sync = compute_scope_metrics(
        repo_id,
        anchor_path,
        by_commit,
        head_files,
        content_ref_rows=[],
        mode=ScopeMode.REPO_WIDE,
        windows=(0, 7, 30),
    )

    span_years = observation_span_years(manifest)
    n_updates = int(sync.get("n_instruction_updates") or 0)
    update_frequency = n_updates / span_years if span_years > 0 else None

    present = anchor_path in {normalize_path(p) for p in head_files}
    if family.spectrum_group == "instructions" and states is not None:
        persistence = lifecycle_persistence_row(states, repo_id, anchor_path)
        if persistence is None:
            persistence = git_persistence_metrics(anchor_path, manifest, present)
    else:
        persistence = git_persistence_metrics(anchor_path, manifest, present)

    return {
        "repo_id": repo_id,
        "spectrum_group": family.spectrum_group,
        "family_id": family.family_id,
        "family_label": family.label,
        "anchor_path": anchor_path,
        "observation_span_years": round(span_years, 3),
        "n_anchor_updates": n_updates,
        "update_frequency_per_year": round(update_frequency, 4) if update_frequency is not None else None,
        "n_repo_wide_code_events": int(sync.get("n_governed_code_events") or 0),
        "co_change_rate": sync.get("sync_0"),
        "sync_7": sync.get("sync_7"),
        "sync_30": sync.get("sync_30"),
        "median_update_lag_days_30": sync.get("median_lag_days_30"),
        "present_in_head": persistence["present_in_head"],
        "mature_present_180": persistence["mature_present_180"],
        "maintained_180": persistence["maintained_180"],
        "lifecycle_persistence_rate": persistence["lifecycle_persistence_rate"],
        "follow_up_days": persistence["follow_up_days"],
        "days_since_last_touch": persistence["days_since_last_touch"],
        "scope_mode": ScopeMode.REPO_WIDE.value,
        "notes": sync.get("notes", ""),
    }


def aggregate_family_comparison(metrics_df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = [
        "update_frequency_per_year",
        "co_change_rate",
        "sync_7",
        "sync_30",
        "median_update_lag_days_30",
        "lifecycle_persistence_rate",
    ]

    rows: list[dict] = []
    for (group, family_id), grp in metrics_df.groupby(["spectrum_group", "family_id"], sort=True):
        row = {
            "spectrum_group": group,
            "family_id": family_id,
            "family_label": grp["family_label"].iloc[0],
            "n_repo_rows": len(grp),
            "n_repos": grp["repo_id"].nunique(),
        }
        for col in numeric_cols:
            vals = grp[col].dropna()
            row[f"median_{col}"] = median(vals) if len(vals) else None
            row[f"mean_{col}"] = float(vals.mean()) if len(vals) else None
            row[f"n_{col}"] = int(len(vals))
        rows.append(row)
    return pd.DataFrame(rows)


def _group_median_of_family_medians(comparison_df: pd.DataFrame, col: str) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for group, sub in comparison_df.groupby("spectrum_group", sort=True):
        vals = sub[col].dropna()
        out[str(group)] = float(median(vals)) if len(vals) else None
    return out


def calibration_index(comparison_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Map group medians to a descriptive synchronization index.

    0 ≈ documentation pole, 1 ≈ configuration pole (higher = more config-like).
    """
    higher_config_metrics = [
        "median_co_change_rate",
        "median_sync_7",
        "median_sync_30",
        "median_update_frequency_per_year",
        "median_lifecycle_persistence_rate",
    ]
    lower_config_metrics = ["median_median_update_lag_days_30"]
    group_order = ("configuration", "instructions", "documentation")

    rows: list[dict] = []
    for col in higher_config_metrics + lower_config_metrics:
        values = _group_median_of_family_medians(comparison_df, col)
        defined = [values[g] for g in group_order if values.get(g) is not None]
        if len(defined) < 2:
            continue
        lo, hi = min(defined), max(defined)
        span = hi - lo
        row: dict = {"metric": col}
        for g in group_order:
            val = values.get(g)
            row[f"{g}_raw"] = val
            if val is None:
                row[f"{g}_norm"] = None
            elif span == 0:
                row[f"{g}_norm"] = 0.5
            elif col in lower_config_metrics:
                row[f"{g}_norm"] = (hi - val) / span
            else:
                row[f"{g}_norm"] = (val - lo) / span
        rows.append(row)

    detail_df = pd.DataFrame(rows)
    if detail_df.empty:
        return pd.DataFrame(), detail_df

    summary_rows = []
    for g in group_order:
        col = f"{g}_norm"
        if col not in detail_df.columns:
            continue
        vals = detail_df[col].dropna().tolist()
        summary_rows.append(
            {
                "spectrum_group": g,
                "synchronization_index": float(sum(vals) / len(vals)) if vals else None,
                "n_metrics": len(vals),
            }
        )
    return pd.DataFrame(summary_rows), detail_df
