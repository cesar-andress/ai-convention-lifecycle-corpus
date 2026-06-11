#!/usr/bin/env python3
"""Discover repositories containing at least one lifecycle instructional artifact."""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lifecycle.detection import artifact_type, is_lifecycle_artifact, load_config
from lifecycle.git_utils import clone_repo, list_head_files, parse_github_url

DEFAULT_CONFIG = ROOT / "protocol" / "lifecycle_v1.yaml"


def iter_seed_urls(cfg: dict) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for rel in cfg["discovery"]["seeds"]:
        path = ROOT / rel
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key = line.lower().rstrip("/")
            if key in seen:
                continue
            seen.add(key)
            urls.append(line)
    return urls


def discover(
    seed_urls: list[str],
    cfg: dict,
    target_n: int,
    timeout: int,
) -> list[dict]:
    shallow = cfg["discovery"].get("shallow_discover", True)
    rows: list[dict] = []
    seen: set[str] = set()

    with tempfile.TemporaryDirectory(prefix="lifecycle-discover-") as tmp:
        tmp_path = Path(tmp)
        for seed in seed_urls:
            if len(rows) >= target_n:
                break
            parsed = parse_github_url(seed)
            if not parsed:
                continue
            owner, repo = parsed
            key = f"{owner}/{repo}".lower()
            if key in seen:
                continue
            seen.add(key)

            clone_dir = tmp_path / owner / repo
            if clone_dir.exists():
                shutil.rmtree(clone_dir)
            if not clone_repo(seed, clone_dir, timeout=timeout, shallow=shallow):
                print(f"skip clone: {owner}/{repo}", file=sys.stderr)
                continue

            artifact_paths = [p for p in list_head_files(clone_dir) if is_lifecycle_artifact(p, cfg)]
            if not artifact_paths:
                print(f"skip no artifacts: {owner}/{repo}", file=sys.stderr)
                continue

            types = sorted({artifact_type(p, cfg) for p in artifact_paths})
            rows.append(
                {
                    "repo_url": seed,
                    "repo_id": f"{owner}/{repo}",
                    "owner": owner,
                    "repo": repo,
                    "n_artifacts_head": len(artifact_paths),
                    "artifact_types_head": "|".join(t for t in types if t),
                }
            )
            print(f"ok: {owner}/{repo} ({len(artifact_paths)} artifacts)", file=sys.stderr)

    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=None, help="target repo count (default: protocol pilot_n)")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--timeout", type=int, default=None)
    args = parser.parse_args()

    cfg = load_config(str(args.config))
    target_n = args.n if args.n is not None else int(cfg["discovery"]["pilot_n"])
    timeout = args.timeout if args.timeout is not None else int(cfg["discovery"]["clone_timeout_seconds"])
    out = args.out or ROOT / cfg["outputs"]["discovered"]

    rows = discover(iter_seed_urls(cfg), cfg, target_n, timeout)

    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["repo_url", "repo_id", "owner", "repo", "n_artifacts_head", "artifact_types_head"]
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"discovered {len(rows)} repos -> {out}")
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
