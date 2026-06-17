# Public release audit

**Repository:** `ai-convention-lifecycle-corpus`  
**Audit date:** 2026-06-10  
**Scope:** Accidental leakage of legacy experiments, manuscript assets, local environment files, or non-reproducible artifacts.

---

## 1. Audit procedure

Commands run from the corpus root:

```bash
find . -type l -ls
find . \( -name '__pycache__' -o -name '*.pyc' -o -name '.venv' -o -name '*.log' \
  -o -name '.ipynb_checkpoints' -o -path './data/repos/*' \)
git ls-files
rg -i 'cochange|co-change|VDG|A10|workflow predictor|prompt-provenance|/home/|ai-artifact-cochange' .
rg -i 'reviewer|response.to.review|\.tex|main\.pdf|submission_readiness' .
glob: **/*.{tex,pdf,ipynb}
make verify-headline
```

---

## 2. Summary verdict

| Category | Status |
|----------|--------|
| Symlinks | **PASS** — none found |
| Absolute local paths in data/code | **PASS** — none in tracked files |
| Manuscript files (`.tex`, PDF, review notes) | **PASS** — none tracked |
| Legacy project artifacts (co-change, VDG, A10, etc.) | **PASS** — not present in release tree |
| Temporary / environment artifacts | **PASS** — not tracked; working-tree cache cleaned |
| Git clone directory (`data/repos/`) | **PASS** — absent and gitignored |
| Reproducibility integrity | **PASS** — `make verify-headline` OK |

**Overall:** The public repository is clean for Zenodo release. No removals from git history were required beyond pre-audit working-tree hygiene.

---

## 3. Detailed findings

### 3.1 Symbolic links

| Finding | Action |
|---------|--------|
| `find . -type l -ls` returned **no output** | None. Prior symlink `lifecycle → scripts/lifecycle` was removed in commit `955a7a0`. |

### 3.2 Absolute local paths

| Finding | Action |
|---------|--------|
| No `/home/`, `/Users/`, or username paths in tracked JSON, CSV, YAML, Python, or seed files | None |
| Relative sibling references to `../paper/` in `README.md` and audit docs | **Retained** — documents that the manuscript lives outside the deposit; not a filesystem dependency |

### 3.3 Abandoned / parallel project references

Searched terms: `cochange`, `co-change`, `VDG`, `A10`, `workflow predictor`, `prompt-provenance-framework`, `v4/`, `stratified_validation`.

| Match location | Interpretation | Action |
|----------------|----------------|--------|
| `protocol/lifecycle_v1.yaml` comment: "no co-change study" | Scope boundary for artifact detection | **Retained** — clarifies what this corpus excludes |
| `docs/legacy_removal_log.md`, `docs/repository_migration.md`, `docs/separation_audit.md` | Documentation of excluded internal work | **Retained** — audit trail only; no legacy code or data shipped |
| `seeds/seeds_stratified.txt`, `seeds/seeds_stratified.txt` path in protocol | **Final v2 seed pool** (`ai_adopter`), not the abandoned `stratified_validation.yaml` experiment | **Retained** — required by `protocol/adoption_maintenance_v2.yaml` |
| "stratified" in annotation / analysis docs | Statistical stratification (20 dormant + 20 active validation sample) | **Retained** — part of final study protocol |
| `exclude_top_prompt_repos` in v2 protocol and JSON | Sensitivity analysis for high–prompt-count repositories in **this** study | **Retained** — not the prompt-provenance-framework project |
| No matches for VDG, A10, workflow predictor, prompt-provenance in tracked content | — | — |

### 3.4 Manuscript and submission material

| Asset type | Tracked count | Action |
|------------|---------------|--------|
| `.tex` | 0 | — |
| `.pdf` | 0 | — |
| `.ipynb` | 0 | — |
| Reviewer response drafts | 0 | — |
| Review / writing notes | 0 | — |
| `submission_readiness`, `claims_allowed`, `paper_title` in outputs | 0 | Removed in prior corpus cleanup (commit `223db40`) |

`docs/separation_audit.md` **describes** manuscript paths under `../paper/` for boundary documentation only; those files are not in this repository.

### 3.5 Temporary logs, caches, clones, virtual environments

| Finding | Tracked in git? | Action |
|---------|-----------------|--------|
| `scripts/lifecycle/__pycache__/` (12 `.pyc` files) | No (gitignored) | **Removed from working tree** before this audit |
| `.venv/` | No (gitignored) | Absent |
| `data/repos/` | No (gitignored) | Absent |
| `*.log` | No | Absent |
| `.ipynb_checkpoints/` | No | Absent; added to `.gitignore` as precaution |

### 3.6 Tracked release inventory (53 files)

All tracked paths belong to the final **AI Convention Lifecycle Corpus v2.0.0** replication package:

- `protocol/` (3 YAML)
- `scripts/lifecycle/` (11 Python modules)
- `data/lifecycle/` (8 aggregate files)
- `results/lifecycle/` (8 v2 outputs)
- `annotation/annotation_sheet.csv`
- `seeds/` (7 URL lists)
- `docs/`, `metadata/`, `zenodo/`, root README, LICENSE, CITATION.cff, Makefile, requirements.txt

No legacy v1 results, pilot scripts, or parallel-study protocols are tracked.

---

## 4. Actions taken in this audit

1. Deleted working-tree `__pycache__/` directories (not part of git history).
2. Added `.ipynb_checkpoints/` to `.gitignore`.
3. Created this audit document.
4. Re-ran `make verify-headline` — **OK: n_repos=209 artifact_gap= 0.56**.

---

## 5. Post-audit verification

```bash
$ find . -type l -ls
# (no output)

$ find . -name '__pycache__' -o -name '*.pyc'
# (no output after cleanup)

$ git ls-files | wc -l
53

$ make verify-headline
OK: n_repos=209 artifact_gap= 0.56
```

---

## 6. Maintainer checklist (before Zenodo upload)

- [ ] Confirm `data/repos/` is not populated locally before `git add -A`
- [ ] Run `make clean` and verify no `__pycache__` before tagging a release
- [x] Replace `PLACEHOLDER` DOI and URLs in `CITATION.cff` and `metadata/zenodo.json` (`10.5281/zenodo.20729490`)
- [ ] Upload from a fresh clone or `git archive` to avoid untracked local files

---

## 7. Related documents

- `docs/separation_audit.md` — paper vs. corpus boundary
- `docs/legacy_removal_log.md` — v1 pilot assets removed from public tree
- `docs/commit_policy.md` — required commit workflow for corpus changes
