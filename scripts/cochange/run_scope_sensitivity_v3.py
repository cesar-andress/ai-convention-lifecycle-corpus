#!/usr/bin/env python3
"""Scope-sensitivity pilot v3: adds package-subtree mode to v2 parser."""

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

SCOPE_MODES = (
    ScopeMode.REPO_WIDE,
    ScopeMode.SUBTREE,
    ScopeMode.CONTENT_REFERENCED,
    ScopeMode.PACKAGE_SUBTREE,
)

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
    "n_package_roots_detected",
    "package_roots_used",
    "package_subtree_status",
    "notes",
    "parser_version",
]


def parse_windows(text: str) -> tuple[int, ...]:
    return tuple(int(x.strip()) for x in text.split(",") if x.strip())


def fmt_pct(v) -> str:
    return f"{v:.1%}" if pd.notna(v) else "n/a"


def render_v3_report(metrics_df: pd.DataFrame, pilot_df: pd.DataFrame) -> str:
    lines = [
        "# Scope sensitivity pilot report (v3 — package-subtree)",
        "",
        f"**Parser version:** {PARSER_VERSION}  ",
        "Methodological pilot — do not generalize to a population.",
        "",
        "## Sync@30 by scope mode",
        "",
        "| repo | instruction | repo_wide | subtree | content_ref | package_subtree | pkg status |",
        "|------|-------------|-----------|---------|-------------|-----------------|------------|",
    ]

    pivot = metrics_df.pivot_table(
        index=["repo_id", "instruction_file"],
        columns="scope_mode",
        values="sync_30",
        aggfunc="first",
    )
    pkg = metrics_df[metrics_df.scope_mode == "package_subtree"].set_index(
        ["repo_id", "instruction_file"]
    )

    for (repo_id, instr), row in pivot.iterrows():
        status = ""
        if (repo_id, instr) in pkg.index:
            status = str(pkg.loc[(repo_id, instr), "package_subtree_status"])
        lines.append(
            f"| `{repo_id}` | `{instr}` | {fmt_pct(row.get('repo_wide'))} | "
            f"{fmt_pct(row.get('subtree'))} | {fmt_pct(row.get('content_referenced'))} | "
            f"{fmt_pct(row.get('package_subtree'))} | {status} |"
        )

    lines.extend(["", "## Package-subtree vs repo-wide (sync@30 delta)", ""])
    wide = metrics_df[metrics_df.scope_mode == "repo_wide"][["repo_id", "instruction_file", "sync_30"]]
    wide = wide.rename(columns={"sync_30": "repo_wide_sync_30"})
    pkg_metrics = metrics_df[metrics_df.scope_mode == "package_subtree"][
        [
            "repo_id",
            "instruction_file",
            "sync_30",
            "package_subtree_status",
            "package_roots_used",
            "n_package_roots_detected",
        ]
    ].rename(columns={"sync_30": "package_subtree_sync_30"})
    merged = wide.merge(pkg_metrics, on=["repo_id", "instruction_file"], how="inner")
    merged["delta_pkg_minus_wide"] = merged["package_subtree_sync_30"] - merged["repo_wide_sync_30"]

    strong = merged[
        merged["package_subtree_status"] == "usable"
    ].copy()
    strong["abs_delta"] = merged["delta_pkg_minus_wide"].abs()
    strong = strong.sort_values("abs_delta", ascending=False)

    if strong.empty:
        lines.append("No usable package-subtree scopes in this pilot.")
    else:
        for _, r in strong.head(10).iterrows():
            lines.append(
                f"- `{r['repo_id']}` / `{r['instruction_file']}`: "
                f"repo-wide {fmt_pct(r['repo_wide_sync_30'])} → package-subtree {fmt_pct(r['package_subtree_sync_30'])} "
                f"(Δ={fmt_pct(r['delta_pkg_minus_wide'])}; roots={r['package_roots_used'] or '—'})"
            )

    lines.extend(["", "## Package-subtree vs content-referenced agreement", ""])
    content = metrics_df[metrics_df.scope_mode == "content_referenced"][["repo_id", "instruction_file", "sync_30"]]
    content = content.rename(columns={"sync_30": "content_sync_30"})
    cmp2 = content.merge(pkg_metrics, on=["repo_id", "instruction_file"], how="inner")
    cmp2 = cmp2[cmp2.package_subtree_status == "usable"]
    cmp2["abs_delta"] = (cmp2["content_sync_30"] - cmp2["package_subtree_sync_30"]).abs()
    agree = cmp2[cmp2["abs_delta"] <= 0.05].sort_values(["repo_id", "instruction_file"])
    disagree = cmp2[cmp2["abs_delta"] > 0.05].sort_values("abs_delta", ascending=False)

    lines.append("**Within 5 pp (usable package-subtree):**")
    if agree.empty:
        lines.append("- none")
    else:
        for _, r in agree.iterrows():
            lines.append(
                f"- `{r['repo_id']}` / `{r['instruction_file']}`: "
                f"content {fmt_pct(r['content_sync_30'])} vs package {fmt_pct(r['package_subtree_sync_30'])}"
            )

    lines.append("")
    lines.append("**Differ by >5 pp (usable package-subtree):**")
    if disagree.empty:
        lines.append("- none")
    else:
        for _, r in disagree.head(8).iterrows():
            lines.append(
                f"- `{r['repo_id']}` / `{r['instruction_file']}`: "
                f"content {fmt_pct(r['content_sync_30'])} vs package {fmt_pct(r['package_subtree_sync_30'])}"
            )

    lines.extend(["", "## Inconclusive package-subtree cases", ""])
    incon = merged[~merged.package_subtree_status.isin(["usable", "fallback_subtree_nested"])]
    if incon.empty:
        lines.append("None.")
    else:
        for _, r in incon.iterrows():
            lines.append(
                f"- `{r['repo_id']}` / `{r['instruction_file']}`: **{r['package_subtree_status']}** "
                f"(detected roots={int(r['n_package_roots_detected'])})"
            )

    fallback = merged[merged.package_subtree_status == "fallback_subtree_nested"]
    if not fallback.empty:
        lines.extend(["", "## Nested fallback to subtree", ""])
        for _, r in fallback.iterrows():
            lines.append(
                f"- `{r['repo_id']}` / `{r['instruction_file']}`: sync@30={fmt_pct(r['package_subtree_sync_30'])} "
                f"(roots `{r['package_roots_used']}`)"
            )

    lines.extend(["", "## Interpretation guardrail", "", "Optimize validity over recall.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-repos", type=Path, default=ROOT / "results/cochange/pilot/pilot_repos.csv")
    parser.add_argument("--manifest-dir", type=Path, default=ROOT / "results/cochange/pilot")
    parser.add_argument("--out-csv", type=Path, default=ROOT / "results/cochange/pilot/scope_sensitivity_v3.csv")
    parser.add_argument("--out-report", type=Path, default=ROOT / "results/cochange/pilot/scope_sensitivity_v3_report.md")
    parser.add_argument("--windows", default="0,7,30")
    args = parser.parse_args()

    windows = parse_windows(args.windows)
    pilot_df = pd.read_csv(args.pilot_repos)
    repos_dir = ROOT / "data/repos"
    all_metrics: list[dict] = []

    for _, pilot_row in pilot_df.iterrows():
        repo_id = pilot_row["repo_id"]
        repo_dir = repo_dir_from_id(repo_id, repos_dir)
        manifest_path = manifest_output_path(args.manifest_dir, repo_id)
        if not manifest_path.exists():
            print(f"skip {repo_id}: missing {manifest_path}", file=sys.stderr)
            continue

        manifest = pd.read_parquet(manifest_path)
        by_commit = build_commit_index(manifest)
        head_files = set(list_head_files(repo_dir))
        instruction_files = [p for p in str(pilot_row.get("pilot_instruction_files", "")).split(";") if p]

        for instruction_path in instruction_files:
            ref_rows = extract_content_references(repo_id, repo_dir, instruction_path, head_files)
            for mode in SCOPE_MODES:
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
                if mode == ScopeMode.PACKAGE_SUBTREE:
                    print(
                        f"{repo_id} {instruction_path} package_subtree: "
                        f"status={metrics['package_subtree_status']} sync_30={metrics.get('sync_30')}",
                        file=sys.stderr,
                    )

    metrics_df = pd.DataFrame(all_metrics)
    for col in METRIC_COLUMNS:
        if col not in metrics_df.columns:
            metrics_df[col] = None
    metrics_df = metrics_df[METRIC_COLUMNS]
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(args.out_csv, index=False)
    print(f"wrote {args.out_csv}")

    report = render_v3_report(metrics_df, pilot_df)
    args.out_report.write_text(report)
    print(f"wrote {args.out_report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
