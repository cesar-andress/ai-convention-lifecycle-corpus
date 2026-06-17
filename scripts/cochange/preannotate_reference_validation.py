#!/usr/bin/env python3
"""Conservative pre-annotation draft for manual reference validation (not final)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.corpus_paths import configure

ROOT = configure()

ANNOTATOR = "PREANNOTATION"
DRAFT_NOTE = "PREANNOTATION draft — requires human review before use in validation summary."

CONFIG_BASENAMES = {
    "package.json",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "requirements-dev.txt",
    "go.mod",
    "go.sum",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "cargo.toml",
    "composer.json",
    "dockerfile",
    "uv.lock",
    "filenames.gni",
}

DOC_EXTENSIONS = {".md", ".rst", ".txt", ".adoc", ".html"}


def _norm(value: object) -> str:
    return "" if value is None else str(value).strip()


def _basename(path: str) -> str:
    path = _norm(path).rstrip("/")
    return path.rsplit("/", 1)[-1] if path else ""


def _is_directory_resolved(resolved: str) -> bool:
    resolved = _norm(resolved)
    return resolved.endswith("/") or (
        resolved != "" and "/" in resolved and not Path(resolved).suffix
    )


def _is_include_pointer(raw: str, resolved: str) -> bool:
    raw_l = raw.strip()
    base = _basename(resolved)
    if raw_l.startswith("@") and base.upper().endswith(".MD"):
        return True
    if re.fullmatch(r"(?i)agents\.md|claude\.md|readme\.md", raw_l):
        return False
    if re.search(r"(?i)(agents|claude)\.md$", resolved) and raw_l.endswith(base):
        return True
    return False


def _is_build_command(raw: str, rule: str) -> bool:
    if rule != "make_command_to_makefile":
        return False
    return not _is_test_command(raw, rule)


def _is_test_command(raw: str, rule: str) -> bool:
    if rule != "make_command_to_makefile":
        return False
    raw_l = raw.lower()
    return any(t in raw_l for t in ("test", "check", "sanity", "pytest", "verify"))


def _dot_prefix_lost(raw: str, resolved: str) -> bool:
    for token in (".github/", ".apache-", "./"):
        if token in raw and token.lstrip("./") in resolved and token not in resolved:
            return True
    if raw.strip().startswith(".") and not resolved.startswith("."):
        raw_base = _basename(raw.strip("[]()`"))
        if raw_base.startswith(".") and _basename(resolved) == raw_base.lstrip("."):
            return True
    return False


def _is_documentation_path(resolved: str) -> bool:
    resolved_l = resolved.lower()
    if resolved_l.startswith("docs/") or "contributing-docs" in resolved_l:
        return True
    if "/doc/" in resolved_l or "/docs/" in resolved_l:
        return True
    return any(resolved_l.endswith(ext) for ext in DOC_EXTENSIONS)


def _is_config_path(resolved: str, raw: str = "") -> bool:
    base = _basename(resolved).lower()
    raw_base = _basename(raw.strip("[]()`")).lower()
    if base in CONFIG_BASENAMES or raw_base in CONFIG_BASENAMES:
        return True
    return base.endswith(".lock") or raw_base.endswith(".lock")


def _relative_resolution_suspect(raw: str, resolved: str) -> bool:
    raw_l = raw.lower()
    resolved_l = resolved.lower()
    if raw_l.startswith("/") and not resolved_l.startswith("docs/"):
        return True
    if "documentation" in raw_l and resolved_l != raw_l.strip("[]()"):
        return True
    return False


def preannotate_row(row: pd.Series) -> tuple[dict[str, str], list[str], bool]:
    """Return annotation dict, review reasons, auto_confident flag."""
    raw = _norm(row["raw_reference"])
    resolved = _norm(row["resolved_path"])
    rule = _norm(row["extraction_rule"])
    confidence = _norm(row["confidence"]).lower()
    review_reasons: list[str] = []

    base = {
        "manual_is_reference_correct": "",
        "manual_resolved_path_correct": "",
        "manual_should_be_used_for_scope": "",
        "manual_reference_category": "",
        "manual_notes": DRAFT_NOTE,
        "annotator": ANNOTATOR,
        "annotated_at": date.today().isoformat(),
    }

    def finish(**overrides: str) -> tuple[dict[str, str], list[str], bool]:
        out = {**base, **overrides}
        confident = confidence != "low" and not review_reasons
        if confidence == "low":
            review_reasons.append("low parser confidence")
        if rule == "markdown_link" and (
            _dot_prefix_lost(raw, resolved) or _relative_resolution_suspect(raw, resolved)
        ):
            review_reasons.append("markdown link resolution")
        if _dot_prefix_lost(raw, resolved):
            review_reasons.append("possible dot-prefix resolution error")
            if out["manual_resolved_path_correct"] == "TRUE":
                out["manual_resolved_path_correct"] = "AMBIGUOUS"
                out["manual_notes"] = (
                    f"{DRAFT_NOTE} Verify resolved path; leading dot or .github prefix may be wrong."
                )
        if _relative_resolution_suspect(raw, resolved):
            review_reasons.append("relative or docs-path resolution suspect")
        return out, review_reasons, confident and not review_reasons

    # Rule 6: low confidence and not clearly classifiable
    if confidence == "low":
        if rule == "code_span" and _basename(resolved).lower() == "readme.md":
            return finish(
                manual_is_reference_correct="TRUE",
                manual_resolved_path_correct="TRUE",
                manual_should_be_used_for_scope="FALSE",
                manual_reference_category="documentation_reference",
            )
        if rule == "markdown_link" and _relative_resolution_suspect(raw, resolved):
            return finish(
                manual_is_reference_correct="AMBIGUOUS",
                manual_resolved_path_correct="AMBIGUOUS",
                manual_should_be_used_for_scope="AMBIGUOUS",
                manual_reference_category="ambiguous",
                manual_notes=f"{DRAFT_NOTE} Low confidence; unclear resolution/governance.",
            )
        return finish(
            manual_is_reference_correct="AMBIGUOUS",
            manual_resolved_path_correct="AMBIGUOUS",
            manual_should_be_used_for_scope="AMBIGUOUS",
            manual_reference_category="ambiguous",
            manual_notes=f"{DRAFT_NOTE} Low confidence; not clearly classifiable.",
        )

    # Rule 3: include pointers
    if _is_include_pointer(raw, resolved):
        return finish(
            manual_is_reference_correct="TRUE",
            manual_resolved_path_correct="TRUE",
            manual_should_be_used_for_scope="TRUE",
            manual_reference_category="include_pointer",
        )

    # Rule 5: build/test commands
    if rule == "make_command_to_makefile":
        category = "test_command" if _is_test_command(raw, rule) else "build_command"
        return finish(
            manual_is_reference_correct="TRUE",
            manual_resolved_path_correct="TRUE",
            manual_should_be_used_for_scope="FALSE",
            manual_reference_category=category,
        )

    # Rule 4: documentation links and markdown targets
    if rule == "markdown_link":
        if _is_config_path(resolved, raw):
            return finish(
                manual_is_reference_correct="TRUE",
                manual_resolved_path_correct="TRUE",
                manual_should_be_used_for_scope="TRUE",
                manual_reference_category="config_file",
            )
        return finish(
            manual_is_reference_correct="TRUE",
            manual_resolved_path_correct="TRUE",
            manual_should_be_used_for_scope="FALSE",
            manual_reference_category="documentation_reference",
        )

    resolved_base = _basename(resolved).lower()
    raw_base = _basename(raw.strip("[]()`")).lower()

    if raw_base in CONFIG_BASENAMES or resolved_base in CONFIG_BASENAMES or rule == "known_config_filename":
        return finish(
            manual_is_reference_correct="TRUE",
            manual_resolved_path_correct="TRUE",
            manual_should_be_used_for_scope="TRUE",
            manual_reference_category="config_file",
        )

    if _is_documentation_path(resolved) and not _is_include_pointer(raw, resolved):
        return finish(
            manual_is_reference_correct="TRUE",
            manual_resolved_path_correct="TRUE",
            manual_should_be_used_for_scope="FALSE",
            manual_reference_category="documentation_reference",
        )

    # Rule 1: explicit directories
    if resolved.endswith("/") or rule in {"common_directory_name", "scope_section:code_span"}:
        if _is_directory_resolved(resolved) or resolved.endswith("/"):
            return finish(
                manual_is_reference_correct="TRUE",
                manual_resolved_path_correct="TRUE",
                manual_should_be_used_for_scope="TRUE",
                manual_reference_category="directory",
            )

    # Rule 2: explicit source/config files
    if resolved and ("/" in resolved or "." in _basename(resolved)):
        category = "path"
        if resolved_base.endswith(".json") and "config" in resolved.lower():
            category = "config_file"
        return finish(
            manual_is_reference_correct="TRUE",
            manual_resolved_path_correct="TRUE",
            manual_should_be_used_for_scope="TRUE",
            manual_reference_category=category,
        )

    review_reasons.append("unclassified by pre-annotation rules")
    return finish(
        manual_is_reference_correct="AMBIGUOUS",
        manual_resolved_path_correct="AMBIGUOUS",
        manual_should_be_used_for_scope="AMBIGUOUS",
        manual_reference_category="ambiguous",
        manual_notes=f"{DRAFT_NOTE} Could not classify conservatively.",
    )


def build_preannotation(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    rows: list[dict] = []
    review_rows: list[dict] = []

    for i, row in df.iterrows():
        ann, reasons, confident = preannotate_row(row)
        out = row.to_dict()
        out.update(ann)
        rows.append(out)

        needs_review = (
            ann["manual_reference_category"] == "ambiguous"
            or any(
                ann[k] == "AMBIGUOUS"
                for k in (
                    "manual_is_reference_correct",
                    "manual_resolved_path_correct",
                    "manual_should_be_used_for_scope",
                )
            )
            or _norm(row["confidence"]).lower() == "low"
            or _dot_prefix_lost(_norm(row["raw_reference"]), _norm(row["resolved_path"]))
            or _relative_resolution_suspect(_norm(row["raw_reference"]), _norm(row["resolved_path"]))
        )
        if needs_review:
            review_rows.append(
                {
                    "csv_row": int(i) + 2,
                    "repo_id": _norm(row["repo_id"]),
                    "instruction_file": _norm(row["instruction_file"]),
                    "raw_reference": _norm(row["raw_reference"]),
                    "resolved_path": _norm(row["resolved_path"]),
                    "confidence": _norm(row["confidence"]),
                    "extraction_rule": _norm(row["extraction_rule"]),
                    "preannotation_category": ann["manual_reference_category"],
                    "review_reasons": "; ".join(dict.fromkeys(reasons)) or "ambiguous or flagged labels",
                }
            )

    return pd.DataFrame(rows), review_rows


def summary_counts(df: pd.DataFrame) -> dict[str, object]:
    category_counts = Counter(_norm(v) for v in df["manual_reference_category"] if _norm(v))
    bool_counts = {
        col: Counter(_norm(v).upper() for v in df[col] if _norm(v))
        for col in (
            "manual_is_reference_correct",
            "manual_resolved_path_correct",
            "manual_should_be_used_for_scope",
        )
    }
    return {
        "total_rows": len(df),
        "annotator": ANNOTATOR,
        "annotated_at": date.today().isoformat(),
        "status": "preannotation_draft_not_final_validation",
        "category_counts": dict(sorted(category_counts.items())),
        "boolean_value_counts": {k: dict(v) for k, v in bool_counts.items()},
        "ambiguous_rows": int((df["manual_reference_category"] == "ambiguous").sum()),
        "scope_true": int((df["manual_should_be_used_for_scope"] == "TRUE").sum()),
        "scope_false": int((df["manual_should_be_used_for_scope"] == "FALSE").sum()),
    }


def render_report(summary: dict, review_rows: list[dict]) -> str:
    lines = [
        "# Reference validation pre-annotation draft",
        "",
        "**Not final validation.** Human review required before running acceptance thresholds.",
        "",
        f"- Source: `annotation/cochange_reference_validation_sample.csv`",
        f"- Draft output: `annotation/cochange_reference_validation_preannotated.csv`",
        f"- Annotator tag: `{summary['annotator']}`",
        f"- Date: `{summary['annotated_at']}`",
        "",
        "## Summary counts",
        "",
        f"- Total rows: **{summary['total_rows']}**",
        f"- Scope TRUE: **{summary['scope_true']}**",
        f"- Scope FALSE: **{summary['scope_false']}**",
        f"- Category `ambiguous`: **{summary['ambiguous_rows']}**",
        "",
        "### By category",
        "",
    ]
    for cat, count in summary["category_counts"].items():
        lines.append(f"- `{cat}`: {count}")

    lines.extend(["", "### Boolean labels", ""])
    for col, counts in summary["boolean_value_counts"].items():
        parts = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        lines.append(f"- `{col}`: {parts or 'none'}")

    lines.extend(
        [
            "",
            "## Rows still requiring human review",
            "",
            f"**{len(review_rows)}** rows flagged (ambiguous labels, low confidence, or resolution risk).",
            "",
        ]
    )
    for item in review_rows:
        lines.append(
            f"- Row **{item['csv_row']}** `{item['repo_id']}` / `{item['instruction_file']}`: "
            f"`{item['raw_reference']}` → `{item['resolved_path']}` "
            f"({item['confidence']}, `{item['extraction_rule']}`, draft=`{item['preannotation_category']}`) — "
            f"{item['review_reasons']}"
        )

    lines.extend(
        [
            "",
            "## Next steps",
            "",
            "1. Review flagged rows first, then spot-check high-confidence directory/path labels.",
            "2. Copy accepted rows into `annotation/cochange_reference_validation_sample.csv` with your annotator id.",
            "3. Run `make summarize-reference-validation` only on the human-validated CSV.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "annotation/cochange_reference_validation_sample.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "annotation/cochange_reference_validation_preannotated.csv",
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        default=ROOT / "annotation/cochange_reference_validation_preannotation_report.md",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=ROOT / "annotation/cochange_reference_validation_preannotation_summary.json",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False)
    preannotated, review_rows = build_preannotation(df)
    summary = summary_counts(preannotated)
    summary["rows_requiring_human_review"] = len(review_rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    preannotated.to_csv(args.output, index=False)
    args.report_json.write_text(
        json.dumps({"summary": summary, "review_rows": review_rows}, indent=2) + "\n",
        encoding="utf-8",
    )
    args.report_md.write_text(render_report(summary, review_rows), encoding="utf-8")

    print(f"wrote {args.output}")
    print(f"wrote {args.report_md}")
    print(f"wrote {args.report_json}")
    print(f"flagged_for_review={len(review_rows)}/{len(preannotated)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
