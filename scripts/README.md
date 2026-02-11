# Scripts Documentation

## seed_test_accounts.py

Creates test **admin** and **learner** accounts with a test company so you can try the platform locally. The learner is assigned to the company and (by default) one published module is created and assigned to that company.

**Requirements:** `.env` with `JWT_SECRET_KEY` and `SURREAL_*` (or `SURREAL_URL`), and SurrealDB reachable. Run after the API has been started at least once (migrations applied).

```bash
# Create test company, admin (admin / changeme), learner (learner / learner123), and one sample module
uv run python scripts/seed_test_accounts.py

# Skip creating a sample notebook (company and users only)
uv run python scripts/seed_test_accounts.py --no-notebook

# If you already have a learner without company, assign them to the test company
uv run python scripts/seed_test_accounts.py --force
```

Optional env vars: `DEFAULT_ADMIN_USERNAME`, `DEFAULT_ADMIN_PASSWORD`, `TEST_LEARNER_USERNAME`, `TEST_LEARNER_PASSWORD`, `TEST_COMPANY_NAME`, `TEST_COMPANY_SLUG`, `TEST_NOTEBOOK_NAME`.

---

## clear_command_queue.py

Clears the **surreal-commands** job queue (e.g. podcast generation backlog). Optionally removes artifact rows that reference pending jobs so the UI no longer shows stuck “generating” items.

**Requirements:** `.env` (or `SURREAL_*` env vars) and SurrealDB reachable.

```bash
# Clear the job queue only (all pending/running commands)
uv run python scripts/clear_command_queue.py

# Also remove placeholder podcast artifacts (artifact_id starting with "command:")
uv run python scripts/clear_command_queue.py --artifacts

# See what would be deleted without changing the DB
uv run python scripts/clear_command_queue.py --dry-run
uv run python scripts/clear_command_queue.py --artifacts --dry-run
```

---

## export_docs.py

Consolidates markdown documentation files for use with ChatGPT or other platforms with file upload limits.

### What It Does

- Scans all subdirectories in the `docs/` folder
- For each subdirectory, combines all `.md` files (excluding `index.md` files)
- Creates one consolidated markdown file per subdirectory
- Saves all exported files to `doc_exports/` in the project root

### Usage

```bash
# Using Makefile (recommended)
make export-docs

# Or run directly with uv
uv run python scripts/export_docs.py

# Or run with standard Python
python scripts/export_docs.py
```

### Output

The script creates `doc_exports/` directory with consolidated files like:

- `getting-started.md` - All getting-started documentation
- `user-guide.md` - All user guide content
- `features.md` - All feature documentation
- `development.md` - All development documentation
- etc.

Each exported file includes:
- A main header with the folder name
- Section headers for each source file
- Source file attribution
- The complete content from each markdown file
- Visual separators between sections

### Example Output Structure

```markdown
# Getting Started

This document consolidates all content from the getting-started documentation folder.

---

## Installation

*Source: installation.md*

[Full content of installation.md]

---

## Quick Start

*Source: quick-start.md*

[Full content of quick-start.md]

---
```

### Notes

- The `doc_exports/` directory is gitignored and safe to regenerate anytime
- Index files (`index.md`) are automatically excluded
- Files are sorted alphabetically for consistent output
- The script handles subdirectories only (ignores files in the root `docs/` folder)
