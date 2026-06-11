#!/usr/bin/env python3
"""Run instruction-lifecycle pilot pipeline end-to-end."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=None, help="discover target N (passed to discover.py)")
    args, _ = parser.parse_known_args()

    py = sys.executable
    env = {**dict(__import__("os").environ), "PYTHONPATH": str(ROOT)}
    discover_cmd = [py, str(ROOT / "lifecycle" / "discover.py")]
    if args.n is not None:
        discover_cmd.extend(["-n", str(args.n)])

    steps = [
        discover_cmd,
        [py, str(ROOT / "lifecycle" / "extract_history.py")],
        [py, str(ROOT / "lifecycle" / "build_dataset.py")],
        [py, str(ROOT / "lifecycle" / "analyze.py")],
    ]
    for cmd in steps:
        proc = subprocess.run(cmd, cwd=ROOT, env=env)
        if proc.returncode != 0:
            print(f"failed at {' '.join(cmd)}", file=sys.stderr)
            return proc.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
