"""Provisional governed-scope rules for co-change synchronization prototypes."""

from __future__ import annotations

from pathlib import PurePosixPath

# Mirrors lifecycle exclusions plus common binary/media extensions (provisional).
EXCLUDED_PREFIXES = (
    ".git/",
    "node_modules/",
    "vendor/",
    "dist/",
    "build/",
    "target/",
    "coverage/",
)

EXCLUDED_BASENAMES = frozenset(
    {
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
    }
)

BINARY_EXTENSIONS = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".svg",
        ".pdf",
        ".zip",
        ".gz",
        ".tar",
        ".tgz",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".mp4",
        ".mp3",
        ".wasm",
        ".bin",
        ".pyc",
        ".class",
        ".jar",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
    }
)

INSTRUCTION_BASENAMES = frozenset(
    {
        "AGENTS.md",
        "CLAUDE.md",
        "SKILL.md",
    }
)


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def is_excluded_governed_path(path: str) -> bool:
    path = normalize_path(path)
    for prefix in EXCLUDED_PREFIXES:
        if path == prefix.rstrip("/") or path.startswith(prefix):
            return True
    base = path.rsplit("/", 1)[-1]
    if base in EXCLUDED_BASENAMES:
        return True
    suffix = PurePosixPath(path).suffix.lower()
    if suffix in BINARY_EXTENSIONS:
        return True
    return False


def instruction_scope_label(instruction_path: str) -> str:
    """Human-readable governed-scope description for reports."""
    instruction_path = normalize_path(instruction_path)
    base = instruction_path.rsplit("/", 1)[-1]
    if instruction_path.count("/") == 0 and base in INSTRUCTION_BASENAMES:
        return "repository-wide (excluding vendor/build/binary paths)"
    parent = instruction_path.rsplit("/", 1)[0] if "/" in instruction_path else ""
    if parent:
        return f"subtree `{parent}/` (excluding vendor/build/binary paths)"
    return "parent-directory subtree (provisional)"


def path_in_governed_scope(changed_path: str, instruction_path: str) -> bool:
    """
    Return True if changed_path is governed by instruction_path under provisional rules.

    See docs/cochange_scope_rules.md for rationale and limitations.
    """
    changed_path = normalize_path(changed_path)
    instruction_path = normalize_path(instruction_path)

    if changed_path == instruction_path:
        return False
    if is_excluded_governed_path(changed_path):
        return False

    base = instruction_path.rsplit("/", 1)[-1]

    # Root-level agent briefs (e.g. CLAUDE.md at repo root).
    if instruction_path.count("/") == 0 and base in INSTRUCTION_BASENAMES:
        return True

    # Nested instruction files: govern sibling paths under the same directory subtree.
    if "/" in instruction_path:
        subtree = instruction_path.rsplit("/", 1)[0] + "/"
        return changed_path.startswith(subtree)

    # Cursor/Windsurf/rules-style paths: parent directory subtree (provisional).
    parent = instruction_path.rsplit("/", 1)[0]
    if parent:
        return changed_path.startswith(parent + "/")

    return False
