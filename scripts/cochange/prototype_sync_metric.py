#!/usr/bin/env python3
"""Compute provisional instruction–code synchronization metrics (dagster prototype)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from statistics import median

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cochange.scope import instruction_scope_label, normalize_path, path_in_governed_scope
from lifecycle.corpus_paths import configure

ROOT = configure()

DEFAULT_REPO_ID = "dagster-io/dagster"
DEFAULT_MANIFEST = ROOT / "results" / "cochange" / "prototype" / "dagster_changed_files.parquet"
DEFAULT_JSON = ROOT / "results" / "cochange" / "prototype" / "dagster_sync_metrics.json"
DEFAULT_REPORT = ROOT / "results" / "cochange" / "prototype" / "dagster_sync_report.md"
DEFAULT_INSTRUCTION_FILES = ("CLAUDE.md", "docs/CLAUDE.md")
WINDOWS_DAYS = (0, 7, 30)


def build_commit_index(df: pd.DataFrame) -> dict[str, dict]:
    """Map commit SHA -> {author_date, paths:set, statuses:dict}."""
    by_commit: dict[str, dict] = {}
    for row in df.itertuples(index=False):
        entry = by_commit.setdefault(
            row.commit,
            {"author_date": row.author_date, "paths": set(), "statuses": {}},
        )
        entry["paths"].add(row.changed_path)
        entry["statuses"][row.changed_path] = row.change_status
    return by_commit


def instruction_update_commits(
    by_commit: dict[str, dict], instruction_path: str
) -> list[tuple[str, pd.Timestamp]]:
    instruction_path = normalize_path(instruction_path)
    updates: list[tuple[str, pd.Timestamp]] = []
    for sha, meta in by_commit.items():
        if instruction_path not in meta["paths"]:
            continue
        status = meta["statuses"].get(instruction_path, "")
        if status == "D":
            updates.append((sha, meta["author_date"]))
            continue
        updates.append((sha, meta["author_date"]))
    updates.sort(key=lambda x: x[1])
    return updates


def governed_code_events(
    by_commit: dict[str, dict], instruction_path: str
) -> list[tuple[str, pd.Timestamp, list[str]]]:
    instruction_path = normalize_path(instruction_path)
    events: list[tuple[str, pd.Timestamp, list[str]]] = []

    for sha, meta in by_commit.items():
        paths = meta["paths"]
        governed = [
            p
            for p in paths
            if path_in_governed_scope(p, instruction_path)
        ]
        if not governed:
            continue
        # Exclude commits that touch ONLY the instruction file.
        non_instruction = [p for p in paths if p != instruction_path]
        if not non_instruction:
            continue
        events.append((sha, meta["author_date"], sorted(governed)))

    events.sort(key=lambda x: x[1])
    return events


def next_instruction_update_lag_days(
    event_time: pd.Timestamp,
    instruction_updates: list[tuple[str, pd.Timestamp]],
    window_days: int,
    same_commit_sha: str,
) -> float | None:
    """Return lag in days to qualifying instruction update, or None if unsynced."""
    window_end = event_time + timedelta(days=window_days)
    for sha, ts in instruction_updates:
        if ts < event_time:
            continue
        if window_days == 0 and sha != same_commit_sha:
            continue
        if ts > window_end:
            break
        if sha == same_commit_sha or ts >= event_time:
            return max(0.0, (ts - event_time).total_seconds() / 86400.0)
    return None


def compute_sync_metrics(
    repo_id: str,
    instruction_path: str,
    by_commit: dict[str, dict],
    windows: tuple[int, ...] = WINDOWS_DAYS,
) -> dict:
    instruction_path = normalize_path(instruction_path)
    updates = instruction_update_commits(by_commit, instruction_path)
    events = governed_code_events(by_commit, instruction_path)

    result: dict = {
        "repo": repo_id,
        "instruction_file": instruction_path,
        "governed_scope": instruction_scope_label(instruction_path),
        "instruction_file_found_in_history": bool(updates),
        "number_of_instruction_update_events": len(updates),
        "number_of_governed_code_events": len(events),
        "synchronization_rate": {},
        "median_lag_days_to_next_instruction_update": {},
        "assumptions": [
            "Provisional scope rules in docs/cochange_scope_rules.md",
            "git log --no-merges on default branch (HEAD)",
            "Governed-code event requires ≥1 governed path plus ≥1 non-instruction changed path",
            "W=0 requires instruction update in the same commit",
        ],
        "notes": [],
    }

    if not updates:
        result["notes"].append(
            f"No commits modifying `{instruction_path}` were found in the changed-file manifest."
        )
    if not events:
        result["notes"].append(
            f"No governed-code events attributed to `{instruction_path}` under provisional scope."
        )

    for w in windows:
        synced = 0
        lags: list[float] = []
        for sha, event_time, _ in events:
            lag = next_instruction_update_lag_days(event_time, updates, w, sha)
            if lag is not None:
                synced += 1
                lags.append(lag)
        rate = synced / len(events) if events else None
        result["synchronization_rate"][f"W={w}"] = rate
        result["median_lag_days_to_next_instruction_update"][f"W={w}"] = (
            median(lags) if lags else None
        )

    return result


def render_report(repo_id: str, metrics: list[dict], manifest_path: Path, n_commits: int, n_rows: int) -> str:
    lines = [
        "# Dagster co-change synchronization prototype",
        "",
        f"**Repository:** `{repo_id}`  ",
        f"**Changed-file manifest:** `{manifest_path}`  ",
        f"**Commits parsed:** {n_commits}  ",
        f"**Changed-file rows:** {n_rows}  ",
        "",
        "Provisional scope rules: `docs/cochange_scope_rules.md`.",
        "",
    ]
    for m in metrics:
        lines.extend(
            [
                f"## `{m['instruction_file']}`",
                "",
                f"- **Governed scope:** {m['governed_scope']}",
                f"- **Instruction file found in history:** {m['instruction_file_found_in_history']}",
                f"- **Instruction-update commits:** {m['number_of_instruction_update_events']}",
                f"- **Governed-code events:** {m['number_of_governed_code_events']}",
                "",
                "| Window | Sync rate | Median lag (days) |",
                "|--------|-----------|-------------------|",
            ]
        )
        for key in m["synchronization_rate"]:
            rate = m["synchronization_rate"][key]
            lag = m["median_lag_days_to_next_instruction_update"][key]
            rate_s = f"{rate:.1%}" if rate is not None else "n/a"
            lag_s = f"{lag:.2f}" if lag is not None else "n/a"
            lines.append(f"| {key} | {rate_s} | {lag_s} |")
        if m.get("notes"):
            lines.append("")
            lines.append("**Notes:**")
            for note in m["notes"]:
                lines.append(f"- {note}")
        lines.append("")
    lines.extend(
        [
            "## Interpretation guardrail",
            "",
            "This report describes one repository under provisional path-based scope rules.",
            "Do not generalize to cross-family claims without replication and sensitivity analyses.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--instruction-file", action="append", dest="instruction_files")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report-out", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    if not args.manifest.exists():
        raise SystemExit(f"missing manifest: {args.manifest} (run prototype_changed_files.py first)")

    df = pd.read_parquet(args.manifest)
    by_commit = build_commit_index(df)
    n_commits = df["commit"].nunique()
    n_rows = len(df)

    instruction_files = args.instruction_files or list(DEFAULT_INSTRUCTION_FILES)
    metrics = [
        compute_sync_metrics(args.repo_id, path, by_commit) for path in instruction_files
    ]

    payload = {
        "repo": args.repo_id,
        "manifest": str(args.manifest),
        "commits_parsed": int(n_commits),
        "changed_file_rows": int(n_rows),
        "windows_days": list(WINDOWS_DAYS),
        "instruction_metrics": metrics,
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(f"wrote {args.json_out}")

    report = render_report(args.repo_id, metrics, args.manifest, n_commits, n_rows)
    args.report_out.write_text(report)
    print(f"wrote {args.report_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
