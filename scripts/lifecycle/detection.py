"""Lifecycle artifact path classification (AI instructional scope only)."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "protocol" / "lifecycle_v1.yaml"


@lru_cache(maxsize=1)
def load_config(path: str | None = None) -> dict:
    cfg_path = Path(path) if path else DEFAULT_CONFIG
    with cfg_path.open() as f:
        return yaml.safe_load(f)


def normalize_path(p: str) -> str:
    return p.replace("\\", "/").lstrip("./")


def _matches_any(path: str, patterns: list[str]) -> bool:
    return any(re.search(pat, path) for pat in patterns)


def is_excluded(path: str, cfg: dict) -> bool:
    path = normalize_path(path)
    for prefix in cfg.get("exclude_path_prefixes", []):
        if path == prefix.rstrip("/") or path.startswith(prefix):
            return True
    base = path.rsplit("/", 1)[-1]
    if base in cfg.get("exclude_basenames", []):
        return True
    if _matches_any(path, cfg.get("exclude_path_regex", [])):
        return True
    return False


def artifact_type(path: str, cfg: dict | None = None) -> str | None:
    cfg = cfg or load_config()
    path = normalize_path(path)
    if is_excluded(path, cfg):
        return None
    for item in cfg["artifact_patterns"]:
        if re.search(item["regex"], path):
            return item["id"]
    return None


def is_lifecycle_artifact(path: str, cfg: dict | None = None) -> bool:
    return artifact_type(path, cfg) is not None


def is_ci_path(path: str, cfg: dict | None = None) -> bool:
    cfg = cfg or load_config()
    return _matches_any(normalize_path(path), cfg.get("ci_path_regex", []))


def is_bot(author_name: str, author_email: str, cfg: dict | None = None) -> bool:
    cfg = cfg or load_config()
    blob = f"{author_name} {author_email}"
    return re.search(cfg["bot_author_regex"], blob) is not None
