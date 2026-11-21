# Deployment

The API and Celery worker run from the same Python image. PostgreSQL stores application/auth data; Redis is the Celery broker/result backend. The React app deploys separately to Cloudflare.

## API and worker

```sh
cp .env.example .env
docker compose up --build
```

Compose applies Alembic migrations before starting Uvicorn, then starts Celery after Redis is healthy. The API is exposed on port 8000 by default.

- Set `DOCKER_DATABASE_URL` and `DOCKER_REDIS_URL` for external managed services.
- Set `CLIENT_ORIGINS` to comma-separated frontend origins without paths.
- `SESSION_COOKIE_SECURE` defaults to false in local Compose. Set it to true behind production HTTPS.
- Review migrations before deployment and back up persistent databases.

## Cloudflare web app

```sh
pnpm --filter @repo/web exec wrangler login
moon run web:bundle-check
VITE_API_URL="https://api.example.com" pnpm deploy:web
```

`VITE_API_URL` is embedded at build time. Allow the deployed web origin in `CLIENT_ORIGINS`.

The Cloudflare Worker serves the SPA and handles `/api/chat` before static assets. Configure the
agent secret without placing it in `wrangler.jsonc` or a `VITE_*` variable:

```sh
pnpm --filter @repo/web exec wrangler secret put GEMINI_API_KEY
```

The browser never receives this key. A missing secret returns `503` from `/api/chat`; search,
history, profile, and authentication continue to use FastAPI through `VITE_API_URL`.

For local `pnpm dev`, Vite reads `GEMINI_API_KEY` from the repository root `.env` only during
the serve command. Production builds do not load that local value or copy `.env`/`.dev.vars`
into `dist`; Cloudflare must receive the secret through Wrangler as shown above.

CI installs pinned Moon toolchains, checks both languages, applies migrations to PostgreSQL, validates the Cloudflare bundle, and builds the Python container. The CD job remains an explicit placeholder.
