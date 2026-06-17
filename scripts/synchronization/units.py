"""Validation unit extraction and stratified sampling for sync construct validation."""

from __future__ import annotations

import hashlib
import random
from datetime import timedelta

import pandas as pd

from cochange.changed_files import manifest_output_path
from cochange.repo_utils import repo_dir_from_id
from cochange.scope_modes import ScopeMode, build_resolved_scope
from cochange.sync_engine import (
    build_commit_index,
    governed_code_events,
    instruction_update_commits,
)
from lifecycle.git_utils import run_git
from spectrum.families import FAMILIES, select_anchor, touch_counts_from_manifest

PRIMARY_WINDOW_DAYS = 30
SCOPE_MODE = ScopeMode.REPO_WIDE

INSTRUCTION_FAMILIES = {"claude_md", "agents_md", "cursor_rules"}
DOCUMENTATION_FAMILIES = {"readme", "contributing", "docs_index"}
CONFIGURATION_FAMILIES = {"github_workflows", "package_json", "pyproject_toml", "go_mod"}

MANUAL_COLUMNS = [
    "manual_is_semantically_synchronized",
    "manual_confidence",
    "manual_reason",
    "manual_sync_type",
    "annotator",
    "annotated_at",
]

REVIEW_CONTEXT_COLUMNS = [
    "validation_unit_id",
    "repo_id",
    "repo_size_class",
    "repo_commit_count",
    "artifact_family",
    "family_id",
    "artifact_path",
    "governed_code_commit",
    "governed_code_commit_date",
    "changed_paths_in_code_commit",
    "artifact_update_commit",
    "artifact_update_date",
    "lag_days",
    "metric_label",
    "metric_sync_30",
    "commit_message_governed_code",
    "commit_message_artifact_update",
    "changed_files_governed_commit",
    "changed_files_artifact_update",
    "diff_summary_governed",
    "diff_summary_artifact",
    "scope_mode",
    "notes",
]


def artifact_family_group(family_id: str) -> str:
    if family_id in INSTRUCTION_FAMILIES:
        return "instructions"
    if family_id in DOCUMENTATION_FAMILIES:
        return "documentation"
    if family_id in CONFIGURATION_FAMILIES:
        return "configuration"
    raise ValueError(f"unknown family_id: {family_id}")


def repo_size_class(commit_count: int, tertiles: tuple[int, int]) -> str:
    low, high = tertiles
    if commit_count <= low:
        return "small"
    if commit_count <= high:
        return "medium"
    return "large"


def compute_repo_tertiles(repo_commit_counts: dict[str, int]) -> tuple[int, int]:
    counts = sorted(repo_commit_counts.values())
    if len(counts) < 3:
        mid = counts[len(counts) // 2] if counts else 0
        return mid, mid
    q1 = counts[len(counts) // 3]
    q2 = counts[(2 * len(counts)) // 3]
    return q1, q2


def nearest_update_within_window(
    event_time: pd.Timestamp,
    updates: list[tuple[str, pd.Timestamp]],
    window_days: int,
    same_commit_sha: str,
) -> tuple[str | None, pd.Timestamp | None, float | None]:
    window_end = event_time + timedelta(days=window_days)
    for sha, ts in updates:
        if ts < event_time:
            continue
        if window_days == 0 and sha != same_commit_sha:
            continue
        if ts > window_end:
            break
        if sha == same_commit_sha or ts >= event_time:
            lag = max(0.0, (ts - event_time).total_seconds() / 86400.0)
            return sha, ts, lag
    return None, None, None


def make_unit_id(repo_id: str, artifact_path: str, governed_sha: str) -> str:
    raw = f"{repo_id}|{artifact_path}|{governed_sha}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def truncate_text(text: str, max_len: int = 800) -> str:
    text = " ".join(str(text).split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def git_commit_message(repo_dir, sha: str) -> str:
    proc = run_git(["git", "log", "-1", "--format=%B", sha], cwd=repo_dir, timeout=30)
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def git_diff_stat(repo_dir, sha: str, max_chars: int = 600) -> str:
    proc = run_git(["git", "show", "--stat", "--format=", sha], cwd=repo_dir, timeout=60)
    if proc.returncode != 0:
        return ""
    return truncate_text(proc.stdout.strip(), max_chars)


def paths_in_commit(by_commit: dict[str, dict], sha: str) -> list[str]:
    meta = by_commit.get(sha)
    if not meta:
        return []
    return sorted(meta["paths"])


def extract_units_for_repo_family(
    repo_id: str,
    family,
    anchor_path: str,
    manifest: pd.DataFrame,
    head_files: set[str],
    repo_size: str,
    repo_commit_count: int,
    *,
    max_pool_per_family: int = 80,
    rng: random.Random,
) -> list[dict]:
    by_commit = build_commit_index(manifest)
    scope = build_resolved_scope(SCOPE_MODE, anchor_path, head_files, [])
    updates = instruction_update_commits(by_commit, anchor_path)
    events = governed_code_events(by_commit, anchor_path, scope)
    if not events:
        return []

    pool: list[dict] = []
    for sha, event_time, governed_paths in events:
        update_sha, update_ts, lag = nearest_update_within_window(
            event_time, updates, PRIMARY_WINDOW_DAYS, sha
        )
        synchronized = update_sha is not None
        metric_label = "synchronized" if synchronized else "not_synchronized"
        family_group = artifact_family_group(family.family_id)

        unit = {
            "validation_unit_id": make_unit_id(repo_id, anchor_path, sha),
            "repo_id": repo_id,
            "repo_size_class": repo_size,
            "repo_commit_count": repo_commit_count,
            "artifact_family": family_group,
            "family_id": family.family_id,
            "artifact_path": anchor_path,
            "governed_code_commit": sha,
            "governed_code_commit_date": event_time.isoformat(),
            "changed_paths_in_code_commit": ";".join(governed_paths[:40])
            + (";..." if len(governed_paths) > 40 else ""),
            "artifact_update_commit": update_sha or "",
            "artifact_update_date": update_ts.isoformat() if update_ts is not None else "",
            "lag_days": round(lag, 3) if lag is not None else "",
            "metric_label": metric_label,
            "metric_sync_30": synchronized,
            "commit_message_governed_code": "",
            "commit_message_artifact_update": "",
            "changed_files_governed_commit": ";".join(paths_in_commit(by_commit, sha)[:50]),
            "changed_files_artifact_update": ";".join(paths_in_commit(by_commit, update_sha)[:50])
            if update_sha
            else "",
            "diff_summary_governed": "",
            "diff_summary_artifact": "",
            "scope_mode": SCOPE_MODE.value,
            "notes": "",
        }
        pool.append(unit)

    if len(pool) <= max_pool_per_family:
        return pool

    by_stratum: dict[tuple[str, str], list[dict]] = {}
    for unit in pool:
        key = (unit["artifact_family"], unit["metric_label"])
        by_stratum.setdefault(key, []).append(unit)

    capped: list[dict] = []
    per_stratum_cap = max(5, max_pool_per_family // max(len(by_stratum), 1))
    for units in by_stratum.values():
        if len(units) <= per_stratum_cap:
            capped.extend(units)
        else:
            capped.extend(rng.sample(units, per_stratum_cap))
    return capped


def stratified_sample(
    pool: list[dict],
    target_n: int,
    rng: random.Random,
) -> tuple[list[dict], dict]:
    strata: dict[tuple[str, str, str], list[dict]] = {}
    for unit in pool:
        key = (
            unit["artifact_family"],
            unit["metric_label"],
            unit["repo_size_class"],
        )
        strata.setdefault(key, []).append(unit)

    n_strata = len(strata)
    per_stratum = max(1, target_n // n_strata) if n_strata else target_n
    selected: list[dict] = []
    seen_ids: set[str] = set()
    shortages: dict[str, int] = {}

    for key, units in sorted(strata.items()):
        rng.shuffle(units)
        take = min(per_stratum, len(units))
        for unit in units[:take]:
            if unit["validation_unit_id"] in seen_ids:
                continue
            selected.append(unit)
            seen_ids.add(unit["validation_unit_id"])
        if take < per_stratum:
            shortages["|".join(key)] = per_stratum - take

    if len(selected) < target_n:
        remaining = [u for u in pool if u["validation_unit_id"] not in seen_ids]
        rng.shuffle(remaining)
        for unit in remaining:
            if len(selected) >= target_n:
                break
            selected.append(unit)
            seen_ids.add(unit["validation_unit_id"])

    return selected[:target_n], shortages


def enrich_git_context(units: list[dict], repos_dir) -> None:
    msg_cache: dict[tuple[str, str], str] = {}
    diff_cache: dict[tuple[str, str], str] = {}

    for unit in units:
        repo_dir = repo_dir_from_id(unit["repo_id"], repos_dir)
        for sha, msg_field, diff_field in (
            (unit.get("governed_code_commit"), "commit_message_governed_code", "diff_summary_governed"),
            (unit.get("artifact_update_commit"), "commit_message_artifact_update", "diff_summary_artifact"),
        ):
            if not sha:
                continue
            cache_key = (unit["repo_id"], sha)
            if cache_key not in msg_cache:
                msg_cache[cache_key] = git_commit_message(repo_dir, sha)
            unit[msg_field] = truncate_text(msg_cache[cache_key], 1000)
            if cache_key not in diff_cache:
                diff_cache[cache_key] = git_diff_stat(repo_dir, sha)
            unit[diff_field] = diff_cache[cache_key]


def build_validation_pool(
    pilot_repos_df: pd.DataFrame,
    manifest_dir,
    repos_dir,
    *,
    rng: random.Random | None = None,
) -> tuple[list[dict], dict]:
    rng = rng or random.Random(42)
    repo_commit_counts: dict[str, int] = {}
    manifests: dict[str, pd.DataFrame] = {}

    for repo_id in pilot_repos_df["repo_id"]:
        manifest_path = manifest_output_path(manifest_dir, repo_id)
        if not manifest_path.exists():
            continue
        manifest = pd.read_parquet(manifest_path)
        manifests[repo_id] = manifest
        repo_commit_counts[repo_id] = int(manifest["commit"].nunique())

    tertiles = compute_repo_tertiles(repo_commit_counts)
    pool: list[dict] = []

    for _, row in pilot_repos_df.iterrows():
        repo_id = row["repo_id"]
        manifest = manifests.get(repo_id)
        if manifest is None:
            continue
        repo_dir = repo_dir_from_id(repo_id, repos_dir)
        from lifecycle.git_utils import list_head_files

        head_files = set(list_head_files(repo_dir))
        touches = touch_counts_from_manifest(manifest)
        commit_count = repo_commit_counts[repo_id]
        size_class = repo_size_class(commit_count, tertiles)

        for family in FAMILIES:
            anchor = select_anchor(family, head_files, touches)
            if anchor is None:
                continue
            units = extract_units_for_repo_family(
                repo_id,
                family,
                anchor,
                manifest,
                head_files,
                size_class,
                commit_count,
                rng=rng,
            )
            pool.extend(units)

    meta = {
        "n_pilot_repos": int(pilot_repos_df["repo_id"].nunique()),
        "n_repos_with_manifest": len(manifests),
        "repo_commit_tertiles": {"small_max": tertiles[0], "medium_max": tertiles[1]},
        "pool_size_before_sample": len(pool),
    }
    return pool, meta


def prepare_sample(
    pilot_repos_df: pd.DataFrame,
    manifest_dir,
    repos_dir,
    *,
    target_n: int = 100,
    seed: int = 42,
) -> tuple[pd.DataFrame, dict]:
    rng = random.Random(seed)
    pool, meta = build_validation_pool(pilot_repos_df, manifest_dir, repos_dir, rng=rng)
    selected, shortages = stratified_sample(pool, target_n, rng)
    enrich_git_context(selected, repos_dir)

    meta["target_n"] = target_n
    meta["sampled_n"] = len(selected)
    meta["stratum_shortages"] = shortages
    meta["balance"] = (
        pd.DataFrame(selected)
        .groupby(["artifact_family", "metric_label", "repo_size_class"], dropna=False)
        .size()
        .reset_index(name="count")
        .to_dict(orient="records")
    )
    meta["balance_by_family"] = (
        pd.DataFrame(selected).groupby("artifact_family").size().to_dict()
    )
    meta["balance_by_metric_label"] = (
        pd.DataFrame(selected).groupby("metric_label").size().to_dict()
    )
    meta["balance_by_repo_size"] = (
        pd.DataFrame(selected).groupby("repo_size_class").size().to_dict()
    )

    sample_df = pd.DataFrame(selected)
    for col in REVIEW_CONTEXT_COLUMNS:
        if col not in sample_df.columns:
            sample_df[col] = ""
    sample_df = sample_df[REVIEW_CONTEXT_COLUMNS]

    annotation_df = sample_df.copy()
    for col in MANUAL_COLUMNS:
        annotation_df[col] = ""

    return sample_df, annotation_df, meta
