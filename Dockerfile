FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /uvx /bin/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
COPY apps/ai/pyproject.toml apps/ai/pyproject.toml
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/worker/pyproject.toml apps/worker/pyproject.toml
COPY packages/db/pyproject.toml packages/db/pyproject.toml
COPY packages/queue/pyproject.toml packages/queue/pyproject.toml

RUN uv sync --frozen --no-dev --all-packages --no-install-workspace

COPY apps/ai apps/ai
COPY apps/api apps/api
COPY apps/worker apps/worker
COPY packages/db packages/db
COPY packages/queue packages/queue

RUN uv sync --frozen --no-dev --all-packages

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin app
USER app

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
