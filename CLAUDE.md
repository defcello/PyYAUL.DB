# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. For architecture details and code examples, see [CLAUDE_REFERENCE.md](CLAUDE_REFERENCE.md).

## Overview

**PyYAUL.DB** provides a SQLAlchemy-based schema versioning system for SkillTrails. The core class is `pyyaul.db.version.Version`, which subclasses `pyyaul.base.version.Version` from the sibling `PyYAUL.Base` repo.

This repo is one of several sub-repos managed under `devenv-skilltrails/` via `manifest.xml`. No `pip install` or `pyproject.toml`; dependencies are sibling repos added to `sys.path` by consumer `_execommon.py` files.

## Architecture

```
pyyaul/db/
    version.py   — Version class: schema declaration, matching, creation, migration utilities
    orm.py       — ORM class: reflects existing DB schema into SQLAlchemy session-able tables
```

`pyyaul/` has no `__init__.py` — implicit namespace package (matches PyYAUL.Base convention).

## Dependencies

- `../PyYAUL.Base` — provides `pyyaul.base.version.Version` (the abstract base class)
- SQLAlchemy (must be installed in the Python environment)

## Key Rules

- **`vLatest.py` must export an instance, not a class**: `Schema = v0.SchemaV0()` not `Schema = v0.SchemaV0`
- **`_initMetaData` pattern depends on the version:**
  - **v0 (base)**: declare the full schema — all tables and columns
  - **vN (incremental, adding columns to an existing table)**: call `super()._initMetaData(metadata)` to inherit the parent schema, then re-declare only the table with just the new columns and `extend_existing=True`
  - **vN (incremental, adding a new table)**: call `super()._initMetaData(metadata)`, then declare the new table normally (no `extend_existing`)
- **`_update` handles only the incremental migration** (e.g., `ALTER TABLE ADD COLUMN`)
- Always import schema from `vLatest` in consumers, never from a specific `vN` module

## Known Bugs

- **`SQLAlchemyError` not imported** in `version.py` — `except SQLAlchemyError` in `schema_create()` will raise `NameError` if triggered. See defcello/PyYAUL.DB#1.
- **`compareTables()` uses `zip()`** — silently ignores column count mismatches. See defcello/PyYAUL.DB#2.

## Consumers

- `skilltrails-initdb`: calls `schema.update(engine)` to bootstrap a fresh database
- `skilltrails-admin`: imports schema instances for `db_checkUpdateAvailable()` checks on the dashboard
- `PyYAUL.Web`: `SchemaV0_Base` in `pyyaul/web/auth/db/schema/v0.py` subclasses `Version`

## GitHub Issues

Repo: `defcello/PyYAUL.DB`. Use `gh issue create` for deferred work. Run `/jc-retrospective` at session end.
