"""Shared constants and helpers for blinded sync construct validation."""

from __future__ import annotations

from collections import Counter

import pandas as pd

BLINDED_CONTEXT_COLUMNS = [
    "unit_id",
    "repo_id",
    "artifact_family",
    "artifact_path",
    "governed_code_commit",
    "governed_code_commit_date",
    "changed_paths_in_code_commit",
    "artifact_update_commit",
    "artifact_update_date",
    "commit_message_governed_code",
    "commit_message_artifact_update",
    "changed_files_governed_commit",
    "changed_files_artifact_update",
    "diff_summary_governed",
    "diff_summary_artifact",
    "scope_mode",
    "notes",
]

BLINDED_MANUAL_COLUMNS = [
    "manual_is_semantically_synchronized",
    "manual_confidence",
    "manual_reason_tag",
    "manual_reason_free_text",
    "annotator",
    "annotated_at",
]

METRIC_DERIVED_COLUMNS = [
    "metric_sync_30",
    "metric_label",
    "lag_days",
    "repo_size_class",
    "repo_commit_count",
    "family_id",
]

ACCEPTED_SYNC = {"TRUE", "FALSE", "AMBIGUOUS"}
ACCEPTED_CONFIDENCE = {"high", "medium", "low"}
ACCEPTED_REASON_TAG = {
    "substantive_sync",
    "cosmetic_sync",
    "unrelated_cochange",
    "stale_no_update",
    "no_sync_needed",
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
    "annotator_A_reason_tag",
    "annotator_B_reason_tag",
    "annotator_A_reason_free_text",
    "annotator_B_reason_free_text",
    "adjudicated_label",
    "adjudicated_confidence",
    "adjudication_notes",
]


def norm(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def is_filled(value: object) -> bool:
    return norm(value) != ""


def normalize_sync_label(value: object) -> str:
    return norm(value).upper()


def row_is_annotated(row: pd.Series) -> bool:
    return is_filled(row.get("manual_is_semantically_synchronized"))


def row_is_decisive(row: pd.Series) -> bool:
    return normalize_sync_label(row.get("manual_is_semantically_synchronized")) in {"TRUE", "FALSE"}


def blinded_workbook_from_source(source_df: pd.DataFrame, annotator_id: str) -> pd.DataFrame:
    out = pd.DataFrame()
    out["unit_id"] = source_df["validation_unit_id"]
    for col in BLINDED_CONTEXT_COLUMNS:
        if col == "unit_id":
            continue
        src_col = {
            "commit_message_governed_code": "commit_message_governed_code",
            "commit_message_artifact_update": "commit_message_artifact_update",
            "changed_files_governed_commit": "changed_files_governed_commit",
            "changed_files_artifact_update": "changed_files_artifact_update",
            "diff_summary_governed": "diff_summary_governed",
            "diff_summary_artifact": "diff_summary_artifact",
        }.get(col, col)
        if src_col in source_df.columns:
            out[col] = source_df[src_col]
        else:
            out[col] = ""

    for col in BLINDED_MANUAL_COLUMNS:
        if col == "annotator":
            out[col] = annotator_id
        else:
            out[col] = ""

    return out[BLINDED_CONTEXT_COLUMNS + BLINDED_MANUAL_COLUMNS]


def cohens_kappa(labels_a: list[str], labels_b: list[str], categories: list[str]) -> float | None:
    if len(labels_a) != len(labels_b) or len(labels_a) == 0:
        return None
    n = len(labels_a)
    observed = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n

    counts_a = Counter(labels_a)
    counts_b = Counter(labels_b)
    expected = sum((counts_a[c] / n) * (counts_b[c] / n) for c in categories)

    if expected == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1.0 - expected)


def metric_sync_positive(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = norm(value).lower()
    return text in {"true", "1", "yes"}
