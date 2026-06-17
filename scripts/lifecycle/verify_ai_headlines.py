#!/usr/bin/env python3
"""Verify bundled AI-convention headline statistics remain unchanged."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.adoption_maintenance import (
    THRESHOLDS,
    add_states_and_flags,
    gap_artifact_mature,
    gap_repo_level,
    gap_repo_maturity_matched_unrestricted,
    gap_repo_restricted,
)
from lifecycle.corpus_paths import configure

ROOT = configure()
FROZEN = ROOT / "data" / "lifecycle" / "artifact_states_v2.parquet"
BUNDLED = ROOT / "results" / "lifecycle" / "adoption_maintenance_v2.json"

EXPECTED = {
    "n_repos": 209,
    "artifact_gap_mature": 0.56,
    "repo_gap": 0.072,
    "restricted_gap": 0.214,
    "maturity_matched_gap": 0.684,
    "n_mature_present": 577,
}


def main() -> int:
    bundled = json.loads(BUNDLED.read_text())
    h = bundled["headline_primary_180"]
    checks = [
        ("bundled n_repos", h["n_repos"], EXPECTED["n_repos"]),
        ("bundled artifact_gap", round(h["artifact_gap_mature"], 3), EXPECTED["artifact_gap_mature"]),
        ("bundled repo_gap", round(h["repo_gap"], 3), EXPECTED["repo_gap"]),
        ("bundled n_mature_present", h["n_mature_present"], EXPECTED["n_mature_present"]),
    ]
    restricted = json.loads((ROOT / "results/lifecycle/restricted_repository_gap_v2.json").read_text())
    checks.extend(
        [
            ("bundled restricted_gap", round(restricted["restricted_repository_gap"], 3), EXPECTED["restricted_gap"]),
            (
                "bundled maturity_matched_gap",
                round(restricted["maturity_matched_unrestricted_repository_gap"], 3),
                EXPECTED["maturity_matched_gap"],
            ),
        ]
    )

    df = pd.read_parquet(FROZEN)
    t = 180
    art = gap_artifact_mature(df, t)
    repo = gap_repo_level(df, t)
    rest = gap_repo_restricted(df, t)
    mat = gap_repo_maturity_matched_unrestricted(df, t)
    checks.extend(
        [
            ("parquet artifact_gap", round(art["gap_rate"], 3), EXPECTED["artifact_gap_mature"]),
            ("parquet repo_gap", round(repo["gap_rate"], 3), EXPECTED["repo_gap"]),
            ("parquet restricted_gap", round(rest["gap_rate"], 3), EXPECTED["restricted_gap"]),
            ("parquet maturity_matched_gap", round(mat["gap_rate"], 3), EXPECTED["maturity_matched_gap"]),
            ("parquet n_mature_present", art["n_mature_present"], EXPECTED["n_mature_present"]),
        ]
    )

    failed = 0
    for label, got, exp in checks:
        if got != exp:
            print(f"FAIL {label}: got {got} expected {exp}")
            failed += 1
        else:
            print(f"OK {label}: {got}")

    if failed:
        return 1
    print("AI-convention headline verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
