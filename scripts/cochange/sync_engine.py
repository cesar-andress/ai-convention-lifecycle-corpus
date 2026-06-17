"""Synchronization metric engine shared by prototype and scope-sensitivity pilots."""

from __future__ import annotations

from datetime import timedelta
from statistics import median

import pandas as pd

from cochange.scope_modes import ResolvedScope, ScopeMode, build_resolved_scope


def build_commit_index(df: pd.DataFrame) -> dict[str, dict]:
    by_commit: dict[str, dict] = {}
    for row in df.itertuples(index=False):
        entry = by_commit.setdefault(
            row.commit,
            {"author_date": row.author_date, "paths": set(), "statuses": {}},
        )
        entry["paths"].add(row.changed_path)
        entry["statuses"][row.changed_path] = row.change_status
    return by_commit


def instruction_update_commits(
    by_commit: dict[str, dict], instruction_path: str
) -> list[tuple[str, pd.Timestamp]]:
    updates: list[tuple[str, pd.Timestamp]] = []
    for sha, meta in by_commit.items():
        if instruction_path not in meta["paths"]:
            continue
        updates.append((sha, meta["author_date"]))
    updates.sort(key=lambda x: x[1])
    return updates


def governed_code_events(
    by_commit: dict[str, dict],
    instruction_path: str,
    scope: ResolvedScope,
) -> list[tuple[str, pd.Timestamp, list[str]]]:
    events: list[tuple[str, pd.Timestamp, list[str]]] = []
    for sha, meta in by_commit.items():
        paths = meta["paths"]
        governed = [p for p in paths if scope.path_in_scope(p)]
        if not governed:
            continue
        non_instruction = [p for p in paths if p != instruction_path]
        if not non_instruction:
            continue
        events.append((sha, meta["author_date"], sorted(governed)))
    events.sort(key=lambda x: x[1])
    return events


def next_instruction_update_lag_days(
    event_time: pd.Timestamp,
    instruction_updates: list[tuple[str, pd.Timestamp]],
    window_days: int,
    same_commit_sha: str,
) -> float | None:
    window_end = event_time + timedelta(days=window_days)
    for sha, ts in instruction_updates:
        if ts < event_time:
            continue
        if window_days == 0 and sha != same_commit_sha:
            continue
        if ts > window_end:
            break
        if sha == same_commit_sha or ts >= event_time:
            return max(0.0, (ts - event_time).total_seconds() / 86400.0)
    return None


def compute_scope_metrics(
    repo_id: str,
    instruction_path: str,
    by_commit: dict[str, dict],
    head_files: set[str],
    content_ref_rows: list[dict],
    mode: ScopeMode,
    windows: tuple[int, ...] = (0, 7, 30),
) -> dict:
    scope = build_resolved_scope(mode, instruction_path, head_files, content_ref_rows)
    updates = instruction_update_commits(by_commit, instruction_path)
    events = governed_code_events(by_commit, instruction_path, scope)

    notes: list[str] = []
    if not updates:
        notes.append("No instruction-update commits in manifest.")
    if not events:
        notes.append("No governed-code events under this scope mode.")
    if mode == ScopeMode.CONTENT_REFERENCED and scope.content_refs_used == 0:
        notes.append("No content references resolved in HEAD; content-referenced scope is empty.")
    if mode == ScopeMode.PACKAGE_SUBTREE:
        if scope.package_subtree_status.startswith("inconclusive"):
            notes.append(f"Package-subtree scope {scope.package_subtree_status}.")
        elif scope.package_subtree_status == "fallback_subtree_nested":
            notes.append("Nested instruction: package-subtree fell back to parent subtree.")

    n_governed_paths_head = sum(1 for p in head_files if scope.path_in_scope(p))

    metrics = {
        "repo_id": repo_id,
        "instruction_file": instruction_path,
        "scope_mode": mode.value,
        "governed_scope_description": scope.description,
        "n_governed_paths_head": n_governed_paths_head,
        "n_governed_code_events": len(events),
        "n_instruction_updates": len(updates),
        "n_content_refs": scope.content_refs_total,
        "n_content_refs_used": scope.content_refs_used,
        "n_package_roots_detected": scope.n_package_roots_detected,
        "package_roots_used": ";".join(sorted(scope.package_roots_used)),
        "package_subtree_status": scope.package_subtree_status,
        "notes": "; ".join(notes),
    }

    lags_30: list[float] = []
    for w in windows:
        synced = 0
        lags: list[float] = []
        for sha, event_time, _ in events:
            lag = next_instruction_update_lag_days(event_time, updates, w, sha)
            if lag is not None:
                synced += 1
                lags.append(lag)
        metrics[f"sync_{w}"] = synced / len(events) if events else None
        if w == 30:
            lags_30 = lags

    metrics["median_lag_days_30"] = median(lags_30) if lags_30 else None

    return metrics
