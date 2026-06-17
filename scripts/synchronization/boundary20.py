"""Boundary-20 purposive selection and blinded annotation package."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from cochange.repo_utils import repo_dir_from_id
from lifecycle.git_utils import run_git
from synchronization.blinded_protocol import norm

LEDGER_COLUMNS = [
    "unit_id",
    "repo_id",
    "artifact_family",
    "artifact_path",
    "metric_label",
    "metric_sync_30",
    "lag_days",
    "selection_reason",
    "expected_failure_mode",
    "why_high_information",
]

BOUNDARY20_CONTEXT_COLUMNS = [
    "unit_id",
    "repo_id",
    "artifact_family",
    "artifact_path",
    "governed_code_commit",
    "governed_code_commit_message",
    "changed_paths_in_governed_commit",
    "governed_commit_diff_summary",
    "artifact_contents_at_governed_commit",
    "artifact_excerpt",
    "context_availability_notes",
]

BOUNDARY20_MANUAL_COLUMNS = [
    "manual_is_semantically_synchronized",
    "manual_confidence",
    "manual_reason_tag",
    "manual_reason_free_text",
    "annotator",
    "annotated_at",
]

BOUNDARY20_REASON_TAGS = {
    "substantive_sync",
    "no_sync_needed",
    "stale_missing_update",
    "stale_contradiction",
    "coincidental_update",
    "artifact_genesis_not_resync",
    "unrelated_cochange",
    "insufficient_context",
    "ambiguous",
}

ADJUDICATION_COLUMNS = [
    "unit_id",
    "repo_id",
    "artifact_family",
    "artifact_path",
    "annotator_A_label",
    "annotator_B_label",
    "annotator_C_label",
    "annotator_A_reason_tag",
    "annotator_B_reason_tag",
    "annotator_C_reason_tag",
    "adjudicated_label",
    "adjudicated_confidence",
    "adjudication_notes",
]

FAILURE_MODES = [
    "false_sync_coincidental",
    "false_sync_version_bump",
    "false_sync_same_commit_unrelated",
    "false_sync_genesis",
    "false_desync_scope_orthogonal",
    "false_desync_no_update_needed",
    "false_desync_stale",
    "boundary_lag",
    "instruction_agent_consumed",
    "monorepo_noise",
]

MAX_ARTIFACT_CHARS = 4000
EXCERPT_CHARS = 1200


def truncate(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def git_file_at_commit(repo_dir: Path, commit: str, path: str) -> tuple[str, str]:
    if not commit or not path:
        return "", "missing_commit_or_path"
    proc = run_git(["git", "show", f"{commit}:{path}"], cwd=repo_dir, timeout=30)
    if proc.returncode != 0:
        return "", f"unavailable_at_commit:{proc.stderr.strip()[:120]}"
    return truncate(proc.stdout, MAX_ARTIFACT_CHARS), "ok"


def git_diff_stat(repo_dir: Path, commit: str) -> str:
    proc = run_git(["git", "show", "--stat", "--format=", commit], cwd=repo_dir, timeout=60)
    if proc.returncode != 0:
        return ""
    return truncate(proc.stdout.strip(), 800)


def excerpt_from_contents(contents: str) -> str:
    if not contents:
        return ""
    return truncate(contents, EXCERPT_CHARS)


def version_bump_heuristic(row: pd.Series) -> bool:
    blob = " ".join(
        [
            norm(row.get("commit_message_artifact_update")),
            norm(row.get("diff_summary_artifact")),
            norm(row.get("changed_files_artifact_update")),
        ]
    ).lower()
    return bool(
        re.search(
            r"\b(bump|version|release|changelog|poetry\.lock|package-lock|go\.sum|dependabot)\b",
            blob,
        )
    )


def score_unit(row: pd.Series, ab_disagree: bool) -> list[tuple[int, str, str, str]]:
    """Return list of (priority, selection_reason, failure_mode, why). Higher priority first."""
    hits: list[tuple[int, str, str, str]] = []
    has_upd = norm(row.get("artifact_update_commit")) != ""
    same_commit = has_upd and norm(row.get("artifact_update_commit")) == norm(
        row.get("governed_code_commit")
    )
    lag = pd.to_numeric(row.get("lag_days"), errors="coerce")
    nested = row.get("artifact_family") == "instructions" and "/" in norm(row.get("artifact_path"))
    monorepo = norm(row.get("repo_size_class")) == "large"
    instr = row.get("artifact_family") == "instructions"

    if ab_disagree:
        hits.append(
            (
                100,
                "ab_disagreement",
                "annotator_criterion_divergence",
                "Prior A/B labels diverged; tests whether proxy-aligned preannotation masked semantic disagreement.",
            )
        )
    if instr:
        hits.append(
            (
                90,
                "instruction_artifact",
                "instruction_agent_consumed",
                "AI instruction files are agent-consumed and weakly enforced; sharp probe for proxy validity.",
            )
        )
    if same_commit:
        hits.append(
            (
                88,
                "same_commit_cochange",
                "false_sync_same_commit_unrelated",
                "Same-commit co-change may be unrelated; tests coincidental-update false sync.",
            )
        )
    if version_bump_heuristic(row):
        hits.append(
            (
                85,
                "version_bump_or_release",
                "false_sync_version_bump",
                "Version or lockfile churn may look synchronized without semantic alignment.",
            )
        )
    if pd.notna(lag) and 25 <= float(lag) <= 30:
        hits.append(
            (
                82,
                "boundary_lag_near_window",
                "boundary_lag",
                "Lag near the 30-day window tests sensitivity to operational window choice.",
            )
        )
    if not has_upd and instr:
        hits.append(
            (
                80,
                "no_update_instruction",
                "false_desync_stale",
                "No artifact update on instruction file; tests stale vs no-sync-needed ambiguity.",
            )
        )
    if not has_upd and row.get("artifact_family") == "configuration":
        hits.append(
            (
                78,
                "no_update_configuration",
                "false_desync_scope_orthogonal",
                "Code change may be outside artifact's governed scope; tests scope-orthogonal false desync.",
            )
        )
    if not has_upd and row.get("artifact_family") == "documentation":
        hits.append(
            (
                76,
                "no_update_documentation",
                "false_desync_no_update_needed",
                "Documentation may not require update; tests false desync from absent co-update.",
            )
        )
    if nested:
        hits.append(
            (
                74,
                "nested_instruction_path",
                "instruction_agent_consumed",
                "Nested instruction path in monorepo; scope and governance unclear from path alone.",
            )
        )
    if monorepo:
        hits.append(
            (
                70,
                "large_monorepo",
                "monorepo_noise",
                "Large monorepo with many orthogonal paths; repo-wide scope inflates desync signal.",
            )
        )
    if has_upd and pd.notna(lag) and float(lag) <= 1:
        hits.append(
            (
                68,
                "rapid_followup_update",
                "false_sync_genesis",
                "Very short lag may reflect genesis or incidental touch rather than semantic resync.",
            )
        )
    if row.get("metric_label") == "synchronized" and has_upd:
        hits.append(
            (
                65,
                "metric_synchronized_case",
                "false_sync_coincidental",
                "Metric-positive case for testing false sync modes with human judgment.",
            )
        )
    if row.get("metric_label") == "not_synchronized" and not has_upd:
        hits.append(
            (
                63,
                "metric_not_synchronized_no_update",
                "false_desync_scope_orthogonal",
                "Metric-negative without update; tests whether desync is semantically justified.",
            )
        )
    return hits


def select_boundary20(
    pool: pd.DataFrame,
    disagree_ids: set[str],
    *,
    target_n: int = 20,
) -> pd.DataFrame:
    """Purposive subsample: diversify failure modes, not only A/B disagreements."""

    candidates: list[dict] = []
    for _, row in pool.iterrows():
        uid = row["validation_unit_id"]
        hits = score_unit(row, uid in disagree_ids)
        if not hits:
            continue
        hits_sorted = sorted(hits, key=lambda x: x[0], reverse=True)
        reason_map = {h[1]: h for h in hits_sorted}
        candidates.append(
            {
                "unit_id": uid,
                "priority": hits_sorted[0][0],
                "hits": hits_sorted,
                "reason_map": reason_map,
                "artifact_family": row["artifact_family"],
                "_row": row,
            }
        )

    if not candidates:
        return pd.DataFrame(columns=LEDGER_COLUMNS)

    def ledger_fields(item: dict, reason: str) -> tuple[str, str, str]:
        hit = item["reason_map"].get(reason)
        if hit is None:
            hit = item["hits"][0]
        return hit[1], hit[2], hit[3]

    selected: list[dict] = []
    selected_ids: set[str] = set()

    def try_add(item: dict, reason: str) -> bool:
        uid = item["unit_id"]
        if uid in selected_ids:
            return False
        sel_reason, failure, why = ledger_fields(item, reason)
        selected.append(
            {
                "unit_id": uid,
                "selection_reason": sel_reason,
                "expected_failure_mode": failure,
                "why_high_information": why,
                "_row": item["_row"],
            }
        )
        selected_ids.add(uid)
        return True

    def pool_with_reason(reason: str) -> list[dict]:
        return sorted(
            [c for c in candidates if reason in c["reason_map"] and c["unit_id"] not in selected_ids],
            key=lambda x: x["reason_map"][reason][0],
            reverse=True,
        )

    # Family representation (at least one per family)
    for family in ("instructions", "documentation", "configuration"):
        fam = sorted(
            [c for c in candidates if c["artifact_family"] == family and c["unit_id"] not in selected_ids],
            key=lambda x: x["priority"],
            reverse=True,
        )
        if fam:
            # Prefer instruction_artifact reason for instructions when available
            pick_reason = "instruction_artifact" if family == "instructions" and "instruction_artifact" in fam[0]["reason_map"] else fam[0]["hits"][0][1]
            for item in fam:
                if pick_reason in item["reason_map"]:
                    try_add(item, pick_reason)
                    break
            else:
                try_add(fam[0], fam[0]["hits"][0][1])

    # Diversify structured failure modes (one slot each when available)
    diversity_reasons = [
        "ab_disagreement",
        "same_commit_cochange",
        "version_bump_or_release",
        "boundary_lag_near_window",
        "no_update_instruction",
        "no_update_documentation",
        "no_update_configuration",
        "nested_instruction_path",
        "large_monorepo",
        "rapid_followup_update",
        "metric_synchronized_case",
        "metric_not_synchronized_no_update",
    ]
    for reason in diversity_reasons:
        if len(selected) >= target_n:
            break
        for item in pool_with_reason(reason):
            if try_add(item, reason):
                break

    # Additional A/B disagreements up to ~40% of sample
    ab_cap = max(6, target_n // 2)
    ab_count = sum(1 for s in selected if s["selection_reason"] == "ab_disagreement")
    for item in pool_with_reason("ab_disagreement"):
        if len(selected) >= target_n or ab_count >= ab_cap:
            break
        if try_add(item, "ab_disagreement"):
            ab_count += 1

    # Fill by top priority
    remaining = sorted(
        [c for c in candidates if c["unit_id"] not in selected_ids],
        key=lambda x: x["priority"],
        reverse=True,
    )
    for item in remaining:
        if len(selected) >= target_n:
            break
        try_add(item, item["hits"][0][1])

    out_rows = []
    for item in selected[:target_n]:
        row = item["_row"]
        out_rows.append(
            {
                "unit_id": item["unit_id"],
                "repo_id": row["repo_id"],
                "artifact_family": row["artifact_family"],
                "artifact_path": row["artifact_path"],
                "metric_label": row["metric_label"],
                "metric_sync_30": row["metric_sync_30"],
                "lag_days": row["lag_days"],
                "selection_reason": item["selection_reason"],
                "expected_failure_mode": item["expected_failure_mode"],
                "why_high_information": item["why_high_information"],
            }
        )
    return pd.DataFrame(out_rows)


def build_blinded_row(row: pd.Series, ledger_row: pd.Series, repos_dir: Path) -> dict:
    repo_dir = repo_dir_from_id(row["repo_id"], repos_dir)
    governed = norm(row.get("governed_code_commit"))
    path = norm(row.get("artifact_path"))
    contents, status = git_file_at_commit(repo_dir, governed, path)
    diff_summary = git_diff_stat(repo_dir, governed) if governed else ""

    notes = [f"artifact_at_governed_commit:{status}"]
    if not norm(row.get("commit_message_governed_code")):
        notes.append("sparse_governed_commit_message")
    if not norm(row.get("changed_paths_in_code_commit")):
        notes.append("no_changed_paths_listed")

    return {
        "unit_id": ledger_row["unit_id"],
        "repo_id": row["repo_id"],
        "artifact_family": row["artifact_family"],
        "artifact_path": path,
        "governed_code_commit": governed,
        "governed_code_commit_message": truncate(row.get("commit_message_governed_code", ""), 1500),
        "changed_paths_in_governed_commit": truncate(row.get("changed_paths_in_code_commit", ""), 2000),
        "governed_commit_diff_summary": diff_summary or truncate(row.get("diff_summary_governed", ""), 800),
        "artifact_contents_at_governed_commit": contents,
        "artifact_excerpt": excerpt_from_contents(contents),
        "context_availability_notes": "; ".join(notes),
        "manual_is_semantically_synchronized": "",
        "manual_confidence": "",
        "manual_reason_tag": "",
        "manual_reason_free_text": "",
        "annotator": "",
        "annotated_at": "",
    }


def blinded_workbook(rows: list[dict], annotator_id: str) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["annotator"] = annotator_id
    cols = BOUNDARY20_CONTEXT_COLUMNS + BOUNDARY20_MANUAL_COLUMNS
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols]
