# CLAUDE_REFERENCE.md

Architecture reference for PyYAUL.DB. See [CLAUDE.md](CLAUDE.md) for overview and key rules.

## Subclassing `Version`

Declare your schema by subclassing `Version` and overriding `_initMetaData`:

```python
from pyyaul.db.version import Version
from sqlalchemy import Column, Integer, String
from sqlalchemy.schema import Table

class SchemaV0(Version):
    clsPrev = None  # No previous version

    def _initMetaData(self, metadata):
        Table(
            'table_user',
            metadata,
            Column('id', Integer, primary_key=True),
            Column('email', String(100)),
            schema='my_schema',
        )
```

To add a v1 migration, declare the full v1 schema in `_initMetaData` and implement `_update` for the incremental SQL:

```python
class SchemaV1(Version):
    clsPrev = SchemaV0  # Points to the previous version

    def _initMetaData(self, metadata):
        Table(
            'table_user',
            metadata,
            Column('id', Integer, primary_key=True),
            Column('email', String(100)),
            Column('display_name', String(200)),  # New column
            schema='my_schema',
        )

    def _update(self, engine):
        self._updateAddColumn(
            engine,
            self.metadata.tables['my_schema.table_user'],
            self.metadata.tables['my_schema.table_user'].columns['display_name'],
        )
        return engine
```

## `update(engine)` Flow

`Version.update(engine)` is idempotent:

1. Calls `self.version(engine)` — walks the `clsPrev` chain via `matches()` to detect current DB version
2. **No match** (fresh DB): calls `_initialize(engine)` → `metadata.create_all(engine)`
3. **Already at this version**: no-op
4. **At a previous version**: recursively calls `clsPrev().update(engine)`, then `_update(engine)`
5. Asserts `self.matches(engine)` at the end

## `matches(engine)` — Schema Detection

Uses SQLAlchemy `MetaData.reflect()` to read the live DB, then compares each declared table/column. Returns `True` only if all declared tables and columns are structurally identical to the DB.

**Note:** Does NOT check for extra tables or extra columns in the DB beyond what's declared.

## Helper Methods

| Method | Purpose |
|--------|---------|
| `schema_create(connection, schema, replaceExisting=False)` | Creates a PostgreSQL schema; optionally DROPs existing |
| `schema_exists(connection, schema)` | Checks if a PostgreSQL schema exists |
| `table_exists(connection, schema, table)` | Checks if a table exists |
| `_updateAddColumn(engine, table, column)` | `ALTER TABLE ... ADD COLUMN` utility |
