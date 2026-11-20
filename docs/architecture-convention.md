# Architecture Conventions

Start with the [root README](../README.md). This page describes the general
ownership and change conventions for the repository.

- [Technical rules](rules/README.md): index of area-specific rules.
- [Backend](rules/backend.md): FastAPI modules, authentication, and runtime dependencies.
- [AI](rules/ai.md): orchestration, provider boundaries, deterministic budgets, and fake mode.
- [Job search](rules/job-search.md): staged discovery, specialist assessment, persistence, and API polling.
- [Frontend](rules/frontend.md): React routes, features, API calls, and UI state.
- [Database](rules/database.md): SQLAlchemy models, Alembic migrations, and integration tests.
- [Contracts](rules/contracts.md): TypeScript/Python public boundaries.
- [Worker](rules/worker.md): Celery producers, processors, and task lifecycle.
- [Storage](rules/storage.md): object storage configuration and ownership.
- [Deployment](rules/deployment.md): Docker, runtime configuration, and Cloudflare publishing.
- [Decisions](decision/README.md): recording and replacing architectural decisions.

## Common rules

- Applications own settings and runtime startup. Shared packages accept configuration explicitly.
- Python apps import workspace packages through their published module names. TypeScript packages use declared public workspace exports.
- Keep browser code free of database and queue infrastructure. `@repo/api-client` is the web HTTP boundary.
- Update Pydantic and Zod representations together when a public JSON contract changes.
- Keep feature logic with its feature. Extract a package only for concrete reuse.
- Never print credentials, password hashes, session tokens, or sensitive payloads.
- Record architectural choices with lasting tradeoffs in a decision file.

## Change workflow

1. Read this page, the relevant rule, and accepted decisions.
2. Update the public contract, owner, and consumers in one change.
3. Add tests and keep `.env.example` aligned with settings.
4. Run `pnpm check`, `pnpm typecheck`, `pnpm test`, and `pnpm build`.
5. Review generated migrations and lockfiles before committing.

Root pnpm scripts delegate to Moon. Use `moon run <project>:<task>` for a focused check.
