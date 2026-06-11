# Corpus commit policy

This repository (`ai-convention-lifecycle-corpus`) is the public replication package. **Every change must be committed immediately** after it is made.

## Scope

Applies whenever you add, move, modify, or remove anything inside this repository.

## Requirements

- Commit messages must be in **English**.
- Use conventional, clear messages.
- **One logical change per commit** — do not batch unrelated changes.
- Do **not** commit manuscript files (those belong in `../paper/`).
- Do **not** commit temporary files, caches, logs, cloned repositories (`data/repos/`), or virtual environments (`.venv/`).

## Workflow

Before each commit:

```bash
git status
```

After each commit, record:

- commit hash
- commit message
- files changed

## Recommended message style

- `Initialize public corpus repository`
- `Add adoption-maintenance protocol`
- `Add reproducibility scripts`
- `Add released analysis outputs`
- `Add annotation workflow`
- `Document Zenodo release metadata`
- `Remove legacy exploratory artifacts`
- `Add reproducibility guide`
- `Add dataset description`
- `Add paper-corpus separation audit`

## Repository bootstrap

If the repository is not initialized:

```bash
cd ~/papers/ai-artifact-cochange/ai-convention-lifecycle-corpus
git init
git branch -M main
```
