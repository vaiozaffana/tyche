# Monorepo Template

A Moonrepo workspace with a FastAPI API, React web app, Celery worker, PostgreSQL, and Redis.

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

Start with [repository rules](docs/README.md), then read the guide for your change:

- [Backend](docs/backend.md)
- [Frontend](docs/frontend.md)
- [Database](docs/database.md)
- [Contracts](docs/contracts.md)
- [Worker](docs/worker.md)
- [Storage](docs/storage.md)
- [Deployment](docs/deployment.md)

Record lasting architectural choices in [decision records](docs/decision/README.md).
