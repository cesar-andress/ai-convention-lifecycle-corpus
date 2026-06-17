"""Content-reference extraction from instruction files at HEAD (v2)."""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from pathlib import Path

from cochange.scope import normalize_path
from lifecycle.git_utils import list_head_files, run_git

PARSER_VERSION = "v2"

CONFIG_BASENAMES = frozenset(
    {
        "package.json",
        "package-lock.json",
        "pyproject.toml",
        "poetry.lock",
        "requirements.txt",
        "requirements-dev.txt",
        "Cargo.toml",
        "Cargo.lock",
        "pom.xml",
        "Makefile",
        "makefile",
        "tox.ini",
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "go.mod",
        "go.sum",
        "setup.py",
        "setup.cfg",
    }
)

COMMON_TOP_LEVEL_DIRS = frozenset(
    {
        "backend",
        "frontend",
        "packages",
        "services",
        "docs",
        "src",
        "lib",
        "cmd",
        "internal",
        "api",
        "apps",
        "modules",
        "dev",
        "python_modules",
        "examples",
        "pkg",
        "crates",
    }
)

SCOPE_HEADING_KEYWORDS = (
    "scope",
    "repository structure",
    "project structure",
    "architecture",
    "layout",
    "code organization",
    "codebase layout",
    "directory structure",
    "monorepo",
)

NOISE_BACKTICK = frozenset(
    {
        "get",
        "post",
        "put",
        "delete",
        "patch",
        "sh",
        "bash",
        "text",
        "json",
        "yaml",
        "switch",
        "run",
        "run",
        "true",
        "false",
        "none",
        "null",
        "dag",
        "prek",
        "breeze",
    }
)

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
INCLUDE_LINE_RE = re.compile(r"^@?([\w./-]+\.(?:md|mdc|txt|yaml|yml))\s*$", re.I)
HEADING_RE = re.compile(r"^(#{1,4})\s+(.+)$")
EXPLICIT_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_./])([\w.-]+(?:/[\w.*-]+)+/?)(?![A-Za-z0-9_./])"
)
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
COMMON_DIR_RE = re.compile(
    r"(?<![A-Za-z0-9_])(backend|frontend|packages|services|docs|src|lib|cmd|internal|api|apps|modules|dev|python_modules|examples|pkg|crates)(?![A-Za-z0-9_])",
    re.I,
)
MAKE_CMD_RE = re.compile(r"(?i)\bmake\s+([A-Za-z0-9_.-]+)")


@dataclass(frozen=True)
class ExtractedReference:
    reference_type: str
    raw_text: str
    extraction_rule: str
    confidence: str
    resolved_path: str = ""
    exists_in_head: bool = False
    resolution_status: str = "unresolved"

    def to_row(self, repo_id: str, instruction_file: str, *, misguidance_mode: bool = False) -> dict:
        used = self.exists_in_head and self.confidence in {"high", "medium"}
        row = {
            "repo_id": repo_id,
            "instruction_file": instruction_file,
            "reference_type": self.reference_type,
            "raw_reference": self.raw_text,
            "raw_text": self.raw_text,
            "resolved_path": self.resolved_path,
            "exists_in_head": self.exists_in_head,
            "used_for_scope": used,
            "extraction_rule": self.extraction_rule,
            "confidence": self.confidence,
            "parser_version": PARSER_VERSION,
        }
        if misguidance_mode:
            row["extracted_reference"] = self.raw_text
            row["resolution_status"] = self.resolution_status
        return row


def read_instruction_at_head(repo_dir: Path, instruction_path: str) -> str | None:
    proc = run_git(["git", "show", f"HEAD:{instruction_path}"], cwd=repo_dir)
    if proc.returncode != 0 or not proc.stdout:
        return None
    return proc.stdout


def instruction_base_dir(instruction_path: str) -> str:
    instruction_path = normalize_path(instruction_path)
    if "/" not in instruction_path:
        return ""
    return instruction_path.rsplit("/", 1)[0]


def _looks_like_include_pointer(line: str) -> bool:
    line = line.strip()
    if not INCLUDE_LINE_RE.match(line):
        return False
    return line.count("/") <= 3


def load_effective_instruction_text(
    repo_dir: Path,
    instruction_path: str,
    head_files: set[str],
    *,
    misguidance_mode: bool = False,
) -> tuple[str | None, list[ExtractedReference]]:
    """Return merged text and include-directive references (single hop)."""
    instruction_path = normalize_path(instruction_path)
    text = read_instruction_at_head(repo_dir, instruction_path)
    if text is None:
        return None, []

    include_refs: list[ExtractedReference] = []
    stripped = text.strip()
    lines = stripped.splitlines()

    if len(lines) == 1:
        m = INCLUDE_LINE_RE.match(lines[0].strip())
        if m:
            include_path = normalize_path(m.group(1))
            resolved, exists = resolve_reference(include_path, head_files, instruction_path)
            conf = "high" if exists else ("medium" if misguidance_mode else "low")
            include_refs.append(
                _make_extracted_reference(
                    reference_type="include_directive",
                    raw_text=lines[0].strip(),
                    extraction_rule="include_directive",
                    confidence=conf,
                    resolved_path=resolved or include_path,
                    exists_in_head=exists,
                    head_files=head_files,
                    instruction_path=instruction_path,
                    misguidance_mode=misguidance_mode,
                )
            )
            included = read_instruction_at_head(repo_dir, include_path) if exists else None
            if included:
                return included, include_refs
            return text, include_refs

    if lines and (len(lines) == 1 or lines[0].strip().startswith("@") or _looks_like_include_pointer(lines[0])):
        m = INCLUDE_LINE_RE.match(lines[0].strip())
        if m:
            include_path = normalize_path(m.group(1))
            resolved, exists = resolve_reference(include_path, head_files, instruction_path)
            conf = "high" if exists else ("medium" if misguidance_mode else "low")
            include_refs.append(
                _make_extracted_reference(
                    reference_type="include_directive",
                    raw_text=lines[0].strip(),
                    extraction_rule="include_directive",
                    confidence=conf,
                    resolved_path=resolved or include_path,
                    exists_in_head=exists,
                    head_files=head_files,
                    instruction_path=instruction_path,
                    misguidance_mode=misguidance_mode,
                )
            )
            included = read_instruction_at_head(repo_dir, include_path) if exists else None
            if included:
                return lines[0] + "\n\n" + included + "\n\n" + "\n".join(lines[1:]), include_refs

    return text, include_refs


def resolve_reference(
    raw: str,
    head_files: set[str],
    instruction_path: str,
) -> tuple[str | None, bool]:
    raw = normalize_path(raw.strip().strip("\"'<>"))
    if not raw or raw.startswith("http://") or raw.startswith("https://"):
        return None, False
    if raw.startswith("mailto:"):
        return None, False

    base = instruction_base_dir(instruction_path)
    candidates: list[str] = []

    if raw.startswith(("./", "../")) or (base and not raw.startswith("/") and "/" in raw):
        joined = posixpath.normpath(posixpath.join(base, raw) if base else raw)
        candidates.append(joined)
    candidates.append(raw)
    if not raw.endswith("/"):
        candidates.append(raw + "/")

    seen: set[str] = set()
    for cand in candidates:
        cand = normalize_path(cand)
        if cand in seen:
            continue
        seen.add(cand)

        if cand in head_files:
            return cand, True

        dir_prefix = cand if cand.endswith("/") else cand + "/"
        if any(p.startswith(dir_prefix) for p in head_files):
            return cand.rstrip("/") + "/", True

        # basename at repo root
        if "/" not in cand and cand in head_files:
            return cand, True

    return raw, False


def _path_exists_at_head(path: str, head_files: set[str]) -> bool:
    path = normalize_path(path)
    if not path:
        return False
    if path in head_files:
        return True
    dir_prefix = path if path.endswith("/") else path + "/"
    return any(p.startswith(dir_prefix) for p in head_files)


def _intended_reference_paths(raw: str, resolved: str, instruction_path: str) -> list[str]:
    raw_clean = normalize_path(raw.strip().strip("\"'<>").split("#")[0])
    paths: list[str] = []
    if raw_clean:
        paths.append(raw_clean)
    if resolved:
        paths.append(normalize_path(resolved))
    base = instruction_base_dir(instruction_path)
    if raw_clean.startswith(("./", "../")) or (base and raw_clean and "/" in raw_clean):
        joined = posixpath.normpath(posixpath.join(base, raw_clean) if base else raw_clean)
        paths.append(normalize_path(joined))
    deduped: list[str] = []
    for path in paths:
        if path and path not in deduped:
            deduped.append(path)
    return deduped


def compute_resolution_status(
    raw: str,
    resolved: str | None,
    exists_in_head: bool,
    head_files: set[str],
    instruction_path: str,
) -> str:
    if resolved is None or not str(resolved).strip():
        return "unresolved"
    resolved = normalize_path(resolved)
    if exists_in_head:
        return "resolved"
    for candidate in _intended_reference_paths(raw, resolved, instruction_path):
        if _path_exists_at_head(candidate, head_files):
            return "resolved_intended"
    raw_clean = normalize_path(raw.strip().strip("\"'<>").split("#")[0])
    if raw_clean.startswith(".") and not resolved.startswith("."):
        return "partial_resolution"
    if ".github/" in raw_clean and ".github/" not in resolved:
        return "partial_resolution"
    return "not_in_head"


def _misguidance_retain_token(token: str) -> bool:
    if not _is_plausible_path_token(token):
        return False
    if "/" in token or token.startswith("."):
        return True
    base = token.rsplit("/", 1)[-1]
    if base in CONFIG_BASENAMES:
        return True
    if base.lower() in NOISE_BACKTICK and "/" not in token and "." not in base:
        return False
    if base.endswith(
        (".py", ".go", ".md", ".yaml", ".yml", ".json", ".toml", ".rst", ".gni", ".lock", ".js", ".ts")
    ):
        return True
    return len(token) >= 3 and "." in base


def _make_extracted_reference(
    *,
    reference_type: str,
    raw_text: str,
    extraction_rule: str,
    confidence: str,
    resolved_path: str | None,
    exists_in_head: bool,
    head_files: set[str],
    instruction_path: str,
    misguidance_mode: bool,
) -> ExtractedReference:
    resolved = normalize_path(resolved_path or "")
    resolution_status = "unresolved"
    if misguidance_mode:
        resolution_status = compute_resolution_status(
            raw_text,
            resolved or None,
            exists_in_head,
            head_files,
            instruction_path,
        )
    return ExtractedReference(
        reference_type=reference_type,
        raw_text=raw_text,
        extraction_rule=extraction_rule,
        confidence=confidence,
        resolved_path=resolved or normalize_path(raw_text.strip("[]()`").split("#")[0]),
        exists_in_head=exists_in_head,
        resolution_status=resolution_status,
    )


def _is_plausible_path_token(token: str) -> bool:
    token = token.strip()
    if len(token) < 2:
        return False
    if token.lower() in {"e.g.", "i.e.", "etc."}:
        return False
    if "://" in token:
        return False
    if token.startswith("www."):
        return False
    if re.fullmatch(r"[A-Z_]{2,}", token):
        return False
    if token in {"allowlist/blocklist", "whitelist/blacklist", "primary/secondary", "master/slave"}:
        return False
    return True


def _backtick_confidence(token: str, exists: bool, in_scope_section: bool) -> str:
    base = token.rsplit("/", 1)[-1]
    if base in CONFIG_BASENAMES and exists:
        return "high"
    if "/" in token and exists:
        return "high" if in_scope_section else "medium"
    if base in CONFIG_BASENAMES:
        return "medium"
    if exists and ("/" in token or base.endswith((".py", ".go", ".md", ".yaml", ".yml", ".json", ".toml"))):
        return "medium" if in_scope_section else "low"
    if base.lower() in NOISE_BACKTICK:
        return "low"
    if "*" in token or "{" in token:
        return "low"
    return "low"


def _scope_heading(title: str) -> bool:
    t = title.lower().strip("`*_")
    return any(kw in t for kw in SCOPE_HEADING_KEYWORDS)


def _split_sections(text: str) -> list[tuple[str | None, list[str]]]:
    sections: list[tuple[str | None, list[str]]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        hm = HEADING_RE.match(line.strip())
        if hm:
            if current_lines or current_title is not None:
                sections.append((current_title, current_lines))
            current_title = hm.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)
    sections.append((current_title, current_lines))
    return sections


def extract_from_text_block(
    text: str,
    head_files: set[str],
    instruction_path: str,
    *,
    in_scope_section: bool = False,
    section_title: str | None = None,
    misguidance_mode: bool = False,
) -> list[ExtractedReference]:
    refs: list[ExtractedReference] = []
    scope_section = in_scope_section or (section_title is not None and _scope_heading(section_title))

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        for match in MARKDOWN_LINK_RE.finditer(stripped):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            resolved, exists = resolve_reference(target, head_files, instruction_path)
            conf = "high" if exists and scope_section else ("medium" if exists or misguidance_mode else "low")
            refs.append(
                _make_extracted_reference(
                    reference_type="markdown_link",
                    raw_text=match.group(0),
                    extraction_rule="markdown_link",
                    confidence=conf,
                    resolved_path=resolved or target,
                    exists_in_head=exists,
                    head_files=head_files,
                    instruction_path=instruction_path,
                    misguidance_mode=misguidance_mode,
                )
            )

        for match in BACKTICK_RE.finditer(stripped):
            token = match.group(1).strip()
            if not _is_plausible_path_token(token):
                continue
            resolved, exists = resolve_reference(token, head_files, instruction_path)
            conf = _backtick_confidence(token, exists, scope_section)
            if scope_section and exists and conf == "medium":
                conf = "high"
            if conf == "low" and not exists:
                if misguidance_mode and _misguidance_retain_token(token):
                    conf = "medium"
                else:
                    continue
            rule = f"scope_section:code_span" if scope_section and _scope_heading(section_title or "") else "code_span"
            refs.append(
                _make_extracted_reference(
                    reference_type="code_span",
                    raw_text=token,
                    extraction_rule=rule if scope_section and "scope_section" in rule else "code_span",
                    confidence=conf,
                    resolved_path=resolved or token,
                    exists_in_head=exists,
                    head_files=head_files,
                    instruction_path=instruction_path,
                    misguidance_mode=misguidance_mode,
                )
            )

        for match in EXPLICIT_PATH_RE.finditer(stripped):
            token = match.group(1).strip()
            if not _is_plausible_path_token(token):
                continue
            resolved, exists = resolve_reference(token, head_files, instruction_path)
            conf = "high" if exists and ("/" in token or token.endswith("/")) else ("medium" if exists else "low")
            if conf == "low":
                if misguidance_mode and _misguidance_retain_token(token):
                    conf = "medium"
                else:
                    continue
            refs.append(
                _make_extracted_reference(
                    reference_type="explicit_path",
                    raw_text=token,
                    extraction_rule="explicit_path",
                    confidence=conf,
                    resolved_path=resolved or token,
                    exists_in_head=exists,
                    head_files=head_files,
                    instruction_path=instruction_path,
                    misguidance_mode=misguidance_mode,
                )
            )

        for match in MAKE_CMD_RE.finditer(stripped):
            if "Makefile" in head_files or "makefile" in head_files:
                mk = "Makefile" if "Makefile" in head_files else "makefile"
                refs.append(
                    _make_extracted_reference(
                        reference_type="command",
                        raw_text=match.group(0),
                        extraction_rule="make_command_to_makefile",
                        confidence="medium",
                        resolved_path=mk,
                        exists_in_head=True,
                        head_files=head_files,
                        instruction_path=instruction_path,
                        misguidance_mode=misguidance_mode,
                    )
                )
            elif misguidance_mode:
                refs.append(
                    _make_extracted_reference(
                        reference_type="command",
                        raw_text=match.group(0),
                        extraction_rule="make_command_to_makefile",
                        confidence="medium",
                        resolved_path="Makefile",
                        exists_in_head=False,
                        head_files=head_files,
                        instruction_path=instruction_path,
                        misguidance_mode=misguidance_mode,
                    )
                )

        for match in COMMON_DIR_RE.finditer(stripped):
            name = match.group(1).lower()
            canonical = name
            for d in COMMON_TOP_LEVEL_DIRS:
                if d.lower() == name:
                    canonical = d
                    break
            resolved, exists = resolve_reference(canonical, head_files, instruction_path)
            if not exists:
                resolved, exists = resolve_reference(canonical + "/", head_files, instruction_path)
            conf = "medium" if exists else "low"
            if conf == "low" and not misguidance_mode:
                continue
            if conf == "low":
                conf = "medium"
            refs.append(
                _make_extracted_reference(
                    reference_type="directory_mention",
                    raw_text=match.group(0),
                    extraction_rule="common_directory_name",
                    confidence=conf,
                    resolved_path=resolved or canonical,
                    exists_in_head=exists,
                    head_files=head_files,
                    instruction_path=instruction_path,
                    misguidance_mode=misguidance_mode,
                )
            )

    for basename in CONFIG_BASENAMES:
        if re.search(rf"(?<![A-Za-z0-9_.-]){re.escape(basename)}(?![A-Za-z0-9_.-])", text):
            resolved, exists = resolve_reference(basename, head_files, instruction_path)
            if exists or misguidance_mode:
                refs.append(
                    _make_extracted_reference(
                        reference_type="config_file",
                        raw_text=basename,
                        extraction_rule="known_config_filename",
                        confidence="high" if exists else "medium",
                        resolved_path=resolved or basename,
                        exists_in_head=exists,
                        head_files=head_files,
                        instruction_path=instruction_path,
                        misguidance_mode=misguidance_mode,
                    )
                )

    return refs


def dedupe_refs(refs: list[ExtractedReference]) -> list[ExtractedReference]:
    seen: set[tuple[str, str, str]] = set()
    out: list[ExtractedReference] = []
    for ref in refs:
        key = (ref.extraction_rule, ref.raw_text, ref.resolved_path)
        if key in seen:
            continue
        seen.add(key)
        out.append(ref)
    return out


def extract_content_references(
    repo_id: str,
    repo_dir: Path,
    instruction_path: str,
    head_files: set[str] | None = None,
    *,
    misguidance_mode: bool = False,
) -> list[dict]:
    instruction_path = normalize_path(instruction_path)
    head_files = set(head_files or list_head_files(repo_dir))

    text, include_refs = load_effective_instruction_text(
        repo_dir,
        instruction_path,
        head_files,
        misguidance_mode=misguidance_mode,
    )
    if text is None:
        return [r.to_row(repo_id, instruction_path, misguidance_mode=misguidance_mode) for r in include_refs]

    all_refs: list[ExtractedReference] = list(include_refs)

    sections = _split_sections(text)
    if len(sections) == 1 and sections[0][0] is None:
        all_refs.extend(
            extract_from_text_block(
                text,
                head_files,
                instruction_path,
                in_scope_section=False,
                misguidance_mode=misguidance_mode,
            )
        )
    else:
        for title, lines in sections:
            block = "\n".join(lines)
            in_scope = title is not None and _scope_heading(title)
            all_refs.extend(
                extract_from_text_block(
                    block,
                    head_files,
                    instruction_path,
                    in_scope_section=in_scope,
                    section_title=title,
                    misguidance_mode=misguidance_mode,
                )
            )

    return [
        r.to_row(repo_id, instruction_path, misguidance_mode=misguidance_mode)
        for r in dedupe_refs(all_refs)
    ]


# Backward-compatible alias for tests/comparison imports
extract_content_references_v2 = extract_content_references
