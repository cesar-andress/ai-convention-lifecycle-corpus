# Co-change scope rules (provisional)

Design note for the synchronization feasibility prototype (`scripts/cochange/`).

**Status:** provisional — intended for sensitivity analysis before any cross-family paper claims.

---

## 1. Purpose

For an AI instruction file (e.g. `CLAUDE.md`), we need a rule that maps each commit’s changed paths to:

1. **Governed-code changes** — paths the instruction is assumed to govern.
2. **Instruction updates** — commits that modify the instruction file itself.

These rules underpin the synchronization metric:

> A governed-code event is *synchronized* if the instruction file is updated in the same commit or within *W* days afterward.

---

## 2b. Scope sensitivity modes (pilot)

The scope-sensitivity pilot evaluates each instruction file under four modes:

| Mode | ID | Rule |
|------|-----|------|
| **A — repo-wide** | `repo_wide` | All non-excluded paths in the repository. |
| **B — subtree** | `subtree` | Paths under the instruction file’s parent directory; for root instruction files this equals repo-wide in the current pilot. |
| **C — content-referenced** | `content_referenced` | Only paths referenced in instruction file at HEAD (parser v2; high/medium confidence). |
| **D — package-subtree** | `package_subtree` | Monorepo package roots inferred from manifest indicators + content refs; see `scripts/cochange/package_subtree.py`. |

Outputs: `results/cochange/pilot/scope_sensitivity_v3.csv` (includes mode D).

---

## 2. Provisional scope rules

### 2.1 Root-level instruction file (e.g. `CLAUDE.md`)

- **Scope:** the entire repository.
- **Interpretation:** the file is treated as a project-wide agent brief.
- **Exclusions:** governed-path test rejects obvious non-code trees and generic docs (see §3).

### 2.2 Nested instruction file (e.g. `docs/CLAUDE.md`)

- **Scope:** the directory subtree rooted at the instruction’s parent directory (`docs/` in this example).
- **Interpretation:** localized guidance for that subtree only.
- The instruction file itself is not counted as a governed-code path (instruction updates are tracked separately).

### 2.3 Cursor / Windsurf / rules files (future)

- **Scope (provisional):** parent directory subtree of the rules file, unless a rule-specific scope is parsed later from file content.
- **Not evaluated in the dagster prototype.**

### 2.4 Prompt libraries and multi-file trees (future)

- Scope may require content parsing or explicit path patterns.
- **Out of scope for the dagster prototype.**

---

## 3. Excluded governed paths

A changed path is **never** treated as governed code if it matches:

| Category | Patterns |
|----------|----------|
| Vendor / build trees | `.git/`, `node_modules/`, `vendor/`, `dist/`, `build/`, `target/`, `coverage/` |
| Generic documentation basenames | `README.md`, `CHANGELOG.md`, `LICENSE`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md` |
| Binary / media extensions (provisional) | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.ico`, `.svg`, `.pdf`, `.zip`, `.gz`, `.tar`, `.woff`, `.woff2`, `.ttf`, `.mp4`, `.mp3`, `.wasm`, `.pyc`, … |

These mirror the lifecycle corpus exclusions where applicable, plus a provisional binary-extension filter.

---

## 4. Event definitions (prototype)

| Term | Definition |
|------|------------|
| **Changed-file row** | One `(commit, path, status)` tuple from `git log --name-status`. |
| **Instruction update** | Commit that modifies the instruction path (any non-delete status on that path, or `D` if treating deletion as update — prototype uses modify/add/rename/copy). |
| **Governed-code event** | Commit that changes ≥1 governed path under the instruction scope **and** does **not** change *only* the instruction file (i.e. at least one other governed path, or instruction + other paths). |
| **Synchronized (window *W*)** | Governed-code event at time *t* such that an instruction update occurs in the same commit or with author date in (*t*, *t*+*W*]. |
| **Synchronization rate** | `# synchronized governed-code events / # governed-code events`. |

**Same-commit updates:** *W*=0 includes instruction changes in the same commit as the governed-code event.

---

## 5. Known ambiguities (dagster and beyond)

1. **Root `CLAUDE.md` vs nested copies** — multiple instruction files may overlap in scope; prototype analyzes each file independently.
2. **Monorepo packages** — root brief may over- or under-attribute package-local changes.
3. **Generated / vendored code** — excluded by prefix rules but may leave residual false positives.
4. **Merge commits** — prototype uses `--no-merges` for cleaner attribution (may drop valid co-changes).
5. **Rename detection** — `--no-renames` treats renames as delete+add pairs; scope attribution follows resulting paths.
6. **Semantic governance** — path rules do not read instruction content; a file may claim scope the rules do not capture.

---

## 6. Sensitivity analyses (future)

Before cross-family claims, vary:

- subtree vs repository-wide for nested files;
- inclusion of merge commits;
- exclusion sets (binary extensions, docs basenames);
- *W* ∈ {0, 7, 14, 30, 90} days;
- instruction file discovery (HEAD-only vs full history).

---

## 7. Implementation reference

- Scope logic: `scripts/cochange/scope.py`
- Changed-file extraction: `scripts/cochange/prototype_changed_files.py`
- Sync metric: `scripts/cochange/prototype_sync_metric.py`
