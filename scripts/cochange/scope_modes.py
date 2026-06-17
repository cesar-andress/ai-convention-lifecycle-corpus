"""Governed-scope modes for co-change synchronization pilots."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from cochange.package_subtree import infer_package_subtree_scope
from cochange.scope import is_excluded_governed_path, normalize_path


class ScopeMode(str, Enum):
    REPO_WIDE = "repo_wide"
    SUBTREE = "subtree"
    CONTENT_REFERENCED = "content_referenced"
    PACKAGE_SUBTREE = "package_subtree"


@dataclass(frozen=True)
class ResolvedScope:
    mode: ScopeMode
    instruction_path: str
    description: str
    governed_paths_head: frozenset[str]
    content_refs_total: int = 0
    content_refs_used: int = 0
    n_package_roots_detected: int = 0
    package_roots_used: frozenset[str] = frozenset()
    package_subtree_status: str = ""

    def path_in_scope(self, changed_path: str) -> bool:
        changed_path = normalize_path(changed_path)
        if changed_path == self.instruction_path:
            return False
        if is_excluded_governed_path(changed_path):
            return False

        if self.mode == ScopeMode.CONTENT_REFERENCED:
            for ref in self.governed_paths_head:
                if ref.endswith("/"):
                    if changed_path.startswith(ref):
                        return True
                elif changed_path == ref:
                    return True
            return False

        if self.mode == ScopeMode.PACKAGE_SUBTREE:
            if self.package_subtree_status.startswith("inconclusive"):
                return False
            prefixes = self.package_roots_used or self.governed_paths_head
            if not prefixes:
                return False
            for prefix in prefixes:
                p = prefix if prefix.endswith("/") else prefix + "/"
                if changed_path.startswith(p) or changed_path == prefix.rstrip("/"):
                    return True
            return False

        if self.mode == ScopeMode.REPO_WIDE:
            return True

        prefix = self._subtree_prefix()
        if prefix == "":
            return True
        return changed_path.startswith(prefix)

    def _subtree_prefix(self) -> str:
        instruction_path = normalize_path(self.instruction_path)
        if "/" not in instruction_path:
            return ""
        return instruction_path.rsplit("/", 1)[0] + "/"


def scope_description(
    mode: ScopeMode,
    instruction_path: str,
    *,
    n_refs_used: int = 0,
    n_refs_total: int = 0,
    package_roots: list[str] | None = None,
    package_status: str = "",
) -> str:
    instruction_path = normalize_path(instruction_path)
    if mode == ScopeMode.REPO_WIDE:
        return "repository-wide (non-excluded paths)"
    if mode == ScopeMode.SUBTREE:
        if "/" not in instruction_path:
            return "subtree=repo root (equivalent to repo-wide for root instruction files)"
        parent = instruction_path.rsplit("/", 1)[0]
        return f"subtree `{parent}/` (non-excluded paths)"
    if mode == ScopeMode.PACKAGE_SUBTREE:
        roots = package_roots or []
        if package_status.startswith("inconclusive"):
            return f"package-subtree ({package_status})"
        if package_status == "fallback_subtree_nested":
            return f"package-subtree fallback to subtree `{roots[0] if roots else '?'}`"
        shown = ", ".join(f"`{r}`" for r in roots[:5])
        if len(roots) > 5:
            shown += f", +{len(roots) - 5} more"
        return f"package-subtree ({shown})"
    return f"content-referenced ({n_refs_used}/{n_refs_total} refs resolved in HEAD)"


def build_resolved_scope(
    mode: ScopeMode,
    instruction_path: str,
    head_files: set[str],
    content_ref_rows: list[dict] | None = None,
) -> ResolvedScope:
    instruction_path = normalize_path(instruction_path)
    content_ref_rows = content_ref_rows or []
    refs_used = [r for r in content_ref_rows if r.get("used_for_scope")]

    if mode == ScopeMode.PACKAGE_SUBTREE:
        prefixes, status, n_detected, roots_list = infer_package_subtree_scope(
            instruction_path, head_files, content_ref_rows
        )
        desc = scope_description(
            mode,
            instruction_path,
            package_roots=roots_list,
            package_status=status,
        )
        return ResolvedScope(
            mode=mode,
            instruction_path=instruction_path,
            description=desc,
            governed_paths_head=frozenset(prefixes),
            content_refs_total=len(content_ref_rows),
            content_refs_used=len(refs_used),
            n_package_roots_detected=n_detected,
            package_roots_used=frozenset(roots_list),
            package_subtree_status=status,
        )

    governed_paths: set[str] = set()
    if mode == ScopeMode.CONTENT_REFERENCED:
        for row in refs_used:
            resolved = normalize_path(str(row.get("resolved_path") or ""))
            if not resolved:
                continue
            if resolved.endswith("/"):
                governed_paths.add(resolved)
            elif resolved in head_files:
                governed_paths.add(resolved)
            elif any(p.startswith(resolved + "/") for p in head_files):
                governed_paths.add(resolved + "/")
            else:
                governed_paths.add(resolved)

    desc = scope_description(
        mode,
        instruction_path,
        n_refs_used=len(refs_used),
        n_refs_total=len(content_ref_rows),
    )
    return ResolvedScope(
        mode=mode,
        instruction_path=instruction_path,
        description=desc,
        governed_paths_head=frozenset(governed_paths),
        content_refs_total=len(content_ref_rows),
        content_refs_used=len(refs_used),
    )


def legacy_path_in_governed_scope(changed_path: str, instruction_path: str) -> bool:
    """Backward-compatible prototype rule (repo-wide for root agent briefs)."""
    from cochange.scope import INSTRUCTION_BASENAMES

    changed_path = normalize_path(changed_path)
    instruction_path = normalize_path(instruction_path)
    if changed_path == instruction_path or is_excluded_governed_path(changed_path):
        return False
    base = instruction_path.rsplit("/", 1)[-1]
    if instruction_path.count("/") == 0 and base in INSTRUCTION_BASENAMES:
        return True
    if "/" in instruction_path:
        subtree = instruction_path.rsplit("/", 1)[0] + "/"
        return changed_path.startswith(subtree)
    parent = instruction_path.rsplit("/", 1)[0]
    if parent:
        return changed_path.startswith(parent + "/")
    return False
