# Validated drift review packets

Ground-truth validation workbook — **pilot subset, no population claims.**

Fill manual labels in `validated_drift_ground_truth.csv`.

## Priority ranking explained

Priority ranking (higher = review first):
1. `history_quality=reliable` — git history supports path existence and deletion timeline.
2. `source_code_reference` — concrete source file with extension (.py, .go, …).
3. `config_reference` — manifest/config artifact (setup.py, *.yaml, …).
4. `deleted_directory` — directory prefix; may be generic if top-level name only.
5. `documentation_reference` — doc paths; drift possible but governance differs.
6. `unknown` — globs, weak resolution, or unclassified patterns.

`priority_score` combines category rank (0–60), history quality (0–30), deletion evidence (0–10),
and instruction reference signal (0–10), minus penalties for globs (−15) and parser-artifact hints (−10).

## [1] `DC006` — priority score **100**

- **Evidence strength:** `strong`
- **Repository:** `dagster-io/dagster`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `setup.py`
- **Resolved path:** `setup.py`
- **Auto category:** `config_reference`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2018-05-22` (`61d6fe3d93e7…`)
- Last seen: `2018-07-19` (`bd4a1bec4153…`)
- Deletion commit: `2018-07-19` (`bd4a1bec4153…`)
- Path lifetime (days): `58`
- History path used: `setup.py`

### Instruction context

- Section heading: Package Management
- Line: 87

```markdown
  82| - Never skip this step - code quality checks are essential for all contributions
  83| 
  84| ## Package Management
  85| 
  86| - Always use uv instead of pip
  87| - **IMPORTANT**: When command line entry_points change in setup.py, you must reinstall the package using `uv pip install -e .` for the changes to take effect
  88| 
  89| ## Code searching
  90| 
  91| - DO NOT search for Python code (.py files) inside of .tox folders. These are temporary environments and this will only cause confusion.
  92| - Always search for package dependencies in setup.py files only. This is the current source of truth for dependencies in this repository.
```

**Priority explanation:** category=config_reference (+50); history=reliable (+30); deleted_commit (+10); instruction_ref (+10) → score=100

---

## [2] `DC011` — priority score **100**

- **Evidence strength:** `moderate`
- **Repository:** `apache/airflow`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `airflow/cli/cli_parser.py`
- **Resolved path:** `airflow/cli/cli_parser.py`
- **Auto category:** `source_code_reference`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2020-03-22` (`8465d66f05ba…`)
- Last seen: `2025-03-21` (`243fe86d4b3e…`)
- Deletion commit: `2025-03-21` (`243fe86d4b3e…`)
- Path lifetime (days): `1824`
- History path used: `airflow/cli/cli_parser.py`

### Instruction context

- Section heading: _(none)_
- Line: n/a

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

**Priority explanation:** category=source_code_reference (+60); history=reliable (+30); deleted_commit (+10); instruction_ref (+0) → score=100

---

## [3] `DC012` — priority score **100**

- **Evidence strength:** `moderate`
- **Repository:** `apache/airflow`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `tests/cli/test_cli_parser.py`
- **Resolved path:** `tests/cli/test_cli_parser.py`
- **Auto category:** `source_code_reference`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2020-03-22` (`8465d66f05ba…`)
- Last seen: `2025-03-21` (`243fe86d4b3e…`)
- Deletion commit: `2025-03-21` (`243fe86d4b3e…`)
- Path lifetime (days): `1824`
- History path used: `tests/cli/test_cli_parser.py`

### Instruction context

- Section heading: _(none)_
- Line: n/a

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

**Priority explanation:** category=source_code_reference (+60); history=reliable (+30); deleted_commit (+10); instruction_ref (+0) → score=100

---

## [4] `DC013` — priority score **100**

- **Evidence strength:** `moderate`
- **Repository:** `apache/airflow`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `airflow/cli/cli_parser.py`
- **Resolved path:** `airflow/cli/cli_parser.py`
- **Auto category:** `source_code_reference`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2020-03-22` (`8465d66f05ba…`)
- Last seen: `2025-03-21` (`243fe86d4b3e…`)
- Deletion commit: `2025-03-21` (`243fe86d4b3e…`)
- Path lifetime (days): `1824`
- History path used: `airflow/cli/cli_parser.py`

### Instruction context

- Section heading: _(none)_
- Line: n/a

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

**Priority explanation:** category=source_code_reference (+60); history=reliable (+30); deleted_commit (+10); instruction_ref (+0) → score=100

---

## [5] `DC014` — priority score **100**

- **Evidence strength:** `moderate`
- **Repository:** `apache/airflow`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `tests/cli/test_cli_parser.py`
- **Resolved path:** `tests/cli/test_cli_parser.py`
- **Auto category:** `source_code_reference`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2020-03-22` (`8465d66f05ba…`)
- Last seen: `2025-03-21` (`243fe86d4b3e…`)
- Deletion commit: `2025-03-21` (`243fe86d4b3e…`)
- Path lifetime (days): `1824`
- History path used: `tests/cli/test_cli_parser.py`

### Instruction context

- Section heading: _(none)_
- Line: n/a

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

**Priority explanation:** category=source_code_reference (+60); history=reliable (+30); deleted_commit (+10); instruction_ref (+0) → score=100

---

## [6] `DC005` — priority score **90**

- **Evidence strength:** `strong`
- **Repository:** `dagster-io/dagster`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `examples/docs_snippets/docs_snippets/intro_tutorial/basics/connecting_ops/`
- **Resolved path:** `examples/docs_snippets/docs_snippets/intro_tutorial/basics/connecting_ops/`
- **Auto category:** `deleted_directory`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2022-08-25` (`84221d05f29b…`)
- Last seen: `2026-04-23` (`cb2b0148b00a…`)
- Deletion commit: `2026-04-23` (`cb2b0148b00a…`)
- Path lifetime (days): `1336`
- History path used: `examples/docs_snippets/docs_snippets/intro_tutorial/basics/connecting_ops/`

### Instruction context

- Section heading: Terminal 1: Start GraphQL server
- Line: 57

```markdown
  52| 
  53| ## UI Development
  54| 
  55| ```bash
  56| # Terminal 1: Start GraphQL server
  57| cd examples/docs_snippets/docs_snippets/intro_tutorial/basics/connecting_ops/
  58| dagster-webserver -p 3333 -f complex_job.py
  59| 
  60| # Terminal 2: Start UI development server
  61| cd js_modules
  62| make dev_webapp
```

**Priority explanation:** category=deleted_directory (+40); history=reliable (+30); deleted_commit (+10); instruction_ref (+10) → score=90

---

## [7] `DC029` — priority score **82**

- **Evidence strength:** `moderate`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `src/`
- **Resolved path:** `src/`
- **Auto category:** `deleted_directory`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2025-03-10` (`a6524720f555…`)
- Last seen: `2025-03-10` (`a6524720f555…`)
- Deletion commit: `2023-09-18` (`54a76e140163…`)
- Path lifetime (days): `0`
- History path used: `src/`

### Instruction context

- Section heading: Architecture Notes
- Line: 36

```markdown
  31| 
  32| - Payload 3.x is built as a Next.js native CMS that installs directly in `/app` folder
  33| - UI is built with React Server Components (RSC)
  34| - Database adapters use Drizzle ORM under the hood
  35| - Packages use TypeScript with strict mode and path mappings defined in `tsconfig.base.json`
  36| - Source files are in `src/`, compiled outputs go to `dist/`
  37| - Monorepo uses pnpm workspaces and Turbo for builds
  38| 
  39| ## Quick Start
  40| 
  41| 1. `pnpm install`
```

**Priority explanation:** category=deleted_directory (+40); history=reliable (+30); deleted_commit (+10); instruction_ref (+10); penalties: generic path token (−8) → score=82

---

## [8] `DC030` — priority score **82**

- **Evidence strength:** `moderate`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `src`
- **Resolved path:** `src/`
- **Auto category:** `deleted_directory`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2025-03-10` (`a6524720f555…`)
- Last seen: `2025-03-10` (`a6524720f555…`)
- Deletion commit: `2023-09-18` (`54a76e140163…`)
- Path lifetime (days): `0`
- History path used: `src`

### Instruction context

- Section heading: Architecture Notes
- Line: 36

```markdown
  31| 
  32| - Payload 3.x is built as a Next.js native CMS that installs directly in `/app` folder
  33| - UI is built with React Server Components (RSC)
  34| - Database adapters use Drizzle ORM under the hood
  35| - Packages use TypeScript with strict mode and path mappings defined in `tsconfig.base.json`
  36| - Source files are in `src/`, compiled outputs go to `dist/`
  37| - Monorepo uses pnpm workspaces and Turbo for builds
  38| 
  39| ## Quick Start
  40| 
  41| 1. `pnpm install`
```

**Priority explanation:** category=deleted_directory (+40); history=reliable (+30); deleted_commit (+10); instruction_ref (+10); penalties: generic path token (−8) → score=82

---

## [9] `DC031` — priority score **82**

- **Evidence strength:** `moderate`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `dev`
- **Resolved path:** `dev/`
- **Auto category:** `deleted_directory`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2023-04-10` (`2f799a942055…`)
- Last seen: `2023-10-05` (`ac8bcfac237e…`)
- Deletion commit: `2023-10-05` (`ac8bcfac237e…`)
- Path lifetime (days): `177`
- History path used: `dev`

### Instruction context

- Section heading: Quick Start
- Line: 43

```markdown
  38| 
  39| ## Quick Start
  40| 
  41| 1. `pnpm install`
  42| 2. `pnpm run build:core`
  43| 3. `pnpm run dev` (MongoDB) or `pnpm run dev:postgres`
  44| 
  45| ## Build Commands
  46| 
  47| - `pnpm install` - Install all dependencies
  48| - `pnpm turbo` - All Turbo commands should be run from root with pnpm - not with `turbo` directly
```

**Priority explanation:** category=deleted_directory (+40); history=reliable (+30); deleted_commit (+10); instruction_ref (+10); penalties: generic path token (−8) → score=82

---

## [10] `DC035` — priority score **82**

- **Evidence strength:** `moderate`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `Dev`
- **Resolved path:** `dev/`
- **Auto category:** `deleted_directory`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2023-04-10` (`2f799a942055…`)
- Last seen: `2023-10-05` (`ac8bcfac237e…`)
- Deletion commit: `2023-10-05` (`ac8bcfac237e…`)
- Path lifetime (days): `177`
- History path used: `dev/`

### Instruction context

- Section heading: Development
- Line: 53

```markdown
  48| - `pnpm turbo` - All Turbo commands should be run from root with pnpm - not with `turbo` directly
  49| - `pnpm run build` or `pnpm run build:core` - Build core packages (excludes plugins and storage adapters)
  50| - `pnpm run build:all` - Build all packages
  51| - `pnpm run build:<directory_name>` - Build specific package (e.g. `pnpm run build:db-mongodb`, `pnpm run build:ui`)
  52| 
  53| ## Development
  54| 
  55| ### Coding Patterns and Best Practices
  56| 
  57| - Always use object parameters for function arguments: `fn({ name }: { name: string })` not `fn(name: string)` (improves backwards-compatibility)
  58| - Prefer types over interfaces (except when extending external types)
```

**Priority explanation:** category=deleted_directory (+40); history=reliable (+30); deleted_commit (+10); instruction_ref (+10); penalties: generic path token (−8) → score=82

---

## [11] `DC015` — priority score **80**

- **Evidence strength:** `moderate`
- **Repository:** `apache/airflow`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `newsfragments/`
- **Resolved path:** `newsfragments/`
- **Auto category:** `deleted_directory`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2026-02-28` (`996c74080210…`)
- Last seen: `2026-03-09` (`8bf498965c87…`)
- Deletion commit: `2026-03-09` (`8bf498965c87…`)
- Path lifetime (days): `8`
- History path used: `newsfragments/`

### Instruction context

- Section heading: _(none)_
- Line: n/a

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

**Priority explanation:** category=deleted_directory (+40); history=reliable (+30); deleted_commit (+10); instruction_ref (+0) → score=80

---

## [12] `DC009` — priority score **72**

- **Evidence strength:** `moderate`
- **Repository:** `apache/airflow`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `src`
- **Resolved path:** `src/`
- **Auto category:** `deleted_directory`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2014-10-11` (`e491dab9a5c9…`)
- Last seen: `2014-10-12` (`6cffc62e77dd…`)
- Deletion commit: `2014-10-12` (`6cffc62e77dd…`)
- Path lifetime (days): `0`
- History path used: `src`

### Instruction context

- Section heading: _(none)_
- Line: n/a

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

**Priority explanation:** category=deleted_directory (+40); history=reliable (+30); deleted_commit (+10); instruction_ref (+0); penalties: generic path token (−8) → score=72

---

## [13] `DC010` — priority score **72**

- **Evidence strength:** `moderate`
- **Repository:** `apache/airflow`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `tests/`
- **Resolved path:** `tests/`
- **Auto category:** `deleted_directory`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2026-03-06` (`47a1ca7bd945…`)
- Last seen: `2026-04-29` (`cf2fe46c0593…`)
- Deletion commit: `2026-02-12` (`553228f837f9…`)
- Path lifetime (days): `0`
- History path used: `tests/`

### Instruction context

- Section heading: _(none)_
- Line: n/a

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

**Priority explanation:** category=deleted_directory (+40); history=reliable (+30); deleted_commit (+10); instruction_ref (+0); penalties: generic path token (−8) → score=72

---

## [14] `DC036` — priority score **65**

- **Evidence strength:** `weak`
- **Repository:** `prefecthq/prefect`
- **Instruction file:** `AGENTS.md`
- **Extracted reference:** `tests/path.py`
- **Resolved path:** `tests/path.py`
- **Auto category:** `source_code_reference`
- **History quality:** `failed`
- **Current status:** `stale`

### Historical context

- First appearance: `n/a` (`…`)
- Last seen: `n/a` (`…`)
- Deletion commit: `n/a` (`…`)
- Path lifetime (days): `n/a`
- History path used: `n/a`

### Instruction context

- Section heading: Testing (see tests/AGENTS.md for full details)
- Line: 49

```markdown
  44| uv run --project ./src/integrations/<name> <cmd>   # Run against a local integration from repo root
  45| prefect server start                               # Start local server
  46| prefect config view                                # Inspect current configuration
  47| 
  48| # Testing (see tests/AGENTS.md for full details)
  49| uv run pytest tests/path.py -k name    # Run specific test
  50| uv run pytest tests/path.py -x -n4     # Parallel, stop on first failure
  51| 
  52| # Linting & formatting
  53| uv run ruff check --fix .              # Lint with auto-fix
  54| uv run ruff format .                   # Format code
```

**Priority explanation:** category=source_code_reference (+60); history=failed (+0); deleted_commit (+0); instruction_ref (+10); penalties: failed history lookup (−5) → score=65

---

## [15] `DC002` — priority score **60**

- **Evidence strength:** `moderate`
- **Repository:** `cheat/cheat`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `.cheat`
- **Resolved path:** `cheat`
- **Auto category:** `unknown`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2019-08-03` (`d10290541d68…`)
- Last seen: `2019-10-20` (`e5114a3e7665…`)
- Deletion commit: `2019-10-20` (`e5114a3e7665…`)
- Path lifetime (days): `78`
- History path used: `cheat`

### Instruction context

- Section heading: Install cheat to your PATH
- Line: 15

```markdown
  10| make build
  11| 
  12| # Build release binaries for all platforms
  13| make build-release
  14| 
  15| # Install cheat to your PATH
  16| make install
  17| ```
  18| 
  19| ### Testing and Quality Checks
  20| ```bash
```

**Priority explanation:** category=unknown (+10); history=reliable (+30); deleted_commit (+10); instruction_ref (+10) → score=60

---

## [16] `DC032` — priority score **60**

- **Evidence strength:** `moderate`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `.scss`
- **Resolved path:** `scss`
- **Auto category:** `unknown`
- **History quality:** `reliable`
- **Current status:** `stale`

### Historical context

- First appearance: `2021-07-01` (`929b21d68b9d…`)
- Last seen: `2023-08-23` (`a67278b29ff6…`)
- Deletion commit: `2023-08-23` (`a67278b29ff6…`)
- Path lifetime (days): `782`
- History path used: `scss`

### Instruction context

- Section heading: React Component File Structure
- Line: 100

```markdown
  95| Each React component should have its own named folder:
  96| 
  97| ```
  98| ComponentName/
  99| ├── index.tsx       # Component implementation
 100| └── index.scss      # Styles (if applicable)
 101| ```
 102| 
 103| - **Do:** Create a folder per component with `index.tsx` and `index.scss`
 104| - **Don't:** Place multiple `ComponentName.tsx` files in a single folder with one shared `.scss` file
 105| - Re-export from barrel files (`index.ts`) when grouping related components in a parent directory
```

**Priority explanation:** category=unknown (+10); history=reliable (+30); deleted_commit (+10); instruction_ref (+10) → score=60

---

## [17] `DC007` — priority score **55**

- **Evidence strength:** `weak`
- **Repository:** `apache/airflow`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `dev/my_script.py`
- **Resolved path:** `dev/my_script.py`
- **Auto category:** `source_code_reference`
- **History quality:** `failed`
- **Current status:** `stale`

### Historical context

- First appearance: `n/a` (`…`)
- Last seen: `n/a` (`…`)
- Deletion commit: `n/a` (`…`)
- Path lifetime (days): `n/a`
- History path used: `n/a`

### Instruction context

- Section heading: _(none)_
- Line: n/a

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

**Priority explanation:** category=source_code_reference (+60); history=failed (+0); deleted_commit (+0); instruction_ref (+0); penalties: failed history lookup (−5) → score=55

---

## [18] `DC018` — priority score **55**

- **Evidence strength:** `weak`
- **Repository:** `BerriAI/litellm`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `litellm/proxy/dev_config.yaml`
- **Resolved path:** `litellm/proxy/dev_config.yaml`
- **Auto category:** `config_reference`
- **History quality:** `failed`
- **Current status:** `stale`

### Historical context

- First appearance: `n/a` (`…`)
- Last seen: `n/a` (`…`)
- Deletion commit: `n/a` (`…`)
- Path lifetime (days): `n/a`
- History path used: `n/a`

### Instruction context

- Section heading: _(none)_
- Line: 25

```markdown
  20| 
  21| When creating PRs, don't set base to `main`. `litellm_internal_staging` serves that purpose
  22| 
  23| Always use @.github/pull_request_template.md as a guide for your PR body
  24| 
  25| Never use `pytest` commands or the like as "Screenshots / Proof of Fix". We prefer curl'ing a live proxy instance running on localhost:4000 (I like to run it with `python litellm/proxy/proxy_cli.py --config litellm/proxy/dev_config.yaml --detailed_debug --reload --use_v2_migration_resolver 2>&1 | tee litellm.log`) and showing both the command run and the output. Also, it should hit real LLM provider APIs, not mocks, and cost real $$$ because that is the most realistic test. The proof of fix should be exactly what the end user / customer would see / do. The run logs in PR #27703 is a prime example of how to do it (not a huge fan of using a python test script that future me and the team will have no visibility into; I prefer just curl commands or a short list of bash commands (e.g., using `for`)). If it's a UI thing, just tell me which URLs to go to (e.g., http://localhost:4000/ui/?page=logs), where to click, what fields to fill out, etc. along with the other commands to run in an ordered list, and I'll do it myself and post the screenshots after you make the PR
  26| 
  27| If you ever make public-facing PR descriptions, comments, issues, commit messages, etc., always follow these guidelines to sound less AI-y:
  28| - don't use emojis
  29| - don't use "—". Instead, reach for ";", ".", etc.
  30| - don't use the pattern "It's not X, it's Y", "You're not X, you're Y", etc.
```

**Priority explanation:** category=config_reference (+50); history=failed (+0); deleted_commit (+0); instruction_ref (+10); penalties: failed history lookup (−5) → score=55

---

## [19] `DC037` — priority score **45**

- **Evidence strength:** `weak`
- **Repository:** `grafana/grafana`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `conf/custom.ini`
- **Resolved path:** `conf/custom.ini`
- **Auto category:** `config_reference`
- **History quality:** `failed`
- **Current status:** `stale`

### Historical context

- First appearance: `n/a` (`…`)
- Last seen: `n/a` (`…`)
- Deletion commit: `n/a` (`…`)
- Path lifetime (days): `n/a`
- History path used: `n/a`

### Instruction context

- Section heading: _(none)_
- Line: n/a

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

**Priority explanation:** category=config_reference (+50); history=failed (+0); deleted_commit (+0); instruction_ref (+0); penalties: failed history lookup (−5) → score=45

---

## [20] `DC038` — priority score **45**

- **Evidence strength:** `weak`
- **Repository:** `grafana/grafana`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `conf/custom.ini`
- **Resolved path:** `conf/custom.ini`
- **Auto category:** `config_reference`
- **History quality:** `failed`
- **Current status:** `stale`

### Historical context

- First appearance: `n/a` (`…`)
- Last seen: `n/a` (`…`)
- Deletion commit: `n/a` (`…`)
- Path lifetime (days): `n/a`
- History path used: `n/a`

### Instruction context

- Section heading: _(none)_
- Line: n/a

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

**Priority explanation:** category=config_reference (+50); history=failed (+0); deleted_commit (+0); instruction_ref (+0); penalties: failed history lookup (−5) → score=45

---

## [21] `DC004` — priority score **25**

- **Evidence strength:** `weak`
- **Repository:** `electron/electron`
- **Instruction file:** `docs/CLAUDE.md`
- **Extracted reference:** `docs/api/file.md`
- **Resolved path:** `docs/api/file.md`
- **Auto category:** `documentation_reference`
- **History quality:** `failed`
- **Current status:** `doc_reference`

### Historical context

- First appearance: `n/a` (`…`)
- Last seen: `n/a` (`…`)
- Deletion commit: `n/a` (`…`)
- Path lifetime (days): `n/a`
- History path used: `n/a`

### Instruction context

- Section heading: Finding when an API was added
- Line: 29

```markdown
  24| * `arg` type - Description.
  25| ````
  26| 
  27| ### Finding when an API was added
  28| 
  29| - `git log --all --reverse --oneline -S "methodName" -- docs/api/file.md` — find first commit adding a method name
  30| - `git log --reverse -L :FunctionName:path/to/source.cc` — trace C++ implementation history
  31| - `git log --grep="keyword" --oneline` — find merge commits referencing PRs
  32| - `gh pr view <number> --repo electron/electron --json baseRefName` — verify PR targets main (not a backport)
  33| - Always use the main-branch PR URL in history blocks, not backport PRs
  34| 
```

**Priority explanation:** category=documentation_reference (+30); history=failed (+0); deleted_commit (+0); instruction_ref (+0); penalties: failed history lookup (−5) → score=25

---

## [22] `DC016` — priority score **25**

- **Evidence strength:** `weak`
- **Repository:** `apache/airflow`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `docs/05_pull_requests.rst`
- **Resolved path:** `docs/05_pull_requests.rst`
- **Auto category:** `documentation_reference`
- **History quality:** `failed`
- **Current status:** `doc_reference`

### Historical context

- First appearance: `n/a` (`…`)
- Last seen: `n/a` (`…`)
- Deletion commit: `n/a` (`…`)
- Path lifetime (days): `n/a`
- History path used: `n/a`

### Instruction context

- Section heading: _(none)_
- Line: n/a

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

**Priority explanation:** category=documentation_reference (+30); history=failed (+0); deleted_commit (+0); instruction_ref (+0); penalties: failed history lookup (−5) → score=25

---

## [23] `DC003` — priority score **17**

- **Evidence strength:** `weak`
- **Repository:** `electron/electron`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `patches/chromium/*.patch`
- **Resolved path:** `patches/chromium/*.patch`
- **Auto category:** `unknown`
- **History quality:** `uncertain`
- **Current status:** `stale`

### Historical context

- First appearance: `2026-06-10` (`5d2ab4d1fc46…`)
- Last seen: `2026-06-11` (`d96cfe6d5c36…`)
- Deletion commit: `2026-06-10` (`c6312c9b1781…`)
- Path lifetime (days): `0`
- History path used: `patches/chromium/*.patch`

### Instruction context

- Section heading: Find which patch affects a file
- Line: 257

```markdown
 252| 
 253| # Look for Chromium CL reference in commit
 254| git log -1 {commit_sha}  # Find "Reviewed-on:" line
 255| 
 256| # Find which patch affects a file
 257| grep -l "filename.cc" patches/chromium/*.patch
 258| ```
 259| 
 260| ## CI/CD
 261| 
 262| GitHub Actions workflows in `.github/workflows/`:
```

**Priority explanation:** category=unknown (+10); history=uncertain (+12); deleted_commit (+10); instruction_ref (+10); penalties: glob pattern, artifact heuristic (−25) → score=17

---

## [24] `DC019` — priority score **17**

- **Evidence strength:** `weak`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `packages/db-*`
- **Resolved path:** `packages/db-*`
- **Auto category:** `unknown`
- **History quality:** `uncertain`
- **Current status:** `stale`

### Historical context

- First appearance: `2026-06-09` (`1d6d105da6ea…`)
- Last seen: `2026-06-11` (`6ed9b8507aa8…`)
- Deletion commit: `2026-05-18` (`03f81aea98bf…`)
- Path lifetime (days): `0`
- History path used: `packages/db-*`

### Instruction context

- Section heading: Key Directories
- Line: 15

```markdown
  10| 
  11| - `packages/` - All publishable packages
  12|   - `packages/payload` - Core Payload package containing the main CMS logic
  13|   - `packages/ui` - Admin UI components (React Server Components)
  14|   - `packages/next` - Next.js integration layer
  15|   - `packages/db-*` - Database adapters (MongoDB, Postgres, SQLite, Vercel Postgres, D1 SQLite)
  16|   - `packages/drizzle` - Drizzle ORM integration
  17|   - `packages/kv-redis` - Redis key-value store adapter
  18|   - `packages/richtext-*` - Rich text editors (Lexical)
  19|   - `packages/storage-*` - Storage adapters (S3, Azure, GCS, Uploadthing, Vercel Blob, R2)
  20|   - `packages/email-*` - Email adapters (Nodemailer, Resend)
```

**Priority explanation:** category=unknown (+10); history=uncertain (+12); deleted_commit (+10); instruction_ref (+10); penalties: glob pattern, artifact heuristic (−25) → score=17

---

## [25] `DC020` — priority score **17**

- **Evidence strength:** `weak`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `packages/db-*`
- **Resolved path:** `packages/db-*`
- **Auto category:** `unknown`
- **History quality:** `uncertain`
- **Current status:** `stale`

### Historical context

- First appearance: `2026-06-09` (`1d6d105da6ea…`)
- Last seen: `2026-06-11` (`6ed9b8507aa8…`)
- Deletion commit: `2026-05-18` (`03f81aea98bf…`)
- Path lifetime (days): `0`
- History path used: `packages/db-*`

### Instruction context

- Section heading: Key Directories
- Line: 15

```markdown
  10| 
  11| - `packages/` - All publishable packages
  12|   - `packages/payload` - Core Payload package containing the main CMS logic
  13|   - `packages/ui` - Admin UI components (React Server Components)
  14|   - `packages/next` - Next.js integration layer
  15|   - `packages/db-*` - Database adapters (MongoDB, Postgres, SQLite, Vercel Postgres, D1 SQLite)
  16|   - `packages/drizzle` - Drizzle ORM integration
  17|   - `packages/kv-redis` - Redis key-value store adapter
  18|   - `packages/richtext-*` - Rich text editors (Lexical)
  19|   - `packages/storage-*` - Storage adapters (S3, Azure, GCS, Uploadthing, Vercel Blob, R2)
  20|   - `packages/email-*` - Email adapters (Nodemailer, Resend)
```

**Priority explanation:** category=unknown (+10); history=uncertain (+12); deleted_commit (+10); instruction_ref (+10); penalties: glob pattern, artifact heuristic (−25) → score=17

---

## [26] `DC021` — priority score **17**

- **Evidence strength:** `weak`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `packages/richtext-*`
- **Resolved path:** `packages/richtext-*`
- **Auto category:** `unknown`
- **History quality:** `uncertain`
- **Current status:** `stale`

### Historical context

- First appearance: `2026-06-05` (`d4944285af6d…`)
- Last seen: `2026-06-11` (`47f74f491b1d…`)
- Deletion commit: `2026-06-05` (`d4944285af6d…`)
- Path lifetime (days): `0`
- History path used: `packages/richtext-*`

### Instruction context

- Section heading: Key Directories
- Line: 18

```markdown
  13|   - `packages/ui` - Admin UI components (React Server Components)
  14|   - `packages/next` - Next.js integration layer
  15|   - `packages/db-*` - Database adapters (MongoDB, Postgres, SQLite, Vercel Postgres, D1 SQLite)
  16|   - `packages/drizzle` - Drizzle ORM integration
  17|   - `packages/kv-redis` - Redis key-value store adapter
  18|   - `packages/richtext-*` - Rich text editors (Lexical)
  19|   - `packages/storage-*` - Storage adapters (S3, Azure, GCS, Uploadthing, Vercel Blob, R2)
  20|   - `packages/email-*` - Email adapters (Nodemailer, Resend)
  21|   - `packages/plugin-*` - Additional functionality plugins
  22|   - `packages/graphql` - GraphQL API layer
  23|   - `packages/translations` - i18n translations
```

**Priority explanation:** category=unknown (+10); history=uncertain (+12); deleted_commit (+10); instruction_ref (+10); penalties: glob pattern, artifact heuristic (−25) → score=17

---

## [27] `DC022` — priority score **17**

- **Evidence strength:** `weak`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `packages/richtext-*`
- **Resolved path:** `packages/richtext-*`
- **Auto category:** `unknown`
- **History quality:** `uncertain`
- **Current status:** `stale`

### Historical context

- First appearance: `2026-06-05` (`d4944285af6d…`)
- Last seen: `2026-06-11` (`47f74f491b1d…`)
- Deletion commit: `2026-06-05` (`d4944285af6d…`)
- Path lifetime (days): `0`
- History path used: `packages/richtext-*`

### Instruction context

- Section heading: Key Directories
- Line: 18

```markdown
  13|   - `packages/ui` - Admin UI components (React Server Components)
  14|   - `packages/next` - Next.js integration layer
  15|   - `packages/db-*` - Database adapters (MongoDB, Postgres, SQLite, Vercel Postgres, D1 SQLite)
  16|   - `packages/drizzle` - Drizzle ORM integration
  17|   - `packages/kv-redis` - Redis key-value store adapter
  18|   - `packages/richtext-*` - Rich text editors (Lexical)
  19|   - `packages/storage-*` - Storage adapters (S3, Azure, GCS, Uploadthing, Vercel Blob, R2)
  20|   - `packages/email-*` - Email adapters (Nodemailer, Resend)
  21|   - `packages/plugin-*` - Additional functionality plugins
  22|   - `packages/graphql` - GraphQL API layer
  23|   - `packages/translations` - i18n translations
```

**Priority explanation:** category=unknown (+10); history=uncertain (+12); deleted_commit (+10); instruction_ref (+10); penalties: glob pattern, artifact heuristic (−25) → score=17

---

## [28] `DC023` — priority score **17**

- **Evidence strength:** `weak`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `packages/storage-*`
- **Resolved path:** `packages/storage-*`
- **Auto category:** `unknown`
- **History quality:** `uncertain`
- **Current status:** `stale`

### Historical context

- First appearance: `2026-04-10` (`6690769b9f73…`)
- Last seen: `2026-06-09` (`a8c8da8df42f…`)
- Deletion commit: `2026-04-10` (`6690769b9f73…`)
- Path lifetime (days): `0`
- History path used: `packages/storage-*`

### Instruction context

- Section heading: Key Directories
- Line: 19

```markdown
  14|   - `packages/next` - Next.js integration layer
  15|   - `packages/db-*` - Database adapters (MongoDB, Postgres, SQLite, Vercel Postgres, D1 SQLite)
  16|   - `packages/drizzle` - Drizzle ORM integration
  17|   - `packages/kv-redis` - Redis key-value store adapter
  18|   - `packages/richtext-*` - Rich text editors (Lexical)
  19|   - `packages/storage-*` - Storage adapters (S3, Azure, GCS, Uploadthing, Vercel Blob, R2)
  20|   - `packages/email-*` - Email adapters (Nodemailer, Resend)
  21|   - `packages/plugin-*` - Additional functionality plugins
  22|   - `packages/graphql` - GraphQL API layer
  23|   - `packages/translations` - i18n translations
  24| - `test/` - Test suites organized by feature area. Each directory contains a granular Payload config and test files
```

**Priority explanation:** category=unknown (+10); history=uncertain (+12); deleted_commit (+10); instruction_ref (+10); penalties: glob pattern, artifact heuristic (−25) → score=17

---

## [29] `DC024` — priority score **17**

- **Evidence strength:** `weak`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `packages/storage-*`
- **Resolved path:** `packages/storage-*`
- **Auto category:** `unknown`
- **History quality:** `uncertain`
- **Current status:** `stale`

### Historical context

- First appearance: `2026-04-10` (`6690769b9f73…`)
- Last seen: `2026-06-09` (`a8c8da8df42f…`)
- Deletion commit: `2026-04-10` (`6690769b9f73…`)
- Path lifetime (days): `0`
- History path used: `packages/storage-*`

### Instruction context

- Section heading: Key Directories
- Line: 19

```markdown
  14|   - `packages/next` - Next.js integration layer
  15|   - `packages/db-*` - Database adapters (MongoDB, Postgres, SQLite, Vercel Postgres, D1 SQLite)
  16|   - `packages/drizzle` - Drizzle ORM integration
  17|   - `packages/kv-redis` - Redis key-value store adapter
  18|   - `packages/richtext-*` - Rich text editors (Lexical)
  19|   - `packages/storage-*` - Storage adapters (S3, Azure, GCS, Uploadthing, Vercel Blob, R2)
  20|   - `packages/email-*` - Email adapters (Nodemailer, Resend)
  21|   - `packages/plugin-*` - Additional functionality plugins
  22|   - `packages/graphql` - GraphQL API layer
  23|   - `packages/translations` - i18n translations
  24| - `test/` - Test suites organized by feature area. Each directory contains a granular Payload config and test files
```

**Priority explanation:** category=unknown (+10); history=uncertain (+12); deleted_commit (+10); instruction_ref (+10); penalties: glob pattern, artifact heuristic (−25) → score=17

---

## [30] `DC025` — priority score **17**

- **Evidence strength:** `weak`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `packages/email-*`
- **Resolved path:** `packages/email-*`
- **Auto category:** `unknown`
- **History quality:** `uncertain`
- **Current status:** `stale`

### Historical context

- First appearance: `2024-07-15` (`f494ebabbffb…`)
- Last seen: `2026-06-09` (`a8c8da8df42f…`)
- Deletion commit: `2026-01-06` (`e50d811f25ee…`)
- Path lifetime (days): `540`
- History path used: `packages/email-*`

### Instruction context

- Section heading: Key Directories
- Line: 20

```markdown
  15|   - `packages/db-*` - Database adapters (MongoDB, Postgres, SQLite, Vercel Postgres, D1 SQLite)
  16|   - `packages/drizzle` - Drizzle ORM integration
  17|   - `packages/kv-redis` - Redis key-value store adapter
  18|   - `packages/richtext-*` - Rich text editors (Lexical)
  19|   - `packages/storage-*` - Storage adapters (S3, Azure, GCS, Uploadthing, Vercel Blob, R2)
  20|   - `packages/email-*` - Email adapters (Nodemailer, Resend)
  21|   - `packages/plugin-*` - Additional functionality plugins
  22|   - `packages/graphql` - GraphQL API layer
  23|   - `packages/translations` - i18n translations
  24| - `test/` - Test suites organized by feature area. Each directory contains a granular Payload config and test files
  25| - `docs/` - Documentation (deployed to payloadcms.com)
```

**Priority explanation:** category=unknown (+10); history=uncertain (+12); deleted_commit (+10); instruction_ref (+10); penalties: glob pattern, artifact heuristic (−25) → score=17

---

## [31] `DC026` — priority score **17**

- **Evidence strength:** `weak`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `packages/email-*`
- **Resolved path:** `packages/email-*`
- **Auto category:** `unknown`
- **History quality:** `uncertain`
- **Current status:** `stale`

### Historical context

- First appearance: `2024-07-15` (`f494ebabbffb…`)
- Last seen: `2026-06-09` (`a8c8da8df42f…`)
- Deletion commit: `2026-01-06` (`e50d811f25ee…`)
- Path lifetime (days): `540`
- History path used: `packages/email-*`

### Instruction context

- Section heading: Key Directories
- Line: 20

```markdown
  15|   - `packages/db-*` - Database adapters (MongoDB, Postgres, SQLite, Vercel Postgres, D1 SQLite)
  16|   - `packages/drizzle` - Drizzle ORM integration
  17|   - `packages/kv-redis` - Redis key-value store adapter
  18|   - `packages/richtext-*` - Rich text editors (Lexical)
  19|   - `packages/storage-*` - Storage adapters (S3, Azure, GCS, Uploadthing, Vercel Blob, R2)
  20|   - `packages/email-*` - Email adapters (Nodemailer, Resend)
  21|   - `packages/plugin-*` - Additional functionality plugins
  22|   - `packages/graphql` - GraphQL API layer
  23|   - `packages/translations` - i18n translations
  24| - `test/` - Test suites organized by feature area. Each directory contains a granular Payload config and test files
  25| - `docs/` - Documentation (deployed to payloadcms.com)
```

**Priority explanation:** category=unknown (+10); history=uncertain (+12); deleted_commit (+10); instruction_ref (+10); penalties: glob pattern, artifact heuristic (−25) → score=17

---

## [32] `DC027` — priority score **17**

- **Evidence strength:** `weak`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `packages/plugin-*`
- **Resolved path:** `packages/plugin-*`
- **Auto category:** `unknown`
- **History quality:** `uncertain`
- **Current status:** `stale`

### Historical context

- First appearance: `2026-06-11` (`0a840997e88e…`)
- Last seen: `2026-06-11` (`dc41f9fb7927…`)
- Deletion commit: `2026-06-10` (`19342ed0ac26…`)
- Path lifetime (days): `0`
- History path used: `packages/plugin-*`

### Instruction context

- Section heading: Key Directories
- Line: 21

```markdown
  16|   - `packages/drizzle` - Drizzle ORM integration
  17|   - `packages/kv-redis` - Redis key-value store adapter
  18|   - `packages/richtext-*` - Rich text editors (Lexical)
  19|   - `packages/storage-*` - Storage adapters (S3, Azure, GCS, Uploadthing, Vercel Blob, R2)
  20|   - `packages/email-*` - Email adapters (Nodemailer, Resend)
  21|   - `packages/plugin-*` - Additional functionality plugins
  22|   - `packages/graphql` - GraphQL API layer
  23|   - `packages/translations` - i18n translations
  24| - `test/` - Test suites organized by feature area. Each directory contains a granular Payload config and test files
  25| - `docs/` - Documentation (deployed to payloadcms.com)
  26| - `tools/` - Monorepo tooling
```

**Priority explanation:** category=unknown (+10); history=uncertain (+12); deleted_commit (+10); instruction_ref (+10); penalties: glob pattern, artifact heuristic (−25) → score=17

---

## [33] `DC028` — priority score **17**

- **Evidence strength:** `weak`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `packages/plugin-*`
- **Resolved path:** `packages/plugin-*`
- **Auto category:** `unknown`
- **History quality:** `uncertain`
- **Current status:** `stale`

### Historical context

- First appearance: `2026-06-11` (`0a840997e88e…`)
- Last seen: `2026-06-11` (`dc41f9fb7927…`)
- Deletion commit: `2026-06-10` (`19342ed0ac26…`)
- Path lifetime (days): `0`
- History path used: `packages/plugin-*`

### Instruction context

- Section heading: Key Directories
- Line: 21

```markdown
  16|   - `packages/drizzle` - Drizzle ORM integration
  17|   - `packages/kv-redis` - Redis key-value store adapter
  18|   - `packages/richtext-*` - Rich text editors (Lexical)
  19|   - `packages/storage-*` - Storage adapters (S3, Azure, GCS, Uploadthing, Vercel Blob, R2)
  20|   - `packages/email-*` - Email adapters (Nodemailer, Resend)
  21|   - `packages/plugin-*` - Additional functionality plugins
  22|   - `packages/graphql` - GraphQL API layer
  23|   - `packages/translations` - i18n translations
  24| - `test/` - Test suites organized by feature area. Each directory contains a granular Payload config and test files
  25| - `docs/` - Documentation (deployed to payloadcms.com)
  26| - `tools/` - Monorepo tooling
```

**Priority explanation:** category=unknown (+10); history=uncertain (+12); deleted_commit (+10); instruction_ref (+10); penalties: glob pattern, artifact heuristic (−25) → score=17

---

## [34] `DC001` — priority score **15**

- **Evidence strength:** `weak`
- **Repository:** `cheat/cheat`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `./internal/package_name`
- **Resolved path:** `internal/package_name`
- **Auto category:** `unknown`
- **History quality:** `failed`
- **Current status:** `stale`

### Historical context

- First appearance: `n/a` (`…`)
- Last seen: `n/a` (`…`)
- Deletion commit: `n/a` (`…`)
- Path lifetime (days): `n/a`
- History path used: `n/a`

### Instruction context

- Section heading: Run a single test
- Line: 26

```markdown
  21| # Run all tests
  22| make test
  23| go test ./...
  24| 
  25| # Run a single test
  26| go test -run TestFunctionName ./internal/package_name
  27| 
  28| # Generate test coverage report
  29| make coverage
  30| 
  31| # Run linter (revive)
```

**Priority explanation:** category=unknown (+10); history=failed (+0); deleted_commit (+0); instruction_ref (+10); penalties: failed history lookup (−5) → score=15

---

## [35] `DC017` — priority score **15**

- **Evidence strength:** `weak`
- **Repository:** `apache/airflow`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `[Agent-assisted contribution section of `README.md`](README.md#agent-assisted-contribution-apache-steward)`
- **Resolved path:** `README.md#agent-assisted-contribution-apache-steward`
- **Auto category:** `documentation_reference`
- **History quality:** `failed`
- **Current status:** `doc_reference`

### Historical context

- First appearance: `n/a` (`…`)
- Last seen: `n/a` (`…`)
- Deletion commit: `n/a` (`…`)
- Path lifetime (days): `n/a`
- History path used: `n/a`

### Instruction context

- Section heading: _(none)_
- Line: n/a

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

**Priority explanation:** category=documentation_reference (+30); history=failed (+0); deleted_commit (+0); instruction_ref (+0); penalties: artifact heuristic, failed history lookup (−15) → score=15

---

## [36] `DC033` — priority score **15**

- **Evidence strength:** `weak`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `payload/shared`
- **Resolved path:** `payload/shared`
- **Auto category:** `unknown`
- **History quality:** `failed`
- **Current status:** `stale`

### Historical context

- First appearance: `n/a` (`…`)
- Last seen: `n/a` (`…`)
- Deletion commit: `n/a` (`…`)
- Path lifetime (days): `n/a`
- History path used: `n/a`

### Instruction context

- Section heading: Patterns
- Line: 294

```markdown
 289| ```
 290| 
 291| Correct:
 292| 
 293| ```typescript
 294| import { formatAdminURL } from 'payload/shared'
 295| import * as qs from 'qs-esm'
 296| 
 297| const where = parentId
 298|   ? { [parentFieldName]: { equals: parentId } }
 299|   : {
```

**Priority explanation:** category=unknown (+10); history=failed (+0); deleted_commit (+0); instruction_ref (+10); penalties: failed history lookup (−5) → score=15

---

## [37] `DC034` — priority score **15**

- **Evidence strength:** `weak`
- **Repository:** `payloadcms/payload`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `payload/no-imports-from-exports-dir`
- **Resolved path:** `payload/no-imports-from-exports-dir`
- **Auto category:** `unknown`
- **History quality:** `failed`
- **Current status:** `stale`

### Historical context

- First appearance: `n/a` (`…`)
- Last seen: `n/a` (`…`)
- Deletion commit: `n/a` (`…`)
- Path lifetime (days): `n/a`
- History path used: `n/a`

### Instruction context

- Section heading: RSC/Client Bundling Rules
- Line: 355

```markdown
 350| ```typescript
 351| // BAD - relative import doesn't work in prod
 352| import { MyClientComponent } from './MyComponent.js'
 353| 
 354| // GOOD - import from client exports bundle
 355| // eslint-disable-next-line payload/no-imports-from-exports-dir -- Server component must reference exports dir for proper client boundary
 356| import { MyClientComponent } from '../../exports/client/index.js'
 357| ```
 358| 
 359| **Testing bundling changes:** Always test with `pnpm prepare-run-test-against-prod` followed by `pnpm dev:prod <suite>`. Dev mode (`pnpm dev`) doesn't catch these issues.
```

**Priority explanation:** category=unknown (+10); history=failed (+0); deleted_commit (+0); instruction_ref (+10); penalties: failed history lookup (−5) → score=15

---

## [38] `DC008` — priority score **5**

- **Evidence strength:** `weak`
- **Repository:** `apache/airflow`
- **Instruction file:** `CLAUDE.md`
- **Extracted reference:** `shared/<dist>`
- **Resolved path:** `shared/<dist`
- **Auto category:** `unknown`
- **History quality:** `failed`
- **Current status:** `stale`

### Historical context

- First appearance: `n/a` (`…`)
- Last seen: `n/a` (`…`)
- Deletion commit: `n/a` (`…`)
- Path lifetime (days): `n/a`
- History path used: `n/a`

### Instruction context

- Section heading: _(none)_
- Line: n/a

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

**Priority explanation:** category=unknown (+10); history=failed (+0); deleted_commit (+0); instruction_ref (+0); penalties: failed history lookup (−5) → score=5

---
