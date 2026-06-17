#!/usr/bin/env python3
"""Prepare boundary20 purposive validation package."""

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
from synchronization.blinded_protocol import normalize_sync_label
from synchronization.boundary20 import (
    ADJUDICATION_COLUMNS,
    build_blinded_row,
    blinded_workbook,
    select_boundary20,
)

ROOT = configure()


def load_disagreement_ids() -> set[str]:
    a_path = ROOT / "annotation/sync_construct_validation_blinded_annotator_A.csv"
    b_path = ROOT / "annotation/sync_construct_validation_blinded_annotator_B.csv"
    if not a_path.exists() or not b_path.exists():
        return set()
    a = pd.read_csv(a_path)
    b = pd.read_csv(b_path)
    merged = a[["unit_id", "manual_is_semantically_synchronized"]].merge(
        b[["unit_id", "manual_is_semantically_synchronized"]],
        on="unit_id",
        suffixes=("_A", "_B"),
    )
    merged["A"] = merged["manual_is_semantically_synchronized_A"].map(normalize_sync_label)
    merged["B"] = merged["manual_is_semantically_synchronized_B"].map(normalize_sync_label)
    return set(merged.loc[merged.A != merged.B, "unit_id"])


def render_protocol_snippet(ledger: pd.DataFrame, disagree_n: int) -> str:
    return "\n".join(
        [
            "# Boundary20 protocol report",
            "",
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "See full narrative in `results/synchronization_validation/boundary20_protocol_report.md`.",
            "",
            f"- Selected units: **{len(ledger)}**",
            f"- A/B disagreements in parent frame: **{disagree_n}**",
            f"- Instructions in boundary20: **{(ledger.artifact_family == 'instructions').sum()}**",
            "",
            "## Selection ledger (researcher-only)",
            "",
            ledger.to_markdown(index=False),
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "annotation/sync_construct_validation_sample.csv",
    )
    parser.add_argument(
        "--ledger-out",
        type=Path,
        default=ROOT / "results/synchronization_validation/boundary20_selection_ledger.csv",
    )
    parser.add_argument(
        "--annotator-a-out",
        type=Path,
        default=ROOT / "annotation/boundary20_annotator_A.csv",
    )
    parser.add_argument(
        "--annotator-b-out",
        type=Path,
        default=ROOT / "annotation/boundary20_annotator_B.csv",
    )
    parser.add_argument(
        "--annotator-c-out",
        type=Path,
        default=ROOT / "annotation/boundary20_annotator_C.csv",
    )
    parser.add_argument(
        "--adjudication-out",
        type=Path,
        default=ROOT / "annotation/boundary20_adjudication.csv",
    )
    parser.add_argument("--target-n", type=int, default=20)
    args = parser.parse_args()

    pool = pd.read_csv(args.source)
    disagree_ids = load_disagreement_ids()
    ledger = select_boundary20(pool, disagree_ids, target_n=args.target_n)

    pool_idx = pool.set_index("validation_unit_id")
    repos_dir = ROOT / "data/repos"
    blinded_rows = []
    for _, led in ledger.iterrows():
        row = pool_idx.loc[led["unit_id"]]
        blinded_rows.append(build_blinded_row(row, led, repos_dir))

    wb_a = blinded_workbook(blinded_rows, "annotator_A")
    wb_b = blinded_workbook(blinded_rows, "annotator_B")
    wb_c = blinded_workbook(blinded_rows, "annotator_C")

    args.ledger_out.parent.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(args.ledger_out, index=False)
    wb_a.to_csv(args.annotator_a_out, index=False)
    wb_b.to_csv(args.annotator_b_out, index=False)
    wb_c.to_csv(args.annotator_c_out, index=False)
    pd.DataFrame(columns=ADJUDICATION_COLUMNS).to_csv(args.adjudication_out, index=False)

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_selected": len(ledger),
        "ab_disagreements_in_pool": len(disagree_ids),
        "selection_reason_counts": ledger["selection_reason"].value_counts().to_dict(),
        "failure_mode_counts": ledger["expected_failure_mode"].value_counts().to_dict(),
        "family_counts": ledger["artifact_family"].value_counts().to_dict(),
        "metric_label_counts": ledger["metric_label"].value_counts().to_dict(),
        "unit_ids": ledger["unit_id"].tolist(),
    }
    meta_path = args.ledger_out.parent / "boundary20_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")

    print(f"wrote {args.ledger_out}")
    print(f"wrote {args.annotator_a_out}")
    print(f"wrote {args.annotator_b_out}")
    print(f"wrote {args.annotator_c_out}")
    print(f"wrote {args.adjudication_out} (template)")
    print(f"wrote {meta_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
