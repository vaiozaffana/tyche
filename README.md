# Tyche

Tyche is a job-search agent project built as a Moonrepo workspace with a FastAPI API,
React web app, Celery worker, PostgreSQL, and Redis.

The repository currently contains the application foundation only. The job-search feature has
not been implemented; its authoritative implementation plan is the
[Job Search Agent MVP ExecPlan](docs/plans/job-search-mvp.md).

```text
apps/       api, web, worker
packages/   contracts, api-client, db, queue, storage, ui
docs/       working guides and decision records
```

Moon pins Node.js 24, pnpm 10, Python 3.12, and uv for consistent cross-language tasks. Install [Moon 2](https://moonrepo.dev/docs/install), then run:

```sh
moon setup
pnpm install
uv sync --frozen --all-packages --all-groups
cp .env.example .env
docker compose -f docker-compose.dev.yaml up -d
pnpm db:migrate
pnpm dev
```

`pnpm dev` delegates to Moon and starts the API, web app, and Celery worker. Open the web app at `http://localhost:3000`; FastAPI health and docs are at `http://localhost:8000/health` and `http://localhost:8000/docs`. Development PostgreSQL and Redis use ports `15432` and `16379`.

Run one application with `moon run api:dev`, `moon run web:dev`, or `moon run worker:dev`.

## Common commands

| Command                           | Purpose                                                            |
| --------------------------------- | ------------------------------------------------------------------ |
| `pnpm check`                      | Check boundaries, env docs, lint, and formatting in both languages |
| `pnpm typecheck`                  | Typecheck Python and TypeScript projects                           |
| `pnpm test`                       | Run Python and TypeScript test suites                              |
| `pnpm build`                      | Compile Python sources and build the React app                     |
| `pnpm format`                     | Format Python and TypeScript sources                               |
| `pnpm db:generate -- -m "change"` | Generate an Alembic migration                                      |
| `pnpm db:migrate`                 | Apply committed database migrations                                |
| `pnpm createsuperuser`            | Create or promote an admin user                                    |

## Working guides

Start with [architecture conventions](docs/architecture-convention.md), then
read the technical rule for your change:

- [Technical rules](docs/rules/README.md)
- [Backend](docs/rules/backend.md)
- [Frontend](docs/rules/frontend.md)
- [Database](docs/rules/database.md)
- [Contracts](docs/rules/contracts.md)
- [Worker](docs/rules/worker.md)
- [Storage](docs/rules/storage.md)
- [Deployment](docs/rules/deployment.md)

Record lasting architectural choices in [decision records](docs/decision/README.md).
