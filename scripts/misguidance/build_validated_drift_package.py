#!/usr/bin/env python3
"""Build ground-truth validation package for historical drift candidates."""

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

from lifecycle.corpus_paths import configure

ROOT = configure()

GLOB_CHARS = frozenset("*?{")
GENERIC_PATH_TOKENS = frozenset(
    {
        "src",
        "dev",
        "tests",
        "docs",
        "modules",
        "backend",
        "api",
        "packages",
        "examples",
    }
)

CATEGORY_RANK = {
    "source_code_reference": 6,
    "config_reference": 5,
    "deleted_directory": 4,
    "documentation_reference": 3,
    "deleted_file": 5,
    "renamed_path": 6,
    "moved_path": 6,
    "unknown": 1,
}

CATEGORY_RANK_EXPLANATION = """
Priority ranking (higher = review first):
1. `history_quality=reliable` — git history supports path existence and deletion timeline.
2. `source_code_reference` — concrete source file with extension (.py, .go, …).
3. `config_reference` — manifest/config artifact (setup.py, *.yaml, …).
4. `deleted_directory` — directory prefix; may be generic if top-level name only.
5. `documentation_reference` — doc paths; drift possible but governance differs.
6. `unknown` — globs, weak resolution, or unclassified patterns.

`priority_score` combines category rank (0–60), history quality (0–30), deletion evidence (0–10),
and instruction reference signal (0–10), minus penalties for globs (−15) and parser-artifact hints (−10).
""".strip()

HISTORY_QUALITY_SCORE = {"reliable": 30, "uncertain": 12, "failed": 0}


def _norm(value: object) -> str:
    return "" if value is None else str(value).strip()


def _has_glob(text: str) -> bool:
    return any(ch in text for ch in GLOB_CHARS)


def _is_generic_path(raw: str, resolved: str) -> bool:
    for token in (raw.strip("/"), resolved.strip("/")):
        base = token.rsplit("/", 1)[-1].lower()
        if base in GENERIC_PATH_TOKENS or token.lower() in GENERIC_PATH_TOKENS:
            return True
    return False


def _instruction_still_references(row: pd.Series) -> bool:
    if _norm(row.get("current_status")) != "stale":
        return False
    if _norm(row.get("context_line_number")):
        return True
    excerpt = _norm(row.get("context_excerpt"))
    return bool(excerpt) and "not found verbatim" not in excerpt.lower()


def compute_priority_score(row: pd.Series) -> tuple[int, str]:
    category = _norm(row.get("auto_drift_category")) or "unknown"
    cat_rank = CATEGORY_RANK.get(category, 1)
    cat_points = cat_rank * 10

    hq = _norm(row.get("history_quality"))
    hist_points = HISTORY_QUALITY_SCORE.get(hq, 0)

    deleted_points = 10 if _norm(row.get("deleted_commit")) else 0
    ref_points = 10 if _instruction_still_references(row) else 0

    penalty = 0
    penalties: list[str] = []
    raw = _norm(row.get("extracted_reference"))
    resolved = _norm(row.get("resolved_path"))
    if _has_glob(raw) or _has_glob(resolved):
        penalty += 15
        penalties.append("glob pattern")
    if _norm(row.get("heuristic_likely_artifact")) == "yes":
        penalty += 10
        penalties.append("artifact heuristic")
    if _is_generic_path(raw, resolved):
        penalty += 8
        penalties.append("generic path token")
    if _norm(row.get("resolution_status")) == "partial_resolution":
        penalty += 8
        penalties.append("partial resolution")
    if hq == "failed":
        penalty += 5
        penalties.append("failed history lookup")

    score = max(0, cat_points + hist_points + deleted_points + ref_points - penalty)
    parts = [
        f"category={category} (+{cat_points})",
        f"history={hq} (+{hist_points})",
        f"deleted_commit (+{deleted_points})",
        f"instruction_ref (+{ref_points})",
    ]
    if penalties:
        parts.append(f"penalties: {', '.join(penalties)} (−{penalty})")
    explanation = "; ".join(parts) + f" → score={score}"
    return score, explanation


def compute_evidence_strength(row: pd.Series) -> str:
    raw = _norm(row.get("extracted_reference"))
    resolved = _norm(row.get("resolved_path"))
    hq = _norm(row.get("history_quality"))
    deleted = _norm(row.get("deleted_commit"))
    resolution = _norm(row.get("resolution_status"))

    weak_reasons = 0
    if hq in {"failed", "uncertain"}:
        weak_reasons += 1
    if _has_glob(raw) or _has_glob(resolved):
        weak_reasons += 2
    if _is_generic_path(raw, resolved):
        weak_reasons += 1
    if _norm(row.get("heuristic_likely_artifact")) == "yes":
        weak_reasons += 1
    if resolution == "partial_resolution":
        weak_reasons += 1
    if _norm(row.get("auto_drift_category")) == "unknown":
        weak_reasons += 1

    if weak_reasons >= 2:
        return "weak"

    if (
        hq == "reliable"
        and deleted
        and _instruction_still_references(row)
        and weak_reasons == 0
    ):
        return "strong"

    if _norm(row.get("historical_existence")) == "existed_before" and (
        _norm(row.get("first_seen_commit")) or _norm(row.get("last_seen_commit"))
    ):
        return "moderate"

    return "weak"


def render_review_md(rows: list[dict]) -> str:
    lines = [
        "# Validated drift review packets",
        "",
        "Ground-truth validation workbook — **pilot subset, no population claims.**",
        "",
        "Fill manual labels in `validated_drift_ground_truth.csv`.",
        "",
        "## Priority ranking explained",
        "",
        CATEGORY_RANK_EXPLANATION,
        "",
    ]

    for row in rows:
        lines.extend(
            [
                f"## [{row['priority_rank']}] `{row['candidate_id']}` — priority score **{row['priority_score']}**",
                "",
                f"- **Evidence strength:** `{row['evidence_strength']}`",
                f"- **Repository:** `{row['repo_id']}`",
                f"- **Instruction file:** `{row['instruction_file']}`",
                f"- **Extracted reference:** `{row['extracted_reference']}`",
                f"- **Resolved path:** `{row['resolved_path']}`",
                f"- **Auto category:** `{row['auto_drift_category']}`",
                f"- **History quality:** `{row['history_quality']}`",
                f"- **Current status:** `{row['current_status']}`",
                "",
                "### Historical context",
                "",
                f"- First appearance: `{row.get('first_seen_date') or 'n/a'}` (`{row.get('first_seen_commit', '')[:12]}…`)",
                f"- Last seen: `{row.get('last_seen_date') or 'n/a'}` (`{str(row.get('last_seen_commit', ''))[:12]}…`)",
                f"- Deletion commit: `{row.get('deleted_date') or 'n/a'}` (`{str(row.get('deleted_commit', ''))[:12]}…`)",
                f"- Path lifetime (days): `{row.get('path_lifetime_days') or 'n/a'}`",
                f"- History path used: `{row.get('history_path_used') or 'n/a'}`",
                "",
                "### Instruction context",
                "",
                f"- Section heading: {row.get('section_heading') or '_(none)_'}",
                f"- Line: {row.get('context_line_number') or 'n/a'}",
                "",
                "```markdown",
                row.get("context_excerpt") or "(no excerpt)",
                "```",
                "",
                f"**Priority explanation:** {row.get('priority_explanation', '')}",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines)


def render_decision_report(rows: list[dict]) -> str:
    by_strength = Counter(r["evidence_strength"] for r in rows)
    strong = [r for r in rows if r["evidence_strength"] == "strong"]
    moderate = [r for r in rows if r["evidence_strength"] == "moderate"]
    weak = [r for r in rows if r["evidence_strength"] == "weak"]

    lines = [
        "# Validated drift — decision support (preliminary)",
        "",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "**Not ground truth yet** — manual labels in `validated_drift_ground_truth.csv` are empty.",
        "",
        "## Stage 5 — Evidence strength estimate (automatic, not manual)",
        "",
        f"- **Strong:** {by_strength.get('strong', 0)} candidates",
        f"- **Moderate:** {by_strength.get('moderate', 0)} candidates",
        f"- **Weak:** {by_strength.get('weak', 0)} candidates",
        "",
        "### Strong candidates",
        "",
    ]
    if strong:
        for r in strong:
            lines.append(
                f"- `{r['candidate_id']}` `{r['repo_id']}`: `{r['extracted_reference']}` "
                f"(deleted {r.get('deleted_date') or 'n/a'})"
            )
    else:
        lines.append("_None._")

    lines.extend(["", "### Moderate candidates", ""])
    if moderate:
        for r in moderate[:15]:
            lines.append(f"- `{r['candidate_id']}` `{r['repo_id']}`: `{r['extracted_reference']}`")
        if len(moderate) > 15:
            lines.append(f"- … and {len(moderate) - 15} more (see priority CSV).")
    else:
        lines.append("_None._")

    lines.extend(["", "### Weak candidates", ""])
    lines.append(f"{len(weak)} candidates — review last or mark as parser artifacts.")

    lines.extend(
        [
            "",
            "## Stage 6 — Decision support",
            "",
            "### 1. If only **strong** candidates are accepted, how many remain?",
            "",
            f"**{len(strong)}** (automatic pre-filter; manual review may accept fewer).",
            "",
            "### 2. If **strong + moderate** are accepted, how many remain?",
            "",
            f"**{len(strong) + len(moderate)}** (upper bound before manual pruning).",
            "",
            "### 3. Is the resulting phenomenon large enough for a dedicated paper?",
            "",
        ]
    )

    if len(strong) >= 5:
        paper_answer = (
            "A **focused mixed-methods paper** is plausible if manual review confirms most strong "
            f"candidates ({len(strong)} automatic strong): phenomenon exists but is not ubiquitous."
        )
    elif len(strong) + len(moderate) >= 8:
        paper_answer = (
            "A **focused qualitative / case-study paper** is more defensible than a prevalence paper; "
            "the core phenomenon appears real but narrow."
        )
    else:
        paper_answer = (
            "Unlikely as a prevalence paper on current evidence alone; consider reframing as "
            "methodological note unless manual review upgrades several moderate candidates."
        )
    lines.append(paper_answer)

    lines.extend(
        [
            "",
            "### 4. Recommended next study design",
            "",
        ]
    )

    if len(strong) >= 8:
        next_study = "**Mixed-methods study** — manual-validated core set + bounded full-corpus measurement of the same evidence tiers (not headline prevalence)."
    elif len(strong) >= 3:
        next_study = "**Focused qualitative study** on validated strong cases, with optional bounded measurement replication on the same 8 pilot repos."
    else:
        next_study = "**Focused qualitative study** first; defer full-corpus measurement until ground-truth labels confirm ≥5 real drift cases."

    lines.append(next_study)

    lines.extend(
        [
            "",
            "## Objective reminder",
            "",
            "Maximizing drift counts is not the goal. The defensible core is the manually validated "
            "subset of strong/moderate cases with reliable deletion history and literal instruction references.",
            "",
        ]
    )
    return "\n".join(lines)


def build_package(candidates_csv: Path, out_dir: Path) -> None:
    df = pd.read_csv(candidates_csv, dtype=str, keep_default_na=False)
    if df.empty:
        raise SystemExit(f"No rows in {candidates_csv}")

    scored: list[dict] = []
    for _, row in df.iterrows():
        record = row.to_dict()
        score, explanation = compute_priority_score(row)
        record["priority_score"] = score
        record["priority_explanation"] = explanation
        record["evidence_strength"] = compute_evidence_strength(row)
        scored.append(record)

    scored.sort(key=lambda r: (-int(r["priority_score"]), r["candidate_id"]))
    for rank, record in enumerate(scored, start=1):
        record["priority_rank"] = rank

    out_dir.mkdir(parents=True, exist_ok=True)

    priority_cols = [
        "priority_rank",
        "priority_score",
        "priority_explanation",
        "evidence_strength",
        "candidate_id",
        "repo_id",
        "instruction_file",
        "extracted_reference",
        "resolved_path",
        "extraction_rule",
        "confidence",
        "current_status",
        "historical_existence",
        "auto_drift_category",
        "history_quality",
        "first_seen_commit",
        "first_seen_date",
        "deleted_commit",
        "deleted_date",
        "path_lifetime_days",
        "heuristic_likely_drift",
        "heuristic_likely_artifact",
    ]
    priority_df = pd.DataFrame(scored)[priority_cols]
    priority_path = out_dir / "validated_drift_priority.csv"
    priority_df.to_csv(priority_path, index=False)

    ground_truth_cols = priority_cols + [
        "is_real_drift",
        "confidence",
        "drift_type",
        "notes",
    ]
    gt_df = pd.DataFrame(scored)[priority_cols].copy()
    for col in ("is_real_drift", "confidence", "drift_type", "notes"):
        gt_df[col] = ""
    gt_path = out_dir / "validated_drift_ground_truth.csv"
    gt_df.to_csv(gt_path, index=False)

    review_path = out_dir / "validated_drift_review.md"
    review_path.write_text(render_review_md(scored), encoding="utf-8")

    decision_path = out_dir / "validated_drift_decision_report.md"
    decision_path.write_text(render_decision_report(scored), encoding="utf-8")

    meta = {
        "n_candidates": len(scored),
        "evidence_strength": dict(Counter(r["evidence_strength"] for r in scored)),
        "priority_score_range": [int(scored[-1]["priority_score"]), int(scored[0]["priority_score"])],
    }
    (out_dir / "validated_drift_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {priority_path}")
    print(f"wrote {gt_path}")
    print(f"wrote {review_path}")
    print(f"wrote {decision_path}")
    print(f"evidence: strong={meta['evidence_strength'].get('strong', 0)} "
          f"moderate={meta['evidence_strength'].get('moderate', 0)} "
          f"weak={meta['evidence_strength'].get('weak', 0)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidates-csv",
        type=Path,
        default=ROOT / "results/misguidance/drift_candidates/drift_candidates.csv",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "results/misguidance/drift_candidates",
    )
    args = parser.parse_args()
    build_package(args.candidates_csv, args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
