# How to cite this corpus

Use these instructions when you reuse **data**, **code**, or **headline statistics** from the **AI Convention Lifecycle Corpus**. You do **not** need the companion MSR paper to cite this replication package.

| What you used | Cite |
|---------------|------|
| Bundled Parquet/CSV/JSON, seeds, or headline numbers | **Zenodo archive** (preferred) |
| Pipeline scripts or `Makefile` targets only | **GitHub repository** + version tag |
| A specific frozen release | **Dataset version** (`v2.0.0`) in addition to Zenodo DOI |

Machine-readable metadata: [`CITATION.cff`](../CITATION.cff) at the repository root.

---

## 1. Zenodo archive (preferred)

The Zenodo record is the **canonical, citable archive** for the bundled datasets and replication materials.

| Field | Value |
|-------|-------|
| Title | AI Convention Lifecycle Corpus v2.0.0 — Expanded 209-Repository Dataset and Adoption–Maintenance Framework |
| Version | 2.0.0 |
| DOI | `10.5281/zenodo.20637986` |
| URL | `https://doi.org/10.5281/zenodo.20637986` |

### BibTeX (dataset entry)

```bibtex
@dataset{ai_convention_lifecycle_corpus_v2,
  author       = {Andr{\'e}s, C\'esar and Moncunilla, David Mart{\'i}n},
  title        = {{AI Convention Lifecycle Corpus v2.0.0 --- Expanded 209-Repository Dataset and Adoption--Maintenance Framework}},
  year         = {2026},
  publisher    = {Zenodo},
  version      = {2.0.0},
  doi          = {10.5281/zenodo.20637986},
  url          = {https://doi.org/10.5281/zenodo.20637986}
}
```

### Plain text (APA-style)

> Andrés, C., & Moncunilla, D. M. (2026). *AI Convention Lifecycle Corpus v2.0.0 — Expanded 209-Repository Dataset and Adoption–Maintenance Framework* (Version 2.0.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.20637986

### Markdown link

```markdown
[AI Convention Lifecycle Corpus v2.0.0](https://doi.org/10.5281/zenodo.20637986)
```

---

## 2. GitHub repository

Cite the **GitHub repository** when you refer to the **live source tree**, development history, or code without pinning to a Zenodo snapshot—for example, when describing the pipeline implementation or opening an issue.

| Field | Value |
|-------|-------|
| Repository | `https://github.com/cesar-andress/ai-convention-lifecycle-corpus` |
| Default branch | `main` |

### BibTeX (software entry)

```bibtex
@software{ai_convention_lifecycle_corpus_github,
  author       = {Andr{\'e}s, C\'esar and Moncunilla, David Mart{\'i}n},
  title        = {{AI Convention Lifecycle Corpus}},
  year         = {2026},
  url          = {https://github.com/cesar-andress/ai-convention-lifecycle-corpus},
  version      = {2.0.0},
  note         = {Mining pipeline and replication materials for the AI Convention Lifecycle Corpus}
}
```

### Plain text

> Andrés, C., & Moncunilla, D. M. (2026). *AI Convention Lifecycle Corpus* (Version 2.0.0) [Software]. GitHub. https://github.com/cesar-andress/ai-convention-lifecycle-corpus

**Recommendation:** For reproducible research, prefer the **Zenodo DOI** (§1) for data and results. Use GitHub when the citation target is the codebase itself.

---

## 3. Dataset version

Always name the **version tag** when you report numbers from this corpus so readers can match your tables to the frozen bundle.

| Version | Cohort | Notes |
|---------|--------|-------|
| **v2.0.0** | 220 discovered / 209 analyzed repos | Current headline release; primary window *T* = 180 days |

### BibTeX (version-specific dataset entry)

Use this when you need an explicit version string in the citation key or bibliography:

```bibtex
@dataset{ai_convention_lifecycle_corpus_v2_0_0,
  author       = {Andr{\'e}s, C\'esar and Moncunilla, David Mart{\'i}n},
  title        = {{AI Convention Lifecycle Corpus v2.0.0 --- Expanded 209-Repository Dataset and Adoption--Maintenance Framework}},
  year         = {2026},
  publisher    = {Zenodo},
  version      = {v2.0.0},
  doi          = {10.5281/zenodo.20637986},
  url          = {https://doi.org/10.5281/zenodo.20637986},
  note         = {209 analyzed repositories; 13{,}988 ever-introduced artifacts; headline mature-present gap 56.0\% at T=180 days}
}
```

### In prose (methods / data availability)

> We used the AI Convention Lifecycle Corpus v2.0.0 — Expanded 209-Repository Dataset and Adoption–Maintenance Framework (Andrés & Moncunilla, 2026; Zenodo: https://doi.org/10.5281/zenodo.20637986), comprising 209 analyzed GitHub repositories and 13,988 ever-introduced AI instructional artifact instances.

### Version + Git commit (optional, for code-only forks)

If you cite a specific commit rather than a tag:

```bibtex
@software{ai_convention_lifecycle_corpus_commit,
  author       = {Andr{\'e}s, C\'esar and Moncunilla, David Mart{\'i}n},
  title        = {{AI Convention Lifecycle Corpus}},
  year         = {2026},
  url          = {https://github.com/cesar-andress/ai-convention-lifecycle-corpus},
  note         = {Commit: \texttt{<40-char-SHA>}; tag v2.0.0 recommended for replication}
}
```

Replace `<40-char-SHA>` with the release commit hash from the `v2.0.0` Git tag.

---

## Companion MSR paper (separate citation)

The empirical study narrative appears in a **companion conference paper** (MSR '26). Cite it **only** when you refer to the paper's framing, figures, or claims—not when you reuse this corpus alone.

Metadata for that paper is listed under `preferred-citation` in [`CITATION.cff`](../CITATION.cff). The paper source is **not** bundled in this repository.

---

## Quick checklist

- [ ] Named **version** (`v2.0.0`) in methods or appendix
- [ ] Included **Zenodo DOI** for data/results reuse
- [ ] Used **GitHub URL** only when citing the codebase itself
- [ ] Did **not** conflate corpus citation with the MSR paper unless both were used
