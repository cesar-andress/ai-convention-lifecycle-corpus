#!/usr/bin/env python3
"""Summarize inter-annotator agreement and populate adjudication workbook."""

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
from synchronization.blinded_protocol import (
    ADJUDICATION_COLUMNS,
    cohens_kappa,
    is_filled,
    norm,
    normalize_sync_label,
    row_is_annotated,
    row_is_decisive,
)

ROOT = configure()

KAPPA_CATEGORIES = ["TRUE", "FALSE", "AMBIGUOUS"]
DECISIVE_CATEGORIES = ["TRUE", "FALSE"]


def _fmt_rate(value: float | None) -> str:
    return f"{value:.3f}" if value is not None else "n/a"


def load_annotator(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing annotator file: {path}")
    df = pd.read_csv(path)
    if "unit_id" not in df.columns:
        raise SystemExit(f"{path} missing unit_id column")
    out = df.copy()
    out["annotator_source"] = label
    return out


def merge_pair(df_a: pd.DataFrame, df_b: pd.DataFrame, source_df: pd.DataFrame | None) -> pd.DataFrame:
    a = df_a[["unit_id", "repo_id", "artifact_family", "artifact_path"]].merge(
        df_a[
            [
                "unit_id",
                "manual_is_semantically_synchronized",
                "manual_confidence",
                "manual_reason_tag",
                "manual_reason_free_text",
            ]
        ].rename(
            columns={
                "manual_is_semantically_synchronized": "A_label",
                "manual_confidence": "A_confidence",
                "manual_reason_tag": "A_reason_tag",
                "manual_reason_free_text": "A_reason_free_text",
            }
        ),
        on="unit_id",
    )
    b = df_b[
        [
            "unit_id",
            "manual_is_semantically_synchronized",
            "manual_confidence",
            "manual_reason_tag",
            "manual_reason_free_text",
        ]
    ].rename(
        columns={
            "manual_is_semantically_synchronized": "B_label",
            "manual_confidence": "B_confidence",
            "manual_reason_tag": "B_reason_tag",
            "manual_reason_free_text": "B_reason_free_text",
        }
    )
    merged = a.merge(b, on="unit_id", how="inner")
    if source_df is not None and "repo_size_class" in source_df.columns:
        size_map = source_df.set_index("validation_unit_id")["repo_size_class"].to_dict()
        merged["repo_size_class"] = merged["unit_id"].map(size_map)
    return merged


def build_adjudication_rows(merged: pd.DataFrame) -> pd.DataFrame:
    disagreements = merged[
        merged.apply(
            lambda r: row_is_annotated(
                pd.Series({"manual_is_semantically_synchronized": r.get("A_label")})
            )
            and row_is_annotated(
                pd.Series({"manual_is_semantically_synchronized": r.get("B_label")})
            )
            and normalize_sync_label(r.get("A_label")) != normalize_sync_label(r.get("B_label")),
            axis=1,
        )
    ].copy()

    rows = []
    for _, r in disagreements.iterrows():
        rows.append(
            {
                "unit_id": r["unit_id"],
                "repo_id": r["repo_id"],
                "artifact_family": r["artifact_family"],
                "artifact_path": r["artifact_path"],
                "annotator_A_label": norm(r.get("A_label")),
                "annotator_B_label": norm(r.get("B_label")),
                "annotator_A_reason_tag": norm(r.get("A_reason_tag")),
                "annotator_B_reason_tag": norm(r.get("B_reason_tag")),
                "annotator_A_reason_free_text": norm(r.get("A_reason_free_text")),
                "annotator_B_reason_free_text": norm(r.get("B_reason_free_text")),
                "adjudicated_label": "",
                "adjudicated_confidence": "",
                "adjudication_notes": "",
            }
        )
    return pd.DataFrame(rows, columns=ADJUDICATION_COLUMNS)


def agreement_summary(merged: pd.DataFrame) -> dict:
    both = merged[
        merged.apply(
            lambda r: is_filled(r.get("A_label")) and is_filled(r.get("B_label")),
            axis=1,
        )
    ].copy()

    if both.empty:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_units": len(merged),
            "paired_annotated_units": 0,
            "raw_agreement": None,
            "cohens_kappa_3class": None,
            "decisive_paired_units": 0,
            "decisive_raw_agreement": None,
            "cohens_kappa_decisive": None,
            "disagreement_count": 0,
            "disagreement_table": [],
            "by_artifact_family": [],
            "by_repo_size_class": [],
            "low_confidence_unit_count": 0,
        }

    labels_a = both["A_label"].map(normalize_sync_label).tolist()
    labels_b = both["B_label"].map(normalize_sync_label).tolist()
    raw_agreement = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / len(both) if len(both) else None

    decisive_mask = both.apply(
        lambda r: normalize_sync_label(r["A_label"]) in DECISIVE_CATEGORIES
        and normalize_sync_label(r["B_label"]) in DECISIVE_CATEGORIES,
        axis=1,
    )
    decisive = both[decisive_mask]
    dec_a = decisive["A_label"].map(normalize_sync_label).tolist()
    dec_b = decisive["B_label"].map(normalize_sync_label).tolist()
    decisive_agreement = (
        sum(1 for a, b in zip(dec_a, dec_b) if a == b) / len(decisive) if len(decisive) else None
    )

    disagreement_table = (
        both.groupby(["A_label", "B_label"], dropna=False).size().reset_index(name="count")
    )

    by_family = []
    for family, sub in both.groupby("artifact_family", sort=True):
        la = sub["A_label"].map(normalize_sync_label).tolist()
        lb = sub["B_label"].map(normalize_sync_label).tolist()
        agree = sum(1 for a, b in zip(la, lb) if a == b) / len(sub) if len(sub) else None
        by_family.append(
            {
                "artifact_family": family,
                "paired_rows": len(sub),
                "raw_agreement": agree,
                "kappa_3class": cohens_kappa(la, lb, KAPPA_CATEGORIES),
            }
        )

    by_size = []
    if "repo_size_class" in both.columns:
        for size, sub in both.groupby("repo_size_class", sort=True):
            la = sub["A_label"].map(normalize_sync_label).tolist()
            lb = sub["B_label"].map(normalize_sync_label).tolist()
            agree = sum(1 for a, b in zip(la, lb) if a == b) / len(sub) if len(sub) else None
            by_size.append(
                {
                    "repo_size_class": size,
                    "paired_rows": len(sub),
                    "raw_agreement": agree,
                    "kappa_3class": cohens_kappa(la, lb, KAPPA_CATEGORIES),
                }
            )

    low_conf = int(
        both.apply(
            lambda r: norm(r.get("A_confidence")).lower() == "low"
            or norm(r.get("B_confidence")).lower() == "low",
            axis=1,
        ).sum()
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_units": len(merged),
        "paired_annotated_units": len(both),
        "raw_agreement": raw_agreement,
        "cohens_kappa_3class": cohens_kappa(labels_a, labels_b, KAPPA_CATEGORIES),
        "decisive_paired_units": len(decisive),
        "decisive_raw_agreement": decisive_agreement,
        "cohens_kappa_decisive": cohens_kappa(dec_a, dec_b, DECISIVE_CATEGORIES),
        "disagreement_count": int(
            both.apply(
                lambda r: normalize_sync_label(r["A_label"]) != normalize_sync_label(r["B_label"]),
                axis=1,
            ).sum()
        ),
        "disagreement_table": disagreement_table.to_dict(orient="records"),
        "by_artifact_family": by_family,
        "by_repo_size_class": by_size,
        "low_confidence_unit_count": low_conf,
    }


def render_markdown(summary: dict) -> str:
    lines = [
        "# Synchronization construct validation — inter-annotator agreement",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Coverage",
        "",
        f"- Total units in workbooks: **{summary['total_units']}**",
        f"- Paired annotated units: **{summary['paired_annotated_units']}**",
        f"- Disagreements: **{summary['disagreement_count']}**",
        f"- Units with low confidence (either annotator): **{summary['low_confidence_unit_count']}**",
        "",
    ]

    if summary["paired_annotated_units"] == 0:
        lines.append("No paired annotations yet. Fill annotator A/B workbooks first.")
        return "\n".join(lines)

    lines.extend(
        [
            "## Agreement",
            "",
            f"- Raw agreement: **{summary['raw_agreement']:.3f}**"
            if summary["raw_agreement"] is not None
            else "- Raw agreement: n/a",
            f"- Cohen's κ (TRUE/FALSE/AMBIGUOUS): **{summary['cohens_kappa_3class']:.3f}**"
            if summary["cohens_kappa_3class"] is not None
            else "- Cohen's κ (3-class): n/a",
            f"- Decisive raw agreement: **{summary['decisive_raw_agreement']:.3f}**"
            if summary["decisive_raw_agreement"] is not None
            else "- Decisive raw agreement: n/a",
            f"- Cohen's κ (TRUE/FALSE only): **{summary['cohens_kappa_decisive']:.3f}**"
            if summary["cohens_kappa_decisive"] is not None
            else "- Cohen's κ (decisive): n/a",
            "",
            "## Disagreement table",
            "",
            "| A label | B label | count |",
            "|---------|---------|-------|",
        ]
    )
    for row in summary.get("disagreement_table", []):
        lines.append(f"| {row['A_label']} | {row['B_label']} | {row['count']} |")

    lines.extend(["", "## By artifact family", ""])
    for row in summary.get("by_artifact_family", []):
        ag = row["raw_agreement"]
        k = row["kappa_3class"]
        lines.append(
            f"- **{row['artifact_family']}**: n={row['paired_rows']}, "
            f"agreement={_fmt_rate(ag)}, κ={_fmt_rate(k)}"
        )

    if summary.get("by_repo_size_class"):
        lines.extend(["", "## By repository size", ""])
        for row in summary["by_repo_size_class"]:
            lines.append(
                f"- **{row['repo_size_class']}**: n={row['paired_rows']}, "
                f"agreement={_fmt_rate(row['raw_agreement'])}"
            )

    lines.extend(
        [
            "",
            "## Adjudication",
            "",
            "Disagreements exported to `annotation/sync_construct_validation_adjudication.csv`.",
            "Fill adjudicated_label, adjudicated_confidence, adjudication_notes, then run "
            "`make summarize-sync-metric-vs-human`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--annotator-a",
        type=Path,
        default=ROOT / "annotation/sync_construct_validation_blinded_annotator_A.csv",
    )
    parser.add_argument(
        "--annotator-b",
        type=Path,
        default=ROOT / "annotation/sync_construct_validation_blinded_annotator_B.csv",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "annotation/sync_construct_validation_sample.csv",
        help="Unblinded source for repo_size_class join only",
    )
    parser.add_argument(
        "--adjudication-out",
        type=Path,
        default=ROOT / "annotation/sync_construct_validation_adjudication.csv",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=ROOT / "results/synchronization_validation/sync_agreement_summary.json",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=ROOT / "results/synchronization_validation/sync_agreement_summary.md",
    )
    args = parser.parse_args()

    df_a = load_annotator(args.annotator_a, "A")
    df_b = load_annotator(args.annotator_b, "B")
    source_df = pd.read_csv(args.source) if args.source.exists() else None

    merged = merge_pair(df_a, df_b, source_df)
    summary = agreement_summary(merged)

    adjudication_df = build_adjudication_rows(merged)
    args.adjudication_out.parent.mkdir(parents=True, exist_ok=True)
    adjudication_df.to_csv(args.adjudication_out, index=False)

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    args.md_out.write_text(render_markdown(summary))

    print(f"wrote {args.adjudication_out} ({len(adjudication_df)} disagreements)")
    print(f"wrote {args.json_out}")
    print(f"wrote {args.md_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
