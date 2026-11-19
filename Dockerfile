# syntax=docker/dockerfile:1
#
# Parlament Deschis — production image.
#
# The service is read-only at runtime: the SQLite database is rebuilt from the
# official sources by a scheduled job and baked into the image. That is what
# makes it work on a free host, where a free web service has no persistent
# disk and loses local files on every redeploy (render.com/docs/free).
#
# The exact release tag is checked into data/latest-release.txt. Copying that
# marker before the download invalidates the dataset layer for every release
# and makes the image contents reproducible. The downloaded database is
# prepared as a single file with journal_mode=DELETE; a WAL database cannot be
# opened on a read-only filesystem because it needs -wal/-shm sidecars.

# --- stage 1: the single-page app -----------------------------------------
FROM node:22-alpine AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- stage 2: the API and the pipeline -------------------------------------
FROM python:3.15-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Pin uv to the exact version used by CI and local development so that
# `uv sync --locked` resolves the same lockfile revision everywhere.
RUN pip install --no-cache-dir uv==0.13.1
WORKDIR /app

# Dependencies first, so a code change does not reinstall them.
# --locked fails loudly if uv.lock and pyproject.toml ever drift apart.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

COPY backend/ ./backend/
COPY pipeline/ ./pipeline/
COPY scripts/ ./scripts/
COPY data/reference/ ./data/reference/
COPY --from=frontend /app/dist ./frontend/dist

RUN uv sync --locked --no-dev

# --- stage 3: the database -------------------------------------------------
# The build must fail loudly when the database is missing: an image without
# it would serve an empty tool, which is worse than no tool at all.
#
# Residual risk (P5-E): this in-build download calls the GitHub releases API
# WITHOUT a token, so it shares the shared-runner IP's unauthenticated 60
# requests/hour allowance and can intermittently 403 under load. The `audit`
# job in ci.yml already authenticates its download with GITHUB_TOKEN (P4-C);
# the image build does not. Authenticating here would require plumbing a new
# BuildKit `--mount=type=secret` plus a `secrets:` entry on the build step in
# ci.yml. No such build-secret mechanism exists anywhere in this repo, so we
# deliberately do NOT introduce an unconfigured secret requirement that would
# break builds. Retry/backoff in download_dataset.py mitigates transient
# failures; the rate-limit ceiling is accepted as a documented residual.
FROM backend AS data
COPY data/latest-release.txt ./data/latest-release.txt
RUN python scripts/download_dataset.py \
        --metadata /tmp/dataset-metadata.json \
        /tmp/source.db \
    && python scripts/prepare_db.py /tmp/source.db /app/data/parlament.db \
    && rm /tmp/source.db

# --- stage 4: runtime ------------------------------------------------------
FROM python:3.15-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PARLAMENT_DB=/app/data/parlament.db \
    PARLAMENT_DATASET_METADATA=/app/data/dataset-metadata.json

RUN useradd --create-home --uid 10001 nedcode
WORKDIR /app

COPY --from=backend /app/.venv /app/.venv
COPY --from=backend /app/backend /app/backend
COPY --from=backend /app/pipeline /app/pipeline
COPY --from=backend /app/frontend/dist /app/frontend/dist
COPY --from=data /app/data/parlament.db /app/data/parlament.db
COPY --from=data /tmp/dataset-metadata.json /app/data/dataset-metadata.json
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && chown -R nedcode:nedcode /app

USER nedcode
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health/ready', timeout=4).status == 200 else 1)"

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
