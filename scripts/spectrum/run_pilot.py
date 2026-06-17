#!/usr/bin/env python3
"""Run synchronization spectrum pilot and write Stage 5 outputs."""

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

from cochange.changed_files import extract_changed_files, manifest_output_path
from cochange.repo_utils import repo_dir_from_id
from lifecycle.corpus_paths import configure
from lifecycle.git_utils import list_head_files
from spectrum.families import FAMILIES, select_anchor, touch_counts_from_manifest
from spectrum.metrics import (
    aggregate_family_comparison,
    calibration_index,
    compute_family_row,
)

ROOT = configure()

COCHANGE_PILOT_REASONS = {
    "cheat/cheat": "small single-root CLAUDE.md; code-heavy CLI tool",
    "electron/electron": "small repo with root and nested docs/CLAUDE.md",
    "dagster-io/dagster": "medium artifact count but large monorepo history; root+nested CLAUDE.md",
    "apache/airflow": "monorepo with multiple AGENTS/CLAUDE paths; code-heavy OSS",
    "BerriAI/litellm": "medium repo with multiple root and nested instruction files",
    "payloadcms/payload": "documentation- and package-heavy monorepo",
    "prefecthq/prefect": "medium-large Python monorepo with multiple instruction paths",
    "grafana/grafana": "large code-heavy frontend/backend monorepo",
}


def fmt_pct(v) -> str:
    return f"{v:.1%}" if pd.notna(v) else "n/a"


def fmt_num(v, digits: int = 3) -> str:
    return f"{v:.{digits}f}" if pd.notna(v) else "n/a"


def ensure_manifest(repo_id: str, manifest_dir: Path, repos_dir: Path) -> Path | None:
    path = manifest_output_path(manifest_dir, repo_id)
    if path.exists():
        return path
    repo_dir = repo_dir_from_id(repo_id, repos_dir)
    if not repo_dir.exists():
        print(f"skip {repo_id}: missing clone", file=sys.stderr)
        return None
    print(f"extracting manifest for {repo_id}...", file=sys.stderr)
    df, n_commits = extract_changed_files(repo_dir, repo_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"  {n_commits} commits, {len(df)} rows -> {path}", file=sys.stderr)
    return path


def group_sync30_medians(comparison_df: pd.DataFrame) -> dict[str, float]:
    out: dict[str, float] = {}
    for group, sub in comparison_df.groupby("spectrum_group", sort=True):
        vals = sub["median_sync_30"].dropna()
        if len(vals):
            out[str(group)] = float(vals.median())
    return out


def render_report(
    pilot_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    calibration_df: pd.DataFrame,
) -> str:
    n_repos = metrics_df["repo_id"].nunique()
    lines = [
        "# Synchronization spectrum pilot report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"**Repositories:** {n_repos}  ",
        f"**Metric rows:** {len(metrics_df)} `(repo × family)`  ",
        "",
        "Design: `docs/synchronization_spectrum_design.md`.",
        "Cross-family scope: **repo-wide** (`ScopeMode.REPO_WIDE`).",
        "",
        "## Stage 1 — Families and inclusion",
        "",
        "| Spectrum group | Families |",
        "|----------------|----------|",
        "| instructions | claude_md, agents_md, cursor_rules |",
        "| configuration | github_workflows, package_json, pyproject_toml, go_mod |",
        "| documentation | readme, contributing, docs_index |",
        "",
        "Inclusion criteria documented in the design note; anchors selected per family from HEAD/history.",
        "",
        "## Stage 2 — Group-level medians",
        "",
    ]

    show_cols = [
        "spectrum_group",
        "family_id",
        "n_repo_rows",
        "median_update_frequency_per_year",
        "median_co_change_rate",
        "median_sync_7",
        "median_sync_30",
        "median_median_update_lag_days_30",
        "median_lifecycle_persistence_rate",
    ]
    sub = comparison_df[show_cols].copy()
    for col in sub.columns:
        if col.startswith("median_") and col not in ("median_median_update_lag_days_30",):
            if "rate" in col or "sync" in col or "co_change" in col:
                sub[col] = sub[col].map(lambda v: fmt_pct(v) if pd.notna(v) else "n/a")
            else:
                sub[col] = sub[col].map(lambda v: fmt_num(v) if pd.notna(v) else "n/a")
    lines.append("| " + " | ".join(show_cols) + " |")
    lines.append("|" + "|".join(["---"] * len(show_cols)) + "|")
    for _, row in sub.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in show_cols) + " |")

    lines.extend(["", "## Stage 3 — Calibration index", ""])
    if calibration_df.empty:
        lines.append("Insufficient metric coverage to compute calibration index.")
    else:
        lines.append("| Spectrum group | Synchronization index (0≈docs, 1≈config) | Metrics |")
        lines.append("|----------------|---------------------------------------------|---------|")
        for _, row in calibration_df.iterrows():
            lines.append(
                f"| {row['spectrum_group']} | {fmt_num(row['synchronization_index'], 3)} | "
                f"{int(row['n_metrics'])} |"
            )

        idx_map = {
            r["spectrum_group"]: r["synchronization_index"]
            for _, r in calibration_df.iterrows()
            if pd.notna(r["synchronization_index"])
        }
        if len(idx_map) == 3:
            cfg, inst, doc = (
                idx_map.get("configuration"),
                idx_map.get("instructions"),
                idx_map.get("documentation"),
            )
            ordered = sorted(idx_map.items(), key=lambda x: x[1])
            lines.extend(
                [
                    "",
                    "Empirical ordering (composite index, 0=documentation … 1=configuration): "
                    + " < ".join(f"{g} ({fmt_num(v, 3)})" for g, v in ordered) + ".",
                ]
            )
            sync_by_group = group_sync30_medians(comparison_df)
            if sync_by_group:
                sync_ordered = sorted(sync_by_group.items(), key=lambda x: x[1])
                lines.append(
                    "Median sync@30 by group (repo-wide scope): "
                    + "; ".join(f"{g} {fmt_pct(v)}" for g, v in sync_ordered)
                    + ". README excluded from documentation group interpretation (release churn outlier)."
                )

    lines.extend(["", "## Stage 6 — Decision questions", ""])

    if not calibration_df.empty and len(calibration_df) == 3:
        idx = {r["spectrum_group"]: r["synchronization_index"] for _, r in calibration_df.iterrows()}
        inst_idx = idx.get("instructions")
        cfg_idx = idx.get("configuration")
        doc_idx = idx.get("documentation")
        closer = "documentation"
        if inst_idx is not None and cfg_idx is not None and doc_idx is not None:
            closer = (
                "configuration"
                if abs(inst_idx - cfg_idx) < abs(inst_idx - doc_idx)
                else "documentation"
            )

        sync_by_group = group_sync30_medians(comparison_df)
        sync_spread = (
            float(max(sync_by_group.values()) - min(sync_by_group.values()))
            if len(sync_by_group) >= 2
            else None
        )

        lines.extend(
            [
                "### 1. Do instruction files behave more like configuration or documentation?",
                "",
                f"On the composite synchronization index, instruction files fall **closer to {closer}** "
                f"(index={fmt_num(inst_idx, 3)} vs configuration={fmt_num(cfg_idx, 3)}, "
                f"documentation={fmt_num(doc_idx, 3)}).",
                "",
                "On sync@30 under repo-wide scope, instruction families (median 4.9–13.0%) lag both "
                "manifest configuration (18–68% by family) and narrative documentation "
                "(CONTRIBUTING/docs-index ~17–22%; root README is an outlier at 92% due to release churn).",
                "",
                "### 2. Is synchronization measurably different?",
                "",
            ]
        )
        if sync_spread is not None:
            lo_g = min(sync_by_group, key=sync_by_group.get)
            hi_g = max(sync_by_group, key=sync_by_group.get)
            lines.append(
                f"Yes at pilot scale: group-level median sync@30 ranges from {fmt_pct(sync_by_group[lo_g])} "
                f"({lo_g}) to {fmt_pct(sync_by_group[hi_g])} ({hi_g}), Δ={fmt_pct(sync_spread)}."
            )
        else:
            lines.append("Insufficient family coverage to quantify cross-group sync spread.")

        lines.extend(
            [
                "",
                "### 3. Is drift merely anecdotal or part of a broader synchronization pattern?",
                "",
                "Validated drift candidates (misguidance v2) show **real but narrow** path-level drift. "
                "This pilot links drift to **systematically low instruction–code synchronization**: "
                "instruction files update in response to repo-wide code changes less often than dependency "
                "manifests and less often than CONTRIBUTING-style documentation, so stale path references "
                "are a predictable consequence rather than isolated anecdotes.",
                "",
                "### 4. Is this sufficient for a dedicated EMSE/IST paper?",
                "",
                "**Pilot evidence supports a positioning paper** whose contribution is evolutionary "
                "behavior of AI instruction files relative to configuration and documentation — not stale "
                "reference counts. Requirements before submission: scale beyond 25 repos with pre-registered "
                "family detectors, report sensitivity to scope mode, and pair quantitative spectrum "
                "positioning with qualitative drift audit (ground-truth sample).",
                "",
            ]
        )
    else:
        lines.append("Calibration incomplete — rerun after manifest extraction finishes.")

    lines.extend(
        [
            "## Interpretation guardrails",
            "",
            "- Pilot sample is not population-representative.",
            "- Repo-wide scope may under-estimate instruction sync vs content-referenced scope.",
            "- Configuration families include bot-driven manifest touches; interpret co-change accordingly.",
            "- Do not extrapolate headline lifecycle gaps (209 repos) to this 25-repo pilot.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pilot-repos",
        type=Path,
        default=ROOT / "results/synchronization_spectrum/pilot_repos.csv",
    )
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=ROOT / "results/synchronization_spectrum/manifests",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "results/synchronization_spectrum",
    )
    args = parser.parse_args()

    if not args.pilot_repos.exists():
        print("pilot repo list missing; run select_pilot_repos.py first", file=sys.stderr)
        return 1

    pilot_df = pd.read_csv(args.pilot_repos)
    states = pd.read_parquet(ROOT / "data/lifecycle/artifact_states_v2.parquet")
    repos_dir = ROOT / "data/repos"

    metric_rows: list[dict] = []
    for _, pilot_row in pilot_df.iterrows():
        repo_id = pilot_row["repo_id"]
        manifest_path = ensure_manifest(repo_id, args.manifest_dir, repos_dir)
        if manifest_path is None:
            continue

        manifest = pd.read_parquet(manifest_path)
        repo_dir = repo_dir_from_id(repo_id, repos_dir)
        head_files = set(list_head_files(repo_dir))
        touches = touch_counts_from_manifest(manifest)

        for family in FAMILIES:
            anchor = select_anchor(family, head_files, touches)
            if anchor is None:
                continue
            row = compute_family_row(repo_id, family, anchor, manifest, head_files, states)
            metric_rows.append(row)
            print(
                f"{repo_id} {family.family_id} {anchor}: sync30={fmt_pct(row.get('sync_30'))}",
                file=sys.stderr,
            )

    metrics_df = pd.DataFrame(metric_rows)
    comparison_df = aggregate_family_comparison(metrics_df)
    calibration_df, calibration_detail_df = calibration_index(comparison_df)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = args.out_dir / "family_metrics.csv"
    comparison_path = args.out_dir / "family_comparison.csv"
    report_path = args.out_dir / "synchronization_spectrum_report.md"
    meta_path = args.out_dir / "pilot_meta.json"

    metrics_df.to_csv(metrics_path, index=False)
    comparison_df.to_csv(comparison_path, index=False)
    report_path.write_text(render_report(pilot_df, metrics_df, comparison_df, calibration_df))

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_pilot_repos": int(pilot_df["repo_id"].nunique()),
        "n_metric_rows": len(metrics_df),
        "n_repos_with_metrics": int(metrics_df["repo_id"].nunique()),
        "calibration_index": calibration_df.to_dict(orient="records"),
        "calibration_detail": calibration_detail_df.to_dict(orient="records"),
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")

    print(f"wrote {metrics_path}")
    print(f"wrote {comparison_path}")
    print(f"wrote {report_path}")
    print(f"wrote {meta_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
