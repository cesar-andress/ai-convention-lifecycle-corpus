#!/usr/bin/env python3
"""Scale to 200 repos and run adoption-maintenance v2 pipeline."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.corpus_paths import CORPUS_ROOT, SCRIPTS_DIR

ROOT = CORPUS_ROOT
LIFECYCLE = SCRIPTS_DIR / "lifecycle"
DISCOVERED_V2 = ROOT / "data" / "lifecycle" / "discovered_v2.csv"
EXTRACT_META = ROOT / "data" / "lifecycle" / "extract_meta.json"
ARTIFACTS_META = ROOT / "data" / "lifecycle" / "artifacts_build_meta.json"


def run(cmd: list[str]) -> int:
    env = {**dict(__import__("os").environ), "PYTHONPATH": str(SCRIPTS_DIR)}
    return subprocess.run(cmd, cwd=ROOT, env=env).returncode


def main() -> int:
    py = sys.executable
    v2 = ROOT / "protocol" / "adoption_maintenance_v2.yaml"

    steps = [
        [
            py,
            str(LIFECYCLE / "discover_v2.py"),
            "--append",
            "--only-seed-files",
            "seeds/wave2_s0_candidates.txt",
            "seeds/lifecycle_cached_clones.txt",
            "seeds/lifecycle_gh_repo_search.txt",
            "--local-repos-dir",
            str(ROOT / "data" / "repos"),
        ],
        [
            py,
            str(LIFECYCLE / "extract_history.py"),
            "--discovered",
            str(DISCOVERED_V2),
            "--resume",
            "--attrition-out",
            str(ROOT / "results" / "lifecycle" / "extract_attrition_v2.csv"),
            "--meta-out",
            str(EXTRACT_META),
        ],
        [py, str(LIFECYCLE / "build_dataset.py")],
        [
            py,
            str(LIFECYCLE / "adoption_maintenance_v2.py"),
            "--discovered",
            str(DISCOVERED_V2),
        ],
    ]
    for cmd in steps:
        if run(cmd) != 0:
            print(f"failed: {' '.join(cmd)}", file=sys.stderr)
            return 1

    if not EXTRACT_META.exists() or not ARTIFACTS_META.exists():
        print("missing extract/build meta after pipeline", file=sys.stderr)
        return 1

    extract_meta = json.loads(EXTRACT_META.read_text())
    build_meta = json.loads(ARTIFACTS_META.read_text())
    n_disc = extract_meta.get("n_discovered")
    n_touch = extract_meta.get("n_repos_in_touch_history")
    n_art_repos = build_meta.get("n_repos")
    print(f"scale check: discovered={n_disc} touch_repos={n_touch} artifact_repos={n_art_repos}")

    summary_path = ROOT / "results" / "lifecycle" / "adoption_maintenance_v2.json"
    if summary_path.exists():
        s = json.loads(summary_path.read_text())
        print("reproduction_checks:", s.get("reproduction_checks"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
