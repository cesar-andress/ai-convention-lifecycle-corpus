#!/usr/bin/env python3
"""Prepare blinded dual-annotator workbooks and calibration subset."""

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
    BLINDED_CONTEXT_COLUMNS,
    BLINDED_MANUAL_COLUMNS,
    blinded_workbook_from_source,
    is_filled,
    norm,
)

ROOT = configure()

CALIBRATION_TARGET = 14


def _has_artifact_update(row: pd.Series) -> bool:
    return is_filled(row.get("artifact_update_commit"))


def select_calibration_units(source_df: pd.DataFrame, *, seed: int = 42) -> pd.DataFrame:
    """Select 12–15 blinded calibration units without exposing metric labels."""
    import random

    random.seed(seed)
    selected_ids: list[str] = []

    def pick(pool: pd.DataFrame, n: int, *, exclude: set[str]) -> None:
        candidates = pool[~pool["validation_unit_id"].isin(exclude)]
        if candidates.empty:
            return
        take = min(n, len(candidates))
        picks = candidates.sample(n=take, random_state=seed + len(selected_ids))
        for uid in picks["validation_unit_id"]:
            if uid not in exclude:
                selected_ids.append(uid)
                exclude.add(uid)

    exclude: set[str] = set()

    for family in ("instructions", "documentation", "configuration"):
        sub = source_df[source_df["artifact_family"] == family]
        with_update = sub[sub.apply(_has_artifact_update, axis=1)]
        without_update = sub[~sub.apply(_has_artifact_update, axis=1)]
        pick(with_update, 2, exclude=exclude)
        pick(without_update, 2, exclude=exclude)

    # Boundary / hard cases (identified from context, not metric fields).
    boundary_masks = []

    same_commit = source_df.apply(
        lambda r: is_filled(r.get("artifact_update_commit"))
        and norm(r.get("artifact_update_commit")) == norm(r.get("governed_code_commit")),
        axis=1,
    )
    boundary_masks.append(("same_commit_cochange", same_commit))

    artifact_in_governed = source_df.apply(
        lambda r: is_filled(r.get("artifact_path"))
        and norm(r.get("artifact_path")) in norm(r.get("changed_files_governed_commit", "")),
        axis=1,
    )
    boundary_masks.append(("artifact_in_governed_commit", artifact_in_governed))

    short_context = source_df.apply(
        lambda r: len(norm(r.get("commit_message_governed_code"))) < 40
        and not is_filled(r.get("artifact_update_commit")),
        axis=1,
    )
    boundary_masks.append(("sparse_context_no_update", short_context))

    unrelated_hint = source_df.apply(
        lambda r: is_filled(r.get("artifact_update_commit"))
        and norm(r.get("artifact_path")) not in norm(r.get("changed_files_artifact_update", "")),
        axis=1,
    )
    boundary_masks.append(("update_missing_artifact_path", unrelated_hint))

    for label, mask in boundary_masks:
        if len(selected_ids) >= CALIBRATION_TARGET:
            break
        pool = source_df[mask & ~source_df["validation_unit_id"].isin(exclude)]
        if pool.empty:
            continue
        pick(pool, 1, exclude=exclude)

    if len(selected_ids) < 12:
        remaining = source_df[~source_df["validation_unit_id"].isin(exclude)]
        pick(remaining, 12 - len(selected_ids), exclude=exclude)

    if len(selected_ids) > CALIBRATION_TARGET:
        selected_ids = selected_ids[:CALIBRATION_TARGET]

    cal = source_df[source_df["validation_unit_id"].isin(selected_ids)].copy()
    cal = cal.sort_values(["artifact_family", "validation_unit_id"]).reset_index(drop=True)
    return cal


def calibration_blinded(cal_df: pd.DataFrame) -> pd.DataFrame:
    blind = blinded_workbook_from_source(cal_df, annotator_id="")
    blind["calibration_purpose"] = (
        "Code calibration unit — annotate before the full workbook; discuss disagreements "
        "and refine the codebook before proceeding."
    )
    return blind[BLINDED_CONTEXT_COLUMNS + ["calibration_purpose"] + BLINDED_MANUAL_COLUMNS]


def render_protocol_readme(meta: dict) -> str:
    lines = [
        "# Blinded synchronization construct validation protocol",
        "",
        f"Generated: {meta['generated_at']}",
        "",
        "## Annotator workbooks (fill these)",
        "",
        "- `annotation/sync_construct_validation_blinded_annotator_A.csv`",
        "- `annotation/sync_construct_validation_blinded_annotator_B.csv`",
        "",
        "Codebook: `annotation/sync_construct_validation_codebook.md`",
        "",
        "## Calibration first",
        "",
        f"- `annotation/sync_construct_validation_calibration_units.csv` ({meta['calibration_n']} units)",
        "- Same columns as main workbooks; subset of unit IDs also present in A/B files.",
        "",
        "## Workflow",
        "",
        "1. Both annotators code calibration units independently.",
        "2. Compare labels, discuss disagreements, refine codebook.",
        "3. Both annotators code full blinded workbooks (100 units each).",
        "4. Run `make summarize-sync-agreement` to populate adjudication sheet.",
        "5. Adjudicator fills `annotation/sync_construct_validation_adjudication.csv`.",
        "6. Run `make summarize-sync-metric-vs-human`.",
        "",
        "## Blinding",
        "",
        "Annotator files exclude metric-derived fields (`metric_sync_30`, `lag_days`, "
        "`metric_label`, stratum/size fields).",
        "",
        f"**Calibration unit IDs:** {', '.join(meta.get('calibration_unit_ids', []))}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "annotation/sync_construct_validation_sample.csv",
    )
    parser.add_argument(
        "--annotator-a-out",
        type=Path,
        default=ROOT / "annotation/sync_construct_validation_blinded_annotator_A.csv",
    )
    parser.add_argument(
        "--annotator-b-out",
        type=Path,
        default=ROOT / "annotation/sync_construct_validation_blinded_annotator_B.csv",
    )
    parser.add_argument(
        "--calibration-out",
        type=Path,
        default=ROOT / "annotation/sync_construct_validation_calibration_units.csv",
    )
    parser.add_argument(
        "--adjudication-out",
        type=Path,
        default=ROOT / "annotation/sync_construct_validation_adjudication.csv",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"missing source sample: {args.input}")

    source_df = pd.read_csv(args.input)
    if "validation_unit_id" not in source_df.columns:
        raise SystemExit("source sample missing validation_unit_id")

    workbook_a = blinded_workbook_from_source(source_df, annotator_id="annotator_A")
    workbook_b = blinded_workbook_from_source(source_df, annotator_id="annotator_B")

    cal_source = select_calibration_units(source_df)
    cal_blinded = calibration_blinded(cal_source)

    adjudication_template = pd.DataFrame(columns=ADJUDICATION_COLUMNS)

    args.annotator_a_out.parent.mkdir(parents=True, exist_ok=True)
    workbook_a.to_csv(args.annotator_a_out, index=False)
    workbook_b.to_csv(args.annotator_b_out, index=False)
    cal_blinded.to_csv(args.calibration_out, index=False)
    adjudication_template.to_csv(args.adjudication_out, index=False)

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_rows": len(source_df),
        "calibration_n": len(cal_blinded),
        "calibration_unit_ids": cal_blinded["unit_id"].tolist(),
        "calibration_balance": cal_source.groupby("artifact_family").size().to_dict(),
        "calibration_with_artifact_update": int(cal_source.apply(_has_artifact_update, axis=1).sum()),
        "calibration_without_artifact_update": int((~cal_source.apply(_has_artifact_update, axis=1)).sum()),
        "blinded_columns": BLINDED_CONTEXT_COLUMNS + BLINDED_MANUAL_COLUMNS,
        "hidden_metric_columns": [
            "metric_sync_30",
            "metric_label",
            "lag_days",
            "repo_size_class",
            "repo_commit_count",
        ],
    }
    meta_path = args.annotator_a_out.parent / "sync_construct_validation_blinded_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")

    readme_path = ROOT / "results/synchronization_validation/sync_validation_blinded_protocol.md"
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    readme_path.write_text(render_protocol_readme(meta))

    print(f"wrote {args.annotator_a_out} ({len(workbook_a)} units)")
    print(f"wrote {args.annotator_b_out} ({len(workbook_b)} units)")
    print(f"wrote {args.calibration_out} ({len(cal_blinded)} units)")
    print(f"wrote {args.adjudication_out} (template, 0 rows)")
    print(f"wrote {meta_path}")
    print(f"wrote {readme_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
