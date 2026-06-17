#!/usr/bin/env python3
"""Run scope-sensitivity pilot: compare sync metrics under repo-wide, subtree, content-referenced scopes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cochange.changed_files import extract_changed_files, manifest_output_path
from cochange.content_refs import extract_content_references
from cochange.repo_utils import ensure_repo, repo_dir_from_id, repo_url_from_discovered, safe_repo_dirname
from cochange.scope_modes import ScopeMode
from cochange.sync_engine import build_commit_index, compute_scope_metrics
from lifecycle.corpus_paths import configure
from lifecycle.git_utils import count_repo_commits, list_head_files

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
]


def parse_windows(text: str) -> tuple[int, ...]:
    return tuple(int(x.strip()) for x in text.split(",") if x.strip())


def load_pilot_repos(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"missing pilot repo list: {path} (run select_pilot_repos.py first)")
    return pd.read_csv(path)


def render_scope_report(metrics_df: pd.DataFrame, pilot_df: pd.DataFrame) -> str:
    lines = [
        "# Scope sensitivity pilot report",
        "",
        "Methodological pilot only — do not generalize to a population.",
        "",
        f"**Repositories:** {metrics_df['repo_id'].nunique()}  ",
        f"**Instruction files analyzed:** {metrics_df['instruction_file'].nunique()}  ",
        f"**Metric rows:** {len(metrics_df)} (3 scope modes per instruction file)  ",
        "",
        "## Pilot repositories",
        "",
        "| repo_id | reason | instruction files |",
        "|---------|--------|-------------------|",
    ]
    for _, row in pilot_df.iterrows():
        lines.append(
            f"| `{row['repo_id']}` | {row['reason_selected']} | `{row.get('pilot_instruction_files','')}` |"
        )

    lines.extend(["", "## Sync@30 by scope mode", ""])
    pivot = metrics_df.pivot_table(
        index=["repo_id", "instruction_file"],
        columns="scope_mode",
        values="sync_30",
        aggfunc="first",
    )
    if not pivot.empty:
        lines.append("| repo | instruction | repo_wide | subtree | content_referenced |")
        lines.append("|------|-------------|-----------|---------|-------------------|")
        for (repo_id, instr), row in pivot.iterrows():
            def fmt(v):
                return f"{v:.1%}" if pd.notna(v) else "n/a"

            lines.append(
                f"| `{repo_id}` | `{instr}` | {fmt(row.get('repo_wide'))} | "
                f"{fmt(row.get('subtree'))} | {fmt(row.get('content_referenced'))} |"
            )

    lines.extend(["", "## Strong repo-wide vs content-referenced divergence (sync@30)", ""])
    wide = metrics_df[metrics_df.scope_mode == "repo_wide"][
        ["repo_id", "instruction_file", "sync_30", "n_governed_code_events"]
    ].rename(columns={"sync_30": "sync_30_repo_wide", "n_governed_code_events": "events_repo_wide"})
    content = metrics_df[metrics_df.scope_mode == "content_referenced"][
        ["repo_id", "instruction_file", "sync_30", "n_governed_paths_head", "n_content_refs_used", "notes"]
    ].rename(
        columns={
            "sync_30": "sync_30_content",
            "n_governed_paths_head": "governed_paths_content",
            "n_content_refs_used": "refs_used",
        }
    )
    merged = wide.merge(content, on=["repo_id", "instruction_file"], how="inner")
    merged["abs_delta_sync30"] = (merged["sync_30_repo_wide"] - merged["sync_30_content"]).abs()
    merged = merged.sort_values("abs_delta_sync30", ascending=False)
    strong = merged[merged["abs_delta_sync30"] >= 0.02].head(10)
    if strong.empty:
        lines.append("No cases with ≥2 percentage-point sync@30 gap between repo-wide and content-referenced scopes.")
    else:
        for _, row in strong.iterrows():
            lines.append(
                f"- `{row['repo_id']}` / `{row['instruction_file']}`: "
                f"repo-wide {row['sync_30_repo_wide']:.1%} vs content {row['sync_30_content']:.1%} "
                f"(Δ={row['abs_delta_sync30']:.1%}; refs_used={row['refs_used']}; "
                f"events_repo_wide={int(row['events_repo_wide'])})"
            )

    lines.extend(
        [
            "",
            "## Interpretation prompts",
            "",
            "- If repo-wide sync@30 is near zero but content-referenced sync@30 is materially higher, repo-wide scope may be too broad.",
            "- If content-referenced scope has zero resolved references, treat that mode as inconclusive rather than as high synchronization.",
            "- For root instruction files, subtree and repo-wide modes are equivalent by design in this pilot.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pilot-repos",
        type=Path,
        default=ROOT / "results/cochange/pilot/pilot_repos.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "results/cochange/pilot",
    )
    parser.add_argument("--windows", default="0,7,30")
    parser.add_argument("--clone-timeout", type=int, default=600)
    parser.add_argument("--skip-clone", action="store_true")
    args = parser.parse_args()

    windows = parse_windows(args.windows)
    pilot_df = load_pilot_repos(args.pilot_repos)
    repos_dir = ROOT / "data/repos"
    all_metrics: list[dict] = []

    for _, pilot_row in pilot_df.iterrows():
        repo_id = pilot_row["repo_id"]
        repo_dir = repo_dir_from_id(repo_id, repos_dir)
        repo_url = repo_url_from_discovered(repo_id, ROOT / "data/lifecycle/discovered_v2.csv")
        manifest_path = manifest_output_path(args.output_dir, repo_id)

        if not args.skip_clone:
            ensure_repo(repo_id, repo_dir, repo_url, timeout=args.clone_timeout)

        if not manifest_path.exists() or count_repo_commits(repo_dir) == 0:
            print(f"extracting manifest for {repo_id}...", file=sys.stderr)
            df, _ = extract_changed_files(repo_dir, repo_id)
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(manifest_path, index=False)
        else:
            print(f"using existing manifest for {repo_id}", file=sys.stderr)

        manifest = pd.read_parquet(manifest_path)
        by_commit = build_commit_index(manifest)
        head_files = set(list_head_files(repo_dir))

        instruction_files = str(pilot_row.get("pilot_instruction_files", "")).split(";")
        instruction_files = [p for p in instruction_files if p]

        repo_out_dir = args.output_dir / safe_repo_dirname(repo_id)
        repo_out_dir.mkdir(parents=True, exist_ok=True)

        for instruction_path in instruction_files:
            ref_rows = extract_content_references(repo_id, repo_dir, instruction_path, head_files)
            ref_csv = repo_out_dir / "content_references.csv"
            pd.DataFrame(ref_rows).to_csv(ref_csv, index=False)

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
                all_metrics.append(metrics)
                print(
                    f"{repo_id} {instruction_path} {mode.value}: "
                    f"sync_30={metrics.get('sync_30')} events={metrics['n_governed_code_events']}",
                    file=sys.stderr,
                )

    metrics_df = pd.DataFrame(all_metrics)
    for col in METRIC_COLUMNS:
        if col not in metrics_df.columns:
            metrics_df[col] = None
    metrics_df = metrics_df[METRIC_COLUMNS]

    metrics_csv = args.output_dir / "scope_sensitivity_metrics.csv"
    metrics_df.to_csv(metrics_csv, index=False)
    print(f"wrote {metrics_csv}")

    report = render_scope_report(metrics_df, pilot_df)
    report_path = args.output_dir / "scope_sensitivity_report.md"
    report_path.write_text(report)
    print(f"wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
