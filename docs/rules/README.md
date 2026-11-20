# Technical Rules

Use the rule for the area being changed. Read the relevant accepted records in
[`../decision/`](../decision/) when a change affects architecture or an existing
tradeoff. General repository conventions live in
[`../architecture-convention.md`](../architecture-convention.md).

- [Backend](backend.md): FastAPI modules, authentication, and runtime dependencies.
- [AI](ai.md): agent orchestration, provider integrations, budgets, and offline fakes.
- [Job search](job-search.md): pipeline stages, subagents, gates, budgets, and operations.
- [Frontend](frontend.md): React routes, features, API calls, and UI state.
- [Database](database.md): SQLAlchemy models, Alembic migrations, and integration tests.
- [Contracts](contracts.md): TypeScript/Python public boundaries.
- [Worker](worker.md): Celery producers, processors, and task lifecycle.
- [Storage](storage.md): object storage configuration and ownership.
- [Deployment](deployment.md): Docker, runtime configuration, and Cloudflare publishing.

When adding a new area, add its rule here and link it from the architecture
conventions page. Keep implementation-specific instructions in the relevant
rule instead of duplicating them in general documentation.
