#!/usr/bin/env python3
"""Run misguidance pilot on scope-sensitivity pilot repositories."""

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

from cochange.repo_utils import repo_dir_from_id
from lifecycle.corpus_paths import configure
from misguidance.detect_stale_references import (
    STATUS_AMBIGUOUS,
    STATUS_DOC_REFERENCE,
    STATUS_STALE,
    STATUS_UNRESOLVED,
    STATUS_VALID,
    aggregate_metrics,
    detect_stale_references,
)

ROOT = configure()


def _headline(summary_df: pd.DataFrame) -> dict[str, int | float | None]:
    instr = summary_df[summary_df["instruction_file"] != "__repo_total__"]
    total_refs = int(instr["n_references"].sum())
    total_primary_stale = int(instr["n_primary_stale"].sum())
    return {
        "n_references": total_refs,
        "n_valid": int(instr["n_valid"].sum()),
        "n_stale": int(instr["n_stale"].sum()),
        "n_stale_doc": int(instr["n_stale_doc"].sum()),
        "n_ambiguous": int(instr["n_ambiguous"].sum()),
        "n_unresolved": int(instr["n_unresolved"].sum()),
        "n_primary_stale": total_primary_stale,
        "stale_rate": (total_primary_stale / total_refs) if total_refs else None,
        "n_existed_before": int(instr["n_existed_before"].sum()),
        "n_never_existed": int(instr["n_never_existed"].sum()),
    }


def render_report(
    stale_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    out_path: Path,
    *,
    extraction_mode: str,
    compare_headline: dict[str, int | float | None] | None = None,
) -> None:
    instr = summary_df[summary_df["instruction_file"] != "__repo_total__"].copy()
    repo_totals = summary_df[summary_df["instruction_file"] == "__repo_total__"].copy()
    headline = _headline(summary_df)

    total_refs = int(headline["n_references"])
    total_primary_stale = int(headline["n_primary_stale"])
    total_stale_all = int(instr["n_stale_all"].sum())
    total_valid = int(headline["n_valid"])
    total_existed_before = int(headline["n_existed_before"])
    total_never_existed = int(headline["n_never_existed"])

    cat_cols = [c for c in summary_df.columns if c.startswith("n_cat_")]
    category_totals: Counter[str] = Counter()
    for col in cat_cols:
        name = col.replace("n_cat_", "")
        category_totals[name] = int(instr[col].fillna(0).sum())

    hist_df = stale_df[stale_df["historical_existence"].astype(str).str.len() > 0]
    hist_by_status = (
        hist_df.groupby(["status", "historical_existence"]).size().reset_index(name="n")
        if not hist_df.empty
        else pd.DataFrame()
    )

    stale_primary = stale_df[stale_df["counts_toward_primary_misguidance"] == True]  # noqa: E712
    stale_doc = stale_df[stale_df["status"] == STATUS_DOC_REFERENCE]
    drift_strong = stale_df[stale_df["historical_existence"] == "existed_before"]
    valid_examples = stale_df[stale_df["status"] == STATUS_VALID].head(8)
    stale_examples = pd.concat([stale_primary, stale_doc, drift_strong]).drop_duplicates().head(15)

    mode_label = "misguidance extraction (v2)" if extraction_mode == "v2" else "scope-biased extraction (v1)"
    lines = [
        "# Misguidance pilot report",
        "",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        f"Extraction mode: **{mode_label}**",
        "",
        "**Pilot only — no population claims.** Stale references are *possible instruction–code drift*, not proven errors.",
        "",
        "Definitions: `docs/misguidance_definition.md`, `docs/misguidance_extraction_audit.md`",
        "",
    ]

    if compare_headline:
        v1_refs = int(compare_headline["n_references"])
        v2_refs = total_refs
        delta_refs = v2_refs - v1_refs
        lines.extend(
            [
                "## Pilot v1 vs v2 comparison",
                "",
                "| Metric | v1 (scope extraction) | v2 (misguidance extraction) | Δ |",
                "|--------|----------------------:|----------------------------:|--:|",
                f"| References extracted | {v1_refs} | {v2_refs} | {delta_refs:+d} |",
                f"| Valid | {int(compare_headline['n_valid'])} | {total_valid} | {total_valid - int(compare_headline['n_valid']):+d} |",
                f"| Primary stale | {int(compare_headline['n_primary_stale'])} | {total_primary_stale} | {total_primary_stale - int(compare_headline['n_primary_stale']):+d} |",
                f"| Ambiguous | {int(compare_headline['n_ambiguous'])} | {int(headline['n_ambiguous'])} | {int(headline['n_ambiguous']) - int(compare_headline['n_ambiguous']):+d} |",
                f"| Unresolved | {int(compare_headline['n_unresolved'])} | {int(headline['n_unresolved'])} | {int(headline['n_unresolved']) - int(compare_headline['n_unresolved']):+d} |",
                f"| Primary stale rate | {100.0 * float(compare_headline['stale_rate'] or 0):.1f}% | {100.0 * float(headline['stale_rate'] or 0):.1f}% | — |",
                f"| `existed_before` (history) | {int(compare_headline['n_existed_before'])} | {total_existed_before} | {total_existed_before - int(compare_headline['n_existed_before']):+d} |",
                "",
            ]
        )

    lines.extend(
        [
            "## Pilot coverage",
            "",
            f"- Repositories: **{repo_totals['repo_id'].nunique()}**",
            f"- Instruction files: **{len(instr)}**",
            f"- References extracted: **{total_refs}**",
            "",
            "## Headline counts (instruction files)",
            "",
            f"- Valid at HEAD: **{total_valid}**",
            f"- Primary stale (excludes docs/commands/ambiguous): **{total_primary_stale}**",
            f"- Stale documentation references: **{int(headline['n_stale_doc'])}**",
            f"- All stale-type (primary + doc): **{total_stale_all}**",
            f"- Ambiguous: **{int(headline['n_ambiguous'])}**",
            f"- Unresolved: **{int(headline['n_unresolved'])}**",
            "",
            f"Primary stale rate (conservative): **{100.0 * float(headline['stale_rate'] or 0):.1f}%** "
            f"({total_primary_stale}/{total_refs})",
            "",
            "## Historical existence (stale, doc-stale, ambiguous, unresolved)",
            "",
            f"- Previously existed (`existed_before`): **{total_existed_before}**",
            f"- Never existed in git history: **{total_never_existed}**",
            "",
        ]
    )

    if not hist_by_status.empty:
        lines.append("### By detection status")
        lines.append("")
        for _, row in hist_by_status.sort_values(["status", "historical_existence"]).iterrows():
            lines.append(f"- `{row['status']}` + `{row['historical_existence']}`: {int(row['n'])}")

    lines.extend(["", "## Category breakdown", ""])
    for cat, count in sorted(category_totals.items()):
        if count:
            lines.append(f"- `{cat}`: {count}")

    lines.extend(["", "## Per instruction file", ""])
    lines.append("| repo | instruction | n_refs | valid | primary_stale | stale_doc | ambiguous | unresolved | stale_rate |")
    lines.append("|------|-------------|--------|-------|---------------|-----------|-----------|------------|------------|")
    for _, row in instr.sort_values(["repo_id", "instruction_file"]).iterrows():
        rate = row["stale_rate"]
        rate_s = f"{100.0 * rate:.1f}%" if pd.notna(rate) else "n/a"
        lines.append(
            f"| `{row['repo_id']}` | `{row['instruction_file']}` | {int(row['n_references'])} | "
            f"{int(row['n_valid'])} | {int(row['n_primary_stale'])} | {int(row['n_stale_doc'])} | "
            f"{int(row['n_ambiguous'])} | {int(row['n_unresolved'])} | {rate_s} |"
        )

    lines.extend(["", "## Research questions (pilot answers)", ""])
    if compare_headline:
        delta_refs = total_refs - int(compare_headline["n_references"])
        lines.append(
            "1. **How much did extraction volume increase?** "
            + f"v2 extracted **{total_refs}** refs vs v1 **{int(compare_headline['n_references'])}** "
            + f"(**{delta_refs:+d}**, {100.0 * delta_refs / max(int(compare_headline['n_references']), 1):.1f}% relative increase)."
        )
    else:
        lines.append(f"1. **References extracted:** {total_refs}.")

    lines.extend(
        [
            "2. **How many stale references now appear?** "
            + f"Primary stale **{total_primary_stale}**, doc-stale **{int(headline['n_stale_doc'])}**, "
            + f"ambiguous **{int(headline['n_ambiguous'])}**, unresolved **{int(headline['n_unresolved'])}**.",
            "3. **How many previously existed?** "
            + f"`existed_before={total_existed_before}` (stronger drift evidence), "
            + f"`never_existed={total_never_existed}` (possible parser noise or never-valid text).",
            "4. **Is misguidance now measurable?** "
            + (
                "Yes — non-zero stale or historical drift signal under misguidance extraction."
                if total_primary_stale > 0 or total_existed_before > 0 or int(headline["n_stale_doc"]) > 0
                else "Still weak — review extraction audit and ambiguous/unresolved rows."
            ),
            "5. **Enough signal for full-corpus collection?** "
            + (
                "Promising for a bounded full-corpus *pilot extension* after manual spot-check of "
                f"`existed_before` examples ({total_existed_before} refs); not ready for population claims."
                if total_existed_before > 0 or total_primary_stale >= 5
                else "Not yet — improve extraction/validation loop before scaling collection."
            ),
            "",
            "## Examples — valid references",
            "",
        ]
    )

    if valid_examples.empty:
        lines.append("_None._")
    else:
        for _, row in valid_examples.iterrows():
            lines.append(
                f"- `{row['repo_id']}` / `{row['instruction_file']}`: "
                f"`{row['reference']}` → `{row['resolved_path']}` ({row['status']})"
            )

    lines.extend(["", "## Examples — possible drift (stale / existed_before)", ""])
    if stale_examples.empty:
        lines.append("_None under current rules._")
    else:
        for _, row in stale_examples.iterrows():
            lines.append(
                f"- `{row['repo_id']}` / `{row['instruction_file']}`: "
                f"`{row['reference']}` → `{row['resolved_path']}` "
                f"({row['status']}, `{row.get('misguidance_category', '')}`, "
                f"history=`{row.get('historical_existence', '')}`)"
            )

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- Stale labels indicate *possible* instruction–code drift, not agent harm or author error.",
            "- Commands are not executed; command targets are not auto-stale.",
            "- Documentation references tracked separately from primary misguidance.",
            "- Eight pilot repos — not a population sample.",
            "",
        ]
    )

    out_path.write_text("\n".join(lines), encoding="utf-8")


def run_pilot(
    pilot_csv: Path,
    out_dir: Path,
    *,
    misguidance_extraction: bool,
    check_history: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    pilot = pd.read_csv(pilot_csv)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_refs: list[dict] = []
    summaries: list[dict] = []

    for _, pr in pilot.iterrows():
        repo_id = pr["repo_id"]
        repo_dir = repo_dir_from_id(repo_id, ROOT / "data/repos")
        if not repo_dir.is_dir():
            print(f"skip {repo_id}: clone missing at {repo_dir}", file=sys.stderr)
            continue

        repo_rows: list[dict] = []
        for instr in str(pr["pilot_instruction_files"]).split(";"):
            instr = instr.strip()
            if not instr:
                continue
            rows = detect_stale_references(
                repo_id,
                repo_dir,
                instr,
                check_history=check_history,
                misguidance_extraction=misguidance_extraction,
            )
            all_refs.extend(rows)
            repo_rows.extend(rows)
            summaries.append(aggregate_metrics(rows, repo_id, instr))
            print(
                f"{repo_id} {instr}: refs={len(rows)} "
                f"primary_stale={summaries[-1]['n_primary_stale']} "
                f"stale_doc={summaries[-1]['n_stale_doc']} "
                f"ambiguous={summaries[-1]['n_ambiguous']}"
            )

        if repo_rows:
            summaries.append(aggregate_metrics(repo_rows, repo_id, None))

    return pd.DataFrame(all_refs), pd.DataFrame(summaries)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pilot-repos",
        type=Path,
        default=ROOT / "results/cochange/pilot/pilot_repos.csv",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "results/misguidance/pilot",
    )
    parser.add_argument(
        "--extraction-mode",
        choices=("v1", "v2"),
        default="v1",
        help="v1=scope-biased parser output; v2=misguidance_mode extraction",
    )
    parser.add_argument("--no-history", action="store_true", help="Skip git history checks")
    args = parser.parse_args()

    misguidance_extraction = args.extraction_mode == "v2"
    stale_df, summary_df = run_pilot(
        args.pilot_repos,
        args.out_dir,
        misguidance_extraction=misguidance_extraction,
        check_history=not args.no_history,
    )

    compare_headline = None
    if misguidance_extraction:
        v1_summary_path = ROOT / "results/misguidance/pilot/misguidance_summary.csv"
        if v1_summary_path.is_file():
            compare_headline = _headline(pd.read_csv(v1_summary_path))

    stale_path = args.out_dir / "stale_references.csv"
    summary_path = args.out_dir / "misguidance_summary.csv"
    report_path = args.out_dir / "misguidance_report.md"

    stale_df.to_csv(stale_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    render_report(
        stale_df,
        summary_df,
        report_path,
        extraction_mode=args.extraction_mode,
        compare_headline=compare_headline,
    )

    meta = {
        "extraction_mode": args.extraction_mode,
        "headline": _headline(summary_df),
        "compare_v1": compare_headline,
    }
    (args.out_dir / "misguidance_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {stale_path} ({len(stale_df)} rows)")
    print(f"wrote {summary_path} ({len(summary_df)} rows)")
    print(f"wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
