from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from celery import Celery
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from repo_db import create_engine, create_session_factory
from repo_queue import create_celery
from sqlalchemy.orm import Session as DatabaseSession
from sqlalchemy.orm import sessionmaker
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from api.modules.auth.router import router as auth_router
from api.modules.job_search.router import router as job_search_router
from api.modules.profile.router import router as profile_router
from api.modules.users.router import router as users_router
from api.settings import Settings

API_ERROR_CODES = {
    "unauthorized",
    "forbidden",
    "invalid_cursor",
    "too_many_active_searches",
    "user_not_found",
}


def create_app(
    settings: Settings | None = None,
    session_factory: sessionmaker[DatabaseSession] | None = None,
    queue_app: Celery | None = None,
) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = None
        if session_factory is None:
            engine = create_engine(settings.database_url)
            app.state.session_factory = create_session_factory(engine)
        else:
            app.state.session_factory = session_factory
        yield
        if engine is not None:
            engine.dispose()

    app = FastAPI(title="Tyche API", lifespan=lifespan)
    app.state.settings = settings
    app.state.queue_app = queue_app or create_celery(settings.redis_url)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.client_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.middleware("http")
    async def enforce_trusted_origin(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        origin = request.headers.get("origin")
        if (
            request.method not in {"GET", "HEAD", "OPTIONS"}
            and origin
            and origin not in settings.client_origins
        ):
            return JSONResponse({"error": "forbidden"}, status_code=403)
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, _error: RequestValidationError) -> JSONResponse:
        return JSONResponse({"error": "validation_error"}, status_code=400)

    @app.exception_handler(HTTPException)
    async def http_error(_request: Request, error: HTTPException) -> JSONResponse:
        if isinstance(error.detail, str) and error.detail in API_ERROR_CODES:
            return JSONResponse({"error": error.detail}, status_code=error.status_code)
        return JSONResponse({"detail": error.detail}, status_code=error.status_code)

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"ok": True, "service": "api"}

    app.include_router(auth_router)
    app.include_router(job_search_router)
    app.include_router(profile_router)
    app.include_router(users_router)
    return app
