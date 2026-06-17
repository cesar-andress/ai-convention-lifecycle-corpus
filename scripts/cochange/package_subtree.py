"""Package-subtree scope inference for monorepo instruction files."""

from __future__ import annotations

from cochange.scope import normalize_path

PACKAGE_INDICATOR_FILES = frozenset(
    {
        "package.json",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "requirements-dev.txt",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "Cargo.toml",
        "go.mod",
        "composer.json",
        "Dockerfile",
    }
)

TOP_LEVEL_DIR_HINTS = (
    "packages/",
    "apps/",
    "services/",
    "modules/",
    "python_modules/",
    "libs/",
    "src/",
)


def is_root_instruction_file(instruction_path: str) -> bool:
    return "/" not in normalize_path(instruction_path)


def _dir_prefix(path: str) -> str:
    path = normalize_path(path)
    if not path:
        return ""
    return path if path.endswith("/") else path + "/"


def _parent_dir_prefix(path: str) -> str:
    path = normalize_path(path)
    if "/" not in path:
        return ""
    return path.rsplit("/", 1)[0] + "/"


def detect_candidate_package_roots(head_files: set[str]) -> dict[str, set[str]]:
    """Map package-root directory prefix -> indicator filenames found there."""
    roots: dict[str, set[str]] = {}
    for path in head_files:
        base = path.rsplit("/", 1)[-1]
        if base not in PACKAGE_INDICATOR_FILES:
            continue
        root_prefix = _parent_dir_prefix(path) if "/" in path else ""
        roots.setdefault(root_prefix, set()).add(base)
    return roots


def _resolved_prefix(resolved: str) -> str:
    resolved = normalize_path(resolved)
    if not resolved:
        return ""
    if resolved.endswith("/"):
        return resolved
    if "/" in resolved:
        return _parent_dir_prefix(resolved)
    return resolved + "/"


def _contains_path(prefix: str, target: str) -> bool:
    prefix = _dir_prefix(prefix)
    target = normalize_path(target)
    if not prefix:
        return True
    return target == prefix.rstrip("/") or target.startswith(prefix)


def _package_roots_for_path(path: str, candidates: dict[str, set[str]]) -> set[str]:
    """Smallest candidate package roots that contain path (exclude repo root)."""
    path = normalize_path(path)
    matches: list[str] = []
    for root_key in candidates:
        if root_key == "":
            continue
        prefix = _dir_prefix(root_key)
        if _contains_path(prefix, path):
            matches.append(prefix)
    if not matches:
        return set()
    # Prefer most specific (longest prefix)
    matches.sort(key=len, reverse=True)
    best_len = len(matches[0])
    return {m for m in matches if len(m) == best_len}


def _top_level_hint_for_reference(resolved: str, raw: str, head_files: set[str]) -> set[str]:
    selected: set[str] = set()
    resolved = normalize_path(resolved)
    raw = normalize_path(raw.strip())
    for hint in TOP_LEVEL_DIR_HINTS:
        hint_dir = hint.rstrip("/")
        exists = hint_dir in head_files or any(p.startswith(hint) for p in head_files)
        if not exists:
            continue
        if resolved.startswith(hint) or resolved == hint_dir:
            selected.add(hint)
        elif raw.rstrip("/") == hint_dir or raw.rstrip("/") + "/" == hint:
            selected.add(hint)
    return selected


def infer_package_subtree_scope(
    instruction_path: str,
    head_files: set[str],
    content_ref_rows: list[dict],
) -> tuple[frozenset[str], str, int, list[str]]:
    """
    Return (governed_prefixes, status, n_package_roots_detected, package_roots_used_list).
    """
    instruction_path = normalize_path(instruction_path)
    candidates = detect_candidate_package_roots(head_files)
    n_detected = len(candidates)
    refs_used = [r for r in content_ref_rows if r.get("used_for_scope")]

    if not is_root_instruction_file(instruction_path):
        return _infer_nested(instruction_path, head_files, candidates, n_detected)

    if not refs_used:
        return frozenset(), "inconclusive_no_references", n_detected, []

    selected: set[str] = set()
    non_root_candidates = {k: v for k, v in candidates.items() if k != ""}

    for row in refs_used:
        resolved = normalize_path(str(row.get("resolved_path") or ""))
        raw = str(row.get("raw_reference") or row.get("raw_text") or "")
        if not resolved:
            continue

        selected.update(_package_roots_for_path(resolved, non_root_candidates))
        if "/" in resolved:
            selected.update(_package_roots_for_path(_parent_dir_prefix(resolved), non_root_candidates))

        selected.update(_top_level_hint_for_reference(resolved, raw, head_files))

    normalized = {_dir_prefix(p) for p in selected if p}
    if not normalized:
        return frozenset(), "inconclusive_no_package_roots", n_detected, []

    return frozenset(normalized), "usable", n_detected, sorted(normalized)


def _infer_nested(
    instruction_path: str,
    head_files: set[str],
    candidates: dict[str, set[str]],
    n_detected: int,
) -> tuple[frozenset[str], str, int, list[str]]:
    instruction_path = normalize_path(instruction_path)
    matches: list[str] = []
    for root_key, _ in candidates.items():
        if root_key == "":
            continue
        prefix = _dir_prefix(root_key)
        if instruction_path.startswith(prefix) or instruction_path == root_key.rstrip("/"):
            matches.append(prefix)

    if matches:
        best = max(matches, key=len)
        return frozenset([best]), "usable", n_detected, [best]

    parent = _parent_dir_prefix(instruction_path)
    if parent:
        return frozenset([parent]), "fallback_subtree_nested", n_detected, [parent]

    return frozenset(), "inconclusive_no_package_roots", n_detected, []
