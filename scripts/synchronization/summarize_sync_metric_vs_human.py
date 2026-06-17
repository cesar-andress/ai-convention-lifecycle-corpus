#!/usr/bin/env python3
"""Compare operational sync@30 metric against adjudicated human labels."""

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
    is_filled,
    metric_sync_positive,
    norm,
    normalize_sync_label,
    row_is_decisive,
)

ROOT = configure()


def _fmt_rate(value: float | None) -> str:
    return f"{value:.3f}" if value is not None else "n/a"


def load_adjudicated(adjudication_path: Path, annotator_a: Path, annotator_b: Path) -> pd.DataFrame:
    """Build final human label per unit: adjudication when present, else A if A==B."""
    source_cols = ["validation_unit_id", "metric_sync_30", "artifact_family", "repo_size_class"]
    # Will merge from unblinded source separately

    a = pd.read_csv(annotator_a)
    b = pd.read_csv(annotator_b)
    paired = a[["unit_id", "manual_is_semantically_synchronized", "manual_confidence"]].merge(
        b[["unit_id", "manual_is_semantically_synchronized", "manual_confidence"]],
        on="unit_id",
        suffixes=("_A", "_B"),
    )

    adjudicated = pd.DataFrame(columns=["unit_id", "adjudicated_label", "adjudicated_confidence"])
    if adjudication_path.exists():
        adj = pd.read_csv(adjudication_path)
        if len(adj) and "unit_id" in adj.columns:
            adjudicated = adj[
                ["unit_id", "adjudicated_label", "adjudicated_confidence"]
            ].copy()

    rows = []
    for _, r in paired.iterrows():
        uid = r["unit_id"]
        adj_row = adjudicated[adjudicated["unit_id"] == uid]
        if not adj_row.empty and is_filled(adj_row.iloc[0].get("adjudicated_label")):
            label = normalize_sync_label(adj_row.iloc[0]["adjudicated_label"])
            conf = norm(adj_row.iloc[0].get("adjudicated_confidence")).lower()
            source = "adjudicated"
        elif (
            is_filled(r.get("manual_is_semantically_synchronized_A"))
            and is_filled(r.get("manual_is_semantically_synchronized_B"))
            and normalize_sync_label(r["manual_is_semantically_synchronized_A"])
            == normalize_sync_label(r["manual_is_semantically_synchronized_B"])
        ):
            label = normalize_sync_label(r["manual_is_semantically_synchronized_A"])
            conf_a = norm(r.get("manual_confidence_A")).lower()
            conf_b = norm(r.get("manual_confidence_B")).lower()
            conf = conf_a if conf_a == conf_b else "mixed"
            source = "consensus_ab"
        else:
            label = ""
            conf = ""
            source = "unresolved"

        rows.append(
            {
                "unit_id": uid,
                "human_label": label,
                "human_confidence": conf,
                "label_source": source,
            }
        )
    return pd.DataFrame(rows)


def compute_metric_vs_human(merged: pd.DataFrame) -> dict:
    decisive = merged[
        merged.apply(
            lambda r: row_is_decisive(pd.Series({"manual_is_semantically_synchronized": r["human_label"]})),
            axis=1,
        )
    ].copy()

    high_conf = decisive[
        decisive["human_confidence"].isin(["high"])
        | (
            (decisive["label_source"] == "consensus_ab")
            & decisive["human_confidence"].isin(["high", "mixed"])
        )
    ]

    def confusion(sub: pd.DataFrame) -> dict:
        if sub.empty:
            return {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "precision": None, "recall": None, "specificity": None, "f1": None, "n": 0}
        metric_pos = sub["metric_sync_30"].map(metric_sync_positive)
        human_pos = sub["human_label"].map(lambda v: normalize_sync_label(v) == "TRUE")
        tp = int((metric_pos & human_pos).sum())
        fp = int((metric_pos & ~human_pos).sum())
        fn = int((~metric_pos & human_pos).sum())
        tn = int((~metric_pos & ~human_pos).sum())
        precision = tp / (tp + fp) if (tp + fp) else None
        recall = tp / (tp + fn) if (tp + fn) else None
        specificity = tn / (tn + fp) if (tn + fp) else None
        f1 = (2 * precision * recall / (precision + recall)) if precision and recall and (precision + recall) else None
        return {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "precision": precision,
            "recall": recall,
            "specificity": specificity,
            "f1": f1,
            "n": len(sub),
        }

    overall = confusion(decisive)
    high_conf_stats = confusion(high_conf)

    by_family = []
    for family, sub in decisive.groupby("artifact_family", sort=True):
        stats = confusion(sub)
        stats["artifact_family"] = family
        by_family.append(stats)

    unresolved = int((merged["label_source"] == "unresolved").sum())
    ambiguous_human = int((merged["human_label"] == "AMBIGUOUS").sum())

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_units": len(merged),
        "decisive_human_labels": len(decisive),
        "ambiguous_human_labels": ambiguous_human,
        "unresolved_units": unresolved,
        "overall": overall,
        "high_confidence_decisive_only": high_conf_stats,
        "by_artifact_family": by_family,
    }


def render_markdown(summary: dict) -> str:
    lines = [
        "# Synchronization metric vs adjudicated human labels",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Label coverage",
        "",
        f"- Total units: **{summary['total_units']}**",
        f"- Decisive human labels (TRUE/FALSE): **{summary['decisive_human_labels']}**",
        f"- Ambiguous human labels: **{summary['ambiguous_human_labels']}**",
        f"- Unresolved (disagreement, no adjudication): **{summary['unresolved_units']}**",
        "",
    ]

    if summary["decisive_human_labels"] == 0:
        lines.extend(
            [
                "No decisive adjudicated/consensus labels yet.",
                "Complete A/B annotation, adjudication, then re-run this target.",
                "",
            ]
        )
        return "\n".join(lines)

    def fmt_stats(title: str, stats: dict) -> list[str]:
        out = [
            f"## {title}",
            "",
            f"- n={stats['n']}",
            f"- TP={stats['tp']} FP={stats['fp']} FN={stats['fn']} TN={stats['tn']}",
        ]
        for key in ("precision", "recall", "specificity", "f1"):
            val = stats.get(key)
            out.append(f"- {key}: **{val:.3f}**" if val is not None else f"- {key}: n/a")
        out.append("")
        return out

    lines.extend(fmt_stats("Overall (decisive human labels)", summary["overall"]))
    lines.extend(fmt_stats("High-confidence decisive only", summary["high_confidence_decisive_only"]))

    lines.extend(["## By artifact family", "", "| family | n | precision | recall | F1 |", "|--------|---|-----------|--------|-----|"])
    for row in summary.get("by_artifact_family", []):
        lines.append(
            f"| {row['artifact_family']} | {row['n']} | "
            f"{_fmt_rate(row.get('precision'))} | "
            f"{_fmt_rate(row.get('recall'))} | "
            f"{_fmt_rate(row.get('f1'))} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "annotation/sync_construct_validation_sample.csv",
    )
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
        "--adjudication",
        type=Path,
        default=ROOT / "annotation/sync_construct_validation_adjudication.csv",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=ROOT / "results/synchronization_validation/sync_metric_vs_human_summary.json",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=ROOT / "results/synchronization_validation/sync_metric_vs_human_summary.md",
    )
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"missing unblinded source: {args.source}")

    source = pd.read_csv(args.source)
    human = load_adjudicated(args.adjudication, args.annotator_a, args.annotator_b)

    merged = human.merge(
        source[
            [
                "validation_unit_id",
                "metric_sync_30",
                "artifact_family",
                "repo_size_class",
            ]
        ],
        left_on="unit_id",
        right_on="validation_unit_id",
        how="left",
    )

    summary = compute_metric_vs_human(merged)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    args.md_out.write_text(render_markdown(summary))

    print(f"wrote {args.json_out}")
    print(f"wrote {args.md_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
