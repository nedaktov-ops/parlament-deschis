# syntax=docker/dockerfile:1
#
# Parlament Deschis — production image.
#
# The service is read-only at runtime: the SQLite database is rebuilt from the
# official sources by a scheduled job and baked into the image. That is what
# makes it work on a free host, where a free web service has no persistent
# disk and loses local files on every redeploy (render.com/docs/free).
#
# The database is prepared by scripts/prepare_db.py, which rewrites it into a
# single file with journal_mode=DELETE. A WAL database cannot even be opened
# on a read-only filesystem, because it needs to create its -wal/-shm files.

# --- stage 1: the single-page app -----------------------------------------
FROM node:22-alpine AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- stage 2: the API and the pipeline -------------------------------------
FROM python:3.12-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

RUN pip install --no-cache-dir uv
WORKDIR /app

# Dependencies first, so a code change does not reinstall them.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --no-dev --no-install-project

COPY backend/ ./backend/
COPY pipeline/ ./pipeline/
COPY scripts/ ./scripts/
COPY data/reference/ ./data/reference/
COPY --from=frontend /app/dist ./frontend/dist

RUN uv sync --no-dev

# --- stage 3: the database -------------------------------------------------
# The build must fail loudly when the database is missing: an image without
# it would serve an empty tool, which is worse than no tool at all.
FROM backend AS data
ARG SOURCE_DB=data/parlament-real.db
COPY ${SOURCE_DB} /tmp/source.db
RUN python scripts/prepare_db.py /tmp/source.db /app/data/parlament.db \
    && rm /tmp/source.db

# --- stage 4: runtime ------------------------------------------------------
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PARLAMENT_DB=/app/data/parlament.db

RUN useradd --create-home --uid 10001 nedcode
WORKDIR /app

COPY --from=backend /app/.venv /app/.venv
COPY --from=backend /app/backend /app/backend
COPY --from=backend /app/pipeline /app/pipeline
COPY --from=backend /app/frontend/dist /app/frontend/dist
COPY --from=data /app/data/parlament.db /app/data/parlament.db
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && chown -R nedcode:nedcode /app

USER nedcode
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
