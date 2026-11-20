# Database

`packages/db` owns SQLAlchemy models, engine/session factories, and Alembic migrations.

## Rules

- Define persistence tables in `src/repo_db/models.py`; public API representations belong in application schemas.
- New feature tables may use SQLModel `table=True` when they bind `metadata = Base.metadata`; callers still use the injected SQLAlchemy `Session`, 2.0-style statements, and one Alembic metadata graph.
- Preserve quoted table/column names when compatibility with existing template databases matters.
- Application startup owns the engine. Feature services receive a session.
- Enforce durable invariants with database constraints and transactions.
- Store UTC timestamps and serialize them as ISO strings at public boundaries.
- Commit Alembic revisions with model changes. Review generated operations for data loss before applying them.
- Never rewrite a migration already used by a shared database.

## Changing the schema

```sh
pnpm db:generate -- -m "describe change"
pnpm db:migrate
moon run db:migration-check api:test
```

The initial Alembic revision detects existing template tables and stamps them without dropping their data. Tests use SQLite for fast service/API coverage; migration verification and runtime checks use PostgreSQL.
