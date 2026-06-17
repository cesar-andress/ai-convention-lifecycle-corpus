#!/usr/bin/env python3
"""Re-run scope-sensitivity pilot with v2 reference extraction and compare to v1."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cochange.changed_files import manifest_output_path
from cochange.content_refs import PARSER_VERSION, extract_content_references
from cochange.repo_utils import repo_dir_from_id, safe_repo_dirname
from cochange.scope_modes import ScopeMode
from cochange.sync_engine import build_commit_index, compute_scope_metrics
from lifecycle.corpus_paths import configure
from lifecycle.git_utils import list_head_files

ROOT = configure()

METRIC_COLUMNS = [
    "repo_id",
    "instruction_file",
    "scope_mode",
    "governed_scope_description",
    "n_governed_paths_head",
    "n_governed_code_events",
    "n_instruction_updates",
    "sync_0",
    "sync_7",
    "sync_30",
    "median_lag_days_30",
    "n_content_refs",
    "n_content_refs_used",
    "notes",
    "parser_version",
]


def parse_windows(text: str) -> tuple[int, ...]:
    return tuple(int(x.strip()) for x in text.split(",") if x.strip())


def load_v1_metrics(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["parser_version"] = "v1"
    return df


def comparison_table(v1: pd.DataFrame, v2: pd.DataFrame) -> pd.DataFrame:
    content_v1 = v1[v1.scope_mode == "content_referenced"][
        ["repo_id", "instruction_file", "n_content_refs", "n_content_refs_used", "sync_30"]
    ].rename(
        columns={
            "n_content_refs": "v1_refs",
            "n_content_refs_used": "v1_refs_used",
            "sync_30": "v1_sync_30",
        }
    )
    content_v2 = v2[v2.scope_mode == "content_referenced"][
        ["repo_id", "instruction_file", "n_content_refs", "n_content_refs_used", "sync_30"]
    ].rename(
        columns={
            "n_content_refs": "v2_refs",
            "n_content_refs_used": "v2_refs_used",
            "sync_30": "v2_sync_30",
        }
    )
    merged = content_v1.merge(content_v2, on=["repo_id", "instruction_file"], how="outer")
    merged["delta_refs_used"] = merged["v2_refs_used"] - merged["v1_refs_used"]
    merged["delta_sync_30"] = merged["v2_sync_30"] - merged["v1_sync_30"]
    return merged.sort_values(["repo_id", "instruction_file"])


def render_v2_report(
    metrics_df: pd.DataFrame,
    pilot_df: pd.DataFrame,
    compare_df: pd.DataFrame,
) -> str:
    lines = [
        "# Scope sensitivity pilot report (v2 parser)",
        "",
        f"**Parser version:** {PARSER_VERSION}  ",
        "Methodological pilot only — do not generalize to a population.",
        "",
        "## Sync@30 by scope mode (v2)",
        "",
        "| repo | instruction | repo_wide | subtree | content_referenced | refs_used |",
        "|------|-------------|-----------|---------|-------------------|-----------|",
    ]
    pivot = metrics_df.pivot_table(
        index=["repo_id", "instruction_file"],
        columns="scope_mode",
        values="sync_30",
        aggfunc="first",
    )
    used = metrics_df[metrics_df.scope_mode == "content_referenced"].set_index(
        ["repo_id", "instruction_file"]
    )["n_content_refs_used"]
    for (repo_id, instr), row in pivot.iterrows():
        ru = used.get((repo_id, instr), float("nan"))

        def fmt(v):
            return f"{v:.1%}" if pd.notna(v) else "n/a"

        lines.append(
            f"| `{repo_id}` | `{instr}` | {fmt(row.get('repo_wide'))} | "
            f"{fmt(row.get('subtree'))} | {fmt(row.get('content_referenced'))} | "
            f"{int(ru) if pd.notna(ru) else 0} |"
        )

    lines.extend(["", "## v1 vs v2 content-referenced comparison", ""])
    lines.append(
        "| repo | instruction | v1 refs | v1 used | v2 refs | v2 used | v1 sync@30 | v2 sync@30 | Δ sync@30 |"
    )
    lines.append(
        "|------|-------------|---------|---------|---------|---------|------------|------------|-----------|"
    )
    for _, r in compare_df.iterrows():
        def pct(v):
            return f"{v:.1%}" if pd.notna(v) else "n/a"

        lines.append(
            f"| `{r['repo_id']}` | `{r['instruction_file']}` | "
            f"{int(r['v1_refs']) if pd.notna(r['v1_refs']) else 0} | "
            f"{int(r['v1_refs_used']) if pd.notna(r['v1_refs_used']) else 0} | "
            f"{int(r['v2_refs']) if pd.notna(r['v2_refs']) else 0} | "
            f"{int(r['v2_refs_used']) if pd.notna(r['v2_refs_used']) else 0} | "
            f"{pct(r['v1_sync_30'])} | {pct(r['v2_sync_30'])} | {pct(r['delta_sync_30']) if pd.notna(r['delta_sync_30']) else 'n/a'} |"
        )

    zero_v2 = compare_df[compare_df["v2_refs_used"].fillna(0) == 0]
    lines.extend(
        [
            "",
            "## Zero usable references (v2)",
            "",
        ]
    )
    if zero_v2.empty:
        lines.append("All instruction files have at least one high/medium confidence reference used for scope.")
    else:
        for _, r in zero_v2.iterrows():
            lines.append(f"- `{r['repo_id']}` / `{r['instruction_file']}`")

    lines.extend(["", "## Interpretation guardrail", "", "Optimize for scope validity, not recall.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-repos", type=Path, default=ROOT / "results/cochange/pilot/pilot_repos.csv")
    parser.add_argument("--manifest-dir", type=Path, default=ROOT / "results/cochange/pilot")
    parser.add_argument("--v1-metrics", type=Path, default=ROOT / "results/cochange/pilot/scope_sensitivity_metrics.csv")
    parser.add_argument("--out-csv", type=Path, default=ROOT / "results/cochange/pilot/scope_sensitivity_v2.csv")
    parser.add_argument("--out-report", type=Path, default=ROOT / "results/cochange/pilot/scope_sensitivity_v2_report.md")
    parser.add_argument("--windows", default="0,7,30")
    args = parser.parse_args()

    windows = parse_windows(args.windows)
    pilot_df = pd.read_csv(args.pilot_repos)
    repos_dir = ROOT / "data/repos"
    all_metrics: list[dict] = []
    all_refs: list[dict] = []

    for _, pilot_row in pilot_df.iterrows():
        repo_id = pilot_row["repo_id"]
        repo_dir = repo_dir_from_id(repo_id, repos_dir)
        manifest_path = manifest_output_path(args.manifest_dir, repo_id)
        if not manifest_path.exists():
            print(f"skip {repo_id}: missing manifest {manifest_path}", file=sys.stderr)
            continue

        manifest = pd.read_parquet(manifest_path)
        by_commit = build_commit_index(manifest)
        head_files = set(list_head_files(repo_dir))
        instruction_files = [p for p in str(pilot_row.get("pilot_instruction_files", "")).split(";") if p]
        repo_out_dir = args.manifest_dir / safe_repo_dirname(repo_id)
        repo_out_dir.mkdir(parents=True, exist_ok=True)

        for instruction_path in instruction_files:
            ref_rows = extract_content_references(repo_id, repo_dir, instruction_path, head_files)
            all_refs.extend(ref_rows)
            safe_instr = instruction_path.replace("/", "__")
            pd.DataFrame(ref_rows).to_csv(repo_out_dir / f"content_references_v2_{safe_instr}.csv", index=False)

            for mode in ScopeMode:
                metrics = compute_scope_metrics(
                    repo_id,
                    instruction_path,
                    by_commit,
                    head_files,
                    ref_rows,
                    mode,
                    windows=windows,
                )
                metrics["parser_version"] = PARSER_VERSION
                all_metrics.append(metrics)

    metrics_df = pd.DataFrame(all_metrics)
    for col in METRIC_COLUMNS:
        if col not in metrics_df.columns:
            metrics_df[col] = None
    metrics_df = metrics_df[METRIC_COLUMNS]
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(args.out_csv, index=False)
    print(f"wrote {args.out_csv}")

    v1 = load_v1_metrics(args.v1_metrics)
    compare_df = comparison_table(v1, metrics_df)
    compare_df.to_csv(args.out_csv.parent / "scope_parser_v1_v2_comparison.csv", index=False)

    report = render_v2_report(metrics_df, pilot_df, compare_df)
    args.out_report.write_text(report)
    print(f"wrote {args.out_report}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
