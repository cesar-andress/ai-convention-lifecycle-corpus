"""Resolve corpus root and configure imports for scripts/lifecycle."""

from __future__ import annotations

import sys
from pathlib import Path

_PKG = Path(__file__).resolve().parent
SCRIPTS_DIR = _PKG.parent
CORPUS_ROOT = SCRIPTS_DIR.parent


def configure() -> Path:
    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    return CORPUS_ROOT
