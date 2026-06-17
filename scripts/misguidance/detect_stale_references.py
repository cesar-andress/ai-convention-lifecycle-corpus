#!/usr/bin/env python3
"""Detect stale content references in instruction files at repository HEAD."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cochange.content_refs import CONFIG_BASENAMES, extract_content_references
from cochange.scope import normalize_path
from lifecycle.git_utils import list_head_files, run_git

DOC_EXTENSIONS = (".md", ".rst", ".txt", ".adoc", ".html", ".ipynb")
DOC_PATH_MARKERS = ("docs/", "contributing-docs", "/doc/", "documentation", "adr/")
COMMAND_RULES = frozenset({"make_command_to_makefile"})

STATUS_VALID = "valid"
STATUS_STALE = "stale"
STATUS_AMBIGUOUS = "ambiguous"
STATUS_UNRESOLVED = "unresolved"
STATUS_UNKNOWN_COMMAND = "unknown_command"
STATUS_DOC_REFERENCE = "doc_reference"


def _norm(value: object) -> str:
    return "" if value is None else str(value).strip()


def _basename(path: str) -> str:
    path = _norm(path).rstrip("/")
    return path.rsplit("/", 1)[-1] if path else ""


def is_documentation_reference(row: dict) -> bool:
    ref_type = _norm(row.get("reference_type")).lower()
    rule = _norm(row.get("extraction_rule")).lower()
    raw = _norm(row.get("raw_reference") or row.get("raw_text")).lower()
    resolved = _norm(row.get("resolved_path")).lower()

    if ref_type in {"markdown_link"} or rule == "markdown_link":
        return True
    if any(resolved.endswith(ext) for ext in DOC_EXTENSIONS):
        return True
    if any(marker in resolved for marker in DOC_PATH_MARKERS):
        return True
    if any(marker in raw for marker in DOC_PATH_MARKERS):
        return True
    if resolved.endswith("agents.md") or resolved.endswith("claude.md"):
        return ref_type != "include_directive"
    return False


def is_command_reference(row: dict) -> bool:
    rule = _norm(row.get("extraction_rule"))
    ref_type = _norm(row.get("reference_type")).lower()
    return rule in COMMAND_RULES or ref_type == "command"


def is_config_reference(row: dict) -> bool:
    ref_type = _norm(row.get("reference_type")).lower()
    rule = _norm(row.get("extraction_rule")).lower()
    base = _basename(_norm(row.get("resolved_path") or row.get("raw_reference"))).lower()
    return ref_type == "config_file" or rule == "known_config_filename" or base in {b.lower() for b in CONFIG_BASENAMES}


def is_directory_reference(row: dict) -> bool:
    resolved = _norm(row.get("resolved_path"))
    ref_type = _norm(row.get("reference_type")).lower()
    rule = _norm(row.get("extraction_rule")).lower()
    if resolved.endswith("/"):
        return True
    if ref_type in {"directory_mention"}:
        return True
    if rule == "common_directory_name":
        return True
    if "/" not in resolved and not Path(resolved).suffix:
        return False
    return resolved.endswith("/") or rule in {"common_directory_name"}


def _dot_prefix_lost(raw: str, resolved: str) -> bool:
    raw_clean = _norm(raw).strip("[]()`")
    resolved = _norm(resolved)
    if raw_clean.startswith(".") and not resolved.startswith("."):
        raw_base = _basename(raw_clean)
        if raw_base.startswith(".") and _basename(resolved) == raw_base.lstrip("."):
            return True
        if ".github/" in raw_clean and not resolved.startswith(".github/"):
            return True
        if raw_clean.startswith("./") or raw_clean.startswith("../"):
            return False
        if "/" in raw_clean:
            return True
    if ".github/" in raw_clean and ".github/" not in resolved:
        return True
    return False


def resolution_uncertain(row: dict, *, misguidance_extraction: bool = False) -> bool:
    resolution_status = _norm(row.get("resolution_status"))
    if resolution_status == "unresolved":
        return True
    if resolution_status == "partial_resolution":
        return True
    confidence = _norm(row.get("confidence")).lower()
    resolved = _norm(row.get("resolved_path"))
    raw = _norm(row.get("raw_reference") or row.get("raw_text"))
    if not resolved:
        return True
    if misguidance_extraction and confidence == "medium":
        return resolution_status in {"partial_resolution", "unresolved"}
    if confidence == "low":
        return True
    if _dot_prefix_lost(raw, resolved):
        return True
    return False


def _intended_paths(raw: str, resolved: str) -> list[str]:
    raw_clean = normalize_path(raw.strip("[]()`").split("#")[0])
    paths: list[str] = []
    if raw_clean:
        paths.append(raw_clean)
    if resolved:
        paths.append(normalize_path(resolved))
    if raw_clean.endswith("/") and not raw_clean.endswith("//"):
        paths.append(raw_clean)
    deduped: list[str] = []
    for p in paths:
        if p and p not in deduped:
            deduped.append(p)
    return deduped


def path_exists_in_head(resolved: str, head_files: set[str]) -> bool:
    resolved = normalize_path(resolved)
    if not resolved:
        return False
    if resolved in head_files:
        return True
    dir_prefix = resolved if resolved.endswith("/") else resolved + "/"
    return any(p.startswith(dir_prefix) for p in head_files)


def reference_exists_at_head(raw: str, resolved: str, head_files: set[str]) -> bool:
    for candidate in _intended_paths(raw, resolved):
        if path_exists_in_head(candidate, head_files):
            return True
    return False


def check_historical_existence(repo_dir: Path, resolved_path: str, raw_reference: str = "") -> str:
    """Return existed_before | never_existed | unknown."""
    candidates: list[str] = []
    for path in (resolved_path, raw_reference):
        path = normalize_path(path.strip("[]()`").split("#")[0])
        if not path:
            continue
        candidates.extend([path])
        if not path.endswith("/"):
            candidates.append(path + "/")
        if "/" in path:
            candidates.append(path.rsplit("/", 1)[0] + "/")

    seen: set[str] = set()
    for candidate in candidates:
        candidate = normalize_path(candidate)
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        try:
            proc = run_git(
                ["git", "log", "--all", "--pretty=format:%H", "-1", "--", candidate],
                cwd=repo_dir,
                timeout=120,
            )
        except Exception:
            return "unknown"
        if proc.returncode == 0 and proc.stdout.strip():
            return "existed_before"

    return "never_existed"


def classify_misguidance_category(
    status: str,
    row: dict,
    historical_existence: str,
) -> str:
    if status == STATUS_UNRESOLVED:
        return "unresolved_reference"
    if status in {STATUS_VALID, STATUS_UNKNOWN_COMMAND, STATUS_AMBIGUOUS}:
        return ""
    if status == STATUS_DOC_REFERENCE:
        return "stale_doc_reference"
    if status != STATUS_STALE:
        return ""

    if is_config_reference(row):
        category = "stale_config"
    elif is_directory_reference(row):
        category = "stale_directory"
    elif is_documentation_reference(row):
        category = "stale_doc_reference"
    else:
        category = "stale_path"

    return category


def counts_toward_primary_misguidance(status: str, category: str) -> bool:
    if status != STATUS_STALE:
        return False
    return category not in {"stale_doc_reference", "unresolved_reference", ""}


def detect_reference_status(
    row: dict,
    head_files: set[str],
    repo_dir: Path | None = None,
    *,
    check_history: bool = False,
    misguidance_extraction: bool = False,
) -> dict:
    """Classify one extracted reference row."""
    resolved = _norm(row.get("resolved_path"))
    raw = _norm(row.get("raw_reference") or row.get("raw_text") or row.get("extracted_reference"))
    exists = reference_exists_at_head(raw, resolved, head_files)
    resolution_status = _norm(row.get("resolution_status"))

    historical_existence = ""
    status = STATUS_UNRESOLVED
    category = ""

    if is_command_reference(row):
        mapped = _basename(resolved).lower() in {"makefile"} | {b.lower() for b in CONFIG_BASENAMES}
        if mapped and exists:
            status = STATUS_VALID
        else:
            status = STATUS_UNKNOWN_COMMAND
    elif not resolved:
        status = STATUS_UNRESOLVED
    elif resolution_status == "resolved_intended" or (exists and resolution_status in {"resolved", ""}):
        status = STATUS_VALID
    elif resolution_uncertain(row, misguidance_extraction=misguidance_extraction):
        if exists:
            status = STATUS_VALID
        else:
            status = STATUS_AMBIGUOUS
    elif exists:
        status = STATUS_VALID
    elif is_documentation_reference(row):
        status = STATUS_DOC_REFERENCE
    else:
        status = STATUS_STALE

    history_targets = {STATUS_STALE, STATUS_DOC_REFERENCE, STATUS_UNRESOLVED, STATUS_AMBIGUOUS}
    if check_history and status in history_targets and repo_dir is not None:
        historical_existence = check_historical_existence(repo_dir, resolved, raw)

    category = classify_misguidance_category(status, row, historical_existence)

    return {
        "reference": raw,
        "extracted_reference": raw,
        "reference_type": _norm(row.get("reference_type")),
        "extraction_rule": _norm(row.get("extraction_rule")),
        "confidence": _norm(row.get("confidence")),
        "resolved_path": resolved,
        "resolution_status": resolution_status,
        "exists_in_head": exists,
        "status": status,
        "misguidance_category": category,
        "historical_existence": historical_existence,
        "counts_toward_primary_misguidance": counts_toward_primary_misguidance(status, category),
        "parser_version": _norm(row.get("parser_version")),
        "extraction_mode": "misguidance_v2" if misguidance_extraction else "scope_v2",
    }


def detect_stale_references(
    repo_id: str,
    repo_dir: Path,
    instruction_file: str,
    *,
    check_history: bool = True,
    misguidance_extraction: bool = False,
) -> list[dict]:
    head_files = set(list_head_files(repo_dir))
    extracted = extract_content_references(
        repo_id,
        repo_dir,
        instruction_file,
        head_files,
        misguidance_mode=misguidance_extraction,
    )

    rows: list[dict] = []
    for ref in extracted:
        result = detect_reference_status(
            ref,
            head_files,
            repo_dir,
            check_history=check_history,
            misguidance_extraction=misguidance_extraction,
        )
        rows.append(
            {
                "repo_id": repo_id,
                "instruction_file": instruction_file,
                **result,
            }
        )
    return rows


def aggregate_metrics(rows: list[dict], repo_id: str, instruction_file: str | None = None) -> dict:
    n = len(rows)
    status_counts = {s: 0 for s in (
        STATUS_VALID,
        STATUS_STALE,
        STATUS_AMBIGUOUS,
        STATUS_UNRESOLVED,
        STATUS_UNKNOWN_COMMAND,
        STATUS_DOC_REFERENCE,
    )}
    category_counts: dict[str, int] = {}
    hist_counts: dict[str, int] = {}

    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
        cat = row.get("misguidance_category") or ""
        if cat:
            category_counts[cat] = category_counts.get(cat, 0) + 1
        hist = row.get("historical_existence") or ""
        if hist:
            hist_counts[hist] = hist_counts.get(hist, 0) + 1
        if hist == "never_existed" and row.get("status") in {
            STATUS_STALE,
            STATUS_DOC_REFERENCE,
            STATUS_UNRESOLVED,
            STATUS_AMBIGUOUS,
        }:
            category_counts["never_existed_reference"] = category_counts.get("never_existed_reference", 0) + 1
        if hist == "existed_before" and row.get("status") in {
            STATUS_STALE,
            STATUS_DOC_REFERENCE,
            STATUS_UNRESOLVED,
            STATUS_AMBIGUOUS,
        }:
            category_counts["existed_before_reference"] = category_counts.get("existed_before_reference", 0) + 1

    n_primary_stale = sum(1 for r in rows if r.get("counts_toward_primary_misguidance"))
    n_stale_all = status_counts[STATUS_STALE] + status_counts[STATUS_DOC_REFERENCE]

    out = {
        "repo_id": repo_id,
        "instruction_file": instruction_file or "__repo_total__",
        "n_references": n,
        "n_valid": status_counts[STATUS_VALID],
        "n_stale": status_counts[STATUS_STALE],
        "n_stale_doc": status_counts[STATUS_DOC_REFERENCE],
        "n_stale_all": n_stale_all,
        "n_primary_stale": n_primary_stale,
        "n_ambiguous": status_counts[STATUS_AMBIGUOUS],
        "n_unresolved": status_counts[STATUS_UNRESOLVED],
        "n_unknown_command": status_counts[STATUS_UNKNOWN_COMMAND],
        "stale_rate": (n_primary_stale / n) if n else None,
        "stale_rate_all": (n_stale_all / n) if n else None,
        "n_existed_before": hist_counts.get("existed_before", 0),
        "n_never_existed": hist_counts.get("never_existed", 0),
        "n_history_unknown": hist_counts.get("unknown", 0),
        **{f"n_cat_{k}": v for k, v in sorted(category_counts.items())},
    }
    return out
