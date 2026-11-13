---
status: accepted
date: 2026-11-11
supersedes: []
superseded_by: null
---

# Use FastAPI, Celery, and Moon for server-side applications

## Context

The template previously used Hono, Drizzle, Better Auth, and BullMQ in a pnpm-only workspace. It needs a Python API/worker while retaining the React product and the same auth, profile, users, database, and background-task behavior.

## Decision

Use FastAPI with Pydantic, SQLAlchemy/Alembic, opaque database sessions, and Argon2 in `apps/api` and `packages/db`. Use Celery with Redis in `apps/worker` and `packages/queue`. Keep React, Zod browser contracts, and UI packages in pnpm. Use Moonrepo as the cross-language task graph while uv and pnpm remain the ecosystem package managers.

## Consequences

- Public HTTP behavior stays stable, but Hono RPC inference is replaced by a small typed fetch client.
- Browser Zod and server Pydantic schemas must be updated together.
- Moon provides one root workflow while preserving focused native tooling.
- Existing table names remain compatible; sessions/password hashes from the removed auth implementation are not reused.
