# Zenodo release checklist

Step-by-step procedure for publishing a new **AI Convention Lifecycle Corpus** release. Work through sections **in order**; check each box before moving on.

**Repository:** `https://github.com/cesar-andress/ai-convention-lifecycle-corpus`  
**Current headline version:** `v2.0.0` (update placeholders below when bumping)

Related docs: [`zenodo/README.md`](../zenodo/README.md), [`metadata/zenodo.json`](../metadata/zenodo.json), [`docs/CITING.md`](CITING.md), [`docs/reproducibility.md`](reproducibility.md).

---

## Pre-release (local)

### A. Decide version number

Use [Semantic Versioning](https://semver.org/) for the corpus tag:

| Change type | Bump | Example |
|-------------|------|---------|
| Protocol-compatible data refresh, new parquets/results | **minor** | `2.0.0` → `2.1.0` |
| Metadata/docs only, no data change | **patch** | `2.0.0` → `2.0.1` |
| Breaking protocol or cohort redefinition | **major** | `2.0.0` → `3.0.0` |

Write the new version here before starting: **`v__________`**

- [ ] Version number chosen and recorded in release notes draft

---

### B. Version bump (repository files)

Update **every** occurrence of the old version string in:

| File | Fields to update |
|------|------------------|
| [`CITATION.cff`](../CITATION.cff) | `version`, `date-released`; title suffix if cohort name changes |
| [`metadata/zenodo.json`](../metadata/zenodo.json) | `version`, `publication_date`, `title` if needed |
| [`metadata/study_manifest.json`](../metadata/study_manifest.json) | `sample` counts, `headline_primary_180`, `study_id` if cohort changes |
| [`README.md`](../README.md) | §1 table, §6 citation, §8 Zenodo table |
| [`docs/CITING.md`](CITING.md) | version tables, BibTeX `version` / `note` fields |
| [`metadata/replication_package.md`](../metadata/replication_package.md) | headline table, version in title line |

Commands to find stale version strings:

```bash
cd ai-convention-lifecycle-corpus
rg '2\.0\.0|v2\.0\.0|XXXXXXX' --glob '!docs/ZENODO_RELEASE_CHECKLIST.md'
```

- [ ] All version strings updated consistently
- [ ] `date-released` / `publication_date` set to release date (ISO `YYYY-MM-DD`)
- [ ] `metadata/study_manifest.json` matches `results/lifecycle/adoption_maintenance_v2.json` headline counts

---

### C. Pre-release quality gates (corpus root)

```bash
python3 -m venv .venv
source .venv/bin/activate
make install
make verify-headline
make analyze    # optional: confirm analysis reproduces bundled results
```

- [ ] `make verify-headline` prints `OK: n_repos=209 artifact_gap= 0.56` (or updated headline for new cohort)
- [ ] No unintended files staged (run `git status`; no `.venv/`, `data/repos/`, `__pycache__/`)

---

### D. Public-release audit

- [ ] Ran [`docs/public_release_audit.md`](public_release_audit.md) checks (no credentials, no private URLs, no manuscript `.tex`/`.pdf` in corpus)
- [ ] Author names/ORCIDs updated if de-anonymizing (replace placeholders in `CITATION.cff`, `metadata/zenodo.json`)

---

## Git tag

From a **clean** `main` branch at the commit you intend to archive:

```bash
git status          # working tree clean
git pull origin main

# Example for v2.1.0 — replace VERSION
VERSION=v2.1.0
git tag -a "$VERSION" -m "AI Convention Lifecycle Corpus $VERSION"
git push origin "$VERSION"
```

- [ ] Tag created locally: `git tag -l 'v*' | tail -1`
- [ ] Tag pushed to GitHub: `git ls-remote --tags origin | grep VERSION`

---

## GitHub release

1. Open **GitHub → Releases → Draft a new release**.
2. **Choose tag:** the tag from § Git tag (e.g. `v2.1.0`).
3. **Release title:** `AI Convention Lifecycle Corpus v2.1.0` (match tag).
4. **Description:** summarize cohort size, headline gap, and what changed vs. previous release.
5. **Attach assets (optional):** source zip is auto-generated; do **not** attach `data/repos/`.
6. Publish release.

- [ ] GitHub release published and linked to correct tag
- [ ] Release notes mention primary maintenance window (*T* = 180 d) and analyzed repo count
- [ ] Release URL copied: `https://github.com/cesar-andress/ai-convention-lifecycle-corpus/releases/tag/VERSION`

---

## Zenodo archive creation

### E. Prepare upload bundle

**Include** repository root contents **excluding**:

- `.git/`
- `.venv/`
- `data/repos/` (local git clones)
- `__pycache__/`

Example clean export:

```bash
VERSION=v2.1.0   # set your tag
DEST="/tmp/ai-convention-lifecycle-corpus-${VERSION}"
rm -rf "$DEST"
rsync -a --exclude='.git' --exclude='.venv' --exclude='data/repos' \
  --exclude='__pycache__' ./ "$DEST/"
(cd "$(dirname "$DEST")" && zip -r "${DEST}.zip" "$(basename "$DEST")")
ls -lh "${DEST}.zip"
```

- [ ] Zip created and size is reasonable (aggregates only; expect ~tens of MB, not clone-scale GB)

### F. Create or version Zenodo record

**First release:** create new deposit at [https://zenodo.org/deposit/new](https://zenodo.org/deposit/new).

**Subsequent releases:** open existing record → **New version** (preserves DOI prefix, new version DOI).

| Zenodo field | Value |
|--------------|-------|
| Upload type | **Dataset** |
| Publication date | release date |
| Title | `AI Convention Lifecycle Corpus — Adoption Is Not Maintenance (vX.Y.Z)` |
| Version | semver without `v` prefix (e.g. `2.1.0`) |
| License | **CC-BY 4.0** (note MIT code in description) |
| Access | Open |

Copy description HTML from [`metadata/zenodo.json`](../metadata/zenodo.json) and adjust version/cohort numbers.

**Related identifiers:**

- GitHub repo: `https://github.com/cesar-andress/ai-convention-lifecycle-corpus` — relation **isSupplementTo**
- Link to GitHub release URL from above

**GitHub–Zenodo integration (recommended):** enable Zenodo-GitHub hook so publishing a GitHub release triggers archival; still verify metadata manually.

- [ ] Upload zip attached
- [ ] Metadata pasted and version-specific numbers verified
- [ ] Record **published** (not left in draft)

---

## DOI verification

After Zenodo assigns a DOI:

1. Copy DOI: `10.5281/zenodo.________`
2. Resolve in browser: `https://doi.org/10.5281/zenodo.________`
3. Confirm landing page shows correct **version**, **files**, and **title**.

```bash
# Quick HTTP check (expect 200 or 302 to Zenodo record)
DOI=10.5281/zenodo.________
curl -sI "https://doi.org/${DOI}" | head -5
```

- [ ] DOI resolves publicly (no login required)
- [ ] Zenodo file list matches upload bundle (spot-check: `protocol/`, `data/lifecycle/*.parquet`, `results/lifecycle/adoption_maintenance_v2.json`)
- [ ] Zenodo version number matches Git tag (without `v`)

---

## Citation update

Replace **`XXXXXXX`** with the numeric Zenodo record ID in **all** of:

| File | What to replace |
|------|-----------------|
| [`CITATION.cff`](../CITATION.cff) | `doi`, `url` |
| [`metadata/zenodo.json`](../metadata/zenodo.json) | `related_identifiers[].identifier` |
| [`README.md`](../README.md) | §6 BibTeX, §8 DOI table |
| [`docs/CITING.md`](CITING.md) | all `10.5281/zenodo.XXXXXXX` and prose examples |

Search for leftovers:

```bash
rg 'XXXXXXX|zenodo\.PLACEHOLDER' .
```

Commit citation fixes on `main` **after** DOI is known; optionally tag a **patch** release (`v2.1.1`) if the tag was already cut without DOI strings.

- [ ] No `XXXXXXX` placeholders remain in citation files
- [ ] [`CITATION.cff`](../CITATION.cff) validates (optional: [cff-validator](https://github.com/citation-file-format/cff-validator))
- [ ] GitHub release description updated with DOI link

**Companion paper (separate repo):** update Zenodo DOI in `paper/` artifact section if required — **not** part of this corpus commit unless coordinating both releases.

---

## Reproducibility verification

Run checks on the **Zenodo download** (not only the local tree):

```bash
# Download published archive from Zenodo UI or:
# wget -O corpus.zip "https://zenodo.org/records/RECORD_ID/files/BUNDLE.zip"

unzip -q corpus.zip -d /tmp/corpus-verify
cd /tmp/corpus-verify/*/   # adjust if zip root differs

python3 -m venv .venv
source .venv/bin/activate
make install
make verify-headline
```

- [ ] `make verify-headline` passes on extracted Zenodo archive
- [ ] `make analyze` completes without error (optional; confirms parquets + scripts)
- [ ] Headline JSON matches `metadata/study_manifest.json` (`n_analyzed_repos`, `artifact_gap_mature`)

Document verification date and Zenodo record URL in GitHub release notes.

---

## Archive integrity verification

Confirm the published artifact is complete and unmodified in transit.

### File inventory

Compare against [`metadata/replication_package.md`](../metadata/replication_package.md):

```bash
cd /tmp/corpus-verify/*/   # extracted Zenodo tree
for f in \
  protocol/lifecycle_v1.yaml \
  protocol/adoption_maintenance_v1.yaml \
  protocol/adoption_maintenance_v2.yaml \
  data/lifecycle/discovered_v2.csv \
  data/lifecycle/artifacts_full.parquet \
  data/lifecycle/artifact_states_v2.parquet \
  results/lifecycle/adoption_maintenance_v2.json \
  annotation/annotation_sheet.csv \
  CITATION.cff \
  LICENSE \
  README.md
do
  test -e "$f" && echo "OK $f" || echo "MISSING $f"
done
```

- [ ] All critical paths present (`MISSING` count = 0)

### Excluded paths absent

```bash
test ! -d data/repos && echo 'OK: no data/repos'
test ! -d .git && echo 'OK: no .git'
find . -name '__pycache__' | wc -l   # expect 0
```

- [ ] No `data/repos/`, `.git/`, or `__pycache__/` in archive

### Checksum record (optional but recommended)

Store sha256 of the published zip in GitHub release notes:

```bash
sha256sum corpus.zip
```

- [ ] SHA-256 recorded in GitHub release or `metadata/study_manifest.json` (`release_sha256` field if added)

### Cross-links

- [ ] GitHub release links to Zenodo DOI
- [ ] Zenodo record links to GitHub release URL
- [ ] README §8 DOI table shows live DOI (not placeholder)

---

## Post-release

- [ ] Announce DOI (README badge optional)
- [ ] Update any external registries that mirror this corpus
- [ ] Archive this checklist with completed boxes saved in release notes or team wiki

---

## Quick reference (copy for release notes)

```text
Release:     vX.Y.Z
Git tag:     vX.Y.Z
GitHub:      https://github.com/cesar-andress/ai-convention-lifecycle-corpus/releases/tag/vX.Y.Z
Zenodo DOI:  https://doi.org/10.5281/zenodo.________
Cohort:      ___ discovered / ___ analyzed repos; ___ ever-introduced artifacts
Headline:    ___% artifact-level gap (T=180 d); ___% repo-level gap
Verified:    make verify-headline OK on YYYY-MM-DD
SHA-256:     (zip checksum)
```

---

## Version history log

| Version | Date | DOI | Notes |
|---------|------|-----|-------|
| v2.0.0 | 2026-06-11 | `10.5281/zenodo.XXXXXXX` (pending) | Initial public v2 cohort (209 analyzed repos) |
| | | | |

Append a row after each successful release.
