# Repository Guidelines

## Project Structure

This is a Moonrepo monorepo. Runtime applications live in `apps/`: `api` is the
FastAPI service, `web` is the React/Vite frontend, and `worker` runs Celery
tasks. Shared code lives in `packages/`: `contracts` and `api-client` define
the browser/API boundary, while `db`, `queue`, `storage`, and `ui` provide
backend, infrastructure, storage, and frontend components. Python tests are in
each app's `tests/` directory; TypeScript tests sit beside source files as
`*.test.ts`. Operational and architecture documentation is in `docs/`.

## Documentation First

Before changing code, read `docs/architecture-convention.md`,
`docs/rules/README.md`, and the rule relevant to the affected area
(`docs/rules/backend.md`, `docs/rules/frontend.md`,
`docs/rules/database.md`, `docs/rules/contracts.md`,
`docs/rules/worker.md`, `docs/rules/storage.md`, or
`docs/rules/deployment.md`). Read accepted decision records in
`docs/decision/` when the change touches architecture or established
tradeoffs. Any new convention, architectural decision, workflow, integration,
or behavior that a future agent must understand must be documented in the
appropriate `docs/` guide or a new decision record in the same change.

## Development Commands

Use Node.js 24, pnpm 10, Python 3.12, and uv. For a first checkout:

```sh
moon setup && pnpm install
uv sync --frozen --all-packages --all-groups
cp .env.example .env
docker compose -f docker-compose.dev.yaml up -d
pnpm db:migrate
```

Common commands:

- `pnpm dev` starts the API, web app, and worker; use `moon run api:dev` (or
  `web:dev`/`worker:dev`) for one service.
- `pnpm check` runs boundary, environment, lint, and formatting checks.
- `pnpm typecheck`, `pnpm test`, and `pnpm build` run static checks, all tests,
  and production builds respectively.
- `pnpm format` applies formatting. Generate and apply migrations with
  `pnpm db:generate -- -m "describe change"` and `pnpm db:migrate`.

## Code Style and Testing

Use two-space indentation for TypeScript and standard Python indentation.
Python uses Ruff (100-character lines, imports enabled) and strict mypy;
TypeScript uses Oxfmt, Oxlint with warnings denied, and project-local
TypeScript settings. Keep feature logic in its owning app or feature, and use
workspace package exports for shared code. Name Python tests `test_*.py` and
TypeScript tests `*.test.ts`; add or update tests with behavior changes.

## Changes and Pull Requests

The history currently contains only the initial commit, so no repository-specific
commit convention is established. Use a short, imperative subject (for example,
`Fix profile validation`) and keep commits focused. Pull requests should explain
the behavior change, link the relevant issue or decision record when applicable,
list verification commands, and include screenshots for visible UI changes.

## Configuration and Security

Copy `.env.example` rather than committing `.env`. Never log credentials,
password hashes, session tokens, or sensitive payloads. Keep Pydantic and Zod
representations synchronized when changing public JSON contracts, and review
generated migrations and lockfiles before committing.
