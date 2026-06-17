#!/usr/bin/env python3
"""Summarize manual validation of content-reference parser extractions."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.corpus_paths import configure

ROOT = configure()

BOOLEAN_COLUMNS = [
    "manual_is_reference_correct",
    "manual_resolved_path_correct",
    "manual_should_be_used_for_scope",
]

THRESHOLDS = {
    "manual_is_reference_correct": 0.85,
    "manual_resolved_path_correct": 0.80,
    "manual_should_be_used_for_scope": 0.75,
}

ACCEPTED_BOOLEAN_VALUES = {"TRUE", "FALSE", "AMBIGUOUS"}
ACCEPTED_CATEGORIES = {
    "path",
    "directory",
    "config_file",
    "build_command",
    "test_command",
    "documentation_reference",
    "include_pointer",
    "false_positive",
    "ambiguous",
}


def _normalize(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _is_filled(value: object) -> bool:
    return _normalize(value) != ""


def _boolean_rate(series: pd.Series) -> dict[str, object]:
    values = [_normalize(v).upper() for v in series if _is_filled(v)]
    decisive = [v for v in values if v in {"TRUE", "FALSE"}]
    ambiguous = sum(1 for v in values if v == "AMBIGUOUS")
    true_count = sum(1 for v in decisive if v == "TRUE")
    false_count = sum(1 for v in decisive if v == "FALSE")
    annotated = len(decisive) + ambiguous
    precision = (true_count / len(decisive)) if decisive else None
    return {
        "annotated_rows": annotated,
        "decisive_rows": len(decisive),
        "true_count": true_count,
        "false_count": false_count,
        "ambiguous_count": ambiguous,
        "precision": precision,
    }


def _row_is_annotated(row: pd.Series) -> bool:
    return any(_is_filled(row.get(col)) for col in BOOLEAN_COLUMNS + ["manual_reference_category"])


def _row_is_fully_annotated(row: pd.Series) -> bool:
    return all(_is_filled(row.get(col)) for col in BOOLEAN_COLUMNS + ["manual_reference_category"])


def _row_to_dict(row: pd.Series) -> dict[str, str]:
    return {
        "repo_id": _normalize(row.get("repo_id")),
        "instruction_file": _normalize(row.get("instruction_file")),
        "raw_reference": _normalize(row.get("raw_reference")),
        "resolved_path": _normalize(row.get("resolved_path")),
        "extraction_rule": _normalize(row.get("extraction_rule")),
        "confidence": _normalize(row.get("confidence")),
        "manual_is_reference_correct": _normalize(row.get("manual_is_reference_correct")),
        "manual_resolved_path_correct": _normalize(row.get("manual_resolved_path_correct")),
        "manual_should_be_used_for_scope": _normalize(row.get("manual_should_be_used_for_scope")),
        "manual_reference_category": _normalize(row.get("manual_reference_category")),
        "manual_notes": _normalize(row.get("manual_notes")),
    }


def build_summary(df: pd.DataFrame, source_csv: str) -> dict[str, object]:
    total_rows = len(df)
    annotated_rows = int(df.apply(_row_is_annotated, axis=1).sum())
    fully_annotated_rows = int(df.apply(_row_is_fully_annotated, axis=1).sum())
    unannotated_rows = total_rows - annotated_rows

    validation_pending = annotated_rows == 0

    boolean_summary = {
        col: _boolean_rate(df[col]) for col in BOOLEAN_COLUMNS
    }

    by_rule: dict[str, dict[str, object]] = {}
    for rule, group in df.groupby("extraction_rule", dropna=False):
        by_rule[str(rule)] = {
            "n_rows": int(len(group)),
            "precision": {
                col: _boolean_rate(group[col])["precision"] for col in BOOLEAN_COLUMNS
            },
        }

    by_confidence: dict[str, dict[str, object]] = {}
    for conf, group in df.groupby("confidence", dropna=False):
        by_confidence[str(conf)] = {
            "n_rows": int(len(group)),
            "precision": {
                col: _boolean_rate(group[col])["precision"] for col in BOOLEAN_COLUMNS
            },
        }

    category_counts = Counter(
        _normalize(row.get("manual_reference_category")).lower()
        for _, row in df.iterrows()
        if _is_filled(row.get("manual_reference_category"))
    )

    false_positives = [
        _row_to_dict(row)
        for _, row in df.iterrows()
        if _normalize(row.get("manual_reference_category")).lower() == "false_positive"
        or _normalize(row.get("manual_is_reference_correct")).upper() == "FALSE"
    ]

    ambiguous_cases = [
        _row_to_dict(row)
        for _, row in df.iterrows()
        if _normalize(row.get("manual_reference_category")).lower() == "ambiguous"
        or any(
            _normalize(row.get(col)).upper() == "AMBIGUOUS"
            for col in BOOLEAN_COLUMNS
            if _is_filled(row.get(col))
        )
    ]

    threshold_checks = {}
    for col, threshold in THRESHOLDS.items():
        precision = boolean_summary[col]["precision"]
        if precision is None:
            threshold_checks[col] = {
                "threshold": threshold,
                "observed": None,
                "passes": None,
            }
        else:
            threshold_checks[col] = {
                "threshold": threshold,
                "observed": precision,
                "passes": precision >= threshold,
            }

    all_pass = (
        not validation_pending
        and all(check["passes"] is True for check in threshold_checks.values())
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_csv": source_csv,
        "validation_pending": validation_pending,
        "total_rows": total_rows,
        "annotated_rows": annotated_rows,
        "fully_annotated_rows": fully_annotated_rows,
        "unannotated_rows": unannotated_rows,
        "thresholds": THRESHOLDS,
        "boolean_precision": boolean_summary,
        "threshold_checks": threshold_checks,
        "content_ref_acceptable_for_paper": all_pass,
        "content_ref_status": (
            "pending_manual_annotation"
            if validation_pending
            else ("acceptable" if all_pass else "exploratory_only")
        ),
        "precision_by_extraction_rule": by_rule,
        "precision_by_confidence": by_confidence,
        "manual_reference_category_counts": dict(sorted(category_counts.items())),
        "false_positives": false_positives,
        "ambiguous_cases": ambiguous_cases,
        "accepted_boolean_values": sorted(ACCEPTED_BOOLEAN_VALUES),
        "accepted_categories": sorted(ACCEPTED_CATEGORIES),
    }


def _fmt_pct(value: object) -> str:
    if value is None:
        return "n/a"
    return f"{100.0 * float(value):.1f}%"


def render_markdown(summary: dict[str, object]) -> str:
    lines: list[str] = [
        "# Content-reference parser manual validation summary",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        f"Source: `{summary['source_csv']}`",
        "",
    ]

    if summary["validation_pending"]:
        lines.extend(
            [
                "## Status: validation pending",
                "",
                "No manual annotation rows were found. Fill "
                "`annotation/cochange_reference_validation_sample.csv`, then run:",
                "",
                "```bash",
                "make summarize-reference-validation",
                "```",
                "",
            ]
        )
    else:
        status = summary["content_ref_status"]
        acceptable = summary["content_ref_acceptable_for_paper"]
        lines.extend(
            [
                f"## Status: **{status}**",
                "",
                f"Content-ref acceptable for paper sensitivity analysis: **{acceptable}**",
                "",
            ]
        )

    lines.extend(
        [
            "## Coverage",
            "",
            f"- Total rows: **{summary['total_rows']}**",
            f"- Annotated rows (any manual field): **{summary['annotated_rows']}**",
            f"- Fully annotated rows (all booleans + category): **{summary['fully_annotated_rows']}**",
            f"- Unannotated rows: **{summary['unannotated_rows']}**",
            "",
            "## Provisional thresholds",
            "",
            "| Metric | Threshold | Observed | Pass |",
            "|--------|-----------|----------|------|",
        ]
    )

    for col, check in summary["threshold_checks"].items():  # type: ignore[assignment]
        observed = check["observed"]
        passes = check["passes"]
        pass_str = "n/a" if passes is None else ("yes" if passes else "no")
        lines.append(
            f"| `{col}` | {_fmt_pct(check['threshold'])} | {_fmt_pct(observed)} | {pass_str} |"
        )

    lines.extend(["", "## Boolean precision (TRUE / (TRUE + FALSE))", ""])
    for col, stats in summary["boolean_precision"].items():  # type: ignore[assignment]
        lines.append(
            f"- `{col}`: precision={_fmt_pct(stats['precision'])}, "
            f"true={stats['true_count']}, false={stats['false_count']}, "
            f"ambiguous={stats['ambiguous_count']}, annotated={stats['annotated_rows']}"
        )

    lines.extend(["", "## Counts by `manual_reference_category`", ""])
    counts = summary["manual_reference_category_counts"]
    if not counts:
        lines.append("_None yet._")
    else:
        for category, count in counts.items():  # type: ignore[assignment]
            lines.append(f"- `{category}`: {count}")

    lines.extend(["", "## Precision by extraction rule", ""])
    for rule, stats in summary["precision_by_extraction_rule"].items():  # type: ignore[assignment]
        prec = stats["precision"]
        scope_prec = prec["manual_should_be_used_for_scope"]
        ref_prec = prec["manual_is_reference_correct"]
        lines.append(
            f"- `{rule}` (n={stats['n_rows']}): "
            f"reference={_fmt_pct(ref_prec)}, scope={_fmt_pct(scope_prec)}"
        )

    lines.extend(["", "## Precision by confidence", ""])
    for conf, stats in summary["precision_by_confidence"].items():  # type: ignore[assignment]
        prec = stats["precision"]
        scope_prec = prec["manual_should_be_used_for_scope"]
        ref_prec = prec["manual_is_reference_correct"]
        lines.append(
            f"- `{conf}` (n={stats['n_rows']}): "
            f"reference={_fmt_pct(ref_prec)}, scope={_fmt_pct(scope_prec)}"
        )

    lines.extend(["", "## False positives", ""])
    fps = summary["false_positives"]
    if not fps:
        lines.append("_None labeled yet._")
    else:
        for row in fps[:20]:
            lines.append(
                f"- `{row['repo_id']}` / `{row['instruction_file']}`: "
                f"`{row['raw_reference']}` → `{row['resolved_path']}` "
                f"(category=`{row['manual_reference_category']}`)"
            )
        if len(fps) > 20:
            lines.append(f"- … and {len(fps) - 20} more (see JSON).")

    lines.extend(["", "## Ambiguous cases", ""])
    amb = summary["ambiguous_cases"]
    if not amb:
        lines.append("_None labeled yet._")
    else:
        for row in amb[:20]:
            lines.append(
                f"- `{row['repo_id']}` / `{row['instruction_file']}`: "
                f"`{row['raw_reference']}` → `{row['resolved_path']}` "
                f"(category=`{row['manual_reference_category']}`)"
            )
        if len(amb) > 20:
            lines.append(f"- … and {len(amb) - 20} more (see JSON).")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "If any threshold fails, content-referenced scope remains **exploratory only** "
            "in the paper until parser rules or annotation sample issues are resolved.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "annotation/cochange_reference_validation_sample.csv",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=ROOT / "results/cochange/reference_validation_summary.json",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=ROOT / "results/cochange/reference_validation_summary.md",
    )
    args = parser.parse_args()

    if not args.input.is_file():
        raise SystemExit(f"Input not found: {args.input}")

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    source_csv = str(args.input)
    try:
        source_csv = str(args.input.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        pass
    summary = build_summary(df, source_csv)

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(summary, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    args.md_out.write_text(render_markdown(summary), encoding="utf-8")

    print(f"read {args.input} ({summary['total_rows']} rows)")
    print(f"annotated={summary['annotated_rows']} unannotated={summary['unannotated_rows']}")
    print(f"status={summary['content_ref_status']}")
    print(f"wrote {args.json_out}")
    print(f"wrote {args.md_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
