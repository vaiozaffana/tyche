# Backend

The FastAPI application lives in `apps/api`. Run it with `moon run api:dev`.

## Rules

- Put feature routers and services in `src/api/modules/<feature>`.
- Routers own HTTP validation, authorization, status codes, and error mapping. Services own database operations.
- Use Pydantic at HTTP boundaries and keep JSON aliases compatible with the TypeScript contracts.
- Inject SQLAlchemy sessions through FastAPI dependencies. Do not create engines inside feature services.
- Select and serialize public user fields through response models; never return ORM rows directly.
- Store password hashes with Argon2 and only hashed session tokens in PostgreSQL. Session cookies are HttpOnly and SameSite=Lax.
- Validate unsafe request origins in addition to CORS. Keep `/health` independent of database/session access.
- Keep application settings in `src/api/settings.py` and document every field in `.env.example`.

## Adding a feature

1. Define request/response models in `schemas.py` or a focused feature schema module.
2. Implement a service accepting a SQLAlchemy session and normalized input.
3. Add an `APIRouter`, mount it in `app.py`, and map expected errors.
4. Update `@repo/api-client` and browser Zod schemas when the web app consumes it.
5. Test validation, authorization, expected errors, and success behavior with ASGITransport.

Run `moon run api:lint api:format-check api:typecheck api:test` for focused verification.
