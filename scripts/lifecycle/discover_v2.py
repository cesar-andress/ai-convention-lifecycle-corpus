#!/usr/bin/env python3
"""Discover repos for adoption-maintenance v2 with mixed seed pools and funnel."""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lifecycle.corpus_paths import configure

ROOT = configure()

from lifecycle.detection import artifact_type, is_lifecycle_artifact, load_config
from lifecycle.git_utils import clone_repo, list_head_files, parse_github_url

DEFAULT_V2 = ROOT / "protocol" / "adoption_maintenance_v2.yaml"
DEFAULT_LC = ROOT / "protocol" / "lifecycle_v1.yaml"


def load_v2(path: Path) -> dict:
    import yaml

    with path.open() as f:
        return yaml.safe_load(f)


def iter_pooled_seeds(v2: dict) -> list[tuple[str, str]]:
    """Return (url, seed_pool) preserving pool order, deduped."""
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for pool, files in v2["discovery"]["seed_pools"].items():
        for rel in files:
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
                out.append((line, pool))
    return out


def discover_v2(
    candidates: list[tuple[str, str]],
    cfg: dict,
    *,
    target_n: int,
    max_candidates: int,
    timeout: int,
    shallow: bool,
    existing_rows: list[dict] | None = None,
    local_repos_dir: Path | None = None,
) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = list(existing_rows or [])
    funnel: list[dict] = []
    seen: set[str] = set()
    if existing_rows:
        for r in existing_rows:
            seen.add(r["repo_id"].lower())
    counts = Counter(
        {
            "candidates_processed": 0,
            "duplicate_skip": 0,
            "parse_fail": 0,
            "clone_fail": 0,
            "no_artifacts": 0,
            "adopted": len(rows),
        }
    )
    pool_adopted: Counter = Counter(r.get("seed_pool", "") for r in rows)

    with tempfile.TemporaryDirectory(prefix="lifecycle-discover-v2-") as tmp:
        tmp_path = Path(tmp)
        for url, pool in candidates:
            if len(rows) >= target_n:
                break
            if counts["candidates_processed"] >= max_candidates:
                break

            parsed = parse_github_url(url)
            if not parsed:
                counts["parse_fail"] += 1
                continue
            owner, repo = parsed
            key = f"{owner}/{repo}".lower()
            if key in seen:
                counts["duplicate_skip"] += 1
                continue
            seen.add(key)
            counts["candidates_processed"] += 1

            local_dir = (local_repos_dir / owner / repo) if local_repos_dir else None
            if local_dir is not None and local_dir.exists() and (local_dir / ".git").exists():
                paths = [p for p in list_head_files(local_dir) if is_lifecycle_artifact(p, cfg)]
            else:
                clone_dir = tmp_path / owner / repo
                if clone_dir.exists():
                    shutil.rmtree(clone_dir)
                if not clone_repo(url, clone_dir, timeout=timeout, shallow=shallow):
                    counts["clone_fail"] += 1
                    print(f"skip clone [{pool}]: {owner}/{repo}", file=sys.stderr)
                    continue
                paths = [p for p in list_head_files(clone_dir) if is_lifecycle_artifact(p, cfg)]

            if not paths:
                counts["no_artifacts"] += 1
                print(f"skip no artifacts [{pool}]: {owner}/{repo}", file=sys.stderr)
                continue

            types = sorted({artifact_type(p, cfg) for p in paths if artifact_type(p, cfg)})
            rows.append(
                {
                    "repo_url": url,
                    "repo_id": f"{owner}/{repo}",
                    "owner": owner,
                    "repo": repo,
                    "seed_pool": pool,
                    "n_artifacts_head": len(paths),
                    "artifact_types_head": "|".join(types),
                }
            )
            counts["adopted"] += 1
            pool_adopted[pool] += 1
            print(f"ok [{pool}]: {owner}/{repo} ({len(paths)})", file=sys.stderr)

    for stage, val in counts.items():
        funnel.append({"stage": stage, "seed_pool": "ALL", "count": val})
    for pool, val in pool_adopted.items():
        funnel.append({"stage": "adopted", "seed_pool": pool, "count": val})

    return rows, funnel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=None)
    parser.add_argument("--max-candidates", type=int, default=None)
    parser.add_argument("--v2-config", type=Path, default=DEFAULT_V2)
    parser.add_argument("--lifecycle-config", type=Path, default=DEFAULT_LC)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--funnel-out", type=Path, default=None)
    parser.add_argument(
        "--append",
        action="store_true",
        help="Keep repos already in --out and discover until target is reached.",
    )
    parser.add_argument(
        "--local-repos-dir",
        type=Path,
        default=ROOT / "data" / "repos",
        help="Use existing clones under owner/repo when present (same HEAD detection).",
    )
    parser.add_argument(
        "--only-seed-files",
        nargs="*",
        default=None,
        help="Restrict discovery to these seed file paths (for expansion runs).",
    )
    args = parser.parse_args()

    v2 = load_v2(args.v2_config)
    cfg = load_config(str(args.lifecycle_config))
    target = args.n or int(v2["scale"]["target_adopted_repos"])
    max_c = args.max_candidates or int(v2["scale"]["max_candidates"])
    timeout = int(v2["discovery"]["clone_timeout_seconds"])
    shallow = bool(v2["discovery"].get("shallow_discover", True))

    out = args.out or ROOT / v2["discovery"]["outputs"]["discovered"]
    existing_rows: list[dict] = []
    if args.append and out.exists():
        existing_rows = list(csv.DictReader(out.open()))

    if args.only_seed_files:
        candidates: list[tuple[str, str]] = []
        seen_urls: set[str] = set()
        for rel in args.only_seed_files:
            path = ROOT / rel
            if not path.exists():
                continue
            pool = "general_oss"
            for pool_name, files in v2["discovery"]["seed_pools"].items():
                if rel in files:
                    pool = pool_name
                    break
            for line in path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key = line.lower().rstrip("/")
                if key in seen_urls:
                    continue
                seen_urls.add(key)
                candidates.append((line, pool))
    else:
        candidates = iter_pooled_seeds(v2)

    rows, funnel = discover_v2(
        candidates,
        cfg,
        target_n=target,
        max_candidates=max_c,
        timeout=timeout,
        shallow=shallow,
        existing_rows=existing_rows,
        local_repos_dir=args.local_repos_dir,
    )

    funnel_out = args.funnel_out or ROOT / v2["discovery"]["outputs"]["funnel"]
    out.parent.mkdir(parents=True, exist_ok=True)
    funnel_out.parent.mkdir(parents=True, exist_ok=True)

    fields = ["repo_url", "repo_id", "owner", "repo", "seed_pool", "n_artifacts_head", "artifact_types_head"]
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    with funnel_out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["stage", "seed_pool", "count"])
        w.writeheader()
        w.writerows(funnel)

    summary = {
        "target_adopted_repos": target,
        "adopted_repos": len(rows),
        "max_candidates": max_c,
        "funnel": {r["stage"]: r["count"] for r in funnel if r["seed_pool"] == "ALL"},
        "adopted_by_pool": {r["seed_pool"]: r["count"] for r in funnel if r["stage"] == "adopted"},
    }
    print(summary)
    print(f"discovered {len(rows)} -> {out}")
    return 0 if len(rows) >= min(target, 1) else 1


if __name__ == "__main__":
    sys.exit(main())
