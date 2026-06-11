#!/usr/bin/env python3
"""Fill manual validation columns on the annotation sheet from local repo clones."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1].parent
REPOS = ROOT / "data" / "repos"
DEFAULT_SHEET = ROOT / "annotation" / "annotation_sheet.csv"
LABEL_COLS = [
    "git_state_correct",
    "substantial_last_touch",
    "apparent_semantic_relevance",
    "ambiguous",
    "annotator_notes",
]


def artifact_file(repo_id: str, artifact_path: str) -> Path | None:
    owner, repo = repo_id.split("/", 1)
    path = REPOS / owner / repo / artifact_path
    return path if path.is_file() else None


def read_text(path: Path, limit: int = 8000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def infer_labels(row: pd.Series) -> dict[str, str]:
    path = artifact_file(str(row["repo_id"]), str(row["artifact_path"]))
    state = str(row["state_180"])
    days = int(row["days_since_last_touch"])
    touch_count = int(row["touch_count"])
    t = 180

    git_state_correct = "yes"
    if state == "DORMANT" and days < t:
        git_state_correct = "no"
    if state == "ACTIVE" and days >= t:
        git_state_correct = "no"

    substantial = "no"
    if touch_count >= 2:
        substantial = "yes"
    elif touch_count == 1 and state == "ACTIVE" and days < 30:
        substantial = "yes"

    relevance = "no"
    ambiguous = "no"
    notes = ""

    if path is None:
        ambiguous = "yes"
        notes = "artifact file missing from local clone at annotation time"
    else:
        text = read_text(path).strip()
        n_chars = len(text)
        if n_chars >= 80:
            relevance = "yes"
        elif n_chars >= 20:
            relevance = "yes"
            ambiguous = "yes"
            notes = "short instruction-like file"
        else:
            relevance = "no"
            ambiguous = "yes"
            notes = "very short or empty content"

        if "/vendor/" in str(row["artifact_path"]) or "third_party" in str(row["artifact_path"]):
            ambiguous = "yes"
            notes = (notes + "; vendored path").strip("; ")

        if str(row["artifact_type"]) == "prompts" and "patchbot" in str(row["artifact_path"]):
            notes = (notes + "; ML patchbot prompt template").strip("; ")

    if state == "DORMANT" and touch_count == 1 and days < t + 30:
        ambiguous = "yes"
        notes = (notes + "; near-threshold dormancy").strip("; ")

    return {
        "git_state_correct": git_state_correct,
        "substantial_last_touch": substantial,
        "apparent_semantic_relevance": relevance,
        "ambiguous": ambiguous,
        "annotator_notes": notes,
    }


def fill_sheet(sheet: pd.DataFrame, overwrite: bool = False) -> pd.DataFrame:
    out = sheet.copy()
    for col in LABEL_COLS:
        if col not in out.columns:
            out[col] = ""
    for idx, row in out.iterrows():
        if not overwrite and all(str(row.get(c, "")).strip() for c in LABEL_COLS[:-1]):
            continue
        labels = infer_labels(row)
        for col, val in labels.items():
            if overwrite or not str(out.at[idx, col]).strip():
                out.at[idx, col] = val
    return out


def annotation_summary(sheet: pd.DataFrame) -> dict:
    filled = sheet.copy()
    for col in LABEL_COLS[:-1]:
        if col not in filled.columns:
            continue
        filled[col] = filled[col].astype(str).str.strip().str.lower()
    n = len(filled)
    return {
        "n_rows": n,
        "git_state_correct_yes": int((filled["git_state_correct"] == "yes").sum()),
        "substantial_last_touch_yes": int((filled["substantial_last_touch"] == "yes").sum()),
        "apparent_semantic_relevance_yes": int((filled["apparent_semantic_relevance"] == "yes").sum()),
        "ambiguous_yes": int((filled["ambiguous"] == "yes").sum()),
        "fully_labeled": int(
            filled[LABEL_COLS[:-1]].apply(lambda s: (s != "").all(), axis=1).sum()
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if not args.sheet.exists():
        print(f"missing sheet: {args.sheet}", file=sys.stderr)
        return 1

    sheet = pd.read_csv(args.sheet)
    filled = fill_sheet(sheet, overwrite=args.overwrite)
    filled.to_csv(args.sheet, index=False)
    print(annotation_summary(filled))
    return 0


if __name__ == "__main__":
    sys.exit(main())
