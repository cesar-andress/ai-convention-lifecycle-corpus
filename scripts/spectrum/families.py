"""Artifact family definitions for the synchronization spectrum pilot."""

from __future__ import annotations

import re
from dataclasses import dataclass

from cochange.scope import EXCLUDED_PREFIXES, normalize_path


@dataclass(frozen=True)
class FamilyDef:
    family_id: str
    spectrum_group: str
    label: str
    pattern: re.Pattern[str]
    anchor_priority: tuple[str, ...] = ()


FAMILIES: tuple[FamilyDef, ...] = (
    FamilyDef(
        "claude_md",
        "instructions",
        "CLAUDE.md",
        re.compile(r"(^|/)CLAUDE\.md$"),
        ("CLAUDE.md",),
    ),
    FamilyDef(
        "agents_md",
        "instructions",
        "AGENTS.md",
        re.compile(r"(^|/)AGENTS\.md$"),
        ("AGENTS.md",),
    ),
    FamilyDef(
        "cursor_rules",
        "instructions",
        "Cursor rules",
        re.compile(r"(^|/)\.cursor/rules/.*\.(md|mdc)$"),
    ),
    FamilyDef(
        "github_workflows",
        "configuration",
        "GitHub Actions workflows",
        re.compile(r"(^|/)\.github/workflows/.*\.ya?ml$"),
    ),
    FamilyDef(
        "package_json",
        "configuration",
        "package.json",
        re.compile(r"(^|/)package\.json$"),
        ("package.json",),
    ),
    FamilyDef(
        "pyproject_toml",
        "configuration",
        "pyproject.toml",
        re.compile(r"(^|/)pyproject\.toml$"),
        ("pyproject.toml",),
    ),
    FamilyDef(
        "go_mod",
        "configuration",
        "go.mod",
        re.compile(r"(^|/)go\.mod$"),
        ("go.mod",),
    ),
    FamilyDef(
        "readme",
        "documentation",
        "README.md",
        re.compile(r"(^|/)README\.md$"),
        ("README.md",),
    ),
    FamilyDef(
        "contributing",
        "documentation",
        "CONTRIBUTING.md",
        re.compile(r"(^|/)CONTRIBUTING\.md$"),
        ("CONTRIBUTING.md",),
    ),
    FamilyDef(
        "docs_index",
        "documentation",
        "docs index page",
        re.compile(r"^docs/(README\.md|index\.md|index\.html)$"),
        ("docs/README.md", "docs/index.md", "docs/index.html"),
    ),
)

FAMILY_BY_ID = {f.family_id: f for f in FAMILIES}


def is_excluded_path(path: str) -> bool:
    path = normalize_path(path)
    for prefix in EXCLUDED_PREFIXES:
        if path == prefix.rstrip("/") or path.startswith(prefix):
            return True
    return False


def paths_matching_family(paths: set[str] | list[str], family: FamilyDef) -> list[str]:
    out = [normalize_path(p) for p in paths if family.pattern.search(normalize_path(p))]
    return sorted({p for p in out if not is_excluded_path(p)})


def touch_counts_from_manifest(manifest) -> dict[str, int]:
    counts = manifest.groupby("changed_path").size()
    return {normalize_path(k): int(v) for k, v in counts.items()}


def select_anchor(
    family: FamilyDef,
    head_files: set[str],
    touch_counts: dict[str, int],
) -> str | None:
    candidates = paths_matching_family(head_files | set(touch_counts), family)
    if not candidates:
        return None

    for pref in family.anchor_priority:
        if pref in candidates:
            return pref

    def rank(path: str) -> tuple[int, int, str]:
        depth = path.count("/")
        at_root = 0 if "/" not in path else 1
        return (at_root, -touch_counts.get(path, 0), depth, path)

    return sorted(candidates, key=rank)[0]
