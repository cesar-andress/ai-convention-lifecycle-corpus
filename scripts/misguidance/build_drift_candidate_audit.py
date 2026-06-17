#!/usr/bin/env python3
"""Build manual-audit package for drift candidates (historical_existence=existed_before)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cochange.content_refs import read_instruction_at_head
from cochange.repo_utils import repo_dir_from_id
from cochange.scope import normalize_path
from lifecycle.corpus_paths import configure
from lifecycle.git_utils import run_git

ROOT = configure()

HEADING_RE = re.compile(r"^(#{1,4})\s+(.+)$")
DOC_EXTENSIONS = (".md", ".rst", ".txt", ".adoc", ".html")
SOURCE_EXTENSIONS = (".py", ".go", ".rs", ".ts", ".tsx", ".js", ".jsx", ".java", ".kt", ".cs")
CONFIG_NAMES = {
    "setup.py",
    "pyproject.toml",
    "go.mod",
    "package.json",
    "dockerfile",
    "dev_config.yaml",
    "custom.ini",
}
GLOB_CHARS = frozenset("*?{")


def _norm(value: object) -> str:
    return "" if value is None else str(value).strip()


def history_path_candidates(raw: str, resolved: str) -> list[str]:
    raw_clean = normalize_path(raw.strip("[]()`").split("#")[0])
    resolved = normalize_path(resolved)
    paths: list[str] = []
    for candidate in (raw_clean, resolved):
        if not candidate:
            continue
        paths.append(candidate)
        if not candidate.endswith("/"):
            paths.append(candidate + "/")
    deduped: list[str] = []
    for path in paths:
        if path not in deduped:
            deduped.append(path)
    return deduped


def _has_glob_pattern(path: str) -> bool:
    return any(ch in path for ch in GLOB_CHARS)


def _commit_fields(repo_dir: Path, commit: str) -> dict[str, str]:
    if not commit:
        return {}
    proc = run_git(
        ["git", "show", "-s", "--format=%H|%at|%cI", commit],
        cwd=repo_dir,
        timeout=60,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return {"commit": commit}
    parts = proc.stdout.strip().split("|", 2)
    out = {"commit": parts[0]}
    if len(parts) > 1:
        out["timestamp"] = parts[1]
        try:
            out["iso_date"] = datetime.fromtimestamp(int(parts[1]), tz=timezone.utc).date().isoformat()
        except ValueError:
            out["iso_date"] = parts[2][:10] if len(parts) > 2 else ""
    elif len(parts) > 2:
        out["iso_date"] = parts[2][:10]
    return out


def _first_commit_for_path(repo_dir: Path, path: str) -> str:
    proc = run_git(
        ["git", "log", "--all", "--diff-filter=A", "--format=%H", "-1", "--", path],
        cwd=repo_dir,
        timeout=120,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip().splitlines()[0]
    proc = run_git(
        ["git", "log", "--all", "--format=%H", "-1", "--", path],
        cwd=repo_dir,
        timeout=120,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip().splitlines()[-1]
    return ""


def _delete_commit_for_path(repo_dir: Path, path: str) -> str:
    proc = run_git(
        ["git", "log", "--all", "--diff-filter=D", "--format=%H", "-1", "--", path],
        cwd=repo_dir,
        timeout=120,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip().splitlines()[0]
    return ""


def _last_seen_commit(repo_dir: Path, path: str) -> str:
    proc = run_git(
        ["git", "log", "--all", "--format=%H", "-1", "--", path],
        cwd=repo_dir,
        timeout=120,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip().splitlines()[0]
    return ""


def _rename_info(repo_dir: Path, path: str) -> dict[str, str]:
    proc = run_git(
        ["git", "log", "--all", "--follow", "--name-status", "--format=%H", "-1", "--", path],
        cwd=repo_dir,
        timeout=120,
    )
    if proc.returncode != 0:
        return {}
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    for line in lines:
        if line.startswith("R") or line.startswith("R"):
            parts = line.split("\t")
            if len(parts) >= 3:
                return {
                    "rename_commit": parts[0].split()[-1] if " " in parts[0] else "",
                    "rename_from": parts[1],
                    "rename_to": parts[2],
                }
        if re.match(r"^R\d+\t", line):
            parts = line.split("\t")
            return {"rename_from": parts[1], "rename_to": parts[2]}
    # name-status lines after commit hash line
    if len(lines) >= 2:
        status_line = lines[1]
        if status_line.startswith("R"):
            parts = status_line.split("\t")
            if len(parts) >= 3:
                return {"rename_from": parts[1], "rename_to": parts[2], "rename_commit": lines[0]}
    return {}


def collect_path_history(repo_dir: Path, raw: str, resolved: str) -> dict[str, object]:
    candidates = history_path_candidates(raw, resolved)
    best_intro = ""
    best_delete = ""
    best_last = ""
    rename_info: dict[str, str] = {}
    matched_path = ""

    for path in candidates:
        intro = _first_commit_for_path(repo_dir, path)
        delete = _delete_commit_for_path(repo_dir, path)
        last = _last_seen_commit(repo_dir, path)
        if intro or delete or last:
            matched_path = path
            best_intro = intro or best_intro
            best_delete = delete or best_delete
            best_last = last or best_last
            if not rename_info:
                rename_info = _rename_info(repo_dir, path)
            if intro and delete:
                break

    intro_fields = _commit_fields(repo_dir, best_intro)
    delete_fields = _commit_fields(repo_dir, best_delete)
    last_fields = _commit_fields(repo_dir, best_last or best_delete or best_intro)

    lifetime_days = ""
    if intro_fields.get("timestamp") and delete_fields.get("timestamp"):
        try:
            lifetime_days = int(delete_fields["timestamp"]) - int(intro_fields["timestamp"])
            lifetime_days = max(0, lifetime_days // 86400)
        except ValueError:
            lifetime_days = ""

    quality = "reliable"
    if _has_glob_pattern(raw) or _has_glob_pattern(resolved):
        quality = "uncertain"
    if not matched_path or (not best_intro and not best_last):
        quality = "failed"

    return {
        "history_path_used": matched_path,
        "first_seen_commit": intro_fields.get("commit", best_intro),
        "first_seen_date": intro_fields.get("iso_date", ""),
        "last_seen_commit": last_fields.get("commit", best_last),
        "last_seen_date": last_fields.get("iso_date", ""),
        "deleted_commit": delete_fields.get("commit", best_delete),
        "deleted_date": delete_fields.get("iso_date", ""),
        "path_lifetime_days": lifetime_days,
        "rename_from": rename_info.get("rename_from", ""),
        "rename_to": rename_info.get("rename_to", ""),
        "rename_commit": rename_info.get("rename_commit", ""),
        "history_quality": quality,
    }


def _heading_at_line(lines: list[str], line_idx: int) -> str:
    for i in range(line_idx, -1, -1):
        match = HEADING_RE.match(lines[i].strip())
        if match:
            return match.group(2).strip()
    return ""


def extract_instruction_context(
    repo_dir: Path,
    instruction_file: str,
    extracted_reference: str,
    *,
    window: int = 5,
) -> dict[str, str]:
    text = read_instruction_at_head(repo_dir, instruction_file)
    if not text:
        return {
            "section_heading": "",
            "context_excerpt": "",
            "context_line_number": "",
        }

    lines = text.splitlines()
    needles = [
        extracted_reference,
        extracted_reference.strip("[]()`"),
        normalize_path(extracted_reference.strip("[]()`").split("#")[0]),
    ]
    needles = [n for n in dict.fromkeys(needles) if n]

    for idx, line in enumerate(lines):
        if any(needle and needle in line for needle in needles):
            start = max(0, idx - window)
            end = min(len(lines), idx + window + 1)
            excerpt_lines = [f"{i + 1:4d}| {lines[i]}" for i in range(start, end)]
            return {
                "section_heading": _heading_at_line(lines, idx),
                "context_excerpt": "\n".join(excerpt_lines),
                "context_line_number": str(idx + 1),
            }

    return {
        "section_heading": "",
        "context_excerpt": "(reference string not found verbatim in instruction file at HEAD)",
        "context_line_number": "",
    }


def auto_drift_category(row: dict, history: dict) -> str:
    status = _norm(row.get("status"))
    resolved = _norm(row.get("resolved_path"))
    raw = _norm(row.get("extracted_reference"))
    mis_cat = _norm(row.get("misguidance_category"))

    if history.get("rename_from") and history.get("rename_to"):
        if _norm(history["rename_from"]).rsplit("/", 1)[0] != _norm(history["rename_to"]).rsplit("/", 1)[0]:
            return "moved_path"
        return "renamed_path"

    if status == "doc_reference" or mis_cat == "stale_doc_reference":
        return "documentation_reference"
    if any(resolved.endswith(ext) for ext in DOC_EXTENSIONS) or "docs/" in resolved:
        return "documentation_reference"

    base = resolved.rstrip("/").rsplit("/", 1)[-1].lower()
    if base in CONFIG_NAMES or base.endswith((".yaml", ".yml", ".toml", ".ini", ".cfg", ".lock")):
        return "config_reference"

    if resolved.endswith("/") or mis_cat == "stale_directory" or raw.endswith("/"):
        return "deleted_directory"

    if any(resolved.endswith(ext) for ext in SOURCE_EXTENSIONS):
        return "source_code_reference"

    if "." in base and not _has_glob_pattern(resolved):
        return "deleted_file"

    if _has_glob_pattern(raw) or _has_glob_pattern(resolved):
        return "unknown"

    return "unknown"


def heuristic_assessment(row: dict, history: dict, category: str) -> tuple[str, str]:
    """Return (likely_drift_hint, likely_artifact_hint) — not manual labels."""
    reasons_drift: list[str] = []
    reasons_artifact: list[str] = []

    if history.get("history_quality") == "reliable" and history.get("deleted_commit"):
        reasons_drift.append("path had a deletion commit in git history")
    if history.get("history_quality") == "uncertain":
        reasons_artifact.append("glob or pattern-like reference")
    if _has_glob_pattern(_norm(row.get("extracted_reference"))):
        reasons_artifact.append("glob/example token in instruction text")
    if _norm(row.get("resolution_status")) == "partial_resolution":
        reasons_artifact.append("partial path resolution")
    if category in {"documentation_reference"} and "#" in _norm(row.get("extracted_reference")):
        reasons_artifact.append("anchor/link fragment rather than repo path")
    if category == "deleted_directory" and _norm(row.get("extracted_reference")) in {"src", "dev", "tests"}:
        reasons_artifact.append("generic top-level directory mention")
    if history.get("rename_to"):
        reasons_drift.append("git rename detected")

    drift = "yes" if reasons_drift and len(reasons_drift) >= len(reasons_artifact) else ("maybe" if reasons_drift else "no")
    artifact = "yes" if reasons_artifact and len(reasons_artifact) > len(reasons_drift) else ("maybe" if reasons_artifact else "no")
    return drift, artifact


def render_instruction_context_md(rows: list[dict]) -> str:
    lines = [
        "# Drift candidate instruction context",
        "",
        "±5 lines around each extracted reference in the instruction file at HEAD.",
        "",
        "**Manual review file:** `drift_candidate_review.csv`",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"## Candidate `{row['candidate_id']}` — `{row['repo_id']}` / `{row['instruction_file']}`",
                "",
                f"- Reference: `{row['extracted_reference']}`",
                f"- Resolved path: `{row['resolved_path']}`",
                f"- Section heading: {row.get('section_heading') or '_(none)_'}",
                f"- Line: {row.get('context_line_number') or 'n/a'}",
                f"- Auto category: `{row.get('auto_drift_category', '')}`",
                "",
                "```markdown",
                row.get("context_excerpt") or "(no context)",
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def render_report(rows: list[dict], out_path: Path) -> None:
    by_repo = Counter(r["repo_id"] for r in rows)
    by_category = Counter(r["auto_drift_category"] for r in rows)
    drift_hints = Counter(r["heuristic_likely_drift"] for r in rows)
    artifact_hints = Counter(r["heuristic_likely_artifact"] for r in rows)
    reliable = sum(1 for r in rows if r.get("history_quality") == "reliable")

    lines = [
        "# Drift candidate audit report (qualitative)",
        "",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "**Pilot subset only — no population claims.**",
        "",
        f"Candidates (historical_existence=`existed_before`): **{len(rows)}**",
        "",
        "## 1. Which repositories contribute most candidates?",
        "",
    ]
    for repo, count in by_repo.most_common():
        lines.append(f"- `{repo}`: **{count}**")

    lines.extend(["", "## 2. Which categories dominate?", ""])
    for cat, count in by_category.most_common():
        lines.append(f"- `{cat}`: {count}")

    lines.extend(
        [
            "",
            "## 3. How many appear likely to be real drift? (heuristic pre-assessment only)",
            "",
            "Manual columns in `drift_candidate_review.csv` are empty — these are **not** validated labels.",
            "",
        ]
    )
    for label, count in drift_hints.most_common():
        lines.append(f"- heuristic `{label}`: {count}")

    lines.extend(
        [
            "",
            "## 4. How many appear to be parser artifacts? (heuristic pre-assessment only)",
            "",
        ]
    )
    for label, count in artifact_hints.most_common():
        lines.append(f"- heuristic `{label}`: {count}")

    lines.extend(
        [
            "",
            "## 5. Strong enough for a full-corpus study?",
            "",
            f"- Reliable git history rows: **{reliable}/{len(rows)}**",
            f"- Heuristic `yes` drift: **{drift_hints.get('yes', 0)}**",
            f"- Heuristic `yes` artifact: **{artifact_hints.get('yes', 0)}**",
            "",
            "Qualitative conclusion: complete manual review of `drift_candidate_review.csv` before deciding "
            "on full-corpus collection. If manual review confirms even a modest subset of the "
            f"**{len(rows)}** candidates as plausible drift, the phenomenon warrants a bounded scale-up; "
            "otherwise refine extraction/history rules first.",
            "",
            "## Historical context summary",
            "",
            f"- Median path lifetime (days, where computed): "
            + _median_lifetime(rows),
            "",
            "## Next steps",
            "",
            "1. Fill `drift_candidate_review.csv` (`appears_to_be_real_drift`, `appears_to_be_false_positive`, `reference_still_meaningful`, `notes`).",
            "2. Re-run summarizer after review (future target).",
            "3. Only then decide on full-corpus misguidance collection.",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _median_lifetime(rows: list[dict]) -> str:
    values = [int(r["path_lifetime_days"]) for r in rows if str(r.get("path_lifetime_days", "")).isdigit()]
    if not values:
        return "n/a"
    values.sort()
    mid = values[len(values) // 2]
    return str(mid)


def build_audit(stale_csv: Path, out_dir: Path) -> None:
    df = pd.read_csv(stale_csv, dtype=str, keep_default_na=False)
    candidates = df[df["historical_existence"] == "existed_before"].copy()
    if candidates.empty:
        raise SystemExit(f"No existed_before rows in {stale_csv}")

    out_dir.mkdir(parents=True, exist_ok=True)
    audit_rows: list[dict] = []

    for idx, row in candidates.iterrows():
        repo_id = _norm(row["repo_id"])
        instruction_file = _norm(row["instruction_file"])
        repo_dir = repo_dir_from_id(repo_id, ROOT / "data/repos")
        candidate_id = f"DC{len(audit_rows) + 1:03d}"

        history = collect_path_history(
            repo_dir,
            _norm(row.get("extracted_reference") or row.get("reference")),
            _norm(row["resolved_path"]),
        )
        context = extract_instruction_context(
            repo_dir,
            instruction_file,
            _norm(row.get("extracted_reference") or row.get("reference")),
        )
        category = auto_drift_category(row.to_dict(), history)
        drift_hint, artifact_hint = heuristic_assessment(row.to_dict(), history, category)

        record = {
            "candidate_id": candidate_id,
            "repo_id": repo_id,
            "instruction_file": instruction_file,
            "extracted_reference": _norm(row.get("extracted_reference") or row.get("reference")),
            "resolved_path": _norm(row["resolved_path"]),
            "extraction_rule": _norm(row["extraction_rule"]),
            "confidence": _norm(row["confidence"]),
            "current_status": _norm(row["status"]),
            "historical_existence": _norm(row["historical_existence"]),
            "misguidance_category": _norm(row.get("misguidance_category")),
            "resolution_status": _norm(row.get("resolution_status")),
            "first_seen_commit": history.get("first_seen_commit", ""),
            "first_seen_date": history.get("first_seen_date", ""),
            "last_seen_commit": history.get("last_seen_commit", ""),
            "last_seen_date": history.get("last_seen_date", ""),
            "deleted_commit": history.get("deleted_commit", ""),
            "deleted_date": history.get("deleted_date", ""),
            "path_lifetime_days": history.get("path_lifetime_days", ""),
            "history_path_used": history.get("history_path_used", ""),
            "history_quality": history.get("history_quality", ""),
            "rename_from": history.get("rename_from", ""),
            "rename_to": history.get("rename_to", ""),
            "auto_drift_category": category,
            "heuristic_likely_drift": drift_hint,
            "heuristic_likely_artifact": artifact_hint,
            "section_heading": context.get("section_heading", ""),
            "context_line_number": context.get("context_line_number", ""),
            "context_excerpt": context.get("context_excerpt", ""),
        }
        audit_rows.append(record)
        print(f"{candidate_id} {repo_id} {record['extracted_reference'][:50]} -> {category} history={history.get('history_quality')}")

    drift_df = pd.DataFrame(audit_rows)
    drift_path = out_dir / "drift_candidates.csv"
    drift_df.to_csv(drift_path, index=False)

    review_cols = list(drift_df.columns) + [
        "appears_to_be_real_drift",
        "appears_to_be_false_positive",
        "reference_still_meaningful",
        "notes",
    ]
    review_df = drift_df.copy()
    for col in ("appears_to_be_real_drift", "appears_to_be_false_positive", "reference_still_meaningful", "notes"):
        review_df[col] = ""
    review_df = review_df[review_cols]
    review_path = out_dir / "drift_candidate_review.csv"
    review_df.to_csv(review_path, index=False)

    context_md = out_dir / "instruction_context.md"
    context_md.write_text(render_instruction_context_md(audit_rows), encoding="utf-8")

    report_path = out_dir / "drift_candidate_report.md"
    render_report(audit_rows, report_path)

    meta = {
        "source_stale_references": str(stale_csv),
        "n_candidates": len(audit_rows),
        "by_repo": dict(Counter(r["repo_id"] for r in audit_rows)),
        "by_category": dict(Counter(r["auto_drift_category"] for r in audit_rows)),
    }
    (out_dir / "drift_candidate_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {drift_path} ({len(drift_df)} rows)")
    print(f"wrote {review_path}")
    print(f"wrote {context_md}")
    print(f"wrote {report_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stale-csv",
        type=Path,
        default=ROOT / "results/misguidance/pilot_v2/stale_references.csv",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "results/misguidance/drift_candidates",
    )
    args = parser.parse_args()
    build_audit(args.stale_csv, args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
