#!/usr/bin/env python3
"""Compare sync@30 (from researcher ledger) to adjudicated human labels for boundary20."""

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
    normalize_sync_label,
)

ROOT = configure()


def _fmt_rate(value: float | None) -> str:
    return f"{value:.3f}" if value is not None else "n/a"


def load_human_labels(
    annotator_a: Path,
    annotator_b: Path,
    annotator_c: Path,
    adjudication: Path,
) -> pd.DataFrame:
    base = pd.read_csv(annotator_a)[["unit_id", "repo_id", "artifact_family", "artifact_path"]]
    labels: dict[str, dict[str, str]] = {}
    for name, path in [
        ("annotator_A", annotator_a),
        ("annotator_B", annotator_b),
        ("annotator_C", annotator_c),
    ]:
        sub = pd.read_csv(path)[["unit_id", "manual_is_semantically_synchronized"]]
        labels[name] = {
            row.unit_id: normalize_sync_label(row.manual_is_semantically_synchronized)
            for _, row in sub.iterrows()
            if is_filled(row.manual_is_semantically_synchronized)
        }

    adjudicated: dict[str, str] = {}
    if adjudication.exists():
        adj = pd.read_csv(adjudication)
        for _, row in adj.iterrows():
            if is_filled(row.get("adjudicated_label")):
                adjudicated[row.unit_id] = normalize_sync_label(row.adjudicated_label)

    rows = []
    for _, row in base.iterrows():
        uid = row.unit_id
        la = labels["annotator_A"].get(uid, "")
        lb = labels["annotator_B"].get(uid, "")
        lc = labels["annotator_C"].get(uid, "")
        if uid in adjudicated:
            human = adjudicated[uid]
            source = "adjudicated"
        elif la and la == lb == lc:
            human = la
            source = "consensus_abc"
        elif la and lb and la == lb:
            human = la
            source = "consensus_ab"
        elif la and lc and la == lc:
            human = la
            source = "consensus_ac"
        elif lb and lc and lb == lc:
            human = lb
            source = "consensus_bc"
        else:
            human = ""
            source = "unresolved"

        rows.append(
            {
                "unit_id": uid,
                "repo_id": row.repo_id,
                "artifact_family": row.artifact_family,
                "artifact_path": row.artifact_path,
                "human_label": human,
                "label_source": source,
                "annotator_A": la,
                "annotator_B": lb,
                "annotator_C": lc,
            }
        )
    return pd.DataFrame(rows)


def confusion(sub: pd.DataFrame) -> dict:
    if sub.empty:
        return {
            "tp": 0,
            "fp": 0,
            "fn": 0,
            "tn": 0,
            "precision": None,
            "recall": None,
            "specificity": None,
            "f1": None,
            "agreement_rate": None,
            "n": 0,
        }
    metric_pos = sub["metric_sync_30"].map(metric_sync_positive)
    human_pos = sub["human_label"].map(lambda v: normalize_sync_label(v) == "TRUE")
    agree = metric_pos == human_pos
    tp = int((metric_pos & human_pos).sum())
    fp = int((metric_pos & ~human_pos).sum())
    fn = int((~metric_pos & human_pos).sum())
    tn = int((~metric_pos & ~human_pos).sum())
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    specificity = tn / (tn + fp) if (tn + fp) else None
    denom = (precision + recall) if precision is not None and recall is not None else None
    f1 = (2 * precision * recall / denom) if denom else None
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
        "agreement_rate": float(agree.mean()),
        "n": len(sub),
    }


def ambiguous_sensitivity(merged: pd.DataFrame) -> dict:
    """Bounds if all AMBIGUOUS units were resolved in metric-favoring vs metric-opposing ways."""
    amb = merged[merged["human_label"] == "AMBIGUOUS"]
    decisive = merged[merged["human_label"].isin(["TRUE", "FALSE"])]
    if amb.empty:
        base = float((decisive["metric_sync_30"].map(metric_sync_positive) == (decisive["human_label"] == "TRUE")).mean()) if len(decisive) else None
        return {
            "ambiguous_count": 0,
            "decisive_agreement_excluding_ambiguous": base,
            "worst_case_if_ambiguous_all_metric_favoring": base,
            "worst_case_if_ambiguous_all_metric_opposing": base,
        }

    def agreement_with_resolved(extra: pd.DataFrame) -> float | None:
        combined = pd.concat([decisive, extra], ignore_index=True)
        if combined.empty:
            return None
        metric_pos = combined["metric_sync_30"].map(metric_sync_positive)
        human_pos = combined["human_label"].map(lambda v: normalize_sync_label(v) == "TRUE")
        return float((metric_pos == human_pos).mean())

    favor_rows = []
    oppose_rows = []
    for _, row in amb.iterrows():
        metric_pos = metric_sync_positive(row["metric_sync_30"])
        favor = row.to_dict()
        oppose = row.to_dict()
        favor["human_label"] = "TRUE" if metric_pos else "FALSE"
        oppose["human_label"] = "FALSE" if metric_pos else "TRUE"
        favor_rows.append(favor)
        oppose_rows.append(oppose)

    decisive_agree = agreement_with_resolved(pd.DataFrame())
    return {
        "ambiguous_count": len(amb),
        "decisive_agreement_excluding_ambiguous": decisive_agree,
        "worst_case_if_ambiguous_all_metric_favoring": agreement_with_resolved(pd.DataFrame(favor_rows)),
        "worst_case_if_ambiguous_all_metric_opposing": agreement_with_resolved(pd.DataFrame(oppose_rows)),
    }


def example_rows(merged: pd.DataFrame, kind: str, limit: int = 5) -> list[dict]:
    decisive = merged[merged["human_label"].isin(["TRUE", "FALSE"])].copy()
    metric_pos = decisive["metric_sync_30"].map(metric_sync_positive)
    human_pos = decisive["human_label"] == "TRUE"
    if kind == "false_sync":
        sub = decisive[metric_pos & ~human_pos]
    elif kind == "false_desync":
        sub = decisive[~metric_pos & human_pos]
    else:
        return []
    cols = ["unit_id", "repo_id", "artifact_family", "artifact_path", "metric_sync_30", "metric_label", "human_label", "label_source"]
    return sub[cols].head(limit).to_dict(orient="records")


def compute_summary(merged: pd.DataFrame) -> dict:
    decisive = merged[merged["human_label"].isin(["TRUE", "FALSE"])]
    ambiguous = merged[merged["human_label"] == "AMBIGUOUS"]
    unresolved = merged[merged["label_source"] == "unresolved"]

    overall = confusion(decisive)
    amb_sens = ambiguous_sensitivity(merged)

    by_family = []
    for family, sub in decisive.groupby("artifact_family", sort=True):
        stats = confusion(sub)
        stats["artifact_family"] = family
        by_family.append(stats)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_units": len(merged),
        "decisive_human_labels": len(decisive),
        "ambiguous_human_labels": len(ambiguous),
        "unresolved_units": len(unresolved),
        "overall": overall,
        "agreement_excluding_ambiguous": amb_sens.get("decisive_agreement_excluding_ambiguous"),
        "ambiguous_sensitivity": amb_sens,
        "by_artifact_family": by_family,
        "examples_false_sync": example_rows(merged, "false_sync"),
        "examples_false_desync": example_rows(merged, "false_desync"),
    }


def render_markdown(summary: dict) -> str:
    lines = [
        "# Boundary20: sync@30 vs adjudicated human labels",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Label coverage",
        "",
        f"- Total units: **{summary['total_units']}**",
        f"- Decisive human labels (TRUE/FALSE): **{summary['decisive_human_labels']}**",
        f"- Ambiguous human labels: **{summary['ambiguous_human_labels']}**",
        f"- Unresolved (no consensus/adjudication): **{summary['unresolved_units']}**",
        "",
    ]

    if summary["decisive_human_labels"] == 0:
        lines.extend(
            [
                "No decisive labels yet. Complete A/B/C annotation and adjudication, then re-run.",
                "",
            ]
        )
        return "\n".join(lines)

    stats = summary["overall"]
    lines.extend(
        [
            "## Confusion matrix (decisive labels)",
            "",
            f"- n={stats['n']}",
            f"- TP={stats['tp']} FP={stats['fp']} FN={stats['fn']} TN={stats['tn']}",
            f"- precision: **{_fmt_rate(stats.get('precision'))}**",
            f"- recall: **{_fmt_rate(stats.get('recall'))}**",
            f"- specificity: **{_fmt_rate(stats.get('specificity'))}**",
            f"- F1: **{_fmt_rate(stats.get('f1'))}**",
            f"- agreement (metric vs human): **{_fmt_rate(stats.get('agreement_rate'))}**",
            "",
            f"- Agreement excluding AMBIGUOUS: **{_fmt_rate(summary.get('agreement_excluding_ambiguous'))}**",
            "",
            "## AMBIGUOUS sensitivity bounds",
            "",
        ]
    )
    amb = summary["ambiguous_sensitivity"]
    lines.append(f"- Ambiguous count: **{amb['ambiguous_count']}**")
    lines.append(f"- If ambiguous resolved metric-favoring: **{_fmt_rate(amb.get('worst_case_if_ambiguous_all_metric_favoring'))}**")
    lines.append(f"- If ambiguous resolved metric-opposing: **{_fmt_rate(amb.get('worst_case_if_ambiguous_all_metric_opposing'))}**")
    lines.append("")

    if summary.get("examples_false_sync"):
        lines.extend(["## Examples: false sync (metric+, human FALSE)", ""])
        for ex in summary["examples_false_sync"]:
            lines.append(f"- `{ex['unit_id']}` {ex['repo_id']} {ex['artifact_path']} (metric_label={ex.get('metric_label')})")
        lines.append("")

    if summary.get("examples_false_desync"):
        lines.extend(["## Examples: false desync (metric−, human TRUE)", ""])
        for ex in summary["examples_false_desync"]:
            lines.append(f"- `{ex['unit_id']}` {ex['repo_id']} {ex['artifact_path']} (metric_label={ex.get('metric_label')})")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ledger",
        type=Path,
        default=ROOT / "results/synchronization_validation/boundary20_selection_ledger.csv",
    )
    parser.add_argument("--annotator-a", type=Path, default=ROOT / "annotation/boundary20_annotator_A.csv")
    parser.add_argument("--annotator-b", type=Path, default=ROOT / "annotation/boundary20_annotator_B.csv")
    parser.add_argument("--annotator-c", type=Path, default=ROOT / "annotation/boundary20_annotator_C.csv")
    parser.add_argument("--adjudication", type=Path, default=ROOT / "annotation/boundary20_adjudication.csv")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=ROOT / "results/synchronization_validation/boundary20_metric_vs_human_summary.json",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=ROOT / "results/synchronization_validation/boundary20_metric_vs_human_summary.md",
    )
    args = parser.parse_args()

    if not args.ledger.exists():
        raise SystemExit(f"missing ledger: {args.ledger}")

    ledger = pd.read_csv(args.ledger)
    human = load_human_labels(args.annotator_a, args.annotator_b, args.annotator_c, args.adjudication)
    merged = human.merge(
        ledger[
            [
                "unit_id",
                "metric_sync_30",
                "metric_label",
                "lag_days",
                "selection_reason",
                "expected_failure_mode",
            ]
        ],
        on="unit_id",
        how="left",
    )

    summary = compute_summary(merged)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    args.md_out.write_text(render_markdown(summary))

    print(f"wrote {args.json_out}")
    print(f"wrote {args.md_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
