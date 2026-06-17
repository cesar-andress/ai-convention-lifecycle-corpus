#!/usr/bin/env python3
"""Summarize inter-annotator agreement for boundary20 package."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.corpus_paths import configure
from synchronization.blinded_protocol import cohens_kappa, is_filled, normalize_sync_label
from synchronization.boundary20 import ADJUDICATION_COLUMNS

ROOT = configure()

CATEGORIES = ["TRUE", "FALSE", "AMBIGUOUS"]
DECISIVE = ["TRUE", "FALSE"]
ANNOTATORS = ["annotator_A", "annotator_B", "annotator_C"]


def fleiss_kappa(matrix: list[list[int]]) -> float | None:
    if not matrix:
        return None
    n_items = len(matrix)
    n_cat = len(matrix[0])
    n_raters = sum(matrix[0])
    if n_raters < 2:
        return None

    p_j = [sum(row[j] for row in matrix) / (n_items * n_raters) for j in range(n_cat)]
    p_bar = sum(
        sum(row[j] ** 2 for j in range(n_cat)) - n_raters
        for row in matrix
    ) / (n_items * n_raters * (n_raters - 1))

    p_e = sum(p ** 2 for p in p_j)
    if p_e == 1.0:
        return 1.0 if p_bar == 1.0 else 0.0
    return (p_bar - p_e) / (1 - p_e)


def krippendorff_alpha_nominal(labels_by_unit: dict[str, list[str]]) -> float | None:
    values = CATEGORIES
    v_idx = {v: i for i, v in enumerate(values)}
    coincidences = [[0] * len(values) for _ in values]
    n_items = 0
    for labels in labels_by_unit.values():
        labs = [normalize_sync_label(x) for x in labels if is_filled(x) and normalize_sync_label(x) in values]
        if len(labs) < 2:
            continue
        n_items += 1
        for a in labs:
            for b in labs:
                coincidences[v_idx[a]][v_idx[b]] += 1
    if n_items == 0:
        return None
    total = sum(sum(row) for row in coincidences)
    if total == 0:
        return None
    n_c = len(values)
    obs = sum(coincidences[i][i] for i in range(n_c)) / total
    expected = sum(
        sum(coincidences[i]) * sum(coincidences[j][i] for j in range(n_c))
        for i in range(n_c)
    ) / (total * total)
    if expected == 1.0:
        return 1.0 if obs == 1.0 else 0.0
    return (obs - expected) / (1 - expected)


def build_merged(a_path: Path, b_path: Path, c_path: Path) -> pd.DataFrame:
    m = pd.read_csv(a_path)[["unit_id", "repo_id", "artifact_family", "artifact_path"]]
    for name, path in zip(ANNOTATORS, [a_path, b_path, c_path]):
        sub = pd.read_csv(path)[["unit_id", "manual_is_semantically_synchronized", "manual_confidence", "manual_reason_tag"]]
        sub = sub.rename(
            columns={
                "manual_is_semantically_synchronized": f"label_{name}",
                "manual_confidence": f"confidence_{name}",
                "manual_reason_tag": f"reason_tag_{name}",
            }
        )
        m = m.merge(sub, on="unit_id", how="left")
    return m


def export_adjudication(m_ann: pd.DataFrame, out_path: Path) -> pd.DataFrame:
    norm_cols = [f"norm_{n}" for n in ANNOTATORS]
    for col, raw in zip(norm_cols, [f"label_{n}" for n in ANNOTATORS]):
        m_ann[col] = m_ann[raw].map(normalize_sync_label)

    disagree = m_ann[m_ann[norm_cols].nunique(axis=1) > 1]
    rows = []
    for _, r in disagree.iterrows():
        rows.append(
            {
                "unit_id": r["unit_id"],
                "repo_id": r["repo_id"],
                "artifact_family": r["artifact_family"],
                "artifact_path": r["artifact_path"],
                "annotator_A_label": r["norm_annotator_A"],
                "annotator_B_label": r["norm_annotator_B"],
                "annotator_C_label": r["norm_annotator_C"],
                "annotator_A_reason_tag": r.get("reason_tag_annotator_A", ""),
                "annotator_B_reason_tag": r.get("reason_tag_annotator_B", ""),
                "annotator_C_reason_tag": r.get("reason_tag_annotator_C", ""),
                "adjudicated_label": "",
                "adjudicated_confidence": "",
                "adjudication_notes": "",
            }
        )
    df = pd.DataFrame(rows, columns=ADJUDICATION_COLUMNS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotator-a", type=Path, default=ROOT / "annotation/boundary20_annotator_A.csv")
    parser.add_argument("--annotator-b", type=Path, default=ROOT / "annotation/boundary20_annotator_B.csv")
    parser.add_argument("--annotator-c", type=Path, default=ROOT / "annotation/boundary20_annotator_C.csv")
    parser.add_argument("--adjudication-out", type=Path, default=ROOT / "annotation/boundary20_adjudication.csv")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=ROOT / "results/synchronization_validation/boundary20_agreement_summary.json",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=ROOT / "results/synchronization_validation/boundary20_agreement_summary.md",
    )
    args = parser.parse_args()

    m = build_merged(args.annotator_a, args.annotator_b, args.annotator_c)
    label_cols = [f"label_{n}" for n in ANNOTATORS]
    norm_cols = [f"norm_{n}" for n in ANNOTATORS]

    annotated_mask = m[label_cols].apply(lambda col: col.map(is_filled)).any(axis=1)
    all_three = m[label_cols].apply(lambda col: col.map(is_filled)).all(axis=1)
    m_ann = m[all_three].copy()
    for col, raw in zip(norm_cols, label_cols):
        m_ann[col] = m_ann[raw].map(normalize_sync_label)

    raw_agreement = float((m_ann[norm_cols].nunique(axis=1) == 1).mean()) if len(m_ann) else None

    pairwise = {}
    for a, b in combinations(ANNOTATORS, 2):
        ca, cb = f"norm_{a}", f"norm_{b}"
        sub = m_ann[m_ann[ca].isin(CATEGORIES) & m_ann[cb].isin(CATEGORIES)]
        if len(sub):
            dec = sub[sub[ca].isin(DECISIVE) & sub[cb].isin(DECISIVE)]
            pairwise[f"{a}_vs_{b}"] = {
                "n": len(sub),
                "raw_agreement": float((sub[ca] == sub[cb]).mean()),
                "cohens_kappa_3class": cohens_kappa(sub[ca].tolist(), sub[cb].tolist(), CATEGORIES),
                "cohens_kappa_decisive": cohens_kappa(dec[ca].tolist(), dec[cb].tolist(), DECISIVE) if len(dec) else None,
            }

    fleiss = None
    if len(m_ann):
        matrix = []
        cat_idx = {c: i for i, c in enumerate(CATEGORIES)}
        for _, row in m_ann.iterrows():
            counts = [0, 0, 0]
            for col in norm_cols:
                lab = row[col]
                if lab in cat_idx:
                    counts[cat_idx[lab]] += 1
            matrix.append(counts)
        fleiss = fleiss_kappa(matrix)

    labels_by_unit = {
        row.unit_id: [row[f"label_{n}"] for n in ANNOTATORS if is_filled(row[f"label_{n}"])]
        for _, row in m.iterrows()
        if any(is_filled(row[c]) for c in label_cols)
    }
    alpha = krippendorff_alpha_nominal(labels_by_unit)

    ambiguous_rate = float(m_ann[norm_cols].apply(lambda r: "AMBIGUOUS" in r.values, axis=1).mean()) if len(m_ann) else None

    disagreement_rows = []
    if len(m_ann):
        for _, row in m_ann.iterrows():
            labs = [row[c] for c in norm_cols]
            if len(set(labs)) > 1:
                disagreement_rows.append({"unit_id": row.unit_id, "A": labs[0], "B": labs[1], "C": labs[2]})

    by_family = []
    if len(m_ann):
        for fam, grp in m_ann.groupby("artifact_family"):
            by_family.append(
                {
                    "artifact_family": fam,
                    "n": len(grp),
                    "raw_agreement": float((grp[norm_cols].nunique(axis=1) == 1).mean()),
                }
            )

    adj_df = export_adjudication(m_ann, args.adjudication_out)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_units": len(m),
        "units_with_any_annotation": int(annotated_mask.sum()),
        "units_annotated_by_all_three": len(m_ann),
        "raw_agreement_all_three": raw_agreement,
        "fleiss_kappa": fleiss,
        "krippendorff_alpha_nominal": alpha,
        "ambiguous_rate": ambiguous_rate,
        "pairwise": pairwise,
        "by_artifact_family": by_family,
        "disagreement_table": disagreement_rows,
        "adjudication_rows": len(adj_df),
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(summary, indent=2, default=str) + "\n")

    lines = [
        "# Boundary20 agreement summary",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        f"- Units: {summary['total_units']}",
        f"- Annotated by all three: {summary['units_annotated_by_all_three']}",
        f"- Raw agreement: {_fmt_rate(raw_agreement)}",
        f"- Fleiss κ: {_fmt_rate(fleiss)}",
        f"- Krippendorff α: {_fmt_rate(alpha)}",
        f"- AMBIGUOUS rate: {_fmt_rate(ambiguous_rate)}",
        f"- Adjudication rows: {summary['adjudication_rows']}",
        "",
    ]
    if pairwise:
        lines.append("## Pairwise Cohen κ")
        for k, v in pairwise.items():
            lines.append(f"- {k}: agreement={v['raw_agreement']:.3f}, κ3={v['cohens_kappa_3class']}")
    args.md_out.write_text("\n".join(lines))

    print(f"wrote {args.json_out}")
    print(f"wrote {args.md_out}")
    print(f"wrote {args.adjudication_out} ({len(adj_df)} disagreements)")
    return 0


def _fmt_rate(value: float | None) -> str:
    return f"{value:.3f}" if value is not None else "n/a"


if __name__ == "__main__":
    sys.exit(main())
