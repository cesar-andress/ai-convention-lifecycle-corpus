#!/usr/bin/env python3
"""Regression checks for repository-relative path normalization."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.git_utils import normalize_repo_relative_path, safe_normalize_repo_relative_path

CASES = [
    ("./.github/workflows/ci.yml", ".github/workflows/ci.yml"),
    (".github/workflows/ci.yml", ".github/workflows/ci.yml"),
    ("docs/CLAUDE.md", "docs/CLAUDE.md"),
    ("./docs/CLAUDE.md", "docs/CLAUDE.md"),
    (".github/copilot-instructions.md", ".github/copilot-instructions.md"),
    ("./.github/copilot-instructions.md", ".github/copilot-instructions.md"),
]

REJECT_CASES = [
    "../weird/path.yml",
]


def main() -> int:
    failed = 0
    for raw, expected in CASES:
        got = normalize_repo_relative_path(raw)
        if got != expected:
            print(f"FAIL: {raw!r} -> {got!r} (expected {expected!r})")
            failed += 1
        else:
            print(f"OK: {raw!r} -> {got!r}")
    for raw in REJECT_CASES:
        try:
            got = normalize_repo_relative_path(raw)
            print(f"FAIL: {raw!r} should be rejected but got {got!r}")
            failed += 1
        except ValueError:
            print(f"OK: {raw!r} rejected")
        if safe_normalize_repo_relative_path(raw) is not None:
            print(f"FAIL: safe_normalize should return None for {raw!r}")
            failed += 1
        else:
            print(f"OK: safe_normalize {raw!r} -> None")
    if failed:
        print(f"{failed} normalization checks failed", file=sys.stderr)
        return 1
    print("All normalization checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
