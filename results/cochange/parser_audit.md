# Parser audit — content-referenced scope extraction (v1)

**Audited file:** `scripts/cochange/content_refs.py` (pilot run, 2026-06)  
**Purpose:** Document why v1 extraction under-resolved references and left several pilot repositories with zero usable content-referenced scope.

---

## 1. Extraction rules currently implemented (v1)

| Rule ID | Mechanism | `extraction_rule` value | Notes |
|---------|-----------|-------------------------|-------|
| R1 | Regex on each non-empty, non-`#` line | `npm_run`, `make_target`, `pytest`, `cargo_go_test` | Commands recorded; only mapped to scope if resolved path basename is in `COMMAND_MAPPABLE_FILES` |
| R2 | Backtick regex `` `([^`\n]+)` `` | `backtick` | Captures **all** backtick spans, including `GET`, `switch`, `cheat`, globs |
| R3 | Inline slash token `\w+/\w*` | `inline_slash_token` | Catches URLs (`claude.ai/code`), metaphors (`allowlist/blocklist`), relative paths without resolution |
| R4 | Filename + extension regex | `filename_ext` | Requires extension match on same line |
| R5 | `.github/workflows/...` regex | `github_workflows` | Workflow path prefix |
| R6 | Trailing-slash token `\w+/` | `trailing_slash_token` | Directory-like tokens; used for scope if resolves under HEAD |
| R7 | Substring search for known root filenames in full text | `known_config_filename` | `package.json`, `Makefile`, `pyproject.toml`, `Dockerfile`, etc. — only if **exact basename** appears in file text **and** exists at repo root in HEAD |

**Resolution (v1):** `_resolve_reference(raw, head_files)` — exact file match, else prefix match if any HEAD path starts with `candidate/`. No resolution relative to instruction file directory. No following of `@include` pointers.

**Scope use (v1):** `used_for_scope = exists_in_head` for path-like types; commands only if mapped to config file at repo root.

---

## 2. Precision-oriented assumptions (v1)

1. **Line-at-a-time scanning** — skips block context (fenced code blocks, scope sections, markdown structure).
2. **HEAD existence required** — references that resolve only after joining with instruction directory (`./internal/...`, `../shared`) often fail.
3. **Commands are not scope** unless they map to a root config file — `make test` does not expand to `Makefile` unless separately extracted via R7.
4. **No confidence tiers** — any resolving `trailing_slash_token` is treated equally; noisy tokens that resolve by accident are included.
5. **No `@file` include expansion** — pointer-only instruction files contribute almost no text.
6. **No markdown link parsing** — `[ADR](dev/breeze/doc/...)` ignored.
7. **Comment-line skip** — lines starting with `#` skip markdown headings (`## Architecture`), losing structured scope hints.

---

## 3. Pilot outcomes (v1)

From `results/cochange/pilot/scope_sensitivity_metrics.csv` (15 instruction-file pairs):

| repo | instruction | refs total | refs used | content sync@30 |
|------|-------------|-----------|-----------|-----------------|
| cheat/cheat | CLAUDE.md | 39 | 1 | 17.1% |
| electron/electron | CLAUDE.md | 125 | 11 | 2.8% |
| dagster-io/dagster | CLAUDE.md | 68 | 6 | 4.6% |
| prefecthq/prefect | AGENTS.md | 110 | 16 | 10.9% |
| payloadcms/payload | CLAUDE.md | 222 | 6 | 12.6% |
| **apache/airflow** | **CLAUDE.md** | **1** | **0** | **n/a** |
| **apache/airflow** | **_shared/AGENTS.md** | **6** | **0** | **n/a** |
| **grafana/grafana** | **CLAUDE.md** | **1** | **0** | **n/a** |
| BerriAI/litellm | mcp_server/CLAUDE.md | 4 | 0 | n/a |

**Zero usable references (content scope empty):** 4 instruction-file pairs across 2 repositories (airflow ×2, grafana CLAUDE.md, litellm nested CLAUDE.md).

---

## 4. Root causes for zero usable references

### 4.1 Pointer-only instruction files (`@AGENTS.md`)

- **grafana/grafana `CLAUDE.md`** — entire file is `@AGENTS.md` (1 line). v1 does not follow the include; only 1 spurious ref extracted.
- **apache/airflow `CLAUDE.md`** — starts with `@AGENTS.md`; body not parsed from included AGENTS content in v1 counter (only 1 ref row).

### 4.2 Relative paths not anchored to instruction file

- **airflow `_shared/AGENTS.md`** — token `../../../../shared` resolves incorrectly; `../` fragments create false directory tokens; `prek` in backticks does not map to scope.

### 4.3 Commands not linked to config files

- **cheat/cheat** — many `make *` commands; `Makefile` not linked from `make test` (only explicit substring search). Missed `cmd/cheat/` from heading `` `cmd/cheat/` `` (backtick path with slash partially caught but `cmd/cheat/` not as directory token at repo root).

### 4.4 Markdown structure ignored

- Architecture / command sections list packages (`cmd/cheat/`, `internal/config`) in headings and prose — v1 does not treat section context as higher-trust scope signal.

### 4.5 Noise filtering too weak / resolution too strict (dual failure)

- Weak filtering: metaphors like `allowlist/blocklist` extracted (grafana docs/AGENTS.md).
- Strict resolution: valid relative paths (`dev/breeze/...` from markdown links in airflow CLAUDE body) never extracted because links not parsed.

---

## 5. Implications for v2

Priority fixes (validity over recall):

1. Expand **`@include` / `@path` pointer** to effective instruction text (single hop).
2. Parse **markdown links** and **explicit backtick paths** with noise denylist.
3. Extract from **scope-related headings** with elevated confidence.
4. Resolve paths **relative to instruction file directory**.
5. Map **`make` targets** to `Makefile` when present (medium confidence).
6. Introduce **confidence tiers**; use only **high/medium** for `used_for_scope`.
7. Recognize **common directory names** only when they exist as top-level directories in HEAD.

---

## 7. v2 follow-up (same pilot sample)

After implementing `content_refs.py` v2 (include directives, markdown links, scope sections, relative resolution, confidence tiers), the same 8-repository pilot yielded:

| Metric | v1 | v2 |
|--------|----|----|
| Instruction-file pairs with usable content scope | 11/15 | **14/15** |
| Total refs used for scope (sum) | 53 | **291** |
| Pairs with zero usable refs | 4 | **1** (`litellm/.../CLAUDE.md`) |

See `results/cochange/pilot/scope_parser_v1_v2_comparison.csv` and `results/cochange/parser_audit.md` §1 for v1 baseline.

