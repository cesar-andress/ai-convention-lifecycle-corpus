# Drift candidate instruction context

±5 lines around each extracted reference in the instruction file at HEAD.

**Manual review file:** `drift_candidate_review.csv`

## Candidate `DC001` — `cheat/cheat` / `CLAUDE.md`

- Reference: `./internal/package_name`
- Resolved path: `internal/package_name`
- Section heading: Run a single test
- Line: 26
- Auto category: `unknown`

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

## Candidate `DC002` — `cheat/cheat` / `CLAUDE.md`

- Reference: `.cheat`
- Resolved path: `cheat`
- Section heading: Install cheat to your PATH
- Line: 15
- Auto category: `unknown`

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

## Candidate `DC003` — `electron/electron` / `CLAUDE.md`

- Reference: `patches/chromium/*.patch`
- Resolved path: `patches/chromium/*.patch`
- Section heading: Find which patch affects a file
- Line: 257
- Auto category: `unknown`

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

## Candidate `DC004` — `electron/electron` / `docs/CLAUDE.md`

- Reference: `docs/api/file.md`
- Resolved path: `docs/api/file.md`
- Section heading: Finding when an API was added
- Line: 29
- Auto category: `documentation_reference`

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

## Candidate `DC005` — `dagster-io/dagster` / `CLAUDE.md`

- Reference: `examples/docs_snippets/docs_snippets/intro_tutorial/basics/connecting_ops/`
- Resolved path: `examples/docs_snippets/docs_snippets/intro_tutorial/basics/connecting_ops/`
- Section heading: Terminal 1: Start GraphQL server
- Line: 57
- Auto category: `deleted_directory`

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

## Candidate `DC006` — `dagster-io/dagster` / `CLAUDE.md`

- Reference: `setup.py`
- Resolved path: `setup.py`
- Section heading: Package Management
- Line: 87
- Auto category: `config_reference`

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

## Candidate `DC007` — `apache/airflow` / `CLAUDE.md`

- Reference: `dev/my_script.py`
- Resolved path: `dev/my_script.py`
- Section heading: _(none)_
- Line: n/a
- Auto category: `source_code_reference`

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

## Candidate `DC008` — `apache/airflow` / `CLAUDE.md`

- Reference: `shared/<dist>`
- Resolved path: `shared/<dist`
- Section heading: _(none)_
- Line: n/a
- Auto category: `unknown`

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

## Candidate `DC009` — `apache/airflow` / `CLAUDE.md`

- Reference: `src`
- Resolved path: `src/`
- Section heading: _(none)_
- Line: n/a
- Auto category: `deleted_directory`

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

## Candidate `DC010` — `apache/airflow` / `CLAUDE.md`

- Reference: `tests/`
- Resolved path: `tests/`
- Section heading: _(none)_
- Line: n/a
- Auto category: `deleted_directory`

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

## Candidate `DC011` — `apache/airflow` / `CLAUDE.md`

- Reference: `airflow/cli/cli_parser.py`
- Resolved path: `airflow/cli/cli_parser.py`
- Section heading: _(none)_
- Line: n/a
- Auto category: `source_code_reference`

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

## Candidate `DC012` — `apache/airflow` / `CLAUDE.md`

- Reference: `tests/cli/test_cli_parser.py`
- Resolved path: `tests/cli/test_cli_parser.py`
- Section heading: _(none)_
- Line: n/a
- Auto category: `source_code_reference`

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

## Candidate `DC013` — `apache/airflow` / `CLAUDE.md`

- Reference: `airflow/cli/cli_parser.py`
- Resolved path: `airflow/cli/cli_parser.py`
- Section heading: _(none)_
- Line: n/a
- Auto category: `source_code_reference`

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

## Candidate `DC014` — `apache/airflow` / `CLAUDE.md`

- Reference: `tests/cli/test_cli_parser.py`
- Resolved path: `tests/cli/test_cli_parser.py`
- Section heading: _(none)_
- Line: n/a
- Auto category: `source_code_reference`

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

## Candidate `DC015` — `apache/airflow` / `CLAUDE.md`

- Reference: `newsfragments/`
- Resolved path: `newsfragments/`
- Section heading: _(none)_
- Line: n/a
- Auto category: `deleted_directory`

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

## Candidate `DC016` — `apache/airflow` / `CLAUDE.md`

- Reference: `docs/05_pull_requests.rst`
- Resolved path: `docs/05_pull_requests.rst`
- Section heading: _(none)_
- Line: n/a
- Auto category: `documentation_reference`

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

## Candidate `DC017` — `apache/airflow` / `CLAUDE.md`

- Reference: `[Agent-assisted contribution section of `README.md`](README.md#agent-assisted-contribution-apache-steward)`
- Resolved path: `README.md#agent-assisted-contribution-apache-steward`
- Section heading: _(none)_
- Line: n/a
- Auto category: `documentation_reference`

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

## Candidate `DC018` — `BerriAI/litellm` / `CLAUDE.md`

- Reference: `litellm/proxy/dev_config.yaml`
- Resolved path: `litellm/proxy/dev_config.yaml`
- Section heading: _(none)_
- Line: 25
- Auto category: `config_reference`

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

## Candidate `DC019` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `packages/db-*`
- Resolved path: `packages/db-*`
- Section heading: Key Directories
- Line: 15
- Auto category: `unknown`

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

## Candidate `DC020` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `packages/db-*`
- Resolved path: `packages/db-*`
- Section heading: Key Directories
- Line: 15
- Auto category: `unknown`

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

## Candidate `DC021` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `packages/richtext-*`
- Resolved path: `packages/richtext-*`
- Section heading: Key Directories
- Line: 18
- Auto category: `unknown`

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

## Candidate `DC022` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `packages/richtext-*`
- Resolved path: `packages/richtext-*`
- Section heading: Key Directories
- Line: 18
- Auto category: `unknown`

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

## Candidate `DC023` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `packages/storage-*`
- Resolved path: `packages/storage-*`
- Section heading: Key Directories
- Line: 19
- Auto category: `unknown`

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

## Candidate `DC024` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `packages/storage-*`
- Resolved path: `packages/storage-*`
- Section heading: Key Directories
- Line: 19
- Auto category: `unknown`

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

## Candidate `DC025` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `packages/email-*`
- Resolved path: `packages/email-*`
- Section heading: Key Directories
- Line: 20
- Auto category: `unknown`

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

## Candidate `DC026` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `packages/email-*`
- Resolved path: `packages/email-*`
- Section heading: Key Directories
- Line: 20
- Auto category: `unknown`

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

## Candidate `DC027` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `packages/plugin-*`
- Resolved path: `packages/plugin-*`
- Section heading: Key Directories
- Line: 21
- Auto category: `unknown`

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

## Candidate `DC028` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `packages/plugin-*`
- Resolved path: `packages/plugin-*`
- Section heading: Key Directories
- Line: 21
- Auto category: `unknown`

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

## Candidate `DC029` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `src/`
- Resolved path: `src/`
- Section heading: Architecture Notes
- Line: 36
- Auto category: `deleted_directory`

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

## Candidate `DC030` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `src`
- Resolved path: `src/`
- Section heading: Architecture Notes
- Line: 36
- Auto category: `deleted_directory`

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

## Candidate `DC031` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `dev`
- Resolved path: `dev/`
- Section heading: Quick Start
- Line: 43
- Auto category: `deleted_directory`

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

## Candidate `DC032` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `.scss`
- Resolved path: `scss`
- Section heading: React Component File Structure
- Line: 100
- Auto category: `unknown`

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

## Candidate `DC033` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `payload/shared`
- Resolved path: `payload/shared`
- Section heading: Patterns
- Line: 294
- Auto category: `unknown`

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

## Candidate `DC034` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `payload/no-imports-from-exports-dir`
- Resolved path: `payload/no-imports-from-exports-dir`
- Section heading: RSC/Client Bundling Rules
- Line: 355
- Auto category: `unknown`

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

## Candidate `DC035` — `payloadcms/payload` / `CLAUDE.md`

- Reference: `Dev`
- Resolved path: `dev/`
- Section heading: Development
- Line: 53
- Auto category: `deleted_directory`

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

## Candidate `DC036` — `prefecthq/prefect` / `AGENTS.md`

- Reference: `tests/path.py`
- Resolved path: `tests/path.py`
- Section heading: Testing (see tests/AGENTS.md for full details)
- Line: 49
- Auto category: `source_code_reference`

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

## Candidate `DC037` — `grafana/grafana` / `CLAUDE.md`

- Reference: `conf/custom.ini`
- Resolved path: `conf/custom.ini`
- Section heading: _(none)_
- Line: n/a
- Auto category: `config_reference`

```markdown
(reference string not found verbatim in instruction file at HEAD)
```

## Candidate `DC038` — `grafana/grafana` / `CLAUDE.md`

- Reference: `conf/custom.ini`
- Resolved path: `conf/custom.ini`
- Section heading: _(none)_
- Line: n/a
- Auto category: `config_reference`

```markdown
(reference string not found verbatim in instruction file at HEAD)
```
