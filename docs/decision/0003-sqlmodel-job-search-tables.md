---
status: accepted
date: 2026-11-20
supersedes: []
superseded_by: null
---

# Use SQLModel for job-search tables with the existing SQLAlchemy metadata

## Context

The repository already has SQLAlchemy declarative auth tables and an injected SQLAlchemy `Session`.
The product requires SQLModel for new job-search tables without splitting Alembic's schema graph.

## Decision

Define the three job-search tables as SQLModel `table=True` classes and bind each to
`Base.metadata`. Continue using `sqlalchemy.orm.Session`, injected by callers, with 2.0-style
statements. Alembic keeps one `target_metadata`.

The spike proved foreign-key resolution, SQLite and PostgreSQL create/insert/select, rollback, and
strict mypy. Migration `30052bf381b1` adds only job-search tables and indexes; `alembic check`
reports no further operations after upgrade.

## Alternatives

- Separate SQLModel metadata was rejected because cross-metadata foreign keys and autogenerate are
  harder to reason about.
- Rewriting existing auth models as SQLModel was rejected as unrelated migration risk.
- A SQLModel `Session` was rejected because the repository already standardizes SQLAlchemy sessions.

## Consequences

All models share one migration graph and tests can use SQLite. SQLModel class expressions use its
typed `col()` helper where strict mypy needs it.

## Status history

| Date       | Status   | Reason            |
| ---------- | -------- | ----------------- |
| 2026-11-20 | accepted | Initial decision. |
