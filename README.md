# Tyche

Tyche is a job-search agent project built as a Moonrepo workspace with a FastAPI API,
React web app, Celery worker, PostgreSQL, and Redis.

The repository includes an asynchronous job-search product. Authenticated users collaborate with a
generative UI agent, approve a precise search brief, watch the persisted run, and inspect ranked
matches. The worker discovers Google Jobs through SerpApi, selectively enriches incomplete postings
with Firecrawl, and ranks them with guarded Gemini specialists. The implementation plans are the
[Job Search Agent MVP](docs/plans/job-search-mvp.md) and
[Generative Job Search UI](docs/plans/generative-job-search-ui.md).

```text
apps/       ai, api, web, worker
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

`pnpm dev` delegates to Moon and starts the API, web app, and Celery worker. `apps/ai`
is imported by the worker and has no standalone process. Open the web app at
`http://localhost:3000`; FastAPI health and docs are at `http://localhost:8000/health` and
`http://localhost:8000/docs`. Development PostgreSQL and Redis use ports `15432` and `16379`.

Run one application with `moon run api:dev`, `moon run web:dev`, or `moon run worker:dev`.

## Job search

Open the authenticated web workspace at `http://localhost:3000`. The UI agent validates a brief,
requires approval before starting paid work, renders tool-specific UI, and synchronizes these API
resources through TanStack Query:

- `POST /job-searches` with `{"prompt":"..."}` returns `202` and a search ID.
- `GET /job-searches/{id}` returns status and ranked results for the owner.
- `GET /job-searches` returns the owner's 20 most recent searches.

For a key-free demo:

```sh
uv run --package tyche-ai python -m tyche_ai.job_search.cli --fake \
  "Cari lowongan akuntan pajak di Surabaya seminggu terakhir"
```

See the [job-search guide](docs/rules/job-search.md) for provider settings, budgets, gates,
extension rules, and production logging constraints.

The web Worker needs `GEMINI_API_KEY` for `/api/chat`. Search history and result pages still work
when the agent secret is absent. In Cloudflare, configure it with `wrangler secret put` as described
in the [deployment guide](docs/rules/deployment.md); never expose it as `VITE_*`.

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
- [AI](docs/rules/ai.md)
- [Job search](docs/rules/job-search.md)
- [Frontend](docs/rules/frontend.md)
- [Database](docs/rules/database.md)
- [Contracts](docs/rules/contracts.md)
- [Worker](docs/rules/worker.md)
- [Storage](docs/rules/storage.md)
- [Deployment](docs/rules/deployment.md)

Record lasting architectural choices in [decision records](docs/decision/README.md).
