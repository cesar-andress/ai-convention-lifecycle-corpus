#!/usr/bin/env python3
"""Summarize manual construct validation of synchronization metric."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.corpus_paths import configure
from synchronization.units import MANUAL_COLUMNS

ROOT = configure()

ACCEPTED_SYNC = {"TRUE", "FALSE", "AMBIGUOUS"}
ACCEPTED_CONFIDENCE = {"high", "medium", "low"}
ACCEPTED_SYNC_TYPE = {
    "substantive_sync",
    "cosmetic_sync",
    "unrelated_cochange",
    "stale_no_update",
    "no_sync_needed",
    "ambiguous",
}


def _norm(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _is_filled(value: object) -> bool:
    return _norm(value) != ""


def _row_annotated(row: pd.Series) -> bool:
    return _is_filled(row.get("manual_is_semantically_synchronized"))


def _row_decisive(row: pd.Series) -> bool:
    val = _norm(row.get("manual_is_semantically_synchronized")).upper()
    return val in {"TRUE", "FALSE"}


def _fmt_rate(value: float | None) -> str:
    return f"{value:.3f}" if value is not None else "n/a"


def _metric_sync_positive(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = _norm(value).lower()
    return text in {"true", "1", "yes"}


def compute_metrics(df: pd.DataFrame) -> dict:
    annotated = df[df.apply(_row_annotated, axis=1)].copy()
    decisive = annotated[annotated.apply(_row_decisive, axis=1)].copy()

    ambiguous_count = int(
        annotated["manual_is_semantically_synchronized"]
        .map(lambda v: _norm(v).upper() == "AMBIGUOUS")
        .sum()
    ) if len(annotated) else 0

    tp = fp = fn = tn = 0
    precision = false_positive_rate = false_negative_rate = accuracy = None
    by_family_rows: list[dict] = []
    by_size_rows: list[dict] = []

    if len(decisive) > 0 and "metric_sync_30" in decisive.columns:
        metric_flag = decisive["metric_sync_30"].map(_metric_sync_positive)
        metric_pos = decisive[metric_flag]
        metric_neg = decisive[~metric_flag]

        tp = int((metric_pos["manual_is_semantically_synchronized"].str.upper() == "TRUE").sum())
        fp = int((metric_pos["manual_is_semantically_synchronized"].str.upper() == "FALSE").sum())
        fn = int((metric_neg["manual_is_semantically_synchronized"].str.upper() == "TRUE").sum())
        tn = int((metric_neg["manual_is_semantically_synchronized"].str.upper() == "FALSE").sum())

        precision = tp / (tp + fp) if (tp + fp) else None
        false_positive_rate = fp / (fp + tn) if (fp + tn) else None
        false_negative_rate = fn / (fn + tp) if (fn + tp) else None
        accuracy = (tp + tn) / len(decisive) if len(decisive) else None

        for family, sub in decisive.groupby("artifact_family", sort=True):
            sub_flag = sub["metric_sync_30"].map(_metric_sync_positive)
            mpos = sub[sub_flag]
            mneg = sub[~sub_flag]
            _tp = int((mpos["manual_is_semantically_synchronized"].str.upper() == "TRUE").sum())
            _fp = int((mpos["manual_is_semantically_synchronized"].str.upper() == "FALSE").sum())
            _fn = int((mneg["manual_is_semantically_synchronized"].str.upper() == "TRUE").sum())
            _tn = int((mneg["manual_is_semantically_synchronized"].str.upper() == "FALSE").sum())
            agree = _tp + _tn
            by_family_rows.append(
                {
                    "artifact_family": family,
                    "decisive_rows": len(sub),
                    "accuracy": agree / len(sub) if len(sub) else None,
                    "precision_sync30": _tp / (_tp + _fp) if (_tp + _fp) else None,
                    "false_positive_rate": _fp / (_fp + _tn) if (_fp + _tn) else None,
                    "false_negative_rate": _fn / (_fn + _tp) if (_fn + _tp) else None,
                }
            )

        for size, sub in decisive.groupby("repo_size_class", sort=True):
            sub_flag = sub["metric_sync_30"].map(_metric_sync_positive)
            agree = int(
                (sub_flag & (sub["manual_is_semantically_synchronized"].str.upper() == "TRUE")).sum()
                + (~sub_flag & (sub["manual_is_semantically_synchronized"].str.upper() == "FALSE")).sum()
            )
            by_size_rows.append(
                {
                    "repo_size_class": size,
                    "decisive_rows": len(sub),
                    "accuracy": agree / len(sub) if len(sub) else None,
                }
            )

    sync_type_counts = (
        annotated["manual_sync_type"]
        .map(lambda v: _norm(v).lower())
        .value_counts()
        .to_dict()
    )

    invalid_rows = []
    for idx, row in annotated.iterrows():
        issues = []
        sync_val = _norm(row.get("manual_is_semantically_synchronized")).upper()
        if sync_val and sync_val not in ACCEPTED_SYNC:
            issues.append(f"invalid manual_is_semantically_synchronized={sync_val}")
        conf = _norm(row.get("manual_confidence")).lower()
        if conf and conf not in ACCEPTED_CONFIDENCE:
            issues.append(f"invalid manual_confidence={conf}")
        st = _norm(row.get("manual_sync_type")).lower()
        if st and st not in ACCEPTED_SYNC_TYPE:
            issues.append(f"invalid manual_sync_type={st}")
        if issues:
            invalid_rows.append(
                {
                    "row_index": int(idx),
                    "validation_unit_id": row.get("validation_unit_id"),
                    "issues": issues,
                }
            )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_rows": len(df),
        "annotated_rows": len(annotated),
        "decisive_rows": len(decisive),
        "ambiguous_rows": ambiguous_count,
        "unannotated_rows": int(len(df) - len(annotated)),
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "precision_sync30_vs_manual": precision,
        "false_positive_rate": false_positive_rate,
        "false_negative_rate": false_negative_rate,
        "accuracy_decisive": accuracy,
        "by_artifact_family": by_family_rows,
        "by_repo_size_class": by_size_rows,
        "manual_sync_type_counts": sync_type_counts,
        "invalid_annotation_rows": invalid_rows,
    }


def render_markdown(summary: dict, source_csv: Path) -> str:
    lines = [
        "# Synchronization construct validation summary",
        "",
        f"Source: `{source_csv}`",
        f"Generated: {summary['generated_at']}",
        "",
        "## Coverage",
        "",
        f"- Total units: **{summary['total_rows']}**",
        f"- Annotated: **{summary['annotated_rows']}**",
        f"- Decisive (TRUE/FALSE): **{summary['decisive_rows']}**",
        f"- Ambiguous manual labels: **{summary['ambiguous_rows']}**",
        f"- Unannotated: **{summary['unannotated_rows']}**",
        "",
    ]

    if summary["decisive_rows"] == 0:
        lines.extend(
            [
                "## Metric agreement",
                "",
                "No decisive manual annotations yet. Fill "
                "`annotation/sync_construct_validation_sample.csv` and re-run "
                "`make summarize-sync-validation`.",
                "",
            ]
        )
        return "\n".join(lines)

    cm = summary["confusion_matrix"]
    lines.extend(
        [
            "## Metric agreement (sync@30 vs manual TRUE/FALSE)",
            "",
            f"- Precision: **{_fmt_rate(summary['precision_sync30_vs_manual'])}**",
            f"- False positive rate: **{_fmt_rate(summary['false_positive_rate'])}**",
            f"- False negative rate: **{_fmt_rate(summary['false_negative_rate'])}**",
            f"- Accuracy (decisive): **{_fmt_rate(summary['accuracy_decisive'])}**",
            "",
            "### Confusion matrix",
            "",
            f"- TP (metric sync, manual TRUE): {cm['tp']}",
            f"- FP (metric sync, manual FALSE): {cm['fp']}",
            f"- FN (metric not sync, manual TRUE): {cm['fn']}",
            f"- TN (metric not sync, manual FALSE): {cm['tn']}",
            "",
            "## By artifact family",
            "",
            "| family | decisive | accuracy | precision | FPR | FNR |",
            "|--------|----------|----------|-----------|-----|-----|",
        ]
    )

    for row in summary["by_artifact_family"]:
        lines.append(
            f"| {row['artifact_family']} | {row['decisive_rows']} | "
            f"{_fmt_rate(row['accuracy'])} | {_fmt_rate(row['precision_sync30'])} | "
            f"{_fmt_rate(row['false_positive_rate'])} | {_fmt_rate(row['false_negative_rate'])} |"
        )

    lines.extend(["", "## By repository size", ""])
    for row in summary["by_repo_size_class"]:
        lines.append(
            f"- **{row['repo_size_class']}**: {row['decisive_rows']} decisive, "
            f"accuracy={_fmt_rate(row['accuracy'])}"
        )

    if summary["manual_sync_type_counts"]:
        lines.extend(["", "## Manual sync types", ""])
        for key, count in sorted(summary["manual_sync_type_counts"].items()):
            if key:
                lines.append(f"- `{key}`: {count}")

    if summary["invalid_annotation_rows"]:
        lines.extend(["", "## Invalid annotation values", ""])
        for item in summary["invalid_annotation_rows"]:
            lines.append(
                f"- row {item['row_index']} `{item['validation_unit_id']}`: "
                f"{', '.join(item['issues'])}"
            )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "annotation/sync_construct_validation_sample.csv",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=ROOT / "results/synchronization_validation/sync_validation_summary.json",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=ROOT / "results/synchronization_validation/sync_validation_summary.md",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"missing annotation workbook: {args.input}")

    df = pd.read_csv(args.input)
    summary = compute_metrics(df)

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"wrote {args.json_out}")

    md = render_markdown(summary, args.input)
    args.md_out.write_text(md)
    print(f"wrote {args.md_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
